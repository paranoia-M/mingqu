# run_build.py - PyInstaller 打包的真实入口
# 这个文件将作为打包的主文件
import os
import sys
import subprocess

# 检查环境变量 ST_IS_BUILDER，如果存在，则运行 Streamlit 应用
if os.environ.get('ST_IS_BUILDER') == 'TRUE':
    try:
        # Streamlit 启动命令
        # 注意：这里我们让它运行 dashboard_final.py
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard_final.py", "--global.developmentMode", "false"], check=True)
    except Exception as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)
else:
    # 正常启动时，让 PyInstaller 知道如何处理
    # 这一行通常由 PyInstaller Hook 处理，但为了确保，可以留作备用启动
    os.environ['ST_IS_BUILDER'] = 'TRUE'
    subprocess.run([sys.executable, __file__])