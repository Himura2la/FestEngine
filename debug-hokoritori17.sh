cd src
python3 main.pyw \
    --filename_re "^(?P<num>\d{3}) (?P<nom>.*?)\. (?P<nicks>.*?) - (?P<name>.*?)( \(ID(?P<id>\d{1,3})\))?$" \
--background_tracks_dir "/media/himura/Data/Фесты/Hokori Tori 2017/Fest/background" \
--background_zad_path "/media/himura/Data/Фесты/Hokori Tori 2017/Fest/ht17_bg.jpg" \
--auto_load_files --debug_output \
"/media/himura/Data/Фесты/Hokori Tori 2017/Fest/zad" "/media/himura/Data/Фесты/Hokori Tori 2017/Fest/tracks" \
