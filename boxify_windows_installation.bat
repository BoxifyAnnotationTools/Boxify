@echo off
setlocal

cd /d %~dp0

set FAILED=0
set TORCH_STATUS=SUCCESS
set GPU_TYPE=CPU
set ARCH=x64

echo.
echo ==========================================
echo         Thx for Choosing Boxify
echo ==========================================
echo         system initializing...
echo ==========================================
echo.

:: ─────────────────────────────
:: 1. System Scan
:: ─────────────────────────────
echo [*] System Scanning...

:: Detect ARM
echo %PROCESSOR_ARCHITECTURE% | findstr /i "ARM" >nul
if %ERRORLEVEL% equ 0 (
    set ARCH=ARM
    echo [!] Detected Windows on ARM.
)

:: Detect NVIDIA (simple & safe)
powershell -NoProfile -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name" | findstr /i "NVIDIA RTX GTX TESLA A100 H100 V100 T4 P100 L40" >nul

if not errorlevel 1 (
    set GPU_TYPE=NVIDIA
    echo [OK] NVIDIA GPU detected.
) else (
    echo [!] No NVIDIA GPU detected. Using CPU mode.
)

:: ─────────────────────────────
:: 2. Check Python
:: ─────────────────────────────
echo [1/6] Checking Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [!] Python not found. Installing...
    winget install Python.Python.3.11 -e
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install Python
        set FAILED=1
        goto END
    )
)

:: ─────────────────────────────
:: 3. Virtual Environment
:: ─────────────────────────────
echo [2/6] Managing virtual environment...

if not exist "%~dp0venv\Scripts\activate.bat" (
    echo [*] Creating virtual environment...
    python -m venv "%~dp0venv"
)

if not exist "%~dp0venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment creation failed.
    set FAILED=1
    goto END
)

call "%~dp0venv\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment.
    set FAILED=1
    goto END
)

:: ─────────────────────────────
:: 4. Install PyTorch
:: ─────────────────────────────
echo [3/6] Configuring AI Engine...

:: Handle ARM first
if "%ARCH%"=="ARM" goto TORCH_ARM

:: Handle NVIDIA
if "%GPU_TYPE%"=="NVIDIA" goto TORCH_CUDA

:: Default CPU
goto TORCH_CPU


:TORCH_ARM
echo [!] Skipping PyTorch (ARM not supported).
set TORCH_STATUS=SKIPPED_ARM
goto TORCH_DONE


:TORCH_CUDA
echo [*] Installing PyTorch (CUDA 12.1)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 (
    echo [WARN] PyTorch install failed.
    set TORCH_STATUS=FAILED
)
goto TORCH_DONE


:TORCH_CPU
echo [*] Installing PyTorch (CPU)...
pip install torch torchvision torchaudio
if errorlevel 1 (
    echo [WARN] PyTorch install failed.
    set TORCH_STATUS=FAILED
)
goto TORCH_DONE


:TORCH_DONE

:: ─────────────────────────────
:: 5. Other Dependencies
:: ─────────────────────────────
echo.
echo [4/6] Installing dependencies...
python -m pip install --upgrade pip setuptools wheel
python -m pip install ultralytics pyinstaller streamlit yt-dlp
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dependency installation failed.
    set FAILED=1
    goto END
)

:: ─────────────────────────────
:: 6. Shortcut
:: ─────────────────────────────
echo.
echo [5/6] Creating shortcut...

set SCRIPT=%~dp0utils\Annotator.py
set SHORTCUT=%~dp0Boxify.lnk

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%'); ^
$s.TargetPath='%~dp0venv\Scripts\python.exe'; ^
$s.Arguments='\"%SCRIPT%\"'; ^
$s.WorkingDirectory='%~dp0'; ^
$s.IconLocation='%~dp0assets\boxify.ico'; ^
$s.Save()"

:: ─────────────────────────────
:: FINAL
:: ─────────────────────────────
echo.
echo ==========================================
if %FAILED% equ 1 (
    echo           INSTALLATION FAILED
) else (
    echo           Boxify is ready!
)
echo ==========================================

if "%TORCH_STATUS%"=="SKIPPED_ARM" (
    echo [NOTICE] ARM detected - AI disabled.
) else if "%GPU_TYPE%"=="CPU" (
    echo [NOTICE] Running in CPU mode.
) else if "%TORCH_STATUS%"=="FAILED" (
    echo [WARNING] PyTorch failed.
)

echo.
echo Launch: Boxify.lnk
echo ==========================================

goto FINISH

:END
echo.
echo Installation stopped due to error.
pause
exit

:FINISH
pause