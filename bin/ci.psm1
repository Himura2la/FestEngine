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

    $env:Path += ";$env:PYTHON_PATH;$env:PYTHON_PATH\Scripts"
    pip install pyinstaller python-vlc wxpython pywinauto
}


function FestEngineBuild {
    pushd '.\bin'

    echo '--- Building a Full version ---'
    python build.py

    echo '--- Building a Debug version ---'
    python build.py -d

    popd
}

function FestEngineCleanProprietaryLibs {
    echo '--- Cleaning MS DLLs ---'

    pushd '.\bin\FestEngine-debug'
    Remove-Item MSVCP140.dll, VCRUNTIME140.dll, api-ms-*

    cd '..\FestEngine'
    Remove-Item MSVCP140.dll, VCRUNTIME140.dll, api-ms-*

    popd
}

function FestEnginePackage {
    echo '--- Building Localization and Packing ---'

    if ($env:ARCH -eq '64') {
        echo '--- Preparing a Debug version ---'
        cd '.\bin\FestEngine-debug'
        BuildLocalization
        echo '--- Packing a Debug version ---'
        7z a "..\festengine-$env:VER-win$env:ARCH-VLCv$env:VLC_VERSION-debug.zip" *
    }

    echo '--- Preparing a Full version ---'
    cd '.\bin\FestEngine'
    BuildLocalization
    echo '--- Packing a Full version ---'
    7z a "..\festengine-$env:VER-win$env:ARCH-VLCv$env:VLC_VERSION-full.zip" *
    
    if ($env:VLC -eq 'latest') {
        echo '--- Minimalizing a Full version ---'
        cd '.\bin\'
        .\minimalize.bat
        echo '--- Packing a Minimal version ---'
        7z a '.\festengine-$env:VER-win$env:ARCH-minimal.zip' '.\FestEngine\*'
    }
}

function BuildLocalization {
    New-Item -Path '.\locale\ru\LC_MESSAGES' -ItemType Directory
    python $env:PYTHON_PATH\Tools\i18n\msgfmt.py -o '.\locale\ru\LC_MESSAGES\main.mo' '.\src\locale\ru\LC_MESSAGES\main.po'
}

Export-ModuleMember -Function FestEngine*