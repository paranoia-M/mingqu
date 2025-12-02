# database/models.py
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 创建本地数据库文件
SQLALCHEMY_DATABASE_URL = "sqlite:///./channel_monitor.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MonitorData(Base):
    __tablename__ = "monitor_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    
    # 采集原始数据
    depth = Column(Float)           # 水深
    velocity_surf = Column(Float)   # 表面流速
    voltage = Column(Float)         # 设备电压
    
    # 计算得出的数据
    velocity_avg = Column(Float)    # 平均流速
    flow_rate = Column(Float)       # 流量 Q
    fr_number = Column(Float)       # Fr 数
    
    # 判别结果
    regime = Column(String)         # 流态：缓流/急流
    flow_type = Column(String)      # 工况：均匀/非均匀
    alert_msg = Column(String)      # 报警信息

# 自动创建表
Base.metadata.create_all(bind=engine)