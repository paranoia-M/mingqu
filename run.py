# run.py (适配打包环境版)
import subprocess
import sys
import time
import os
import signal

def run_system():
    print("🚀 正在启动 [明渠非均匀流流量监测系统]...")
    
    # 检测是否在 PyInstaller 打包环境中运行
    if getattr(sys, 'frozen', False):
        # 如果是打包后的环境，Python 解释器不是 sys.executable，而是内部的依赖
        # 在 PyInstaller 单目录模式下，我们尽量寻找系统中的 python 或者
        # 更稳妥的方式：我们假设用户环境或者我们在 spec 里打包了 python 解释器。
        # 但最简单的方案是：依然尝试调用 python。
        # 注意：这里是一个简化处理。完美打包多进程 Streamlit 极度复杂。
        # 我们尝试使用环境变量中的 python，或者回退到 sys.executable (如果打包包含了解释器)
        python_cmd = sys.executable 
    else:
        # 开发环境
        python_cmd = sys.executable

    processes = []

    try:
        # 1. 启动后端
        print("-> 正在启动后端 API (Port 8000)...")
        # 注意：打包后 uvicorn 可能找不到，这里保持 -m 调用假设环境完整
        backend = subprocess.Popen(
            [python_cmd, "-m", "uvicorn", "main:app", "--reload"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        processes.append(backend)
        
        time.sleep(2)

        # 2. 启动前端
        print("-> 正在启动前端 Dashboard (Port 8501)...")
        frontend = subprocess.Popen(
            [python_cmd, "-m", "streamlit", "run", "dashboard_final.py"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        processes.append(frontend)

        print("✅ 系统启动完成！按 Ctrl+C 可一键关闭所有服务。")
        frontend.wait()

    except KeyboardInterrupt:
        print("\n🛑 接收到停止指令...")
    finally:
        for p in processes:
            try:
                p.terminate()
                p.wait()
            except: pass
        print("👋 退出。")

if __name__ == "__main__":
    run_system()