[app]

# Application name as shown on Android
title = Survey Office Manager

# Android package details. Keep package.name lowercase with no spaces.
package.name = surveyofficemanager
package.domain = org.referencepoint

# Source files
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = tests,bin,build,.buildozer,__pycache__,venv,env,buildozer_env
source.exclude_exts = pyc,pyo

# App version
version = 0.1.0

# Python/Kivy requirements
requirements = python3,kivy

# Android UI settings
orientation = portrait
fullscreen = 0

# App icon
icon.filename = %(source.dir)s/icon.png

# Android build settings
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

# Keep debug APK output as APK for easy phone installation.
android.debug_artifact = apk
p4a.bootstrap = sdl2

# Log level
log_level = 2

[buildozer]

# 0 = normal output, 1 = debug output
log_level = 2
warn_on_root = 1

android.release_artifact = apk
