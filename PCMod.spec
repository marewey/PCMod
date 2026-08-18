# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Only bundle essential source icon assets, excluding heavy data/packs, data/update, or log files
datas_list = []
if os.path.exists('data/icons'):
    datas_list.append(('data/icons', 'data/icons'))
if os.path.exists('bin'):
    datas_list.append(('bin', 'bin'))

a = Analysis(
    ['PCMod.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'clr',
        'System',
        'System.Windows.Forms',
        'System.Drawing',
        'webview',
        'portablemc',
        'bottle',
        'proxy_tools'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'email', 'http.server'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PCMod',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon='data/icons/icon.ico'
)
