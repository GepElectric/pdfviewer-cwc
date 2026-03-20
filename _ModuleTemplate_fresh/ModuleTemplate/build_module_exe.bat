@echo off
setlocal

for %%I in ("%~dp0.") do set "ROOT=%%~fI"
cd /d "%ROOT%"

echo Building ExampleModule EXE...
echo Working directory: "%ROOT%"

python -m PyInstaller --noconfirm --clean --windowed --onedir --name ExampleModule --paths "%ROOT%" --paths "%ROOT%\example_module" "%ROOT%\main.py"

if errorlevel 1 (
  echo.
  echo Build failed.
  pause
  exit /b 1
)

set STAGE_DIR=%ROOT%\dist\example_module_package
set ZIP_PATH=%ROOT%\dist\example_module_package.zip
if exist "%STAGE_DIR%" rmdir /s /q "%STAGE_DIR%"
mkdir "%STAGE_DIR%"
if exist "%ZIP_PATH%" del /q "%ZIP_PATH%"

xcopy "%ROOT%\dist\ExampleModule" "%STAGE_DIR%\ExampleModule" /e /i /y >nul
copy "%ROOT%\module.json" "%STAGE_DIR%\" >nul
copy "%ROOT%\requirements.txt" "%STAGE_DIR%\" >nul
copy "%ROOT%\README.md" "%STAGE_DIR%\" >nul
powershell -NoProfile -Command "Compress-Archive -Path '%STAGE_DIR%\\*' -DestinationPath '%ZIP_PATH%' -Force"

if errorlevel 1 (
  echo.
  echo ZIP packaging failed.
  pause
  exit /b 1
)

echo.
echo Build complete.
echo Module package ready in: "%STAGE_DIR%"
echo ZIP package ready in : "%ZIP_PATH%"
echo Use the ZIP in host Install Module, or copy the folder into host modules as "modules\example_module\"
pause
