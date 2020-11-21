import sys
import os
import subprocess
import time
import argparse

name = 'FestEngine'
bin_path = os.getcwd()
sources_path = os.path.join('..', 'src')
main_file = 'main.pyw'
appimage_excludelist_url = 'https://raw.githubusercontent.com/AppImage/AppImages/master/excludelist'

pyinst_flags = ['--clean', '-y', main_file]

parser = argparse.ArgumentParser()
parser.add_argument('vlc_path', nargs='?')
parser.add_argument('-debug', action='store_true', help='Debug mode with console window')
parser.add_argument('-novlc', action='store_true', help='Build completely without VLC')
args = parser.parse_args()

if args.debug:
    name = 'FestEngine-debug'
else:
    pyinst_flags.insert(1, '--windowed')

print("---------------Building %s! ---------------" % name)

vlc_binaries = []
vlc_path = None

if sys.platform.startswith('linux'):
    pyinst_flags.insert(0, '--strip')

elif sys.platform == "win32" and not args.novlc:
    if args.vlc_path:
        vlc_path = args.vlc_path[0]
    else:   # Trying to search find VLC
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

    vlc_binaries = sum([['--add-binary', '%s;%s' % (src_path, tgt_path)]
                        for src_path, tgt_path in vlc_binaries.items()], [])
else:
    print("Sorry, your platform is not supported")
    exit(1)
dist_path = os.path.abspath(os.curdir)
os.chdir(sources_path)

hidden_imports = ['wx._adv', 'wx._html', 'wx._xml']
hidden_imports = sum((['--hidden-import', i] for i in hidden_imports), [])

pyinst_cmd = ['pyinstaller', '-n', name, '--distpath', dist_path] + vlc_binaries + hidden_imports + pyinst_flags

print("Running:", " ".join(pyinst_cmd))

p = subprocess.Popen(pyinst_cmd)

t = 0
while p.poll() is None:
    time.sleep(1)
    t += 1
    if t % 10 == 0:
        print("--- Still building... %ds passed." % t)

print("--------------- Built in %ds with exitcode %d! ---------------" % (t, p.poll()))

if p.poll() == 0:
    os.chdir(os.path.join(bin_path, name))
    if sys.platform.startswith('linux'):
        print("--- Cleaning extra libs according to the AppImage excludelibs list...")
        import urllib.request
        exclude_libs = urllib.request.urlopen(appimage_excludelist_url).read()
        exclude_libs = [e.rsplit('.so', 1)[0] for e in exclude_libs.decode().split('\n') if e and e[0] != '#']
        exclude_libs += ['libvlc', 'libvlccore']
        exclude_libs.append('libharfbuzz')  # https://github.com/AppImage/AppImageKit/issues/454
        all_files = os.listdir()
        libs_to_exclude = list(filter(lambda f: any([f.startswith(l) for l in exclude_libs]), all_files))
    if sys.platform == "win32":
        print("--- Cleaning non-GPL Microsoft DLLs...")
        from glob import glob
        libs_to_exclude = ['MSVCP140.dll', 'VCRUNTIME140.dll'] + glob('api-ms-*')
    print("--- Removing:", libs_to_exclude)
    [os.remove(lib) for lib in libs_to_exclude]

plugins_cache = os.path.join(bin_path, name, 'plugins', 'plugins.dat')
if os.path.isfile(plugins_cache):
    os.remove(plugins_cache)

print("--------------- Ready! ---------------")
