@echo off
setlocal
title Rilleras Converter - Setup
cd /d "%~dp0"

echo.
echo  ===========================================
echo    Rilleras Converter - Setup
echo  ===========================================
echo.

rem ---------------------------------------------------------------- Python --
call :find_python
if defined PYEXE goto have_python

echo  Python was not found on this PC.
echo  Trying to install it automatically with winget...
echo.
where winget >nul 2>&1
if errorlevel 1 goto no_winget

winget install --id Python.Python.3.12 --source winget --silent --accept-package-agreements --accept-source-agreements --scope user
echo.
call :find_python
if defined PYEXE goto have_python

echo  Python still not detected. Close this window, open a NEW one and run
echo  setup.bat again - a fresh terminal picks up the updated PATH.
goto fail

:no_winget
echo  winget is unavailable. Please install Python 3.10 or newer from
echo    https://www.python.org/downloads/
echo  and tick "Add python.exe to PATH", then run setup.bat again.
goto fail

:have_python
echo  Python : %PYEXE%
"%PYEXE%" --version
echo.

rem ------------------------------------------------------------------ venv --
if exist ".venv\Scripts\python.exe" goto venv_ready
echo  Creating virtual environment (.venv)...
"%PYEXE%" -m venv .venv
if errorlevel 1 (
    echo  Could not create the virtual environment.
    goto fail
)

:venv_ready
set "VPY=%CD%\.venv\Scripts\python.exe"
echo  Installing packages - this can take a few minutes on first run...
echo.
"%VPY%" -m pip install --upgrade pip --disable-pip-version-check --quiet
"%VPY%" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo  Package installation failed. Check your internet connection and retry.
    goto fail
)

rem -------------------------------------------------------------- shortcuts --
echo.
echo  Creating launcher and shortcuts...
> "Rilleras Converter.bat" echo @echo off
>>"Rilleras Converter.bat" echo cd /d "%%~dp0"
>>"Rilleras Converter.bat" echo start "" "%%~dp0.venv\Scripts\pythonw.exe" "%%~dp0RillerasConverter.py"

powershell -NoProfile -ExecutionPolicy Bypass -File "tools\make_shortcuts.ps1" -Root "%CD%"

echo.
echo  ===========================================
echo    Setup complete.
echo  ===========================================
echo.
echo  Start the app from the Desktop shortcut, the Start Menu,
echo  or by running "Rilleras Converter.bat" in this folder.
echo.
choice /C YN /N /M "  Launch Rilleras Converter now? [Y/N] "
if errorlevel 2 goto done
start "" "%CD%\.venv\Scripts\pythonw.exe" "%CD%\RillerasConverter.py"

:done
echo.
pause
exit /b 0

:fail
echo.
pause
exit /b 1

rem ------------------------------------------------------------ subroutine --
:find_python
set "PYEXE="
set "PROBE=%TEMP%\rilleras_python_probe.txt"

py -3 -c "import sys;print(sys.executable)" > "%PROBE%" 2>nul
if not errorlevel 1 set /p PYEXE=<"%PROBE%"
if defined PYEXE goto probe_done

python -c "import sys;print(sys.executable)" > "%PROBE%" 2>nul
if not errorlevel 1 set /p PYEXE=<"%PROBE%"
if defined PYEXE goto probe_done

for /f "delims=" %%P in ('dir /b /s "%LOCALAPPDATA%\Programs\Python\python.exe" 2^>nul') do (
    set "PYEXE=%%P"
    goto probe_done
)
for /f "delims=" %%P in ('dir /b /s "%ProgramFiles%\Python*\python.exe" 2^>nul') do (
    set "PYEXE=%%P"
    goto probe_done
)

:probe_done
del "%PROBE%" >nul 2>&1
exit /b 0
