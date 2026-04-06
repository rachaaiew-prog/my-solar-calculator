import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse
import pydeck as pdk

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Solar Assistant | วิเคราะห์ระบบจำหน่ายไฟฟ้า",
    page_icon="☀️",
    layout="wide"
)

# --- ข้อมูลแพ็กเกจมาตรฐาน PEA Solar ---
pea_packages = [
    {"name": "Micro Solar (1 Phase)", "inverter_size": 3.0, "pv_size": 3.78, "price": 145000},
    {"name": "Home Solar (1 Phase)", "inverter_size": 5.0, "pv_size": 5.67, "price": 225000},
    {"name": "Premium Solar (3 Phase)", "inverter_size": 5.0, "pv_size": 5.67, "price": 235000},
    {"name": "Business Solar (3 Phase)", "inverter_size": 10.0, "pv_size": 11.34, "price": 390000},
    {"name": "Max Solar (3 Phase)", "inverter_size": 20.0, "pv_size": 22.68, "price": 750000}
]

# --- ฟังก์ชันจำลองข้อมูลสำหรับ Heat Map (เน้นหม้อแปลงเฉพาะ) ---
def get_simulated_grid_data():
    # พิกัดตำแหน่งหม้อแปลง (ศูนย์กลาง)
    base_lat, base_lon = 16.7115, 103.7477
    tr_name = "TR 250 (บ้านหนองแวง) 56-02564"
    
    # 1. ข้อมูลผู้ติดตั้งโซล่าเซลล์ (2 ราย)
    solar_data = pd.DataFrame({
        'id': [f'Solar-01 ({tr_name})', f'Solar-02 ({tr_name})'],
        'lat': [base_lat + 0.0012, base_lat - 0.0008],
        'lon': [base_lon + 0.0009, base_lon - 0.0011],
        'capacity_kw': [5, 10],
        'phase_connection': ['Phase A', '3 Phase'],
        'weight': [0.9, 1.0],
        'type': 'Solar PV Installed',
        'color_rgb': [[255, 69, 0, 230]] * 2, 
        'line_color': [[255, 215, 0]] * 2 
    })
    
    # 2. ข้อมูลผู้ขอใช้ไฟติดตั้ง Wall Charger (5 ราย)
    ev_data = pd.DataFrame({
        'id': [f'EV-{i:02d} ({tr_name})' for i in range(1, 6)],
        'lat': [base_lat + 0.002, base_lat + 0.0015, base_lat - 0.001, base_lat - 0.002, base_lat + 0.0005],
        'lon': [base_lon + 0.001, base_lon - 0.0015, base_lon + 0.002, base_lon + 0.0005, base_lon - 0.0025],
        'capacity_kw': [7, 7, 11, 7, 22],
        'phase_connection': ['Phase B', 'Phase C', 'Phase A', 'Phase B', '3 Phase'],
        'weight': [0.7, 0.7, 0.8, 0.7, 1.0],
        'type': 'EV Wall Charger Request',
        'color_rgb': [[57, 255, 20, 230]] * 5,
        'line_color': [[255, 255, 255]] * 5
    })
    
    df = pd.concat([solar_data, ev_data], ignore_index=True)
    df['gmaps_link'] = df.apply(lambda row: f"https://www.google.com/maps?q={row['lat']},{row['lon']}", axis=1)
    return df

# --- Custom CSS เพื่อปรับแต่ง UI ตามรูปภาพ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    
    /* โครงสร้างพื้นฐาน - เปลี่ยนเป็นสีเขียวอมขาว #e8f5e9 */
    html, body, [class*="css"] { 
        font-family: 'Kanit', sans-serif; 
        color: #e8f5e9 !important;
    }
    
    /* พื้นหลังไล่เฉดสีน้ำเงินม่วงเข้ม */
    .stApp { 
        background: linear-gradient(180deg, #1e1b4b 0%, #111827 100%);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2 {
        color: #e8f5e9 !important;
    }

    /* Header Section */
    .app-header {
        background: transparent;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    .header-title {
        font-size: 2.8rem;
        font-weight: 600;
        color: #f0fdf4; /* สีเขียวสว่างนวล */
        margin: 0;
    }
    .header-subtitle {
        font-size: 1.2rem;
        color: rgba(232, 245, 233, 0.75); /* เขียวอมขาวโปร่งแสง */
    }

    /* กล่องข้อมูลแบบ Card (สีเทาเข้มโปร่งแสง) */
    .analysis-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
        backdrop-filter: blur(5px);
    }
    
    .registration-form {
        background: rgba(255, 255, 255, 0.03);
        padding: 35px;
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 25px;
    }

    /* ปรับแต่ง Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 5px;
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        color: rgba(232, 245, 233, 0.5);
        padding: 10px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #312e81 !important; 
        color: #f0fdf4 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }

    /* ปุ่มวิเคราะห์สีส้มทอง */
    .product-btn {
        display: block; width: 100%; text-align: center;
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
        color: #1e1b4b !important; padding: 18px; border-radius: 16px;
        text-decoration: none; font-weight: 600; font-size: 1.1rem;
        margin-top: 20px;
        transition: transform 0.2s;
    }
    .product-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(245, 158, 11, 0.3);
    }
    
    /* ปุ่มส่งข้อมูลสีเขียวพรีเมียม */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #10b981, #059669);
        color: white !important;
        border-radius: 14px;
        border: none;
        padding: 12px 30px;
        font-weight: 500;
        width: 100%;
        margin-top: 10px;
    }
    
    /* ปรับแต่ง Input Fields */
    input, textarea, select {
        background-color: rgba(0, 0, 0, 0.2) !important;
        color: #e8f5e9 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #f0fdf4 !important;
        font-size: 2rem !important;
        font-weight: 600;
    }
    [data-testid="stMetricLabel"] {
        color: rgba(232, 245, 233, 0.6) !important;
    }
    
    /* DataFrame/Table */
    .stDataFrame {
        background-color: transparent !important;
    }
    
    /* Divider */
    hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
st.markdown("""
    <div class="app-header">
        <h1 class="header-title">Solar Assistant Pro ☀️</h1>
        <p class="header-subtitle">วิเคราะห์โหลดหม้อแปลงไฟฟ้าจำหน่าย (Single Transformer Analysis)</p>
    </div>
    """, unsafe_allow_html=True)

# --- ข้อมูลสรุปด้านบน (Top Summary Bar) ---
top_col1, top_col2 = st.columns([1, 1])
with top_col1:
    st.markdown("""
        <div class="analysis-card" style="display: flex; align-items: center; gap: 1.5rem; padding: 15px 25px;">
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 12px;">🏠</div>
            <div>
                <small style="color: rgba(232,245,233,0.5)">Micro Solar (1 Phase)</small><br>
                <span style="font-size: 1.2rem; font-weight: 500;">ระบบ 1 เฟส</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

with top_col2:
    st.markdown("""
        <div class="analysis-card" style="display: flex; align-items: center; gap: 1.5rem; padding: 15px 25px;">
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 12px;">⚡</div>
            <div>
                <small style="color: rgba(232,245,233,0.5)">หม้อแปลงเป้าหมาย</small><br>
                <span style="font-size: 1.2rem; font-weight: 500;">TR 250 (บ้านหนองแวง) 56-02564</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["💡 วิเคราะห์การติดตั้งรายบ้าน", "📊 วิเคราะห์โหลดหม้อแปลง (Single Balance)"])

with tab1:
    with st.sidebar:
        st.markdown("### ⚙️ ตั้งค่าพารามิเตอร์")
        unit_price = st.number_input("ค่าไฟฟ้าเฉลี่ย (บาท/หน่วย)", value=4.7, step=0.1)
        phase = st.radio("ระบบไฟฟ้าที่บ้าน", ["1 Phase", "3 Phase"])
        st.divider()
        sun_hours = st.slider("ชั่วโมงแดดจัดเฉลี่ยต่อวัน", 3.0, 6.0, 4.2)
        system_loss = st.slider("System Loss (%)", 5, 30, 15) / 100

    st.markdown("### 📝 รายการเครื่องใช้ไฟฟ้าช่วงกลางวัน")
    device_list = [
        {"item": "แอร์ 9,000 BTU (Inverter)", "watts": 800},
        {"item": "แอร์ 12,000 BTU (Inverter)", "watts": 1100},
        {"item": "แอร์ 18,000 BTU (Inverter)", "watts": 1600},
        {"item": "แอร์ 24,000 BTU (Inverter)", "watts": 2200},
        {"item": "Wall Charger 7 kW (EV)", "watts": 7000},
        {"item": "ปั๊มน้ำ / อุปกรณ์อื่นๆ", "watts": 500},
        {"item": "ตู้เย็น / ระบบไฟส่องสว่าง", "watts": 300},
    ]

    total_daily_wh = 0
    # แสดงเป็น Card รายการ
    for i, dev in enumerate(device_list):
        with st.container():
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1: chosen = st.checkbox(dev['item'], key=f"u_{i}")
            with c2: qty = st.number_input(f"จำนวน (เครื่อง) - {i}", min_value=0, value=0, key=f"q_{i}", label_visibility="collapsed")
            with c3: hrs = st.number_input(f"ชม. ใช้งาน - {i}", min_value=0, max_value=24, value=0, key=f"h_{i}", label_visibility="collapsed")
            if chosen and qty > 0: 
                total_daily_wh += (dev['watts'] * qty * hrs)

    units_per_day = total_daily_wh / 1000

    if units_per_day > 0:
        eff_factor = 1 - system_loss
        target_kw = units_per_day / (sun_hours * eff_factor)
        is_1p = phase == "1 Phase"
        available = [p for p in pea_packages if ((is_1p and "1 Phase" in p['name']) or (not is_1p and "3 Phase" in p['name']))]
        pkg = next((p for p in available if p['inverter_size'] >= target_kw), available[-1])
        saving_year = pkg['pv_size'] * sun_hours * eff_factor * unit_price * 365
        payback = pkg['price'] / saving_year

        st.markdown("### 📊 ผลการวิเคราะห์ระบบที่เหมาะสม")
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("ขนาดแนะนำ", f"{pkg['inverter_size']} kW")
        with m2: st.metric("งบประมาณ", f"{pkg['price']:,} ฿")
        with m3: st.metric("ระยะคืนทุน", f"{payback:.1f} ปี")
        with m4: st.metric("กำไรสะสม 25 ปี", f"{(saving_year * 25) - pkg['price']:,.0f} ฿")
        
        st.markdown(f'<a href="https://peasolar.pea.co.th/our-products/" target="_blank" class="product-btn">🔍 รายละเอียดอุปกรณ์ {pkg["inverter_size"]}kW</a>', unsafe_allow_html=True)

        # --- ฟอร์มลงทะเบียน ---
        st.markdown('<div class="registration-form">', unsafe_allow_html=True)
        st.markdown("### 📞 ลงทะเบียนขอรับคำปรึกษา")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            cust_name = st.text_input("ชื่อ-นามสกุล")
            cust_phone = st.text_input("เบอร์โทรศัพท์")
        with col_f2:
            cust_address = st.text_area("สถานที่ติดตั้ง")
        
        if st.button("ยืนยันการส่งข้อมูล"):
            if cust_name and cust_phone:
                st.success(f"บันทึกข้อมูลเรียบร้อยแล้ว!")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("กรุณาเลือกรายการอุปกรณ์ไฟฟ้าเพื่อเริ่มการวิเคราะห์")

with tab2:
    tr_full_id = "TR 250 (บ้านหนองแวง) 56-02564"
    st.markdown(f"### 🗺️ แผนภูมิภาระโหลดหม้อแปลง {tr_full_id}")
    
    grid_df = get_simulated_grid_data()
    solar_only = grid_df[grid_df['type'] == 'Solar PV Installed']
    ev_only = grid_df[grid_df['type'] == 'EV Wall Charger Request']

    col_map, col_stat = st.columns([2.5, 1])

    with col_stat:
        st.markdown("#### 📈 ข้อมูลการวิเคราะห์")
        total_solar = solar_only['capacity_kw'].sum()
        total_ev = ev_only['capacity_kw'].sum()
        
        st.markdown(f"""
        <div class="analysis-card">
            <small style="color: #a7f3d0;">กลางวัน (Solar Impact)</small><br>
            <span style="font-size:1.5rem;">-{total_solar * 0.7:.1f} kW</span>
        </div>
        <div class="analysis-card">
            <small style="color: #fca5a5;">กลางคืน (EV Impact)</small><br>
            <span style="font-size:1.5rem;">+{total_ev * 0.85:.1f} kW</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.warning(f"ความเสี่ยงโหลดเกิน: {(total_ev * 0.85) - (total_solar * 0.7):.1f} kW")

    with col_map:
        view_state = pdk.ViewState(latitude=16.7115, longitude=103.7477, zoom=15, pitch=45)
        scatterplot = pdk.Layer(
            "ScatterplotLayer", grid_df, get_position="[lon, lat]",
            get_fill_color="color_rgb", get_line_color="line_color",
            get_radius=40, line_width_min_pixels=2, pickable=True
        )
        tr_marker = pdk.Layer(
            "ScatterplotLayer", pd.DataFrame({'lat': [16.7115], 'lon': [103.7477]}),
            get_position="[lon, lat]", get_fill_color=[99, 102, 241, 100],
            get_radius=250, pickable=False
        )

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v10",
            initial_view_state=view_state,
            layers=[tr_marker, scatterplot],
            tooltip={"text": "{id}\nType: {type}\nCapacity: {capacity_kw} kW"}
        ))

    st.divider()
    st.markdown("#### 📋 รายละเอียดการเชื่อมต่อโครงข่าย")
    st.dataframe(grid_df[['id', 'type', 'capacity_kw', 'phase_connection']], use_container_width=True, hide_index=True)

st.divider()
st.markdown(f"<div style='text-align: center; color: rgba(232,245,233,0.3); font-size: 0.8rem;'>Solar Assistant v7.5 Premium Edition | {tr_full_id}</div>", unsafe_allow_html=True)
