# 图片资源嗅探工具

这是一个用于自动嗅探网页中所有图片资源的工具，支持嗅探完成后预览和批量下载。**特别针对Android移动端进行了优化，支持打包成APK在手机上运行。**

## 🌟 功能特点

- 🔍 根据输入的链接，自动嗅探该链接中的所有图片资源
- ⏱️ 支持等待所有图片加载完成
- 🔄 处理懒加载的图片资源（data-src属性）
- 🖼️ 尝试获取原始图片而非压缩版本
- 📏 支持按图片大小过滤（排除小于指定大小的图片）
- 👀 支持图片预览和批量下载
- 📱 **移动端友好的触摸界面**
- 🤖 **支持打包成Android APK**
- ☁️ **GitHub Actions自动构建**

## 📱 Android版本（推荐）

### 快速获取APK

1. **从GitHub Releases下载**（推荐）
   - 访问本项目的[Releases页面](../../releases)
   - 下载最新版本的APK文件

2. **自动构建**
   - Fork本项目到您的GitHub账户
   - 推送代码会自动触发构建
   - 在Actions页面下载构建好的APK

### 本地构建APK

如果您想本地构建，请参考 [README_ANDROID.md](README_ANDROID.md) 的详细说明。

### GitHub Actions构建（推荐）

我们提供了多种构建方案：

**方案一：Docker自动构建**
```bash
git add .
git commit -m "更新代码"
git push origin main
```
推送后会自动使用Docker构建APK，避免环境配置问题。

**方案二：手动触发备用构建**
1. 进入GitHub仓库的Actions页面
2. 选择"构建Android APK (备用方案)"
3. 点击"Run workflow"手动触发

**方案三：本地构建**
```bash
# Linux/Mac
chmod +x build_local.sh
./build_local.sh

# Windows
build_local.bat
```

详细说明请参考：[README_GITHUB_ACTIONS.md](README_GITHUB_ACTIONS.md)

## 🔧 技术架构

### 移动端版本 (main.py)
- **框架**: Kivy（跨平台移动应用框架）
- **网络**: requests + 正则表达式解析
- **优势**: 轻量级、无需浏览器、适合移动端、支持Android打包


## 📂 项目结构

```
image_resource_sniffing/
├── main.py                   # Android版本主文件
├── buildozer.spec           # Android构建配置
├── requirements.txt         # Python依赖
├── .github/workflows/       # GitHub Actions配置
├── README.md                # 主说明文档
├── README_ANDROID.md        # Android版本说明
└── README_GITHUB_ACTIONS.md # GitHub Actions说明
```

## 🚀 快速开始

### 方式一：直接使用APK（推荐）
1. 从[Releases页面](../../releases)下载APK
2. 在Android设备上安装
3. 授予网络和存储权限
4. 开始使用

### 方式二：Fork并自动构建
1. Fork本项目
2. 推送代码到您的仓库
3. GitHub Actions自动构建APK
4. 从您的仓库Releases页面下载

### 方式三：本地运行移动端版本
1. 克隆项目：`git clone ...`
2. 安装依赖：`pip install -r requirements.txt`
3. 运行：`python main.py`

## 📋 注意事项

1. **Android版本**：
   - 需要Android 5.0+（API 21+）
   - 首次运行需要授予网络和存储权限
   - 图片保存在 `/sdcard/Download/ImageSniffer/` 目录

2. **通用注意事项**：
   - 请遵守网站的robots.txt和使用条款
   - 不要用于商业用途或侵犯版权
   - 建议设置合理的请求间隔，避免对服务器造成压力
