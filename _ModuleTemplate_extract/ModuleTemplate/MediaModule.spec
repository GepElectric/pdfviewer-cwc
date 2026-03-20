# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Mazda\\Desktop\\Program\\CWC\\PdfViewer\\_ModuleTemplate_extract\\ModuleTemplate\\main.py'],
    pathex=['C:\\Users\\Mazda\\Desktop\\Program\\CWC\\PdfViewer\\_ModuleTemplate_extract\\ModuleTemplate', 'C:\\Users\\Mazda\\Desktop\\Program\\CWC\\PdfViewer\\_ModuleTemplate_extract\\ModuleTemplate\\media_module'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MediaModule',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
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
    name='MediaModule',
)
