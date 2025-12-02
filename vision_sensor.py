import cv2
import requests
import time
import numpy as np
import sys

API_URL = "http://127.0.0.1:8000/api/upload_data_v2"
LOWER_GREEN = np.array([40, 40, 40])
UPPER_GREEN = np.array([80, 255, 255])

def run_vision():
    print(">>> 视觉识别子进程已启动...")
    cap = cv2.VideoCapture(0)
    time.sleep(1)
    if not cap.isOpened(): sys.exit(101)
    ret, _ = cap.read()
    if not ret: sys.exit(101)

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        count = sum(1 for c in contours if cv2.contourArea(c) > 500)
        
        for c in contours:
            if cv2.contourArea(c) > 500:
                x,y,w,h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
        
        cv2.putText(frame, f"Obj: {count}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.imshow("Vision Sensor", frame)
        
        try:
            payload = {"depth": 2.1, "velocity_surf": 1.6, "voltage": 12.0, "channel_width": 5.0, "sediment": 0.2, "floating_count": count}
            requests.post(API_URL, json=payload, timeout=0.5)
        except: pass
        
        if cv2.waitKey(100) == ord('q'): break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_vision()