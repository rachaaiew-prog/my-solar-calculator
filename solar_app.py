import streamlit as st
import pandas as pd
import math

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Solar Assistant | วิเคราะห์ระบบโซลาร์เซลล์",
    page_icon="☀️",
    layout="wide"
)

# --- ข้อมูลแพ็กเกจมาตรฐาน PEA Solar (อ้างอิงตามขนาด Inverter) ---
pea_packages = [
    {
        "name": "Micro Solar (1 Phase)", 
        "inverter_size": 3.0, 
        "pv_size": 3.78, 
        "price": 145000, 
        "desc": "Inverter 3kW (1-Phase): เหมาะสำหรับบ้านขนาดเล็ก แอร์ 1-2 เครื่อง"
    },
    {
        "name": "Home Solar (1 Phase)", 
        "inverter_size": 5.0, 
        "pv_size": 5.67, 
        "price": 225000, 
        "desc": "Inverter 5kW (1-Phase): เหมาะสำหรับบ้านขนาดกลาง แอร์ 2-3 เครื่อง"
    },
    {
        "name": "Premium Solar (3 Phase)", 
        "inverter_size": 5.0, 
        "pv_size": 5.67, 
        "price": 235000, 
        "desc": "Inverter 5kW (3-Phase): สำหรับบ้านไฟ 3 เฟส แอร์ 2-3 เครื่อง"
    },
    {
        "name": "Business Solar (3 Phase)", 
        "inverter_size": 10.0, 
        "pv_size": 11.34, 
        "price": 390000, 
        "desc": "Inverter 10kW (3-Phase): ออฟฟิศขนาดกลาง แอร์ 4-6 เครื่อง"
    },
    {
        "name": "Max Solar (3 Phase)", 
        "inverter_size": 20.0, 
        "pv_size": 22.68, 
        "price": 750000, 
        "desc": "Inverter 20kW (3-Phase): อาคารพาณิชย์ หรือโรงงานขนาดเล็ก"
    }
]

# --- Custom CSS สำหรับธีมม่วงที่เข้มข้นขึ้น ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Kanit', sans-serif;
    }
    
    /* พื้นหลังม่วงอมขาวที่ม่วงชัดเจนขึ้น (Rich Lavender Tint) */
    .stApp {
        background-color: #f1eeff;
    }
    
    /* Header Style: Gradient ม่วงเข้มไปม่วงสว่าง */
    .app-header {
        background: linear-gradient(135deg, #4a148c 0%, #7b1fa2 50%, #9c27b0 100%);
        padding: 2.5rem;
        color: white;
        border-radius: 28px;
        margin-bottom: 2.5rem;
        text-align: center;
        box-shadow: 0 15px 35px rgba(74, 20, 140, 0.25);
    }
    
    .pea-logo {
        width: 90px;
        margin-bottom: 1rem;
        filter: drop-shadow(0px 4px 10px rgba(0,0,0,0.3));
    }
    
    /* Card Style: เน้นขอบม่วง */
    .stMetric {
        background-color: white !important;
        padding: 24px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 20px rgba(74, 20, 140, 0.05) !important;
        border: 1px solid #e1bee7 !important;
    }
    
    .package-card {
        background-color: white;
        padding: 2rem;
        border-radius: 24px;
        border-left: 12px solid #6a11cb;
        margin-bottom: 2rem;
        box-shadow: 0 12px 30px rgba(106, 17, 203, 0.1);
    }
    
    /* Tab Style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }

    .stTabs [aria-selected="true"] {
        color: #4a148c !important;
        border-bottom-color: #4a148c !important;
        font-weight: bold;
    }
    
    /* Button: ม่วงเข้ม */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #4a148c, #7b1fa2);
        color: white;
        border-radius: 14px;
        padding: 0.6rem 2.5rem;
        border: none;
        font-weight: 500;
        transition: all 0.3s;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(90deg, #7b1fa2, #4a148c);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(74, 20, 140, 0.3);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f6ff;
        border-right: 1px solid #e1bee7;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ส่วนหัวของโปรแกรม ---
pea_logo_url = "https://www.pea.co.th/Portals/0/Images/logo.png"

st.markdown(f"""
    <div class="app-header">
        <img src="{pea_logo_url}" class="pea-logo" alt="PEA Logo">
        <h1 style='font-weight: 500; margin-top: 0; letter-spacing: 1px;'>Solar Assistant</h1>
        <p style='font-size: 1.15rem; opacity: 0.95;'>ระบบวิเคราะห์การลงทุนโซลาร์เซลล์อัจฉริยะ (PEA Solar Standard)</p>
    </div>
    """, unsafe_allow_html=True)

# --- แถบเมนูด้านข้าง (Sidebar) ---
with st.sidebar:
    st.markdown("### 🔮 ตั้งค่าระบบ")
    unit_price = st.number_input("ค่าไฟเฉลี่ย (บาท/หน่วย)", min_value=1.0, value=4.7, step=0.1)
    phase_type = st.radio("ระบบไฟฟ้าที่บ้าน", ["1 Phase (220V)", "3 Phase (380V)"])
    
    st.divider()
    st.markdown("### ⚡ ข้อมูลอุปกรณ์")
    panel_watt = 630  
    st.caption(f"แผงมาตรฐาน: {panel_watt}W Mono Half-Cut")
    
    st.divider()
    st.markdown("### ☀️ ปัจจัยการผลิต")
    sun_hours = st.slider("ชั่วโมงแดดเฉลี่ย/วัน", 3.0, 6.0, 4.2)
    system_loss = st.slider("System Loss (%)", 5, 30, 15) / 100

# --- ขั้นตอนที่ 1: ประมาณการโหลด ---
st.markdown("### 📝 1. ระบุการใช้ไฟฟ้าช่วงกลางวัน (09:00 - 16:00)")
st.info("ระบุอุปกรณ์ที่ใช้งานเพื่อหาขนาด Inverter ที่รองรับโหลดได้จริง")

device_list = [
    {"item": "แอร์ 9,000 BTU", "watts": 800, "icon": "❄️"},
    {"item": "แอร์ 12,000 BTU", "watts": 1100, "icon": "❄️"},
    {"item": "แอร์ 18,000 BTU", "watts": 1600, "icon": "❄️"},
    {"item": "แอร์ 24,000 BTU", "watts": 2100, "icon": "❄️"},
    {"item": "ตู้เย็น", "watts": 150, "icon": "🧊"},
    {"item": "ทีวี/คอมพิวเตอร์", "watts": 250, "icon": "📺"},
    {"item": "พัดลม", "watts": 60, "icon": "🌬️"},
    {"item": "ปั๊มน้ำ", "watts": 450, "icon": "💧"},
    {"item": "หลอดไฟ LED", "watts": 15, "icon": "💡"},
]

total_daily_wh = 0
col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
with col_h1: st.markdown("**รายการ**")
with col_h2: st.markdown("**จำนวน**")
with col_h3: st.markdown("**ชั่วโมง/วัน**")

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

# --- ขั้นตอนที่ 2: วิเคราะห์และแนะนำ ---
if units_per_day > 0:
    st.divider()
    st.markdown("### 📊 2. ผลการวิเคราะห์แพ็กเกจ")
    
    eff_factor = 1 - system_loss
    target_inverter_kw = units_per_day / (sun_hours * eff_factor)
    
    is_1phase = phase_type == "1 Phase (220V)"
    available_packages = [
        pkg for pkg in pea_packages 
        if (is_1phase and "1 Phase" in pkg['name']) or (not is_1phase and "3 Phase" in pkg['name'])
    ]

    suggested_pkg = None
    for pkg in available_packages:
        if pkg['inverter_size'] >= target_inverter_kw:
            suggested_pkg = pkg
            break
    
    if not suggested_pkg and available_packages:
        suggested_pkg = available_packages[-1]
    
    if not suggested_pkg:
        suggested_pkg = pea_packages[0]

    num_panels = math.ceil((suggested_pkg['pv_size'] * 1000) / panel_watt)
    actual_pv_kwp = (num_panels * panel_watt) / 1000

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Inverter Size", f"{suggested_pkg['inverter_size']} kW")
    with m2:
        st.metric("PV Modules (630W)", f"{num_panels} แผง")
    with m3:
        st.metric("Total Investment", f"{suggested_pkg['price']:,} ฿")

    if is_1phase and target_inverter_kw > 5.0:
        st.error("⚠️ โหลดของคุณเกินขีดจำกัด 5kW สำหรับระบบ 1 เฟส แนะนำให้เปลี่ยนเป็นระบบ 3 เฟส")

    st.markdown(f"""
    <div class="package-card">
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h2 style='color:#4a148c; margin:0;'>{suggested_pkg['name']}</h2>
            <span style='background:linear-gradient(90deg, #6a11cb, #2575fc); color:white; padding:6px 18px; border-radius:50px; font-size:0.85rem; font-weight:500;'>MATCHED</span>
        </div>
        <p style='margin-top:15px; font-size:1.15rem; color:#333;'>
            ระบบที่เหมาะสมที่สุดคือ Inverter ขนาด <b>{suggested_pkg['inverter_size']} kW</b> 
            ติดตั้งร่วมกับแผง Mono {panel_watt}W จำนวน {num_panels} แผง
        </p>
        <h3 style='color:#7b1fa2; margin-bottom:8px;'>งบประมาณรวม: {suggested_pkg['price']:,} บาท</h3>
        <p style='color:#777; font-size:0.85rem;'>* ราคาประมาณการเบื้องต้น รวมอุปกรณ์และค่าดำเนินการขออนุญาตตามเกณฑ์ PEA</p>
    </div>
    """, unsafe_allow_html=True)

    tab_finance, tab_compare = st.tabs(["💰 การคืนทุน (ROI)", "📋 รายละเอียดแพ็กเกจทั้งหมด"])
    
    with tab_finance:
        pkg_prod_day = actual_pv_kwp * sun_hours * eff_factor
        monthly_save = pkg_prod_day * 30 * unit_price
        annual_save = monthly_save * 12
        payback_years = suggested_pkg['price'] / annual_save if annual_save > 0 else 0
        
        c1, c2 = st.columns([1, 1.2])
        with c1:
            st.markdown(f"#### วิเคราะห์รายได้")
            st.markdown(f"""
            - **ประหยัดค่าไฟ:** {monthly_save:,.0f} บาท/เดือน
            - **ประหยัดรายปี:** {annual_save:,.0f} บาท/ปี
            - **จุดคุ้มทุน:** ประมาณ {payback_years:.1f} ปี
            """)
        with c2:
            years = list(range(0, 11))
            cashflow = [-suggested_pkg['price'] + (annual_save * y) for y in years]
            st.line_chart(pd.DataFrame({"Year": years, "Cumulative Profit": cashflow}).set_index("Year"))

    with tab_compare:
        df_pkg = pd.DataFrame(pea_packages)
        df_pkg.columns = ["Model", "Inverter (kW)", "Total PV (kWp)", "Price (THB)", "Notes"]
        st.dataframe(df_pkg.style.format({"Price (THB)": "{:,.0f}"}), use_container_width=True)

else:
    st.warning("👈 เลือกเครื่องใช้ไฟฟ้าใน Sidebar เพื่อประมวลผลระบบที่เหมาะสม")

st.divider()
st.markdown("<p style='text-align:center; color:#999; font-size:0.9rem;'>Solar Assistant v2.2 | Powered by PEA Solar Data</p>", unsafe_allow_html=True)
