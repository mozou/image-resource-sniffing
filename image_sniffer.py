#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片资源嗅探工具 - Python版本
支持命令行和GUI两种模式
"""

import os
import re
import json
import time
import argparse
import threading
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    from PIL import Image, ImageTk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("GUI依赖未安装，仅支持命令行模式")


class ImageInfo:
    """图片信息类"""
    def __init__(self, url, size=0, width=0, height=0, content_type=''):
        self.url = url
        self.size = size
        self.width = width
        self.height = height
        self.content_type = content_type
        self.filename = self._extract_filename()
    
    def _extract_filename(self):
        """从URL提取文件名"""
        parsed = urlparse(self.url)
        filename = os.path.basename(parsed.path)
        if not filename or '.' not in filename:
            # 根据content_type推断扩展名
            ext = '.jpg'
            if 'png' in self.content_type.lower():
                ext = '.png'
            elif 'gif' in self.content_type.lower():
                ext = '.gif'
            elif 'webp' in self.content_type.lower():
                ext = '.webp'
            filename = f"image_{hash(self.url) % 10000}{ext}"
        return filename
    
    def to_dict(self):
        """转换为字典"""
        return {
            'url': self.url,
            'filename': self.filename,
            'size': self.size,
            'width': self.width,
            'height': self.height,
            'content_type': self.content_type
        }


class ImageSniffer:
    """图片嗅探器"""
    
    def __init__(self):
        self.session = self._create_session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    def _create_session(self):
        """创建带重试机制的会话"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _get_page_content(self, url):
        """获取页面内容"""
        headers = {
            'User-Agent': self.user_agents[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise Exception(f"获取页面失败: {str(e)}")
    
    def _extract_images_from_html(self, html_content, base_url):
        """从HTML内容中提取图片URL"""
        image_urls = set()
        
        # 提取img标签中的src
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        for match in re.finditer(img_pattern, html_content, re.IGNORECASE):
            url = match.group(1)
            full_url = urljoin(base_url, url)
            if self._is_image_url(full_url):
                image_urls.add(full_url)
        
        # 提取img标签中的data-src（懒加载）
        data_src_pattern = r'<img[^>]+data-src=["\']([^"\']+)["\'][^>]*>'
        for match in re.finditer(data_src_pattern, html_content, re.IGNORECASE):
            url = match.group(1)
            full_url = urljoin(base_url, url)
            if self._is_image_url(full_url):
                image_urls.add(full_url)
        
        # 提取CSS背景图片
        bg_pattern = r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)'
        for match in re.finditer(bg_pattern, html_content, re.IGNORECASE):
            url = match.group(1)
            full_url = urljoin(base_url, url)
            if self._is_image_url(full_url):
                image_urls.add(full_url)
        
        # 提取链接中的图片
        link_pattern = r'<a[^>]+href=["\']([^"\']+\.(jpg|jpeg|png|gif|webp|bmp))["\'][^>]*>'
        for match in re.finditer(link_pattern, html_content, re.IGNORECASE):
            url = match.group(1)
            full_url = urljoin(base_url, url)
            image_urls.add(full_url)
        
        return list(image_urls)
    
    def _is_image_url(self, url):
        """判断URL是否为图片"""
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg')
        parsed = urlparse(url.lower())
        return any(parsed.path.endswith(ext) for ext in image_extensions) or 'image' in parsed.path
    
    def _get_image_info(self, url):
        """获取图片信息"""
        try:
            # 先尝试HEAD请求
            headers = {'User-Agent': self.user_agents[0]}
            response = self.session.head(url, headers=headers, timeout=10, allow_redirects=True)
            
            if response.status_code != 200:
                # 如果HEAD失败，尝试GET请求
                response = self.session.get(url, headers=headers, timeout=10, stream=True)
            
            content_type = response.headers.get('Content-Type', '')
            content_length = int(response.headers.get('Content-Length', 0))
            
            # 如果没有Content-Length，尝试获取部分内容来估算大小
            if content_length == 0 and hasattr(response, 'iter_content'):
                chunk_size = 8192
                total_size = 0
                for chunk in response.iter_content(chunk_size):
                    total_size += len(chunk)
                    if total_size > 1024 * 1024:  # 限制最大1MB用于检测
                        break
                content_length = total_size
            
            return ImageInfo(url, content_length, 0, 0, content_type)
            
        except Exception as e:
            print(f"获取图片信息失败 {url}: {str(e)}")
            return ImageInfo(url, 0, 0, 0, '')
    
    def _try_get_original_image(self, url):
        """尝试获取原始图片URL"""
        # 常见的缩略图到原图的转换规则
        replacements = [
            ('_thumb', ''),
            ('_small', ''),
            ('_medium', ''),
            ('-thumb', ''),
            ('-small', ''),
            ('-medium', ''),
            ('thumb_', ''),
            ('small_', ''),
            ('medium_', ''),
            ('_t.', '.'),
            ('_s.', '.'),
            ('_m.', '.'),
        ]
        
        original_candidates = [url]  # 原URL作为候选
        
        for old, new in replacements:
            if old in url:
                candidate = url.replace(old, new)
                original_candidates.append(candidate)
        
        # 测试哪个URL返回更大的图片
        best_url = url
        best_size = 0
        
        for candidate in original_candidates:
            try:
                response = self.session.head(candidate, timeout=5)
                if response.status_code == 200:
                    size = int(response.headers.get('Content-Length', 0))
                    if size > best_size:
                        best_size = size
                        best_url = candidate
            except:
                continue
        
        return best_url
    
    def sniff_images(self, url, min_size_kb=10, wait_time=5, progress_callback=None):
        """嗅探图片"""
        try:
            if progress_callback:
                progress_callback("正在获取页面内容...", 0.1)
            
            # 获取页面内容
            html_content = self._get_page_content(url)
            
            if progress_callback:
                progress_callback("正在提取图片链接...", 0.3)
            
            # 提取图片URL
            image_urls = self._extract_images_from_html(html_content, url)
            
            if not image_urls:
                return []
            
            if progress_callback:
                progress_callback(f"找到 {len(image_urls)} 个图片链接，正在获取详细信息...", 0.5)
            
            # 尝试获取原始图片
            original_urls = []
            for img_url in image_urls:
                original_url = self._try_get_original_image(img_url)
                original_urls.append(original_url)
            
            # 获取图片信息
            images = []
            min_size_bytes = min_size_kb * 1024
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(self._get_image_info, url) for url in original_urls]
                
                for i, future in enumerate(as_completed(futures)):
                    try:
                        img_info = future.result(timeout=15)
                        if img_info.size >= min_size_bytes:
                            images.append(img_info)
                        
                        if progress_callback:
                            progress = 0.5 + (i + 1) / len(futures) * 0.4
                            progress_callback(f"已处理 {i + 1}/{len(futures)} 张图片", progress)
                    except Exception as e:
                        print(f"处理图片时出错: {str(e)}")
            
            # 按大小排序
            images.sort(key=lambda x: x.size, reverse=True)
            
            if progress_callback:
                progress_callback(f"嗅探完成，找到 {len(images)} 张符合条件的图片", 1.0)
            
            return images
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"嗅探失败: {str(e)}", 1.0)
            raise
    
    def download_images(self, images, download_dir, progress_callback=None):
        """批量下载图片"""
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        downloaded = 0
        total = len(images)
        
        for i, img_info in enumerate(images):
            try:
                if progress_callback:
                    progress_callback(f"正在下载 {i+1}/{total}: {img_info.filename}", i / total)
                
                # 下载图片
                response = self.session.get(img_info.url, stream=True, timeout=30)
                response.raise_for_status()
                
                file_path = os.path.join(download_dir, img_info.filename)
                
                # 确保文件名唯一
                counter = 1
                base_name, ext = os.path.splitext(file_path)
                while os.path.exists(file_path):
                    file_path = f"{base_name}_{counter}{ext}"
                    counter += 1
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                downloaded += 1
                print(f"已下载: {img_info.filename}")
                
            except Exception as e:
                print(f"下载失败 {img_info.filename}: {str(e)}")
        
        if progress_callback:
            progress_callback(f"下载完成: {downloaded}/{total}", 1.0)
        
        return downloaded


class ImageSnifferGUI:
    """图片嗅探器GUI界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("图片资源嗅探工具")
        self.root.geometry("800x600")
        
        self.sniffer = ImageSniffer()
        self.images = []
        self.download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'ImageSniffer')
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="输入参数", padding="10")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # URL输入
        ttk.Label(input_frame, text="网址:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(input_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 参数设置
        ttk.Label(input_frame, text="最小大小(KB):").grid(row=2, column=0, sticky=tk.W)
        self.min_size_var = tk.StringVar(value="10")
        ttk.Entry(input_frame, textvariable=self.min_size_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=(5, 20))
        
        ttk.Label(input_frame, text="等待时间(秒):").grid(row=2, column=2, sticky=tk.W)
        self.wait_time_var = tk.StringVar(value="5")
        ttk.Entry(input_frame, textvariable=self.wait_time_var, width=10).grid(row=2, column=3, sticky=tk.W, padx=(5, 0))
        
        # 按钮区域
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(10, 0))
        
        self.sniff_btn = ttk.Button(button_frame, text="开始嗅探", command=self.start_sniffing)
        self.sniff_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.download_btn = ttk.Button(button_frame, text="批量下载", command=self.download_all, state=tk.DISABLED)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="选择下载目录", command=self.select_download_dir).pack(side=tk.LEFT)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # 结果区域
        result_frame = ttk.LabelFrame(main_frame, text="嗅探结果", padding="10")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 结果列表
        columns = ('文件名', '大小', 'URL')
        self.tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('文件名', text='文件名')
        self.tree.heading('大小', text='大小(KB)')
        self.tree.heading('URL', text='URL')
        
        self.tree.column('文件名', width=200)
        self.tree.column('大小', width=100)
        self.tree.column('URL', width=400)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 双击预览
        self.tree.bind('<Double-1>', self.preview_image)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        input_frame.columnconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
    
    def update_progress(self, message, progress):
        """更新进度"""
        self.status_var.set(message)
        self.progress_var.set(progress * 100)
        self.root.update_idletasks()
    
    def start_sniffing(self):
        """开始嗅探"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入有效的URL")
            return
        
        try:
            min_size = int(self.min_size_var.get())
            wait_time = int(self.wait_time_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return
        
        # 清空结果
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.images = []
        self.download_btn.config(state=tk.DISABLED)
        
        # 禁用按钮
        self.sniff_btn.config(state=tk.DISABLED)
        
        # 在新线程中执行嗅探
        threading.Thread(
            target=self._sniff_thread,
            args=(url, min_size, wait_time),
            daemon=True
        ).start()
    
    def _sniff_thread(self, url, min_size, wait_time):
        """嗅探线程"""
        try:
            images = self.sniffer.sniff_images(url, min_size, wait_time, self.update_progress)
            self.root.after(0, self._sniff_completed, images)
        except Exception as e:
            self.root.after(0, self._sniff_failed, str(e))
    
    def _sniff_completed(self, images):
        """嗅探完成"""
        self.images = images
        self.sniff_btn.config(state=tk.NORMAL)
        
        if images:
            self.download_btn.config(state=tk.NORMAL)
            
            # 显示结果
            for img in images:
                self.tree.insert('', tk.END, values=(
                    img.filename,
                    f"{img.size / 1024:.1f}" if img.size > 0 else "未知",
                    img.url
                ))
            
            self.status_var.set(f"嗅探完成，找到 {len(images)} 张图片")
        else:
            self.status_var.set("未找到符合条件的图片")
    
    def _sniff_failed(self, error_msg):
        """嗅探失败"""
        self.sniff_btn.config(state=tk.NORMAL)
        self.status_var.set(f"嗅探失败: {error_msg}")
        messagebox.showerror("嗅探失败", error_msg)
    
    def select_download_dir(self):
        """选择下载目录"""
        directory = filedialog.askdirectory(initialdir=self.download_dir)
        if directory:
            self.download_dir = directory
            messagebox.showinfo("提示", f"下载目录已设置为: {directory}")
    
    def download_all(self):
        """批量下载"""
        if not self.images:
            return
        
        # 禁用按钮
        self.download_btn.config(state=tk.DISABLED)
        self.sniff_btn.config(state=tk.DISABLED)
        
        # 在新线程中下载
        threading.Thread(
            target=self._download_thread,
            daemon=True
        ).start()
    
    def _download_thread(self):
        """下载线程"""
        try:
            downloaded = self.sniffer.download_images(self.images, self.download_dir, self.update_progress)
            self.root.after(0, self._download_completed, downloaded, len(self.images))
        except Exception as e:
            self.root.after(0, self._download_failed, str(e))
    
    def _download_completed(self, downloaded, total):
        """下载完成"""
        self.download_btn.config(state=tk.NORMAL)
        self.sniff_btn.config(state=tk.NORMAL)
        self.status_var.set(f"下载完成: {downloaded}/{total} 张图片")
        messagebox.showinfo("下载完成", f"共下载 {downloaded}/{total} 张图片\n保存位置: {self.download_dir}")
    
    def _download_failed(self, error_msg):
        """下载失败"""
        self.download_btn.config(state=tk.NORMAL)
        self.sniff_btn.config(state=tk.NORMAL)
        self.status_var.set(f"下载失败: {error_msg}")
        messagebox.showerror("下载失败", error_msg)
    
    def preview_image(self, event):
        """预览图片"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        url = item['values'][2]
        
        # 在新窗口中显示图片预览
        self.show_image_preview(url)
    
    def show_image_preview(self, url):
        """显示图片预览窗口"""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("图片预览")
        preview_window.geometry("600x500")
        
        # 显示URL
        url_label = ttk.Label(preview_window, text=f"URL: {url}", wraplength=580)
        url_label.pack(pady=10)
        
        # 图片显示区域
        image_frame = ttk.Frame(preview_window)
        image_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # 加载图片
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            from PIL import Image, ImageTk
            import io
            
            image_data = io.BytesIO(response.content)
            pil_image = Image.open(image_data)
            
            # 调整图片大小以适应窗口
            max_size = (500, 400)
            pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(pil_image)
            
            image_label = ttk.Label(image_frame, image=photo)
            image_label.image = photo  # 保持引用
            image_label.pack(expand=True)
            
        except Exception as e:
            error_label = ttk.Label(image_frame, text=f"无法加载图片: {str(e)}")
            error_label.pack(expand=True)
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='图片资源嗅探工具')
    parser.add_argument('--cli', action='store_true', help='使用命令行模式')
    parser.add_argument('--url', help='要嗅探的网页URL')
    parser.add_argument('--min-size', type=int, default=10, help='最小图片大小(KB)')
    parser.add_argument('--wait-time', type=int, default=5, help='页面加载等待时间(秒)')
    parser.add_argument('--output', help='输出结果的JSON文件路径')
    parser.add_argument('--download-dir', help='图片下载目录')
    
    args = parser.parse_args()
    
    if args.cli or not GUI_AVAILABLE:
        # 命令行模式
        if not args.url:
            print("错误: 命令行模式需要指定 --url 参数")
            return
        
        sniffer = ImageSniffer()
        
        def progress_callback(message, progress):
            print(f"[{progress*100:.1f}%] {message}")
        
        try:
            print(f"开始嗅探: {args.url}")
            images = sniffer.sniff_images(args.url, args.min_size, args.wait_time, progress_callback)
            
            if images:
                print(f"\n找到 {len(images)} 张图片:")
                for i, img in enumerate(images, 1):
                    print(f"{i}. {img.filename} ({img.size/1024:.1f}KB) - {img.url}")
                
                # 保存结果到JSON文件
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        json.dump([img.to_dict() for img in images], f, ensure_ascii=False, indent=2)
                    print(f"\n结果已保存到: {args.output}")
                
                # 下载图片
                if args.download_dir:
                    print(f"\n开始下载到: {args.download_dir}")
                    downloaded = sniffer.download_images(images, args.download_dir, progress_callback)
                    print(f"下载完成: {downloaded}/{len(images)} 张图片")
            else:
                print("未找到符合条件的图片")
                
        except Exception as e:
            print(f"嗅探失败: {str(e)}")
    
    else:
        # GUI模式
        if not GUI_AVAILABLE:
            print("GUI依赖未安装，请安装: pip install pillow")
            return
        
        app = ImageSnifferGUI()
        app.run()


if __name__ == '__main__':
    main()