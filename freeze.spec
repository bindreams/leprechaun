# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from importlib.util import find_spec

sys.setrecursionlimit(5000)
block_cipher = None

def module_dir(module_name):
    """Return module's root directory.
    If the module does not have a directory (it is a single file) then return None.
    """
    module_origin = find_spec(module_name).origin
    if os.path.basename(module_origin) == "__init__.py":
        return os.path.dirname(module_origin)
    return None


a = Analysis(
    ['lepricon/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[(module_dir("lepricon") + "/data", "lepricon/data")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='lepricon',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    uac_admin=True,
    icon="assets/icon.ico"
)
