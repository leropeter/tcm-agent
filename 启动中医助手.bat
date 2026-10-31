@echo off
chcp 65001 >nul
title 中医辨证调养助手 TCM Agent
cd /d "%~dp0"

echo ================================================
echo   中医药辨证调养助手 - 正在启动
echo   浏览器会自动打开，没打开就手动访问：
echo   http://127.0.0.1:8501
echo ================================================
echo.

set PY=E:\Python312\python.exe
if not exist "%PY%" (
    echo [错误] 找不到 Python：%PY%
    echo 请修改本文件里的 PY 路径为你的 python.exe 位置
    pause
    exit /b 1
)

"%PY%" -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false

echo.
echo 服务已停止。按任意键关闭窗口。
pause >nul
