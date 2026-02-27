@echo off
echo ===================================================
echo 🚀 TechPulse AI 启动器
echo ===================================================
echo.

echo 1. 启动Web服务 (http://localhost:5000)
echo 2. 启动定时任务 (每天8:00/20:00更新)
echo 3. 同时启动两者
echo.

set /p choice="请选择 (1/2/3): "

if "%choice%"=="1" goto web
if "%choice%"=="2" goto scheduler
if "%choice%"=="3" goto both
goto end

:web
echo.
echo 🌐 启动Web服务...
start cmd /k "python app.py"
goto end

:scheduler
echo.
echo ⏰ 启动定时任务...
start cmd /k "python scheduler.py"
goto end

:both
echo.
echo 🌐 启动Web服务...
start cmd /k "python app.py"
echo ⏰ 启动定时任务...
start cmd /k "python scheduler.py"
goto end

:end
echo.
echo ✅ 启动完成！
pause