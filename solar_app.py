import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse
import pydeck as pdk

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Solar Insight Pro | วิเคราะห์ระบบจำหน่ายไฟฟ้า",
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
        'color_rgb': [[255, 69, 0, 230], [255, 69, 0, 230]], 
        'line_color': [[200, 50, 0], [200, 50, 0]] 
    })
    
    # 2. ข้อมูลผู้ขอใช้ไฟติดตั้ง Wall Charger (5 ราย)
    # แก้ไข Error: มั่นใจว่าทุกลิสต์มีความยาวเท่ากับ 5 (จำนวนแถว)
    ev_data = pd.DataFrame({
        'id': [f'EV-{i:02d} ({tr_name})' for i in range(1, 6)],
        'lat': [base_lat + 0.002, base_lat + 0.0015, base_lat - 0.001, base_lat - 0.002, base_lat + 0.0005],
        'lon': [base_lon + 0.001, base_lon - 0.0015, base_lon + 0.002, base_lon + 0.0005, base_lon - 0.0025],
        'capacity_kw': [7, 7, 11, 7, 22],
        'phase_connection': ['Phase B', 'Phase C', 'Phase A', 'Phase B', '3 Phase'],
        'weight': [0.7, 0.7, 0.8, 0.7, 1.0],
        'type': 'EV Wall Charger Request',
        'color_rgb': [[16, 185, 129, 230]] * 5,
        'line_color': [[0, 0, 0]] * 5  # แก้ไขจาก [0, 0, 0] * 5 เป็น [[0, 0, 0]] * 5
    })
    
    df = pd.concat([solar_data, ev_data], ignore_index=True)
    df['gmaps_link'] = df.apply(lambda row: f"https://www.google.com/maps?q={row['lat']},{row['lon']}", axis=1)
    return df

# --- Custom CSS ปรับเป็น Light Theme (สีขาว) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    
    /* โครงสร้างพื้นฐาน */
    html, body, [class*="css"] { 
        font-family: 'Kanit', sans-serif; 
        color: #1f2937 !important;
    }
    
    .stApp { 
        background-color: #f9fafb;
    }
    
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    .app-header {
        background: transparent;
        padding: 1.5rem 0;
        margin-bottom: 1.5rem;
        border-bottom: 3px solid #3b82f6;
    }
    .header-title {
        font-size: 2.8rem;
        font-weight: 600;
        color: #1e3a8a;
        margin: 0;
    }
    .header-subtitle {
        font-size: 1.1rem;
        color: #4b5563;
        margin-top: 5px;
    }

    .analysis-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #e5e7eb;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .registration-form {
        background: #ffffff;
        padding: 30px;
        border-radius: 20px;
        border: 2px solid #e5e7eb;
        margin-top: 25px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: #e5e7eb;
        border-radius: 12px;
        padding: 5px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important; 
        color: #1e3a8a !important;
    }

    .product-btn {
        display: block; width: 100%; text-align: center;
        background: #2563eb;
        color: white !important; padding: 15px; border-radius: 12px;
        text-decoration: none; font-weight: 600; font-size: 1.1rem;
        margin-top: 15px;
    }
    
    div.stButton > button:first-child {
        background-color: #10b981;
        color: white !important;
        border-radius: 10px;
        border: none;
        padding: 12px 24px;
        width: 100%;
        font-weight: 600;
    }
    
    [data-testid="stMetricValue"] {
        color: #1e3a8a !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
st.markdown("""
    <div class="app-header">
        <h1 class="header-title">Solar Insight Pro ☀️</h1>
        <p class="header-subtitle">ระบบวิเคราะห์ข้อมูลโครงข่ายไฟฟ้าอัจฉริยะ (Smart Grid Intelligence)</p>
    </div>
    """, unsafe_allow_html=True)

# --- Top Summary Bar ---
top_col1, top_col2 = st.columns([1, 1])
with top_col1:
    st.markdown("""
        <div class="analysis-card" style="display: flex; align-items: center; gap: 1rem;">
            <div style="background: #eff6ff; padding: 12px; border-radius: 10px; font-size: 1.5rem;">🏢</div>
            <div>
                <small style="color: #6b7280">โหมดการทำงาน</small><br>
                <span style="font-size: 1.1rem; font-weight: 600; color: #1e40af;">วิเคราะห์ระบบจำหน่าย</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

with top_col2:
    st.markdown("""
        <div class="analysis-card" style="display: flex; align-items: center; gap: 1rem;">
            <div style="background: #fff7ed; padding: 12px; border-radius: 10px; font-size: 1.5rem;">⚡</div>
            <div>
                <small style="color: #6b7280">หม้อแปลงเป้าหมาย</small><br>
                <span style="font-size: 1.1rem; font-weight: 600; color: #9a3412;">TR 250 (บ้านหนองแวง) 56-02564</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🏠 วิเคราะห์การติดตั้งรายบ้าน", "📊 โหลดหม้อแปลง (Grid Balance)"])

with tab1:
    with st.sidebar:
        st.markdown("### ⚙️ การตั้งค่า")
        unit_price = st.number_input("ค่าไฟฟ้าเฉลี่ย (บาท/หน่วย)", value=4.7, step=0.1)
        phase = st.radio("ระบบไฟฟ้าที่บ้าน", ["1 Phase", "3 Phase"])
        st.divider()
        sun_hours = st.slider("ชั่วโมงแดดเฉลี่ย/วัน", 3.0, 6.0, 4.2)
        system_loss = st.slider("System Loss (%)", 5, 30, 15) / 100

    st.markdown("### 📝 ข้อมูลการใช้ไฟฟ้ากลางวัน")
    device_list = [
        {"item": "แอร์ 9,000 BTU (Inverter)", "watts": 800},
        {"item": "แอร์ 12,000 BTU (Inverter)", "watts": 1100},
        {"item": "แอร์ 18,000 BTU (Inverter)", "watts": 1600},
        {"item": "Wall Charger 7 kW (EV)", "watts": 7000},
        {"item": "อุปกรณ์อื่นๆ", "watts": 500},
    ]

    total_daily_wh = 0
    for i, dev in enumerate(device_list):
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1: chosen = st.checkbox(dev['item'], key=f"u_{i}")
        with c2: qty = st.number_input(f"จำนวน - {i}", min_value=0, value=0, key=f"q_{i}", label_visibility="collapsed")
        with c3: hrs = st.number_input(f"ชม. - {i}", min_value=0, max_value=24, value=0, key=f"h_{i}", label_visibility="collapsed")
        if chosen and qty > 0: 
            total_daily_wh += (dev['watts'] * qty * hrs)

    units_per_day = total_daily_wh / 1000

    # ส่วนแสดงผลลัพธ์การวิเคราะห์
    if units_per_day > 0:
        eff_factor = 1 - system_loss
        target_kw = units_per_day / (sun_hours * eff_factor)
        is_1p = phase == "1 Phase"
        available = [p for p in pea_packages if ((is_1p and "1 Phase" in p['name']) or (not is_1p and "3 Phase" in p['name']))]
        pkg = next((p for p in available if p['inverter_size'] >= target_kw), available[-1])
        saving_year = pkg['pv_size'] * sun_hours * eff_factor * unit_price * 365
        payback = pkg['price'] / saving_year

        st.markdown("### 📈 ระบบที่แนะนำสำหรับคุณ")
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("ขนาดแนะนำ", f"{pkg['inverter_size']} kW")
        with m2: st.metric("ราคาประมาณการ", f"{pkg['price']:,} ฿")
        with m3: st.metric("ระยะคืนทุน", f"{payback:.1f} ปี")
        with m4: st.metric("ประหยัดต่อปี", f"{saving_year:,.0f} ฿")
        
        st.markdown(f'<a href="https://peasolar.pea.co.th/" target="_blank" class="product-btn">🔍 ดูรายละเอียดที่ PEA Solar</a>', unsafe_allow_html=True)
    else:
        st.info("💡 กรุณาระบุข้อมูลการใช้ไฟฟ้าด้านบนเพื่อเริ่มการวิเคราะห์")

    # ฟอร์มลงทะเบียน (ย้ายออกมาด้านนอกเพื่อให้แสดงผลได้ชัดเจนขึ้น)
    st.markdown('<div class="registration-form">', unsafe_allow_html=True)
    st.markdown("### 📞 สนใจติดตั้งโซล่าเซลล์ (ลงทะเบียนเจ้าหน้าที่ติดต่อกลับ)")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.text_input("ชื่อผู้ติดต่อ", placeholder="ระบุชื่อ-นามสกุล")
        st.text_input("เบอร์โทรศัพท์", placeholder="0xx-xxx-xxxx")
    with col_f2:
        st.text_area("ที่อยู่ติดตั้ง / จุดสังเกต", placeholder="ระบุที่อยู่สำหรับการสำรวจหน้างาน")
    
    if st.button("ส่งข้อมูลให้เจ้าหน้าที่"):
        st.success("✅ ส่งข้อมูลสำเร็จ! เจ้าหน้าที่จะติดต่อกลับเพื่อสำรวจหน้างานโดยเร็วที่สุด")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    tr_id = "TR 250 (บ้านหนองแวง)"
    st.markdown(f"### 📍 แผนภูมิโครงข่ายไฟฟ้า {tr_id}")
    
    # ดึงข้อมูลที่แก้ไข Error แล้ว
    grid_df = get_simulated_grid_data()
    
    col_map, col_stat = st.columns([2.5, 1])

    with col_stat:
        st.markdown("#### 📊 สถิติภาระโหลด")
        total_solar = grid_df[grid_df['type'] == 'Solar PV Installed']['capacity_kw'].sum()
        total_ev = grid_df[grid_df['type'] == 'EV Wall Charger Request']['capacity_kw'].sum()
        
        st.markdown(f"""
        <div class="analysis-card">
            <small style="color: #059669;">Solar Installed (Total)</small><br>
            <span style="font-size:1.4rem; font-weight:600;">{total_solar:.1f} kW</span>
        </div>
        <div class="analysis-card">
            <small style="color: #dc2626;">EV Wall Charger Request</small><br>
            <span style="font-size:1.4rem; font-weight:600;">{total_ev:.1f} kW</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.info(f"หม้อแปลงนี้มีผู้ติดตั้ง Solar {len(grid_df[grid_df['type'] == 'Solar PV Installed'])} ราย และผู้ขอ EV {len(grid_df[grid_df['type'] == 'EV Wall Charger Request'])} ราย")

    with col_map:
        view_state = pdk.ViewState(latitude=16.7115, longitude=103.7477, zoom=15, pitch=40)
        scatterplot = pdk.Layer(
            "ScatterplotLayer", grid_df, get_position="[lon, lat]",
            get_fill_color="color_rgb", get_radius=60, pickable=True,
            filled=True, radius_min_pixels=5
        )
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v10",
            initial_view_state=view_state,
            layers=[scatterplot],
            tooltip={"text": "{id}\nประเภท: {type}\nขนาด: {capacity_kw} kW"}
        ))

    st.markdown("#### 📋 ตารางสรุปข้อมูลผู้ขอรับบริการ")
    st.dataframe(grid_df[['id', 'type', 'capacity_kw', 'phase_connection']], use_container_width=True, hide_index=True)

st.divider()
st.markdown("<div style='text-align: center; color: #9ca3af; font-size: 0.8rem;'>© 2024 Solar Insight Pro | บริหารจัดการโครงข่ายอัจฉริยะ</div>", unsafe_allow_html=True)
