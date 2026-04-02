@echo off
REM Playwright 浏览器安装脚本
REM 使用淘宝镜像加速下载

echo 正在安装 Playwright Chromium 浏览器...

set PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright_browsers
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

playwright install chromium

echo.
echo 安装完成！
echo 浏览器位置: %PLAYWRIGHT_BROWSERS_PATH%\chromium-*
pause
