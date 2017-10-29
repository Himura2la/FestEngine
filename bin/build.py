import sys
import os
import subprocess
import time

name = 'FestEngine'
sources_path = os.path.join('..', 'src')
main_file = 'main.pyw'

pyinst_flags = ['--clean', '--windowed', '-y', main_file]

self_name = os.path.basename(sys.argv[0])
print("--------------- %s started! ---------------" % self_name)

vlc_path = None

if sys.platform.startswith('linux'):  # Linux
    vlc_plugins_path = subprocess.check_output(['locate', '-n', '1', 'vlc/plugins']).strip()
    libvlc_path = subprocess.check_output(['locate', '-n', '1', 'libvlc.so']).strip()
    libvlccore_path = subprocess.check_output(['locate', '-n', '1', 'libvlccore.so']).strip()

    if not os.path.isdir(vlc_plugins_path) or \
            not os.path.isfile(libvlc_path) or \
            not os.path.isfile(libvlccore_path):
        vlc_path = None
        print("VLC not found. Try to run 'sudo updatedb' if you just installed it.")
        exit(1)

    vlc_plugins_path = vlc_plugins_path.decode().split('plugins', 1)[0] + 'plugins'
    libvlc_path = libvlc_path.decode()
    libvlccore_path = libvlccore_path.decode()
    vlc_binaries = {libvlc_path: '.',
                    libvlccore_path: '.',
                    vlc_plugins_path: 'plugins'}

    print("Discovered VLC: \n- %s\n- %s\n- %s" % (libvlc_path, libvlccore_path, vlc_plugins_path))

elif sys.platform == "win32":  # Windows
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

vlc_binaries = sum([['--add-binary', '%s:%s' % (src_path, tgt_path)]
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
