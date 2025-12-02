import requests
import time
import random

URL = "http://127.0.0.1:8000/api/upload_data_v2"

def run_simulation():
    print(">>> 模拟器子进程已启动...")
    depth = 2.0
    while True:
        depth += random.uniform(-0.05, 0.05)
        if depth < 0.5: depth = 0.5
        velocity = 4.0 / depth + random.uniform(-0.1, 0.1)
        sediment = (velocity * 0.3) + random.uniform(0, 0.1)
        floating = random.randint(1, 5) if random.random() > 0.85 else 0

        payload = {
            "depth": round(depth, 3),
            "velocity_surf": round(velocity, 3),
            "voltage": 12.5,
            "channel_width": 5.0,
            "sediment": round(sediment, 2),
            "floating_count": floating
        }
        try: requests.post(URL, json=payload)
        except: pass
        time.sleep(1)

if __name__ == "__main__":
    run_simulation()