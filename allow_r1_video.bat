@echo off
:: Auto-elevate via UAC if not already admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

setlocal
set RULENAME=R1VideoServer-8765

netsh advfirewall firewall show rule name="%RULENAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo Firewall rule "%RULENAME%" already exists. Nothing to do.
) else (
    netsh advfirewall firewall add rule name="%RULENAME%" dir=in action=allow protocol=TCP localport=8765
    if %errorlevel% equ 0 (
        echo Firewall rule "%RULENAME%" added successfully.
    ) else (
        echo Failed to add firewall rule.
    )
)

echo.
echo Press any key to close this window...
pause >nul
