import sys
import os
import subprocess
import time

name = 'FestEngine'
sources_path = os.path.join('..', 'src')
main_file = 'main.pyw'

pyinst_flags = ['--clean', '--windowed', '-y', main_file]
appimage_excludelist_url = 'https://raw.githubusercontent.com/AppImage/AppImages/master/excludelist'

self_name = os.path.basename(sys.argv[0])
print("--------------- %s started! ---------------" % self_name)

pyinst_addbinary_sep = ';'
no_vlc = len(sys.argv) == 2 and sys.argv[1] == '-novlc'
vlc_binaries = []
vlc_path = None

if sys.platform.startswith('linux'):
    pyinst_addbinary_sep = ':'
    pyinst_flags.insert(0, '--strip')

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

            print("VLC not found. Install the %s VLC or pass the path to VLC as a parameter." %
                  platform.architecture()[0])
            exit(1)
    print("Using VLC installation: %s" % vlc_path)

    vlc_binaries = sum([['--add-binary', '%s%s%s' % (src_path, pyinst_addbinary_sep, tgt_path)]
                        for src_path, tgt_path in vlc_binaries.items()], [])
else:
    print("Sorry, your platform is not supported")
    exit(1)
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

if p.poll() == 0 and sys.platform.startswith('linux'):
    print("--- Cleaning extra libs according to the AppImage excludelibs list...")
    import urllib.request
    exclude_libs = urllib.request.urlopen(appimage_excludelist_url).read()
    exclude_libs = [e.rsplit('.so', 1)[0] for e in exclude_libs.decode().split('\n') if e and e[0] != '#']
    os.chdir(name)
    all_files = os.listdir()
    libs_to_exclude = filter(lambda f: any([f.startswith(l) for l in exclude_libs]), all_files)
    print("--- Removing:", libs_to_exclude)
    [os.remove(lib) for lib in libs_to_exclude]

print("--------------- Ready! ---------------")
