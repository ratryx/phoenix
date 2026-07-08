# -*- mode: python ; coding: utf-8 -*-
"""
Arquivo de build do PyInstaller para o Phoenix Optimizer v2.

Inclui:
- Fontes do pyfiglet (carregadas dinamicamente, PyInstaller não detecta
  automaticamente — sem isso, o .exe abre e fecha com
  "ModuleNotFoundError: No module named 'pyfiglet.fonts'")
- Pasta gui/ completa (index.html, style.css, app.js) — necessária para
  o Modo GUI funcionar no executável empacotado.
- Ícone da fênix no executável final.

Como usar:
    pyinstaller phoenix.spec

O executável final aparece em dist\PhoenixOptimizer.exe
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('pyfiglet')
datas += [('gui', 'gui')]

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['webview.platforms.winforms', 'webview.platforms.edgechromium'],
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
    a.binaries,
    a.datas,
    [],
    name='PhoenixOptimizer',
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
    icon='assets\\phoenix.ico',
)
