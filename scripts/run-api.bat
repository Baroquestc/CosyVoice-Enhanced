@echo off


call ...\env\python.exe api\api.py --host 0.0.0.0 --port 9001 --model pretrained_models/CosyVoice-300M-SFT

pause