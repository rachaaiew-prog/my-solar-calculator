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

# --- ฟังก์ชันจำลองข้อมูลสำหรับ Heat Map (จำลองข้อมูลจากระบบจำหน่าย) ---
def get_simulated_grid_data():
    # พิกัดกลาง (อ.สมเด็จ จ.กาฬสินธุ์)
    base_lat, base_lon = 16.7115, 103.7477
    
    # 1. ข้อมูลผู้ติดตั้งโซล่าเซลล์ (Solar PV Installed) - สีแดง/ส้ม
    solar_count = 25
    solar_data = pd.DataFrame({
        'id': [f'Solar-{i:02d}' for i in range(1, solar_count + 1)],
        'lat': base_lat + np.random.randn(solar_count) * 0.005,
        'lon': base_lon + np.random.randn(solar_count) * 0.005,
        'capacity_kw': np.random.choice([3, 5, 10, 20], solar_count),
        'weight': np.random.uniform(0.6, 1.0, solar_count), # สำหรับความเข้ม Heatmap
        'type': 'Solar PV Installed',
        'color_rgb': [[255, 140, 0]] * solar_count
    })
    
    # 2. ข้อมูลผู้ขอใช้ไฟติดตั้ง Wall Charger (EV Request) - สีเขียว
    ev_count = 30
    ev_data = pd.DataFrame({
        'id': [f'EV-{i:02d}' for i in range(1, ev_count + 1)],
        'lat': base_lat + np.random.randn(ev_count) * 0.006,
        'lon': base_lon + np.random.randn(ev_count) * 0.006,
        'capacity_kw': np.random.choice([7, 11, 22], ev_count),
        'weight': np.random.uniform(0.5, 0.9, ev_count),
        'type': 'EV Wall Charger Request',
        'color_rgb': [[46, 125, 50]] * ev_count
    })
    
    return pd.concat([solar_data, ev_data], ignore_index=True)

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
    .registration-form {
        background-color: #ffffff; padding: 30px; border-radius: 20px;
        border: 1px solid #e0e0e0; margin-top: 25px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.08);
    }
    .product-btn {
        display: block; width: 100%; text-align: center;
        background: linear-gradient(90deg, #ff9800, #f57c00);
        color: white !important; padding: 20px; border-radius: 15px;
        text-decoration: none; font-weight: bold; font-size: 1.2rem;
        margin-top: 20px; box-shadow: 0 5px 15px rgba(245, 124, 0, 0.3);
        transition: 0.3s;
    }
    .product-btn:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(245, 124, 0, 0.4); }
    .confirm-btn {
        display: block; width: 100%; text-align: center;
        background: #2e7d32; color: white !important;
        padding: 15px; border-radius: 12px; text-decoration: none;
        font-weight: bold; margin-top: 15px; font-size: 1.1rem;
    }
    .legend-box {
        padding: 10px; border-radius: 10px; background: white; 
        border: 1px solid #ddd; display: inline-block; margin-right: 10px;
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
                <p style="font-size:1.1rem; opacity:0.9;">วิเคราะห์จุดคุ้มทุนและแผนภาพความหนาแน่นพลังงานในระบบจำหน่ายไฟฟ้า</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- แท็บเมนูหลัก ---
tab1, tab2 = st.tabs(["💡 วิเคราะห์การติดตั้งรายบ้าน", "🗺️ แผนภูมิความร้อน (Grid Heat Map)"])

with tab1:
    # --- Input Section (Sidebar) ---
    with st.sidebar:
        st.header("⚙️ ตั้งค่าการคำนวณ")
        unit_price = st.number_input("ค่าไฟฟ้าเฉลี่ย (บาท/หน่วย)", value=4.7, step=0.1)
        phase = st.radio("ระบบไฟฟ้าที่บ้าน", ["1 Phase", "3 Phase"])
        st.divider()
        sun_hours = st.slider("ชั่วโมงแดดจัดเฉลี่ยต่อวัน", 3.0, 6.0, 4.2)
        system_loss = st.slider("System Loss (%)", 5, 30, 15) / 100

    # --- 1. ระบุการใช้ไฟฟ้าช่วงกลางวัน (Detailed Selection) ---
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

    # --- การคำนวณและแสดงผล ---
    if units_per_day > 0:
        st.divider()
        eff_factor = 1 - system_loss
        target_kw = units_per_day / (sun_hours * eff_factor)
        
        is_1p = phase == "1 Phase"
        available = [p for p in pea_packages if ((is_1p and "1 Phase" in p['name']) or (not is_1p and "3 Phase" in p['name']))]
        pkg = next((p for p in available if p['inverter_size'] >= target_kw), available[-1])
        
        saving_day = pkg['pv_size'] * sun_hours * eff_factor * unit_price
        saving_year = saving_day * 365
        payback = pkg['price'] / saving_year
        total_profit_25yr = (saving_year * 25) - pkg['price']

        st.markdown("### 📊 สรุปผลการวิเคราะห์")
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("ขนาดระบบแนะนำ", f"{pkg['inverter_size']} kW")
        with m2: st.metric("งบประมาณลงทุน", f"{pkg['price']:,} บาท")
        with m3: st.metric("ระยะเวลาคืนทุน", f"{payback:.1f} ปี")
        with m4: st.metric("กำไรสะสม 25 ปี", f"{total_profit_25yr:,.0f} บาท")

        # กราฟ Break-even
        st.markdown("#### 📈 วิเคราะห์จุดคุ้มทุน (Break-even Analysis)")
        years = list(range(26))
        investment_line = [pkg['price']] * 26
        savings_line = [saving_year * y for y in years]
        chart_df = pd.DataFrame({
            "ปีที่": years,
            "เงินลงทุน (บาท)": investment_line,
            "รายได้สะสม (บาท)": savings_line
        }).set_index("ปีที่")
        st.line_chart(chart_df)

        st.markdown(f'<a href="https://peasolar.pea.co.th/our-products/" target="_blank" class="product-btn">🔍 ดูรายละเอียดสเปกอุปกรณ์ในแพ็กเกจ {pkg["inverter_size"]}kW</a>', unsafe_allow_html=True)

        # --- ส่วนส่งข้อมูล ---
        st.markdown('<div class="registration-form">', unsafe_allow_html=True)
        st.subheader("📥 สนใจรับคำปรึกษาและใบเสนอราคา")
        with st.form("solar_form_v58"):
            col_a, col_b = st.columns(2)
            with col_a: name = st.text_input("ชื่อ-นามสกุล *")
            with col_b: phone = st.text_input("เบอร์โทรศัพท์ *")
            addr = st.text_input("พิกัด GPS หรือ สถานที่ติดตั้ง")
            submitted = st.form_submit_button("🚀 บันทึกข้อมูลและขอใบเสนอราคา")
            if submitted:
                if name and phone:
                    FORM_ID = "1FAIpQLSclm-IwbIb85XoWuO_P8C-o8qHZqyYP4t7GdVz7cc6LpcWgog"
                    info_summary = f"ระบบ {pkg['inverter_size']}kW | ใช้ไฟกลางวัน {units_per_day:.2f} หน่วย | {addr}"
                    params = {"entry.1381098045": name, "entry.225801865": phone, "entry.1907655311": info_summary}
                    final_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/viewform?" + urllib.parse.urlencode(params)
                    st.success("สร้างลิงก์ข้อมูลของคุณเรียบร้อยแล้ว!")
                    st.markdown(f'<a href="{final_url}" target="_blank" class="confirm-btn">✅ กดยืนยันเพื่อส่งข้อมูลให้เจ้าหน้าที่</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👆 กรุณาเลือกรายการเครื่องใช้ไฟฟ้าและระบุเวลาที่ใช้งาน เพื่อให้ระบบเริ่มการวิเคราะห์")

with tab2:
    st.markdown("### 🗺️ Infrastructure Density Heat Map (อ.สมเด็จ)")
    st.write("แผนภาพแสดงความหนาแน่นของผู้ติดตั้ง Solar Cell (สีส้ม) และผู้ยื่นขอ EV Charger (สีเขียว) เพื่อใช้ในการพิจารณาเพิ่มขนาดหม้อแปลง")
    
    # ดึงข้อมูลจำลอง
    grid_df = get_simulated_grid_data()
    solar_only = grid_df[grid_df['type'] == 'Solar PV Installed']
    ev_only = grid_df[grid_df['type'] == 'EV Wall Charger Request']

    # คำนวณ View State
    view_state = pdk.ViewState(
        latitude=16.7115, 
        longitude=103.7477, 
        zoom=13, 
        pitch=45
    )

    # สร้าง Layer
    solar_layer = pdk.Layer(
        "HeatmapLayer",
        solar_only,
        get_position="[lon, lat]",
        get_weight="weight",
        radius_pixels=60,
        intensity=1,
        threshold=0.05,
        color_range=[
            [255, 255, 178], [254, 217, 118], [254, 178, 76], 
            [253, 141, 60], [240, 59, 32], [189, 0, 38]
        ]
    )

    ev_layer = pdk.Layer(
        "HeatmapLayer",
        ev_only,
        get_position="[lon, lat]",
        get_weight="weight",
        radius_pixels=60,
        intensity=1,
        threshold=0.05,
        color_range=[
            [237, 248, 233], [186, 228, 179], [116, 196, 118],
            [49, 163, 84], [0, 109, 44]
        ]
    )

    point_layer = pdk.Layer(
        "ScatterplotLayer",
        grid_df,
        get_position="[lon, lat]",
        get_color="color_rgb",
        get_radius=40,
        pickable=True
    )

    # แสดงผลแผนที่
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state,
        layers=[solar_layer, ev_layer, point_layer],
        tooltip={"text": "{id}\nType: {type}\nCapacity: {capacity_kw} kW"}
    ))

    # คำอธิบายสัญลักษณ์
    st.markdown("""
    <div style="display: flex; gap: 10px;">
        <div class="legend-box"><span style="color: #FF8C00;">●</span> Solar PV Installed (ความหนาแน่นการผลิตไฟ)</div>
        <div class="legend-box"><span style="color: #2E7D32;">●</span> EV Charger Request (ความหนาแน่นการใช้ไฟสูง)</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 บริเวณที่มีสีเข้มซ้อนทับกัน (Overlay) คือจุดวิกฤตที่หม้อแปลงอาจต้องรับภาระหนักทั้งการไหลย้อนของไฟโซล่าและการดึงไฟของรถ EV")

st.divider()
st.caption("Solar Assistant v6.0 | Grid Analysis & Heat Map Integrated")
