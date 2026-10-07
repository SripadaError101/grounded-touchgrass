@echo off
echo ========================================================
echo   🌿 GROUNDED: TouchGrass AI - Open-Source Outdoor Companion
echo ========================================================
echo.
echo Installing / checking requirements...
python -m pip install -r requirements.txt
echo.
echo Starting Grounded...
python run.py
pause
