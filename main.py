# -*- coding: utf-8 -*-
"""
图片资源嗅探工具 - 移动端版本
使用Kivy框架，支持打包为APK
"""

import os
import json
import time
import threading
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import AsyncImage
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform

# 移动端特定导入
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    request_permissions([
        Permission.INTERNET,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.READ_EXTERNAL_STORAGE
    ])


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


class ImageSniffer:
    """图片嗅探器 - 移动端优化版本"""
    
    def __init__(self):
        self.session = self._create_session()
        self.user_agents = [
            'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
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
        import re
        
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
    
    def sniff_images(self, url, min_size_kb=10, progress_callback=None):
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
            
            with ThreadPoolExecutor(max_workers=5) as executor:  # 移动端减少并发数
                futures = [executor.submit(self._get_image_info, url) for url in original_urls]
                
                for i, future in enumerate(futures):
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


class ImagePreviewPopup(Popup):
    """图片预览弹窗"""
    
    def __init__(self, image_info, **kwargs):
        super().__init__(**kwargs)
        self.image_info = image_info
        self.title = f"图片预览 - {image_info.filename}"
        self.size_hint = (0.9, 0.9)
        
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # 图片显示
        self.image_widget = AsyncImage(
            source=image_info.url,
            size_hint_y=0.8,
            allow_stretch=True,
            keep_ratio=True
        )
        layout.add_widget(self.image_widget)
        
        # 图片信息
        info_text = f"大小: {image_info.size / 1024:.1f} KB\n类型: {image_info.content_type}\nURL: {image_info.url}"
        info_label = Label(
            text=info_text,
            size_hint_y=0.15,
            text_size=(None, None),
            halign='left'
        )
        layout.add_widget(info_label)
        
        # 按钮
        button_layout = BoxLayout(size_hint_y=0.05, spacing=dp(10))
        
        download_btn = Button(text="下载", size_hint_x=0.5)
        download_btn.bind(on_press=self.download_image)
        button_layout.add_widget(download_btn)
        
        close_btn = Button(text="关闭", size_hint_x=0.5)
        close_btn.bind(on_press=self.dismiss)
        button_layout.add_widget(close_btn)
        
        layout.add_widget(button_layout)
        self.content = layout
    
    def download_image(self, instance):
        """下载单张图片"""
        try:
            # 获取下载目录
            if platform == 'android':
                download_dir = os.path.join(primary_external_storage_path(), 'Download', 'ImageSniffer')
            else:
                download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'ImageSniffer')
            
            os.makedirs(download_dir, exist_ok=True)
            
            # 下载图片
            response = requests.get(self.image_info.url, stream=True, timeout=30)
            response.raise_for_status()
            
            file_path = os.path.join(download_dir, self.image_info.filename)
            
            # 确保文件名唯一
            counter = 1
            base_name, ext = os.path.splitext(file_path)
            while os.path.exists(file_path):
                file_path = f"{base_name}_{counter}{ext}"
                counter += 1
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 显示成功消息
            popup = Popup(
                title="下载成功",
                content=Label(text=f"图片已保存到:\n{file_path}"),
                size_hint=(0.8, 0.3)
            )
            popup.open()
            
        except Exception as e:
            # 显示错误消息
            popup = Popup(
                title="下载失败",
                content=Label(text=f"下载失败:\n{str(e)}"),
                size_hint=(0.8, 0.3)
            )
            popup.open()


class ImageListItem(BoxLayout):
    """图片列表项"""
    
    def __init__(self, image_info, **kwargs):
        super().__init__(**kwargs)
        self.image_info = image_info
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(80)
        self.spacing = dp(10)
        self.padding = dp(5)
        
        # 缩略图
        thumbnail = AsyncImage(
            source=image_info.url,
            size_hint_x=None,
            width=dp(70),
            allow_stretch=True,
            keep_ratio=True
        )
        self.add_widget(thumbnail)
        
        # 信息区域
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        
        # 文件名
        filename_label = Label(
            text=image_info.filename,
            size_hint_y=0.4,
            text_size=(None, None),
            halign='left',
            font_size=dp(14)
        )
        info_layout.add_widget(filename_label)
        
        # 详细信息
        details = f"{image_info.size / 1024:.1f} KB"
        details_label = Label(
            text=details,
            size_hint_y=0.3,
            text_size=(None, None),
            halign='left',
            font_size=dp(12),
            color=(0.7, 0.7, 0.7, 1)
        )
        info_layout.add_widget(details_label)
        
        self.add_widget(info_layout)
        
        # 预览按钮
        preview_btn = Button(
            text="预览",
            size_hint_x=None,
            width=dp(60),
            font_size=dp(12)
        )
        preview_btn.bind(on_press=self.show_preview)
        self.add_widget(preview_btn)
    
    def show_preview(self, instance):
        """显示预览"""
        popup = ImagePreviewPopup(self.image_info)
        popup.open()


class MainScreen(Screen):
    """主界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'
        self.sniffer = ImageSniffer()
        self.images = []
        
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # 标题
        title = Label(
            text="图片资源嗅探工具",
            size_hint_y=None,
            height=dp(40),
            font_size=dp(18)
        )
        layout.add_widget(title)
        
        # 输入区域
        input_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), spacing=dp(5))
        
        # URL输入
        url_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        url_layout.add_widget(Label(text="网址:", size_hint_x=None, width=dp(60)))
        self.url_input = TextInput(
            multiline=False,
            hint_text="请输入要嗅探的网址",
            font_size=dp(14)
        )
        url_layout.add_widget(self.url_input)
        input_layout.add_widget(url_layout)
        
        # 参数设置
        params_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        
        params_layout.add_widget(Label(text="最小大小(KB):", size_hint_x=None, width=dp(100)))
        self.min_size_input = TextInput(
            text="10",
            multiline=False,
            size_hint_x=None,
            width=dp(80),
            input_filter='int',
            font_size=dp(14)
        )
        params_layout.add_widget(self.min_size_input)
        
        input_layout.add_widget(params_layout)
        
        # 按钮
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        
        self.sniff_btn = Button(text="开始嗅探", font_size=dp(14))
        self.sniff_btn.bind(on_press=self.start_sniffing)
        button_layout.add_widget(self.sniff_btn)
        
        self.download_all_btn = Button(text="批量下载", font_size=dp(14), disabled=True)
        self.download_all_btn.bind(on_press=self.download_all)
        button_layout.add_widget(self.download_all_btn)
        
        input_layout.add_widget(button_layout)
        layout.add_widget(input_layout)
        
        # 进度条
        self.progress_bar = ProgressBar(size_hint_y=None, height=dp(20))
        layout.add_widget(self.progress_bar)
        
        # 状态标签
        self.status_label = Label(
            text="就绪",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(12)
        )
        layout.add_widget(self.status_label)
        
        # 结果列表
        self.scroll_view = ScrollView()
        self.result_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.result_layout.bind(minimum_height=self.result_layout.setter('height'))
        self.scroll_view.add_widget(self.result_layout)
        layout.add_widget(self.scroll_view)
        
        self.add_widget(layout)
    
    def start_sniffing(self, instance):
        """开始嗅探"""
        url = self.url_input.text.strip()
        if not url:
            popup = Popup(
                title="错误",
                content=Label(text="请输入有效的URL"),
                size_hint=(0.8, 0.3)
            )
            popup.open()
            return
        
        try:
            min_size = int(self.min_size_input.text)
        except ValueError:
            min_size = 10
        
        # 清空结果
        self.result_layout.clear_widgets()
        self.images = []
        self.download_all_btn.disabled = True
        
        # 禁用按钮
        self.sniff_btn.disabled = True
        self.progress_bar.value = 0
        
        # 在新线程中执行嗅探
        threading.Thread(
            target=self._sniff_thread,
            args=(url, min_size),
            daemon=True
        ).start()
    
    def _sniff_thread(self, url, min_size):
        """嗅探线程"""
        def progress_callback(message, progress):
            Clock.schedule_once(lambda dt: self._update_progress(message, progress))
        
        try:
            images = self.sniffer.sniff_images(url, min_size, progress_callback)
            Clock.schedule_once(lambda dt: self._sniff_completed(images))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._sniff_failed(str(e)))
    
    def _update_progress(self, message, progress):
        """更新进度"""
        self.status_label.text = message
        self.progress_bar.value = progress * 100
    
    def _sniff_completed(self, images):
        """嗅探完成"""
        self.images = images
        self.sniff_btn.disabled = False
        
        if images:
            self.download_all_btn.disabled = False
            
            # 显示结果
            for image in images:
                item = ImageListItem(image)
                self.result_layout.add_widget(item)
            
            self.status_label.text = f"嗅探完成，找到 {len(images)} 张图片"
        else:
            self.status_label.text = "未找到符合条件的图片"
    
    def _sniff_failed(self, error_msg):
        """嗅探失败"""
        self.sniff_btn.disabled = False
        self.status_label.text = f"嗅探失败: {error_msg}"
        
        popup = Popup(
            title="嗅探失败",
            content=Label(text=error_msg),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def download_all(self, instance):
        """批量下载"""
        if not self.images:
            return
        
        # 禁用按钮
        self.download_all_btn.disabled = True
        self.sniff_btn.disabled = True
        
        # 在新线程中下载
        threading.Thread(
            target=self._download_thread,
            daemon=True
        ).start()
    
    def _download_thread(self):
        """下载线程"""
        try:
            # 获取下载目录
            if platform == 'android':
                download_dir = os.path.join(primary_external_storage_path(), 'Download', 'ImageSniffer')
            else:
                download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'ImageSniffer')
            
            os.makedirs(download_dir, exist_ok=True)
            
            total = len(self.images)
            success = 0
            
            for i, image in enumerate(self.images):
                try:
                    Clock.schedule_once(
                        lambda dt, msg=f"正在下载 {i+1}/{total}": 
                        self._update_download_progress(msg, i / total)
                    )
                    
                    # 下载图片
                    response = requests.get(image.url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    file_path = os.path.join(download_dir, image.filename)
                    
                    # 确保文件名唯一
                    counter = 1
                    base_name, ext = os.path.splitext(file_path)
                    while os.path.exists(file_path):
                        file_path = f"{base_name}_{counter}{ext}"
                        counter += 1
                    
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    success += 1
                    
                except Exception as e:
                    print(f"下载失败 {image.url}: {str(e)}")
            
            Clock.schedule_once(lambda dt: self._download_completed(total, success, download_dir))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._download_failed(str(e)))
    
    def _update_download_progress(self, message, progress):
        """更新下载进度"""
        self.status_label.text = message
        self.progress_bar.value = progress * 100
    
    def _download_completed(self, total, success, download_dir):
        """下载完成"""
        self.download_all_btn.disabled = False
        self.sniff_btn.disabled = False
        self.status_label.text = f"下载完成: {success}/{total} 张图片成功"
        
        popup = Popup(
            title="下载完成",
            content=Label(text=f"共 {total} 张图片，成功下载 {success} 张\n保存位置: {download_dir}"),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def _download_failed(self, error_msg):
        """下载失败"""
        self.download_all_btn.disabled = False
        self.sniff_btn.disabled = False
        self.status_label.text = f"下载失败: {error_msg}"
        
        popup = Popup(
            title="下载失败",
            content=Label(text=error_msg),
            size_hint=(0.8, 0.4)
        )
        popup.open()


class ImageSnifferApp(App):
    """主应用"""
    
    def build(self):
        # 设置窗口标题
        self.title = "图片资源嗅探工具"
        
        # 创建屏幕管理器
        sm = ScreenManager()
        sm.add_widget(MainScreen())
        
        return sm


if __name__ == '__main__':
    ImageSnifferApp().run()