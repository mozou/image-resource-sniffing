# -*- coding: utf-8 -*-
"""
图片资源嗅探工具
功能：根据输入的链接，自动嗅探该链接中的所有图片资源，支持嗅探完成后预览、批量下载
支持排除图片大小<N的图片资源
"""

import os
import time
import json
import requests
import argparse
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from io import BytesIO
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread


class ImageSnifferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("图片资源嗅探工具")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        self.image_sniffer = ImageSniffer()
        self.setup_ui()
        
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建输入区域
        input_frame = ttk.LabelFrame(main_frame, text="输入参数", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        # URL输入
        ttk.Label(input_frame, text="网址:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.url_entry = ttk.Entry(input_frame, width=50)
        self.url_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 最小图片大小
        ttk.Label(input_frame, text="最小图片大小(KB):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_size_entry = ttk.Entry(input_frame, width=10)
        self.min_size_entry.insert(0, "10")
        self.min_size_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 等待时间
        ttk.Label(input_frame, text="页面加载等待时间(秒):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.wait_time_entry = ttk.Entry(input_frame, width=10)
        self.wait_time_entry.insert(0, "5")
        self.wait_time_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="开始嗅探", command=self.start_sniffing)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.download_button = ttk.Button(button_frame, text="批量下载", command=self.batch_download, state=tk.DISABLED)
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        # 创建结果区域
        result_frame = ttk.LabelFrame(main_frame, text="嗅探结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建表格
        columns = ("序号", "URL", "大小(KB)", "宽度", "高度", "类型")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.result_tree.heading(col, text=col)
            if col == "URL":
                self.result_tree.column(col, width=300, anchor=tk.W)
            elif col == "序号":
                self.result_tree.column(col, width=50, anchor=tk.CENTER)
            else:
                self.result_tree.column(col, width=80, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar_y.set)
        
        scrollbar_x = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(xscrollcommand=scrollbar_x.set)
        
        # 放置表格和滚动条
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定双击事件
        self.result_tree.bind("<Double-1>", self.preview_image)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def start_sniffing(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入有效的URL")
            return
        
        try:
            min_size = int(self.min_size_entry.get())
            wait_time = int(self.wait_time_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return
        
        # 清空表格
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 禁用开始按钮
        self.start_button.config(state=tk.DISABLED)
        self.download_button.config(state=tk.DISABLED)
        self.status_var.set("正在嗅探图片资源...")
        
        # 在新线程中运行嗅探过程
        Thread(target=self._run_sniffing, args=(url, min_size, wait_time)).start()
    
    def _run_sniffing(self, url, min_size, wait_time):
        try:
            images = self.image_sniffer.sniff(url, min_size, wait_time)
            
            # 更新UI
            self.root.after(0, self._update_results, images)
        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))
    
    def _update_results(self, images):
        for i, img in enumerate(images, 1):
            size_kb = round(img['size'] / 1024, 2)
            self.result_tree.insert("", tk.END, values=(
                i, img['url'], size_kb, img['width'], img['height'], img['type']
            ))
        
        self.status_var.set(f"嗅探完成，共找到 {len(images)} 张图片")
        self.start_button.config(state=tk.NORMAL)
        
        if images:
            self.download_button.config(state=tk.NORMAL)
    
    def _show_error(self, error_msg):
        messagebox.showerror("错误", error_msg)
        self.status_var.set("嗅探失败")
        self.start_button.config(state=tk.NORMAL)
    
    def preview_image(self, event):
        selected_item = self.result_tree.selection()
        if not selected_item:
            return
        
        item_values = self.result_tree.item(selected_item[0], "values")
        if not item_values:
            return
        
        image_url = item_values[1]
        try:
            # 创建预览窗口
            preview_window = tk.Toplevel(self.root)
            preview_window.title("图片预览")
            
            # 获取图片
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                
                # 调整图片大小以适应窗口
                screen_width = self.root.winfo_screenwidth() * 0.8
                screen_height = self.root.winfo_screenheight() * 0.8
                
                img_width, img_height = img.size
                scale = min(screen_width / img_width, screen_height / img_height)
                
                if scale < 1:
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # 显示图片
                from PIL import ImageTk
                photo = ImageTk.PhotoImage(img)
                
                label = ttk.Label(preview_window, image=photo)
                label.image = photo  # 保持引用
                label.pack(padx=10, pady=10)
                
                # 显示图片信息
                info_text = f"URL: {image_url}\n大小: {item_values[2]} KB\n尺寸: {item_values[3]}x{item_values[4]}\n类型: {item_values[5]}"
                info_label = ttk.Label(preview_window, text=info_text, wraplength=600)
                info_label.pack(padx=10, pady=10)
                
                # 下载按钮
                download_btn = ttk.Button(preview_window, text="下载此图片", 
                                         command=lambda: self.download_single_image(image_url))
                download_btn.pack(pady=10)
            else:
                messagebox.showerror("错误", f"无法加载图片: HTTP {response.status_code}")
        except Exception as e:
            messagebox.showerror("错误", f"预览图片时出错: {str(e)}")
    
    def download_single_image(self, url):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if not save_path:
            return
        
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                messagebox.showinfo("成功", "图片已保存")
            else:
                messagebox.showerror("错误", f"下载失败: HTTP {response.status_code}")
        except Exception as e:
            messagebox.showerror("错误", f"下载图片时出错: {str(e)}")
    
    def batch_download(self):
        # 选择保存目录
        save_dir = filedialog.askdirectory(title="选择保存目录")
        if not save_dir:
            return
        
        # 获取所有图片URL
        all_images = []
        for item in self.result_tree.get_children():
            values = self.result_tree.item(item, "values")
            all_images.append(values[1])  # URL在第二列
        
        if not all_images:
            messagebox.showinfo("提示", "没有可下载的图片")
            return
        
        # 禁用按钮
        self.download_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.DISABLED)
        self.status_var.set("正在下载图片...")
        
        # 在新线程中下载
        Thread(target=self._run_batch_download, args=(all_images, save_dir)).start()
    
    def _run_batch_download(self, urls, save_dir):
        total = len(urls)
        success = 0
        
        for i, url in enumerate(urls):
            try:
                # 更新状态
                self.root.after(0, lambda s=f"正在下载 {i+1}/{total}": self.status_var.set(s))
                
                # 从URL中提取文件名
                filename = os.path.basename(urlparse(url).path)
                if not filename:
                    filename = f"image_{i+1}.jpg"
                
                # 确保文件名唯一
                save_path = os.path.join(save_dir, filename)
                base, ext = os.path.splitext(save_path)
                counter = 1
                while os.path.exists(save_path):
                    save_path = f"{base}_{counter}{ext}"
                    counter += 1
                
                # 下载图片
                response = requests.get(url, stream=True, timeout=10)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    success += 1
            except Exception as e:
                print(f"下载图片 {url} 时出错: {str(e)}")
        
        # 更新UI
        self.root.after(0, lambda: self._download_completed(total, success))
    
    def _download_completed(self, total, success):
        self.status_var.set(f"下载完成: {success}/{total} 张图片成功")
        self.download_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.NORMAL)
        messagebox.showinfo("下载完成", f"共 {total} 张图片，成功下载 {success} 张")


class ImageSniffer:
    def __init__(self):
        self.driver = None
        self.base_url = None
    
    def _setup_driver(self):
        """设置Selenium WebDriver"""
        options = Options()
        options.add_argument("--headless")  # 无头模式
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # 添加用户代理
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # 初始化WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        return driver
    
    def _scroll_to_bottom(self, driver, wait_time=0.5, max_scrolls=10):
        """滚动到页面底部以触发懒加载"""
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(max_scrolls):
            # 滚动到底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 等待页面加载
            time.sleep(wait_time)
            
            # 计算新的滚动高度
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            # 如果高度没有变化，说明已经到底部了
            if new_height == last_height:
                break
                
            last_height = new_height
    
    def _extract_image_info(self, img_url):
        """提取图片信息"""
        try:
            response = requests.head(img_url, timeout=5)
            content_type = response.headers.get('Content-Type', '')
            content_length = int(response.headers.get('Content-Length', 0))
            
            # 如果HEAD请求没有返回Content-Length，尝试GET请求
            if content_length == 0:
                response = requests.get(img_url, stream=True, timeout=5)
                content_length = int(response.headers.get('Content-Length', 0))
                
                # 如果仍然没有Content-Length，读取内容计算大小
                if content_length == 0:
                    content = BytesIO()
                    for chunk in response.iter_content(1024):
                        content.write(chunk)
                    content_length = content.tell()
                    
                    # 尝试获取图片尺寸
                    content.seek(0)
                    img = Image.open(content)
                    width, height = img.size
                    return {
                        'url': img_url,
                        'size': content_length,
                        'width': width,
                        'height': height,
                        'type': content_type
                    }
            
            # 获取图片尺寸
            response = requests.get(img_url, stream=True, timeout=5)
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            
            return {
                'url': img_url,
                'size': content_length,
                'width': width,
                'height': height,
                'type': content_type
            }
        except Exception as e:
            print(f"提取图片信息时出错 {img_url}: {str(e)}")
            return {
                'url': img_url,
                'size': 0,
                'width': 0,
                'height': 0,
                'type': 'unknown'
            }
    
    def _get_all_image_urls(self, driver):
        """获取页面中所有图片URL"""
        image_urls = set()
        
        # 获取所有<img>标签
        img_elements = driver.find_elements(By.TAG_NAME, "img")
        for img in img_elements:
            src = img.get_attribute("src")
            if src and src.startswith(("http://", "https://")):
                image_urls.add(src)
            
            # 检查data-src属性（常用于懒加载）
            data_src = img.get_attribute("data-src")
            if data_src and data_src.startswith(("http://", "https://")):
                image_urls.add(data_src)
            
            # 检查srcset属性
            srcset = img.get_attribute("srcset")
            if srcset:
                for src_item in srcset.split(","):
                    parts = src_item.strip().split(" ")
                    if parts and parts[0].startswith(("http://", "https://")):
                        image_urls.add(parts[0])
        
        # 获取CSS背景图片
        script = """
        var results = [];
        var allElements = document.querySelectorAll('*');
        for (var i = 0; i < allElements.length; i++) {
            var style = window.getComputedStyle(allElements[i]);
            var bgImage = style.backgroundImage;
            if (bgImage && bgImage !== 'none') {
                var match = bgImage.match(/url\\(['"]?(http[^'"\\)]+)['"]?\\)/i);
                if (match) {
                    results.push(match[1]);
                }
            }
        }
        return results;
        """
        background_images = driver.execute_script(script)
        for url in background_images:
            if url.startswith(("http://", "https://")):
                image_urls.add(url)
        
        # 尝试查找原始图片URL（通常在链接中）
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href and href.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
                image_urls.add(href)
        
        return list(image_urls)
    
    def _try_get_original_image(self, url):
        """尝试获取原始图片URL"""
        # 检查URL是否包含缩略图标识
        lower_url = url.lower()
        
        # 常见的缩略图标识
        thumb_patterns = [
            ('thumbnail', 'original'),
            ('thumb', 'original'),
            ('small', 'large'),
            ('_t.', '.'),
            ('-t.', '.'),
            ('_small.', '.'),
            ('-small.', '.'),
            ('_thumb.', '.'),
            ('-thumb.', '.'),
            ('_s.', '.'),
            ('-s.', '.')
        ]
        
        for pattern, replacement in thumb_patterns:
            if pattern in lower_url:
                original_url = url.replace(pattern, replacement)
                try:
                    # 检查原始URL是否可访问
                    response = requests.head(original_url, timeout=5)
                    if response.status_code == 200:
                        return original_url
                except:
                    pass
        
        return url
    
    def sniff(self, url, min_size_kb=10, wait_time=5):
        """
        嗅探指定URL中的所有图片资源
        
        参数:
            url (str): 要嗅探的网页URL
            min_size_kb (int): 最小图片大小（KB）
            wait_time (int): 等待页面加载的时间（秒）
            
        返回:
            list: 图片信息列表
        """
        try:
            self.base_url = url
            self.driver = self._setup_driver()
            
            # 访问页面
            self.driver.get(url)
            
            # 等待页面加载
            time.sleep(wait_time)
            
            # 滚动页面以触发懒加载
            self._scroll_to_bottom(self.driver)
            
            # 获取所有图片URL
            image_urls = self._get_all_image_urls(self.driver)
            
            # 尝试获取原始图片
            original_urls = []
            for url in image_urls:
                original_url = self._try_get_original_image(url)
                original_urls.append(original_url)
            
            # 提取图片信息
            min_size_bytes = min_size_kb * 1024
            images = []
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                image_infos = list(executor.map(self._extract_image_info, original_urls))
                
                for info in image_infos:
                    if info['size'] >= min_size_bytes:
                        images.append(info)
            
            # 按大小排序
            images.sort(key=lambda x: x['size'], reverse=True)
            
            return images
        finally:
            # 关闭WebDriver
            if self.driver:
                self.driver.quit()
                self.driver = None


def main():
    parser = argparse.ArgumentParser(description='图片资源嗅探工具')
    parser.add_argument('--cli', action='store_true', help='使用命令行模式')
    parser.add_argument('--url', type=str, help='要嗅探的URL')
    parser.add_argument('--min-size', type=int, default=10, help='最小图片大小(KB)')
    parser.add_argument('--wait-time', type=int, default=5, help='页面加载等待时间(秒)')
    parser.add_argument('--output', type=str, help='输出结果的JSON文件路径')
    parser.add_argument('--download-dir', type=str, help='图片下载目录')
    
    args = parser.parse_args()
    
    if args.cli:
        if not args.url:
            print("错误: 命令行模式下必须提供URL参数")
            return
        
        print(f"开始嗅探: {args.url}")
        sniffer = ImageSniffer()
        images = sniffer.sniff(args.url, args.min_size, args.wait_time)
        
        print(f"找到 {len(images)} 张图片:")
        for i, img in enumerate(images, 1):
            size_kb = round(img['size'] / 1024, 2)
            print(f"{i}. {img['url']} - {size_kb}KB ({img['width']}x{img['height']})")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(images, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {args.output}")
        
        if args.download_dir and images:
            if not os.path.exists(args.download_dir):
                os.makedirs(args.download_dir)
            
            print(f"开始下载图片到: {args.download_dir}")
            for i, img in enumerate(images, 1):
                try:
                    url = img['url']
                    filename = os.path.basename(urlparse(url).path)
                    if not filename:
                        filename = f"image_{i}.jpg"
                    
                    save_path = os.path.join(args.download_dir, filename)
                    
                    # 确保文件名唯一
                    base, ext = os.path.splitext(save_path)
                    counter = 1
                    while os.path.exists(save_path):
                        save_path = f"{base}_{counter}{ext}"
                        counter += 1
                    
                    print(f"下载 {i}/{len(images)}: {url}")
                    response = requests.get(url, stream=True)
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                except Exception as e:
                    print(f"下载失败: {str(e)}")
            
            print("下载完成")
    else:
        # 启动GUI模式
        root = tk.Tk()
        app = ImageSnifferGUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()