# -*- coding: utf-8 -*-
"""
图片资源嗅探工具 - 简化版本
专为Android APK构建优化
"""

import os
import re
import threading
from urllib.parse import urljoin, urlparse

import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import platform

# Android权限请求
if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
        from android.storage import primary_external_storage_path
        request_permissions([
            Permission.INTERNET,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE
        ])
    except ImportError:
        pass


class ImageSniffer:
    """简化的图片嗅探器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        })
    
    def get_images(self, url, min_size_kb=10):
        """获取图片列表"""
        try:
            # 获取页面内容
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            
            # 提取图片URL
            image_urls = set()
            
            # img标签的src
            for match in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I):
                img_url = urljoin(url, match.group(1))
                if self._is_image_url(img_url):
                    image_urls.add(img_url)
            
            # img标签的data-src（懒加载）
            for match in re.finditer(r'<img[^>]+data-src=["\']([^"\']+)["\']', html, re.I):
                img_url = urljoin(url, match.group(1))
                if self._is_image_url(img_url):
                    image_urls.add(img_url)
            
            # 过滤图片
            valid_images = []
            min_size_bytes = min_size_kb * 1024
            
            for img_url in image_urls:
                try:
                    head_resp = self.session.head(img_url, timeout=10)
                    if head_resp.status_code == 200:
                        size = int(head_resp.headers.get('Content-Length', 0))
                        if size >= min_size_bytes:
                            filename = os.path.basename(urlparse(img_url).path) or f"image_{len(valid_images)}.jpg"
                            valid_images.append({
                                'url': img_url,
                                'size': size,
                                'filename': filename
                            })
                except:
                    continue
            
            return sorted(valid_images, key=lambda x: x['size'], reverse=True)
            
        except Exception as e:
            raise Exception(f"嗅探失败: {str(e)}")
    
    def _is_image_url(self, url):
        """判断是否为图片URL"""
        return any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'])


class MainApp(App):
    """主应用"""
    
    def build(self):
        self.title = "图片资源嗅探工具"
        self.sniffer = ImageSniffer()
        self.images = []
        
        # 主布局
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # 标题
        title = Label(text="图片资源嗅探工具", size_hint_y=None, height=dp(40), font_size=dp(18))
        layout.add_widget(title)
        
        # URL输入
        url_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        url_layout.add_widget(Label(text="网址:", size_hint_x=None, width=dp(60)))
        self.url_input = TextInput(multiline=False, hint_text="请输入网址")
        url_layout.add_widget(self.url_input)
        layout.add_widget(url_layout)
        
        # 最小大小设置
        size_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        size_layout.add_widget(Label(text="最小大小(KB):", size_hint_x=None, width=dp(100)))
        self.size_input = TextInput(text="10", multiline=False, size_hint_x=None, width=dp(80))
        size_layout.add_widget(self.size_input)
        layout.add_widget(size_layout)
        
        # 按钮
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))
        
        self.sniff_btn = Button(text="开始嗅探")
        self.sniff_btn.bind(on_press=self.start_sniff)
        btn_layout.add_widget(self.sniff_btn)
        
        self.download_btn = Button(text="批量下载", disabled=True)
        self.download_btn.bind(on_press=self.download_all)
        btn_layout.add_widget(self.download_btn)
        
        layout.add_widget(btn_layout)
        
        # 进度条
        self.progress = ProgressBar(size_hint_y=None, height=dp(20))
        layout.add_widget(self.progress)
        
        # 状态标签
        self.status = Label(text="就绪", size_hint_y=None, height=dp(30))
        layout.add_widget(self.status)
        
        # 结果列表
        scroll = ScrollView()
        self.result_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.result_layout.bind(minimum_height=self.result_layout.setter('height'))
        scroll.add_widget(self.result_layout)
        layout.add_widget(scroll)
        
        return layout
    
    def start_sniff(self, instance):
        """开始嗅探"""
        url = self.url_input.text.strip()
        if not url:
            self.show_popup("错误", "请输入网址")
            return
        
        try:
            min_size = int(self.size_input.text or "10")
        except:
            min_size = 10
        
        self.sniff_btn.disabled = True
        self.download_btn.disabled = True
        self.result_layout.clear_widgets()
        self.progress.value = 0
        self.status.text = "正在嗅探..."
        
        # 在线程中执行
        threading.Thread(target=self._sniff_thread, args=(url, min_size), daemon=True).start()
    
    def _sniff_thread(self, url, min_size):
        """嗅探线程"""
        try:
            Clock.schedule_once(lambda dt: setattr(self.progress, 'value', 50))
            images = self.sniffer.get_images(url, min_size)
            Clock.schedule_once(lambda dt: self._sniff_done(images))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._sniff_error(str(e)))
    
    def _sniff_done(self, images):
        """嗅探完成"""
        self.images = images
        self.sniff_btn.disabled = False
        self.progress.value = 100
        
        if images:
            self.download_btn.disabled = False
            self.status.text = f"找到 {len(images)} 张图片"
            
            for img in images:
                item = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=dp(10))
                
                # 图片信息
                info = Label(
                    text=f"{img['filename']}\n{img['size']/1024:.1f} KB",
                    size_hint_x=0.7,
                    text_size=(None, None),
                    halign='left'
                )
                item.add_widget(info)
                
                # 下载按钮
                btn = Button(text="下载", size_hint_x=0.3)
                btn.bind(on_press=lambda x, url=img['url'], name=img['filename']: self.download_single(url, name))
                item.add_widget(btn)
                
                self.result_layout.add_widget(item)
        else:
            self.status.text = "未找到符合条件的图片"
    
    def _sniff_error(self, error):
        """嗅探错误"""
        self.sniff_btn.disabled = False
        self.progress.value = 0
        self.status.text = f"嗅探失败: {error}"
        self.show_popup("嗅探失败", error)
    
    def download_single(self, url, filename):
        """下载单张图片"""
        threading.Thread(target=self._download_thread, args=([{'url': url, 'filename': filename}],), daemon=True).start()
    
    def download_all(self, instance):
        """批量下载"""
        if not self.images:
            return
        
        self.download_btn.disabled = True
        self.status.text = "正在下载..."
        threading.Thread(target=self._download_thread, args=(self.images,), daemon=True).start()
    
    def _download_thread(self, images):
        """下载线程"""
        try:
            # 获取下载目录
            if platform == 'android':
                try:
                    download_dir = os.path.join(primary_external_storage_path(), 'Download', 'ImageSniffer')
                except:
                    download_dir = '/sdcard/Download/ImageSniffer'
            else:
                download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'ImageSniffer')
            
            os.makedirs(download_dir, exist_ok=True)
            
            success = 0
            total = len(images)
            
            for i, img in enumerate(images):
                try:
                    Clock.schedule_once(lambda dt, msg=f"下载中 {i+1}/{total}": setattr(self.status, 'text', msg))
                    
                    response = self.sniffer.session.get(img['url'], timeout=30)
                    response.raise_for_status()
                    
                    filepath = os.path.join(download_dir, img['filename'])
                    
                    # 避免重名
                    counter = 1
                    base, ext = os.path.splitext(filepath)
                    while os.path.exists(filepath):
                        filepath = f"{base}_{counter}{ext}"
                        counter += 1
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    success += 1
                    
                except Exception as e:
                    print(f"下载失败 {img['url']}: {e}")
            
            Clock.schedule_once(lambda dt: self._download_done(total, success, download_dir))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._download_error(str(e)))
    
    def _download_done(self, total, success, download_dir):
        """下载完成"""
        self.download_btn.disabled = False
        self.status.text = f"下载完成: {success}/{total}"
        self.show_popup("下载完成", f"成功下载 {success}/{total} 张图片\n保存位置: {download_dir}")
    
    def _download_error(self, error):
        """下载错误"""
        self.download_btn.disabled = False
        self.status.text = f"下载失败: {error}"
        self.show_popup("下载失败", error)
    
    def show_popup(self, title, message):
        """显示弹窗"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()


if __name__ == '__main__':
    MainApp().run()