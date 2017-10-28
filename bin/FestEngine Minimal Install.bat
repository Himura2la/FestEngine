@echo off

set KEY_NAME=HKLM\Software\VideoLAN\VLC
set VALUE_NAME=InstallDir

:: Searching for VLC
FOR /F "usebackq skip=2 tokens=1-2*" %%A IN (`REG QUERY %KEY_NAME% /v %VALUE_NAME% /reg:64 2^>nul`) DO (
    set VLC_PATH=%%C
)
if not defined VLC_PATH (
    FOR /F "usebackq skip=2 tokens=1-2*" %%A IN (`REG QUERY %KEY_NAME% /v %VALUE_NAME% /reg:32 2^>nul`) DO (
        set VLC_PATH=%%C
    )
    if not defined VLC_PATH (
        echo "VLC not found. Please, install VLC (https://www.videolan.org/vlc/index.ru.html) or use the Full verson."
        pause
        exit 1
    )
)

fsutil dirty query %SYSTEMDRIVE% >nul
If %errorLevel% NEQ 0 (
   echo Run me as Administrator, please.
   pause
   exit 1
)

echo Using VLC installation: %VLC_PATH%

cd /D "%~dp0"

mklink libvlc.dll "%VLC_PATH%\libvlc.dll"
mklink libvlccore.dll "%VLC_PATH%\libvlccore.dll"
mklink /D plugins "%VLC_PATH%\plugins"

pause