@echo off
setlocal
title Rilleras Converter - Build
cd /d "%~dp0"

echo.
echo  ===========================================
echo    Building RillerasConverter.exe
echo  ===========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo  No virtual environment found. Run setup.bat first.
    echo.
    pause
    exit /b 1
)

set "VPY=%CD%\.venv\Scripts\python.exe"

echo  Installing build tools...
"%VPY%" -m pip install --upgrade pyinstaller --disable-pip-version-check --quiet
if errorlevel 1 (
    echo  Could not install PyInstaller.
    pause
    exit /b 1
)

echo  Packaging (this takes a few minutes)...
echo.
"%VPY%" -m PyInstaller --noconfirm --clean RillerasConverter.spec
if errorlevel 1 (
    echo.
    echo  Build failed.
    pause
    exit /b 1
)

echo.
echo  Built: %CD%\dist\RillerasConverter.exe
echo.

rem ------- optional: wrap the exe in a Windows installer using Inno Setup --
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    echo  Inno Setup not found - skipping installer build.
    echo  To also produce Setup.exe, install it from https://jrsoftware.org/isdl.php
    echo  and run build.bat again.
    goto done
)

echo  Building the Windows installer...
"%ISCC%" "installer\RillerasConverter.iss"
if errorlevel 1 (
    echo  Installer build failed.
    goto done
)
echo.
echo  Installer: %CD%\installer\Output\RillerasConverterSetup.exe

:done
echo.
pause
exit /b 0
