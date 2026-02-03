@echo off
cd /d "%~dp0"
echo Starting Trading System...
start "Trading Bot (Paper Trading)" "C:\Program Files\Python311\python.exe" trade_and_log.py
start "Dashboard" "C:\Program Files\Python311\python.exe" -m streamlit run dashboard.py
echo System started in two separate windows.
pause
