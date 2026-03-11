@echo off
chcp 65001 >nul
echo ========================================
echo   量化分析系统 - Python 3.12.10
echo ========================================
echo.

echo [1/3] 激活虚拟环境...
call venv312\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败！
    pause
    exit /b 1
)

echo ✅ 虚拟环境已激活
echo.

echo [2/3] 检查Python版本...
python --version
echo.

echo [3/3] 启动后端服务...
echo.
echo ========================================
echo   服务地址: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo ========================================
echo.

cd backend
python main.py