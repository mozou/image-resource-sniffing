#!/bin/bash

# 本地构建脚本
# 需要预先安装Android SDK、NDK和Python环境

echo "🔍 检查构建环境..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查Java
if ! command -v java &> /dev/null; then
    echo "❌ Java 未安装"
    exit 1
fi

echo "✅ 基础环境检查通过"

# 安装Python依赖
echo "📦 安装Python依赖..."
pip3 install --user buildozer cython kivy requests

# 检查buildozer
if ! command -v buildozer &> /dev/null; then
    echo "❌ Buildozer 安装失败"
    echo "请手动安装: pip3 install --user buildozer"
    exit 1
fi

echo "✅ Buildozer 已安装"

# 显示版本信息
echo "📋 环境信息:"
echo "Python: $(python3 --version)"
echo "Java: $(java -version 2>&1 | head -n 1)"
echo "Buildozer: $(buildozer version)"

# 构建APK
echo "🚀 开始构建APK..."
buildozer android debug

# 检查结果
if [ -f "bin/*.apk" ]; then
    echo "🎉 构建成功！"
    echo "APK文件位置: $(ls bin/*.apk)"
else
    echo "❌ 构建失败"
    echo "请检查上面的错误信息"
    exit 1
fi