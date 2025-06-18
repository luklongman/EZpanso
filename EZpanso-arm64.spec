# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=[
        # Include only the specific icon needed
        ('icon.iconset/icon_512x512.png', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'yaml',
        'ruamel.yaml',
        'ruamel.yaml.main',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL.ImageTk',
        'PIL.ImageQt',
        'PyQt6.QtNetwork',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebChannel',
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtQuickWidgets',
        'PyQt6.QtSql',
        'PyQt6.QtTest',
        'PyQt6.QtBluetooth',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PyQt6.QtXml',
        'PyQt6.QtPdf',
        'PyQt6.QtPdfWidgets',
        'PyQt6.QtDBus',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.QtSpatialAudio',
        'PyQt6.Qt3DCore',
        'PyQt6.Qt3DRender',
        'PyQt6.Qt3DInput',
        'PyQt6.Qt3DLogic',
        'PyQt6.Qt3DAnimation',
        'PyQt6.Qt3DExtras',
        'PyQt6.QtCharts',
        'PyQt6.QtDataVisualization',
        'PyQt6.QtStateMachine',
        'PyQt6.QtRemoteObjects',
        'PyQt6.QtSerialPort',
        'PyQt6.QtTextToSpeech',
        'PyQt6.QtHelp',
        'PyQt6.QtUiTools',
        'PyQt6.QtDesigner',
        # Exclude unused Python modules (keeping essential ones)
        'email',
        'http',
        'sqlite3',
        'asyncio',
        'multiprocessing',
        'concurrent',
        'distutils',
        'unittest',
        'doctest',
        'pdb',
        'profile',
        'cProfile',
        'pstats',
        'timeit',
        'trace',
        'turtle',
        'curses',
        'readline',
        'rlcompleter',
        'shelve',
        'dbm',
        'csv',
        'configparser',
        'netrc',
        'xdrlib',
        'plistlib',
        'calendar',
        'mailcap',
        'mimetypes',
        'binhex',
        'quopri',
        'uu',
        'stringprep',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,  # Compress files to reduce size
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EZpanso',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch='arm64',  # Apple Silicon architecture
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='EZpanso',
)

# macOS app bundle
app = BUNDLE(
    coll,
    name='EZpanso.app',
    icon='icon.icns',
    bundle_identifier='com.longman.ezpanso.arm64',
    version='1.2.1',
    info_plist={
        'CFBundleName': 'EZpanso',
        'CFBundleDisplayName': 'EZpanso',
        'CFBundleVersion': '1.2.1',
        'CFBundleShortVersionString': '1.2.1',
        'CFBundleIdentifier': 'com.longman.ezpanso.arm64',
        'CFBundleExecutable': 'EZpanso',
        'CFBundleIconFile': 'icon.icns',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0.0',  # Apple Silicon requires macOS 11+
        'NSRequiresAquaSystemAppearance': False,
        'LSArchitecturePriority': ['arm64'],
    },
)
