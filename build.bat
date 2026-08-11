@echo off
setlocal
title Rilleras Converter - Build
cd /d "%~dp0"

echo.
echo  ===========================================
echo    Rilleras Converter - Release build
echo  ===========================================
echo.
echo  This produces:
echo    1. installer\Output\RillerasConverterSetup.exe  (what you give people)
echo    2. dist\RillerasConverter.exe                   (portable, no install)
echo.
echo  Expect this to take several minutes.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo  No virtual environment found. Run setup.bat first.
    echo.
    pause
    exit /b 1
)

set "VPY=%CD%\.venv\Scripts\python.exe"

echo  [1/4] Installing build tools...
"%VPY%" -m pip install --upgrade pyinstaller --disable-pip-version-check --quiet
if errorlevel 1 (
    echo  Could not install PyInstaller.
    goto fail
)

echo  [2/4] Building the installer payload (folder build, fast startup)...
"%VPY%" -m PyInstaller --noconfirm --clean --log-level WARN RillerasConverter-onedir.spec
if errorlevel 1 (
    echo  Folder build failed.
    goto fail
)

echo  [3/4] Building the portable single-file exe...
"%VPY%" -m PyInstaller --noconfirm --log-level WARN RillerasConverter.spec
if errorlevel 1 (
    echo  Portable build failed.
    goto fail
)

echo  [4/4] Building the Windows installer...
call :find_iscc
if not defined ISCC (
    echo.
    echo  Inno Setup was not found, so Setup.exe could not be built.
    echo  Install it and run build.bat again:
    echo      winget install JRSoftware.InnoSetup
    echo  The portable exe in dist\ is still ready to use.
    goto done
)

"%ISCC%" /Q "installer\RillerasConverter.iss"
if errorlevel 1 (
    echo  Installer build failed.
    goto fail
)

echo.
echo  ===========================================
echo    Build complete
echo  ===========================================
echo.
echo  Installer : %CD%\installer\Output\RillerasConverterSetup.exe
echo  Portable  : %CD%\dist\RillerasConverter.exe
echo.
echo  Give people the installer. It needs no admin rights and adds
echo  Start Menu and Desktop shortcuts plus an uninstaller.
goto done

:done
echo.
pause
exit /b 0

:fail
echo.
pause
exit /b 1

rem ------------------------------------------------------------ subroutine --
:find_iscc
set "ISCC="
for %%D in (
    "%ProgramFiles(x86)%\Inno Setup 6"
    "%ProgramFiles%\Inno Setup 6"
    "%LOCALAPPDATA%\Programs\Inno Setup 6"
) do (
    if exist "%%~D\ISCC.exe" (
        set "ISCC=%%~D\ISCC.exe"
        goto :eof
    )
)
exit /b 0
