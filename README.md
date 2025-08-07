# 图片资源嗅探工具

一个功能强大的网页图片资源嗅探工具，支持Python脚本和Web版本两种使用方式。

## 🌟 功能特点

- 🔍 智能嗅探网页中的所有图片资源
- ⏱️ 支持等待所有图片加载完成
- 🔄 处理懒加载的图片资源（data-src属性）
- 🖼️ 尝试获取原始图片而非压缩版本
- 📏 支持按图片大小过滤（排除小于指定大小的图片）
- 👀 支持图片预览和批量下载
- 💻 提供GUI和命令行两种界面
- 📱 Web版本支持所有设备

## 🚀 快速开始

### 方式一：Python脚本（推荐）

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### GUI模式（图形界面）
```bash
python image_sniffer.py
```

#### 命令行模式
```bash
# 基本使用
python image_sniffer.py --cli --url https://example.com

# 完整参数
python image_sniffer.py --cli --url https://example.com --min-size 10 --wait-time 5 --output results.json --download-dir ./images
```

### 方式二：Web版本

直接用浏览器打开 `web_version.html` 即可使用，支持所有设备。

## 📋 参数说明

### 命令行参数
- `--cli`: 使用命令行模式
- `--url`: 要嗅探的网页URL（必需）
- `--min-size`: 最小图片大小（KB），默认为10KB
- `--wait-time`: 页面加载等待时间（秒），默认为5秒
- `--output`: 输出结果的JSON文件路径（可选）
- `--download-dir`: 图片下载目录（可选）

### GUI界面功能
- 输入网址和参数
- 实时进度显示
- 图片列表展示
- 双击预览图片
- 单张或批量下载
- 自定义下载目录

## 🔧 核心功能

### 智能嗅探算法
- 提取img标签中的src属性
- 支持懒加载图片（data-src属性）
- 提取CSS背景图片
- 提取链接中的图片资源
- 自动去重和过滤

### 原图获取
- 智能识别缩略图URL模式
- 自动尝试获取原始大图
- 支持多种常见的缩略图命名规则

### 并发处理
- 多线程并发获取图片信息
- 带重试机制的网络请求
- 智能超时处理

## 📁 文件说明

- `image_sniffer.py` - 主程序文件（Python脚本）
- `web_version.html` - Web版本（浏览器直接打开）
- `requirements.txt` - Python依赖包
- `README.md` - 项目说明（本文件）
- `USAGE.md` - 详细使用说明

## 💡 使用示例

### 命令行示例
```bash
# 嗅探图片并保存结果
python image_sniffer.py --cli --url https://example.com --min-size 50 --output images.json

# 嗅探并直接下载
python image_sniffer.py --cli --url https://example.com --download-dir ./downloads

# 设置等待时间（适用于需要加载时间的页面）
python image_sniffer.py --cli --url https://example.com --wait-time 10
```

### GUI使用流程
1. 运行 `python image_sniffer.py`
2. 输入要嗅探的网址
3. 设置最小图片大小和等待时间
4. 点击"开始嗅探"
5. 查看结果列表，双击可预览图片
6. 选择下载目录，点击"批量下载"

### Web版本使用
1. 用浏览器打开 `web_version.html`
2. 输入网址和参数
3. 点击"开始嗅探"
4. 预览和下载图片

## ⚠️ 注意事项

1. **网络限制**：某些网站可能有防爬虫机制
2. **跨域问题**：Web版本可能受到浏览器CORS限制
3. **图片格式**：支持常见的图片格式（JPG、PNG、GIF、WebP等）
4. **使用规范**：请遵守网站的robots.txt和使用条款
5. **版权声明**：不要用于商业用途或侵犯版权

## 🎯 适用场景

- 网页图片批量下载
- 设计素材收集
- 图片资源整理
- 网站图片分析
- 学习研究用途

## 🔧 技术特性

- **多线程处理**：提高嗅探效率
- **智能重试**：网络异常自动重试
- **原图识别**：尝试获取高清原图
- **进度反馈**：实时显示处理进度
- **跨平台**：支持Windows、macOS、Linux

## 📊 性能优化

- 使用连接池复用HTTP连接
- 并发处理图片信息获取
- 智能超时和重试机制
- 内存友好的流式下载

---

**完全免费 | 开源项目 | 持续更新**

如有问题或建议，欢迎提交Issue！