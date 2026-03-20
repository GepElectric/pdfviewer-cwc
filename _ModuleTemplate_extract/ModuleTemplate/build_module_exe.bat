@echo off
setlocal

for %%I in ("%~dp0.") do set "ROOT=%%~fI"
cd /d "%ROOT%"

echo Building MediaModule EXE...
echo Working directory: "%ROOT%"

python -m PyInstaller --noconfirm --clean --windowed --onedir --name MediaModule --paths "%ROOT%" --paths "%ROOT%\media_module" "%ROOT%\main.py"

if errorlevel 1 (
  echo.
  echo Build failed.
  pause
  exit /b 1
)

set STAGE_DIR=%ROOT%\dist\media_module_package
set ZIP_PATH=%ROOT%\dist\MediaModule.zip
if exist "%STAGE_DIR%" rmdir /s /q "%STAGE_DIR%"
mkdir "%STAGE_DIR%"
if exist "%ZIP_PATH%" del /q "%ZIP_PATH%"

xcopy "%ROOT%\dist\MediaModule" "%STAGE_DIR%\MediaModule" /e /i /y >nul
copy "%ROOT%\module.json" "%STAGE_DIR%\" >nul
copy "%ROOT%\requirements.txt" "%STAGE_DIR%\" >nul
copy "%ROOT%\README.md" "%STAGE_DIR%\" >nul
powershell -NoProfile -Command ^
  "Start-Sleep -Seconds 2; " ^
  "Add-Type -AssemblyName System.IO.Compression.FileSystem; " ^
  "$stage = '%STAGE_DIR%'; " ^
  "$zip = '%ZIP_PATH%'; " ^
  "if (Test-Path $zip) { Remove-Item $zip -Force }; " ^
  "$archive = [System.IO.Compression.ZipFile]::Open($zip, 'Create'); " ^
  "Get-ChildItem $stage -File -Recurse | ForEach-Object { " ^
  "  $entry = $_.FullName.Substring($stage.Length + 1).Replace('\','/'); " ^
  "  [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $_.FullName, $entry, 'Optimal') | Out-Null " ^
  "}; " ^
  "$archive.Dispose()"

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
echo Use the ZIP in host Install Module, or copy the folder into host modules as "modules\media_module\"
pause
