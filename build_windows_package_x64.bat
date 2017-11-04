c:\Python27\Scripts\pyinstaller.exe --distpath=.\build_x64\ --onefile antifier.py
c:\Python27\Scripts\pyinstaller.exe --distpath=.\build_x64\ --onefile tacx_trainer_debug.py
c:\Python27\Scripts\pyinstaller.exe --distpath=.\build_x64\ --onefile power_curve.py
rd /s /q .\build
iexpress /N antifier_package_x64.SED
