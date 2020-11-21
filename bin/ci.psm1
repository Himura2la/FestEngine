# For use in AppVeyor to build https://github.com/Himura2la/FestEngine

function FestEngineGetDeps {
    if ($env:APPVEYOR_REPO_TAG_NAME) {
        $env:VER = $env:APPVEYOR_REPO_TAG_NAME
    } else {
        $env:VER = $env:APPVEYOR_REPO_COMMIT.substring(0,7)
    }
    if ($env:ARCH -eq '32') {
        $env:PYTHON_PATH = 'C:\Python36'
        $env:VLC_ARCH_FLAG = '--x86'
    } else {
        $env:PYTHON_PATH = 'C:\Python36-x64'
    }
    if ($env:VLC -eq 'latest') {
        $env:VLC_VERSION = ((choco list vlc | Select-String -Pattern '^vlc [\d\.]* \[Approved\]') -split ' ')[1]
        choco install -y --no-progress $env:VLC_ARCH_FLAG vlc
    } else {
        $env:VLC_VERSION = $env:VLC
        choco install -y --no-progress --version $env:VLC_VERSION $env:VLC_ARCH_FLAG vlc
    }

    $env:Path += ";$env:PYTHON_PATH\Scripts"
    & "$env:PYTHON_PATH\python.exe" -m pip install --upgrade pip
    & "$env:PYTHON_PATH\python.exe" -m pip install pyinstaller python-vlc wxpython pywinauto
}


function FestEngineBuild {
    pushd './bin'
    & "$env:PYTHON_PATH\python.exe" build.py
    & "$env:PYTHON_PATH\python.exe" build.py -d
    popd
}

function FestEnginePackage {
    if ($env:ARCH -eq '64') {
        echo '--- Building Localization for Debug version ---'
        BuildLocalization './bin/FestEngine-debug'
        echo '--- Packing a Debug version ---'
        7z a "./bin/festengine-$env:VER-win$env:ARCH-VLCv$env:VLC_VERSION-debug.zip" './bin/FestEngine/*'
    }

    echo '--- Building Localization for a Full version ---'
    BuildLocalization './bin/FestEngine'
    echo '--- Packing a Full version ---'
    7z a "./bin/festengine-$env:VER-win$env:ARCH-VLCv$env:VLC_VERSION-full.zip" './bin/FestEngine/*'
    
    if ($env:VLC -eq 'latest') {
        echo '--- Minimalizing a Full version ---'
        pushd './bin'
        ./minimalize.bat
        echo '--- Packing a Minimal version ---'
        7z a "./festengine-$env:VER-win$env:ARCH-minimal.zip" './FestEngine/*'
        popd
    }
}

function BuildLocalization {
    New-Item -Path './locale/ru/LC_MESSAGES' -ItemType Directory
    & "$env:PYTHON_PATH\python.exe" "$env:PYTHON_PATH\Tools\i18n\msgfmt.py" -o '.\locale\ru\LC_MESSAGES\main.mo' '.\src\locale\ru\LC_MESSAGES\main.po'
}

Export-ModuleMember -Function FestEngine*