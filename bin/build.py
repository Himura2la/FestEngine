import sys
import os
import subprocess
import time

name = 'FestEngine'
sources_path = os.path.join('..', 'src')
main_file = 'main.pyw'

pyinst_flags = ['--clean', '--windowed', '-y', main_file]

linux_libs_local = ['libavcodec', 'libavformat', 'libavutil', 'libswscale', 'libvlccore', 'libvlc']  # /usr/local/lib/ or /usr/lib
linux_libs_gnu = ['libx264', 'libmatroska', 'libebml', 'libmpeg2', 'libmpeg2convert', 'libvorbis', 'libvorbisenc', 'libFLAC', 'libva']  # /usr/lib/x86_64-linux-gnu/

# /usr/(local/)lib/vlc/ -> ./vlc
# /usr/(local/)lib/vlc/libvlc_vdpau.so.0.0.0 -> .


def find_libs(names, base_path):
    all_libs = os.listdir(base_path)
    for name in names:
        existing_libs = max(filter(lambda a: name in a, all_libs))
    # TODO

self_name = os.path.basename(sys.argv[0])
print("--------------- %s started! ---------------" % self_name)

pyinst_addbinary_sep = ';'
no_vlc = len(sys.argv) == 2 and sys.argv[1] == '-novlc'

if sys.platform.startswith('linux'):
    pyinst_addbinary_sep = ':'
    pyinst_flags.insert(0, '--strip')
    if not no_vlc:
                
                

        vlc_binaries = {libvlc_path: '.',
                        libvlccore_path: '.',
                        vlc_plugins_path: 'vlc/plugins'}


elif sys.platform == "win32" and not no_vlc:
    if len(sys.argv) == 2:
        vlc_path = sys.argv[1]
    elif len(sys.argv) > 2:
        print("Usage: python %s [vlc_path]" % self_name)
        exit(1)
    else:
        try:
            from winreg import *  # Python 3
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as reg:
                with OpenKey(reg, "Software\\VideoLAN\\VLC") as key:
                    vlc_path = QueryValueEx(key, "InstallDir")[0]
        except OSError as e:
            print(e)
        else:
            vlc_binaries = {'libvlc.dll': '.',
                            'libvlccore.dll': '.',
                            'plugins': 'plugins'}
            vlc_binaries = {os.path.join(vlc_path, src): tgt for src, tgt in vlc_binaries.items()}
        if not vlc_path or not os.path.isdir(vlc_path):
            import platform
            print("VLC not found. Install the %s VLC or pass the path to VLC as a parameter." % platform.architecture()[0])
            exit(1)
    print("Using VLC installation: %s" % vlc_path)

vlc_binaries = [] if no_vlc else sum([['--add-binary', '%s%s%s' % (src_path, pyinst_addbinary_sep, tgt_path)]
                                        for src_path, tgt_path in vlc_binaries.items()], []) 
dist_path = os.path.abspath(os.curdir)
os.chdir(sources_path)

pyinst_cmd = ['pyinstaller', '-n', name, '--distpath', dist_path] + vlc_binaries + pyinst_flags

print("Running:", " ".join(pyinst_cmd))

p = subprocess.Popen(pyinst_cmd)

t = 0
while p.poll() is None:
    time.sleep(1)
    t += 1
    if t % 20 == 0:
        print("--- Still building... %ds passed." % t)

print("--------------- Built in %ds with exitcode %d! ---------------" % (t, p.poll()))
