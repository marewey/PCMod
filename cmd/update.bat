@echo off
:: %1=type %2=desired version
:: %1=launcher/pack/empty
set update_type=%1
if not "%update_type%"=="empty" set update_version=%2
::Set variables
call :vars
::Set windows size, title, and color
call :window.settings
::Check for internet
call :net.check
::display current versions
echo.Current Versions:
echo. - Launcher Version: %launcher_version%
echo. - Pack Version: %pack_version%
::check for update if none specified
if "%update_type%"=="empty" call :update.check
::update if specified
if not "%update_type%"=="empty" call :update.user.check %update_type% y
::if no internet, exit
if not "%connection%"=="1" echo.Exiting, due to no internet connection for update.&pause&exit
ping localhost -n 3 >nul
exit

:vars
set ftppass=cnff
set url=markspi.ddns.me
for /f "tokens=1-2 delims==" %%a in ('type settings.txt') do set %%a=%%b
for /f "tokens=1-4 delims=;" %%a in ('type data\indexes\version') do (
	if "%%a"=="%pack%" set pack_version=%%b
	if "%%a"=="Launcher" if "%%c"=="PCMod" set launcher_version=%%b
)
goto :eof
:window.settings
title PCMod Update
color 1a
mode con cols=55 lines=25
goto :eof

:net.check
set /p "=Checking Connection... "<nul
ping %url% -n 1 >nul
if "%errorlevel%"=="1" set connection=0
if "%errorlevel%"=="0" set connection=1
copy nul data\indexes\signature >nul
if "%connection%"=="0" echo.[408] REQUEST TIMEOUT&goto :eof
if "%connection%"=="1" bin\wget -q -T 5 http://%url%/pcmod2/updates/sig -O data\indexes\signature 2>nul
title PCMod
for /f %%z in ('type data\indexes\signature') do set sig=%%z
if "%sig%"=="PCMod" set connection=1
if not "%sig%"=="PCMod" set connection=0
if "%sig%"=="" set connection=-1
if "%connection%"=="1" echo.[200] OK
if "%connection%"=="0" echo.[400] BAD REQUEST
if "%connection%"=="-1" echo.[404] NOT FOUND
if not "%sig%"=="PCMod" if "%1"=="popup" bin\nircmd.exe infobox "Unable to connect to MarksPi Server. Internet/Server Error" "PCMod Error"
goto :eof

:update.check
if "%connection%"=="0" echo.*** No Connection ***&goto :eof
echo.Checking for updates...
bin\wget -q -T 5 http://%url%/pcmod2/version -O data\indexes\version.tmp
title PCMod
set pack_update=
set launcher_update=
for /f "tokens=1-3 delims=;" %%a in ('type data\indexes\version.tmp') do (
	if "%%a"=="%pack%" if not "%%b"=="%pack_version%" set pack_update=%%b
	if "%%a"=="Launcher" if "%%c"=="PCMod" if not "%%b"=="%launcher_version%" set launcher_update=%%b
)
if not "%launcher_update%"=="" call :update.user.check launcher y
if "%launcher_update%"=="" if not "%pack_update%"=="" call :update.user.check pack y
if "%launcher_update%"=="" if "%pack_update%"=="" call :update.user.check empty n
goto :eof

:update.user.check type default_key
if "%1"=="pack" echo.New Pack %pack% Update: %pack_update%
if "%1"=="launcher" echo.New Launcher Update: %launcher_update%
if "%1"=="empty" echo.No Updates Found.
if "%2"=="y" echo.AUTO UPDATING...
if "%2"=="y" echo.You have 8 seconds to cancel with N.
echo.-------------------------------------------------------
echo.D=Pack Downloader M=Refresh Mods Y=Auto Update N=Cancel
echo.L=Launcher Custom Version P=Pack Custom Version
choice /m "Update (Y/N/M/D/P/L):" /c:"pmyndl" /t 8 /d %2
set select=%errorlevel%
echo.-------------------------------------------------------
if "%select%"=="6" call :update.launcher.custom
if "%select%"=="5" call :update.pack.downloader
if "%select%"=="4" echo.Cancelling...
if "%select%"=="3" call :update.auto %1
if "%select%"=="2" call :update.mods
if "%select%"=="1" call :update.pack.custom
if "%pack_download%"=="exit" goto :update.user.check
ping localhost -n 2 >nul
goto :eof

:update.launcher.custom
set /p launcher_update=LAUNCHER VERSION:
if "%launcher_update%"=="" set launcher_update=%launcher_version%
call :update launcher
goto :eof

:update.pack.custom
set /p pack_update=PACK VERSION:
if "%pack_update%"=="" set pack_update=%pack_version%
call :update pack
goto :eof

:update.auto type
if "%1"=="empty" if "%launcher_update%"=="" set launcher_update=%launcher_version%
if "%1"=="empty" if "%pack_update%"=="" set pack_update=%pack_version%
if not "%launcher_update%"=="" call :update launcher&goto :eof
if not "%pack_update%"=="" call :update pack
goto :eof

:update.mods
echo.y|del data\packs\%pack%\mods\*.* >>data\update.log 2>&1
call :update.verify
echo.DONE
goto :eof

:update.pack.downloader
ping localhost -n 3 >nul
cls
echo.Select a Pack to download:
echo.------------------------------------------------------
echo. PACK	^| VERSION 	^| ModLoader 	^| MCVersion
echo.------------------------------------------------------
for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version') do (
	if not "%%a"=="Launcher" (
		if not "%%a"=="Vanilla" (
			set a=0
			for /f "tokens=1 delims=;" %%f in ('type data\indexes\version.tmp') do (
				if "%%a"=="%%f" set a=1
			)
			if exist "data\packs\%%a\PCMod-%%a.pak" (
				if "!a!"=="0" echo.+%%a	^| CUSTOM 	^| %%c 	^| %%d
				if "!a!"=="1" echo.*%%a	^| %%b 	^| %%c 	^| %%d
			) else (
				if "!a!"=="0" echo.?%%a	^| CUSTOM 	^| %%c 	^| %%d
				if "!a!"=="1" echo. %%a	^| %%b 	^| %%c 	^| %%d
			)
		)
	)
)
echo.------------------------------------------------------
echo.Type 'exit' to exit
set /p pack_download=PACK VERSION:
if "%pack_download%"=="exit" goto :eof
call :update.pack.downloader.check pack_check
::0=invalid
::1=fresh pack no download
::2=new pack download				2-4-x.zip
::3=fresh pack download				2-4-x.zip with delete of old pack files
::4=update pack download			2-4-x.zip
if "%pack_check%"=="0" echo.%pack_download% is not a valid pack selection.&goto :update.pack.downloader
if "%pack_check%"=="1" echo.This is a custom pack, no download availible.&goto :update.pack.downloader
md data\update 2>nul
set download=%pack_download%
set download_dir=packs
if "%pack_check%"=="3" echo.Cleaning %pack_download%...&echo.a | rd /s /q data\packs\%pack%\
echo.Downloading %pack_download%...
set pack_=%pack%
set pack=%pack_download%
call :update pack new
::call :update.download pack&echo.
::call :update.extract
::call :update.install.pack
::call :update.verify
set pack=%pack_%
echo.a | rd /s /q data\update\
goto :eof
:update.pack.downloader.check
::checks
set exists=0
set valid=0
set update=0
for /f "tokens=1 delims=;" %%a in ('type data\indexes\version') do if "%%a"=="%pack_download%" set valid=2
if exist "data\packs\%pack_download%\PCMod-%pack%.pak" set exists=1
::logic of the checks
if "%valid%"=="2" if "%exists%"=="1" echo.%pack_download% already exists, do you want to download fresh or update?
if "%valid%"=="2" if "%exists%"=="1" choice /m "Update (U/F):" /c:"uf" /t 8 /d u
if "%valid%"=="2" if "%exists%"=="1" if "%errorlevel%"=="1" set update=1
set /a %1=%valid%+%exists%+%update%
goto :eof




:update type new
copy nul bin\.cancelLaunch >nul
del data\update.log 2>nul
set count=
set count_=
ping localhost -n 2 >nul
::Get the username logged in
for /f %%a in ('type data\indexes\user') do set user=%%a
if "%user%"=="" set user=null
ping localhost -n 2 >nul
if "%connection%"=="0" echo.*** Offline ***&pause >nul&exit
color 1a
cls
if "%pack_update%"=="" for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version.tmp') do if "%pack%"=="%%a" set pack_update=%%b
if "%pack_version%"=="" for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version') do if "%pack%"=="%%a" set pack_version=%%b
if not "%2"=="new" set download=%1
if not "%2"=="new" set download=%download%_!%1_update!
if not "%2"=="new" set download_dir=updates/%1
if not "%2"=="new" if "%1"=="pack" set download_dir=%download_dir%/%pack%
if not "%2"=="new" bin\wget.exe -q -T 5 -O data\packs\%pack%\PCMod-%pack%.pak http://%url%/pcmod2/updates/pack/%pack%/PCMod-%pack%.pak
bin\nircmd.exe win close title "PCMod Launcher - %user%"
echo.--- UPDATE %download% ---
md data\update 2>nul
ping localhost -n 2 >nul
if not "%2"=="new" call :update.verify
call :update.download
color 1a
echo.&echo.Update Downloaded.
call :update.extract
if not "%2"=="new" call :update.backup
call :update.install.%1 %2
call :update.mods.clean
call :update.verify
echo.Updating Modlist...
call cmd\settings.bat modlist >>data\update.log 2>&1
echo.Finalizing Update...
if "%lite%"=="1" call cmd\settings.bat lite 1 >>data\update.log 2>&1
::del %temp%\pcmodsysinfo >>data\update.log 2>&1
echo.Restarting PCMod...
ping localhost -n 3 >nul
::del bin\.cancelLaunch 2>nul
start "" "PCMod.hta"
echo.Cleaning Update...
echo.a | rd /s /q data\update\
ping localhost -n 2 >nul
exit /b
goto :eof
exit

:update.backup
echo.Backing Up data...
mkdir data\backup\%pack%\config\ 2>nul
echo.- CONFIG (Local)
echo.a|xcopy /e data\.minecraft\config\* data\backup\%pack%\config\ >>data\update.log 2>&1
goto :eof

:update.verify
del data\indexes\missingmods.txt 2>nul
del data\indexes\extramods.txt 2>nul
SetLocal EnableDelayedExpansion Enableextensions
set count=0
set count_=0
set /p "=Verifying Modcount..." <nul
::Count the files in the mods folder
for /f "tokens=* delims=*" %%a in ('dir /b /a:-d data\packs\%pack%\mods\ 2^>nul') do set /a count_=!count_!+1
::Count the files listed in the index .pak file
for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do if "%%a"=="U" set /a count=!count!+1&if not exist "data\packs\%pack%\mods\%%b" >>data\indexes\missingmods.txt echo.%%b
for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do if "%%a"=="B" set /a count=!count!+1&if not exist "data\packs\%pack%\mods\%%b" >>data\indexes\missingmods.txt echo.%%b
for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do if "%%a"=="C" set /a count=!count!+1&if not exist "data\packs\%pack%\mods\%%b" >>data\indexes\missingmods.txt echo.%%b
for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do if "%%a"=="D" if exist "data\packs\%pack%\mods\%%b" >>data\indexes\extramods.txt echo.%%b
if "%count%"=="%count_%" echo. OK&echo.%count%/%count_% total mods found.&goto :eof
if not "%count%"=="%count_%" echo.Found %count_% total Mods. %count% Mods requested.&ping localhost -n 9 >nul
if %count_% gtr %count% call :update.mods.clean
if %count% gtr %count_% call :update.mods.download
Endlocal
goto :eof
:update.mods.clean
if exist "data\indexes\extramods.txt" echo.Extra Mods found...&type data\indexes\extramods.txt
echo.Cleaning Mods...
if exist "bin\update\%download%\data\packs\%pack%\PCMod-%pack%.pak" for /f "tokens=1-5 delims=;" %%a in ('type bin\update\%download%\data\packs\%pack%\PCMod-%pack%.pak') do (
	if "%%a"=="D" if exist "data\packs\%pack%\mods\%%b" echo.y|del "data\packs\%pack%\mods\%%b" 2>nul&echo.y|del "data\disablesclimods\%%b" 2>nul&echo.Deleting %%d...
)
for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do (
	if "%%a"=="D" if exist "data\packs\%pack%\mods\%%b" echo.y|del "data\packs\%pack%\mods\%%b" 2>nul&echo.y|del "data\disablesclimods\%%b" 2>nul&echo.Deleting %%d...
)
for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do (
	if "%%a"=="S" if exist "data\packs\%pack%\mods\%%b" echo.y|del "data\packs\%pack%\mods\%%b" 2>nul&echo.y|del "data\disablesclimods\%%b" 2>nul&echo.Deleting %%d...
)
goto :eof
:update.mods.download
if exist "data\indexes\missingmods.txt" echo.Missing Mods found...&type data\indexes\missingmods.txt
echo.Downloading Missing Mods...
for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do (
	if not exist "data\packs\%pack%\mods\%%b" (
		if "%%a"=="C" set /p "=- Downloading %%d..."<NUL&bin\wget.exe -q "http://%url%/pcmod2/mods/%pack%/%%b" -O "data\packs\%pack%\mods\%%b"&call :check.empty %%b
		if "%%a"=="U" set /p "=- Downloading %%d..."<NUL&bin\wget.exe -q "http://%url%/pcmod2/mods/%pack%/%%b" -O "data\packs\%pack%\mods\%%b"&call :check.empty %%b
		if "%%a"=="B" set /p "=- Downloading %%d..."<NUL&bin\wget.exe -q "http://%url%/pcmod2/mods/%pack%/%%b" -O "data\packs\%pack%\mods\%%b"&call :check.empty %%b
	)
)
goto :eof
:check.empty
set checkmod=%*
set size_mod=0000
if not exist "data\packs\%pack%\mods\%checkmod%" call :check.empty.failed&goto :eof
FOR /F "tokens=*" %%A IN ("data\packs\%pack%\mods\%checkmod%") DO set size_mod=%%~zA
if "%size_mod%"=="0" call :check.empty.failed&goto :eof
if %size_mod% lss 1000000 echo. (%size_mod:~0,-3%.%size_mod:~-3,-1% KB)
if %size_mod% geq 1000000 echo. (%size_mod:~0,-6%.%size_mod:~-6,-4% MB)
goto :eof
:check.empty.failed
color 1c
echo. *FAILED*
echo.FILE SIZE IS 0 KB. Please Report this.
ping localhost -n 6 >nul
color 1a
goto :eof

::download= pack_2.4.0 or launcher_2.4.0 or 2-4-x
:update.download
color 1e
::Download the size file
set /p "=Getting File Size... " <nul
bin\wget.exe -q http://%url%/pcmod2/%download_dir%/sizes/%download%.size -O data\update\size&title PCMod Update
::Get Sizes of the file and the listed size
FOR /F "tokens=*" %%A IN ("data\update\%download%.zip") DO set size=%%~zA
for /f %%a in ('type data\update\size') do set size_=%%a
echo.%size_:~0,-6%.%size_:~-6,-4% MB
::If Zip file already exists (and has correct size) skip the download
::echo.SIZE: %size_:~0,-6%.%size_:~-6,-5% MB
if exist "data\update\%download%.zip" if "%size%"=="%size_%" echo.Using offline zip file.&goto :eof
if exist "data\update\%download%.zip" if not "%size%"=="%size_%" echo.Size does not match. (%size:~0,-6%.%size:~-6,-5% MB ~= %size_:~0,-6%.%size_:~-6,-5% MB)&echo.Redownloading...&del data\update\%download%.zip 2>data\update_error.log
echo.Downloading File... (%download%.zip)
start /min bin\wget.exe http://%url%/pcmod2/%download_dir%/%download%.zip -O data\update\%download%.zip
set size=0000000
call :update.download.progress
FOR /F "usebackq" %%A IN ('data\update\%download%.zip') DO set size=%%~zA
::If Zip file has correct size go to next step
if "%size%"=="%size_%" goto :eof
color 1c
if not "%size%"=="%size_%" echo.Size does not match. (%size% ~= %size_%)
set /a retrys=%retrys%+1
echo.Failed to Download file...
echo.Retrying (%retrys%/5)...
ping localhost -n 11 >nul
if "%retrys%"=="5" echo.Download Failed. Please contact Mark at markrewey@gmail.com&pause >nul&exit /b
del data\update\%download%.zip >>data\update.log 2>&1
goto :update.download
:update.download.progress
set /p "=" <nul
set /p "=DOWNLOADED/TOTAL SIZE: %size:~0,-6%.%size:~-6,-5% MB / %size_:~0,-6%.%size_:~-6,-5% MB (%percent%%%) " <nul
set /a percent=( %size:~0,-6% * 100 ) / %size_:~0,-6%
if "%size%"=="%size_%" goto :eof
tasklist /fi "imagename eq wget.exe" | findstr "wget.exe" >nul
if "%errorlevel%"=="1" goto :eof
ping localhost -n 2 >nul
FOR /F "usebackq" %%A IN ('data\update\%download%.zip') DO set size=%%~zA
if %size% leq 1000000 set size=0000000
goto :update.download.progress

:update.extract
echo.Extracting... %download%.zip
mkdir data\update\%download% 2>>data\update_error.log
bin\7za.exe x -tzip data\update\%download%.zip -odata\update\%download% -aoa >>data\update.log 2>&1
goto :eof

:update.install.pack
echo.Installing Pack Updates...
::goto :eof
for /f "tokens=*" %%a in ('dir /b data\update\%download%\*') do (
	echo.- %%a
	echo a | xcopy /e /v data\update\%download%\* data\packs\%pack%\ >>data\update.log 2>&1
)
if not "%1"=="new" call :update.version.fix
bin\wget.exe -q http://%url%/pcmod2/update/pack/servers/servers_%pack%.dat -O data\packs\%pack%\servers.dat&title PCMod Update
set pack_version=%pack_update%
ping localhost -n 2 >nul
goto :eof
:update.version.fix
echo.Updating Version File...
copy nul data\indexes\version.fix >>data\update.log 2>&1
for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version.tmp') do (
	if not "%%a"=="%pack%" >>data\indexes\version.fix echo.%%a;%%b;%%c;%%d;%%e&echo.- %%a[%%b]
	if "%%a"=="%pack%" >>data\indexes\version.fix echo.%%a;%pack_update%;%%c;%%d;%%e&echo.- %%a[%pack_version%] --^> %%a[%pack_update%]
)
echo.Custom Packs: 
for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version') do (
	set a=0
	for /f "tokens=1 delims=;" %%f in ('type data\indexes\version.tmp') do (
		if "%%a"=="%%f" set a=1
	)
	if "!a!"=="0" >>data\indexes\version.fix echo.%%a;%%b;%%c;%%d;%%e&echo.- %%a
)
move data\indexes\version.fix data\indexes\version >>data\update.log 2>&1
goto :eof

:update.install.launcher
echo.Installing Launcher Updates...
echo.- PCMod.hta
copy /v data\update\%download%\PCMod.hta PCMod.hta >>data\update.log 2>&1
echo.- data\
echo a | xcopy /e /v data\update\%download%\data\* data\ >>data\update.log 2>&1
echo.- bin\
echo a | xcopy /e /v data\update\%download%\bin\* bin\ >>data\update.log 2>&1
echo.- cmd\
set launcher_version=%launcher_update%
echo a | xcopy /e /v data\update\%download%\cmd\* cmd\ >>data\update.log 2>&1
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
:::::::: UPDATE ::::::::
:::::::: BUFFER ::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
::::::::::::::::::::::::
ping localhost -n 2 >nul
ping localhost -n 2 >nul
ping localhost -n 2 >nul
goto :eof
goto :update.check

::˜ Copy Right Mark Rewey © (2018)
:: Designed for Plattecraft Server.
:: http://www.markspi.ddns.me/pcmod