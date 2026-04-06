import streamlit as st
import pandas as pd
import math
from datetime import datetime

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

# --- Custom CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f1eeff; }
    .app-header {
        background: linear-gradient(135deg, #4a148c 0%, #7b1fa2 50%, #9c27b0 100%);
        padding: 2.5rem; color: white; border-radius: 28px; margin-bottom: 2.5rem;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 15px 35px rgba(74, 20, 140, 0.25);
    }
    .header-left { display: flex; align-items: center; gap: 2rem; }
    .pea-logo { width: 180px; height: auto; filter: drop-shadow(0px 4px 8px rgba(0,0,0,0.3)); }
    .header-text h1 { color: white !important; margin: 0; font-size: 2.5rem; }
    .package-card {
        background-color: white; padding: 2rem; border-radius: 24px;
        border-left: 12px solid #6a11cb; margin-bottom: 2rem;
        box-shadow: 0 12px 30px rgba(106, 17, 203, 0.1);
    }
    .registration-form {
        background-color: #ffffff; padding: 25px; border-radius: 20px;
        border: 1px solid #e1bee7; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
logo_url = "https://lh3.googleusercontent.com/d/1RDUD8icYRqrf1s_HuwCsKABQjoD8OP0n"
st.markdown(f"""
    <div class="app-header">
        <div class="header-left">
            <img src="{logo_url}" class="pea-logo" alt="PEA Logo">
            <div class="header-text">
                <h1>Solar Assistant</h1>
                <p>ระบบวิเคราะห์การลงทุนโซลาร์เซลล์อัจฉริยะ (PEA Solar Standard)</p>
            </div>
        </div>
        <div class="header-right">
            <svg width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🔮 ตั้งค่าระบบ")
    unit_price = st.number_input("ค่าไฟเฉลี่ย (บาท/หน่วย)", min_value=1.0, value=4.7, step=0.1)
    phase_type = st.radio("ระบบไฟฟ้าที่บ้าน", ["1 Phase (220V)", "3 Phase (380V)"])
    st.divider()
    sun_hours = st.slider("ชั่วโมงแดดเฉลี่ย/วัน", 3.0, 6.0, 4.2)
    system_loss = st.slider("System Loss (%)", 5, 30, 15) / 100

# --- ขั้นตอนที่ 1: ประมาณการโหลด ---
st.markdown("### 📝 1. ระบุการใช้ไฟฟ้าช่วงกลางวัน")
device_list = [
    {"item": "แอร์ 9,000 BTU", "watts": 800, "icon": "❄️"},
    {"item": "แอร์ 12,000 BTU", "watts": 1100, "icon": "❄️"},
    {"item": "แอร์ 18,000 BTU", "watts": 1600, "icon": "❄️"},
    {"item": "Wall Charger 7 kW", "watts": 7000, "icon": "🔌"},
    {"item": "ตู้เย็น/อื่นๆ", "watts": 300, "icon": "🧊"},
]

total_daily_wh = 0
for i, dev in enumerate(device_list):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: chosen = st.checkbox(f"{dev['icon']} {dev['item']}", key=f"u_{i}")
    with c2: qty = st.number_input("จำนวน", min_value=0, value=0, key=f"q_{i}")
    with c3: hrs = st.number_input("ชม.", min_value=0, max_value=24, value=0, key=f"h_{i}")
    if chosen and qty > 0: total_daily_wh += (dev['watts'] * qty * hrs)

units_per_day = total_daily_wh / 1000

# --- ขั้นตอนที่ 2: วิเคราะห์และบันทึกข้อมูล ---
if units_per_day > 0:
    st.divider()
    st.markdown("### 📊 2. ผลการวิเคราะห์และลงทะเบียน")
    
    eff_factor = 1 - system_loss
    target_kw = units_per_day / (sun_hours * eff_factor)
    
    is_1phase = phase_type == "1 Phase (220V)"
    suggested_pkg = next((p for p in pea_packages if p['inverter_size'] >= target_kw and ((is_1phase and "1 Phase" in p['name']) or (not is_1phase and "3 Phase" in p['name']))), pea_packages[-1])

    st.markdown(f"""
    <div class="package-card">
        <h2 style='color:#4a148c;'>ขนาดที่แนะนำ: {suggested_pkg['inverter_size']} kW</h2>
        <p>แพ็กเกจ: {suggested_pkg['name']}</p>
        <p>งบประมาณโดยประมาณ: {suggested_pkg['price']:,} บาท</p>
    </div>
    """, unsafe_allow_html=True)

    # --- ฟอร์มเก็บข้อมูลลง Google Sheet ---
    st.markdown('<div class="registration-form">', unsafe_allow_html=True)
    st.subheader("📥 บันทึกข้อมูลผู้สนใจติดตั้ง")
    
    with st.form("data_form"):
        col1, col2 = st.columns(2)
        with col1:
            fname = st.text_input("ชื่อ")
            lname = st.text_input("นามสกุล")
        with col2:
            phone = st.text_input("เบอร์โทรศัพท์")
            location = st.text_input("พิกัด (Lat, Long)", placeholder="เช่น 13.7563, 100.5018")
        
        submit_btn = st.form_submit_button("บันทึกข้อมูลลงฐานข้อมูล")
        
        if submit_btn:
            if fname and phone:
                # จำลองการจัดการลำดับ (ในระบบจริงจะดึงจาก DB)
                current_id = 1 
                
                new_data = {
                    "ที่": current_id,
                    "วันที่บันทึก": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "ชื่อ-สกุล": f"{fname} {lname}",
                    "เบอร์โทร": phone,
                    "พิกัด": location,
                    "ขนาดที่แนะนำ (kW)": suggested_pkg['inverter_size'],
                    "แพ็กเกจ": suggested_pkg['name']
                }
                
                st.success(f"✅ บันทึกข้อมูลคุณ {fname} เรียบร้อยแล้ว!")
                st.write("**Preview ข้อมูลที่จะส่งไปยัง Google Sheet:**")
                st.json(new_data)
                st.info(f"🔗 [คลิกเพื่อเปิดดู Google Sheet ของคุณ](https://docs.google.com/spreadsheets/d/1xpPS8l2ySEKJx4_2u--loOzkne8CR_4zOOZiwXLSlxk/edit?usp=sharing)")
            else:
                st.error("กรุณากรอกข้อมูล ชื่อ และ เบอร์โทร ให้ครบถ้วน")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.warning("👈 กรุณาเลือกเครื่องใช้ไฟฟ้าเพื่อเริ่มการวิเคราะห์")

st.divider()
st.markdown("<p style='text-align:center; color:#999;'>Solar Assistant v3.0 | บันทึกข้อมูลลงฐานข้อมูล Google Sheet</p>", unsafe_allow_html=True)
