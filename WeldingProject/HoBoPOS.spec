# PyInstaller spec - HoBo POS Windows .exe
# Run from repo root (hobo_license_pos): see docs/BUILDING_EXE_WINDOWS.md
# Before running: 1) npm run build in yp_posf with base /app/, 2) copy yp_posf/dist to WeldingProject/static_frontend
# Note: No .py source is bundled — only bytecode. See docs/SECURITY_AND_PROTECTION.md for hardening (Nuitka, PyArmor, DB encryption).

import sys
from pathlib import Path

# Spec is in WeldingProject/HoBoPOS.spec; repo root = parent of WeldingProject
WELDING = Path(SPEC).resolve().parent
REPO_ROOT = WELDING.parent
STATIC_FRONTEND = WELDING / 'static_frontend'
BUILD_OBF = WELDING / 'build_obf'

# Use obfuscated code if build_obf exists (build_exe.bat runs PyArmor first)
if (BUILD_OBF / 'run_server.py').exists():
    _script = BUILD_OBF / 'run_server.py'
    _pathex = [str(BUILD_OBF), str(WELDING), str(REPO_ROOT)]
else:
    _script = WELDING / 'run_server.py'
    _pathex = [str(WELDING), str(REPO_ROOT)]

# Vue build output must exist
if not STATIC_FRONTEND.exists() or not (STATIC_FRONTEND / 'index.html').exists():
    raise SystemExit(
        'Missing WeldingProject/static_frontend (Vue build).\n'
        'Run: cd yp_posf && set VITE_BASE=/app/ && npm run build\n'
        'Then: xcopy /E /I /Y yp_posf\\dist WeldingProject\\static_frontend'
    )

a = Analysis(
    [str(_script)],
    pathex=_pathex,
    datas=[
        (str(STATIC_FRONTEND), 'static_frontend'),
    ],
    hiddenimports=[
        'django',
        'waitress',
        'WeldingProject.wsgi',
        'WeldingProject.settings',
        'core', 'inventory', 'customer', 'license', 'notification', 'service', 'ai', 'accounting', 'installation',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# onedir: folder တစ်ခုထဲမှာ .exe + လိုအပ်တာတွေ အကုန်ထွက်မယ် (zip/copy လုပ်ပြီး ပို့လို့ရတယ်)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HoBoPOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
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
    name='HoBoPOS',
)
