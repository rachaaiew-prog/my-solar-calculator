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

# --- ข้อมูลจำลอง Map Data (Solar 15, EV 20 - อ.สมเด็จ จ.กาฬสินธุ์) ---
def get_simulated_grid_data():
    base_lat, base_lon = 16.7115, 103.7477
    
    # 1. ข้อมูลหม้อแปลง (Transformer Nodes)
    transformers = pd.DataFrame({
        'id': ['TR-01', 'TR-02'],
        'lat': [16.7130, 16.7100],
        'lon': [103.7485, 103.7465],
        'capacity_kva': [160, 250],
        'type': 'Transformer',
        'color_rgb': [[0, 0, 255, 255]] * 2 # สีน้ำเงิน
    })
    
    # 2. ข้อมูล Solar (15 รายการ)
    solar_data = pd.DataFrame({
        'id': [f'S-{i:02d}' for i in range(1, 16)],
        'lat': base_lat + np.random.randn(15) * 0.006,
        'lon': base_lon + np.random.randn(15) * 0.006,
        'capacity_kw': np.random.choice([3, 5, 10], 15),
        'type': 'Solar PV',
        'color_rgb': [[255, 75, 75, 200]] * 15, # สีแดง
        'assigned_tr': np.random.choice(['TR-01', 'TR-02'], 15)
    })
    
    # 3. ข้อมูล EV วงจรที่ 2 (20 รายการ)
    ev_data = pd.DataFrame({
        'id': [f'EV-{i:02d}' for i in range(1, 21)],
        'lat': base_lat + np.random.randn(20) * 0.006,
        'lon': base_lon + np.random.randn(20) * 0.006,
        'capacity_kw': np.random.choice([7, 11], 20),
        'type': 'EV Circuit 2',
        'color_rgb': [[46, 125, 50, 230]] * 20, # สีเขียว
        'assigned_tr': np.random.choice(['TR-01', 'TR-02'], 20)
    })
    
    points = pd.concat([solar_data, ev_data], ignore_index=True)
    
    paths = []
    for _, row in points.iterrows():
        tr = transformers[transformers['id'] == row['assigned_tr']].iloc[0]
        paths.append({
            'from_lat': tr['lat'], 'from_lon': tr['lon'],
            'to_lat': row['lat'], 'to_lon': row['lon'],
            'tr_id': tr['id'],
            'type': row['type']
        })
        
    return transformers, points, pd.DataFrame(paths)

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
    .status-card {
        padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem; border: 1px solid #eee;
        background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
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
                <p style="font-size:1.1rem; opacity:0.9;">วิเคราะห์จุดคุ้มทุนและวางแผนระบบจำหน่ายไฟฟ้า (อ.สมเด็จ)</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["💡 วิเคราะห์การติดตั้งรายบ้าน", "🗺️ วิเคราะห์โครงข่าย (Network Analysis)"])

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
        st.subheader("📥 สนใจรับคำปรึกษาและใบเสนอราคา")
        with st.form("solar_registration"):
            col_a, col_b = st.columns(2)
            with col_a: name = st.text_input("ชื่อ-นามสกุล *")
            with col_b: phone = st.text_input("เบอร์โทรศัพท์ *")
            addr = st.text_input("สถานที่ติดตั้ง หรือ พิกัด GPS")
            if st.form_submit_button("🚀 ส่งข้อมูลขอใบเสนอราคา"):
                if name and phone:
                    st.success(f"บันทึกข้อมูลคุณ {name} เรียบร้อย ทีมงานจะติดต่อกลับโดยเร็วที่สุด")
                else:
                    st.error("กรุณากรอกชื่อและเบอร์โทรศัพท์")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👆 กรุณาเลือกรายการเครื่องใช้ไฟฟ้าเพื่อคำนวณขนาดระบบที่เหมาะสม")

with tab2:
    st.markdown("### 🗺️ Network Visualization: Solar + EV Integration")
    st.write("วิเคราะห์ความสัมพันธ์ระหว่างหม้อแปลงกับผู้ใช้ไฟ Solar 15 ราย และ EV 20 ราย")
    
    tr_df, pt_df, path_df = get_simulated_grid_data()
    view_state = pdk.ViewState(latitude=16.7115, longitude=103.7477, zoom=14.5)
    
    line_layer = pdk.Layer("LineLayer", path_df, get_source_position="[from_lon, from_lat]", get_target_position="[to_lon, to_lat]", get_color="[150, 150, 150, 100]", get_width=2)
    point_layer = pdk.Layer("ScatterplotLayer", pt_df, get_position="[lon, lat]", get_color="color_rgb", get_radius=50, pickable=True)
    tr_layer = pdk.Layer("ScatterplotLayer", tr_df, get_position="[lon, lat]", get_color="color_rgb", get_radius=120, pickable=True)

    st.pydeck_chart(pdk.Deck(map_style='mapbox://styles/mapbox/light-v9', initial_view_state=view_state, layers=[line_layer, point_layer, tr_layer], tooltip={"text": "{id} | {type}\nCapacity: {capacity_kw}{capacity_kva} units"}))

    st.markdown("""
        <div style="display:flex; gap:15px; margin-bottom:20px;">
            <div style="display:flex; align-items:center; gap:5px;"><div style="width:15px;height:15px;background:#0000FF;border-radius:50%;"></div><span>Transformer</span></div>
            <div style="display:flex; align-items:center; gap:5px;"><div style="width:15px;height:15px;background:#FF4B4B;border-radius:50%;"></div><span>Solar PV (15 ราย)</span></div>
            <div style="display:flex; align-items:center; gap:5px;"><div style="width:15px;height:15px;background:#2E7D32;border-radius:50%;"></div><span>EV Circuit 2 (20 ราย)</span></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚡ Transformer Load & Balance Report")
    cols = st.columns(len(tr_df))
    for i, (_, tr) in enumerate(tr_df.iterrows()):
        with cols[i]:
            tr_points = pt_df[pt_df['assigned_tr'] == tr['id']]
            ev_load = tr_points[tr_points['type'] == 'EV Circuit 2']['capacity_kw'].sum()
            solar_gen = tr_points[tr_points['type'] == 'Solar PV']['capacity_kw'].sum()
            usage_pct = (ev_load / tr['capacity_kva']) * 100
            
            st.markdown(f"""
                <div class="status-card">
                    <h4>🏪 {tr['id']} ({tr['capacity_kva']} kVA)</h4>
                    <p><b>Load EV:</b> {ev_load} kW</p>
                    <p><b>Solar Gen:</b> {solar_gen} kW</p>
                    <hr>
                    <p><b>Utilization:</b> {usage_pct:.1f}%</p>
                </div>
            """, unsafe_allow_html=True)
            
            if usage_pct > 80: st.error(f"🚨 {tr['id']} วิกฤต: โหลดสูงเกินไป")
            elif usage_pct > 60: st.warning(f"⚠️ {tr['id']} เสี่ยง: เริ่มหนาแน่น")
            else: st.success(f"✅ {tr['id']} ปกติ: รองรับโหลดได้")

st.divider()
st.caption("Solar Assistant v6.4 | Integrated Residential Calculator & Grid Analysis")
