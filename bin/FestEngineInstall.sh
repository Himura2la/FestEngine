BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -d "$BIN_DIR/plugins" ]; then
    VLC_PLUGIN_PATH="$BIN_DIR/plugins" 
else
    VLC_PLUGIN_PATH=`locate -n 1 vlc/plugins`
fi

if [ ! -d $VLC_PLUGIN_PATH ]; then
    echo "VLC not found. Please, install VLC (https://www.videolan.org/vlc/index.ru.html) or use the Full verson."
    exit 1
fi

echo "VLC_PLUGIN_PATH="$VLC_PLUGIN_PATH" $BIN_DIR/FestEngine" > "FestEngineStart.sh"
chmod +x "FestEngineStart.sh"
echo 'Use "FestEngineStart.sh" to run Fest Engine. You can move it anywhere you like.'
