# vision_sensor.py (V3.0 - 含设备检测与自动退出功能)
import cv2
import requests
import time
import numpy as np
import sys

# 后端接口
API_URL = "http://127.0.0.1:8000/api/upload_data_v2"

# 绿色阈值
LOWER_GREEN = np.array([40, 40, 40])
UPPER_GREEN = np.array([80, 255, 255])

def run_vision_loop():
    # 1. 尝试打开摄像头 (Index 0)
    cap = cv2.VideoCapture(0)
    
    # 给摄像头一点预热时间
    time.sleep(1)

    # 2. 核心检测：判断设备是否存在
    if not cap.isOpened():
        # 返回特殊错误码 101，告诉主程序：没找到摄像头
        sys.exit(101)

    # 尝试读取一帧，确保真的能用
    ret, frame = cap.read()
    if not ret:
        sys.exit(101)

    print(">>> 摄像头启动成功")

    while True:
        ret, frame = cap.read()
        if not ret: break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        floating_count = 0
        for c in contours:
            if cv2.contourArea(c) > 500:
                floating_count += 1
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.putText(frame, f"Floating Objects: {floating_count}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        cv2.imshow("Smart Channel Vision Sensor (Running)", frame)
        
        try:
            # 发送数据
            payload = {
                "depth": 2.05,
                "velocity_surf": 1.5,
                "voltage": 12.5,
                "channel_width": 5.0,
                "sediment": 0.1,
                "floating_count": floating_count
            }
            requests.post(API_URL, json=payload, timeout=0.5)
        except:
            pass 

        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_vision_loop()