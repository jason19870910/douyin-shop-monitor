@echo off
cd c:\Users\Administrator\Documents\trae_projects\douyin\src\frontend
node_modules\.bin\tsc --noEmit 2>errors.txt
echo Exit code: %errorlevel%