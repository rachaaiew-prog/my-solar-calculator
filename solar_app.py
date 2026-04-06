import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse
import pydeck as pdk

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Solar Assistant | วิเคราะห์ระบบโซลาร์เซลล์",
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

# --- ข้อมูลจำลอง Map Data (รวม 20 รายการ - อ.สมเด็จ จ.กาฬสินธุ์) ---
def get_simulated_map_data():
    # พิกัดศูนย์กลาง อ.สมเด็จ จ.กาฬสินธุ์
    base_lat, base_lon = 16.7115, 103.7477
    
    # จำลองข้อมูล Solar (10 รายการ - สีแดง)
    solar_data = pd.DataFrame({
        'lat': base_lat + np.random.randn(10) * 0.008,
        'lon': base_lon + np.random.randn(10) * 0.008,
        'capacity_kw': np.random.choice([3, 5, 10], 10),
        'type': 'Solar PV',
        'color_rgb': [[255, 75, 75, 200]] * 10
    })
    
    # จำลองข้อมูล EV วงจรที่ 2 (10 รายการ - สีเขียว)
    ev_data = pd.DataFrame({
        'lat': base_lat + np.random.randn(10) * 0.008,
        'lon': base_lon + np.random.randn(10) * 0.008,
        'capacity_kw': np.random.choice([7, 11], 10),
        'type': 'EV Circuit 2',
        'color_rgb': [[46, 125, 50, 230]] * 10
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
    .confirm-btn {
        display: block; width: 100%; text-align: center;
        background: #2e7d32; color: white !important;
        padding: 15px; border-radius: 12px; text-decoration: none;
        font-weight: bold; margin-top: 15px; font-size: 1.1rem;
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
                <p style="font-size:1.1rem; opacity:0.9;">วิเคราะห์จุดคุ้มทุนและวางแผนระบบจำหน่ายไฟฟ้า (อ.สมเด็จ)</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["💡 วิเคราะห์การติดตั้ง", "🗺️ Grid Planning (Solar + EV)"])

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

        m1, m2, m3 = st.columns(3)
        m1.metric("ขนาดแนะนำ", f"{pkg['inverter_size']} kW")
        m2.metric("งบประมาณ", f"{pkg['price']:,} บาท")
        m3.metric("คืนทุนใน", f"{payback:.1f} ปี")

        st.markdown(f'<a href="https://peasolar.pea.co.th/our-products/" target="_blank" class="product-btn">🔍 ดูรายละเอียดแพ็กเกจ {pkg["inverter_size"]}kW</a>', unsafe_allow_html=True)
    else:
        st.info("👆 กรุณาเลือกเครื่องใช้ไฟฟ้าเพื่อเริ่มการวิเคราะห์")

with tab2:
    st.markdown("### 🗺️ แผนที่จุดติดตั้ง Solar & EV (อ.สมเด็จ)")
    st.write("แสดงข้อมูลจำลองผู้ยื่นขอขนานไฟ (20 รายการ) เพื่อวิเคราะห์ภาระหม้อแปลง")
    
    map_data = get_simulated_map_data()
    
    # แสดงแผนที่ด้วย Pydeck
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=16.7115,
            longitude=103.7477,
            zoom=14,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=map_data,
                get_position='[lon, lat]',
                get_color='color_rgb',
                get_radius=60,
                pickable=True
            ),
        ],
        tooltip={"text": "ประเภท: {type}\nขนาด: {capacity_kw} kW"}
    ))

    st.markdown("""
        <div style="display: flex; gap: 20px; background: white; padding: 10px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 15px; height: 15px; background: #FF4B4B; border-radius: 50%;"></div>
                <span>Solar PV (10 ราย)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 15px; height: 15px; background: #2E7D32; border-radius: 50%;"></div>
                <span>EV วงจรที่ 2 (10 ราย)</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # ส่วนวิเคราะห์หม้อแปลง
    st.markdown("### ⚡ วิเคราะห์ภาระหม้อแปลงในพื้นที่")
    col_t1, col_t2 = st.columns([1, 2])
    
    with col_t1:
        tr_size = st.selectbox("เลือกขนาดหม้อแปลง (kVA)", [50, 100, 160, 250, 315, 500])
        safe_limit = tr_size * 0.8
        
    with col_t2:
        total_pv = map_data[map_data['type'] == 'Solar PV']['capacity_kw'].sum()
        total_ev = map_data[map_data['type'] == 'EV Circuit 2']['capacity_kw'].sum()
        
        c_a, c_b = st.columns(2)
        c_a.metric("Total Solar Capacity", f"{total_pv} kW")
        c_b.metric("Total EV Load", f"{total_ev} kW")
        
        if total_ev > safe_limit:
            st.error(f"⚠️ คำเตือน: โหลด EV ({total_ev} kW) เกินเกณฑ์ปลอดภัยของหม้อแปลง ({safe_limit:.1f} kVA)")
        else:
            st.success(f"✅ หม้อแปลงขนาด {tr_size} kVA รองรับการใช้งานในโซนนี้ได้")

    st.markdown("#### รายละเอียดผู้ยื่นคำขอ (จำลอง 20 รายการ)")
    st.dataframe(map_data[['type', 'capacity_kw', 'lat', 'lon']], use_container_width=True)

st.divider()
st.caption("Solar Assistant v6.2 | Focus Group: 20 Samples @ Somdet District")
