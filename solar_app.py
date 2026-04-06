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
    base_lat, base_lon = 16.7115, 103.7477
    
    # 1. ข้อมูลผู้ติดตั้งโซล่าเซลล์ (Solar PV Installed) - สีส้มเข้มขอบทอง
    solar_count = 25
    solar_data = pd.DataFrame({
        'id': [f'Solar-{i:02d}' for i in range(1, solar_count + 1)],
        'lat': base_lat + np.random.randn(solar_count) * 0.005,
        'lon': base_lon + np.random.randn(solar_count) * 0.005,
        'capacity_kw': np.random.choice([3, 5, 10, 20], solar_count),
        'weight': np.random.uniform(0.6, 1.0, solar_count),
        'type': 'Solar PV Installed',
        'color_rgb': [[255, 69, 0, 200]] * solar_count, # OrangeRed
        'line_color': [[255, 215, 0]] * solar_count # Gold border
    })
    
    # 2. ข้อมูลผู้ขอใช้ไฟติดตั้ง Wall Charger (EV Request) - สีเขียวนีออน
    ev_count = 30
    ev_data = pd.DataFrame({
        'id': [f'EV-{i:02d}' for i in range(1, ev_count + 1)],
        'lat': base_lat + np.random.randn(ev_count) * 0.006,
        'lon': base_lon + np.random.randn(ev_count) * 0.006,
        'capacity_kw': np.random.choice([7, 11, 22], ev_count),
        'weight': np.random.uniform(0.5, 0.9, ev_count),
        'type': 'EV Wall Charger Request',
        'color_rgb': [[57, 255, 20, 200]] * ev_count, # Neon Green
        'line_color': [[255, 255, 255]] * ev_count
    })
    
    df = pd.concat([solar_data, ev_data], ignore_index=True)
    # เพิ่ม Google Maps Link
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
    .analysis-card {
        background: white; border-radius: 15px; padding: 20px;
        border-left: 5px solid #1a237e; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
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
                <p style="font-size:1.1rem; opacity:0.9;">วิเคราะห์โครงสร้างพื้นฐานและจุดสมดุลพลังงาน (Grid Balance Analysis)</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- แท็บเมนูหลัก ---
tab1, tab2 = st.tabs(["💡 วิเคราะห์การติดตั้งรายบ้าน", "🗺️ แผนภูมิความร้อนและจุดสมดุล (Grid Balance Map)"])

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
    else:
        st.info("👆 กรุณาเลือกรายการเครื่องใช้ไฟฟ้าเพื่อให้ระบบเริ่มวิเคราะห์")

with tab2:
    st.markdown("### 🗺️ Infrastructure Density & Balance Map (อ.สมเด็จ)")
    
    # ดึงข้อมูลจำลอง
    grid_df = get_simulated_grid_data()
    solar_only = grid_df[grid_df['type'] == 'Solar PV Installed']
    ev_only = grid_df[grid_df['type'] == 'EV Wall Charger Request']

    # คำนวณค่าทางสถิติสำหรับ Balance
    total_solar_kw = solar_only['capacity_kw'].sum()
    total_ev_kw = ev_only['capacity_kw'].sum()
    avg_day_load_reduction = total_solar_kw * 0.75 # คาดการณ์การผลิตไฟ 75%
    night_load_increase = total_ev_kw * 0.8 # คาดการณ์การชาร์จพร้อมกัน 80%

    col_map, col_stat = st.columns([3, 1])

    with col_stat:
        st.markdown("#### ⚡ Grid Analytics")
        st.markdown(f"""
        <div class="analysis-card">
            <small>ช่วงกลางวัน (09:00-16:00)</small><br>
            <b>โหลดลดลงสะสม: -{avg_day_load_reduction:.1f} kW</b><br>
            <p style="font-size:0.8rem; color:gray;">(จาก Solar PV {len(solar_only)} ราย)</p>
        </div>
        <div class="analysis-card" style="border-left-color: #2e7d32;">
            <small>ช่วงกลางคืน (22:00 เป็นต้นไป)</small><br>
            <b>โหลดเพิ่มขึ้นสะสม: +{night_load_increase:.1f} kW</b><br>
            <p style="font-size:0.8rem; color:gray;">(จาก EV Charger {len(ev_only)} ราย)</p>
        </div>
        """, unsafe_allow_html=True)
        
        balance_factor = night_load_increase - avg_day_load_reduction
        status_color = "red" if balance_factor > 0 else "green"
        st.warning(f"**Grid Balance:** {'โหลดกลางคืนสูงกว่า' if balance_factor > 0 else 'โหลดกลางวันลดลงมากกว่า'} {abs(balance_factor):.1f} kW")
        st.info("💡 แนะนำให้เสริมกำลังหม้อแปลงในจุดที่มีความหนาแน่นสีเขียวเข้มเพื่อรองรับ EV Peak ตอน 22:00 น.")

    with col_map:
        view_state = pdk.ViewState(latitude=16.7115, longitude=103.7477, zoom=13, pitch=45)

        # Layers
        solar_heatmap = pdk.Layer(
            "HeatmapLayer", solar_only, get_position="[lon, lat]", get_weight="weight",
            radius_pixels=50, intensity=0.8, threshold=0.05,
            color_range=[[255,255,178],[254,178,76],[240,59,32],[189,0,38]] # ส้ม-แดง
        )

        ev_heatmap = pdk.Layer(
            "HeatmapLayer", ev_only, get_position="[lon, lat]", get_weight="weight",
            radius_pixels=50, intensity=0.8, threshold=0.05,
            color_range=[[237,248,233],[116,196,118],[0,109,44]] # เขียว
        )

        scatterplot = pdk.Layer(
            "ScatterplotLayer", grid_df, get_position="[lon, lat]",
            get_fill_color="color_rgb", get_line_color="line_color",
            get_radius=50, line_width_min_pixels=2, pickable=True
        )

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v10",
            initial_view_state=view_state,
            layers=[solar_heatmap, ev_heatmap, scatterplot],
            tooltip={"text": "{id}\nประเภท: {type}\nขนาด: {capacity_kw} kW\nคลิกเพื่อดู Google Maps"}
        ))

    # Legend & Google Maps Instructions
    st.markdown("""
    <div style="display: flex; gap: 10px; margin-top: 10px;">
        <div class="legend-box"><span style="color: #FF4500;">●</span> จุดติดตั้ง Solar (กลางวันช่วยลดโหลด)</div>
        <div class="legend-box"><span style="color: #39FF14;">●</span> จุดขอ EV (22:00 น. ดึงไฟพีค)</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📍 รายละเอียดจุดติดตั้งและลิงก์นำทาง")
    
    # ตารางพร้อมลิงก์ Google Maps
    display_df = grid_df[['id', 'type', 'capacity_kw', 'gmaps_link']].copy()
    st.dataframe(
        display_df,
        column_config={
            "gmaps_link": st.column_config.LinkColumn("เปิด Google Maps", display_text="ดูแผนที่ 🗺️")
        },
        use_container_width=True
    )

st.divider()
st.caption("Solar Assistant v6.5 | Infrastructure Map & Balance Analysis System")
