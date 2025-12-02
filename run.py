# run.py (EXE 专用修复版)
import threading
import uvicorn
import sys
import os
import time
from streamlit.web import cli as stcli
from main import app
import simulator
import vision_sensor

def start_api():
    # 在线程中直接运行 FastAPI，不通过 subprocess
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def main():
    # 1. 检查是否有特殊参数 (用于子进程调度，防止 EXE 递归)
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "simulator":
            simulator.run_simulation()
            return
        elif cmd == "vision":
            vision_sensor.run_vision()
            return

    print("🚀 正在启动一体化监测系统...")

    # 2. 在后台线程启动后端 API
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    
    # 等待后端就绪
    time.sleep(2)

    # 3. 确定资源路径 (适配 PyInstaller)
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    dashboard_path = os.path.join(base_path, 'dashboard_final.py')

    # 4. 在主线程启动 Streamlit
    # 伪造命令行参数，让 Streamlit 以为是从命令行启动的
    sys.argv = [
        "streamlit",
        "run",
        dashboard_path,
        "--global.developmentMode=false",
        "--server.port=8501"
    ]
    
    print("✅ 前端正在加载，请稍候...")
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()