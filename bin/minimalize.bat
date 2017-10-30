cd FestEngine

del MSVCP140.dll VCRUNTIME140.dll
del api-ms-*
del libvlc*
rd /S /Q plugins

copy "..\FestEngine Install.bat" "FestEngine Install.bat"
