@echo off

fsutil dirty query %SYSTEMDRIVE% >nul
If ERRORLEVEL 1 (
   echo Run me as Administrator, please :3
   pause
   exit 1
)

for /f "usebackq tokens=1 skip=1 delims=-" %%A in (`wmic os get osarchitecture 2^>nul`) DO (
    set ARCH=%%A
    goto heaven
)
:heaven

set KEY_NAME=HKLM\Software\VideoLAN\VLC
set VALUE_NAME=InstallDir

:: Searching for VLC
for /f "usebackq skip=2 tokens=1-2*" %%A in (`reg query %KEY_NAME% /v %VALUE_NAME% /reg:64 2^>nul`) do (
    set VLC_PATH=%%C
    set FOUND_ARCH=64
)
if not defined VLC_PATH (
    for /f "usebackq skip=2 tokens=1-2*" %%A in (`reg query %KEY_NAME% /v %VALUE_NAME% /reg:32 2^>nul`) do (
        set VLC_PATH=%%C
        set FOUND_ARCH=32
    )
    if not defined VLC_PATH (
        echo VLC not found. Please, install %ARCH%bit VLC ^(https://www.videolan.org/vlc/index.ru.html^) or use the Full verson.
        goto hell
    )
)

if %ARCH% NEQ %FOUND_ARCH% (
    echo You have only %FOUND_ARCH%bit VLC. Please, install %ARCH%bit VLC ^(https://www.videolan.org/vlc/index.ru.html^) or use the Full verson.
    goto hell
)

echo Using VLC installation: %VLC_PATH%

cd /D "%~dp0"

mklink libvlc.dll "%VLC_PATH%\libvlc.dll"
mklink libvlccore.dll "%VLC_PATH%\libvlccore.dll"
mklink /D plugins "%VLC_PATH%\plugins"

:hell
pause
