import sys
import os
import subprocess
from winreg import *

name = 'FestEngine'
sources_path = '..\\src'
main_file = 'main.pyw'

pyinst_flags = ['--clean', '--windowed', '-y', main_file]

vlc_binaries = {'libvlc.dll': '.',
                'libvlccore.dll': '.',
                'plugins': 'plugins'}

self_name = os.path.basename(sys.argv[0])
print("--------------- %s started! ---------------" % self_name)

if len(sys.argv) == 2:
    vlc_path = sys.argv[1]
elif len(sys.argv) > 2:
    print("Usage: python %s [vlc_path]" % self_name)
    exit(1)
else:
    try:
        with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as reg:
            with OpenKey(reg, "Software\\VideoLAN\\VLC") as key:
                vlc_path = QueryValueEx(key, "InstallDir")[0]
        if not os.path.isdir(vlc_path):
            raise OSError()
    except OSError as e:
        import platform
        print("No VLC found. Install the %s VLC or pass the path to VLC as a parameter." % platform.architecture()[0])
        exit(1)

print("Using VLC installation: %s" % vlc_path)


vlc_binaries = sum([['--add-binary', '%s;%s' % (os.path.join(vlc_path, src_path), tgt_path)]
                for src_path, tgt_path in vlc_binaries.items()], [])

dist_path = os.path.abspath(os.curdir)
os.chdir(sources_path)

pyinst_cmd = ['pyinstaller', '-n', name, '--distpath', dist_path] + vlc_binaries + pyinst_flags

print("Running:", " ".join(pyinst_cmd))

p = subprocess.Popen(pyinst_cmd)
