# -*- mode: python ; coding: utf-8 -*-
# build.spec - Windows专用打包配置

import sys
import os
from pathlib import Path

# Windows特有的隐藏导入
WINDOWS_HIDDEN_IMPORTS = [
    # Windows系统相关
    'psutil._pswindows',
    'win32timezone',
    'pythoncom',
    'pywintypes',
    'win32api',
    'win32process',
    'win32event',
    'win32security',
    
    # 防止Windows上的DLL问题
    'multiprocessing.popen_spawn_win32',
    
    # Windows控制台支持
    'colorama',
]

# 1. ANALYSIS: 分析主文件和数据依赖
a = Analysis(
    ['dashboard_final.py'], 
    pathex=['.'],           
    hiddenimports=[
        # Streamlit核心
        'streamlit.web.cli',
        'streamlit.runtime',
        'streamlit.runtime.caching',
        'streamlit.proto',
        'streamlit.watcher.local_watcher',
        'streamlit.watcher.event_based_path_watcher',
        
        # ASGI服务器
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.http',
        'uvicorn.protocols.websockets',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        
        # 异步支持
        'asyncio',
        'asyncio.windows_events',  # Windows特有
        'concurrent.futures',
        
        # HTTP/网络
        'httpx',
        'httpcore',
        'httpcore._sync',
        'httpcore._async',
        'h11',
        'h2',
        
        # 数据库/数据
        'sqlalchemy',
        'sqlalchemy.ext',
        'sqlalchemy.dialects.sqlite',
        'pandas',
        'pandas._libs.tslibs',
        'numpy',
        'numpy.core',
        
        # 图形/绘图
        'plotly',
        'plotly.graph_objs',
        'plotly.io',
        'plotly.subplots',
        'plotly.basedatatypes',
        
        # 其他必要库
        'yaml',
        'toml',
        'PIL',
        'PIL._imaging',
        
        # 日志/配置
        'logging.handlers',
        'email.mime.text',
        'email.mime.multipart',
        'email.policy',
        
        # 添加Windows特有的隐藏导入
        *WINDOWS_HIDDEN_IMPORTS,
    ],
    excludes=[],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=True,  # 设置为True便于调试
)

# 2. 收集数据文件 - Windows专用方法
def collect_windows_data_files():
    """Windows环境下的数据文件收集"""
    datas = []
    
    try:
        # Streamlit文件
        import streamlit
        streamlit_path = Path(streamlit.__file__).parent
        
        # 递归收集streamlit静态文件
        for root, dirs, files in os.walk(streamlit_path / "static"):
            for file in files:
                if not file.endswith(('.py', '.pyc')):
                    src = Path(root) / file
                    rel_path = src.relative_to(streamlit_path.parent)
                    dest = str(rel_path.parent)
                    datas.append((str(src), dest))
                    
        # streamlit/runtime
        runtime_path = streamlit_path / "runtime"
        if runtime_path.exists():
            datas.append((str(runtime_path), "streamlit/runtime"))
            
    except ImportError as e:
        print(f"警告: 导入streamlit失败 - {e}")
    
    try:
        # Plotly文件
        import plotly
        plotly_path = Path(plotly.__file__).parent
        
        # plotly包数据
        package_data = plotly_path / "package_data"
        if package_data.exists():
            datas.append((str(package_data), "plotly/package_data"))
            
    except ImportError as e:
        print(f"警告: 导入plotly失败 - {e}")
    
    return datas

# 添加数据文件
print("正在收集Windows数据文件...")
a.datas += collect_windows_data_files()

# 3. 添加项目文件
PROJECT_FILES = [
    ('simulator.py', '.'),
    ('vision_sensor.py', '.'),
]

for src, dest in PROJECT_FILES:
    if os.path.exists(src):
        a.datas.append((src, dest))
        print(f"已添加: {src} -> {dest}")

# 4. 处理二进制文件 - Windows特有
def filter_windows_binaries():
    """过滤和添加Windows特有的二进制文件"""
    binaries = []
    
    # 保留所有二进制文件，让PyInstaller自动处理
    # 这里可以添加特定DLL的路径
    return binaries

# 5. Windows特有的配置
# 添加Windows manifest（可选）
# manifest = """
# <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
# <assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
#   <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
#     <security>
#       <requestedPrivileges>
#         <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
#       </requestedPrivileges>
#     </security>
#   </trustInfo>
# </assembly>
# """

# 6. PYZ和EXE配置
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
    upx_exclude=[],  # 可以排除某些文件
    runtime_tmpdir=None,
    console=True,  # Windows建议先用True查看错误
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # 自动检测（64位）
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加.ico图标
    # manifest=manifest,
)