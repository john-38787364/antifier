c:\Python27\Scripts\pyinstaller.exe --distpath=.\build_x32\ --onefile antifier.py
c:\Python27\Scripts\pyinstaller.exe --distpath=.\build_x32\ --onefile tacx_trainer_debug.py
c:\Python27\Scripts\pyinstaller.exe --distpath=.\build_x32\ --onefile power_curve.py
rd /s /q .\build
iexpress /N antifier_package_x32.SED
del *.spec
