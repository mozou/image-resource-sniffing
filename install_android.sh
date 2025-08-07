#!/bin/bash

# 图片资源嗅探工具 - Android APK 构建脚本

echo "开始安装构建环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

echo "Python版本: $python_version"

# 安装依赖
echo "安装Python依赖..."
pip3 install --upgrade pip
pip3 install buildozer cython

# 安装Android构建依赖 (Ubuntu/Debian)
if command -v apt-get &> /dev/null; then
    echo "检测到Ubuntu/Debian系统，安装构建依赖..."
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        git \
        python3 \
        python3-dev \
        ffmpeg \
        libsdl2-dev \
        libsdl2-image-dev \
        libsdl2-mixer-dev \
        libsdl2-ttf-dev \
        libportmidi-dev \
        libswscale-dev \
        libavformat-dev \
        libavcodec-dev \
        zlib1g-dev \
        libgstreamer1.0 \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        openjdk-8-jdk \
        unzip
fi

# 设置Java环境变量
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin

echo "环境安装完成！"
echo ""
echo "构建APK步骤："
echo "1. 运行: buildozer android debug"
echo "2. APK文件将生成在 bin/ 目录下"
echo ""
echo "注意事项："
echo "- 首次构建可能需要很长时间（下载Android SDK/NDK）"
echo "- 确保网络连接稳定"
echo "- 如果构建失败，请检查错误信息并重试"