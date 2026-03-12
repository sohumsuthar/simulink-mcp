@echo off
echo === Simulink MCP Server Setup ===
echo.

REM --- Configure these paths for your system ---
REM Python 3.11 is required for MATLAB R2024a Engine
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found in PATH. Set PYTHON below to your Python 3.11 path.
    pause
    exit /b 1
)
set PYTHON=python

REM Auto-detect MATLAB installation
set MATLAB_ENGINE=
for /d %%D in ("C:\Program Files\MATLAB\R*") do (
    if exist "%%D\extern\engines\python" set MATLAB_ENGINE=%%D\extern\engines\python
)
if "%MATLAB_ENGINE%"=="" (
    echo ERROR: MATLAB installation not found. Install MATLAB with Simulink first.
    pause
    exit /b 1
)
echo Found MATLAB Engine at: %MATLAB_ENGINE%

echo.
echo [1/3] Installing MATLAB Engine for Python...
cd "%MATLAB_ENGINE%"
"%PYTHON%" -m pip install .
if errorlevel 1 (
    echo ERROR: MATLAB engine installation failed. Try running as Administrator.
    pause
    exit /b 1
)

echo.
echo [2/3] Installing MCP dependencies...
cd /d "%~dp0"
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Verifying MATLAB engine...
"%PYTHON%" -c "import matlab.engine; print('MATLAB engine OK')"
if errorlevel 1 (
    echo ERROR: MATLAB engine verification failed.
    pause
    exit /b 1
)

echo.
echo === Setup complete! ===
echo.
echo Add the following to your Claude Desktop config
echo (~~/.config/claude/claude_desktop_config.json or equivalent):
echo.
echo "simulink": {
echo   "command": "python",
echo   "args": ["%~dp0server.py"],
echo   "env": {
echo     "SIMULINK_MCP_WORKDIR": "C:/path/to/your/working/directory"
echo   }
echo }
echo.
pause
