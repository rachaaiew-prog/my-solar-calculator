import streamlit as st
import pandas as pd
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
    
    .registration-form {
        background-color: #ffffff; padding: 25px; border-radius: 20px;
        border: 2px solid #e1bee7; margin-top: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    
    .confirm-btn {
        display: block; width: 100%; text-align: center;
        background: #2e7d32; color: white !important;
        padding: 18px; border-radius: 12px; text-decoration: none;
        font-weight: bold; margin-top: 15px; font-size: 1.2rem;
        transition: 0.3s;
    }
    .confirm-btn:hover { background: #1b5e20; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
st.markdown(f"""
    <div class="app-header">
        <div style="display: flex; align-items: center; gap: 2rem;">
            <img src="https://lh3.googleusercontent.com/d/1RDUD8icYRqrf1s_HuwCsKABQjoD8OP0n" style="width:150px;">
            <div>
                <h1 style="color:white; margin:0;">Solar Assistant</h1>
                <p>ระบบวิเคราะห์การลงทุนโซลาร์เซลล์อัจฉริยะ (PEA Solar Standard)</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ ตั้งระบบ")
    unit_price = st.number_input("ค่าไฟเฉลี่ย (บาท/หน่วย)", value=4.70)
    phase = st.radio("ระบบไฟฟ้าที่บ้าน", ["1 Phase (220V)", "3 Phase (380V)"])
    st.divider()
    sun_hours = st.slider("ชั่วโมงแดดเฉลี่ย/วัน", 3.0, 6.0, 4.20)
    system_loss = st.slider("System Loss (%)", 5, 30, 15) / 100

# --- 1. ระบุการใช้ไฟฟ้าช่วงกลางวัน ---
st.markdown("### 📝 1. ระบุการใช้ไฟฟ้าช่วงกลางวัน")
device_list = [
    {"item": "แอร์ 9,000 BTU", "watts": 800},
    {"item": "แอร์ 12,000 BTU", "watts": 1100},
    {"item": "แอร์ 18,000 BTU", "watts": 1600},
    {"item": "Wall Charger 7 kW", "watts": 7000},
    {"item": "ตู้เย็น/อื่นๆ", "watts": 300},
]

total_daily_wh = 0
col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
with col_h1: st.markdown("**รายการ**")
with col_h2: st.markdown("**จำนวน**")
with col_h3: st.markdown("**ชม.**")

for i, dev in enumerate(device_list):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: chosen = st.checkbox(dev['item'], key=f"u_{i}")
    with c2: qty = st.number_input("จำนวน", min_value=0, value=0, key=f"q_{i}", label_visibility="collapsed")
    with c3: hrs = st.number_input("ชม.", min_value=0, max_value=24, value=0, key=f"h_{i}", label_visibility="collapsed")
    if chosen and qty > 0: total_daily_wh += (dev['watts'] * qty * hrs)

units_per_day = total_daily_wh / 1000

if units_per_day > 0:
    st.divider()
    # คำนวณแพ็กเกจ
    eff_factor = 1 - system_loss
    target_kw = units_per_day / (sun_hours * eff_factor)
    is_1p = "1 Phase" in phase
    available = [p for p in pea_packages if ((is_1p and "1 Phase" in p['name']) or (not is_1p and "3 Phase" in p['name']))]
    pkg = next((p for p in available if p['inverter_size'] >= target_kw), available[-1])
    
    # คำนวณคืนทุน
    saving_year = pkg['pv_size'] * sun_hours * eff_factor * unit_price * 365
    payback = pkg['price'] / saving_year

    # แสดงผล Metric
    m1, m2, m3 = st.columns(3)
    m1.metric("ขนาดแนะนำ", f"{pkg['inverter_size']} kW")
    m2.metric("งบประมาณ", f"{pkg['price']:,} บาท")
    m3.metric("ระยะคืนทุน", f"{payback:.1f} ปี")

    # --- ส่วนการบันทึกข้อมูล ---
    st.markdown('<div class="registration-form">', unsafe_allow_html=True)
    st.subheader("📥 บันทึกข้อมูลและขอใบเสนอราคา")
    
    with st.form("solar_form_final"):
        f_name = st.text_input("ชื่อ *")
        l_name = st.text_input("นามสกุล *")
        phone = st.text_input("เบอร์โทรศัพท์ *")
        lat_long = st.text_input("พิกัด (lat, long)")
        
        submitted = st.form_submit_button("🚀 สร้างลิงก์บันทึกข้อมูล")
        
        if submitted:
            if f_name and phone:
                # ข้อมูลจาก Google Form ของคุณ
                FORM_ID = "1FAIpQLSclm-IwbIb85XoWuO_P8C-o8qHZqyYP4t7GdVz7cc6LpcWgog"
                
                # อัปเดต entry ID ตามที่เห็นจาก Inspect (ตัวอย่างค่าที่น่าจะเป็นไปได้)
                entries = {
                    "pkg_recommend": "entry.1983309523", # ขนาดที่แนะนำติดตั้ง (จากรูปที่คุณส่งมา)
                    "location": "entry.1907655311",      # พิกัด(lat,long)
                    "first_name": "entry.1381098045",    # ชื่อ
                    "last_name": "entry.17058331",     # สกุล
                    "phone_no": "entry.225801865"       # เบอร์โทร
                }
                
                pkg_info = f"{pkg['name']} ({pkg['inverter_size']}kW)"
                params = {
                    entries["pkg_recommend"]: pkg_info,
                    entries["location"]: lat_long,
                    entries["first_name"]: f_name,
                    entries["last_name"]: l_name,
                    entries["phone_no"]: phone
                }
                
                form_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/viewform?" + urllib.parse.urlencode(params)
                
                st.success("เตรียมข้อมูลพร้อมส่งแล้ว!")
                st.markdown(f"""
                    <div style="background:#f1f8e9; padding:20px; border-radius:15px; border:1px solid #c8e6c9; text-align:center;">
                        <p style="font-size:1.1rem; color:#2e7d32;"><b>สร้างลิงก์สำเร็จ!</b></p>
                        <p>กรุณากดปุ่มสีเขียวด้านล่างเพื่อเปิดหน้ายืนยันข้อมูลครับ</p>
                        <a href="{form_url}" target="_blank" class="confirm-btn">✅ กดยืนยันการส่งข้อมูล</a>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("กรุณากรอกชื่อและเบอร์โทรศัพท์ให้ครบถ้วน")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("👆 กรุณาเลือกเครื่องใช้ไฟฟ้าเพื่อเริ่มการวิเคราะห์")

st.divider()
st.caption("Solar Assistant v5.5 | Google Form Integrated with Detected IDs")
