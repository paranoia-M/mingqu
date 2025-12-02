# dashboard_final.py (V24.4 - UI 布局防遮挡修复版)
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

# ==============================================================================
# 1. 全局配置 & CSS (修复遮挡问题)
# ==============================================================================
st.set_page_config(
    page_title="智能监测系统", 
    layout="wide", 
    page_icon="🌊",
    initial_sidebar_state="expanded" 
)
API_URL = "http://127.0.0.1:8000/api"

# 强力 CSS 补丁
st.markdown("""
<style>
    /* 1. 全局深色背景 */
    .stApp {
        background-color: #0e1117;
    }
    
    /* 2. 隐藏 Streamlit 默认菜单和页脚 */
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    
    /* 3. 【核心修复】调整内容容器边距 */
    /* 之前设置太小导致被顶部遮挡，现在增加 padding-top 到 3.5rem */
    .block-container { 
        padding-top: 3.5rem !important; 
        padding-bottom: 1rem !important; 
        padding-left: 1rem !important; 
        padding-right: 1rem !important; 
    }
    
    iframe { display: block; border: none; margin: 0; padding: 0; }
    
    /* 4. 侧边栏背景 */
    [data-testid="stSidebar"] { background-color: #1a1a1a; }
    
    /* 5. Tabs (标签页) 样式优化 */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 20px; 
        background-color: #0e1117; 
        padding-bottom: 5px;
        margin-top: 10px; /* 额外增加一点顶部间距 */
    }
    
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: transparent; 
        color: #FFFFFF !important; 
        font-size: 18px !important; 
        font-weight: 600;
        border: none;
        opacity: 0.7; 
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #00BFFF !important;
        opacity: 1.0;
    }

    .stTabs [aria-selected="true"] { 
        background-color: #1f2937; 
        color: #00fa9a !important; 
        border-radius: 5px 5px 0 0;
        border-bottom: 3px solid #00fa9a; 
        opacity: 1.0;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. 核心逻辑：进程管理
# ==============================================================================
if 'sim_pid' not in st.session_state: st.session_state['sim_pid'] = None
if 'cam_pid' not in st.session_state: st.session_state['cam_pid'] = None
if 'auth' not in st.session_state: st.session_state['auth'] = False

def kill_all_existing(script_name):
    try:
        if os.name != 'nt': os.system(f"pkill -f {script_name}")
    except: pass

def start_p(script_name, state_key):
    kill_all_existing(script_name); time.sleep(0.2)
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.Popen([sys.executable, script_name], startupinfo=startupinfo)
        st.session_state[state_key] = p.pid
        return p
    except: return None

def stop_p(script_name, key):
    kill_all_existing(script_name)
    if st.session_state[key]:
        try: os.kill(st.session_state[key], signal.SIGTERM)
        except: pass
        st.session_state[key] = None

if st.session_state['cam_pid'] is None and st.session_state['sim_pid'] is None:
    kill_all_existing("simulator.py"); start_p("simulator.py", "sim_pid")

# ==============================================================================
# 3. 3D 渲染
# ==============================================================================
def render_3d_channel(depth, width=5, length=50):
    X = np.linspace(0, length, 30)
    Y = np.linspace(-width / 2, width / 2, 10)
    X, Y = np.meshgrid(X, Y)
    Z_bed = -0.005 * X 
    
    water_level = Z_bed.max() + depth
    Z_water = np.full_like(Z_bed, water_level) 
    max_display_h = Z_bed.max() + 4.0
    Z_water[Z_water > max_display_h] = max_display_h
    
    fig = go.Figure(data=[
        go.Surface(x=X, y=Y, z=Z_bed, colorscale=[[0, '#3d3d3d'], [1, '#5c4d3c']], name='河床', showscale=False, opacity=1.0),
        go.Surface(x=X, y=Y, z=Z_water, colorscale=[[0, 'rgba(0, 191, 255, 0.6)'], [1, 'rgba(30, 144, 255, 0.8)']], name='水面', showscale=False, opacity=0.8)
    ])
    
    fig.update_layout(
        title=dict(text=f'🌊 3D 数字孪生渠道 (实时水位: {depth:.2f}m)', font=dict(color='white', size=20)), 
        margin=dict(l=10, r=10, b=10, t=40),
        scene=dict(
            xaxis=dict(title='', showticklabels=False, backgroundcolor='#0e1117'),
            yaxis=dict(title='', showticklabels=False, backgroundcolor='#0e1117'),
            zaxis=dict(title='高程(m)', backgroundcolor='#0e1117', titlefont=dict(color='white'), tickfont=dict(color='gray')),
            aspectmode='manual', aspectratio=dict(x=3, y=1, z=0.5),
            camera=dict(eye=dict(x=1.5, y=-1.5, z=0.8))
        ),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    return fig

# ==============================================================================
# 4. 侧边栏
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/dam.png", width=70)
    st.title("监测控制台")
    st.markdown("### 📡 源状态")
    if st.session_state['cam_pid']: st.success("📷 摄像头在线")
    elif st.session_state['sim_pid']: st.info("💻 模拟器运行中")
    else: st.warning("⚠️ 无数据源")
    st.markdown("---")
    if not st.session_state['auth']:
        st.markdown("#### 🔒 管理员登录")
        with st.form("login_form"):
            user = st.text_input("账号", value="admin")
            pwd = st.text_input("密码", type="password")
            if st.form_submit_button("登录"):
                if user == "admin" and pwd == "123456": st.session_state['auth'] = True; st.rerun()
                else: st.error("密码错误")
    else:
        st.success("👤 管理员已认证")
        if st.button("📥 导出报表"):
            try:
                resp = requests.get(f"{API_URL}/export")
                if resp.status_code == 200: st.download_button("📄 点击下载", resp.content, f"Report_{time.strftime('%H%M')}.csv", "text/csv")
            except: st.error("导出失败")
        if st.button("🚪 退出系统"): st.session_state['auth'] = False; st.rerun()

# ==============================================================================
# 5. 主页面内容
# ==============================================================================
tab1, tab2, tab3 = st.tabs(["🚀 实时监控驾驶舱", "📊 历史数据分析", "🧠 管理决策中心"])

# --- Tab 1 ---
with tab1:
    c_3d, c_cam = st.columns([3, 1])
    with c_3d:
        try:
            res = requests.get(f"{API_URL}/realtime", timeout=0.5).json()
            d_val = res.get('depth', 2.0)
        except: d_val = 2.0
        st.plotly_chart(render_3d_channel(d_val), use_container_width=True)

    with c_cam:
        st.markdown("##### 🕹️ 视觉传感器")
        st.write("")
        is_cam = (st.session_state['cam_pid'] is not None)
        toggle = st.toggle("启动 AI 识别", value=is_cam, key="cam_toggle")
        
        if toggle and not is_cam:
            stop_p("simulator.py", 'sim_pid'); proc = start_p("vision_sensor.py", "cam_pid")
            with st.spinner("启动摄像头..."): time.sleep(2.0)
            if proc and proc.poll() is None: st.toast("摄像头启动成功", icon="📷"); st.rerun()
            else:
                st.error("启动失败：未检测到设备")
                st.session_state['cam_pid'] = None; st.session_state['cam_toggle'] = False
                start_p("simulator.py", "sim_pid"); time.sleep(1); st.rerun()
        elif not toggle and is_cam:
            stop_p("vision_sensor.py", 'cam_pid'); st.toast("摄像头关闭", icon="🛑")
            start_p("simulator.py", "sim_pid"); time.sleep(0.5); st.rerun()

    cam_text = "🟢 真实影像 (Live)" if st.session_state['cam_pid'] else "🔵 模拟仿真 (Sim)"
    cam_color = "#00fa9a" if st.session_state['cam_pid'] else "#00BFFF"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: 'Microsoft YaHei', sans-serif; background-color: #0e1117; color: white; margin: 0; padding: 0; overflow: hidden; }}
            .grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-bottom: 10px; }}
            .card {{ background: #262730; padding: 10px; border-radius: 6px; border-left: 3px solid #00BFFF; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
            .card-label {{ font-size: 11px; color: #aaa; margin-bottom: 4px; }}
            .card-value {{ font-size: 20px; font-weight: bold; letter-spacing: 0.5px; }}
            .card-unit {{ font-size: 10px; color: #666; margin-left: 2px; }}
            .main-container {{ display: flex; gap: 10px; height: 260px; margin-bottom: 10px; }}
            .box {{ flex: 1; background: #262730; border-radius: 8px; padding: 10px; position: relative; display: flex; flex-direction: column; }}
            .box-title {{ font-size: 13px; font-weight: bold; color: #ddd; margin-bottom: 5px; border-bottom: 1px solid #444; padding-bottom: 5px; }}
            .tank-wrap {{ flex: 1; width: 80%; margin: 5px auto; border: 3px solid #555; border-top: none; position: relative; background: #111; border-radius: 0 0 6px 6px; }}
            .water {{ position: absolute; bottom: 0; left: 0; width: 100%; background: linear-gradient(180deg, #00BFFF 0%, #1E90FF 100%); transition: height 1s; opacity: 0.9; }}
            .water-text {{ position: absolute; width: 100%; text-align: center; color: #00BFFF; font-weight: bold; font-size: 16px; transition: bottom 1s; }}
            .video-box {{ flex: 1; background: #000; border-radius: 4px; position: relative; overflow: hidden; background-image: radial-gradient(#222 1px, transparent 1px); background-size: 15px 15px; display: flex; align-items: center; justify-content: center; flex-direction: column; }}
            .ai-rect {{ position: absolute; border: 2px solid #00fa9a; color: #00fa9a; font-size: 12px; padding: 2px; display: none; background: rgba(0, 250, 154, 0.1); }}
            .cam-icon {{ font-size: 28px; margin-bottom: 10px; opacity: 0.7; }}
            #chart-main {{ flex: 1; width: 100%; }}
            .log-container {{ height: 180px; background: #262730; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; }}
            .log-header {{ display: flex; padding-bottom: 5px; border-bottom: 1px solid #555; color: #aaa; font-size: 12px; font-weight: bold; }}
            .log-row {{ display: flex; padding: 6px 0; border-bottom: 1px solid #333; font-size: 12px; color: #eee; transition: background 0.2s; }}
            .col-time {{ flex: 1; }} .col-event {{ flex: 2; }} .col-val {{ flex: 1; text-align: center; }} .col-status {{ flex: 1; text-align: right; }}
            #log-list {{ overflow-y: auto; flex: 1; scrollbar-width: thin; }}
            .badge-ok {{ background: #004d00; color: #00fa9a; padding: 2px 6px; border-radius: 3px; font-size: 10px; }}
            .badge-warn {{ background: #4d0000; color: #ff6b6b; padding: 2px 6px; border-radius: 3px; font-size: 10px; }}
        </style>
    </head>
    <body>
        <div class="grid">
            <div class="card"><div class="card-label">实时水深 (h)</div><div><span id="d-depth" class="card-value">---</span><span class="card-unit">m</span></div></div>
            <div class="card"><div class="card-label">断面流量 (Q)</div><div><span id="d-flow" class="card-value">---</span><span class="card-unit">m³/s</span></div></div>
            <div class="card"><div class="card-label">平均流速 (v)</div><div><span id="d-vel" class="card-value">---</span><span class="card-unit">m/s</span></div></div>
            <div class="card" id="card-fr"><div class="card-label">Fr数 / 流态</div><div class="card-value" style="font-size: 14px;" id="d-fr">---</div></div>
            <div class="card" style="border-left-color: #FFA500;"><div class="card-label">含沙量</div><div><span id="d-sed" class="card-value">---</span><span class="card-unit">kg/m³</span></div></div>
            <div class="card" style="border-left-color: #FF69B4;"><div class="card-label">AI 漂浮物</div><div><span id="d-float" class="card-value">---</span><span class="card-unit">个</span></div></div>
        </div>
        <div class="main-container">
            <div class="box"><div class="box-title">📊 2D 断面孪生</div><div class="tank-wrap"><div class="water" id="water-bar" style="height: 0%;"></div><div class="water-text" id="water-label" style="bottom: 0%;">0.00 m</div></div></div>
            <div class="box"><div class="box-title">🎥 视觉 AI 识别</div><div class="video-box"><div id="ai-box" class="ai-rect">Target</div><div class="cam-icon">📷</div><div style="font-size:12px; color:{cam_color};">{cam_text}</div></div></div>
            <div class="box" style="flex: 1.5;"><div class="box-title">📈 监测趋势</div><div id="chart-main"></div></div>
        </div>
        <div class="log-container">
            <div class="box-title">📝 实时运行日志</div>
            <div class="log-header"><div class="col-time">时间戳</div><div class="col-event">事件描述</div><div class="col-val">参数值</div><div class="col-status">状态</div></div>
            <div id="log-list"><div style="padding:10px; text-align:center; color:#666;">系统初始化中...</div></div>
        </div>
        <script>
            var myChart = echarts.init(document.getElementById('chart-main'));
            var option = {{
                backgroundColor: 'transparent', tooltip: {{ trigger: 'axis' }}, legend: {{ data: ['水深', '含沙量'], textStyle: {{ color: '#aaa', fontSize: 10 }}, top: 0 }},
                grid: {{ left: 10, right: 10, bottom: 5, top: 25, containLabel: true }},
                xAxis: {{ type: 'category', boundaryGap: false, data: [], axisLabel: {{ color: '#777', fontSize: 10 }}, axisTick:{{show:false}}, axisLine:{{lineStyle:{{color:'#444'}}}} }},
                yAxis: [{{ type: 'value', splitLine: {{ show: false }}, axisLabel: {{ color: '#777', fontSize:10 }} }}, {{ type: 'value', splitLine: {{ show: false }}, axisLabel: {{ color: '#777', fontSize:10 }} }}],
                series: [{{ name: '水深', type: 'line', smooth: true, showSymbol: false, data: [], itemStyle: {{ color: '#00BFFF' }}, areaStyle: {{ opacity: 0.2 }} }}, {{ name: '含沙量', type: 'line', smooth: true, showSymbol: false, yAxisIndex: 1, data: [], itemStyle: {{ color: '#FFA500' }} }}]
            }};
            myChart.setOption(option);
            async function refreshData() {{
                try {{
                    let res = await fetch("{API_URL}/realtime");
                    let data = await res.json();
                    
                    if(!data.depth) {{
                        document.getElementById('log-list').innerHTML = '<div style="padding:10px; text-align:center; color:#666;">等待模拟器数据接入...</div>';
                        return;
                    }}
                    
                    document.getElementById('d-depth').innerText = data.depth; document.getElementById('d-flow').innerText = data.flow_rate; document.getElementById('d-vel').innerText = data.velocity_avg; document.getElementById('d-sed').innerText = data.sediment; document.getElementById('d-float').innerText = data.floating_count;
                    let frInfo = data.fr_number + " | " + data.regime.replace("Subcritical","缓").replace("Supercritical","急").replace("Critical", "临界");
                    document.getElementById('d-fr').innerText = frInfo;
                    
                    let aiBox = document.getElementById('ai-box');
                    if (data.floating_count > 0) {{ 
                        aiBox.style.display = 'block'; 
                        let randX = 20 + Math.sin(new Date().getTime()/500)*10;
                        let randY = 30 + Math.cos(new Date().getTime()/500)*10;
                        aiBox.style.top = randY + "%"; aiBox.style.left = randX + "%"; 
                        aiBox.innerText = "Obj: " + data.floating_count; 
                    }} else {{ aiBox.style.display = 'none'; }}
                    
                    let frCard = document.getElementById('card-fr'); frCard.style.borderLeftColor = (data.fr_number > 1) ? "#ff4b4b" : "#00fa9a"; document.getElementById('d-fr').style.color = (data.fr_number > 1) ? "#ff4b4b" : "#00fa9a";
                    let pct = (data.depth / 4.0) * 100; if(pct>100) pct=100; document.getElementById('water-bar').style.height = pct + "%"; document.getElementById('water-label').style.bottom = pct + "%"; document.getElementById('water-label').innerText = data.depth + " m";
                    
                    let resHist = await fetch("{API_URL}/history?limit=30"); 
                    let hist_res = await resHist.json(); 
                    let xData=[], yDepth=[], ySed=[]; 
                    let chartData = [...hist_res].reverse();
                    if (chartData.length > 0) {{
                        chartData.forEach(item => {{ 
                            let d = new Date(item.timestamp); xData.push(d.getHours()+":"+d.getMinutes()+":"+d.getSeconds()); yDepth.push(item.depth || 0); ySed.push(item.sediment || 0); 
                        }});
                    }}
                    myChart.setOption({{ xAxis: {{ data: xData }}, series: [{{ data: yDepth }}, {{ data: ySed }}] }});
                    
                    let listHtml = ""; hist_res.slice(0, 6).forEach(item => {{
                        let d = new Date(item.timestamp); let timeStr = d.toLocaleTimeString(); let count = item.floating_count || 0;
                        let statusHtml = '<span class="badge-ok">正常</span>'; let eventText = "常规监测";
                        let valText = count + " 个";
                        if (count > 0) {{ statusHtml = '<span class="badge-warn">异常</span>'; eventText = "⚠️ 发现漂浮物"; }} 
                        else if (item.sediment > 1.0) {{ statusHtml = '<span class="badge-warn">淤积风险</span>'; eventText = "泥沙含量过高"; valText=item.sediment+" kg/m³"; }}
                        listHtml += `<div class="log-row"><div class="col-time">${{timeStr}}</div><div class="col-event">${{eventText}}</div><div class="col-val">${{valText}}</div><div class="col-status">${{statusHtml}}</div></div>`;
                    }});
                    document.getElementById('log-list').innerHTML = listHtml;
                }} catch(e) {{ }}
            }}
            setInterval(refreshData, 1000); window.onresize = function() {{ myChart.resize(); }};
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=750)

# --- Tab 2 ---
with tab2:
    st.subheader("📈 历史数据全集")
    try:
        hist_resp = requests.get(f"{API_URL}/history?limit=100")
        if hist_resp.status_code == 200:
            df = pd.DataFrame(hist_resp.json())
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                st.dataframe(df.rename(columns={"timestamp": "时间", "depth": "水深", "floating_count": "漂浮物", "sediment": "含沙量"}), use_container_width=True)
            else: st.info("无数据")
    except: st.error("无法连接数据库")

# --- Tab 3 ---
with tab3:
    st.subheader("🧠 管理决策中心")
    if not st.session_state['auth']:
        st.error("🔒 权限被拒绝。请先在左侧侧边栏登录管理员账号。")
    else:
        st.markdown("#### 1. 应急调控闭环")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.info("🎮 远程闸门控制")
            val = st.slider("闸门开度设定", 0, 100, 50)
            reason = st.text_input("操作备注", "常规调度")
            if st.button("🔴 下发控制指令", type="primary"):
                try:
                    requests.post(f"{API_URL}/control", json={"action":f"开度调至 {val}%", "operator":"Admin", "reason":reason})
                    st.success("✅ 指令下发成功")
                except: st.error("❌ 通讯失败")
        with c2:
            st.warning("📝 操作审计日志")
            try:
                logs = requests.get(f"{API_URL}/control/logs").json()
                if logs: st.dataframe(pd.DataFrame(logs), use_container_width=True, height=200)
                else: st.caption("暂无操作记录")
            except: st.write("日志服务离线")
        st.markdown("---")
        st.markdown("#### 2. 深度数据挖掘")
        try:
            data = requests.get(f"{API_URL}/history?limit=300").json()
            df = pd.DataFrame(data)
            for col in ['sediment', 'velocity_surf', 'regime', 'depth']:
                if col not in df.columns: df[col] = 0
            if not df.empty:
                t1, t2 = st.tabs(["流态分布", "流速-泥沙相关性"])
                with t1:
                    fig = px.pie(df, names='regime', title='运行流态占比', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                    st.plotly_chart(fig, use_container_width=True)
                with t2:
                    fig2 = px.scatter(df, x="velocity_surf", y="sediment", color="regime", size="depth", title="流速与含沙量耦合分析")
                    st.plotly_chart(fig2, use_container_width=True)
            else: st.info("数据不足")
        except: st.error("数据源异常")