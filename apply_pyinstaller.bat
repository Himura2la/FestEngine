@echo OFF

setlocal
set KEY_NAME="HKLM\Software\VideoLAN\VLC"
set VALUE_NAME=InstallDir

if not defined VLC_PATH (
    FOR /F "usebackq skip=2 tokens=1-2*" %%A IN (`REG QUERY %KEY_NAME% /v %VALUE_NAME% 2^>nul`) DO (
        @echo %%C
        set VLC_PATH=%%C
    )

    if not defined VLC_PATH (
        @echo %KEY_NAME%\%VALUE_NAME% not found. Check if VLC is installed or provide the path by setting VLC_PATH environment variable manually.
        exit 1
    )
)

@echo Using VLC path = %VLC_PATH%
pyinstaller --name FestEngine --add-binary "%VLC_PATH%\libvlc.dll";. --add-binary "%VLC_PATH%\libvlccore.dll";. --add-binary "%VLC_PATH%\plugins";plugins --windowed -y src/main.pyw
endlocal