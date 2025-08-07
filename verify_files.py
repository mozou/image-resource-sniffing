#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件验证脚本
确保所有必要的文件都存在且配置正确
"""

import os
import sys

def check_file_exists(filename, description):
    """检查文件是否存在"""
    if os.path.exists(filename):
        print(f"✅ {description}: {filename}")
        return True
    else:
        print(f"❌ {description}不存在: {filename}")
        return False

def check_buildozer_spec():
    """检查buildozer.spec配置"""
    if not os.path.exists('buildozer.spec'):
        print("❌ buildozer.spec 文件不存在")
        return False
    
    try:
        with open('buildozer.spec', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键配置
        checks = [
            ('title =', '应用标题'),
            ('package.name =', '包名'),
            ('package.domain =', '包域名'),
            ('source.dir =', '源码目录'),
            ('requirements =', '依赖包'),
            ('android.permissions =', 'Android权限'),
            ('android.api =', 'Android API'),
            ('android.minapi =', '最小Android API')
        ]
        
        all_good = True
        for config, desc in checks:
            if config in content:
                print(f"✅ {desc}配置存在")
            else:
                print(f"❌ {desc}配置缺失: {config}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ 读取buildozer.spec失败: {str(e)}")
        return False

def check_main_py():
    """检查main.py文件"""
    if not os.path.exists('main.py'):
        print("❌ main.py 文件不存在")
        return False
    
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键类和函数
        checks = [
            'class ImageSnifferApp',
            'class MainScreen',
            'class ImageSniffer',
            'if __name__ == \'__main__\'',
            'ImageSnifferApp().run()'
        ]
        
        all_good = True
        for check in checks:
            if check in content:
                print(f"✅ 找到关键代码: {check}")
            else:
                print(f"❌ 缺少关键代码: {check}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ 读取main.py失败: {str(e)}")
        return False

def main():
    """主验证函数"""
    print("🔍 开始文件验证...\n")
    
    # 显示当前目录
    print(f"当前工作目录: {os.getcwd()}")
    print(f"目录内容: {os.listdir('.')}\n")
    
    # 检查必要文件
    files_to_check = [
        ('main.py', '主应用文件'),
        ('buildozer.spec', 'Buildozer配置文件'),
        ('requirements.txt', 'Python依赖文件'),
        ('.github/workflows/build-android.yml', 'GitHub Actions工作流'),
        ('README.md', '说明文档')
    ]
    
    all_files_exist = True
    for filename, description in files_to_check:
        if not check_file_exists(filename, description):
            all_files_exist = False
    
    print()
    
    # 检查配置文件内容
    print("📋 检查配置文件内容...")
    buildozer_ok = check_buildozer_spec()
    print()
    
    print("📋 检查主程序文件...")
    main_py_ok = check_main_py()
    print()
    
    # 总结
    print("=" * 50)
    if all_files_exist and buildozer_ok and main_py_ok:
        print("🎉 所有文件验证通过！")
        print("项目已准备好进行构建。")
        print("\n可以运行以下命令:")
        print("1. 本地构建: buildozer android debug")
        print("2. 推送到GitHub进行云端构建")
        return True
    else:
        print("❌ 文件验证失败，请检查上述错误。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)