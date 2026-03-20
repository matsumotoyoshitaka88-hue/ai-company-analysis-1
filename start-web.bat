@echo off
set PATH=C:\Program Files\nodejs;C:\Users\info\AppData\Roaming\npm;%PATH%
cd /d "%~dp0apps\web"
npx next dev --turbopack --port 3000
