@echo off
start cmd /k "docsify serve ."
timeout /t 2 >nul
start chrome http://localhost:3000/