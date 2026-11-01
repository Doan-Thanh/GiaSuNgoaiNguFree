@echo off
title Push GiaSuNgoaiNguFree to GitHub
color 0a

cd /d "%~dp0"

echo ======================================================================
echo    DANG DAY CODE LEN GITHUB: Doan-Thanh / GiaSuNgoaiNguFree
echo ======================================================================
echo.

git branch -M main
git push -u origin main

echo.
echo ======================================================================
echo    DA XU LY XONG! 
echo    Hay xem thong bao cua Git o phia tren.
echo    Neu thay "branch main set up to track origin/main" la thanh cong!
echo ======================================================================
echo.
pause
