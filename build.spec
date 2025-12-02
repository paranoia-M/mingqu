# -*- mode: python ; coding: utf-8 -*-
# build.spec - 终极稳定版配置，修复 TOC 解析错误

import sys
import os
# 只导入需要的工具函数
from PyInstaller.utils.hooks import get_package_paths

# 获取 Streamlit, Plotly, Uvicorn 的基础路径
try:
    streamlit_path = get_package_paths('streamlit')[0][0]
    plotly_path = get_package_paths('plotly')[0][0]
    uvicorn_path = get_package_paths('uvicorn')[0][0]
except:
    streamlit_path = ''
    plotly_path = ''
    uvicorn_path = ''


# 1. ANALYSIS: 分析主文件和数据依赖
# 注意：a.binaries 保持为空列表，避免内部 Hook 污染
a = Analysis(
    ['dashboard_final.py'], 
    pathex=['.'],           
    hiddenimports=[
        'psutil._pswindows', 'win32timezone', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off', 
        'pandas', 'plotly', 'uvicorn', 'numpy', 'scipy', 'cv2'
    ],
    excludes=[],
    runtime_hooks=[],
    binaries=[], # <--- 关键修复点 1：不让 Hook 污染 binaries
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# 2. DATA FILES: 手动打包核心数据目录和依赖 (使用 3 元组格式)
# 确保所有路径都是 3 元组 ('dest_name', 'source_path', 'type') 或 ('source_path', 'dest_folder')

# 强制收集 Streamlit 的 Web 资源
a.datas += [
    (os.path.join(streamlit_path, 'static'), 'streamlit/static'),
    (os.path.join(streamlit_path, 'web'), 'streamlit/web'),
]

# 强制收集 Plotly 的核心数据
a.datas += [
    (os.path.join(plotly_path, 'package_data'), 'plotly/package_data')
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

# 关键修复点 2：将 a.binaries 从 EXE 构造函数中移除（因为它已经被清空，而且是错误源）
exe = EXE(
    pyz,
    a.scripts,
    # a.binaries,  <--- 已移除
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