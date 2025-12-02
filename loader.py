# loader.py - PyInstaller 启动器
import sys
import os
import subprocess
import time

# --- 关键：添加 Streamlit 依赖目录到 Python 路径 ---
# 在 PyInstaller 的 --onedir 模式下，依赖文件位于程序根目录或子目录
# 需要手动将这些目录添加到 sys.path
def setup_path():
    # 假设打包后的 Streamlit 依赖在 'streamlit' 文件夹内
    base_path = os.path.dirname(sys.executable)
    
    # 尝试寻找 Streamlit 安装目录 (在打包文件夹的 Lib/site-packages 附近)
    # 这部分路径会根据 PyInstaller 版本有所不同，这里提供一个经验路径
    try:
        if sys.platform.startswith('win'):
            # 在 Windows 打包的文件夹结构中查找核心库
            site_packages_dir = os.path.join(base_path, 'Lib', 'site-packages')
            if os.path.isdir(site_packages_dir):
                sys.path.append(site_packages_dir)
            
            # 确保当前目录也在路径中
            sys.path.append(base_path)

    except Exception as e:
        # 如果路径设置失败，打印错误但不退出
        pass

# ----------------------------------------------------
setup_path()

try:
    # 尝试导入 Streamlit 核心模块
    import streamlit.web.bootstrap as st_bootstrap
    
    # 启动 FastAPI 后端 (main.py)
    # 注意：我们不能在这里启动 main.py，因为 Streamlit 占据了主进程。
    # 我们需要在启动 Streamlit 之前，确保 FastAPI 后端已在子进程中启动。
    # 由于 FastAPI 启动复杂，我们简化为：在 main.py 内部启动 Streamlit

    # 替换为主程序的启动逻辑
    # 核心：将主程序入口指向 dashboard_final.py
    
    # 为了简化，我们直接运行 dashboard_final.py
    
    # 注意：PyInstaller 必须将 dashboard_final.py 识别为脚本
    import dashboard_final
    
except ImportError as e:
    # 打印最终的错误信息
    print(f"FATAL ERROR: Failed to load core libraries: {e}")
    print("Please ensure that PyInstaller collected all hidden dependencies (e.g., Streamlit, FastAPI).")
    time.sleep(10) # 保持窗口开启，方便调试
    sys.exit(1)
except Exception as e:
    # 打印其他运行时错误
    print(f"FATAL RUNTIME ERROR: {e}")
    time.sleep(10)
    sys.exit(1)