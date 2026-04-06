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
    
    .package-card {
        background-color: white; padding: 2rem; border-radius: 24px;
        border-left: 12px solid #6a11cb; margin-bottom: 2rem;
        box-shadow: 0 12px 30px rgba(106, 17, 203, 0.1);
    }
    
    .registration-form {
        background-color: #ffffff; padding: 25px; border-radius: 20px;
        border: 2px solid #e1bee7; margin-top: 20px;
    }
    
    .product-btn {
        display: block; width: 100%; text-align: center;
        background: linear-gradient(90deg, #9c27b0, #7b1fa2);
        color: white !important; padding: 18px; border-radius: 15px;
        text-decoration: none; font-weight: bold; font-size: 1.1rem;
        margin-top: 15px; box-shadow: 0 4px 15px rgba(156, 39, 176, 0.3);
    }
    
    .confirm-btn {
        display: block; width: 100%; text-align: center;
        background: #2e7d32; color: white !important;
        padding: 15px; border-radius: 12px; text-decoration: none;
        font-weight: bold; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
st.markdown(f"""
    <div class="app-header">
        <div style="display: flex; align-items: center; gap: 2rem;">
            <img src="https://lh3.googleusercontent.com/d/1RDUD8icYRqrf1s_HuwCsKABQjoD8OP0n" style="width:150px;">
            <div>
                <h1 style="color:white; margin:0;">Solar Assistant</h1>
                <p>วิเคราะห์ความคุ้มค่าและบันทึกข้อมูลเข้า Google Sheet</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Input Section ---
with st.sidebar:
    st.header("⚙️ ตั้งค่า")
    unit_price = st.number_input("ค่าไฟ (บาท/หน่วย)", value=4.7)
    phase = st.radio("ระบบไฟ", ["1 Phase", "3 Phase"])

st.subheader("📝 ระบุหน่วยไฟที่ใช้ช่วงกลางวัน")
units = st.number_input("จำนวนหน่วยต่อวัน (09:00 - 16:00)", min_value=0.0, value=10.0)

if units > 0:
    # คำนวณแพ็กเกจ
    target_kw = units / (4.2 * 0.85)
    is_1p = phase == "1 Phase"
    available = [p for p in pea_packages if ((is_1p and "1 Phase" in p['name']) or (not is_1p and "3 Phase" in p['name']))]
    pkg = next((p for p in available if p['inverter_size'] >= target_kw), available[-1])
    
    # คำนวณคืนทุน
    saving_year = pkg['pv_size'] * 4.2 * 0.85 * unit_price * 365
    payback = pkg['price'] / saving_year

    # แสดงผลเบื้องต้น
    c1, c2, c3 = st.columns(3)
    c1.metric("ขนาดแนะนำ", f"{pkg['inverter_size']} kW")
    c2.metric("ราคา", f"{pkg['price']:,} บาท")
    c3.metric("คืนทุน", f"{payback:.1f} ปี")

    # กราฟจุดคุ้มทุน
    st.markdown("#### กราฟวิเคราะห์จุดคุ้มทุน")
    df_chart = pd.DataFrame({
        "ปีที่": range(21),
        "เงินลงทุน": [pkg['price']] * 21,
        "ประหยัดสะสม": [saving_year * i for i in range(21)]
    }).set_index("ปีที่")
    st.line_chart(df_chart)

    # ลิงก์ผลิตภัณฑ์
    st.markdown(f'<a href="https://peasolar.pea.co.th/our-products/" target="_blank" class="product-btn">🔍 ดูรายละเอียดผลิตภัณฑ์เพิ่มเติม</a>', unsafe_allow_html=True)

    # --- ส่วนบันทึกข้อมูล ---
    st.markdown('<div class="registration-form">', unsafe_allow_html=True)
    st.subheader("📥 บันทึกข้อมูลและขอใบเสนอราคา")
    
    with st.form("solar_form_recovery"):
        name = st.text_input("ชื่อ-นามสกุล *")
        phone = st.text_input("เบอร์โทรศัพท์ *")
        addr = st.text_input("สถานที่ติดตั้ง/พิกัด")
        
        btn = st.form_submit_button("🚀 สร้างลิงก์ส่งข้อมูล")
        
        if btn:
            if name and phone:
                FORM_ID = "1FAIpQLSclm-IwbIb85XoWuO_P8C-o8qHZqyYP4t7GdVz7cc6LpcWgog"
                
                # ใช้ Entry ID ที่คุณเคยส่งมาเบื้องต้น
                entries = {
                    "entry_name": "entry.1381098045", 
                    "entry_phone": "entry.225801865",
                    "entry_addr": "entry.1907655311"
                }
                
                params = {
                    entries["entry_name"]: name,
                    entries["entry_phone"]: phone,
                    entries["entry_addr"]: addr
                }
                
                base_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/viewform?"
                final_url = base_url + urllib.parse.urlencode(params)
                
                st.success("เตรียมข้อมูลเรียบร้อยแล้ว!")
                st.markdown(f'<a href="{final_url}" target="_blank" class="confirm-btn">✅ กดยืนยันการส่งข้อมูล</a>', unsafe_allow_html=True)
            else:
                st.error("กรุณากรอกข้อมูลให้ครบถ้วน")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("Solar Assistant v5.6 | เวอร์ชันย้อนกลับ (Stable Version)")
