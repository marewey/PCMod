@echo off
@setlocal EnableDelayedExpansion Enableextensions
if "%1"=="len" call :len %2 %3&goto :eof
set ftppass=cnff
set program="%cd%\PCMod.hta"
set url=markspi.ddns.me
set debug=data\debug.log
if not exist "settings.txt" call :save new
if not "%1"=="login" echo.^>%1 %2 %3
if "%1"=="login" echo.^>%1 %2 ****
call :load %1
if not "%debug%"=="nul" echo.DEBUGGING to log: %debug%
if not exist "%debug%" >%debug% echo.STARTING DEBUG LOG... %date% %time%
::INIT
if "%1"=="init" call :init
::LINKS
if "%1"=="modlist" call :modlist %2&echo.[DONE]&goto :eof
if "%1"=="web" call :web %2
::LOGIN
if "%1"=="login" call :login %2 %3
::Settings
if "%1"=="shortcut" call :shortcut %2 %3
if "%1"=="autoserver" call :autoserver %2 %3
if "%1"=="log-logins" call :ll %2 %3
if "%1"=="lite" call :lite %2 %3&exit
::THESE SHOULD BE INTEGRATED TO SETTINGS
if "%1"=="version-select" call :version.select %2 %3
if "%1"=="memset" call :memset %2
::PLAYER LIST
if "%1"=="refreshplayers" call :refreshplayers
::MAIN BUTTONS
if "%1"=="update" call :update.now %2 %3
if "%1"=="launch" call :launch&exit

call :save
echo.[DONE]
exit /b

::===============================  UPDATE HANDLEING/CHECK  ==================================
:update.check
call :net.check popup
echo.Checking for updates... Pack %pack% [%pack_version%] Launcher [%launcher_version%]
if "%connection%"=="0" echo.*** No Connection ***&goto :eof
bin\wget -q -T 5 http://%url%/pcmod2/version -O data\indexes\version.tmp
title PCMod
set pack_update=
set launcher_update=
for /f "tokens=1-3 delims=;" %%a in ('type data\indexes\version.tmp') do (
	if "%%a"=="%pack%" if not "%%b"=="%pack_version%" set pack_update=%%b
	if "%%a"=="Launcher" if "%%c"=="PCMod" if not "%%b"=="%launcher_version%" set launcher_update=%%b
)
if not "%launcher_update%"=="" if "%autoupdate%"=="1" call :update.launcher
if "%launcher_update%"=="" if not "%pack_update%"=="" if "%autoupdate%"=="1" call :update.pack
goto :eof
:update.pack
echo.Pack Update Found. [%pack_update%]
>cmd\pack_update.vbs echo.Set Shell=CreateObject("wscript.shell") 
>>cmd\pack_update.vbs echo.Question = Msgbox("PCMod Pack %pack% Version %pack_update% is out." ^& vbCrLf ^& "Would you like to update?" ^& vbCrLf ^& "Warning: You must be up to date to join server!",VbYesNO + VbQuestion, "PCMod Update")
>>cmd\pack_update.vbs echo.If Question = VbYes Then
>>cmd\pack_update.vbs echo.     Shell.Run ("cmd\settings.bat update pack %pack_update%"),1
>>cmd\pack_update.vbs echo.End If
start /min cmd\pack_update.vbs
goto :eof
:update.launcher
echo.Launcher Update Found. [%launcher_update%]
>cmd\launcher_update.vbs echo.Set Shell=CreateObject("wscript.shell") 
>>cmd\launcher_update.vbs echo.Question = Msgbox("PCMod Launcher %launcher_update% is out." ^& vbCrLf ^& "Would you like to update?" ^& vbCrLf ^& "Warning: For best stability, it is best to be up to date!",VbYesNO + VbQuestion, "PCMod Update")
>>cmd\launcher_update.vbs echo.If Question = VbYes Then
>>cmd\launcher_update.vbs echo.     Shell.Run ("cmd\settings.bat update launcher %launcher_update%"),1
>>cmd\launcher_update.vbs echo.End If
start /min cmd\launcher_update.vbs
goto :eof
:update.now
echo.Launching Update...
set update_type=%1
set update_version=%2
if "%update_type%"=="" set update_type=empty
if "%connection%"=="1" if not "%update%"=="" bin\wget -q -T 5 http://%url%/pcmod2/updates/launcher/base/cmd/update.bat -O cmd\update.bat
:: use launcher/pack/empty for 1
copy cmd\update.bat cmd\update_.bat
call cmd\update_.bat %update_type% %update_version%
goto :eof

::===============================  INITIAL LAUNCH AND SETUP  ==================================
:init
if "%fresh%"=="1" set fresh=&call :fresh
if exist "bin\.fresh" call :fresh.id&exit
if "%user%"=="" call :fresh
call :setup
call :update.check
call :download
if "%connection%"=="1" call :refreshplayers
goto :eof
:download
echo.Downloading News.html, Servers.dat, Script.zs and PCMod-%pack%.pak...
if "%connection%"=="0" echo.*** No Connection ***
if "%connection%"=="1" bin\wget.exe -q -T 5 -O data\pages\news.html http://%url%/pcmod2/updates/news.html
::if "%connection%"=="1" bin\wget.exe -q -T 5 -O data\packs\%pack%\PCMod-%pack%.pak http://%url%/pcmod2/updates/PCMod-%pack%.pak
if "%connection%"=="1" if exist "data\packs\%pack%\scripts\script.zs" bin\wget.exe -q -T 5 -O data\packs\%pack%\scripts\script.zs http://%url%/pcmod2/updates/pack/scripts/script_%pack%.zs
if "%connection%"=="1" if exist "data\packs\%pack%\servers.dat" bin\wget.exe -q -T 5 -O data\packs\%pack%\servers.dat http://%url%/pcmod2/updates/pack/servers/servers_%pack%.dat
goto :eof
:setup
call :pythoncheck
if exist "data\indexes\uuid" for /f %%a in ('type data\indexes\uuid') do set uuid=%%a
if exist "data\indexes\%computername%.sysinfo" call :memcalc
if %mem_gb% leq 4 bin\nircmd.exe infobox "Your System does not have enough Memory: Using %memory%MB/%memtot%MB" "PCMod Error"
call :user
echo.Settings:
echo. --Set User: %user%
echo. --Set Memory: %memory%mb
echo. --Set MCVersion: %mcversion%
echo. --Set MCUUID: %mcuuid%
echo. --Set Gamedir: %cd%\data\packs\%pack%
goto :eof

:fresh.id
set /a P_=%random%*3/2+126735
set uuid=PC2-%P_%%username:~0,1%0
>data\indexes\uuid echo.%uuid%&echo.New UUID: %uuid%
:fresh
bin\nircmd.exe win close stitle "PCMod Launcher"
>cmd\fresh.vbs echo.CreateObject("WScript.Shell").Popup "Setting default settings... Please wait", 11, "PCMod Setup"&start cmd\fresh.vbs
echo.*** Starting Setup ***
if "%user%"=="" set user=%username%&call :user %username%
if "%shortcut%"=="1" call :shortcut 1
if exist "data\indexes\%computername%.sysinfo" del data\indexes\%computername%.sysinfo
if exist "%temp%\mem" del %temp%\mem
call :memcalc
call :download
call :modlist
call :mcuuid
del bin\.fresh 2>nul
start "" "PCMod.hta"
echo.[DONE]
echo.*** Setup Complete. ***
copy data\init.log data\backup\init_install.log>nul
echo.
echo.^>init
goto :eof

::===============================  USERNAME AND LOGIN  ==================================
:usererror
echo.Invalid User: %user_%
echo.Corrected User: %user%
bin\nircmd.exe infobox "Sorry, the username: %user_% was %1. Correcting to %user%" "PCMod User Error" 1
goto :eof
:login
bin\nircmd.exe win settext title "PCMod Launcher" "PCMod Launcher - Logging in..."
set user-last=%user%
call :user %1
call :pass %2
if "%returnAuth%"=="408.auth" >data\indexes\user echo.%user-last%&goto :eof
if "%returnAuth%"=="401.auth" >data\indexes\user echo.%user-last%&goto :eof
call :mcuuid
goto :eof
:user
if not "%1"=="" set user=%1
echo.Setting User to %user%...
set user_=%user%
for /f "usebackq" %%a in (`echo.%user_% ^| bin\tr -dc '[_[:alnum:]]\n\r'`) do set user=%%a
call :len %user% userlen
if "%userlen%"=="" set userlen=0
echo.Checking User Length: %userlen%
if %userlen% gtr 16 set user=%user:~0,16%
if %userlen% leq 2 set user=%user%%random%
if not "%user%"=="%user_%" call :usererror invalid
>data\indexes\user echo.%user%
goto :eof
:pass
>%temp%\auth.tmp <nul set/p "=%1"
for /f "tokens=1 delims= " %%a in ('bin\md5sum.exe %temp%\auth.tmp') do >data\indexes\auth echo.%%a
echo.%user%|bin\xcode.exe data\indexes\auth >nul
del %temp%\auth.tmp 2>nul
call :auth
if "%returnAuth%"=="408.auth" bin\nircmd.exe win settext stitle "PCMod Launcher" "PCMod Launcher - Login Failed"
if "%returnAuth%"=="401.auth" bin\nircmd.exe win settext stitle "PCMod Launcher" "PCMod Launcher - Login Failed"
if "%returnAuth%"=="200.auth" bin\nircmd.exe win settext stitle "PCMod Launcher" "PCMod Launcher - %user%"
if "%returnAuth%"=="404.auth" bin\nircmd.exe win settext stitle "PCMod Launcher" "PCMod Launcher - %user%"
goto :eof
:auth
echo.Authorizing User (%user%)...
call :auth.decode
::If offline, notify and then skip
if "%connection%"=="0" set returnAuth=408.auth&>cmd\408.vbs echo.CreateObject("WScript.Shell").Popup "***	Unable to verify identity with server." ^& vbcrlf ^& "	Check your internet connection.", 5, "PCMod - Error"&start cmd\408.vbs&goto :eof
::Check to make sure there is a username and that its valid
set user_=%user%
for /f "usebackq" %%a in (`echo.%user_% ^| bin\tr -dc '[_[:alnum:]]\n\r'`) do set user=%%a
if not "%user%"=="%user_%" echo.Username invalid (%user_%), Correcting username (%user%)
if "%user%"=="" bin\nircmd.exe infobox "No username supplied. Please enter one." "PCMod Error"&echo.*** PCMod Error: No username supplied. Please enter one.
bin\wget -O%temp%\au.th --post-data "x=%token%&u=%user%&z=auth" "http://%url%/pcmod2/commands/authp.php" 2>nul >nul
for /f %%a in ('type %temp%\au.th') do set returnAuth=%%a
del %temp%\au.th 2>nul
::Display AUTH Code and Reason
echo.AUTH RETURN: %token% --- %returnAuth%
if "%returnAuth%"=="401.auth" >cmd\401.vbs echo.CreateObject("WScript.Shell").Popup "***	Password was incorrect. Try again." ^& vbcrlf ^& "	To reset password, Go to pcmod.ddns.me/account", 15, "PCMod - Error"&start cmd\401.vbs
if "%returnAuth%"=="200.auth" >cmd\200.vbs echo.CreateObject("WScript.Shell").Popup "     Logged In Successfully.", 5, "PCMod - Login"&start cmd\200.vbs
goto :eof
:auth.decode
echo.%user%|bin\xcode.exe data\indexes\auth >nul
for /f "tokens=1 delims= " %%a in ('type data\indexes\auth') do set token=%%a
echo.%user%|bin\xcode.exe data\indexes\auth >nul
goto :eof


::===============================  CHECK MEMORY/DEFAULT MEMORY  ==================================
:memcalc
if not exist "data\indexes\%computername%.sysinfo" call :sysinfocheck
if exist "data\indexes\%computername%.sysinfo" for /f "tokens=1-2 delims=:" %%a in ('type data\indexes\%computername%.sysinfo') do if "%%a"=="Total Physical Memory" set memtot=%%b
set /p "=Calculating System Memory... "<NUL
set memtot=%memtot: =%
set memtot=%memtot:~0,-2%
set memtot=%memtot:,=%
set mem_gb=%memtot:~0,-3%
echo.%memtot%MB / %mem_gb%GB
if not exist "%temp%\mem" call :defaultmem
goto :eof
:sysinfocheck
echo.Collecting Systeminfo for memory settings...
systeminfo >data\indexes\%computername%.sysinfo
goto :eof

:defaultmem
echo.Setting Default Memory Setting...
set /a memory=3072+(64*%mem_gb%)
>%temp%\mem echo.%memtot%
echo.Default Memory Setting for your System: %memory%MB/%memtot%MB.
goto :eof

:memset
set mem_set=%1
echo.Changing Memory setting from %memory%MB to %mem_set%MB...
call :memcalc
set /p "=Checking to make sure Memory setting does not exceed system memory... "<NUL
if %mem_set% geq %memtot% echo.[ERROR]&echo.ERROR: %mem_set% exceeds system memory total of %memtot%.&bin\nircmd.exe infobox "Memory setting you entered exceeds system memory~n%mem_set% > %memtot%" "PCMod Error"&goto :eof
echo.[OK]
set memory=%mem_set%
goto :eof

::===============================  CHECK FOR REQUIRED PYTHON AND PORTABLEMC  ==================================
:pythoncheck
set PATH=!PATH:%LOCALAPPDATA%\Microsoft\WindowsApps;=!
if "%errorchecker%"=="4" goto :python_failed
::========================== PYTHON
set /p "=Checking for Python Install... "<NUL
py --version 2>>data\pythonerror.log >data\indexes\python_version
set pycheck=%errorlevel%
if not "%pycheck%"=="0" echo.[NOT INSTALLED]&goto :py_install
if "%pycheck%"=="0" for /f "tokens=1-2 delims= " %%a in ('type data\indexes\python_version') do echo.%%b
::========================== PORTABLEMC
set /p "=Checking for PORTABLEMC... "<NUL
pip list 2>nul | find "portablemc " 2>>data\pythonerror.log >data\indexes\portablemc_version
set pmc=%errorlevel%
if "%pmc%"=="0" for /f "tokens=1-2 delims= " %%a in ('type data\indexes\portablemc_version') do echo.%%b
if not "%pmc%"=="0" echo.[NOT INSTALLED]&goto :portablemc_install
::========================== Resolve
if not exist "%temp%\python_checked" call :pyupgrade
if "%pycheck%"=="0" if "%pmc%"=="0" if not "%errorchecker%"=="" echo.Install Complete.&goto :eof
if "%pycheck%"=="0" if "%pmc%"=="0" if "%errorchecker%"=="" goto :eof
echo.Unexpected Error. Check logs.
echo.[PY=%pycheck%,PMC=%pmc%,ERR=%errorchecker%/3]
echo.PATH=%PATH%
goto :eof
:pyupgrade
echo.Upgrading Python Scripts...
set /a errorchecker=%errorchecker%+1
del data\pythonerror.log 2>nul
::UPDATE PIP
py -m pip install --upgrade pip 2>>data\pythonerror.log >>%debug%
::NO LONGER NEEDED
echo.y|pip uninstall portablemc-fabric 2>>data\pythonerror.log >>%debug%
echo.y|pip uninstall portablemc-forge 2>>data\pythonerror.log >>%debug%
::UPDATE PMC
pip install --upgrade --force-reinstall portablemc 2>>data\pythonerror.log >>%debug%
>%temp%\python_checked echo.%date% - %time%
goto :eof
:portablemc_install
set /a errorchecker=%errorchecker%+1
set /p "=Installing PORTABLEMC... "<NUL
pip install portablemc 2>>data\pythonerror.log >>%debug%
echo.[DONE]
call cmd\refreshenv.cmd
goto :pythoncheck
:py_install
set /a errorchecker=%errorchecker%+1
set /p "=Installing Python... "<NUL
bin\python-3.8.10-amd64.exe /passive InstallAllUsers=0 Include_pip=1 PrependPath=1 SimpleInstall=1
echo.[DONE]
call cmd\refreshenv.cmd
::Find the PATH
set py_path=ERROR
set pmc_path=ERROR
set /p "=Checking PATH for Python... "<NUL
for %%I in (python.exe) do if not "%%~$PATH:I"=="" set py_path=%%~$PATH:I
for %%I in (portablemc.exe) do if not "%%~$PATH:I"=="" set pmc_path=%%~$PATH:I
if not "%py_path%"=="ERROR" if not "%pmc_path%"=="ERROR" echo.[SUCCESS]&echo.PYTHON PATH:%py_path%;%pmc_path%
if "%py_path%"=="ERROR" echo.[ERROR]&echo
goto :pythoncheck
:python_failed
echo.Install Failed.
if not "%pycheck%"=="0" echo.ERROR: Python not installed.&del data\indexes\python_version
if not "%pmc%"=="0" echo.ERROR: PORTABLEMC not installed.
if "%py_path%"=="ERROR" echo.ERROR: Python PATH not set.
if "%pmc_path%"=="ERROR" echo.ERROR: Python Scripts PATH not set.
bin\nircmd.exe infobox "Python Failed to install. Try installing from the web. Otherwise contact Mark" "PCMod Installer" 1
echo.Uploading logs to Server...
set ftppass=cnff
>bin\logup.ftp echo.cd logins
>>bin\logup.ftp echo.cd "%user%"
>>bin\logup.ftp echo.prompt
>>bin\logup.ftp echo.lcd data
>>bin\logup.ftp echo.put launch.log
>>bin\logup.ftp echo.put pythonerror.log
>>bin\logup.ftp echo.put init.log
>>bin\logup.ftp echo.put update.log
>>bin\logup.ftp echo.cd backup
>>bin\logup.ftp echo.put debug.log
>>bin\logup.ftp echo.bye
if exist "bin\tr.exe" for /f "usebackq" %%a in (`echo.%ftppass% ^| bin\tr 'A-Za-z0-9' 'N-ZA-Mn-za-m5-90-4'`) do set ftppass_=%%a
bin\ftps.exe -a -user:pcmod -password:%ftppass_% -s:bin\log.ftp %url% 21 >data\logup.log 2>&1
goto :eof

::===============================  CHANGE SETTINGS/BUTTONS  ==================================
:launch
del cmd\update_.bat 2>nul
call cmd\launch.bat launcher
goto :eof

:version.select
set pack-index=%1
set pack=%2
echo.Setting Pack to %1 / %2
set modcount=0
if exist "data\packs\%2\mods\*.jar" for /f %%a in ('dir /a-d-s-h /b data\packs\%2\mods\*.jar ^| find /v /c ""') do set modcount=%%a
>data\indexes\modcount echo.%modcount%
for /f "tokens=1-4 delims=;" %%a in ('type data\indexes\version') do if "%%a"=="%pack%" set pack_version=%%b
call :update.check
goto :eof

:refreshplayers
echo.Refreshing Player list...
bin\wget.exe -q -T 5 -O data\indexes\online http://%url%/pcmod2/players/list-%pack%
type data\indexes\online
goto :eof

:modlist
::PLACEHOLDER
if not exist "data\packs\%pack%\mods\*.jar" goto :eof
set /p "=Generating Modlist Page... "<nul
SetLocal EnableDelayedExpansion Enableextensions
mkdir data\indexes\modlist\%pack% 2>nul
echo.y|del data\indexes\modlist\%pack%\u 2>nul
echo.y|del data\indexes\modlist\%pack%\c 2>nul
echo.y|del data\indexes\modlist\%pack%\b 2>nul
set mcount=
::count the lines for each coloum to find the greatest one
set count_u=0
set count_b=0
set count_c=0
for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do (
	if "%%a"=="U" (
		set /a count_u=!count_u!+1
		>>data\indexes\modlist\%pack%\u echo.!count_u!;%%b
	)
	if "%%a"=="B" (
		set /a count_b=!count_b!+1
		>>data\indexes\modlist\%pack%\b echo.!count_b!;%%b
	)
	if "%%a"=="C" (
		set /a count_c=!count_c!+1
		>>data\indexes\modlist\%pack%\c echo.!count_c!;%%b
	)
)
::
for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do (
	if "%%a"=="C" set /a mcount=!mcount!+1
	if "%%a"=="B" set /a mcount=!mcount!+1
	if "%%a"=="U" set /a mcount=!mcount!+1
)
>data\indexes\modcount echo.!mcount!
for /f %%a in ('dir /a-d-s-h /b data\packs\%pack%\mods\*.jar ^| find /v /c ""') do set modcount=%%a
>data\indexes\modcount echo.!mcount!
for /f "tokens=1-2 delims==" %%a in ('type settings.txt') do set %%a=%%b
if "%lite%"=="1" set lite_= style="background-color:#cd6155;"
if "%lite%"=="0" set lite_=
>data\pages\modlist.html echo.^<head^>
>>data\pages\modlist.html echo.^<style^>
>>data\pages\modlist.html echo..altext { 
>>data\pages\modlist.html echo.    display: none;
>>data\pages\modlist.html echo.}
>>data\pages\modlist.html echo.label:hover .altext {
>>data\pages\modlist.html echo.    display: inline-block;
>>data\pages\modlist.html echo.}
>>data\pages\modlist.html echo.^</style^>
>>data\pages\modlist.html echo.^</head^>
>>data\pages\modlist.html echo.^<body style="background-color: #5d6d7e;"^>
>>data\pages\modlist.html echo.^<center^>
>>data\pages\modlist.html echo.^<table border="1" style="background-color: #BCF6F6;"^>
>>data\pages\modlist.html echo.^<th style="background-color: #5d6d7e;"^>Mod Name^</th^>
>>data\pages\modlist.html echo.^<th style="background-color: #5d6d7e;"^>Required^</th^>
>>data\pages\modlist.html echo.^<th style="background-color: #5d6d7e;"^>Version Added/Updated^</th^>^<tr^>
for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do (
	if not "%%a"=="D" (
		if "%%a"=="U" set side=Universally&set color= style="background-color:#BCF6F6;"
		if "%%a"=="U" if not "%%e"=="#" set side=Universally*&set color= style="background-color:#A9DDDD;"
		if "%%a"=="C" set side=Client-Side&set color= style="background-color:#CCF1C1;"
		if "%%a"=="C" if not "%%e"=="#" set side=Client-Side*&set color= style="background-color:#B7D8AD;"
		if "%%a"=="B" set side=Core Mod&set color= style="background-color:#FFAFA6;"
		if "%%a"=="C" if "%lite%"=="1" set side=Client-Side&set color= style="background-color:#CCF1C1;text-decoration: line-through;"
		set tmp=%%d
		if not "%%e"=="#" set tmp=%%d [%%e]
		set tmp_a=!tmp:~0,48!
		set tmp_b=!tmp:~48!
		if "!tmp_u_a!"=="~0,24" set tmp_u_a=
		if "!tmp_u_b!"=="~24" set tmp_u_b=
		>>data\pages\modlist.html echo.^<tr^>^<td!color!^>^<label^>!tmp_a!^<span class="altext"^>!tmp_b!^</span^>^</label^>^</td^>
		>>data\pages\modlist.html echo.^<td!color!^>^<label^>!side!^</label^>^</td^>
		>>data\pages\modlist.html echo.^<td!color!^>^<label^>%%c^</label^>^</td^>^</tr^>
	)
)
>>data\pages\modlist.html echo.^</table^>^</center^>
echo.Finished
if "%1"=="start" echo.Starting Page to display...&start data\pages\modlist.hta
goto :eof

:web
if "%1"=="discord" start https://discord.gg/AJaVhvR
if "%1"=="pcmod" start http://pcmod.ddns.me
if "%1"=="auth" start http://pcmod.ddns.me/account
goto :eof

:lite
if "%1"=="1" (
	echo.Switching to Lite mode...
	echo.Moving the Client-side mods out of the mods folder...
	mkdir data\disabledclimods\
	for /f "tokens=1-2 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do if "%%a"=="C" move "data\packs\%pack%\mods\%%b" "data\disabledclimods\" >nul
	echo.Adding back the required client mods...
	for /f "tokens=1-5 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do (
		echo.%%d
		if "%%d"=="OptiFineHDUHpre" move "data\disabledclimods\%%b" "data\packs\%pack%\mods\"
		if "%%d"=="Offline Skins" move "data\disabledclimods\%%b" "data\packs\%pack%\mods\"
		if "%%d"=="Controlling" move "data\disabledclimods\%%b" "data\packs\%pack%\mods\"
		if "%%d"=="darkness" move "data\disabledclimods\%%b" "data\packs\%pack%\mods\"
		if "%%d"=="betterbiomeblend" move "data\disabledclimods\%%b" "data\packs\%pack%\mods\"
		if "%%d"=="EntityCollisionFPSFix" move "data\disabledclimods\%%b" "data\packs\%pack%\mods\"
		if "%%d"=="entityculling" move "data\disabledclimods\%%b" "data\packs\%pack%\mods\"
	)
	echo.Backing up current settings...
	copy data\packs\%pack%\options.txt data\backup\options_default.txt >nul
	set lite=1
	bin\nircmd.exe infobox "Switched to Lite Mode" "PCMod Modes"
)
if "%1"=="0" (
	echo.Switching to Default mode...
	echo.Moving the Client-side mods back to mods folder...
	for /f "tokens=1-2 delims=;" %%a in ('type data\packs\%pack%\PCMod-%pack%.pak') do if "%%a"=="C" move "data\disabledclimods\%%b" "data\packs\%pack%\mods\" >nul
	echo.Backing up current settings...
	copy data\packs\%pack%\options.txt data\backup\options_lite.txt >nul
	set lite=0
	bin\nircmd.exe infobox "Switched to Default Mode" "PCMod Modes"
)
call :save
call :modlist
goto :eof

:shortcut
for /f "usebackq tokens=1,2,*" %%B IN (`reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v Desktop`) do set DESKTOP=%%D
set desktop_=%desktop:"=%
>data\indexes\desktop echo."%desktop_%"
set userprofile_=%userprofile:"=%
if not exist "%desktop_%" set desktop_=%USERPROFILE_%\Desktop
set program_=%program:"=%
set cd_=%cd:"=%
set appdata_=%appdata:"=%
if "%1"=="1" call :shortcut.on %2
if "%1"=="0" call :shortcut.off %2
goto :eof
:shortcut.on
echo.Creating Desktop Shortcut...
set SCRIPT=cmd\shortcut.vbs
echo Set oWS = WScript.CreateObject("WScript.Shell") >%SCRIPT%
echo sLinkFile = "%desktop_%\PCMod.lnk" >>%SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >>%SCRIPT%
echo oLink.TargetPath = "%program_%" >>%SCRIPT%
echo oLink.WorkingDirectory= "%cd_%" >>%SCRIPT%
echo oLink.Description = "PCMod - Plattecraft Modded Launcher" >>%SCRIPT%
echo oLink.IconLocation = "%cd_%\data\icons\icon.ico" >>%SCRIPT%
echo oLink.Save >>%SCRIPT%
cscript /nologo %SCRIPT%
ping localhost -n 1 >nul
del %SCRIPT% 2>nul
mkdir "%appdata_%\Microsoft\Windows\Start Menu\Programs\Plattecraft\" 2>nul
copy "%desktop_%\PCMod.lnk" "%appdata_%\Microsoft\Windows\Start Menu\Programs\Plattecraft\PCMod.lnk" >nul
set shortcut=1
goto :eof
:shortcut.off
echo.Deleting Desktop Shortcut...
del "%desktop_%\PCMod.lnk" 2>nul
del "%appdata_%\Microsoft\Windows\Start Menu\Programs\Plattecraft\PCMod.lnk" 2>nul
set shortcut=0
goto :eof

:autoserver
if "%1"=="1" set autoserver=1
if "%1"=="0" set autoserver=0
goto :eof

:ll
if "%1"=="1" set log-logins=1
if "%1"=="0" set log-logins=0
goto :eof

::===============================  USEFUL TOOLS  ==================================
:len string outputvar
Setlocal EnableDelayedExpansion
:: strLen String [RtnVar]
::             -- String  The string to be measured, surround in quotes if it contains spaces.
::             -- RtnVar  An optional variable to be used to return the string length.
Set "s=#%~1"
Set "len=0"
For %%N in (4096 2048 1024 512 256 128 64 32 16 8 4 3 2 1) do (
  if not "!s:~%%N,1!"=="" (
    set /a "len+=%%N"
    set "s=!s:~%%N!"
  )
)
Endlocal&if not "%~2"=="" set %~2=%len%
goto :eof

:net.check
set /p "=Checking Connection... "<NUL
ping 8.8.8.8 -n 1 >nul
if "%errorlevel%"=="1" set connection=0
if "%errorlevel%"=="0" set connection=1
copy nul data\indexes\signature >nul
if "%connection%"=="0" echo.[-1] NO CONNECTION&goto :eof
if "%connection%"=="1" bin\wget -q -T 5 http://%url%/pcmod2/updates/sig -O data\indexes\signature
if "%errorlevel%"=="1" set connection=0
if "%errorlevel%"=="0" set connection=1
if "%connection%"=="0" echo.[503] SERVICE UNAVAILIBLE&goto :eof
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

:mcuuid
set pack_=%pack%
if not exist "data\packs\%pack_%\jvm\*\bin\java.exe" set pack_=2-5-x
for /f "tokens=*" %%a in ('dir /b /a:d data\packs\%pack_%\jvm\java*') do set java_runtime=data\packs\%pack_%\jvm\%%a\bin\java.exe
::Convert username to UUID
set /p "=Converting Username to UUID... "<nul
if exist "bin\uuid-tool-1.0.jar" for /f "tokens=1-2 delims= " %%a in ('echo.%user%^|%java_runtime% -jar bin\uuid-tool-1.0.jar -o') do (
	if "%user%"=="%%a" set mcuuid=%%b&echo.%user% UUID: %%b
)
>data\indexes\mcuuid echo.%mcuuid%
set mcuuid=%mcuuid:-=%
goto :eof

::===============================  LOADING AND SAVING SETTINGS  ==================================
:load
::Cleanup VBS Msgbox
del cmd\401.vbs 2>nul
del cmd\408.vbs 2>nul
del cmd\200.vbs 2>nul
del cmd\skins.vbs 2>nul
del cmd\launcher_update.vbs 2>nul
del cmd\pack_update.vbs 2>nul
echo.LOADING...
::load user, and change title to include the username
for /f %%a in ('type data\indexes\user') do set user=%%a
if not "%user%"=="" bin\nircmd.exe win settext title "PCMod Launcher - Loading..." "PCMod Launcher - %user%"
if "%user%"=="" bin\nircmd.exe win settext title "PCMod Launcher - Loading..." "PCMod Launcher"
::set default variables
set shortcut=1&set log-logins=1&set lite=0&set autoupdate=1&set autoserver=0
set mcuuid=00000000-0000-0000-0000-000000000000&set memory=4096
::load settings to overwrite default
for /f "tokens=1-2 delims==" %%a in ('type settings.txt') do set %%a=%%b
if exist "data\indexes\uuid" for /f %%a in ('type data\indexes\uuid') do set uuid=%%a
if exist "data\indexes\mcuuid" for /f %%a in ('type data\indexes\mcuuid') do set mcuuid=%%a
::load which pack/version you are using
if "%pack-index%"=="" set pack-index=0
if "%pack%"=="" set pack=2-5-x
for /f "tokens=1-4 delims=;" %%a in ('type data\indexes\version') do (
	if "%%a"=="%pack%" set pack_version=%%b&set mcversion=%%d
	if "%%a"=="Launcher" if "%%c"=="PCMod" set launcher_version=%%b
)
::check for internet
if "%debug%"=="" set debug=nul
call :net.check
goto :eof
:save
echo.SAVING...
if "%1"=="new" set shortcut=1&set log-logins=1&set lite=0&set autoupdate=1&set autoserver=0&set memory=4096&set pack=2-5-x&set pack-index=0&set debug=nul
>settings.txt echo.autoserver=%autoserver%
>>settings.txt echo.autoupdate=%autoupdate%
>>settings.txt echo.lite=%lite%
>>settings.txt echo.log-logins=%log-logins%
>>settings.txt echo.shortcut=%shortcut%
>>settings.txt echo.memory=%memory%
>>settings.txt echo.pack-index=%pack-index%
>>settings.txt echo.pack=%pack%
>>settings.txt echo.debug=%debug%
goto :eof

::˜ Copy Right Mark Rewey © (2018)
:: Designed for Plattecraft Server.
:: http://www.markspi.ddns.me/pcmod