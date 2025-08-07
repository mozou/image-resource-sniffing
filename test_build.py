#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建测试脚本
用于验证构建环境和依赖是否正确配置
"""

import sys
import importlib
import subprocess
import os

def test_python_version():
    """测试Python版本"""
    print(f"Python版本: {sys.version}")
    if sys.version_info < (3, 7):
        print("❌ Python版本过低，需要3.7+")
        return False
    print("✅ Python版本符合要求")
    return True

def test_dependencies():
    """测试依赖包"""
    required_packages = [
        'kivy',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def test_buildozer_config():
    """测试buildozer配置"""
    if not os.path.exists('buildozer.spec'):
        print("❌ buildozer.spec 文件不存在")
        return False
    
    print("✅ buildozer.spec 文件存在")
    
    # 检查关键配置
    with open('buildozer.spec', 'r', encoding='utf-8') as f:
        content = f.read()
        
    required_configs = [
        'title =',
        'package.name =',
        'package.domain =',
        'requirements =',
        'android.permissions ='
    ]
    
    for config in required_configs:
        if config in content:
            print(f"✅ 找到配置: {config}")
        else:
            print(f"❌ 缺少配置: {config}")
            return False
    
    return True

def test_main_file():
    """测试主文件"""
    if not os.path.exists('main.py'):
        print("❌ main.py 文件不存在")
        return False
    
    print("✅ main.py 文件存在")
    
    # 尝试导入主模块
    try:
        import main
        print("✅ main.py 可以正常导入")
        return True
    except Exception as e:
        print(f"❌ main.py 导入失败: {str(e)}")
        return False

def test_buildozer_command():
    """测试buildozer命令"""
    try:
        result = subprocess.run(['buildozer', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Buildozer版本: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Buildozer命令失败: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Buildozer未安装")
        print("请运行: pip install buildozer")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Buildozer命令超时")
        return False
    except Exception as e:
        print(f"❌ Buildozer测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🔍 开始构建环境测试...\n")
    
    tests = [
        ("Python版本", test_python_version),
        ("依赖包", test_dependencies),
        ("Buildozer配置", test_buildozer_config),
        ("主文件", test_main_file),
        ("Buildozer命令", test_buildozer_command)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！构建环境配置正确。")
        print("您可以运行以下命令构建APK:")
        print("buildozer android debug")
        return True
    else:
        print("❌ 部分测试失败，请检查上述错误信息。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)