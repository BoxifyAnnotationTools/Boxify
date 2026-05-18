@echo off
setlocal EnableDelayedExpansion

title Boxify Installer

cd /d %~dp0

:: =========================================================
:: VARIABLES
:: =========================================================
set FAILED=0
set TORCH_STATUS=SUCCESS
set GPU_TYPE=CPU
set ARCH=x64

set PYTHON_VERSION=3.12.10
set PYTHON_FOLDER=Python312
set PYTHON_INSTALLER=%TEMP%\python_installer.exe

:: =========================================================
:: HEADER
:: =========================================================
cls

echo.
echo =========================================================
echo                     BOXIFY INSTALLER
echo =========================================================
echo.
echo This installer will:
echo.
echo  - Install Python 3.12
echo  - Create isolated virtual environment
echo  - Install AI dependencies
echo  - Create desktop shortcut
echo.
echo =========================================================
echo LICENSE INFORMATION
echo =========================================================
echo.
echo Boxify uses the MIT License.
echo.
echo MIT License means:
echo.
echo  - You are free to use the software
echo  - You are free to modify the software
echo  - You are free to distribute the software
echo  - No personal data is collected by this installer
echo  - No files are uploaded anywhere
echo.
echo This installer only installs required dependencies
echo locally on your computer.
echo.
echo =========================================================
echo.

choice /c YN /m "Continue installation?"

if errorlevel 2 (
    echo.
    echo Installation cancelled.
    timeout /t 2 >nul
    exit
)

:: =========================================================
:: INTERNET CHECK
:: =========================================================
echo.
echo [0/6] Checking internet connection...

ping google.com -n 1 >nul

if errorlevel 1 (
    echo [ERROR] No internet connection detected.
    set FAILED=1
    goto END
)

echo [OK] Internet connection detected.

:: =========================================================
:: SYSTEM SCAN
:: =========================================================
echo.
echo [1/6] Scanning system...

:: Detect ARM
echo %PROCESSOR_ARCHITECTURE% | findstr /i "ARM" >nul

if %ERRORLEVEL% equ 0 (
    set ARCH=ARM
    echo [!] Windows ARM detected.
)

:: Detect NVIDIA GPU
powershell -NoProfile -Command "$gpu = Get-CimInstance Win32_VideoController; if($gpu.Name -match 'NVIDIA|RTX|GTX|TESLA'){ exit 0 } else { exit 1 }"

if not errorlevel 1 (
    set GPU_TYPE=NVIDIA
    echo [OK] NVIDIA GPU detected.
) else (
    echo [!] NVIDIA GPU not detected.
    echo [*] CPU mode will be used.
)

:: =========================================================
:: CHECK PYTHON
:: =========================================================
echo.
echo [2/6] Checking Python installation...

py -3.12 --version >nul 2>&1

IF %ERRORLEVEL% NEQ 0 (

    echo [!] Python 3.12 not found.
    echo [*] Downloading Python installer...

    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe' -OutFile '%PYTHON_INSTALLER%'"

    if not exist "%PYTHON_INSTALLER%" (
        echo [ERROR] Failed to download Python installer.
        set FAILED=1
        goto END
    )

    echo [*] Installing Python silently...
    echo [*] This may take a minute...

    start /wait "" "%PYTHON_INSTALLER%" ^
    /quiet ^
    InstallAllUsers=1 ^
    PrependPath=1 ^
    Include_test=0 ^
    Include_launcher=1

    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python installation failed.
        set FAILED=1
        goto END
    )

    echo [OK] Python installed successfully.
)

:: Refresh PATH manually
set "PATH=%PATH%;C:\Program Files\%PYTHON_FOLDER%;C:\Program Files\%PYTHON_FOLDER%\Scripts"

:: Final Python verification
py -3.12 --version >nul 2>&1

IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python still not detected.
    set FAILED=1
    goto END
)

echo [OK] Python detected.

:: =========================================================
:: VIRTUAL ENVIRONMENT
:: =========================================================
echo.
echo [3/6] Preparing virtual environment...

if not exist "%~dp0venv\" (

    echo [*] Creating virtual environment...

    py -3.12 -m venv "%~dp0venv"

    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        set FAILED=1
        goto END
    )
)

if not exist "%~dp0venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment is corrupted.
    set FAILED=1
    goto END
)

call "%~dp0venv\Scripts\activate.bat"

IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment.
    set FAILED=1
    goto END
)

echo [OK] Virtual environment ready.

:: =========================================================
:: UPDATE PIP
:: =========================================================
echo.
echo [4/6] Updating package manager...

python -m pip install --upgrade pip setuptools wheel --retries 5 --timeout 30

IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to update pip.
    set FAILED=1
    goto END
)

:: =========================================================
:: INSTALL PYTORCH
:: =========================================================
echo.
echo [5/6] Installing AI engine...

if "%ARCH%"=="ARM" (
    echo [!] ARM detected.
    echo [!] PyTorch installation skipped.
    set TORCH_STATUS=SKIPPED_ARM
    goto TORCH_DONE
)

echo [*] Installing PyTorch...

pip install torch torchvision torchaudio --retries 5 --timeout 30

if errorlevel 1 (
    echo [WARNING] PyTorch installation failed.
    set TORCH_STATUS=FAILED
)

:TORCH_DONE

:: =========================================================
:: INSTALL OTHER DEPENDENCIES
:: =========================================================
echo.
echo [6/6] Installing Boxify dependencies...

pip install ultralytics pyinstaller streamlit yt-dlp --retries 5 --timeout 30

IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dependency installation failed.
    set FAILED=1
    goto END
)

echo [OK] Dependencies installed successfully.

:: =========================================================
:: CREATE SHORTCUTS
:: =========================================================
echo.
echo [*] Creating Boxify shortcuts...

set "PS_SCRIPT=%TEMP%\boxify_shortcut.ps1"

> "%PS_SCRIPT%" echo $rootPath = Split-Path -Parent "%~f0"
>> "%PS_SCRIPT%" echo $desktop = [Environment]::GetFolderPath('Desktop')
>> "%PS_SCRIPT%" echo $pythonExe = Join-Path $rootPath 'venv\Scripts\python.exe'
>> "%PS_SCRIPT%" echo $scriptPath = Join-Path $rootPath 'utils\Annotator.py'
>> "%PS_SCRIPT%" echo $iconPath = Join-Path $rootPath 'assets\boxify.ico'
>> "%PS_SCRIPT%" echo $rootShortcut = Join-Path $rootPath 'Boxify Launcher.lnk'
>> "%PS_SCRIPT%" echo $desktopShortcut = Join-Path $desktop 'Boxify.lnk'
>> "%PS_SCRIPT%" echo $ws = New-Object -ComObject WScript.Shell

>> "%PS_SCRIPT%" echo $sc1 = $ws.CreateShortcut($rootShortcut)
>> "%PS_SCRIPT%" echo $sc1.TargetPath = $pythonExe
>> "%PS_SCRIPT%" echo $sc1.Arguments = '"' + $scriptPath + '"'
>> "%PS_SCRIPT%" echo $sc1.WorkingDirectory = $rootPath
>> "%PS_SCRIPT%" echo if (Test-Path $iconPath^) { $sc1.IconLocation = $iconPath }
>> "%PS_SCRIPT%" echo $sc1.Save(^)

>> "%PS_SCRIPT%" echo $sc2 = $ws.CreateShortcut($desktopShortcut)
>> "%PS_SCRIPT%" echo $sc2.TargetPath = $rootShortcut
>> "%PS_SCRIPT%" echo if (Test-Path $iconPath^) { $sc2.IconLocation = $iconPath }
>> "%PS_SCRIPT%" echo $sc2.Save(^)

>> "%PS_SCRIPT%" echo Write-Host "[OK] Root launcher created:"
>> "%PS_SCRIPT%" echo Write-Host $rootShortcut
>> "%PS_SCRIPT%" echo Write-Host "[OK] Desktop shortcut created:"
>> "%PS_SCRIPT%" echo Write-Host $desktopShortcut

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"

del "%PS_SCRIPT%" >nul 2>&1

:: =========================================================
:: SUCCESS
:: =========================================================
echo.
echo =========================================================

if %FAILED% equ 1 (
    echo                 INSTALLATION FAILED
) else (
    echo                  BOXIFY IS READY
)

echo =========================================================

if "%TORCH_STATUS%"=="SKIPPED_ARM" (
    echo [NOTICE] ARM platform detected.
    echo [NOTICE] AI acceleration disabled.
)

if "%GPU_TYPE%"=="CPU" (
    echo [NOTICE] Running in CPU mode.
)

if "%TORCH_STATUS%"=="FAILED" (
    echo [WARNING] PyTorch installation failed.
)

echo.
echo Desktop shortcut created:
echo.
echo   Boxify.lnk
echo.
echo Thank you for using Boxify.
echo =========================================================

goto FINISH

:: =========================================================
:: ERROR HANDLER
:: =========================================================
:END

echo.
echo =========================================================
echo                 INSTALLATION FAILED
echo =========================================================
echo.
echo Please check:
echo.
echo  - Internet connection
echo  - Windows permissions
echo  - Antivirus restrictions
echo.
echo Then try again.
echo =========================================================

:: =========================================================
:: EXIT
:: =========================================================
:FINISH

echo.
pause
exit