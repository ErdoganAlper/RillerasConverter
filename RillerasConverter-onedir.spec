# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — one-folder build, used as the installer payload.

Produces dist\\RillerasConverter\\ containing the exe plus its libraries.
Nothing is unpacked at startup, so the app opens in about a second instead of
the ~20 s the single-file build needs to expand itself into %TEMP%. Inno Setup
packs this folder into RillerasConverterSetup.exe, so the end user still only
ever sees one file.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(SPECPATH))  # noqa: F821 - injected by PyInstaller
from build_common import analysis_inputs  # noqa: E402

datas, binaries, hiddenimports = analysis_inputs()

a = Analysis(
    ['RillerasConverter.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # libraries live beside the exe, not inside it
    name='RillerasConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon='convert.ico',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RillerasConverter',
)
