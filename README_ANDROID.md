# 图片资源嗅探工具 - Android版本

这是一个专为Android设备设计的图片资源嗅探工具，使用Kivy框架开发，可以打包成APK在Android手机上运行。

## 功能特点

- 🔍 根据输入的网址自动嗅探所有图片资源
- 📱 专为移动端优化的用户界面
- 🖼️ 支持图片预览功能
- 📥 支持单张图片下载和批量下载
- 📏 支持按图片大小过滤（排除小于指定大小的图片）
- 🔄 自动尝试获取原始图片而非压缩版本
- 📱 支持Android权限管理
- 💾 自动保存到手机下载目录

## 技术特点

### 移动端优化
- 使用轻量级的HTML解析，无需Selenium
- 减少内存占用和CPU使用
- 优化网络请求，支持移动网络环境
- 适配Android存储权限

### 图片嗅探算法
- 支持多种图片格式：JPG、PNG、GIF、WebP、BMP
- 智能识别懒加载图片（data-src属性）
- 提取CSS背景图片
- 自动尝试获取原始尺寸图片
- 支持相对URL转绝对URL

## 构建APK

### 环境要求
- Ubuntu 18.04+ 或其他Linux发行版
- Python 3.7+
- Java 8
- 至少8GB可用磁盘空间

### 快速开始

1. **克隆项目**
```bash
git clone <项目地址>
cd image_resource_sniffing
```

2. **运行安装脚本**
```bash
chmod +x install_android.sh
./install_android.sh
```

3. **构建APK**
```bash
buildozer android debug
```

4. **安装APK**
生成的APK文件位于 `bin/` 目录下，可以传输到Android设备安装。

### 手动构建步骤

如果自动脚本失败，可以手动执行以下步骤：

1. **安装Buildozer**
```bash
pip3 install buildozer cython
```

2. **安装系统依赖**
```bash
# Ubuntu/Debian
sudo apt-get install -y build-essential git python3 python3-dev ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev openjdk-8-jdk unzip

# 设置Java环境
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
```

3. **初始化构建环境**
```bash
buildozer init
```

4. **构建APK**
```bash
buildozer android debug
```

## 使用方法

### 在Android设备上使用

1. **安装APK**
   - 将生成的APK文件传输到Android设备
   - 在设备上启用"未知来源"应用安装
   - 点击APK文件进行安装

2. **授予权限**
   - 首次运行时会请求网络和存储权限
   - 请允许这些权限以确保应用正常工作

3. **嗅探图片**
   - 在"网址"输入框中输入要嗅探的网页URL
   - 设置"最小大小"过滤条件（默认10KB）
   - 点击"开始嗅探"按钮
   - 等待嗅探完成

4. **预览和下载**
   - 点击图片列表中的"预览"按钮查看图片
   - 在预览界面可以下载单张图片
   - 使用"批量下载"按钮下载所有图片
   - 图片将保存到 `/sdcard/Download/ImageSniffer/` 目录

## 配置说明

### buildozer.spec 配置文件

主要配置项说明：

- `title`: 应用标题
- `package.name`: 包名
- `package.domain`: 包域名
- `version`: 应用版本
- `requirements`: Python依赖包
- `android.permissions`: Android权限
- `android.api`: 目标Android API版本
- `android.minapi`: 最低支持的Android API版本

### 权限说明

应用需要以下权限：
- `INTERNET`: 访问网络获取网页内容和图片
- `WRITE_EXTERNAL_STORAGE`: 保存图片到存储设备
- `READ_EXTERNAL_STORAGE`: 读取存储设备内容
- `ACCESS_NETWORK_STATE`: 检查网络状态

## 故障排除

### 常见构建问题

1. **Java版本问题**
```bash
# 确保使用Java 8
sudo update-alternatives --config java
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
```

2. **NDK下载失败**
```bash
# 手动下载NDK并设置路径
buildozer android debug --verbose
```

3. **权限问题**
```bash
# 确保有足够的磁盘空间和权限
sudo chown -R $USER:$USER ~/.buildozer
```

### 运行时问题

1. **网络连接失败**
   - 检查设备网络连接
   - 确认目标网站可以正常访问
   - 某些网站可能有反爬虫机制

2. **图片下载失败**
   - 检查存储权限是否已授予
   - 确认设备有足够的存储空间
   - 某些图片可能需要特殊的访问权限

3. **应用崩溃**
   - 查看Android日志：`adb logcat | grep python`
   - 检查是否有未处理的异常

## 开发说明

### 项目结构
```
image_resource_sniffing/
├── main.py              # 主应用文件
├── buildozer.spec       # Buildozer配置文件
├── requirements.txt     # Python依赖
├── install_android.sh   # 安装脚本
└── README_ANDROID.md    # 说明文档
```

### 核心类说明

- `ImageSniffer`: 图片嗅探核心类
- `ImageInfo`: 图片信息数据类
- `MainScreen`: 主界面屏幕
- `ImageListItem`: 图片列表项组件
- `ImagePreviewPopup`: 图片预览弹窗
- `ImageSnifferApp`: 主应用类

### 自定义修改

如需修改应用功能，主要修改 `main.py` 文件：

1. **修改嗅探算法**: 编辑 `ImageSniffer` 类
2. **修改界面布局**: 编辑 `MainScreen` 类
3. **添加新功能**: 在相应的类中添加方法

修改后重新构建APK：
```bash
buildozer android debug
```

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至开发者邮箱