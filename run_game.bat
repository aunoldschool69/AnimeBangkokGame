@echo off
title Thailand Toy Tour 2.5D Board Game - Dev Server
echo ====================================================================
echo             THAILAND TOY TOUR 2.5D BOARD GAME PROTOTYPE
echo ====================================================================
echo.

:: Check if server.py exists and execute it
if exist server.py (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        echo [OK] Running server.py with 'py'...
        py server.py
        goto end
    )
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        echo [OK] Running server.py with 'python'...
        python server.py
        goto end
    )
)

:: Inline fallback if server.py is missing
where py >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] starting server inline using 127.0.0.1:8000
    start "" "http://127.0.0.1:8000"
    py -m http.server 8000 --bind 127.0.0.1
    goto end
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] starting server inline using 127.0.0.1:8000
    start "" "http://127.0.0.1:8000"
    python -m http.server 8000 --bind 127.0.0.1
    goto end
)

:: If neither is found
echo ====================================================================
echo [ERROR] ไม่พบการติดตั้ง Python (Neither 'py' nor 'python' was found)
echo ====================================================================
echo.
echo Please install Python and check 'Add Python to PATH' or run:
echo    npx http-server ./ -p 8000
echo.
pause

:end
pause
