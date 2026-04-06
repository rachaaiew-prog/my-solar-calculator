import streamlit as st
import pandas as pd
import math

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Solar Calculate Pro | ระบบวิเคราะห์โซลาร์เซลล์",
    page_icon="☀️",
    layout="wide"
)

# --- ข้อมูลแพ็กเกจมาตรฐาน PEA Solar (ราคาประมาณการรวมติดตั้งและขออนุญาต) ---
pea_packages = [
    {"name": "Micro Solar (1 Phase)", "size": 3.3, "price": 145000, "desc": "เหมาะสำหรับบ้านขนาดเล็ก แอร์ 1-2 เครื่อง"},
    {"name": "Home Solar (1 Phase)", "size": 5.5, "price": 225000, "desc": "เหมาะสำหรับบ้านขนาดกลาง แอร์ 2-3 เครื่อง"},
    {"name": "Premium Solar (3 Phase)", "size": 5.5, "price": 235000, "desc": "สำหรับบ้านไฟ 3 เฟส แอร์ 2-3 เครื่อง"},
    {"name": "Business Solar (3 Phase)", "size": 10.0, "price": 390000, "desc": "ออฟฟิศขนาดกลาง แอร์ 4-6 เครื่อง"},
    {"name": "Max Solar (3 Phase)", "size": 20.0, "price": 750000, "desc": "อาคารพาณิชย์ หรือโรงงานขนาดเล็ก"}
]

# --- CSS ตกแต่งหน้าจอ ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .app-header {
        background-color: #004d40;
        padding: 2.5rem;
        color: white;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .package-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 8px solid #ffc107;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- ส่วนหัวของโปรแกรม ---
st.markdown("""
    <div class="app-header">
        <h1>☀️ Solar PV Investment Analyzer</h1>
        <p>วิเคราะห์โหลดไฟฟ้าด้วยเครื่องใช้ไฟฟ้า และแนะนำแพ็กเกจมาตรฐาน PEA Solar</p>
    </div>
    """, unsafe_allow_html=True)

# --- แถบเมนูด้านข้าง (Sidebar) ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าพื้นฐาน")
    unit_price = st.number_input("ราคาค่าไฟต่อหน่วย (บาท)", min_value=1.0, value=4.7, step=0.1)
    phase_type = st.radio("ระบบไฟฟ้าที่บ้าน", ["1 Phase (220V)", "3 Phase (380V)"])
    
    st.divider()
    st.header("🌍 ปัจจัยการผลิต")
    sun_hours = st.slider("ชั่วโมงแดดผลิตไฟเฉลี่ย/วัน", 3.0, 6.0, 4.2)
    system_loss = st.slider("ความสูญเสียในระบบ (Loss) (%)", 5, 30, 15) / 100
    st.caption("แนะนำ 15% สำหรับการติดตั้งมาตรฐาน")

# --- ขั้นตอนที่ 1: เครื่องคำนวณโหลดไฟฟ้า ---
st.header("📝 1. ประมาณการโหลดไฟฟ้าจากอุปกรณ์")
st.info("ระบุเครื่องใช้ไฟฟ้าที่เปิดใช้งานในช่วงกลางวัน (09:00 - 16:00) เพื่อหาขนาดที่ประหยัดที่สุด")

device_list = [
    {"item": "แอร์ 9,000 BTU (Inverter)", "watts": 800, "icon": "❄️"},
    {"item": "แอร์ 12,000 BTU (Inverter)", "watts": 1100, "icon": "❄️"},
    {"item": "แอร์ 18,000 BTU (Inverter)", "watts": 1600, "icon": "❄️"},
    {"item": "ตู้เย็น (ขนาดกลาง)", "watts": 150, "icon": "🧊"},
    {"item": "ทีวี และเครื่องเสียง", "watts": 120, "icon": "📺"},
    {"item": "พัดลม", "watts": 60, "icon": "🌬️"},
    {"item": "คอมพิวเตอร์ / โน้ตบุ๊ก", "watts": 250, "icon": "💻"},
    {"item": "ปั๊มน้ำ (ทำงานเป็นช่วงๆ)", "watts": 400, "icon": "💧"},
    {"item": "หลอดไฟ LED", "watts": 15, "icon": "💡"},
]

total_daily_wh = 0
col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
with col_h1: st.write("**เครื่องใช้ไฟฟ้า**")
with col_h2: st.write("**จำนวน (เครื่อง)**")
with col_h3: st.write("**ชม./วัน (ช่วงมีแดด)**")

for i, dev in enumerate(device_list):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        is_used = st.checkbox(f"{dev['icon']} {dev['item']}", key=f"use_{i}")
    with c2:
        qty = st.number_input("จำนวน", min_value=0, value=0, key=f"qty_{i}", label_visibility="collapsed")
    with c3:
        hrs = st.number_input("ชม.", min_value=0, max_value=24, value=0, key=f"hrs_{i}", label_visibility="collapsed")
    
    if is_used and qty > 0:
        total_daily_wh += (dev['watts'] * qty * hrs)

units_per_day = total_daily_wh / 1000

# --- ขั้นตอนที่ 2: วิเคราะห์ขนาดและจับคู่แพ็กเกจ ---
if units_per_day > 0:
    st.divider()
    st.header("📊 2. ผลการวิเคราะห์และแพ็กเกจที่แนะนำ")
    
    # คำนวณขนาดที่ควรติดตั้ง (kWp)
    eff_factor = 1 - system_loss
    req_kwp = units_per_day / (sun_hours * eff_factor)
    
    # ค้นหาแพ็กเกจที่เหมาะสม (ขนาดต้องครอบคลุมโหลดและตรงกับเฟสไฟ)
    suggested_pkg = None
    for pkg in pea_packages:
        if pkg['size'] >= req_kwp:
            if "3 Phase" in pkg['name'] and phase_type == "1 Phase (220V)":
                continue
            suggested_pkg = pkg
            break
    
    if not suggested_pkg: suggested_pkg = pea_packages[-1]

    # แสดงผลผ่าน Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("ขนาดระบบที่คำนวณได้", f"{req_kwp:.2f} kWp")
    m2.metric("แพ็กเกจที่แนะนำ (PEA)", f"{suggested_pkg['size']} kWp")
    m3.metric("งบลงทุนประมาณการ", f"{suggested_pkg['price']:,} ฿")

    # แสดงรายละเอียดแพ็กเกจ
    st.markdown(f"""
    <div class="package-card">
        <h2 style='color:#004d40; margin-top:0;'>📦 แนะนำแพ็กเกจ: {suggested_pkg['name']}</h2>
        <p style='font-size:1.2rem;'><b>กำลังการผลิต:</b> {suggested_pkg['size']} kWp | <b>งบประมาณ:</b> {suggested_pkg['price']:,} บาท</p>
        <p style='color:#555;'><i>{suggested_pkg['desc']}</i></p>
        <p style='font-size:0.85rem; color:#888;'>* ราคารวมค่าสำรวจ ติดตั้ง และขออนุญาตเชื่อมต่อโครงข่าย (อ้างอิงมาตรฐาน PEA Solar)</p>
    </div>
    """, unsafe_allow_html=True)

    # วิเคราะห์ทางการเงิน
    pkg_prod_day = suggested_pkg['size'] * sun_hours * eff_factor
    monthly_save = pkg_prod_day * 30 * unit_price
    annual_save = monthly_save * 12
    payback_years = suggested_pkg['price'] / annual_save if annual_save > 0 else 0
    co2_saved = (pkg_prod_day * 365 * 0.5) / 1000

    res_tab1, res_tab2, res_tab3 = st.tabs(["💰 วิเคราะห์การเงิน", "🌳 พลังงานสะอาด", "📋 ตารางเปรียบเทียบ"])
    
    with res_tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.success(f"ประหยัดค่าไฟได้ประมาณ: **{monthly_save:,.0f} บาท/เดือน**")
            st.info(f"ประหยัดได้ต่อปี: **{annual_save:,.0f} บาท/ปี**")
            st.warning(f"ระยะเวลาคืนทุน: **{payback_years:.1f} ปี**")
        with c2:
            years = list(range(0, 11))
            cashflow = [-suggested_pkg['price'] + (annual_save * y) for y in years]
            st.line_chart(pd.DataFrame({"ปีที่": years, "กระแสเงินสดสะสม": cashflow}).set_index("ปีที่"))

    with res_tab2:
        st.write("### ผลกระทบต่อสิ่งแวดล้อม")
        st.write(f"🍃 ช่วยลดการปล่อยก๊าซ CO2 ได้ประมาณ **{co2_saved:.2f} ตันต่อปี**")
        st.write(f"🌳 เทียบเท่ากับการปลูกต้นไม้เพิ่มขึ้น **{int(co2_saved * 100)} ต้นต่อปี**")

    with res_tab3:
        st.write("### ตารางแพ็กเกจมาตรฐาน PEA Solar")
        df_pkg = pd.DataFrame(pea_packages)
        df_pkg.columns = ["ชื่อแพ็กเกจ", "ขนาด (kWp)", "ราคา (บาท)", "รายละเอียด"]
        st.dataframe(df_pkg.style.format({"ราคา (บาท)": "{:,.0f}"}), use_container_width=True)

else:
    st.warning("👈 กรุณาเลือกเครื่องใช้ไฟฟ้าและระบุข้อมูลการใช้งานเพื่อเริ่มการประเมิน")

st.divider()
st.caption("หมายเหตุ: ข้อมูลนี้เป็นการคำนวณเบื้องต้นเพื่อประกอบการตัดสินใจ | อ้างอิงชั่วโมงแดดเฉลี่ยในประเทศไทย 4.2 ชม./วัน")
