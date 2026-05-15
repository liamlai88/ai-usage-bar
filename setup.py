"""
py2app build script for AI Usage Bar.

Usage:
    # 开发模式（快速，symlink 资源，只能在本机运行）
    python setup.py py2app --alias

    # 发布模式（完整打包，可拷贝到其他机器）
    python setup.py py2app
"""
from setuptools import setup

APP_NAME = "AI Usage Bar"
APP_VERSION = "1.0.0"
BUNDLE_ID = "com.aiusagebar.widget"

APP = ["claude_widget.py"]

DATA_FILES = [
    ("assets", [
        "assets/claude_logo.png",
        "assets/openai_logo.png",
    ]),
]

OPTIONS = {
    "py2app": {
        "iconfile": "assets/AppIcon.icns",
        "plist": {
            "LSUIElement": True,
            "CFBundleIdentifier": BUNDLE_ID,
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleVersion": APP_VERSION,
            "LSMinimumSystemVersion": "12.0",
            "NSUserNotificationAlertStyle": "alert",
        },
        "packages": [
            "rumps",
            "requests",
            "urllib3",
            "certifi",
            "charset_normalizer",
            "idna",
            "Crypto",
            "serial",
            "data_sources",
        ],
        "includes": [
            "objc",
            "AppKit",
            "Foundation",
            "certifi",
            "Crypto.Cipher._AES",
            "Crypto.Protocol.KDF",
            "serial.serialutil",
            "serial.serialposix",
        ],
        "excludes": [
            "tkinter",
            "matplotlib",
            "numpy",
            "scipy",
            "PIL",
            "PyQt5",
            "wx",
            "test",
            "unittest",
        ],
        "resources": [
            "config.py",
            "i18n.py",
        ],
        "compressed": True,
        "arch": "arm64",
    }
}

setup(
    name=APP_NAME,
    version=APP_VERSION,
    app=APP,
    data_files=DATA_FILES,
    options=OPTIONS,
    setup_requires=["py2app"],
)
