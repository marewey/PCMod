@echo off
@setlocal EnableDelayedExpansion Enableextensions
title PCMod
call :get.time.formated
echo.[START: %timee%]
if not "%1"=="launcher" cd ..&set connection=1&set url=pcmod.ddns.me
echo.Running in '%cd%'
echo.Connection: %connection%
echo.########### LOAD ############
call cmd\refreshenv.cmd >nul
::LOAD VARs FROM FILE
call :vars
::CHECK FOR DEBUG LOG AND SET IT UP
if "%debug%"=="" set debug=nul
if not "%debug%"=="nul" echo.DEBUGGING to log: %debug%
set debug_=^>^>%debug% 2^>^&1
::GET SKIN FILES if not VANILLA
if /i not "%modloader%"=="vanilla" call :skinget
call :mcuuid
call :pmc_check
echo.########### LOGIN ###########
::LOGIN for USER
if "%connection%"=="1" call :auth
:: LOG THE LOGIN
if "%log-logins%"=="1" call :log-logins in
echo.########### LAUNCH ##########
call :launch
::GAME RUNS HERE
call :shutdown
call :get.time.formated
echo.[END:%timee%]
::Move Current Log to the Logs folder
copy "data\launch.log" "data\packs\%pack%\logs\launch-%timee%.log" >nul
exit

:get.time.formated
set time-=%time:~0,-9%-%time:~3,-6%-%time:~6,-3%
set date-=%date:~10%-%date:~4,-8%-%date:~7,-5%
set timee=%date-%_%time-%
goto :eof

:pmc_check
set /p "=Checking for PMC..." <NUL
set portablemc=portablemc
%portablemc% -v show about >nul 2>nul
if "%errorlevel%"=="0" echo. Using System Install
if not "%errorlevel%"=="0" set portablemc=bin\pmc\bin\portablemc&echo. Using Local Install
%portablemc% -v show about >nul 2>nul
if not "%errorlevel%"=="0" echo.ERROR: PORTABLEMC not installed
goto :eof

:vars
echo.Setting Default Variables...
set user=%username%
set memory=4096
set modcnt=0
set mcuuid=00000000-0000-0000-0000-000000000000
set uuid=PC2-NOUUID
set pack=2-4-x
set version=2.4.1
set modloader=forge
set mcversion=1.19.2
set mlversion=43.3.5
echo.Reading Variables from File...
for /f "tokens=1-2 delims==" %%a in ('type settings.txt') do set %%a=%%b
for /f %%a in ('type data\indexes\user') do if not "%%a"=="" set user=%%a
for /f %%a in ('type data\indexes\mcuuid') do if not "%%a"=="" set mcuuid=%%a
if exist "data\indexes\modcount" for /f %%a in ('type data\indexes\modcount') do set modcnt=%%a
if exist "data\indexes\uuid" for /f %%a in ('type data\indexes\uuid') do set uuid=%%a
for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version') do (
	if "%%a"=="%pack%" set pack_version=%%b&set modloader=%%c&set mcversion=%%d&set mlversion=%%e
	if "%%a"=="Launcher" if "%%c"=="PCMod" set launcher_version=%%b
)
set m-version=%modloader%:%mcversion%-%mlversion%
if /i "%modloader%"=="vanilla" set m-version=%mcversion%
if /i "%modloader%"=="fabric" set m-version=%modloader%:%mcversion%:%mlversion%
if /i "%modloader%"=="#-BTW" set m-version=%mlversion%
if "%autoserver%"=="1" set autoserver_=--server plattecraft.ddns.net --server-port 25566
if "%autoserver%"=="1" if "%pack%"=="2-4-x" set autoserver_=--server plattecraft.ddns.net --server-port 25566
if "%autoserver%"=="1" if "%pack%"=="BTW" set autoserver_=--server plattecraft.ddns.net --server-port 25568
if "%autoserver%"=="1" if "%pack%"=="2-3-x" set autoserver_=--server plattecraft.ddns.net --server-port 25567
if "%autoserver%"=="0" set autoserver_=
goto :eof
:mcuuid
::Convert username to UUID
set /p "=Converting Username to UUID... "<nul
if exist "bin\uuid-tool-1.0.jar" for /f "tokens=1-2 delims= " %%a in ('echo.%user%^|data\packs\%pack%\jvm\java-runtime-gamma\bin\java.exe -jar bin\uuid-tool-1.0.jar -o') do (
	if "%user%"=="%%a" set mcuuid=%%b&echo.'%user%' UUID: %%b
)
>data\indexes\mcuuid echo.%mcuuid%
set mcuuid=%mcuuid:-=%
goto :eof

:skinget
if "%connection%"=="0" goto :eof
echo.---=== SKIN DOWNLOADER ===---
::Get local Skin Version
for /f "tokens=1-2 delims= " %%a in ('type data\indexes\skindex') do set %%a_v=%%b
::Get the skindex
set /p "=Getting skindex..." <NUL&%debug_% bin\wget -T 5 -O data\indexes\skindex http://%url%/skins/skin.index&echo. DONE
set skin_missing=0
set skin_updates=0
::Count missing skins
for /f "tokens=1-2 delims= " %%a in ('type data\indexes\skindex') do if not exist "data\packs\%pack%\cachedImages\skins\%%a.png" set /a skin_missing=%skin_missing%+1
::Count new skin updates
for /f "tokens=1-2 delims= " %%a in ('type data\indexes\skindex') do if not "%%b"=="!%%a_v!" set /a skin_updates=%skin_updates%+1
::Report this
if not "%skin_missing%"=="0" echo.Missing Skins: %skin_missing%
if not "%skin_updates%"=="0" echo.Updated Skins: %skin_updates%
::If Skin does not exist, download it
for /f "tokens=1-2 delims= " %%a in ('type data\indexes\skindex') do if not exist "data\packs\%pack%\cachedImages\skins\%%a.png" %debug_% bin\wget -T 5 -O "data\packs\%pack%\cachedImages\skins\%%a.png" "http://%url%/skins/%%a"&echo.Getting skin for "%%a" ...
::If Skin version changed, download it
for /f "tokens=1-2 delims= " %%a in ('type data\indexes\skindex') do if not "%%b"=="!%%a_v!" %debug_% bin\wget -T 5 -O "data\packs\%pack%\cachedImages\skins\%%a.png" "http://%url%/skins/%%a"&echo.Updating skin for "%%a" ... (!%%a_v! to %%b)
if "%skin_missing%"=="0" if "%skin_updates%"=="0" echo.No Skins Downloaded.
echo.---===##### DONE ######===---
::copy "data\packs\%pack%\cachedImages\skins\%user%.png" "data\packs\%pack%\cachedImages\skins\uuid\%mcuuid%.png" >nul
goto :eof

:auth
echo.Authorizing User...
::If offline, notify and then skip
if "%connection%"=="0" set returnAuth=408.auth&echo.*** PCMod Error: Unable to verify identity with server.&>cmd\408.vbs echo.CreateObject("WScript.Shell").Popup "	Unable to verify identity with server.", 5, "PCMod - Error"&start cmd\408.vbs&goto :eof
::Decode auth file for submission
call :auth.decode
::Check to make sure there is a username and that its valid
set user_=%user%
for /f "usebackq" %%a in (`echo.%user_% ^| bin\tr -dc '[:alnum:]_\n\r'`) do set user=%%a
if not "%user%"=="%user_%" echo.Username invalid (%user_%), Correcting username (%user%)
if "%user%"=="" bin\nircmd.exe infobox "No username supplied. Please enter one." "PCMod - Error"&echo.*** PCMod Error: No username supplied. Please enter one.&exit
::Authenticate with Server
%debug_% bin\wget -O%temp%\au.th --post-data "x=%token%&u=%user%&z=auth" "http://%url%/commands/authp.php"
for /f %%a in ('type %temp%\au.th') do set returnAuth=%%a
del %temp%\au.th 2>nul
::Display AUTH Code and Reason
echo.AUTH RETURN: %token% --- %returnAuth%
if "%returnAuth%"=="401.auth" echo.*** PCMod Error: %user% does not have the correct password. Please try again.
if "%returnAuth%"=="404.auth" echo.*** PCMod Warn: %user% does not have a password.
if "%returnAuth%"=="401.auth" >cmd\401.vbs echo.CreateObject("WScript.Shell").Popup "	Password was incorrect. Try again." ^& vbcrlf ^& "	To reset password, Go to pcmod.ddns.me/account", 15, "PCMod - Error"&start cmd\401.vbs&exit
goto :eof
:auth.decode
echo.%user%|bin\xcode.exe data\indexes\auth >nul
for /f "tokens=1 delims= " %%a in ('type data\indexes\auth') do set token=%%a
echo.%user%|bin\xcode.exe data\indexes\auth >nul
goto :eof

:log-logins
::Log the users Launch open/close/crash
if "%connection%"=="0" goto :eof
set state=%1
bin\wget.exe -q -T 5 -t 3 -O data\indexes\xip ifconfig.co
for /f %%a in ('type data\indexes\xip') do set xip=%%a
if "%xip%"=="" set xip=xxx.xxx.xxx.xxx
echo.Sending data to server... (state: %state%)
echo.%uuid% - %state%: [%user%/%mcuuid%/%pack_version%/%launcher_version%],[%xip%],[%modcnt% mods/%memory% MB]
%debug_% bin\wget -t 2 -T 5 -O nul "http://%url%/commands/login2.php" --post-data "user=%user%&uuid=%uuid%&state=%state%&mcuuid=%mcuuid%&version=%pack%/%pack_version%&lversion=%launcher_version%&netinfo=%xip%&modcount=%modcnt%&memory=%memory%"
if "%state%"=="in" call :pcmsg launched
if "%state%"=="crash" call :pcmsg crashed
goto :eof
:pcmsg
set pcmsg=%1
echo.Sending Message to PC [%user% %pcmsg% the game.]...
%debug_% bin\wget -T 5 -t 3 -O nul "http://%url%/commands/climsg2.php" --post-data "user=%user%&state=%pcmsg%&pack=%pack%"
goto :eof

:launch
::Setup Crashreport Catcher
set cnt=0
echo.Starting Crashreport Catcher... %cnt%
if exist "data\packs\%pack%\crash-reports\*.txt" for /f %%A in ('dir /a-d-s-h /b data\packs\%pack%\crash-reports\*.txt ^| find /v /c ""') do set cnt=%%A
::=== START PROCESS
::Close HTA files
title PCMod - Launcher
"%cd%\bin\nircmd.exe" win close title "PCMod - Modlist"
"%cd%\bin\nircmd.exe" win close title "PCMod Launcher - %user%"
::Check to make sure installed
call :checkinstall
echo.LAUNCHING... (data\packs\%pack% %m-version%)
::Display Launching VBS Popup
>cmd\launching.vbs echo.CreateObject("WScript.Shell").Popup "Launching PCMod...			" ^& vbcrlf ^& "	* Username: %user%" ^& vbcrlf ^& "	* MC-UUID: %mcuuid%" ^& vbcrlf ^& "	* PCMod Version: %pack%/%pack_version%" ^& vbcrlf ^& "	* Memory Used: %memory%Mb" ^& vbcrlf ^& "	* Mods: %modcnt%", 30, "PCMod - Launcher"
start cmd\launching.vbs
::Launch Game
if "%showconsole%"=="1" echo. **** Detatching Session, Starting in Console Mode. **** &start %portablemc% --work-dir "%cd%\data\packs\%pack%" --main-dir "%cd%\data\packs\%pack%" --output human start -u %user% -i %mcuuid% %autoserver_% --jvm-args="-Xmx%memory%M -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M" %m-version%
if not "%showconsole%"=="1" %portablemc% --work-dir "%cd%\data\packs\%pack%" --main-dir "%cd%\data\packs\%pack%" start -u %user% -i %mcuuid% %autoserver_% --jvm-args="-Xmx%memory%M -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M" %m-version%
::=== END PROCESS
echo.EXITING...
::Recount Crashreporter Catcher
set ccnt=0
if exist "data\packs\%pack%\crash-reports\*.txt" for /f %%A in ('dir /a-d-s-h /b data\packs\%pack%\crash-reports\*.txt ^| find /v /c ""') do set ccnt=%%A
if not "%connection%"=="0" if not "%ccnt%"=="%cnt%" call :crash
goto :eof
:checkinstall
::CHECK FOR TRUE DARKNESS
if "%pack%"=="2-4-x" if not exist "data\packs\%pack%\mods\*darkness*.jar" bin\wget.exe -q "http://%url%/mods/%pack%/darkness-forge-mc119-2.0.101.jar" -O "data\packs\%pack%\mods\darkness-forge-mc119-2.0.101.jar"
::Check if modloader install is needed
set /p "=Checking for %modloader%... "<nul
set needsinstall=0
if not exist "data\packs\%pack%" echo.PACK MISSING. *CRITICAL ERROR*
if not exist "data\packs\%pack%\libraries\net\*%modloader%*" if /i not "%modloader%"=="vanilla" set needsinstall=1
if not exist "data\packs\%pack%\assets\indexes\*" set needsinstall=1
if not exist "data\packs\%pack%\versions\%modloader%-%mcversion%-%mlversion%" if /i not "%modloader%"=="vanilla" if not "%mlversion%"=="latest" set needsinstall=1
if "%needsinstall%"=="0" echo.FOUND [%modloader% %mcversion%/%mlversion%]&goto :eof
echo.FAILED [NOT FOUND: %modloader% for %mcversion%/%mlversion%]
echo.Installing %modloader%...
::Display popup
>cmd\installing.vbs echo.CreateObject("WScript.Shell").Popup "Installing %modloader%..." ^& vbcrlf ^& "This may take a few minutes" ^& vbcrlf ^& "Please Wait...", 30, "PCMod - Launcher"
start cmd\installing.vbs
::Dry run launcher to download resources
%portablemc% --work-dir "%cd%\data\packs\%pack%" --main-dir "%cd%\data\packs\%pack%" start --dry %m-version%
goto :eof
:crash
::Upload Crashreports
echo.Found new Crashreport (%cnt% to %ccnt%).
>bin\crashup.ftp echo.cd logins
>>bin\crashup.ftp echo.cd "%user%"
>>bin\crashup.ftp echo.prompt
>>bin\crashup.ftp echo.lcd data\packs\%pack%\
>>bin\crashup.ftp echo.mkdir crash-reports
>>bin\crashup.ftp echo.cd crash-reports
>>bin\crashup.ftp echo.lcd crash-reports
if exist "data\packs\%pack%\crash-reports\*.*" for /f %%a in ('dir /b /o:d data\packs\%pack%\crash-reports') do set tmpfile=%%a
>>bin\crashup.ftp echo.mput %tmpfile%
>>bin\crashup.ftp echo.bye
set ftppass=cnff
if exist "bin\tr.exe" for /f "usebackq" %%a in (`echo.%ftppass% ^| bin\tr 'A-Za-z0-9' 'N-ZA-Mn-za-m5-90-4'`) do set ftppass_=%%a
>cmd\crash.vbs echo.CreateObject("WScript.Shell").Popup "Minecraft has crashed. The crashreport was sent to the server for examination.", 15, "PCMod - Error"
start cmd\crash.vbs
start data\packs\%pack%\crash-reports\
if not "%connection%"=="0" if "%log-logins%"=="1" call :log-logins crash
set /p "=Uploading Crash Report to Server... "<NUL
bin\ftps.exe -a -user:pcmod -password:%ftppass_% -s:bin\crashup.ftp %url% 21 >data\crashup.log 2>&1
echo.DONE
del bin\crashup.ftp 2>nul
goto :eof

:shutdown
::Start the HTA Back up
echo.Starting Launcher again...
start "" "PCMod.hta"
if not "%connection%"=="0" if "%log-logins%"=="1" call :log-logins out
::Clean up VBS
del cmd\*.vbs 2>nul
goto :eof

::˜ Copy Right Mark Rewey © (2018)
:: Designed for Plattecraft Server.
:: http://pcmod.ddns.me