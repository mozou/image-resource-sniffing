# 使用GitHub Actions自动构建Android APK

本项目已配置GitHub Actions工作流，可以自动在云端构建Android APK，无需本地安装复杂的构建环境。

## 🚀 快速开始

### 1. 推送代码到GitHub

```bash
# 初始化Git仓库（如果还没有）
git init

# 添加所有文件
git add .

# 提交代码
git commit -m "初始提交：图片资源嗅探工具"

# 添加远程仓库（替换为您的GitHub仓库地址）
git remote add origin https://github.com/您的用户名/image-resource-sniffer.git

# 推送到GitHub
git push -u origin main
```

### 2. 自动构建触发

构建会在以下情况自动触发：
- 推送代码到 `main` 或 `master` 分支
- 创建Pull Request
- 手动触发（在GitHub仓库的Actions页面）

### 3. 下载APK

构建完成后，您可以通过以下方式获取APK：

#### 方式一：从Actions页面下载
1. 访问您的GitHub仓库
2. 点击 "Actions" 标签页
3. 选择最新的构建任务
4. 在 "Artifacts" 部分下载APK文件

#### 方式二：从Releases页面下载（推荐）
1. 访问您的GitHub仓库
2. 点击 "Releases" 标签页
3. 下载最新版本的APK文件

## 📋 构建配置说明

### 工作流文件位置
`.github/workflows/build-android.yml`

### 构建环境
- **操作系统**: Ubuntu Latest
- **Python版本**: 3.9
- **Java版本**: 11
- **构建工具**: Buildozer + Cython

### 构建步骤
1. 检出代码
2. 设置Python和Java环境
3. 安装系统依赖（SDL2、FFmpeg等）
4. 缓存依赖以加速构建
5. 安装Python依赖
6. 使用Buildozer构建APK
7. 上传APK文件
8. 创建GitHub Release（仅main分支）

### 缓存机制
为了加速构建，工作流使用了以下缓存：
- pip依赖缓存
- buildozer构建缓存

首次构建可能需要20-30分钟，后续构建通常在10-15分钟内完成。

## 🔧 自定义构建

### 修改构建配置

如需修改构建配置，编辑 `buildozer.spec` 文件：

```ini
# 修改应用名称
title = 您的应用名称

# 修改包名
package.name = yourapppname
package.domain = com.yourcompany

# 修改版本
version = 1.1

# 添加新的依赖
requirements = python3,kivy,requests,新依赖包名
```

### 手动触发构建

1. 访问GitHub仓库的Actions页面
2. 选择 "构建Android APK" 工作流
3. 点击 "Run workflow" 按钮
4. 选择分支并点击 "Run workflow"

### 构建不同版本

默认构建debug版本，如需构建release版本：

1. 修改 `.github/workflows/build-android.yml`
2. 将 `buildozer android debug` 改为 `buildozer android release`
3. 需要配置签名密钥（见下方说明）

## 🔐 配置应用签名（Release版本）

如需构建正式发布的APK，需要配置签名：

### 1. 生成签名密钥

```bash
keytool -genkey -v -keystore my-release-key.keystore -alias my-key-alias -keyalg RSA -keysize 2048 -validity 10000
```

### 2. 配置GitHub Secrets

在GitHub仓库设置中添加以下Secrets：
- `KEYSTORE_FILE`: 密钥文件的base64编码
- `KEYSTORE_PASSWORD`: 密钥库密码
- `KEY_ALIAS`: 密钥别名
- `KEY_PASSWORD`: 密钥密码

### 3. 修改buildozer.spec

```ini
[app]
# ... 其他配置 ...

# 签名配置
android.release_artifact = aab
android.debug_artifact = apk

[buildozer]
# 签名配置
android.keystore = my-release-key.keystore
android.keyalias = my-key-alias
```

## 📱 APK安装说明

### Android设备安装步骤

1. **下载APK文件**
   - 从GitHub Releases页面下载最新的APK文件

2. **启用未知来源安装**
   - 打开设置 → 安全 → 未知来源
   - 或者在安装时选择"允许此来源"

3. **安装APK**
   - 点击下载的APK文件
   - 按照提示完成安装

4. **授予权限**
   - 首次运行时会请求网络和存储权限
   - 请点击"允许"以确保应用正常工作

### 权限说明

应用需要以下权限：
- **网络访问**: 获取网页内容和下载图片
- **存储访问**: 保存图片到设备存储
- **网络状态**: 检查网络连接状态

## 🐛 故障排除

### 构建失败

1. **检查构建日志**
   - 在Actions页面查看详细的构建日志
   - 查找错误信息和失败原因

2. **常见问题**
   - 依赖包版本冲突：检查requirements.txt
   - buildozer.spec配置错误：验证配置语法
   - 网络问题：重新运行构建

3. **清除缓存**
   - 在Actions页面删除缓存
   - 重新触发构建

### 应用运行问题

1. **安装失败**
   - 确认Android版本兼容性（最低API 21，Android 5.0）
   - 检查设备存储空间

2. **权限问题**
   - 手动在设置中授予应用权限
   - 重启应用

3. **网络问题**
   - 检查设备网络连接
   - 尝试不同的网址

## 📈 版本管理

### 自动版本号

每次推送到main分支时，会自动创建新的Release，版本号格式为 `v{构建编号}`。

### 手动版本号

如需使用自定义版本号，修改 `buildozer.spec` 中的version字段：

```ini
version = 1.2.3
```

## 🤝 贡献指南

1. Fork本仓库
2. 创建功能分支：`git checkout -b feature/新功能`
3. 提交更改：`git commit -am '添加新功能'`
4. 推送分支：`git push origin feature/新功能`
5. 创建Pull Request

Pull Request会自动触发构建，确保代码质量。

## 📞 支持

如遇到问题，请：
1. 查看构建日志
2. 搜索已有的Issues
3. 创建新的Issue并提供详细信息

---

通过GitHub Actions，您可以轻松地在云端构建Android APK，无需复杂的本地环境配置！