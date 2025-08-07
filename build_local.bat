@echo off
echo 🔍 检查构建环境...

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装
    pause
    exit /b 1
)

REM 检查Java
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Java 未安装
    pause
    exit /b 1
)

echo ✅ 基础环境检查通过

REM 安装Python依赖
echo 📦 安装Python依赖...
pip install buildozer cython kivy requests

REM 检查buildozer
buildozer version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Buildozer 安装失败
    echo 请手动安装: pip install buildozer
    pause
    exit /b 1
)

echo ✅ Buildozer 已安装

REM 显示版本信息
echo 📋 环境信息:
python --version
java -version
buildozer version

REM 构建APK
echo 🚀 开始构建APK...
buildozer android debug

REM 检查结果
if exist "bin\*.apk" (
    echo 🎉 构建成功！
    dir bin\*.apk
) else (
    echo ❌ 构建失败
    echo 请检查上面的错误信息
)

pause