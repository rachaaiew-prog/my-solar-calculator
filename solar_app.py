import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse

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

# --- ข้อมูลจำลอง Heat Map (ข้อมูลผู้ยื่นขอขนานไฟ) ---
def get_simulated_solar_data():
    # จำลองตำแหน่งในเขตกรุงเทพฯ/ปริมณฑล หรือพื้นที่ตัวอย่าง
    base_lat, base_lon = 13.7563, 100.5018
    data = pd.DataFrame({
        'lat': base_lat + np.random.randn(50) * 0.02,
        'lon': base_lon + np.random.randn(50) * 0.02,
        'capacity_kw': np.random.choice([3, 5, 10, 20], 50),
        'status': np.random.choice(['Approved', 'Pending', 'Connected'], 50)
    })
    return data

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
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
st.markdown(f"""
    <div class="app-header">
        <div style="display: flex; align-items: center; gap: 2rem;">
            <img src="https://lh3.googleusercontent.com/d/1RDUD8icYRqrf1s_HuwCsKABQjoD8OP0n" style="width:120px; border-radius:10px;">
            <div>
                <h1 style="color:white; margin:0; font-size:2.5rem;">Solar Assistant Pro</h1>
                <p style="font-size:1.1rem; opacity:0.9;">วิเคราะห์จุดคุ้มทุนและแผนการลงทุนโซลาร์เซลล์อัจฉริยะ (PEA Solar)</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Tab System ---
tab1, tab2 = st.tabs(["💡 วิเคราะห์การติดตั้ง", "🗺️ แผนที่ความหนาแน่น (Heat Map)"])

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
        with c1: 
            chosen = st.checkbox(dev['item'], key=f"u_{i}")
        with c2: 
            qty = st.number_input("จำนวน", min_value=0, value=0, key=f"q_{i}", label_visibility="collapsed")
        with c3: 
            hrs = st.number_input("ชม.", min_value=0, max_value=24, value=0, key=f"h_{i}", label_visibility="collapsed")
        
        if chosen and qty > 0: 
            total_daily_wh += (dev['watts'] * qty * hrs)

    units_per_day = total_daily_wh / 1000

    # --- การคำนวณและแสดงผล ---
    if units_per_day > 0:
        st.divider()
        # คำนวณหาขนาดที่เหมาะสม
        eff_factor = 1 - system_loss
        target_kw = units_per_day / (sun_hours * eff_factor)
        
        is_1p = phase == "1 Phase"
        available = [p for p in pea_packages if ((is_1p and "1 Phase" in p['name']) or (not is_1p and "3 Phase" in p['name']))]
        pkg = next((p for p in available if p['inverter_size'] >= target_kw), available[-1])
        
        # ตัวเลขทางการเงิน
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
        st.info(f"💡 คุณจะเริ่ม 'ใช้ไฟฟรี' และมีกำไรหลังจากปีที่ {payback:.1f} เป็นต้นไป")

        # ปุ่มลิงก์ผลิตภัณฑ์
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
                    entries = {
                        "name": "entry.1381098045", 
                        "phone": "entry.225801865",
                        "addr": "entry.1907655311"
                    }
                    
                    info_summary = f"ระบบ {pkg['inverter_size']}kW | ใช้ไฟกลางวัน {units_per_day:.2f} หน่วย | {addr}"
                    params = {
                        entries["name"]: name,
                        entries["phone"]: phone,
                        entries["addr"]: info_summary
                    }
                    
                    final_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/viewform?" + urllib.parse.urlencode(params)
                    st.success("สร้างลิงก์ข้อมูลของคุณเรียบร้อยแล้ว!")
                    st.markdown(f'<a href="{final_url}" target="_blank" class="confirm-btn">✅ กดยืนยันเพื่อส่งข้อมูลให้เจ้าหน้าที่</a>', unsafe_allow_html=True)
                else:
                    st.error("กรุณากรอกข้อมูลที่จำเป็น (*) ให้ครบถ้วน")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👆 กรุณาเลือกรายการเครื่องใช้ไฟฟ้าและระบุเวลาที่ใช้งาน เพื่อให้ระบบเริ่มการวิเคราะห์")

with tab2:
    st.markdown("### 🗺️ Solar PV Density & Transformer Planning")
    st.write("แผนที่แสดงความหนาแน่นของผู้ยื่นขอขนานไฟโซลาร์เซลล์ เพื่อวิเคราะห์ผลกระทบต่อหม้อแปลงในระบบจำหน่าย")
    
    # ดึงข้อมูลจำลอง
    solar_map_data = get_simulated_solar_data()
    
    # แสดงแผนที่
    st.map(solar_map_data)
    
    st.divider()
    
    # ส่วนวิเคราะห์หม้อแปลง
    st.markdown("### ⚡ Transformer Load Analysis (Simulation)")
    col_t1, col_t2 = st.columns([1, 2])
    
    with col_t1:
        st.write("**ตั้งค่าหม้อแปลงจำหน่าย**")
        tr_size = st.selectbox("ขนาดหม้อแปลง (kVA)", [50, 100, 160, 250, 315, 400, 500])
        safe_factor = st.slider("Safety Factor (%)", 50, 100, 80)
        max_pv_limit = (tr_size * (safe_factor/100)) * 0.7  # ประมาณการรับ PV ไม่เกิน 70% ของโหลดปลอดภัย
        
    with col_t2:
        # คำนวณสรุปข้อมูลในพื้นที่แผนที่
        total_requested_pv = solar_map_data['capacity_kw'].sum()
        status_counts = solar_map_data['status'].value_counts()
        
        st.write("**ผลวิเคราะห์ภาระระบบจำหน่าย**")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("จำนวนผู้ยื่นขอ", len(solar_map_data))
        sc2.metric("Total PV Capacity", f"{total_requested_pv} kW")
        sc3.metric("Limit (Estimate)", f"{max_pv_limit:.1f} kW")
        
        if total_requested_pv > max_pv_limit:
            st.warning(f"⚠️ คำเตือน: ปริมาณ Solar PV รวม ({total_requested_pv} kW) เกินขีดจำกัดที่แนะนำสำหรับหม้อแปลงขนาด {tr_size} kVA ในโซนนี้")
        else:
            st.success(f"✅ ข้อมูลเบื้องต้น: หม้อแปลงขนาด {tr_size} kVA ยังสามารถรองรับปริมาณ Solar PV ในโซนนี้ได้")

    st.markdown("#### รายละเอียดคำร้องขอนำเข้า (Grid Connection Requests)")
    st.dataframe(solar_map_data, use_container_width=True)

st.divider()
st.caption("Solar Assistant v5.9 | Grid Planning & Heat Map Integration")
