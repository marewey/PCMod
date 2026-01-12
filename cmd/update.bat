@echo off
@SetLocal EnableDelayedExpansion Enableextensions
:: %1=type %2=desired version
:: %1=launcher/pack/empty
set "update_type=%~1"
set "desired_version=%~2"
if "%update_type%"=="" set "update_type=empty"
:: If an external version was provided, assign it now
if not "%desired_version%"=="" (
    if /i "%update_type%"=="launcher" set "launcher_update=%desired_version%"
    if /i "%update_type%"=="pack"     set "pack_update=%desired_version%"
)
if "%1"=="" cd ..
:: Load settings
if exist settings.txt (
    for /f "tokens=1-2 delims==" %%a in ('type settings.txt') do set "%%a=%%b"
)
:: Initialization
call :vars
call :window.settings
call :drawlogo
call :drawlogo2
bin\ColorBox.exe /0F -1 16 55 27
bin\bg.exe Locate 18 0
call :net.check
if not "!connection!"=="1" (
    echo.Exiting: No internet connection.
    pause & exit
)
:: Display versions
call :drawversions

::: ------------------ ROUTING PHASE (STRICT SYNTAX) -----------------------
if "!update_type!"=="empty" (
    call :update.check
    
    REM 1. Check for BOTH first
    if not "!launcher_update!"=="" (
        if not "!pack_update!"=="" (
            set "update_type=both"
        ) else (
            set "update_type=launcher"
        )
    ) else (
        REM 2. Launcher was empty, check if Pack has something
        if not "!pack_update!"=="" (
            set "update_type=pack"
        )
    )
)

:: NEW: If an update_type was forced or found, but version is still blank,
:: fill it with the current version so the downloader has a target.
if "%launcher_update%"=="" if /i "%update_type%"=="launcher" set "launcher_update=%launcher_version%"
if "%pack_update%"==""     if /i "%update_type%"=="pack"     set "pack_update=%pack_version%"
if "%pack_update%"==""     if /i "%update_type%"=="empty"    set "pack_update=%pack_version%"
if "%launcher_update%"=="" if /i "%update_type%"=="empty"    set "launcher_update=%launcher_version%"

:: Now execute the UI gatekeeper
if not "%update_type%"=="empty" (
    call :update.user.check %update_type% 3
) else (
    call :update.user.check empty 6
)
timeout /t 2 >nul
exit

:vars
set url=pcmod.ddns.me
for /f "tokens=1-4 delims=;" %%a in ('type data\indexes\version') do (
	if "%%a"=="%pack%" set pack_version=%%b
	if "%%a"=="Launcher" if "%%c"=="PCMod" set launcher_version=%%b
)
set startup=1
goto :eof
:window.settings
title PCMod Update
::color 1a
mode con cols=55 lines=27
color 0f
goto :eof
:net.check
set /p "=Checking Connection... "<nul
ping 8.8.8.8 -n 1 >nul
if "%errorlevel%"=="1" set connection=0
if "%errorlevel%"=="0" set connection=1
copy nul data\indexes\signature >nul
if "%connection%"=="0" echo.[-1] NO CONNECTION&goto :eof
if "%connection%"=="1" bin\wget -q -T 5 http://%url%/updates/sig -O data\indexes\signature 2>nul
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
if not "%sig%"=="PCMod" if "%1"=="popup" bin\nircmd.exe infobox "Unable to connect to PCMod Server. Internet/Server Error" "PCMod Error"
goto :eof
:update.check
if "%connection%"=="0" echo.*** No Connection ***&goto :eof
set pack_update=
set launcher_update=
echo.Checking for updates...
bin\wget -q -T 5 http://%url%/version -O data\indexes\version.tmp
title PCMod
:: Ensure the file was actually created before parsing
if not exist "data\indexes\version.tmp" (
    bin\bg.exe print 0C " [ERROR] Could not retrieve version index.\n"
    timeout /t 3 >nul
    goto :eof
)
:: Parse and set variables
for /f "usebackq tokens=1-3 delims=;" %%a in ("data\indexes\version.tmp") do (
    if /i "%%a"=="%pack%" (
        if not "%%b"=="!pack_version!" set "pack_update=%%b"
    )
    if /i "%%a"=="Launcher" if /i "%%c"=="PCMod" (
        if not "%%b"=="!launcher_version!" set "launcher_update=%%b"
    )
)
goto :eof
:update.user.check type default_key
set auto=%2
set submit=%2
set select=%2
set select_l=%2
if "%1"=="pack" set desc=New Pack %pack% Update: %pack_update%
if "%1"=="launcher" set desc=New Launcher Update: %launcher_update%
if "%1"=="both" set desc=New Launcher Update: %launcher_update%^&echo.New Pack %pack% Update: %pack_update%
if "%1"=="empty" set desc=No Updates Found.
if "%2"=="a" set desc=AUTO UPDATING...^&echo.You have 5 seconds to cancel with C.
:update.loop
if not "%startup%"=="1" cls&bin\bg.exe Locate 18 0
set startup=0
set color_1=F8
set color_1h=F0
set color_2=F8
set color_2h=F0
set color_3=F8
set color_3h=F0
set color_4=F8
set color_4h=F0
set color_5=F8
set color_5h=F0
set color_6=F8
set color_6h=F0
set color_!select_l!=F8
set color_!select_l!h=F0
set color_!select!=87
set color_!select!h=8F
if "%debug%"=="1" echo.!select! - !auto! - !submit! - !timeout! - %*&pause
call :drawlogo
call :drawlogo2
bin\ColorBox.exe /0F -1 16 55 27
call :drawbuttons
bin\bg.exe print %title%
if not "!desc!"=="" echo.%desc%
timeout /t 1 >nul
call :menu_loop %1 %2
if "%exit%"=="1" echo.Exiting...&goto :eof
goto :update.loop
exit /b
:menu_loop type default_key
call :drawlogo
call :drawbuttons
call :click_input %2
::SET POS TO TEXTBOX CLEAR TEXTBOX AREA AND ADD DIV AT TOP
bin\bg.exe Locate 18 0
bin\ColorBox.exe /0F -1 17 104 27 ac0
bin\ColorBox.exe /0F -50 16 104 27
::DEFAULT TEXT
set title=08 "Please Select a Menu Option                           \nUse Mouse, Arrow Keys, or Letter Keys to select option."
set desc=
::PROCESS CHANGES
call :logic_input
bin\bg.exe print %title%
if not "!desc!"=="" echo.%desc%
if "!select!"=="0" call :drawversions %1 %2
::FINAL LOGIC
if "%timeout%"=="1" if not "%auto%"=="0" set submit=%auto%&set desc=
set auto=0
if not "!submit!"=="0" if not "!submit!"=="" if not "!submit!"=="6" call :run.this
if "!submit!"=="1" call :update.pack.downloader
if "!submit!"=="2" call :update.mods
if "!submit!"=="3" call :update.auto
if "!submit!"=="4" call :update.launcher.custom
if "!submit!"=="5" call :update.pack.custom
if "!submit!"=="6" set exit=1&set title=&set desc=
if "%debug%"=="1" echo.!select! - !auto! - !submit! - !timeout! - %* - !update_type!/!launcher_update!/!pack_update!/!launcher_version!/!pack_version!
if not "!submit!"=="0" if not "!submit!"=="" bin\bg.exe Locate 18 0&timeout /t 1 >nul&set title=&set desc=&goto :eof
goto :menu_loop
:drawlogo offset
set titlecolor=63
set bordercolor=63
set menucolor=36
set /a logooffset=%1+0
for /l %%l in (0,1,6) do set /a logo%%l=%%l+!logooffset!
bin\bg.exe fcprint !logo0! 0 %bordercolor% "²²" %titlecolor% "²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²" %bordercolor% "²²"
bin\bg.exe fcprint !logo1! 0 %bordercolor% "²²" %titlecolor% "²²       ²²²²      ²²²  ²²²²  ²²²      ²²²       ²²" %bordercolor% "²²"
bin\bg.exe fcprint !logo2! 0 %bordercolor% "²²" %titlecolor% "²²  ²²²²  ²²  ²²²²  ²²   ²²   ²²  ²²²²  ²²  ²²²²  ²" %bordercolor% "²²"
bin\bg.exe fcprint !logo3! 0 %bordercolor% "²²" %titlecolor% "²²       ²²²  ²²²²²²²²        ²²  ²²²²  ²²  ²²²²  ²" %bordercolor% "²²"
bin\bg.exe fcprint !logo4! 0 %bordercolor% "²²" %titlecolor% "²²  ²²²²²²²²  ²²²²  ²²  ²  ²  ²²  ²²²²  ²²  ²²²²  ²" %bordercolor% "²²"
bin\bg.exe fcprint !logo5! 0 %bordercolor% "²²" %titlecolor% "²²  ²²²²²²²²²      ²²²  ²²²²  ²²²      ²²²       ²²" %bordercolor% "²²"
bin\bg.exe fcprint !logo6! 0 %bordercolor% "²²" %titlecolor% "²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²²" %bordercolor% "²²"
goto :eof
:drawlogo2
bin\bg.exe fcprint 7 0 %menucolor% "±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±"
bin\bg.exe fcprint 8 0 %menucolor% "±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±"
bin\bg.exe fcprint 9 0 %menucolor% "±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±"
bin\bg.exe fcprint 10 0 %menucolor% "±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±"
bin\bg.exe fcprint 11 0 %menucolor% "°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°"
bin\bg.exe fcprint 12 0 %menucolor% "°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°"
bin\bg.exe fcprint 13 0 %menucolor% "°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°"
bin\bg.exe fcprint 14 0 %menucolor% "°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°"
bin\bg.exe fcprint 15 0 %bordercolor% "ÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛ"
bin\bg.exe fcprint 16 0 %bordercolor% "ÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛÛ"
goto :eof
:drawbuttons
bin\bg.exe fcprint 8 14 F0   "          Updater         "
bin\bg.exe fcprint 9 14 F0  "           Menu           "
bin\bg.exe fcprint 11 2 %color_1% "|     Pack     |"
bin\bg.exe fcprint 12 2 %color_1% "|  " %color_1h% "D" %color_1% "ownloader  |"
bin\bg.exe fcprint 11 20 %color_2% "|   " %color_2h% "R" %color_2% "efresh   |"
bin\bg.exe fcprint 12 20 %color_2% "|     Mods    |"
bin\bg.exe fcprint 11 37 %color_3% "|     " %color_3h% "A" %color_3% "uto     |"
bin\bg.exe fcprint 12 37 %color_3% "|    Update    |"
bin\bg.exe fcprint 14 2 %color_4% "|   " %color_4h% "L" %color_4% "auncher   |"
bin\bg.exe fcprint 15 2 %color_4% "|    Update    |"
bin\bg.exe fcprint 14 20 %color_5% "|    " %color_5h% "P" %color_5% "ack     |"
bin\bg.exe fcprint 15 20 %color_5% "|   Update    |"
bin\bg.exe fcprint 14 37 %color_6% "|  " %color_6h% "C" %color_6% "ancel/Exit |"
bin\bg.exe fcprint 15 37 %color_6% "|    Update    |"
goto :eof
:drawversions
echo.Current Versions:
echo. * Launcher Version: %launcher_version%
echo. * Pack Version: %pack_version%
goto :eof
:click_input default_sel
set key=
bin\GetInput.exe /T 5000
if %errorlevel% equ 0 (
   set timeout=1
) else (
   set timeout=0
   if %errorlevel% gtr 0 (
      set key=%errorlevel%
   ) else (
      rem Mouse button clicked
      set /A "input=-%errorlevel%, row=input >> 16, col=input & 0xFFFF"
      if !col! lss 32768 (
         set button=1
      ) else (
         set /A col-=32768
         set button=2
      )
   ) 
)
goto :eof
:logic_input
set select_l=!select!
set select_a=!select!
set select=0
set submit=
::CLICK AREA
if !row! geq 11 if !row! leq 12 if !col! geq 2 if !col! leq 17 set select=1
if !row! geq 11 if !row! leq 12 if !col! geq 20 if !col! leq 34 set select=2
if !row! geq 11 if !row! leq 12 if !col! geq 37 if !col! leq 52 set select=3
if !row! geq 14 if !row! leq 15 if !col! geq 2 if !col! leq 17 set select=4
if !row! geq 14 if !row! leq 15 if !col! geq 20 if !col! leq 34 set select=5
if !row! geq 14 if !row! leq 15 if !col! geq 37 if !col! leq 52 set select=6
if "!timeout!"=="1" set select=0
if not "%key%"=="" set select=0
::LETTERS
if "%key%"=="100" set select=1
if "%key%"=="114" set select=2
if "%key%"=="97" set select=3
if "%key%"=="108" set select=4
if "%key%"=="112" set select=5
if "%key%"=="99" set select=6
if "%key%"=="4" set debug=1
::ARROWS
if "%key%"=="294" set /a select_a=!select_l!-3
if "%key%"=="296" set /a select_a=!select_l!+3
if "%key%"=="293" set /a select_a=!select_l!-1
if "%key%"=="295" set /a select_a=!select_l!+1
if "%select_l%"=="0" if "%key%"=="293" set /a select_a=%%
if "%select_l%"=="0" if "%key%"=="294" set /a select_a=1
if "%select_l%"=="0" if "%key%"=="295" set /a select_a=1
if "%select_l%"=="0" if "%key%"=="296" set /a select_a=1
if not "%select_l%"=="%select_a%" if %select_a% leq 0 set /a select_a=!select_a!+6
if not "%select_l%"=="%select_a%" if %select_a% gtr 6 set /a select_a=!select_a!-6
if not "%select_l%"=="%select_a%" set select=%select_a%
if "%key%"=="13" set select=%select_l%
if "%select%"=="%select_l%" set submit=!select!
if "%timeout%"=="1" if not "%auto%"=="0" set select=6
if "%select%"=="1" set title=07 "                   " 8F " Pack Downloader " 07 "            \n\n"&set desc= * Download different modpacks to launch on PCMod Launcher.
if "%select%"=="2" set title=07 "                    " 8F " Refresh Mods  " 07 "               \n\n"&set desc= * Delete all mods from the mods folder and redownload for the currently selected pack.
if "%select%"=="3" set title=07 "                     " 8F " Auto Update " 07 "                \n\n"&set desc= * Automatically updates Launcher or Pack if any update is needed.^&echo. * Defaults to Launcher if no update is not needed
if "%select%"=="4" set title=07 "                   " 8F " Launcher Update " 07 "                \n\n"&set desc= * Updates Launcher to newest version.
if "%select%"=="5" set title=07 "                     " 8F " Pack Update " 07 "                \n\n"&set desc= * Update currently selected Pack.^&echo. * Currently Selected Pack: %pack%
if "%select%"=="6" set title=07 "                 " 8F " Cancel/Exit Update  " 07 "                \n\n"&set desc= * Cancel Auto-Update or Exit Update Program.
set color_!select_l!=F8
set color_!select_l!h=F0
set color_!select!=87
set color_!select!h=8F
goto :eof
:run.this LABEL
cls
call :drawlogo
bin\bg.exe Locate 7 0
goto :eof

:update.auto
:: ... UI setup ...

:: --- Phase 1: Launcher ---
set "run_l="
if /i "%update_type%"=="launcher" set "run_l=1"
if /i "%update_type%"=="both"     set "run_l=1"
if /i "%update_type%"=="empty"    set "run_l=1"

if defined run_l if not "%launcher_update%"=="" (
    call :update.setdownload launcher
    call :update launcher
	echo.Launcher Update Complete.
	timeout /t 3 >nul
    if /i "%update_type%"=="launcher" goto :eof
)

:: --- Phase 2: Pack ---
set "run_p="
if /i "%update_type%"=="pack"  set "run_p=1"
if /i "%update_type%"=="both"  set "run_p=1"
if /i "%update_type%"=="empty" set "run_p=1"

if defined run_p if not "%pack_update%"=="" (
    call :update.setdownload pack
    call :update pack
	echo.%pack% Update Complete.
	timeout /t 3 >nul
)
:: After all phases are done, finalize once
call :update.finalize
goto :eof

:update.setdownload
:: Simplified with quotes for safety
if "%~1"=="pack" (
    set "download_dir=updates/pack/%pack%"
    set "download=pack_%pack_update%"
)
if "%~1"=="launcher" (
    set "download_dir=updates/launcher"
    set "download=launcher_%launcher_update%"
)
goto :eof

:update.launcher.custom
set /p "launcher_update=LAUNCHER VERSION: "
if "!launcher_update!"=="" set "launcher_update=%launcher_version%"
set update_type=launcher
:: Direct call to the auto logic for that specific type
call :update.auto launcher
goto :eof

:update.pack.custom
set /p "pack_update=PACK VERSION: "
if "!pack_update!"=="" set "pack_update=%pack_version%"
set update_type=pack
:: Direct call to the auto logic for that specific type
call :update.auto pack
goto :eof
::----------------------------------------------------------------------------------------------------- REFRESH MODS
:update.mods
echo.Clearing all Mods...
echo.y|del data\packs\%pack%\mods\*.* >>data\update.log 2>&1
timeout /t 2 >nul
call :update.verify
echo.Verification Complete: %total_mods% mods, !missing_count! missing.
goto :eof

:update.verify
set y=0
set x=0
set "modpath=data\packs\%pack%\mods"
set "staging=data\update\staging"
set "PAK_FILE=data\packs\%pack%\PCMod-%pack%.pak"
if exist "%staging%" rd /s /q "%staging%"
mkdir "%staging%" 2>nul
set total_mods=0
for /f %%z in ('findstr /R "^B; ^C; ^U;" "%PAK_FILE%" ^| find /c /v ""') do set total_mods=%%z
bin\bg.exe print 0F "Validating Mod Integrity...\n"
set current_count=0
set missing_count=0
del "data\indexes\missingmods.txt" 2>nul
>>data\update.log 2>&1 echo.Verifying mods...
:: --- PHASE 1: ISOLATION ---
bin\bg.exe print 0F " - Validating mods...\n"
for /f "usebackq tokens=1-5 delims=;" %%a in ("%PAK_FILE%") do (
    set "tag=%%a"
    set "file=%%b"
    set "name=%%d"
    set "is_valid="
    if "%%a"=="B" set "is_valid=1"
    if "%%a"=="C" set "is_valid=1"
    if "%%a"=="U" set "is_valid=1"
    if defined is_valid (
        set /a current_count+=1
        set /a "percent=(current_count * 100) / total_mods"
        if exist "%modpath%\!file!" (
            if "%4"=="new" bin\bg.exe print 0A "  [HAVE] !name! \n"
			>>data\update.log 2>&1 echo.[HAVE] !name!
            move /y "%modpath%\!file!" "%staging%\!file!" >nul 2>&1
        ) else (
            bin\bg.exe print 0E "  [MISS] !name! \n"
			>>data\update.log 2>&1 echo.[MISS] !name!
            set /a missing_count+=1
            echo.%%a;%%b;%%c;%%d;%%e>>"data\indexes\missingmods.txt"
        )
		:: Progress Badge
		bin\bg.exe fcprint !y! !x! 1F "         Validating mods... [ !current_count! / %total_mods% ] !percent!%%             \n                                                       "
    )
)
:: --- PHASE 2: THE PURGE (Removing Ghost Mods) ---
dir /b /a-d "%modpath%\" >nul 2>&1
if !errorlevel! EQU 0 (
    bin\bg.exe print 0F " - Purging Old Mods...\n"
	>>data\update.log 2>&1 echo.Purging mods...
    dir /b /a-d "%modpath%\" >>data\update.log 2>&1
	timeout /t 3 >nul
    del /f /q "%modpath%\*.*" >nul 2>&1
)
timeout /t 1 >nul
:: --- PHASE 3: RESTORATION ---
if exist "%staging%\*" (
    xcopy /y /i "%staging%\*" "%modpath%\" >nul 2>&1
)
rd /s /q "%staging%"
>>data\update.log 2>&1 echo.Verification Complete: %total_mods% mods, !missing_count! missing.
echo.Verification Complete: %total_mods% mods, !missing_count! missing.
timeout /t 3 >nul
if !missing_count! GTR 0 (
    call :update.mods.download
)
timeout /t 3 >nul
goto :eof
:update.mods.download
set /a x=!x!+0
echo.Downloading !missing_count! Missing Mods...
timeout /t 2 >nul
set dl_current=0
>>data\update.log 2>&1 echo.Downloading !missing_count! Missing Mods...
for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\missingmods.txt') do (
    set "file=%%b"
    set "name=%%d"
    set /a dl_current+=1
	set /a "percent=(dl_current * 100) / missing_count"
    bin\bg.exe print 0F " - !name!..."
    bin\wget.exe -q "http://%url%/mods/%pack%/!file!" -O "%modpath%\!file!"
    if exist "%modpath%\!file!" (
        call :check.empty "!file!"
    ) else (
        bin\bg.exe print 0C " [FAILED]\n"
    )
	:: Progress Badge at top right (Y=0, X=30 to fit 55 col window)
    bin\bg.exe fcprint !y! !x! 1F "         Downloading mods... [ !dl_current! / !missing_count! ] !percent!%%            \n                                                       "
)
bin\bg.exe print 0F "Mod Download Complete. \n"
>>data\update.log 2>&1 echo.Download Complete.
timeout /t 3 >nul
goto :eof
:check.empty
set "target_file=%~1"
set "fsize=0"
for %%A in ("%modpath%\%target_file%") do set "fsize=%%~zA"
if "!fsize!"=="" set "fsize=0"
if !fsize! EQU 0 (
    bin\bg.exe print 0C " [0 KB ERROR]\n"
    goto :eof
)
:: Simple Size Display logic
if !fsize! LSS 1048576 (
    :: KB Display (Approximate)
    set /a "kb_size=!fsize! / 1024"
    bin\bg.exe print 0A " [!kb_size! KB] [OK]\n"
) else (
    :: MB Display (Approximate)
    set /a "mb_size=!fsize! / 1048576"
    bin\bg.exe print 0A " [!mb_size! MB] [OK]\n"
)
goto :eof
::----------------------------------------------------------------------------------------------------- MAIN UPDATE CALLS
:update type new
cls
call :drawlogo 2
bin\bg.exe Locate 9 0
copy nul bin\.cancelLaunch >nul
del data\update.log 2>nul
set count=
set count_=
::Get the username logged in
for /f %%a in ('type data\indexes\user') do set user=%%a
if "%user%"=="" set user=null
if "%connection%"=="0" echo.*** Offline ***&pause >nul&exit
::IF VERSION NUMBERS ARE EMPTY, SET THEM
::if "%pack_update%"=="" for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version.tmp') do if "%pack%"=="%%a" set pack_update=%%b
::if "%pack_version%"=="" for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version') do if "%pack%"=="%%a" set pack_version=%%b
if not "%2"=="new" bin\wget.exe -q -T 5 -O data\packs\%pack%\PCMod-%pack%.pak http://%url%/updates/PCMod-%pack%.pak
::CLOSE LAUNCHER WINDOW
bin\nircmd.exe win close title "PCMod Launcher - %user%"
echo.--- UPDATE %download% ---
md data\update 2>nul
call :update.download %1 
echo.Update Downloaded.
call :update.extract
if not "%2"=="new" call :update.backup
call :update.install.%1 %2
goto :eof
:update.finalize
cls
call :drawlogo 2
bin\bg.exe Locate 9 0
call :update.verify
echo.Updating Modlist...
call cmd\settings.bat modlist >>data\update.log 2>&1
echo.Finalizing Update...
if "%lite%"=="1" call cmd\settings.bat lite 1 >>data\update.log 2>&1
echo.Cleaning Update...
echo.a | rd /s /q data\update\ 2>nul
::UI option set to exit afterwards
set auto=6
set select_l=!select!
set select=6
::RESTART PCMOD
echo.Restarting PCMod...
timeout /t 2 >nul
start "" "PCMod.hta"
del bin\.cancelLaunch 2>nul
set update_type=empty
goto :eof

::download= pack_2.4.0 or launcher_2.4.0 or 2-4-x
:update.download
::bin\bg.exe Locate 10 0
::Download the size file
set /p "=Getting File Size... " <nul
bin\wget.exe -q http://%url%/%download_dir%/sizes/%download%.size -O data\update\size&title PCMod Update
::Get Sizes of the file and the listed size
FOR /F "tokens=*" %%A IN ("data\update\%download%.zip") DO set size=%%~zA
for /f %%a in ('type data\update\size') do set size_=%%a
echo.%size_:~0,-6%.%size_:~-6,-4% MB
::If Zip file already exists (and has correct size) skip the download
::echo.SIZE: %size_:~0,-6%.%size_:~-6,-5% MB
if exist "data\update\%download%.zip" if "%size%"=="%size_%" echo.Using offline zip file.&goto :eof
if exist "data\update\%download%.zip" if not "%size%"=="%size_%" echo.Size does not match. (%size:~0,-6%.%size:~-6,-5% MB ~= %size_:~0,-6%.%size_:~-6,-5% MB)&echo.Redownloading...&del data\update\%download%.zip 2>data\update_error.log
echo.Downloading File... %download%.zip (%size_:~0,-6%.%size_:~-6,-4% MB)
start /min bin\wget.exe http://%url%/%download_dir%/%download%.zip -O data\update\%download%.zip
set size=0000000
call :update.download.progress
FOR /F "usebackq" %%A IN ('data\update\%download%.zip') DO set size=%%~zA
::If Zip file has correct size go to next step
if "%size%"=="%size_%" goto :eof
if not "%size%"=="%size_%" echo.Size does not match. (%size% ~= %size_%)
set /a retrys=%retrys%+1
echo.Failed to Download file...
echo.Retrying (%retrys%/5)...
timeout /t 10 >nul
if "%retrys%"=="5" echo.Download Failed. Please contact Mark at markrewey@gmail.com&pause >nul&exit /b
del data\update\%download%.zip >>data\update.log 2>&1
goto :update.download
:update.download.progress
set /a percent=100
set bar=
if %size_% geq 1000000 set /a percent=( %size:~0,-6% * 100 ) / %size_:~0,-6%
set /a "fill_bar = (PERCENT * 55) / 100"
for /l %%a in (1,1,%fill_bar%) do set bar=!bar! 
bin\bg.exe fcprint 0 0 70 "                                                       "
bin\bg.exe fcprint 1 0 80 "                                                       "
bin\bg.exe fcprint 0 0 70 "Download %download%: %size:~0,-6%.%size:~-6,-5% MB/%size_:~0,-6%.%size_:~-6,-5% MB (%percent%%%)"
bin\bg.exe fcprint 1 0 F0 "%bar%"
if "%size%"=="%size_%" goto :eof
tasklist /fi "imagename eq wget.exe" | findstr "wget.exe" >nul
if "%errorlevel%"=="1" goto :eof
timeout /t 1 >nul
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
for /f "tokens=*" %%a in ('dir /b data\update\%download%\*') do (
	echo.- %%a
	echo a | xcopy /e /v data\update\%download%\* data\packs\%pack%\ >>data\update.log 2>&1
)
if not "%1"=="new" call :update.version.fix
bin\wget.exe -q http://%url%/update/pack/servers/servers_%pack%.dat -O data\packs\%pack%\servers.dat&title PCMod Update
set pack_version=%pack_update%
timeout /t 1 >nul
goto :eof
:update.version.fix
echo.Updating Version File...
copy nul data\indexes\version.fix >>data\update.log 2>&1
for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version.tmp') do (
	if not "%%a"=="%pack%" >>data\indexes\version.fix echo.%%a;%%b;%%c;%%d;%%e&if "%debug%"=="1" echo.- %%a[%%b]
	if "%%a"=="%pack%" >>data\indexes\version.fix echo.%%a;%pack_update%;%%c;%%d;%%e&echo.- %%a[%pack_version%] --^> %%a[%pack_update%]
)
if "%debug%"=="1" echo.Custom Packs: 
for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version') do (
	set a=0
	for /f "tokens=1 delims=;" %%f in ('type data\indexes\version.tmp') do (
		if "%%a"=="%%f" set a=1
	)
	if "!a!"=="0" >>data\indexes\version.fix echo.%%a;%%b;%%c;%%d;%%e&if "%debug%"=="1" echo.- %%a
)
move data\indexes\version.fix data\indexes\version >>data\update.log 2>&1
goto :eof
:update.install.launcher
echo.Installing Launcher Updates...
echo.- PCMod.hta
copy /v data\update\%download%\PCMod.hta PCMod.hta >>data\update.log 2>&1
echo.- data\*
echo a | xcopy /e /v data\update\%download%\data\* data\ >>data\update.log 2>&1
echo.- bin\*
echo a | xcopy /e /v data\update\%download%\bin\* bin\ >>data\update.log 2>&1
echo.- cmd\*
echo a | xcopy /e /v data\update\%download%\cmd\* cmd\ >>data\update.log 2>&1
set launcher_version=%launcher_update%
goto :eof
:update.backup
echo.Backing Up data...
mkdir data\backup\%pack%\config\ 2>nul
echo.- CONFIG (Local)
echo.a|xcopy /e data\.minecraft\config\* data\backup\%pack%\config\ >>data\update.log 2>&1
echo.- OPTIONS (Local)
echo.y|copy /e data\.minecraft\options.txt data\backup\%pack%\ >>data\update.log 2>&1
goto :eof
::----------------------------------------------------------------------------------------------------- PACK DOWNLOADER
:update.pack.downloader
bin\bg.exe locate 12 0
bin\bg.exe fcprint 8 0 8F  "                    PACK DOWNLOADER                    "
bin\bg.exe fcprint 9 0 0F "ÕÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ¸"
bin\bg.exe fcprint 10 0 0F "³ PACK  ³ VERSION       ³ ModLoader     ³  MCVersion  ³"
bin\bg.exe fcprint 11 0 0F "ÆÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍµ"
for /f "tokens=1-5 delims=;" %%a in ('type data\indexes\version') do (
	if not "%%a"=="Launcher" (
		if not "%%a"=="Vanilla" (
			set a=0
			for /f "tokens=1 delims=;" %%f in ('type data\indexes\version.tmp') do (
				if "%%a"=="%%f" set a=1
			)
			if exist "data\packs\%%a\PCMod-%%a.pak" (
				if "!a!"=="0" echo.³+%%a	³ CUSTOM 	³ %%c 	³  %%d	³
				if "!a!"=="1" echo.³*%%a	³ %%b 	³ %%c 	³  %%d	³
			) else (
				if "!a!"=="0" echo.³?%%a	³ CUSTOM 	³ %%c 	³  %%d	³
				if "!a!"=="1" echo.³ %%a	³ %%b 	³ %%c 	³  %%d	³
			)
		)
	)
)
echo.ÀÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
echo.Type 'exit' to exit
set /p pack_download=PACK SELECTED:
if "%pack_download%"=="exit" goto :eof
if "%pack_download%"=="refresh" goto :update.pack.downloader
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
set pack=%pack_%
goto :eof
:update.pack.downloader.check
::checks
set exists=0
set valid=0
set update=0
for /f "tokens=1 delims=;" %%a in ('type data\indexes\version') do if "%%a"=="%pack_download%" set valid=2
if exist "data\packs\%pack_download%\PCMod-%pack_download%.pak" set exists=1
::logic of the checks
if "%valid%"=="2" if "%exists%"=="1" echo.%pack_download% already exists, do you want to download fresh or update?
if "%valid%"=="2" if "%exists%"=="1" choice /m "Update (U/F):" /c:"uf" /t 8 /d u
if "%valid%"=="2" if "%exists%"=="1" if "%errorlevel%"=="1" set update=1
set /a %1=!valid! + !exists! + !update!
goto :eof
::˜ Copy Right Mark Rewey © (2026)
:: Designed for Plattecraft Server.
:: http://pcmod.ddns.me