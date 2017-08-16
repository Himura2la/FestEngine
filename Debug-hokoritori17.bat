:: encoding: cp866
cd src
py -2 main.pyw ^
    --filename_re "^(?P<nom>.*?)\. (?P<nicks>.*?) - (?P<name>.*?)( \(ID(?P<num>\d{1,3})\))?$" ^
    --zad_dir "H:\HokoriToriLocal\Fest\zad" ^
    --mp3_dir "H:\HokoriToriLocal\Fest\tracks" ^
    --background_mp3_dir "H:\HokoriToriLocal\Fest\background" ^
    --auto_load_files --debug_output
pause