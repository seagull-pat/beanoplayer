"C:\Python27\scripts\pyinstaller.exe" --distpath "pyinstaller" --workpath "pyinstaller\work" --icon "player\resource\icon.ico" --noconfirm --windowed --name BeanoPlayer player\player.py 

echo D | xcopy player\resource pyinstaller\BeanoPlayer\resource

pause