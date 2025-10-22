# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\repositories\\magin-meet-copilot-pro\\src', 'src'), ('C:\\repositories\\magin-meet-copilot-pro\\templates', 'templates'), ('C:\\repositories\\magin-meet-copilot-pro\\.env', '.'), ('C:\\repositories\\magin-meet-copilot-pro\\google_credentials.json', '.'), ('.\\venv\\Lib\\site-packages\\tiktoken', 'tiktoken'), ('C:\\repositories\\magin-meet-copilot-pro\\chroma_db', 'chroma_db')],
    hiddenimports=['chromadb.telemetry.product.posthog', 'chromadb.api.rust'],
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
    name='MagicMeetCopilotPro',
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
    name='MagicMeetCopilotPro',
)
