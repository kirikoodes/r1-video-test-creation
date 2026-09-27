"""
Petit serveur HTTP local pour recevoir les vidéos enregistrées par la creation
r1 "Test Vidéo Caméra" et les sauvegarder directement sur ce PC.

Démarrage :
    python server.py
(ou : python server.py 8765   pour changer le port, 8765 par défaut)

Le serveur écoute sur toutes les interfaces réseau (0.0.0.0) du PC, sur le
port choisi. Il doit tourner PENDANT l'enregistrement sur le r1, et le PC
doit être sur le MÊME réseau Wi-Fi que le r1.

Les vidéos reçues sont enregistrées dans :
    C:\\Users\\kirik\\OS3\\r1-video-test-creation\\videos-recues\\

Pour trouver l'adresse IP locale à saisir dans la creation sur le r1 :
    ipconfig   (regarder "Adresse IPv4" de la carte Wi-Fi active)
"""
import http.server
import socketserver
import os
import sys
import datetime
import cgi

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos-recues")
os.makedirs(SAVE_DIR, exist_ok=True)


class Handler(http.server.BaseHTTPRequestHandler):
    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        # Sert la creation elle-meme en HTTP simple sur "/" ou "/index.html",
        # pour eviter le blocage "mixed content" HTTPS->HTTP quand la creation
        # est ouverte depuis GitHub Pages (HTTPS) et essaie de parler a ce
        # serveur local en HTTP: en ouvrant directement cette adresse locale
        # dans le r1, toute la page (et donc le fetch vers /upload) reste en
        # HTTP, donc plus de blocage mixed content.
        if self.path in ("/", "/index.html"):
            index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
            try:
                with open(index_path, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self._cors_headers()
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
                return
            except OSError as e:
                self.send_response(500)
                self._cors_headers()
                self.end_headers()
                self.wfile.write(f"ERREUR lecture index.html: {e}".encode("utf-8"))
                return

        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            f"Serveur de reception video r1 - OK\nDossier de sauvegarde: {SAVE_DIR}\n".encode("utf-8")
        )

    def do_POST(self):
        if self.path != "/upload":
            self.send_response(404)
            self._cors_headers()
            self.end_headers()
            return
        try:
            content_type = self.headers.get("Content-Type", "")
            length = int(self.headers.get("Content-Length", 0))
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

            if content_type.startswith("multipart/form-data"):
                # Upload via FormData (fileToUpload)
                ctype, pdict = cgi.parse_header(content_type)
                pdict["boundary"] = pdict["boundary"].encode("utf-8")
                pdict["CONTENT-LENGTH"] = length
                fields = cgi.parse_multipart(self.rfile, pdict)
                file_bytes = None
                for key in fields:
                    if fields[key]:
                        candidate = fields[key][0]
                        if isinstance(candidate, (bytes, bytearray)) and len(candidate) > 0:
                            file_bytes = candidate
                if file_bytes is None:
                    raise ValueError("Aucun fichier trouve dans le formulaire")
                ext = "webm"
            else:
                # Upload brut (raw body = le blob video directement)
                file_bytes = self.rfile.read(length)
                ext = "mp4" if "mp4" in content_type else "webm"

            filename = f"r1-video-{timestamp}.{ext}"
            filepath = os.path.join(SAVE_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(file_bytes)

            self.send_response(200)
            self._cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"OK:{filename}".encode("utf-8"))
            print(f"[{timestamp}] Video recue et enregistree: {filepath} ({len(file_bytes)} octets)")
        except Exception as e:
            self.send_response(500)
            self._cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"ERREUR:{e}".encode("utf-8"))
            print(f"Erreur reception: {e}")

    def log_message(self, format, *args):
        pass  # on garde uniquement nos propres print() plus lisibles


if __name__ == "__main__":
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Serveur de reception video demarre sur le port {PORT}.")
        print(f"Dossier de sauvegarde: {SAVE_DIR}")
        print("Laissez cette fenetre ouverte pendant l'enregistrement sur le r1.")
        print("Ctrl+C pour arreter.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Arret du serveur.")
