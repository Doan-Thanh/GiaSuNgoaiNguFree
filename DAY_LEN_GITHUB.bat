@echo off
chcp 65001 >nul
title DAY CODE LEN GITHUB: Doan-Thanh/GiaSuNgoaiNguFree
color 0a

echo ======================================================================
echo    DANG DAY CODE LEN GITHUB: https://github.com/Doan-Thanh/GiaSuNgoaiNguFree
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/2] Đang kiểm tra nhánh main và remote...
git branch -M main

echo [2/2] Đang đẩy code lên GitHub...
echo (Lưu ý: Nếu trình duyệt hiện popup đăng nhập GitHub, bạn chỉ cần bấm "Sign in with your browser").
echo.
git push -u origin main

echo.
if %errorlevel% equ 0 (
    echo ======================================================================
    echo    🎉 ĐÃ ĐẨY CODE LÊN GITHUB THÀNH CÔNG!
    echo    Xem mã nguồn tại: https://github.com/Doan-Thanh/GiaSuNgoaiNguFree
    echo ======================================================================
) else (
    echo ======================================================================
    echo    ⚠️ CHƯA ĐẨY ĐƯỢC!
    echo    Hãy chắc chắn bạn đã vào https://github.com/new và bấm "Create repository"
    echo    với đúng tên: GiaSuNgoaiNguFree
    echo ======================================================================
)

pause
