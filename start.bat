@echo off
chcp 65001 >nul
title v17 Pure Math Image Processor
cls

:MENU
cls
echo ==========================================================
echo    ✨ v17 Pure Math Edition (參數化運算極速版)
echo ==========================================================
echo.
echo    [1] 🎨 啟動 GUI (網頁介面 - 推薦)
echo    [2] 💻 啟動 CLI (命令列介面)
echo    [3] 📦 安裝/更新 必要的 Python 套件 (首次執行請選此)
echo    [4] ❌ 離開
echo.
echo ==========================================================
set /p choice="請輸入選項 (1-4): "

if "%choice%"=="1" goto GUI
if "%choice%"=="2" goto CLI
if "%choice%"=="3" goto INSTALL
if "%choice%"=="4" goto EXIT
goto MENU

:GUI
cls
echo [INFO] 正在啟動 v17 圖形介面...
echo [TIPS] 這版本不需要 LUT 檔，運算將在毫秒級完成。
echo.
python gui_app.py
pause
goto MENU

:CLI
cls
echo [INFO] 正在啟動 v17 命令列模式...
echo [TIPS] 輸入圖片路徑即可開始批次數學運算。
echo.
python main.py
pause
goto MENU

:INSTALL
cls
echo [INFO] 正在安裝 v17 所需輕量套件 (Numpy, Pillow, Gradio)...
echo ----------------------------------------------------------
pip install -r requirements.txt
echo ----------------------------------------------------------
echo [SUCCESS] 安裝完成！環境已淨化。
pause
goto MENU

:EXIT
exit