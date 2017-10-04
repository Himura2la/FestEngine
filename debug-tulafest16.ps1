
$filename_re = "^(?P<num>\d{3}) (?P<nom>\w{1,2})( \[(?P<start>[GW]{1})\])?\. (?P<name>.*?)(\(.(?P<id>\d{1,3})\))?$"
$bg_tracks = "D:\Clouds\ownCloud\DATA\Прошлые Фесты\Yuki no Odori 2016\Fest\background"
$key1 = "--auto_load_files"
$key2 = "--auto_load_bg"
$key3 = "--debug_output"

$dir1 = "D:\Clouds\ownCloud\DATA\Прошлые Фесты\Yuki no Odori 2016\Fest\mp3_numbered"
$dir2 = "D:\Clouds\ownCloud\DATA\Прошлые Фесты\Yuki no Odori 2016\Fest\zad_numbered"

cd src
& pyw main.pyw --filename_re $filename_re --background_tracks_dir $bg_tracks $key1 $key2 $key3 $dir1 $dir2
