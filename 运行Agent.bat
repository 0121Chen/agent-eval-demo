@echo off
chcp 65001 >nul
cd /d "%~dp0"
set /p q=请输入你的问题（例如：小爱同学没反应了怎么办）:
echo.
python agent.py "%q%"
echo.
pause
