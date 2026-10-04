@echo off
chcp 65001 >nul
echo.
echo   น้ำ.watch ^| Thailand Flood Relief Platform
echo   ----------------------------------------
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ไม่พบ Python กรุณาติดตั้ง Python 3.7+ ก่อน
    pause
    exit /b 1
)

if not exist "venv\Scripts\activate.bat" (
    echo [SETUP] สร้าง virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo [SETUP] ติดตั้ง dependencies...
pip install -r requirements.txt --quiet

echo.
echo   เปิด http://localhost:5000 ในเบราว์เซอร์
echo   กด Ctrl+C เพื่อหยุด
echo.

set FLASK_APP=app.py
set FLASK_ENV=development
python app.py

pause
