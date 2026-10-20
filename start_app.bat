@echo off
title FTTH Analytics Dashboard
cd /d "%~dp0"
echo ========================================================
echo       منظومة متابعة وتحليل شبكات الألياف الضوئية (FTTH)
echo ========================================================
echo جاري تشغيل التطبيق وفتح المتصفح...
start http://localhost:8501
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501
pause
