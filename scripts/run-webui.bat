@echo off

::setup ffmpeg
set PATH=%PATH%;%cd%\ffmpeg\bin

call .\env\python.exe api\webui.py --host "0.0.0.0" --port 8000 --transcription_key "sk-npuhvygjrqzzpdrektmngidpjanbieooozsnzxjjmcwbxmdt" --hot_reload --model "CosyVoice2-0.5B" --language zh

pause