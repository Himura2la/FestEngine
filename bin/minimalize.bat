pushd FestEngine

del MSVCP140.dll VCRUNTIME140.dll
del api-ms-*
del libvlc*
rd /S /Q plugins

copy "..\Install.bat" "Install.bat"

popd
