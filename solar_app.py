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

# --- ฟังก์ชันจำลองข้อมูลสำหรับ Heat Map (เน้นหม้อแปลงเฉพาะ: Solar 2, EV 5) ---
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

# --- Custom CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f8f9fa; }
    .app-header {
        background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3f51b5 100%);
        padding: 2.5rem; color: white; border-radius: 20px; margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(26, 35, 126, 0.2);
    }
    .analysis-card {
        background: white; border-radius: 15px; padding: 20px;
        border-left: 5px solid #1a237e; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .registration-form {
        background-color: #ffffff; padding: 30px; border-radius: 20px;
        border: 1px solid #e0e0e0; margin-top: 25px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.08);
    }
    .legend-box {
        padding: 10px; border-radius: 10px; background: white; 
        border: 1px solid #ddd; display: inline-block; margin-right: 10px;
    }
    /* ปุ่มวิเคราะห์สินค้า */
    .product-btn {
        display: block; width: 100%; text-align: center;
        background: linear-gradient(90deg, #ff9800, #f57c00);
        color: white !important; padding: 20px; border-radius: 15px;
        text-decoration: none; font-weight: bold; font-size: 1.2rem;
        margin-top: 20px; box-shadow: 0 5px 15px rgba(245, 124, 0, 0.3);
    }
    /* แก้ไขสีปุ่มส่งข้อมูลใน Streamlit */
    div.stButton > button:first-child {
        background-color: #2e7d32;
        color: white;
        border-radius: 12px;
        border: none;
        padding: 10px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #1b5e20;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.4);
        border: none;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
st.markdown(f"""
    <div class="app-header">
        <div style="display: flex; align-items: center; gap: 2rem;">
            <img src="https://lh3.googleusercontent.com/d/1RDUD8icYRqrf1s_HuwCsKABQjoD8OP0n" style="width:120px; border-radius:10px;">
            <div>
                <h1 style="color:white; margin:0; font-size:2.5rem;">Solar Assistant Pro</h1>
                <p style="font-size:1.1rem; opacity:0.9;">วิเคราะห์โหลดหม้อแปลงไฟฟ้าจำหน่าย (Single Transformer Analysis)</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["💡 วิเคราะห์การติดตั้งรายบ้าน", "🗺️ วิเคราะห์โหลดหม้อแปลง (Transformer Balance)"])

with tab1:
    with st.sidebar:
        st.header("⚙️ ตั้งค่าการคำนวณ")
        unit_price = st.number_input("ค่าไฟฟ้าเฉลี่ย (บาท/หน่วย)", value=4.7, step=0.1)
        phase = st.radio("ระบบไฟฟ้าที่บ้าน", ["1 Phase", "3 Phase"])
        st.divider()
        sun_hours = st.slider("ชั่วโมงแดดจัดเฉลี่ยต่อวัน", 3.0, 6.0, 4.2)
        system_loss = st.slider("System Loss (%)", 5, 30, 15) / 100

    st.markdown("### 📝 1. ระบุการใช้ไฟฟ้าช่วงกลางวัน (09:00 - 16:00)")
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
    col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
    with col_h1: st.markdown("**รายการเครื่องใช้ไฟฟ้า**")
    with col_h2: st.markdown("**จำนวน (เครื่อง)**")
    with col_h3: st.markdown("**ชม. ที่ใช้งาน**")

    for i, dev in enumerate(device_list):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: chosen = st.checkbox(dev['item'], key=f"u_{i}")
        with c2: qty = st.number_input("จำนวน", min_value=0, value=0, key=f"q_{i}", label_visibility="collapsed")
        with c3: hrs = st.number_input("ชม.", min_value=0, max_value=24, value=0, key=f"h_{i}", label_visibility="collapsed")
        if chosen and qty > 0: 
            total_daily_wh += (dev['watts'] * qty * hrs)

    units_per_day = total_daily_wh / 1000

    if units_per_day > 0:
        st.divider()
        eff_factor = 1 - system_loss
        target_kw = units_per_day / (sun_hours * eff_factor)
        is_1p = phase == "1 Phase"
        available = [p for p in pea_packages if ((is_1p and "1 Phase" in p['name']) or (not is_1p and "3 Phase" in p['name']))]
        pkg = next((p for p in available if p['inverter_size'] >= target_kw), available[-1])
        saving_year = pkg['pv_size'] * sun_hours * eff_factor * unit_price * 365
        payback = pkg['price'] / saving_year

        st.markdown("### 📊 สรุปผลการวิเคราะห์")
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("ขนาดแนะนำ", f"{pkg['inverter_size']} kW")
        with m2: st.metric("งบประมาณ", f"{pkg['price']:,} บาท")
        with m3: st.metric("คืนทุน", f"{payback:.1f} ปี")
        with m4: st.metric("กำไร 25 ปี", f"{(saving_year * 25) - pkg['price']:,.0f} บาท")
        st.markdown(f'<a href="https://peasolar.pea.co.th/our-products/" target="_blank" class="product-btn">🔍 ดูรายละเอียดสเปกอุปกรณ์ {pkg["inverter_size"]}kW</a>', unsafe_allow_html=True)

        # --- ฟอร์มลงทะเบียนข้อมูลลูกค้า ---
        st.markdown('<div class="registration-form">', unsafe_allow_html=True)
        st.markdown("### 📞 ลงทะเบียนขอรับคำปรึกษา / สำรวจหน้างาน")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            cust_name = st.text_input("ชื่อ-นามสกุล ผู้ติดต่อ")
            cust_phone = st.text_input("เบอร์โทรศัพท์")
        with col_f2:
            cust_address = st.text_area("ที่อยู่ติดตั้ง / จุดสังเกต")
        
        if st.button("ยืนยันข้อมูลและส่งเรื่อง", use_container_width=True):
            if cust_name and cust_phone:
                st.success(f"ขอบคุณคุณ {cust_name} ระบบบันทึกข้อมูลเรียบร้อย เจ้าหน้าที่จะติดต่อกลับที่เบอร์ {cust_phone}")
            else:
                st.error("กรุณากรอกข้อมูลชื่อและเบอร์โทรศัพท์ให้ครบถ้วน")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👆 กรุณาเลือกรายการเครื่องใช้ไฟฟ้าเพื่อให้ระบบเริ่มวิเคราะห์")

with tab2:
    tr_full_id = "TR 250 (บ้านหนองแวง) 56-02564"
    st.markdown(f"### 🗺️ Transformer {tr_full_id} Load Balance Map")
    st.info(f"จำลองสถานการณ์: หม้อแปลง {tr_full_id} รองรับผู้ใช้ไฟที่มี Solar 2 ราย และ EV Charger 5 ราย")
    
    grid_df = get_simulated_grid_data()
    solar_only = grid_df[grid_df['type'] == 'Solar PV Installed']
    ev_only = grid_df[grid_df['type'] == 'EV Wall Charger Request']

    # คำนวณค่าทางสถิติสำหรับ Balance
    total_solar_kw = solar_only['capacity_kw'].sum()
    total_ev_kw = ev_only['capacity_kw'].sum()
    avg_day_load_reduction = total_solar_kw * 0.7 
    night_load_increase = total_ev_kw * 0.85 

    col_map, col_stat = st.columns([2.5, 1])

    with col_stat:
        st.markdown(f"#### ⚡ {tr_full_id} Analytics")
        st.markdown(f"""
        <div class="analysis-card">
            <small>ช่วงกลางวัน (ลดโหลดหม้อแปลง)</small><br>
            <b>Net Load Δ: -{avg_day_load_reduction:.1f} kW</b><br>
            <p style="font-size:0.8rem; color:gray;">Solar รวม: {total_solar_kw} kW (2 ราย)</p>
        </div>
        <div class="analysis-card" style="border-left-color: #2e7d32;">
            <small>ช่วง 22:00 น. (เพิ่มโหลดหม้อแปลง)</small><br>
            <b>Net Load Δ: +{night_load_increase:.1f} kW</b><br>
            <p style="font-size:0.8rem; color:gray;">EV รวม: {total_ev_kw} kW (5 ราย)</p>
        </div>
        """, unsafe_allow_html=True)
        
        balance_gap = night_load_increase - avg_day_load_reduction
        st.error(f"**Transformer Stress:** {balance_gap:.1f} kW")

    with col_map:
        view_state = pdk.ViewState(latitude=16.7115, longitude=103.7477, zoom=15, pitch=40)
        scatterplot = pdk.Layer(
            "ScatterplotLayer", grid_df, get_position="[lon, lat]",
            get_fill_color="color_rgb", get_line_color="line_color",
            get_radius=30, line_width_min_pixels=3, pickable=True
        )
        tr_marker = pdk.Layer(
            "ScatterplotLayer", pd.DataFrame({'lat': [16.7115], 'lon': [103.7477]}),
            get_position="[lon, lat]", get_fill_color=[26, 35, 126, 100],
            get_radius=300, pickable=False
        )

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[tr_marker, scatterplot],
            tooltip={"text": "{id}\nCapacity: {capacity_kw} kW\nPhase: {phase_connection}"}
        ))

    st.write("---")
    st.subheader(f"📍 รายละเอียดจุดติดตั้งและการเชื่อมต่อเฟส ({tr_full_id})")
    
    # แสดงตารางแยกตามประเภทพร้อมระบุเฟส
    c_solar, c_ev = st.columns(2)
    
    with c_solar:
        st.markdown("**☀️ กลุ่มติดตั้ง Solar PV**")
        st.dataframe(
            solar_only[['id', 'capacity_kw', 'phase_connection']],
            column_config={
                "id": "รหัสจุดติดตั้ง",
                "capacity_kw": "ขนาด (kW)",
                "phase_connection": "เฟสที่เชื่อมต่อ"
            },
            hide_index=True, use_container_width=True
        )

    with c_ev:
        st.markdown("**🚗 กลุ่มติดตั้ง EV Charger**")
        st.dataframe(
            ev_only[['id', 'capacity_kw', 'phase_connection']],
            column_config={
                "id": "รหัสจุดติดตั้ง",
                "capacity_kw": "ขนาด (kW)",
                "phase_connection": "เฟสที่เชื่อมต่อ"
            },
            hide_index=True, use_container_width=True
        )

st.divider()
st.caption(f"Solar Assistant v7.1 | {tr_full_id} Phase Analysis")
