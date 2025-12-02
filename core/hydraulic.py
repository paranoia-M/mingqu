# core/hydraulic.py
import numpy as np

class HydraulicCalculator:
    def __init__(self, g=9.81):
        self.g = g  # 重力加速度

    def calculate_flow(self, depth: float, width: float, velocity_surf: float, correction_factor=0.85):
        """
        计算断面参数和流量
        :param depth: 水深 (m)
        :param width: 水面宽 (m) - 假设为矩形断面，若为梯形需修改此处公式
        :param velocity_surf: 表面流速 (m/s)
        :param correction_factor: 表面流速转平均流速系数
        """
        # 1. 计算过流面积 A
        area = depth * width
        
        # 2. 计算平均流速 V (修正)
        velocity_avg = velocity_surf * correction_factor
        
        # 3. 计算流量 Q = A * V
        flow_rate = area * velocity_avg
        
        return area, velocity_avg, flow_rate

    def determine_regime(self, velocity_avg: float, depth: float):
        """
        流态判别 (核心需求)
        根据 Fr数 判别 缓流/急流/临界流
        Fr = V / sqrt(g * h)
        """
        if depth <= 0:
            return 0.0, "无水", "无风险"

        # 计算弗劳德数 Fr
        fr_number = velocity_avg / np.sqrt(self.g * depth)
        
        # 判别逻辑
        if fr_number < 0.95:
            regime = "缓流 (Subcritical)"
            risk_level = "正常"
        elif fr_number > 1.05:
            regime = "急流 (Supercritical)"
            risk_level = "高风险 (冲刷预警)"
        else:
            regime = "临界流 (Critical)"
            risk_level = "不稳定"
            
        return round(fr_number, 3), regime, risk_level

    def check_non_uniform(self, current_depth, last_depth, distance_step=1.0):
        """
        判别均匀流/非均匀流
        依据：沿程水深变化率 dh/dx
        """
        if last_depth is None:
            return "初始化"
            
        diff = abs(current_depth - last_depth)
        # 设定一个极小阈值，例如 0.005m (5mm)
        if diff / distance_step < 0.005:
            return "均匀流"
        else:
            if current_depth > last_depth:
                return "非均匀流 (雍水)"
            else:
                return "非均匀流 (降水)"