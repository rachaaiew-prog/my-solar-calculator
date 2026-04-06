import streamlit as st
import pandas as pd
import math
from datetime import datetime
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
    .header-left { display: flex; align-items: center; gap: 2rem; }
    .pea-logo { width: 180px; height: auto; filter: drop-shadow(0px 4px 8px rgba(0,0,0,0.3)); }
    .header-text h1 { color: white !important; margin: 0; font-size: 2.5rem; letter-spacing: 1px; }
    
    .package-card {
        background-color: white; padding: 2rem; border-radius: 24px;
        border-left: 12px solid #6a11cb; margin-bottom: 2rem;
        box-shadow: 0 12px 30px rgba(106, 17, 203, 0.1);
    }
    
    .metric-container {
        background: white; padding: 1.5rem; border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center;
    }

    .registration-form {
        background-color: #ffffff; padding: 25px; border-radius: 20px;
        border: 2px solid #e1bee7; margin-top: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }
    
    .map-btn {
        display: inline-block;
        padding: 8px 15px;
        background-color: #4a148c;
        color: white !important;
        border-radius: 8px;
        text-decoration: none;
        font-size: 0.9rem;
        margin-top: 10px;
        border: none;
        cursor: pointer;
    }
    
    .product-btn {
        display: block;
        width: 100%;
        text-align: center;
        background: linear-gradient(90deg, #9c27b0, #7b1fa2);
        color: white !important;
        padding: 18px;
        border-radius: 15px;
        text-decoration: none;
        font-weight: bold;
        font-size: 1.1rem;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(156, 39, 176, 0.3);
        transition: transform 0.2s;
    }
    .product-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(156, 39, 176, 0.4); }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
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
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                <circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
            </svg>
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
st.markdown("### 📝 1. ระบุการใช้ไฟฟ้าช่วงกลางวัน (09:00 - 16:00)")
device_list = [
    {"item": "แอร์ 9,000 BTU", "watts": 800, "icon": "❄️"},
    {"item": "แอร์ 12,000 BTU", "watts": 1100, "icon": "❄️"},
    {"item": "แอร์ 18,000 BTU", "watts": 1600, "icon": "❄️"},
    {"item": "แอร์ 24,000 BTU", "watts": 2200, "icon": "❄️"},
    {"item": "ทีวี (LED TV)", "watts": 150, "icon": "📺"},
    {"item": "ปั๊มน้ำ (Home Pump)", "watts": 350, "icon": "💧"},
    {"item": "Wall Charger 7 kW", "watts": 7000, "icon": "🔌"},
    {"item": "ตู้เย็น/อื่นๆ", "watts": 300, "icon": "🧊"},
]

total_daily_wh = 0
col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
with col_h1: st.markdown("**รายการ**")
with col_h2: st.markdown("**จำนวน**")
with col_h3: st.markdown("**ชม./วัน**")

for i, dev in enumerate(device_list):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: chosen = st.checkbox(f"{dev['icon']} {dev['item']}", key=f"u_{i}")
    with c2: qty = st.number_input("จำนวน", min_value=0, value=0, key=f"q_{i}", label_visibility="collapsed")
    with c3: hrs = st.number_input("ชม.", min_value=0, max_value=24, value=0, key=f"h_{i}", label_visibility="collapsed")
    if chosen and qty > 0: total_daily_wh += (dev['watts'] * qty * hrs)

units_per_day = total_daily_wh / 1000

# --- ขั้นตอนที่ 2: วิเคราะห์และบันทึกข้อมูล ---
if units_per_day > 0:
    st.divider()
    st.markdown("### 📊 2. ผลการวิเคราะห์และกราฟจุดคุ้มทุน")
    
    eff_factor = 1 - system_loss
    target_kw = units_per_day / (sun_hours * eff_factor)
    is_1phase = phase_type == "1 Phase (220V)"
    available_pkgs = [p for p in pea_packages if ((is_1phase and "1 Phase" in p['name']) or (not is_1phase and "3 Phase" in p['name']))]
    
    # เลือกแพ็กเกจที่เหมาะสมที่สุด (Inverter ต้องใหญ่กว่าหรือเท่ากับ Target)
    suggested_pkg = next((p for p in available_pkgs if p['inverter_size'] >= target_kw), available_pkgs[-1])

    # --- คำนวณทางการเงิน ---
    yearly_saving = suggested_pkg['pv_size'] * sun_hours * eff_factor * unit_price * 365
    payback_years = suggested_pkg['price'] / yearly_saving
    total_saving_25y = (yearly_saving * 25) - suggested_pkg['price']

    # แสดงผล Metric
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("ขนาดแนะนำ", f"{suggested_pkg['inverter_size']} kW", help="ขนาด Inverter ที่เหมาะสมกับโหลดของคุณ")
    with m2: st.metric("งบประมาณเบื้องต้น", f"{suggested_pkg['price']:,} บาท")
    with m3: st.metric("ระยะคืนทุน", f"{payback_years:.1f} ปี", delta_color="inverse")

    # --- กราฟจุดคุ้มทุน ---
    st.markdown("#### วิเคราะห์จุดคุ้มทุนและการประหยัดสะสม (Break-even Analysis)")
    years = list(range(0, 26))
    investment_line = [suggested_pkg['price']] * 26
    savings_line = [yearly_saving * y for y in years]
    
    chart_df = pd.DataFrame({
        "ปีที่": years,
        "เงินลงทุนสะสม (บาท)": investment_line,
        "ประหยัดไฟสะสม (บาท)": savings_line
    }).set_index("ปีที่")
    
    st.line_chart(chart_df, color=["#ff4b4b", "#29b5e8"])
    st.caption(f"กราฟแสดงจุดที่ 'ประหยัดไฟสะสม' ตัดกับ 'เงินลงทุน' คือปีที่ {payback_years:.1f} ซึ่งเป็นจุดคุ้มทุนของคุณ")

    # --- รายละเอียดแพ็กเกจและลิงก์ผลิตภัณฑ์ ---
    st.markdown(f"""
    <div class="package-card">
        <h3 style='color:#4a148c; margin-top:0;'>รายละเอียดแพ็กเกจที่แนะนำ</h3>
        <p><b>ชื่อแพ็กเกจ:</b> {suggested_pkg['name']}</p>
        <p><b>ขนาดแผงโซลาร์:</b> {suggested_pkg['pv_size']} kWp</p>
        <p><b>ประหยัดไฟโดยประมาณ:</b> {yearly_saving/12:,.2f} บาท/เดือน</p>
        <p><b>ผลตอบแทนรวม 25 ปี (กำไร):</b> <span style="color:#2e7d32; font-weight:bold;">{total_saving_25y:,.0f} บาท</span></p>
        <hr style="border:0.5px solid #eee;">
        <p style="font-size:0.9rem; color:#666;">สนใจดูรายละเอียดอุปกรณ์ แผงโซลาร์ และอินเวอร์เตอร์ที่ใช้ในแต่ละขนาด</p>
        <a href="https://peasolar.pea.co.th/our-products/" target="_blank" class="product-btn">
            🔍 คลิกเพื่อดูข้อมูลผลิตภัณฑ์ของเราเพิ่มเติม
        </a>
    </div>
    """, unsafe_allow_html=True)

    # --- ฟอร์มลงทะเบียน ---
    st.markdown('<div class="registration-form">', unsafe_allow_html=True)
    st.subheader("📥 บันทึกข้อมูลและขอใบเสนอราคา")
    
    with st.form("solar_form"):
        f1, f2 = st.columns(2)
        with f1:
            fname = st.text_input("ชื่อ-นามสกุล *")
            phone = st.text_input("เบอร์โทรศัพท์ *")
        with f2:
            lat_long = st.text_input("พิกัด (Lat, Long)", placeholder="คัดลอกจาก Google Maps")
            st.markdown('<a href="https://www.google.com/maps" target="_blank" class="map-btn">📍 ค้นหาบนแผนที่</a>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button("🚀 บันทึกข้อมูล")
        
        if submitted:
            if fname and phone:
                # การส่งข้อมูลผ่าน Google Form Integration
                YOUR_FORM_ID = "1FAIpQLScyYm6-rV2x9VvU6z-Y_p1Kj4p7y_oW_8Xj_9Xj_9Xj_9Xj_A" 
                entry_ids = {
                    "name": "entry.1000001",
                    "phone": "entry.1000002",
                    "pkg": "entry.1000003",
                    "loc": "entry.1000004"
                }
                pkg_data = f"{suggested_pkg['name']} ({suggested_pkg['inverter_size']}kW)"
                params = {
                    entry_ids["name"]: fname,
                    entry_ids["phone"]: phone,
                    entry_ids["pkg"]: pkg_data,
                    entry_ids["loc"]: lat_long
                }
                
                form_url = f"https://docs.google.com/forms/d/e/{YOUR_FORM_ID}/formResponse?submit=Submit&" + urllib.parse.urlencode(params)
                
                st.success(f"บันทึกข้อมูลเบื้องต้นเรียบร้อยแล้ว!")
                st.balloons()
                st.markdown(f"""
                <div style="background-color:#e8f5e9; padding:15px; border-radius:12px; text-align:center;">
                    <a href="{form_url}" target="_blank" style="color:#2e7d32; font-weight:bold; text-decoration:none;">
                        👉 กดยืนยันเพื่อบันทึกข้อมูลเข้า Google Sheet
                    </a>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("กรุณากรอกชื่อและเบอร์โทรศัพท์")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.warning("👈 กรุณาเลือกเครื่องใช้ไฟฟ้าทางด้านซ้ายเพื่อประเมินจุดคุ้มทุน")

st.divider()
st.markdown("<p style='text-align:center; color:#999;'>Solar Assistant v4.6 | วิเคราะห์การคืนทุนและข้อมูลผลิตภัณฑ์ PEA Solar</p>", unsafe_allow_html=True)
