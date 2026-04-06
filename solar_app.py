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
    .stApp { background-color: #f8f9fa; }
    
    .app-header {
        background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3f51b5 100%);
        padding: 2.5rem; color: white; border-radius: 20px; margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(26, 35, 126, 0.2);
    }
    
    .stat-card {
        background: white; padding: 1.5rem; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;
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
                <p style="font-size:1.1rem; opacity:0.9;">วิเคราะห์จุดคุ้มทุนและแผนการลงทุนโซลาร์เซลล์อัจฉริยะ</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Input Section ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าการคำนวณ")
    unit_price = st.number_input("ค่าไฟฟ้าเฉลี่ย (บาท/หน่วย)", value=4.7, step=0.1)
    phase = st.radio("ระบบไฟฟ้าที่บ้าน", ["1 Phase", "3 Phase"])
    st.divider()
    sun_hours = st.slider("ชั่วโมงแดดจัดเฉลี่ยต่อวัน", 3.0, 6.0, 4.2)

st.subheader("📝 วิเคราะห์การใช้ไฟช่วงกลางวัน")
units = st.number_input("จำนวนหน่วยไฟที่ใช้ (09:00 - 16:00) ต่อวัน", min_value=0.0, value=15.0)

if units > 0:
    # คำนวณหาขนาดที่เหมาะสม (Inverter Size)
    # สูตร: Units / (Sun Hours * Efficiency)
    target_kw = units / (sun_hours * 0.85)
    
    # เลือกแพ็กเกจที่ตรงกับเฟสและขนาด
    is_1p = phase == "1 Phase"
    available = [p for p in pea_packages if ((is_1p and "1 Phase" in p['name']) or (not is_1p and "3 Phase" in p['name']))]
    
    # หาแพ็กเกจที่เล็กที่สุดที่ครอบคลุมการใช้งาน หรือถ้าเกินให้เลือกตัวใหญ่สุด
    pkg = next((p for p in available if p['inverter_size'] >= target_kw), available[-1])
    
    # คำนวณตัวเลขทางการเงิน
    saving_day = pkg['pv_size'] * sun_hours * 0.85 * unit_price
    saving_year = saving_day * 365
    payback = pkg['price'] / saving_year
    total_saving_25yr = (saving_year * 25) - pkg['price']

    # แสดงผลเบื้องต้น
    st.markdown("### 📊 สรุปผลการวิเคราะห์")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("ขนาดระบบแนะนำ", f"{pkg['inverter_size']} kW")
    with c2: st.metric("งบประมาณลงทุน", f"{pkg['price']:,} บาท")
    with c3: st.metric("ระยะเวลาคืนทุน", f"{payback:.1f} ปี")
    with c4: st.metric("กำไรสะสม 25 ปี", f"{total_saving_25yr:,.0f} บาท")

    # กราฟวิเคราะห์จุดคุ้มทุน (Break-even Point)
    st.markdown("#### 📈 กราฟวิเคราะห์จุดคุ้มทุน (Break-even Analysis)")
    years = list(range(26))
    investment = [pkg['price']] * 26
    savings = [saving_year * y for y in years]
    
    chart_data = pd.DataFrame({
        "ปีที่": years,
        "เงินลงทุน (บาท)": investment,
        "รายได้ประหยัดสะสม (บาท)": savings
    }).set_index("ปีที่")
    
    st.line_chart(chart_data)
    st.info(f"💡 จุดที่เส้นสีส้มตัดเส้นสีฟ้าคือ 'จุดคุ้มทุน' ของคุณ (ประมาณปีที่ {payback:.1f})")

    # ลิงก์ผลิตภัณฑ์
    st.markdown(f'<a href="https://peasolar.pea.co.th/our-products/" target="_blank" class="product-btn">🔍 คลิกดูรายละเอียดอุปกรณ์ในแพ็กเกจ {pkg["inverter_size"]}kW</a>', unsafe_allow_html=True)

    # --- ส่วนบันทึกข้อมูล ---
    st.markdown('<div class="registration-form">', unsafe_allow_html=True)
    st.subheader("📥 สนใจรับคำปรึกษาและใบเสนอราคา")
    
    with st.form("solar_lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("ชื่อ-นามสกุล *")
        with col2:
            phone = st.text_input("เบอร์โทรศัพท์ *")
        
        addr = st.text_input("สถานที่ติดตั้ง หรือ พิกัด GPS")
        
        submitted = st.form_submit_button("🚀 ส่งข้อมูลขอใบเสนอราคา")
        
        if submitted:
            if name and phone:
                # ข้อมูล Google Form ของคุณ
                FORM_ID = "1FAIpQLSclm-IwbIb85XoWuO_P8C-o8qHZqyYP4t7GdVz7cc6LpcWgog"
                
                # Entry IDs สำหรับฟอร์มของคุณ
                entries = {
                    "name": "entry.1381098045", 
                    "phone": "entry.225801865",
                    "addr": "entry.1907655311"
                }
                
                # ส่งรายละเอียดระบบพ่วงไปด้วยในช่องสถานที่หรือหมายเหตุ
                detail = f"สนใจระบบ {pkg['inverter_size']}kW | {addr}"
                
                params = {
                    entries["name"]: name,
                    entries["phone"]: phone,
                    entries["addr"]: detail
                }
                
                form_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/viewform?" + urllib.parse.urlencode(params)
                
                st.success("ขอบคุณที่สนใจ! ระบบเตรียมข้อมูลของคุณเรียบร้อยแล้ว")
                st.markdown(f"""
                    <div style="text-align:center; padding:10px;">
                        <p>กรุณากดปุ่มด้านล่างเพื่อยืนยันการส่งข้อมูลให้เจ้าหน้าที่ติดต่อกลับ</p>
                        <a href="{form_url}" target="_blank" class="confirm-btn">✅ ยืนยันข้อมูลและส่งฟอร์ม</a>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("กรุณากรอกชื่อและเบอร์โทรศัพท์เพื่อติดต่อกลับ")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("Solar Assistant v5.7 | Premium Analysis & PEA Solar Integrated")
