# -*- mode: python ; coding: utf-8 -*-
# build.spec - 最终稳定版配置，修复 NameError

import sys
import os
# --- 修复点：必须明确导入 PyInstaller 的工具函数 ---
from PyInstaller.utils.hooks import collect_data_files, collect_data_data 
# ----------------------------------------------------

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
    ('core', 'core'),
    ('database', 'database'),
]

# 3. HOOKS: 强制收集复杂包的动态文件和 DLLs 
a.datas += collect_data_files('plotly')
a.datas += collect_data_files('pandas')
a.datas += collect_data_files('streamlit')
a.datas += collect_data_files('numpy')
a.datas += collect_data_files('cv2') # OpenCV
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