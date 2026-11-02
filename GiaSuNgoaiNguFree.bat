@echo off
chcp 65001 >nul
title [GIA SU NGOAI NGU FREE] LUYEN NOI TIENG ANH VA TIENG TRUNG CUNG AI
color 0e

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
        set "PATH=%LOCALAPPDATA%\Microsoft\WindowsApps;%PATH%"
    )
)

echo ======================================================================
echo    GIA SƯ NGOẠI NGỮ FREE - HỌC NÓI TIẾNG ANH VÀ TIẾNG TRUNG MIỄN PHÍ
echo ======================================================================
echo.
echo  [1/2] Đang khởi động hệ thống Gia sư AI...
echo  [2/2] Trình duyệt web sẽ tự động mở sau 1-2 giây!
echo.
echo ----------------------------------------------------------------------
echo   * Tên ứng dụng: Gia Sư Ngoại Ngữ Free
echo   * Tác giả phát triển: THANHBOOKS (Đoàn Đức Thanh)
echo   * Hỗ trợ: Tiếng Anh (US/UK) và Tiếng Trung (Hanzi + Pinyin + Dịch nghĩa)
echo   * Tích hợp: Trí tuệ nhân tạo AI thông minh (Miễn phí 100%%)
echo   * Nhấn phím Ctrl + C để tắt ứng dụng khi học xong
echo ----------------------------------------------------------------------
echo.

python app.py
if %errorlevel% neq 0 (
    echo.
    echo ======================================================================
    echo  [LỖI] Máy chủ đã dừng hoặc gặp sự cố (Mã thoát: %errorlevel%).
    echo ======================================================================
    pause
)
