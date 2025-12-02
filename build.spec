# -*- mode: python ; coding: utf-8 -*-
# build.spec - 修复 PyInstaller 内部 TOC 解析错误

import sys
import os

# --- 导入 os 路径函数，用于跨平台路径 ---
from PyInstaller.utils.hooks import get_package_paths, collect_submodules 
# ----------------------------------------------------------------------

# 获取 Streamlit 和 Plotly 的基础路径
# (这是确保 PyInstaller 找到数据文件的关键)
# try/except 用于保证CI环境能找到路径，否则使用默认值
try:
    streamlit_path = get_package_paths('streamlit')[0]
    plotly_path = get_package_paths('plotly')[0]
except:
    streamlit_path = ''
    plotly_path = ''

# 1. ANALYSIS: 分析主文件和数据依赖
a = Analysis(
    ['dashboard_final.py'], 
    pathex=['.'],           
    hiddenimports=[
        'psutil._pswindows',
        'win32timezone',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'pandas',  # 确保 Pandas 被完全导入
        'plotly'   # 确保 Plotly 被完全导入
    ],
    excludes=[],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# 2. DATA FILES: 手动打包核心数据目录
# 使用 [(source_path, dest_folder)] 格式

# 强制收集 Streamlit 的静态文件和 Web 界面
a.datas += [
    (os.path.join(streamlit_path, 'static'), 'streamlit/static'),
    (os.path.join(streamlit_path, 'web'), 'streamlit/web'),
    (os.path.join(plotly_path, 'package_data'), 'plotly/package_data'),
]

# 强制收集项目自己的文件
a.datas += [
    ('simulator.py', '.'),
    ('vision_sensor.py', '.'),
    ('core', 'core'),
    ('database', 'database'),
]

# 3. PYZ 和 EXE 定义 (生成可执行文件)
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