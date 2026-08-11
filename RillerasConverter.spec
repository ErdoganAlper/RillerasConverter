# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec.

Paths are relative to this file so the build works from any checkout — the
previous version hard-coded an absolute path from the original dev machine.
"""

from PyInstaller.utils.hooks import collect_all

datas = [('convert.ico', '.')]
binaries = []
hiddenimports = [
    'rilleras',
    'rilleras.app',
    'rilleras.core',
    'rilleras.modes',
    'rilleras.settings',
    'rilleras.theme',
]

# These pull in data files / native libs that static analysis alone misses.
for _pkg in ('pdf2docx', 'docx2pdf', 'tkinterdnd2', 'img2pdf'):
    try:
        _d, _b, _h = collect_all(_pkg)
        datas += _d
        binaries += _b
        hiddenimports += _h
    except Exception:
        pass  # optional package not installed in this environment

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
    a.binaries,
    a.datas,
    [],
    name='RillerasConverter',
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
    icon='convert.ico',
    codesign_identity=None,
    entitlements_file=None,
)
