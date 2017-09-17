set VLC_PATH=C:\Program Files (x86)\VideoLAN\VLC
cd ..\src
pyinstaller -n FestEngine --distpath ..\bin --workpath ..\tmp ^
            --add-binary "%VLC_PATH%\libvlc.dll";. ^
            --add-binary "%VLC_PATH%\libvlccore.dll";. ^
            --add-binary "%VLC_PATH%\plugins";plugins ^
            --windowed --clean -y main.pyw
cd ..
rd /S /Q tmp
pause
