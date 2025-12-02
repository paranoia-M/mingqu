# -*- mode: python ; coding: utf-8 -*-
# build.spec

import sys
import os

# 检查当前系统是否为 Windows (虽然我们在 CI 上是 Windows，但最好确保路径分隔符正确)
is_win = sys.platform.startswith('win')

# 定义需要包含的二进制文件（用于解决 DLL 缺失问题）
a = Analysis(
    ['dashboard_final.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('core', 'core'),
        ('database', 'database'),
        ('simulator.py', '.'),
        ('vision_sensor.py', '.'),
    ],
    hiddenimports=[
        'psutil._pswindows',
        'six',
        'pandas._libs.tslibs.base',
        'fastapi',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# 强制收集 Streamlit 和 Plotly 的全部依赖
a.datas += collect_data_files('streamlit')
a.datas += collect_data_data('plotly')
a.datas += collect_data_files('numpy') 
a.datas += collect_data_files('pandas') 
a.datas += collect_data_files('uvicorn')
a.datas += collect_data_files('requests')

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='ChannelMonitor', # 输出的EXE文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False  # 不显示黑色的命令行窗口
)