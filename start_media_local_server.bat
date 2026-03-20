@echo off
setlocal

start "MediaLocalServer" powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pdf_local_server.ps1" -Port 8765
