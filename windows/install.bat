@echo off
setlocal
rem Eye of Creation - Windows screensaver installer
rem Copies the .scr and the video to %LOCALAPPDATA%\EyeOfCreation and opens
rem the Screen Saver settings with Eye of Creation selected.

set "SRC=%~dp0"
set "DEST=%LOCALAPPDATA%\EyeOfCreation"

if not exist "%SRC%EyeOfCreation.scr" (
  echo [!] EyeOfCreation.scr not found next to this script.
  goto :fail
)
if not exist "%SRC%..\assets\EyeOfCreation.mp4" (
  echo [!] assets\EyeOfCreation.mp4 not found. Download the whole repository, not just this folder.
  goto :fail
)

if not exist "%DEST%" mkdir "%DEST%"
copy /Y "%SRC%EyeOfCreation.scr" "%DEST%\EyeOfCreation.scr" >nul || goto :fail
copy /Y "%SRC%..\assets\EyeOfCreation.mp4" "%DEST%\EyeOfCreation.mp4" >nul || goto :fail

rem Remove the "downloaded from the internet" mark so Windows doesn't block it
powershell -NoProfile -Command "Get-ChildItem -LiteralPath '%DEST%' | Unblock-File" >nul 2>&1

echo Installed to %DEST%
echo Opening Screen Saver settings...
rundll32.exe desk.cpl,InstallScreenSaver "%DEST%\EyeOfCreation.scr"
goto :eof

:fail
echo Installation failed.
pause
exit /b 1
