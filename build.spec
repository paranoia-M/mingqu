# -*- mode: python ; coding: utf-8 -*-
# build.spec - 终极稳定版配置

import sys
import os
# 只导入需要的工具函数
from PyInstaller.utils.hooks import get_package_paths

# 获取 Streamlit, Plotly, Uvicorn 的基础路径
try:
    # 尝试在 Linux/CI 环境中获取路径
    streamlit_path = get_package_paths('streamlit')[0][0]
    plotly_path = get_package_paths('plotly')[0][0]
except:
    # 如果失败，则使用默认值
    streamlit_path = ''
    plotly_path = ''

# 1. ANALYSIS: 分析主文件和数据依赖
a = Analysis(
    ['dashboard_final.py'], 
    pathex=['.'],           
    hiddenimports=[
        # 核心隐藏依赖
        'psutil._pswindows', 'win32timezone', 'matplotlib', 'numpy', 'scipy', 'cv2',
        'uvicorn.lifespan.on', 'uvicorn.lifespan.off'
    ],
    excludes=[],
    runtime_hooks=[],
    binaries=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# 2. DATA FILES: 手动打包核心数据目录
a.datas += [
    # 强制收集 Streamlit 的 Web 资源
    (os.path.join(streamlit_path, 'static'), 'streamlit/static'),
    (os.path.join(plotly_path, 'package_data'), 'plotly/package_data'),
    
    # 强制收集项目自己的文件
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
    a.zipfiles,
    a.datas,
    name='ChannelMonitor',
    debug=False,
    console=False, # 无控制台窗口
    # 指定平台特定的二进制文件，但由于是跨平台，保持简洁
)