"C:\Python27\scripts\pyinstaller.exe" --distpath "pyinstaller" --workpath "pyinstaller\work" --specpath "pyinstaller\spec" 	--noconfirm --windowed --name BeanoPlayer --icon "player\resource\icon.ico" player\player.py 

echo D | xcopy player\resource pyinstaller\BeanoPlayer\resource

pause