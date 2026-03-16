@echo off
echo Richte Kassensystem auf diesem PC ein...
cd /d "%~dp0"
echo Installiere benötigte Bibliotheken (Flask)...
python -m pip install -r requirements.txt
echo.
echo Fertig! Du kannst jetzt start_server.bat oder start_gui.bat nutzen.
pause
