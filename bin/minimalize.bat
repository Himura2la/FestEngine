pushd FestEngine

del libvlc*
rd /S /Q plugins

copy "..\Install.bat" "Install.bat"

popd
