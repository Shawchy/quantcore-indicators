@echo off
echo ========================================
echo quantcore-indicators 编译安装脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 清理旧的编译产物...
if exist "target" rd /s /q target
echo 清理完成
echo.

echo [2/3] 编译并安装到当前虚拟环境...
maturin develop --release
if %errorlevel% neq 0 (
    echo.
    echo ❌ 编译失败！
    echo.
    echo 可能的原因：
    echo 1. 未安装 Rust: 运行 rustup-init.exe 安装
    echo 2. 未安装 maturin: 运行 pip install maturin
    echo 3. Python 版本不兼容: 需要 Python 3.8-3.12
    echo 4. Windows 需要 Visual Studio C++ Build Tools
    echo.
    pause
    exit /b 1
)
echo.

echo [3/3] 验证安装...
python -c "import quantcore_indicators; print('✅ 模块加载成功')"
if %errorlevel% neq 0 (
    echo ❌ 验证失败
    pause
    exit /b 1
)
echo.

echo ========================================
echo ✅ 安装完成！
echo ========================================
echo.
echo 可用指标：
python -c "from quantcore_indicators import __all__; print('\n'.join(__all__))"
echo.
pause
