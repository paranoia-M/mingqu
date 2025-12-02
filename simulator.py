# simulator.py (V2.0)
import requests
import time
import random

URL = "http://127.0.0.1:8000/api/upload_data_v2" # 注意接口变成了 v2

def simulate_sensor():
    print(">>> 全功能模拟器启动：水力 + 泥沙 + 视觉识别...")
    depth = 2.0
    
    while True:
        # 1. 水力变化
        change = random.uniform(-0.05, 0.05)
        depth += change
        if depth < 0.5: depth = 0.5
        velocity = 4.0 / depth + random.uniform(-0.1, 0.1)

        # 2. 模拟泥沙 (kg/m3) - 流速越快泥沙通常越大
        sediment = (velocity * 0.5) + random.uniform(0, 0.2)
        
        # 3. 模拟视觉识别漂浮物 (0-5个)
        # 随机突发漂浮物
        floating = 0
        if random.random() > 0.8: # 20% 概率出现漂浮物
            floating = random.randint(1, 6)

        payload = {
            "depth": round(depth, 3),
            "velocity_surf": round(velocity, 3),
            "voltage": 12.0,
            "channel_width": 5.0,
            "sediment": round(sediment, 2),
            "floating_count": floating
        }

        try:
            requests.post(URL, json=payload)
            print(f"发送: 水深={depth:.2f}m | 泥沙={sediment:.2f} | 漂浮物={floating}个")
        except Exception as e:
            print("连接后端失败:", e)

        time.sleep(1)

if __name__ == "__main__":
    simulate_sensor()