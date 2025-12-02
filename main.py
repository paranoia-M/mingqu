# main.py (V2.0 - 含泥沙、漂浮物、导出功能)
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import io
import csv

from database.models import SessionLocal, MonitorData, Base, engine
from core.hydraulic import HydraulicCalculator

# 重新创建表结构
Base.metadata.create_all(bind=engine)

app = FastAPI(title="明渠监测系统 V2.0")

# --- main.py 追加内容 ---

# 简单的内存列表，存储控制日志
control_logs = []

class ControlCommand(BaseModel):
    action: str      # 例如 "关闭闸门"
    operator: str    # 操作员
    reason: str      # 原因

@app.post("/api/control")
def send_control_command(cmd: ControlCommand):
    log_entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": cmd.action,
        "operator": cmd.operator,
        "reason": cmd.reason
    }
    control_logs.insert(0, log_entry) # 最新在最前
    return {"status": "success", "msg": f"指令 [{cmd.action}] 已下发"}

@app.get("/api/control/logs")
def get_control_logs():
    return control_logs

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

calculator = HydraulicCalculator()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# 升级后的数据输入模型
class SensorInput(BaseModel):
    depth: float
    velocity_surf: float
    voltage: float
    channel_width: float = 5.0
    sediment: float = 0.0        # 新增：含沙量 (kg/m3)
    floating_count: int = 0      # 新增：漂浮物数量 (个)

@app.post("/api/upload_data")
def upload_sensor_data(data: SensorInput, db: Session = Depends(get_db)):
    last_record = db.query(MonitorData).order_by(MonitorData.id.desc()).first()
    last_depth = last_record.depth if last_record else None
    
    area, v_avg, Q = calculator.calculate_flow(data.depth, data.channel_width, data.velocity_surf)
    fr, regime, risk = calculator.determine_regime(v_avg, data.depth)
    flow_type = calculator.check_non_uniform(data.depth, last_depth)

    alerts = []
    if risk != "正常": alerts.append(f"流态: {regime}")
    if data.floating_count > 3: alerts.append(f"漂浮物堆积({data.floating_count}个)") # 智能预警
    if data.sediment > 1.5: alerts.append("泥沙含量过高")
    
    alert_str = " | ".join(alerts) if alerts else "正常"

    new_record = MonitorData(
        timestamp=datetime.now(),
        depth=data.depth,
        velocity_surf=data.velocity_surf,
        voltage=data.voltage,
        velocity_avg=round(v_avg, 3),
        flow_rate=round(Q, 3),
        fr_number=fr,
        regime=regime,
        flow_type=flow_type,
        alert_msg=alert_str,
        # 新增字段存储（注意：需确保 models.py 里也加了这两列，这里为了简便直接存入通用结构，
        # 如果报错，请在 models.py 添加 sediment 和 floating_count 列。
        # 本次演示为了不修改 models.py，我们在 dashboard 直接取 API 数据，
        # 实际项目中建议去 models.py 加列。）
    )
    # 临时处理：为了方便，我们将这两个新数据存入 alert_msg 的附加信息里，
    # 或者你需要去 database/models.py 真正添加这两列。
    # 这里我们采用 "并在返回结果里" 的策略，模拟器发什么，前端就显示什么。
    
    db.add(new_record)
    db.commit()
    
    # 返回给前端的实时数据包
    return {
        "status": "success",
        "data": {
            "depth": data.depth,
            "flow_rate": round(Q, 3),
            "velocity_avg": round(v_avg, 3),
            "fr_number": fr,
            "regime": regime,
            "flow_type": flow_type,
            "alert_msg": alert_str,
            "sediment": data.sediment,        # 返回泥沙
            "floating_count": data.floating_count # 返回漂浮物
        }
    }

# 专门为前端提供的数据接口，不再查库，直接用全局变量缓存最新值（简化版）
# 在生产环境中应该查库，这里为了演示方便：
latest_cache = {}

@app.post("/api/upload_data_v2")
def upload_v2(data: SensorInput, db: Session = Depends(get_db)):
    # 复用上面的逻辑，但更新全局缓存
    res = upload_sensor_data(data, db)
    global latest_cache
    latest_cache = res["data"]
    return res

@app.get("/api/realtime")
def get_realtime_data():
    return latest_cache if latest_cache else {}

@app.get("/api/history")
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    data = db.query(MonitorData).order_by(MonitorData.timestamp.desc()).limit(limit).all()
    return data[::-1]

# 新增：导出接口
@app.get("/api/export")
def export_data(db: Session = Depends(get_db)):
    data = db.query(MonitorData).all()
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["ID", "时间", "水深", "流速", "流量", "Fr数", "流态", "报警"])
    for row in data:
        writer.writerow([row.id, row.timestamp, row.depth, row.velocity_surf, row.flow_rate, row.fr_number, row.regime, row.alert_msg])
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=monitor_data.csv"
    return response