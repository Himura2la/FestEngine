:: encoding: cp866
cd src
python main.pyw ^
    --filename_re "^(?P<nom>.*?)\. (?P<nicks>.*?) - (?P<name>.*?)( \(ID(?P<id>\d{1,3})\))?$" ^
    --zad_dir "E:\Fest\zad" ^
    --tracks_dir "E:\Fest\tracks" ^
    --background_tracks_dir "E:\Fest\background" ^
    --background_zad_path "E:\Fest\ht17_bg.jpg" ^
    --auto_load_files --debug_output
