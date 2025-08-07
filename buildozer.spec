[app]

# (str) Title of your application
title = 图片资源嗅探工具

# (str) Package name
package.name = imageresourcesniffer

# (str) Package domain (needed for android/ios packaging)
package.domain = com.imageresourcesniffer

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,txt,md

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .buildozer, .git, __pycache__

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.1.0,requests,urllib3,certifi,charset-normalizer,idna,pillow

# (str) Supported orientation (landscape, sensorLandscape, portrait, sensorPortrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 23b

# 注意：android.sdk 配置项已弃用，由buildozer自动管理

# (str) Android build tools version to use
android.build_tools = 31.0.0

# (bool) Enable AndroidX support. Enable when 'android.gradle_dependencies'
# contains an 'androidx' package, or any package from Kotlin source.
# android.enable_androidx requires android.api >= 28
android.enable_androidx = False

# (str) Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
# 先只构建arm64-v8a架构以减少构建时间和复杂度
android.archs = arm64-v8a

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = False

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (str) Full name including package path of the Java class that implements Android Activity
android.activity_class_name = org.kivy.android.PythonActivity

# (str) Full name including package path of the Java class that implements Python Service
android.service_class_name = org.kivy.android.PythonService

# (str) Android app theme, default is ok for Kivy-based app
android.theme = "@android:style/Theme.NoTitleBar"

# (list) Pattern to whitelist for the whole project
android.whitelist =

# (str) Path to a custom whitelist file
android.whitelist_src =

# (str) Path to a custom blacklist file
android.blacklist_src =

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars can slow
# down the build process. Allows wildcards matching, for example:
# OUYA-ODK/libs/*.jar
android.add_jars = 

# (list) List of Java files to add to the android project (can be java or a
# directory containing the files)
android.add_src =

# (list) Android AAR archives to add
android.add_aars =

# (list) Gradle dependencies to add
android.gradle_dependencies =

# (list) add java compile options
android.add_compile_options =

# (list) Gradle repositories to add {can be necessary for some android.gradle_dependencies}
android.gradle_repositories =

# (str) python-for-android fork to use, defaults to upstream (kivy)
p4a.fork = kivy

# (str) python-for-android branch to use, defaults to master
p4a.branch = master

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
p4a.source_dir =

# (str) The directory in which python-for-android should look for your own build recipes (if any)
p4a.local_recipes =

# (list) python-for-android whitelist
p4a.whitelist =

# (bool) indicates if you want to include sqlite3 so the internal sqlite3 will be used
p4a.setup_py = False

# (str) python-for-android specific commit to use, defaults to HEAD, must be within p4a.branch
# 使用更稳定的旧版本
p4a.commit = HEAD

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

# (str) extra command line arguments to pass when invoking pythonforandroid.toolchain
p4a.extra_args =

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
bin_dir = ./bin
