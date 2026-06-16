# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules


hiddenimports = [
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "yaml",
    "numpy",
    "pandas",
    "sklearn.cluster",
    "sklearn.cluster._kmeans",
    "sklearn.metrics",
    "sklearn.metrics.pairwise",
    "scipy",
    "scipy.linalg",
    "scipy.sparse",
]
hiddenimports += collect_submodules("backend.app")
hiddenimports += collect_submodules("core")

a = Analysis(
    ["desktop_entry.py"],
    pathex=["."],
    binaries=[],
    datas=[("app/config/probe_profiles.yaml", "backend/app/config")],
    hiddenimports=hiddenimports,
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
    name="powermeter-backend",
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
    name="powermeter-backend",
)
