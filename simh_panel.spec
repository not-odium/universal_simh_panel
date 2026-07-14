# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
ROOT = os.path.abspath('.')

a = Analysis(
    ['main.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        ('config/*.json', 'config'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'ui',
        'ui.main_window',
        'ui.panel_widget',
        'ui.terminal_widget',
        'ui.indicators',
        'core',
        'core.simh_controller',
        'core.config_loader',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter', 'unittest', 'email',
        'html', 'http', 'xml', 'pydoc', 'doctest',
        'argparse', 'difflib', 'inspect', 'pdb',
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SIMH_Panel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
