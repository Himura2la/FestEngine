@echo off

set KEY_NAME="HKLM\Software\VideoLAN\VLC"
set VALUE_NAME=InstallDir

FOR /F "tokens=* USEBACKQ" %%F IN (`python -c "import platform; print(platform.architecture()[0][0:2])"`) DO ( 
    set PYTHON_ARCH=%%F
)
if not defined PYTHON_ARCH (
    echo Install Python first, the architecture is determined from it
    exit 1
)

set VLC_PATH=%1

:: Searching for VLC
if not defined VLC_PATH (
    FOR /F "usebackq skip=2 tokens=1-2*" %%A IN (`REG QUERY %KEY_NAME% /v %VALUE_NAME% /reg:%PYTHON_ARCH% 2^>nul`) DO (
        set VLC_PATH=%%C
    )
    if not defined VLC_PATH (
        echo '%KEY_NAME%\%VALUE_NAME%' not found in the registry. Check if VLC is installed or provide the path as an argument.
        exit 1
    )
)

echo Using VLC installation: %VLC_PATH%

cd ..\src
pyinstaller -n FestEngine --distpath ..\bin --workpath ..\tmp ^
            --add-binary "%VLC_PATH%\libvlc.dll";. ^
            --add-binary "%VLC_PATH%\libvlccore.dll";. ^
            --add-binary "%VLC_PATH%\plugins";plugins ^
            --windowed --clean -y main.pyw
cd ..
rd /S /Q tmp
pause
