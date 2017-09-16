:: encoding: cp866
cd src
python main.pyw ^
    --filename_re "^(?P<num>\d{3}) (?P<nom>.*?)\. (?P<nicks>.*?) - (?P<name>.*?)( \(ID(?P<id>\d{1,3})\))?$" ^
    --background_tracks_dir "E:\Fest\background" ^
    --background_zad_path "E:\Fest\ht17_bg.jpg" ^
    --auto_load_files --debug_output
    "E:\Fest\zad" "E:\Fest\tracks"