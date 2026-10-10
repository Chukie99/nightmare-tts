@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat

if not exist output.wav (
    echo ERROR: output.wav not found!
    echo Make sure you ran the TTS runner first (JALANKAN.bat)
    exit /b 1
)

echo Converting output.wav to output.mp3...
ffmpeg -y -i output.wav output.mp3

if %errorlevel% equ 0 (
    echo Conversion successful! MP3 saved as output.mp3
) else (
    echo Conversion failed. Check if ffmpeg is installed and in PATH.
)
pause