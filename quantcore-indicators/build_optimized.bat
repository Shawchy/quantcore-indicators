@echo off
echo ========================================
echo quantcore-indicators 优化版编译安装
echo ========================================
echo.
echo 优化内容:
echo   1. WMA 滑动窗口 O(n*k) - O(n)
echo   2. EMA 缓存友好优化
echo   3. CCI 增量绝对偏差 O(n*k) - O(n)
echo   4. Bollinger 合并计算
echo   5. Stochastic %%D 滑动求和
echo   6. 移除 serde 死依赖
echo   7. 新增 6 个指标: DEMA/TEMA/HMA/ROC/PSAR/NATR
echo.

cd /d "%~dp0"

echo [1/3] 清理旧编译产物...
if exist "target\release" rd /s /q target\release
echo 清理完成
echo.

echo [2/3] 编译并安装...
maturin develop --release
if %errorlevel% neq 0 (
    echo.
    echo 编译失败！请检查:
    echo   1. Rust 是否安装: rustc --version
    echo   2. maturin 是否安装: pip install maturin
    echo   3. numpy 是否安装: pip install numpy
    echo.
    pause
    exit /b 1
)
echo.

echo [3/3] 验证安装...
python -c "from quantcore_indicators import __all__; print(f'OK: {len(__all__)} indicators loaded'); print(__all__)"
echo.

echo ========================================
echo 编译安装完成！
echo ========================================
echo.
echo 指标总数: 20
echo.
echo 运行性能测试:
echo   python benchmarks/final_comparison.py
echo.
pause
