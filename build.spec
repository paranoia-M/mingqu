# -*- mode: python ; coding: utf-8 -*-
# build.spec - 终极稳定版配置，修复 Hook 导入错误

import sys
import os
# --- 修复点：只导入 collect_data_files，并将其用于所有数据收集 ---
from PyInstaller.utils.hooks import collect_data_files
# ----------------------------------------------------------------------

# 1. ANALYSIS: 分析主文件和数据依赖
a = Analysis(
    ['dashboard_final.py'], 
    pathex=['.'],           
    hiddenimports=[
        'pkg_resources.py2_warn', 
        'psutil._pswindows',      
        'win32timezone',          
        'uvicorn.lifespan.on',    
        'uvicorn.lifespan.off'
    ],
    excludes=[],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# 2. DATA FILES: 强制打包子目录和数据文件
a.datas += [
    ('simulator.py', '.'),
    ('vision_sensor.py', '.'),
    # 使用 tuple 格式打包目录，确保它们在 PyInstaller 内部是 collect_data_files 可以处理的格式
    ('core', 'core'),
    ('database', 'database'),
]

# 3. HOOKS: 强制收集复杂包的动态文件和 DLLs 
# 全部使用 collect_data_files
a.datas += collect_data_files('plotly')
a.datas += collect_data_files('pandas')
a.datas += collect_data_files('streamlit')
a.datas += collect_data_files('numpy')
a.datas += collect_data_files('cv2') 
a.datas += collect_data_files('uvicorn')

# 4. PYZ 和 EXE 定义 (生成可执行文件)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='ChannelMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False 
)