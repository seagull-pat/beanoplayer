"C:\Python27\scripts\pyinstaller.exe" --distpath "pyi" --workpath "pyi\work" --noconfirm --windowed --name BeanoPlayer --icon "player\resource\icon.ico" player\player.py 

echo D | xcopy player\resource pyi\BeanoPlayer\resource

pause