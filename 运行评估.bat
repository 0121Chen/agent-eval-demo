@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 开始运行 13 个测试用例的完整评估...
echo.
python eval.py
echo.
pause
