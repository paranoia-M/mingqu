# dashboard_final.py (V24.1 - 最终完整版)
import streamlit as st
import streamlit.components.v1 as components
import requests
import subprocess
import sys
import os
import signal
import time
import pandas as pd
import plotly.express as px
import numpy as np             
import plotly.graph_objects as go 
from datetime import datetime

# 1. 页面配置
st.set_page_config(
    page_title="", 
    layout="wide", 
    page_icon="🌊",
    initial_sidebar_state="expanded" 
)
API_URL = "http://127.0.0.1:8000/api"

# 2. CSS 样式 (Tab 修复)
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} 
    .block-container { padding: 0.5rem 1rem !important; }
    iframe { display: block; border: none; margin: 0; padding: 0; }
    
    /* Tabs 样式 */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: #0e1117; 
        color: #FFFFFF !important; 
        font-size: 16px; 
        font-weight: 500;
        opacity: 0.8;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #1a1a2b; 
        color: #FFFFFF !important; 
        border-bottom: 3px solid #00BFFF; 
        font-weight: bold;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- 进程管理 -----------------
if 'sim_pid' not in st.session_state: st.session_state['sim_pid'] = None
if 'cam_pid' not in st.session_state: st.session_state['cam_pid'] = None

def kill_all_existing(script_name):
    try: os.system(f"pkill -f {script_name}")
    except: pass

def start_p(script_name, state_key):
    kill_all_existing(script_name); time.sleep(0.2)
    try:
        p = subprocess.Popen([sys.executable, script_name])
        st.session_state[state_key] = p.pid
        return p
    except: return None

def stop_p(script_name, key):
    kill_all_existing(script_name); st.session_state[key] = None

# 初始化逻辑：自动启动模拟器
if st.session_state['cam_pid'] is None and st.session_state['sim_pid'] is None:
    kill_all_existing("simulator.py"); start_p("simulator.py", "sim_pid")

# ----------------- 3D 渲染函数 -----------------
def render_3d_channel(depth, width=5, length=50):
    X = np.linspace(0, length, 30)
    Y = np.linspace(-width / 2, width / 2, 10)
    X, Y = np.meshgrid(X, Y)
    Z_bed = -0.005 * X 
    Z_water = np.full_like(Z_bed, Z_bed.max() + depth) 
    Z_water[Z_water > Z_bed.max() + 3] = Z_bed.max() + 3
    
    fig = go.Figure(
        data=[
            go.Surface(x=X, y=Y, z=Z_bed, colorscale=[[0, 'rgb(50, 50, 50)'], [1, 'rgb(100, 80, 50)']], name='Channel Bed', showscale=False, opacity=1.0),
            go.Surface(x=X, y=Y, z=Z_water, colorscale=[[0, 'rgb(0, 100, 255)'], [1, 'rgb(100, 200, 255)']], name='Water Surface', showscale=False, opacity=0.7, hoverinfo='none')
        ]
    )
    fig.update_layout(
        title=f'3D 渠道场景 (水位: {depth:.2f}m)',
        margin=dict(l=0, r=0, b=0, t=30),
        scene=dict(xaxis_title='长度 (m)', yaxis_title='宽度 (m)', zaxis_title='高程 (m)', aspectmode='data'),
        height=400, plot_bgcolor='#0e1117', paper_bgcolor='#0e1117', font=dict(color='white')
    )
    return fig

# ----------------- 侧边栏 (登录与控制) -----------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/dam.png", width=70)
    st.title("明渠非均匀流流量监测系统")
    st.markdown("### 📡 数据源状态")
    
    if 'auth' not in st.session_state: st.session_state['auth'] = False
    
    if st.session_state['cam_pid']: st.success("📷 摄像头在线")
    elif st.session_state['sim_pid']: st.info("💻 模拟器运行中")
    else: st.warning("⚠️ 无数据源")

    st.markdown("---")
    
    if not st.session_state['auth']:
        st.markdown("### 🔒 管理员登录")
        user = st.text_input("账号", value="admin", key="side_user")
        pwd = st.text_input("密码", type="password", key="side_pwd")
        if st.button("登录", key="side_login"):
            if user == "admin" and pwd == "123456": st.session_state['auth'] = True; st.rerun()
            else: st.error("密码错误")
    else:
        st.success("👤 管理员已认证")
        if st.button("📥 导出 CSV"):
            try:
                resp = requests.get(f"{API_URL}/export")
                if resp.status_code == 200: st.download_button("📄 点击下载", resp.content, f"Report_{time.strftime('%H%M')}.csv", "text/csv")
            except: st.error("导出失败")
        if st.button("🚪 退出"): st.session_state['auth'] = False; st.rerun()


# ----------------- 主页面 (三 Tabs 集成) -----------------
st.title("") 
tab1, tab2, tab3 = st.tabs(["🚀 实时监控", "📊 历史数据分析", "🧠 管理决策中心"])

# =========================================================
# === Tab 1: 实时监控 (Dashboard) ===
# =========================================================
with tab1:
    # 3D 渲染 (Python 端)
    latest_depth = 2.0 
    try:
        res = requests.get(f"{API_URL}/realtime").json()
        latest_depth = res.get('depth', 2.0)
    except:
        pass
        
    st.subheader("🌐 3D 渠道数字孪生")
    fig_3d = render_3d_channel(latest_depth)
    st.plotly_chart(fig_3d, use_container_width=True)


    # 顶部控制栏 (摄像头控制)
    col_ctrl, col_ph = st.columns([1, 4])
    with col_ctrl:
        st.caption("视觉传感器控制")
        is_cam = (st.session_state['cam_pid'] is not None)
        toggle = st.toggle("启动 AI 识别", value=is_cam, key="cam_toggle")
        
        if toggle and not is_cam:
            stop_p("simulator.py", 'sim_pid'); proc = start_p("vision_sensor.py", "cam_pid")
            with st.spinner("正在启动摄像头..."): time.sleep(2.0)
            if proc is not None and proc.poll() is None: st.toast("摄像头启动成功", icon="📷"); st.rerun()
            else:
                st.error("⚠️ 启动失败：未检测到设备")
                st.session_state['cam_pid'] = None
                st.session_state['cam_toggle'] = False 
                start_p("simulator.py", "sim_pid"); time.sleep(1); st.rerun()
        elif not toggle and is_cam: 
            stop_p("vision_sensor.py", 'cam_pid')
            st.toast("摄像头已关闭", icon="🛑")
            start_p("simulator.py", "sim_pid"); time.sleep(0.5); st.rerun()

    cam_text = "🟢 真实影像 (Live)" if st.session_state['cam_pid'] else "🔵 模拟仿真 (Sim)"
    cam_color = "#00fa9a" if st.session_state['cam_pid'] else "#00BFFF"

    # --- HTML/JS 嵌入 (包含 KPI, 2D, Logs) ---
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: 'Microsoft YaHei', sans-serif; background-color: #0e1117; color: white; margin: 0; padding: 5px; overflow: hidden; }}
            .grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-bottom: 10px; }}
            .card {{ background: #262730; padding: 8px; border-radius: 6px; border-left: 3px solid #00BFFF; }}
            .card-label {{ font-size: 11px; color: #aaa; }}
            .card-value {{ font-size: 18px; font-weight: bold; }}
            .card-unit {{ font-size: 10px; color: #666; margin-left: 2px; }}
            .main-container {{ display: flex; gap: 10px; height: 280px; margin-bottom: 10px; }}
            .box {{ flex: 1; background: #262730; border-radius: 8px; padding: 10px; position: relative; display: flex; flex-direction: column; }}
            .box-title {{ font-size: 13px; font-weight: bold; color: #ddd; margin-bottom: 5px; border-bottom: 1px solid #444; padding-bottom: 5px; }}
            .tank-wrap {{ flex: 1; width: 80%; margin: 5px auto; border: 3px solid #555; border-top: none; position: relative; background: #111; border-radius: 0 0 6px 6px; }}
            .water {{ position: absolute; bottom: 0; left: 0; width: 100%; background: linear-gradient(180deg, #00BFFF 0%, #1E90FF 100%); transition: height 1s; opacity: 0.9; }}
            .water-text {{ position: absolute; width: 100%; text-align: center; color: #00BFFF; font-weight: bold; font-size: 16px; transition: bottom 1s; }}
            .video-box {{ flex: 1; background: #000; border-radius: 4px; position: relative; overflow: hidden; background-image: radial-gradient(#222 1px, transparent 1px); background-size: 15px 15px; display: flex; align-items: center; justify-content: center; flex-direction: column; }}
            .ai-rect {{ position: absolute; border: 2px solid #00fa9a; color: #00fa9a; font-size: 12px; padding: 2px; display: none; }}
            .cam-icon {{ font-size: 24px; margin-bottom: 10px; }}
            #chart-main {{ flex: 1; width: 100%; }}
            .log-container {{ height: 200px; background: #262730; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; }}
            .log-header {{ display: flex; padding-bottom: 5px; border-bottom: 1px solid #555; color: #aaa; font-size: 12px; font-weight: bold; }}
            .log-row {{ display: flex; padding: 6px 0; border-bottom: 1px solid #333; font-size: 12px; color: #eee; transition: background 0.2s; }}
            .col-time {{ flex: 1; }} .col-event {{ flex: 2; }} .col-val {{ flex: 1; text-align: center; }} .col-status {{ flex: 1; text-align: right; }}
            #log-list {{ overflow-y: auto; flex: 1; scrollbar-width: thin; }}
            .badge-ok {{ background: #006400; color: #00fa9a; padding: 1px 6px; border-radius: 3px; font-size: 10px; }}
            .badge-warn {{ background: #8b0000; color: #ff6b6b; padding: 1px 6px; border-radius: 3px; font-size: 10px; }}
        </style>
    </head>
    <body>
        <div class="grid">
            <div class="card"><div class="card-label">水深 (h)</div><div><span id="d-depth" class="card-value">---</span><span class="card-unit">m</span></div></div>
            <div class="card"><div class="card-label">流量 (Q)</div><div><span id="d-flow" class="card-value">---</span><span class="card-unit">m³/s</span></div></div>
            <div class="card"><div class="card-label">流速 (v)</div><div><span id="d-vel" class="card-value">---</span><span class="card-unit">m/s</span></div></div>
            <div class="card" id="card-fr"><div class="card-label">Fr数 / 流态</div><div class="card-value" style="font-size: 14px;" id="d-fr">---</div></div>
            <div class="card" style="border-left-color: #FFA500;"><div class="card-label">含沙量</div><div><span id="d-sed" class="card-value">---</span><span class="card-unit">kg/m³</span></div></div>
            <div class="card" style="border-left-color: #FF69B4;"><div class="card-label">AI 漂浮物</div><div><span id="d-float" class="card-value">---</span><span class="card-unit">个</span></div></div>
        </div>
        <div class="main-container">
            <div class="box"><div class="box-title">📊 2D 断面孪生</div><div class="tank-wrap"><div class="water" id="water-bar" style="height: 0%;"></div><div class="water-text" id="water-label" style="bottom: 0%;">0.00 m</div></div></div>
            <div class="box"><div class="box-title">🎥 视觉 AI 识别</div><div class="video-box"><div id="ai-box" class="ai-rect">Target</div><div class="cam-icon">📷</div><div style="font-size:12px; color:{cam_color};">{cam_text}</div></div></div>
            <div class="box" style="flex: 1.2;"><div class="box-title">📈 监测趋势</div><div id="chart-main"></div></div>
        </div>
        <div class="log-container">
            <div class="box-title">📝 实时日志 (Real-time Logs)</div>
            <div class="log-header"><div class="col-time">时间戳</div><div class="col-event">事件描述</div><div class="col-val">漂浮物</div><div class="col-status">状态</div></div>
            <div id="log-list"><div style="padding:10px; text-align:center; color:#666;">等待数据...</div></div>
        </div>
        <script>
            var myChart = echarts.init(document.getElementById('chart-main'));
            var option = {{
                backgroundColor: 'transparent', tooltip: {{ trigger: 'axis' }}, legend: {{ data: ['水深', '含沙量'], textStyle: {{ color: '#aaa', fontSize: 10 }}, top: 0 }},
                grid: {{ left: 5, right: 15, bottom: 5, top: 20, containLabel: true }},
                xAxis: {{ type: 'category', boundaryGap: false, data: [], axisLabel: {{ color: '#777', fontSize: 10 }}, axisTick:{{show:false}}, axisLine:{{lineStyle:{{color:'#444'}}}} }},
                yAxis: [{{ type: 'value', splitLine: {{ show: false }}, axisLabel: {{ color: '#777', fontSize:10 }} }}, {{ type: 'value', splitLine: {{ show: false }}, axisLabel: {{ color: '#777', fontSize:10 }} }}],
                series: [{{ name: '水深', type: 'line', smooth: true, showSymbol: false, data: [], itemStyle: {{ color: '#00BFFF' }}, areaStyle: {{ opacity: 0.2 }} }}, {{ name: '含沙量', type: 'line', smooth: true, showSymbol: false, yAxisIndex: 1, data: [], itemStyle: {{ color: '#FFA500' }} }}]
            }};
            myChart.setOption(option);
            async function refreshData() {{
                try {{
                    let res = await fetch("{API_URL}/realtime");
                    let data = await res.json();
                    
                    // --- 数据等待逻辑 ---
                    if(!data.depth) {{
                        document.getElementById('d-depth').innerText = "---";
                        document.getElementById('d-flow').innerText = "---";
                        document.getElementById('d-vel').innerText = "---";
                        document.getElementById('d-fr').innerText = "---";
                        document.getElementById('d-sed').innerText = "---";
                        document.getElementById('d-float').innerText = "---";
                        document.getElementById('log-list').innerHTML = '<div style="padding:10px; text-align:center; color:#666;">等待模拟器数据接入...</div>';
                        return;
                    }}
                    
                    document.getElementById('d-depth').innerText = data.depth; document.getElementById('d-flow').innerText = data.flow_rate; document.getElementById('d-vel').innerText = data.velocity_avg; document.getElementById('d-sed').innerText = data.sediment; document.getElementById('d-float').innerText = data.floating_count;
                    let frInfo = data.fr_number + " | " + data.regime.replace("Subcritical","缓").replace("Supercritical","急").replace("Critical", "临界");
                    document.getElementById('d-fr').innerText = frInfo;
                    let aiBox = document.getElementById('ai-box');
                    if (data.floating_count > 0) {{ aiBox.style.display = 'block'; aiBox.style.top = (20 + Math.random()*40) + "%"; aiBox.style.left = (20 + Math.random()*40) + "%"; aiBox.innerText = "Obj: " + data.floating_count; }} else {{ aiBox.style.display = 'none'; }}
                    let frCard = document.getElementById('card-fr'); frCard.style.borderLeftColor = (data.fr_number > 1) ? "#ff4b4b" : "#00fa9a"; document.getElementById('d-fr').style.color = (data.fr_number > 1) ? "#ff4b4b" : "#00fa9a";
                    let pct = (data.depth / 4.0) * 100; if(pct>100) pct=100; document.getElementById('water-bar').style.height = pct + "%"; document.getElementById('water-label').style.bottom = pct + "%"; document.getElementById('water-label').innerText = data.depth + " m";
                    let resHist = await fetch("{API_URL}/history?limit=30"); 
                    let hist_res = await resHist.json(); 
                    
                    let xData=[], yDepth=[], ySed=[]; 
                    let chartData = [...hist_res].reverse();
                    
                    if (chartData.length > 0) {{
                        chartData.forEach(item => {{ 
                            let d = new Date(item.timestamp); 
                            xData.push(d.getHours()+":"+d.getMinutes()+":"+d.getSeconds()); 
                            yDepth.push(item.depth || 0); 
                            ySed.push(item.sediment || 0); 
                        }});
                    }}

                    myChart.setOption({{ xAxis: {{ data: xData }}, series: [{{ data: yDepth }}, {{ data: ySed }}] }});
                    
                    let listHtml = ""; hist_res.slice(0, 6).forEach(item => {{
                        let d = new Date(item.timestamp); let timeStr = d.toLocaleTimeString(); let count = item.floating_count || 0;
                        let statusHtml = '<span class="badge-ok">正常</span>'; let eventText = "常规监测";
                        if (count > 0) {{ statusHtml = '<span class="badge-warn">异常</span>'; eventText = "⚠️ 发现漂浮物"; }} 
                        else if (item.sediment > 1.0) {{ statusHtml = '<span class="badge-warn">淤积风险</span>'; eventText = "泥沙含量过高"; }}
                        listHtml += `<div class="log-row"><div class="col-time">${{timeStr}}</div><div class="col-event">${{eventText}}</div><div class="col-val">${{count}} 个</div><div class="col-status">${{statusHtml}}</div></div>`;
                    }});
                    document.getElementById('log-list').innerHTML = listHtml;
                }} catch(e) {{ }}
            }}
            setInterval(refreshData, 1000); window.onresize = function() {{ myChart.resize(); }};
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=600)

# =========================================================
# === Tab 2: 历史数据分析 ===
# =========================================================
with tab2:
    st.header("📈 历史数据全集")
    try:
        hist_resp = requests.get(f"{API_URL}/history?limit=100")
        if hist_resp.status_code == 200:
            df = pd.DataFrame(hist_resp.json())
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                st.dataframe(df.rename(columns={"timestamp": "时间", "depth": "水深", "floating_count": "漂浮物", "sediment": "含沙量"}), use_container_width=True)
            else: st.info("无数据")
    except: st.error("无法加载数据")

# =========================================================
# === Tab 3: 管理决策中心 ===
# =========================================================
with tab3:
    st.title("🧠 管理决策中心")

    # 1. 应急控制模块
    if not st.session_state['auth']:
        st.error("❌ 无权限访问。请先在左侧栏登录！")
    else:
        st.subheader("1. 应急调控闭环")
        col_ctrl, col_log = st.columns([1, 2])

        with col_ctrl:
            st.info("🎮 远程闸门控制")
            val = st.slider("闸门开度", 0, 100, 50, key="gate_slider")
            reason = st.text_input("操作原因", "日常调度", key="control_reason")
            
            if st.button("🔴 下发指令", type="primary"):
                try:
                    requests.post(f"{API_URL}/control", json={"action":f"开度调至 {val}%", "operator":"Admin", "reason":reason})
                    st.success("✅ 指令下发成功")
                except: st.error("❌ 网络通讯故障")

        with col_log:
            st.warning("📝 最近操作日志")
            try:
                log_res = requests.get(f"{API_URL}/control/logs")
                logs = log_res.json()
                if logs: 
                    df_log = pd.DataFrame(logs)
                    st.dataframe(df_log, use_container_width=True, height=200, hide_index=True)
                else: st.info("暂无操作记录")
            except: st.write("日志服务离线")

        st.markdown("---")
        
        # 2. 深度分析图表 (核心修复区)
        st.subheader("2. 深度数据挖掘")
        
        # --- 数据加载与模拟逻辑 ---
        try:
            data_list = requests.get(f"{API_URL}/history?limit=300").json()
            df_analysis = pd.DataFrame(data_list)
            
            # --- 关键修复：强制检查并注入缺失列 ---
            df_analysis.columns = [col.lower() for col in df_analysis.columns] 

            REQUIRED_COLS = ['sediment', 'floating_count', 'depth', 'velocity_surf', 'regime', 'flow_rate', 'fr_number']
            for col in REQUIRED_COLS:
                if col not in df_analysis.columns:
                    df_analysis[col] = 0.0
            
        except Exception as e:
            df_analysis = pd.DataFrame() 

        # --- 模拟数据填充 (如果数据不足) ---
        if df_analysis.empty or len(df_analysis) < 10:
            st.info("ℹ️ 实时数据不足，使用模拟样本进行演示分析。")
            mock_data = {
                'regime': ['缓流', '缓流', '急流', '缓流', '临界流'] * 2,
                'velocity_surf': [0.8, 1.2, 2.5, 1.5, 1.0] * 2,
                'sediment': [0.1, 0.3, 1.8, 0.4, 0.6] * 2,
                'depth': [2.0, 1.8, 0.9, 1.5, 1.2] * 2,
                'fr_number': [0.4, 0.6, 1.5, 0.8, 1.0] * 2,
                'floating_count': [0] * 10,
                'flow_rate': [20] * 10
            }
            df_analysis = pd.DataFrame(mock_data)

        # --- 图表渲染 ---
        tab_a, tab_b = st.tabs(["流态分布", "流速-泥沙耦合"])
        
        with tab_a:
            fig_pie = px.pie(df_analysis, names='regime', title='渠道流态占比', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with tab_b:
            fig2 = px.scatter(df_analysis, x="velocity_surf", y="sediment", color="regime", size="depth", title="流速与含沙量相关性分析")
            st.plotly_chart(fig2, use_container_width=True)