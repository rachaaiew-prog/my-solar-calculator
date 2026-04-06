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

# --- แก้ไขฟังก์ชัน Data (Fix ValueError: All arrays must be of the same length) ---
def get_simulated_grid_data():
    base_lat, base_lon = 16.7115, 103.7477
    
    # 1. ข้อมูลผู้ติดตั้งโซล่าเซลล์ (15 รายการ)
    solar_count = 15
    solar_data = pd.DataFrame({
        'id': [f'S-{i:02d}' for i in range(1, solar_count + 1)],
        'lat': base_lat + np.random.randn(solar_count) * 0.004,
        'lon': base_lon + np.random.randn(solar_count) * 0.004,
        'capacity_kw': np.random.choice([3, 5, 10], solar_count),
        'weight': np.random.uniform(0.5, 1.0, solar_count),
        'type': 'Solar PV Installed',
        'color_rgb': [[255, 75, 75]] * solar_count # แก้ไข: สร้าง list ของ list ให้เท่ากับจำนวนแถว
    })
    
    # 2. ข้อมูลผู้ขอใช้ไฟติดตั้ง Wall Charger (20 รายการ)
    ev_count = 20
    ev_data = pd.DataFrame({
        'id': [f'EV-{i:02d}' for i in range(1, ev_count + 1)],
        'lat': base_lat + np.random.randn(ev_count) * 0.004,
        'lon': base_lon + np.random.randn(ev_count) * 0.004,
        'capacity_kw': np.random.choice([7, 11, 22], ev_count),
        'weight': np.random.uniform(0.5, 1.0, ev_count),
        'type': 'Wall Charger Request',
        'color_rgb': [[46, 125, 50]] * ev_count # แก้ไข: สร้าง list ของ list ให้เท่ากับจำนวนแถว
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
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.markdown(f"""
    <div class="app-header">
        <div style="display: flex; align-items: center; gap: 2rem;">
            <img src="https://lh3.googleusercontent.com/d/1RDUD8icYRqrf1s_HuwCsKABQjoD8OP0n" style="width:120px; border-radius:10px;">
            <div>
                <h1 style="color:white; margin:0; font-size:2.2rem;">Solar Assistant Pro</h1>
                <p style="font-size:1.1rem; opacity:0.9;">วิเคราะห์จุดคุ้มทุนและแผนภาพความหนาแน่นพลังงาน (อ.สมเด็จ)</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["💡 วิเคราะห์การติดตั้งรายบ้าน", "🌡️ แผนภูมิความร้อน (Heat Map)"])

with tab1:
    with st.sidebar:
        st.header("⚙️ ตั้งค่าการคำนวณ")
        unit_price = st.number_input("ค่าไฟฟ้าเฉลี่ย (บาท/หน่วย)", value=4.7, step=0.1)
        phase = st.radio("ระบบไฟฟ้าที่บ้าน", ["1 Phase", "3 Phase"])
        st.divider()
        sun_hours = st.slider("ชั่วโมงแดดจัดเฉลี่ยต่อวัน", 3.0, 6.0, 4.2)
        system_loss = st.slider("System Loss (%)", 5, 30, 15) / 100

    st.markdown("### 📝 ระบุการใช้ไฟฟ้าช่วงกลางวัน (09:00 - 16:00)")
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
    c_h1, c_h2, c_h3 = st.columns([2, 1, 1])
    with c_h1: st.markdown("**รายการเครื่องใช้ไฟฟ้า**")
    with c_h2: st.markdown("**จำนวน (เครื่อง)**")
    with c_h3: st.markdown("**ชม. ที่ใช้งาน**")

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
        total_profit_25yr = (saving_year * 25) - pkg['price']

        st.markdown("### 📊 สรุปผลการวิเคราะห์")
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("ขนาดแนะนำ", f"{pkg['inverter_size']} kW")
        with m2: st.metric("งบประมาณ", f"{pkg['price']:,} บาท")
        with m3: st.metric("ระยะเวลาคืนทุน", f"{payback:.1f} ปี")
        with m4: st.metric("กำไรสะสม 25 ปี", f"{total_profit_25yr:,.0f} บาท")

        st.markdown(f'<a href="https://peasolar.pea.co.th/our-products/" target="_blank" class="product-btn">🔍 ดูรายละเอียดแพ็กเกจ {pkg["inverter_size"]}kW</a>', unsafe_allow_html=True)

        st.markdown('<div class="registration-form">', unsafe_allow_html=True)
        st.subheader("📥 บันทึกข้อมูลและขอใบเสนอราคา")
        with st.form("solar_registration"):
            col_a, col_b = st.columns(2)
            with col_a: name = st.text_input("ชื่อ *")
            with col_b: surname = st.text_input("นามสกุล *")
            
            col_c, col_d = st.columns(2)
            with col_c: phone = st.text_input("เบอร์โทรศัพท์ *")
            with col_d: lat_long = st.text_input("พิกัด (lat, long) *", placeholder="16.7115, 103.7477")
            
            st.info(f"ระบบจะส่งข้อมูลขนาดที่แนะนำ: {pkg['inverter_size']} kW ไปยังฐานข้อมูล")
            
            if st.form_submit_button("🚀 ส่งข้อมูล (Google Forms)"):
                if name and surname and phone and lat_long:
                    # สร้าง Google Form URL พร้อม Pre-fill Data (อ้างอิงจากภาพ Google Form ของคุณ)
                    form_id = "1FAIpQLSclm-IwbIB85XoWuO_P8C-o8qHzQyYP4t7Gdvzcc6LpcWgoog"
                    # จำลอง entry ID (ต้องตรวจสอบจาก Google Form จริงของคุณอีกครั้ง)
                    params = {
                        "entry.1983389523": f"{pkg['inverter_size']} kW", # ขนาดแนะนำ
                        "entry.1966863461": lat_long, # พิกัด
                        "entry.1234567890": name, # ชื่อ (สมมติ ID)
                        "entry.1112223334": surname, # นามสกุล (สมมติ ID)
                        "entry.5556667778": phone, # เบอร์โทร (สมมติ ID)
                    }
                    query_string = urllib.parse.urlencode(params)
                    form_url = f"https://docs.google.com/forms/d/e/{form_id}/formResponse?{query_string}&submit=Submit"
                    
                    # ใน Streamlit Cloud เรามักจะใช้ลิ้งค์ให้กดยืนยัน หรือใช้ requests.post ในเบื้องหลัง
                    st.success(f"เตรียมส่งข้อมูลคุณ {name} เรียบร้อย!")
                    st.markdown(f"[คลิกที่นี่เพื่อยืนยันการส่งข้อมูลไปยังระบบเก็บข้อมูล]({form_url})")
                else:
                    st.error("กรุณากรอกข้อมูลให้ครบถ้วนทุกช่อง")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👆 กรุณาเลือกรายการเครื่องใช้ไฟฟ้าเพื่อคำนวณขนาดระบบที่เหมาะสม")

with tab2:
    st.markdown("### 🗺️ Infrastructure Request Heat Map (อ.สมเด็จ)")
    st.write("แสดงความหนาแน่นเชิงพื้นที่ของจุดติดตั้ง Solar PV และผู้ขอใช้ไฟสำหรับ Wall Charger")
    
    data_df = get_simulated_grid_data()
    solar_df = data_df[data_df['type'] == 'Solar PV Installed']
    ev_df = data_df[data_df['type'] == 'Wall Charger Request']
    
    view_state = pdk.ViewState(latitude=16.7115, longitude=103.7477, zoom=14.0, pitch=40)
    
    # Heatmap Layer สำหรับ Solar PV (สีแดง-ส้ม)
    solar_heatmap = pdk.Layer(
        "HeatmapLayer",
        solar_df,
        get_position="[lon, lat]",
        get_weight="weight",
        radius_pixels=60,
        intensity=1.2,
        threshold=0.1,
        color_range=[
            [255, 255, 178],
            [254, 217, 118],
            [254, 178, 76],
            [253, 141, 60],
            [240, 59, 32],
            [189, 0, 38]
        ]
    )
    
    # Heatmap Layer สำหรับ Wall Charger Request (สีเขียว)
    ev_heatmap = pdk.Layer(
        "HeatmapLayer",
        ev_df,
        get_position="[lon, lat]",
        get_weight="weight",
        radius_pixels=60,
        intensity=1.2,
        threshold=0.1,
        color_range=[
            [237, 248, 233],
            [186, 228, 179],
            [116, 196, 118],
            [49, 163, 84],
            [0, 109, 44]
        ]
    )

    # Scatter Layer สำหรับแสดงพิกัดจริง
    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data_df,
        get_position="[lon, lat]",
        get_color="color_rgb",
        get_radius=35,
        pickable=True
    )

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v10',
        initial_view_state=view_state,
        layers=[solar_heatmap, ev_heatmap, point_layer],
        tooltip={"text": "{id}\nType: {type}\nCapacity: {capacity_kw} kW"}
    ))

    # คำอธิบายสัญลักษณ์
    st.markdown("""
        <div style="display:flex; flex-wrap:wrap; gap:20px; background:white; padding:15px; border-radius:10px; border:1px solid #eee;">
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:20px;height:20px;background:linear-gradient(to right, #feb24c, #bd0026);border-radius:4px;"></div>
                <span><b>ความหนาแน่น Solar PV</b> (ผู้ติดตั้งแล้ว 15 ราย)</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:20px;height:20px;background:linear-gradient(to right, #74c476, #006d2c);border-radius:4px;"></div>
                <span><b>ความหนาแน่น Wall Charger</b> (ผู้ขอใช้ไฟ 20 ราย)</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption("Solar Assistant v7.2 | Google Form Integration & Fix ValueError")
