#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级图片资源嗅探工具 - Selenium版本
专门用于处理有严格反爬虫机制的网站
支持JavaScript渲染、懒加载检测等高级功能
"""

import os
import re
import time
import json
import threading
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import io

class SeleniumImageSniffer:
    """使用Selenium的高级图片嗅探器"""
    
    def __init__(self):
        self.driver = None
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """设置requests会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,zh;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
    
    def create_driver(self, headless=True):
        """创建Chrome浏览器驱动"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless')
            
            # 基本设置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # 初始禁用图片加载以提高速度
            
            # 反检测设置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 设置User-Agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 设置语言
            chrome_options.add_argument('--lang=ko-KR')
            
            # 设置窗口大小
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 创建驱动（自动管理ChromeDriver）
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 执行反检测脚本
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
            
        except Exception as e:
            print(f"创建浏览器驱动失败: {e}")
            return False
    
    def wait_for_page_load(self, timeout=30):
        """等待页面完全加载"""
        try:
            # 等待页面基本加载完成
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 额外等待JavaScript执行
            time.sleep(2)
            
            # 滚动页面触发懒加载
            self.scroll_page()
            
            return True
            
        except TimeoutException:
            print("页面加载超时")
            return False
    
    def scroll_page(self):
        """滚动页面以触发懒加载"""
        try:
            # 获取页面高度
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 等待新内容加载
                time.sleep(2)
                
                # 计算新的页面高度
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                    
                last_height = new_height
            
            # 滚动回顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            print(f"滚动页面时出错: {e}")
    
    def extract_images_from_page(self, url, min_size_kb=10):
        """从页面提取图片信息"""
        try:
            print(f"正在访问: {url}")
            
            # 访问页面
            self.driver.get(url)
            
            # 等待页面加载
            if not self.wait_for_page_load():
                raise Exception("页面加载失败")
            
            print("页面加载完成，开始提取图片...")
            
            # 获取所有图片元素
            img_elements = self.driver.find_elements(By.TAG_NAME, "img")
            
            # 获取CSS背景图片
            bg_images = self.extract_background_images()
            
            # 收集所有图片URL
            # 收集所有图片URL，保持顺序
            image_urls = []
            seen_urls = set()
            
            # 处理img标签，按在页面中的顺序
            for img in img_elements:
                # 获取src属性
                src = img.get_attribute('src')
                if src and self.is_valid_image_url(src) and src not in seen_urls:
                    image_urls.append(src)
                    seen_urls.add(src)
                
                # 获取data-src属性（懒加载）
                data_src = img.get_attribute('data-src')
                if data_src and self.is_valid_image_url(data_src) and data_src not in seen_urls:
                    image_urls.append(data_src)
                    seen_urls.add(data_src)
                
                # 获取data-original属性
                data_original = img.get_attribute('data-original')
                if data_original and self.is_valid_image_url(data_original) and data_original not in seen_urls:
                    image_urls.append(data_original)
                    seen_urls.add(data_original)
            
            # 添加背景图片（放在最后）
            for bg_url in bg_images:
                if bg_url not in seen_urls:
                    image_urls.append(bg_url)
                    seen_urls.add(bg_url)
            
            print(f"找到 {len(image_urls)} 个图片URL")
            
            # 验证图片并获取详细信息
            valid_images = []
            min_size_bytes = min_size_kb * 1024
            
            for i, img_url in enumerate(image_urls):
                try:
                    print(f"验证图片 {i+1}/{len(image_urls)}: {img_url[:50]}...")
                    
                    # 获取图片信息
                    img_info = self.get_image_info(img_url)
                    
                    if img_info and img_info['size'] >= min_size_bytes:
                        valid_images.append(img_info)
                        print(f"✓ 有效图片: {img_info['filename']} ({img_info['size']/1024:.1f}KB)")
                    
                except Exception as e:
                    print(f"✗ 验证失败: {e}")
                    continue
            
            # 按大小排序
            # 保持原始顺序，不按大小排序
            
            print(f"嗅探完成，找到 {len(valid_images)} 张有效图片")
            return valid_images
            
        except Exception as e:
            print(f"提取图片失败: {e}")
            return []
    
    def extract_background_images(self):
        """提取CSS背景图片"""
        bg_images = set()
        
        try:
            # 执行JavaScript获取所有背景图片
            script = """
            var bgImages = [];
            var elements = document.querySelectorAll('*');
            
            for (var i = 0; i < elements.length; i++) {
                var style = window.getComputedStyle(elements[i]);
                var bgImage = style.backgroundImage;
                
                if (bgImage && bgImage !== 'none') {
                    var matches = bgImage.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/g);
                    if (matches) {
                        for (var j = 0; j < matches.length; j++) {
                            var url = matches[j].replace(/url\\(['"]?/, '').replace(/['"]?\\)$/, '');
                            bgImages.push(url);
                        }
                    }
                }
            }
            
            return bgImages;
            """
            
            urls = self.driver.execute_script(script)
            
            for url in urls:
                if self.is_valid_image_url(url):
                    # 转换为绝对URL
                    absolute_url = urljoin(self.driver.current_url, url)
                    bg_images.add(absolute_url)
            
        except Exception as e:
            print(f"提取背景图片失败: {e}")
        
        return bg_images
    
    def is_valid_image_url(self, url):
        """判断是否为有效的图片URL"""
        if not url or url.startswith('data:'):
            return False
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        url_lower = url.lower()
        
        return any(ext in url_lower for ext in image_extensions) or 'image' in url_lower
    
    def get_image_info(self, url):
        """获取图片详细信息"""
        try:
            # 使用当前浏览器的cookies
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            # 设置请求头
            headers = {
                'User-Agent': self.driver.execute_script("return navigator.userAgent;"),
                'Referer': self.driver.current_url,
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            }
            
            # 发送HEAD请求获取基本信息
            response = self.session.head(url, headers=headers, cookies=cookie_dict, timeout=10)
            
            if response.status_code != 200:
                # 如果HEAD失败，尝试GET请求
                response = self.session.get(url, headers=headers, cookies=cookie_dict, timeout=10, stream=True)
            
            content_type = response.headers.get('Content-Type', '')
            content_length = int(response.headers.get('Content-Length', 0))
            
            # 如果没有Content-Length，尝试获取实际大小
            if content_length == 0 and hasattr(response, 'iter_content'):
                chunk_size = 8192
                total_size = 0
                for chunk in response.iter_content(chunk_size):
                    total_size += len(chunk)
                    if total_size > 1024 * 1024:  # 限制1MB
                        break
                content_length = total_size
            
            # 提取文件名
            filename = self.extract_filename(url)
            
            return {
                'url': url,
                'filename': filename,
                'size': content_length,
                'content_type': content_type
            }
            
        except Exception as e:
            print(f"获取图片信息失败 {url}: {e}")
            return None
    
    def extract_filename(self, url):
        """从URL提取文件名"""
        try:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            
            if not filename or '.' not in filename:
                # 生成默认文件名
                filename = f"image_{hash(url) % 10000}.jpg"
            
            return filename
            
        except:
            return f"image_{hash(url) % 10000}.jpg"
    
    def download_image(self, img_info, save_dir, index=None):
        """下载单张图片"""
        try:
            # 使用浏览器的cookies（如果浏览器还在运行）
            cookies = {}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,zh;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            
            if self.driver:
                try:
                    cookies_list = self.driver.get_cookies()
                    cookies = {cookie['name']: cookie['value'] for cookie in cookies_list}
                    headers['User-Agent'] = self.driver.execute_script("return navigator.userAgent;")
                    headers['Referer'] = self.driver.current_url
                except:
                    # 浏览器已关闭，使用默认设置
                    pass
            
            response = self.session.get(
                img_info['url'], 
                headers=headers, 
                cookies=cookies, 
                stream=True, 
                timeout=30
            )
            response.raise_for_status()
            
            # 确保保存目录存在
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名（按顺序重命名）
            # 生成文件名（按顺序重命名）
            if index is not None:
                # 获取文件扩展名
                original_ext = os.path.splitext(img_info['filename'])[1].lower()
                if not original_ext:
                    # 从URL推断扩展名
                    url_lower = img_info['url'].lower()
                    if '.png' in url_lower:
                        original_ext = '.png'
                    elif '.gif' in url_lower:
                        original_ext = '.gif'
                    elif '.webp' in url_lower:
                        original_ext = '.webp'
                    elif '.jpeg' in url_lower:
                        original_ext = '.jpeg'
                    elif '.bmp' in url_lower:
                        original_ext = '.bmp'
                    else:
                        # 从Content-Type推断扩展名
                        content_type = img_info.get('content_type', '').lower()
                        if 'png' in content_type:
                            original_ext = '.png'
                        elif 'gif' in content_type:
                            original_ext = '.gif'
                        elif 'webp' in content_type:
                            original_ext = '.webp'
                        elif 'jpeg' in content_type:
                            original_ext = '.jpeg'
                        else:
                            original_ext = '.jpg'
                
                # 按顺序命名：001.jpg, 002.png 等
                filename = f"{index:03d}{original_ext}"
            else:
                filename = img_info['filename']
            
            file_path = os.path.join(save_dir, filename)
            
            # 如果文件已存在，添加后缀
            counter = 1
            base_name, ext = os.path.splitext(file_path)
            while os.path.exists(file_path):
                if index is not None:
                    file_path = f"{base_name}_{counter}{ext}"
                else:
                    file_path = f"{base_name}_{counter}{ext}"
                counter += 1
            
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"下载失败: {e}")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


class SeleniumSnifferGUI:
    """Selenium嗅探器的GUI界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("高级图片嗅探工具 - Selenium版")
        self.root.geometry("1000x700")
        
        self.sniffer = SeleniumImageSniffer()
        self.images = []
        self.current_preview = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="高级图片嗅探工具 - Selenium版", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL输入
        ttk.Label(main_frame, text="网址:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 参数设置
        params_frame = ttk.Frame(main_frame)
        params_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(params_frame, text="最小大小(KB):").grid(row=0, column=0, padx=(0, 5))
        self.min_size_var = tk.StringVar(value="10")
        ttk.Entry(params_frame, textvariable=self.min_size_var, width=10).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(params_frame, text="浏览器模式:").grid(row=0, column=2, padx=(0, 5))
        self.headless_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame, text="静默模式", variable=self.headless_var).grid(row=0, column=3, padx=(0, 20))
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.sniff_btn = ttk.Button(button_frame, text="开始嗅探", command=self.start_sniff)
        self.sniff_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.download_all_btn = ttk.Button(button_frame, text="批量下载", command=self.download_all, state='disabled')
        self.download_all_btn.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(button_frame, text="选择保存目录", command=self.select_save_dir).grid(row=0, column=2, padx=(0, 10))
        
        ttk.Button(button_frame, text="关闭浏览器", command=self.close_browser).grid(row=0, column=3)
        
        # 进度条
        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=4, column=0, columnspan=3, pady=5)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # 结果列表
        result_frame = ttk.LabelFrame(main_frame, text="嗅探结果", padding="5")
        result_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # 创建Treeview
        columns = ('文件名', '大小', 'URL')
        self.tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题
        self.tree.heading('文件名', text='文件名')
        self.tree.heading('大小', text='大小(KB)')
        self.tree.heading('URL', text='URL')
        
        # 设置列宽
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
        
        # 保存目录
        # 保存目录
        self.save_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'ImageSniffer')
    
    def select_save_dir(self):
        """选择保存目录"""
        directory = filedialog.askdirectory(initialdir=self.save_dir)
        if directory:
            self.save_dir = directory
            messagebox.showinfo("提示", f"保存目录已设置为: {directory}")
    
    def close_browser(self):
        """手动关闭浏览器"""
        try:
            self.sniffer.close()
            self.progress_var.set("浏览器已关闭")
            messagebox.showinfo("提示", "浏览器已关闭。注意：关闭浏览器后将无法下载图片，需要重新嗅探。")
        except Exception as e:
            messagebox.showerror("错误", f"关闭浏览器失败: {e}")
    
    def start_sniff(self):
        """开始嗅探"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入有效的URL")
            return
        
        try:
            min_size = int(self.min_size_var.get())
        except ValueError:
            min_size = 10
        
        # 清空结果
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.images = []
        self.download_all_btn.config(state='disabled')
        
        # 禁用按钮并开始进度条
        self.sniff_btn.config(state='disabled')
        self.progress_bar.start()
        
        # 在新线程中执行嗅探
        threading.Thread(
            target=self._sniff_thread,
            args=(url, min_size, self.headless_var.get()),
            daemon=True
        ).start()
    
    def _sniff_thread(self, url, min_size, headless):
        """嗅探线程"""
        try:
            self.progress_var.set("正在启动浏览器...")
            
            # 创建浏览器驱动
            if not self.sniffer.create_driver(headless):
                raise Exception("无法启动浏览器，请确保已安装Chrome和ChromeDriver")
            
            self.progress_var.set("正在嗅探图片...")
            
            # 执行嗅探
            images = self.sniffer.extract_images_from_page(url, min_size)
            
            # 更新UI
            self.root.after(0, self._sniff_completed, images)
            
        except Exception as e:
            self.root.after(0, self._sniff_failed, str(e))
        # 注意：不在这里关闭浏览器，保持连接用于下载
    
    def _sniff_completed(self, images):
        """嗅探完成"""
        self.progress_bar.stop()
        self.sniff_btn.config(state='normal')
        
        self.images = images
        
        if images:
            self.download_all_btn.config(state='normal')
            
            # 显示结果
            for img in images:
                self.tree.insert('', 'end', values=(
                    img['filename'],
                    f"{img['size']/1024:.1f}",
                    img['url'][:80] + '...' if len(img['url']) > 80 else img['url']
                ))
            
            self.progress_var.set(f"嗅探完成，找到 {len(images)} 张图片")
        else:
            self.progress_var.set("未找到符合条件的图片")
    
    def _sniff_failed(self, error_msg):
        """嗅探失败"""
        self.progress_bar.stop()
        self.sniff_btn.config(state='normal')
        self.progress_var.set(f"嗅探失败: {error_msg}")
        messagebox.showerror("嗅探失败", error_msg)
    
    def preview_image(self, event):
        """预览图片"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        filename = item['values'][0]
        
        # 找到对应的图片信息
        img_info = None
        for img in self.images:
            if img['filename'] == filename:
                img_info = img
                break
        
        if not img_info:
            return
        
        # 创建预览窗口
        self.show_preview_window(img_info)
    
    def show_preview_window(self, img_info):
        """显示预览窗口"""
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"预览 - {img_info['filename']}")
        preview_window.geometry("600x500")
        
        try:
            # 下载图片数据用于预览
            cookies = self.sniffer.driver.get_cookies() if self.sniffer.driver else []
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = self.sniffer.session.get(img_info['url'], headers=headers, cookies=cookie_dict, timeout=10)
            
            # 创建PIL图像
            pil_image = Image.open(io.BytesIO(response.content))
            
            # 调整图像大小以适应窗口
            pil_image.thumbnail((550, 400), Image.Resampling.LANCZOS)
            
            # 转换为Tkinter可用的格式
            photo = ImageTk.PhotoImage(pil_image)
            
            # 显示图像
            img_label = ttk.Label(preview_window, image=photo)
            img_label.image = photo  # 保持引用
            img_label.pack(pady=10)
            
            # 显示信息
            info_text = f"文件名: {img_info['filename']}\n大小: {img_info['size']/1024:.1f} KB\nURL: {img_info['url']}"
            ttk.Label(preview_window, text=info_text, wraplength=550).pack(pady=10)
            
            # 下载按钮
            ttk.Button(preview_window, text="下载这张图片", 
                      command=lambda: self.download_single(img_info)).pack(pady=10)
            
        except Exception as e:
            ttk.Label(preview_window, text=f"预览失败: {e}").pack(pady=20)
    
    def download_single(self, img_info):
        """下载单张图片"""
        try:
            # 找到图片在列表中的索引，用于按顺序命名
            index = None
            for i, img in enumerate(self.images, 1):
                if img['url'] == img_info['url']:
                    index = i
                    break
            
            file_path = self.sniffer.download_image(img_info, self.save_dir, index)
            messagebox.showinfo("下载成功", f"图片已保存到: {file_path}")
        except Exception as e:
            messagebox.showerror("下载失败", str(e))
    
    def download_all(self):
        """批量下载"""
        if not self.images:
            return
        
        self.download_all_btn.config(state='disabled')
        self.progress_bar.start()
        
        threading.Thread(target=self._download_all_thread, daemon=True).start()
    
    def _download_all_thread(self):
        """批量下载线程"""
        success_count = 0
        total_count = len(self.images)
        
        for i, img_info in enumerate(self.images):
            try:
                # 按顺序重命名：001.jpg, 002.png 等
                index = i + 1
                self.root.after(0, lambda idx=index, total=total_count, name=img_info['filename']: 
                               self.progress_var.set(f"正在下载 {idx}/{total}: {name}"))
                
                file_path = self.sniffer.download_image(img_info, self.save_dir, index)
                success_count += 1
                print(f"✓ 下载成功: {file_path}")
                
            except Exception as e:
                print(f"✗ 下载失败 {img_info['filename']}: {e}")
        
        # 更新UI
        self.root.after(0, self._download_completed, success_count, total_count)
    
    def _download_completed(self, success_count, total_count):
        """下载完成"""
        self.progress_bar.stop()
        self.download_all_btn.config(state='normal')
        self.progress_var.set(f"下载完成: {success_count}/{total_count} 张图片成功")
        
        messagebox.showinfo("下载完成", 
                           f"共 {total_count} 张图片，成功下载 {success_count} 张\n"
                           f"保存位置: {self.save_dir}")
    
    def run(self):
        """运行GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """关闭程序时的清理工作"""
        self.sniffer.close()
        self.root.destroy()


def main():
    """主函数"""
    import sys
    
    # 检查GUI依赖
    try:
        import tkinter as tk
        from tkinter import ttk
        gui_available = True
    except ImportError:
        gui_available = False
        print("⚠️ GUI依赖不可用，只能使用命令行模式")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        # 命令行模式
        if len(sys.argv) < 3:
            print("用法: python selenium_sniffer.py --cli <URL> [min_size_kb]")
            return
        
        url = sys.argv[2]
        min_size = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        
        sniffer = SeleniumImageSniffer()
        
        try:
            print("正在启动浏览器...")
            if not sniffer.create_driver(headless=True):
                print("❌ 无法启动浏览器，请确保已安装Chrome和ChromeDriver")
                return
            
            print("✅ 浏览器启动成功")
            print(f"正在嗅探: {url}")
            
            images = sniffer.extract_images_from_page(url, min_size)
            
            if images:
                print(f"\n✅ 嗅探完成，找到 {len(images)} 张图片:")
                print("-" * 80)
                
                for i, img in enumerate(images, 1):
                    print(f"{i:2d}. {img['filename']}")
                    print(f"    大小: {img['size']/1024:.1f} KB")
                    print(f"    URL: {img['url']}")
                    print()
                
                # 询问是否下载
                choice = input("是否要下载所有图片? (y/n): ").lower().strip()
                if choice == 'y':
                    save_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'ImageSniffer')
                    print(f"正在下载到: {save_dir}")
                    
                    success = 0
                    for i, img in enumerate(images, 1):
                        try:
                            print(f"下载 {i}/{len(images)}: {img['filename']}")
                            sniffer.download_image(img, save_dir)
                            success += 1
                        except Exception as e:
                            print(f"❌ 下载失败: {e}")
                    
                    print(f"\n✅ 下载完成: {success}/{len(images)} 张图片成功")
                    print(f"保存位置: {save_dir}")
            else:
                print("❌ 未找到符合条件的图片")
                
        except Exception as e:
            print(f"❌ 嗅探失败: {e}")
        finally:
            sniffer.close()
    else:
        # GUI模式
        if not gui_available:
            print("❌ GUI不可用，请使用命令行模式:")
            print("python selenium_sniffer.py --cli <URL>")
            return
        
        try:
            print("启动图形界面...")
            app = SeleniumSnifferGUI()
            app.run()
        except Exception as e:
            print(f"❌ GUI启动失败: {e}")
            print("请尝试使用命令行模式:")
            print("python selenium_sniffer.py --cli <URL>")


if __name__ == '__main__':
    main()
