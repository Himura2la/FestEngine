param (
    [string]$vlc = "$env:PROGRAMFILES\\VideoLAN\\VLC"
)

echo "Using VLC installation: $vlc"

cd ..\src
& pyinstaller -n FestEngine --distpath ..\bin --workpath ..\tmp --add-binary "$vlc\libvlc.dll;." --add-binary "$vlc\libvlccore.dll;." --add-binary "$vlc\plugins;plugins" --clean --windowed -y main.pyw
cd ..
