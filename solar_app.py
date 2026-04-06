import streamlit as st
import pandas as pd
import math

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="ระบบคำนวณโซลาร์เซลล์อัจฉริยะ",
    page_icon="☀️",
    layout="wide"
)

# --- CSS ตกแต่งเพิ่มเติม ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- ส่วนหัวข้อ ---
st.title("☀️ ระบบประเมินการติดตั้งโซลาร์เซลล์ (Solar PV Estimator)")
st.subheader("คำนวณขนาดระบบที่เหมาะสมและจุดคุ้มทุนเบื้องต้น")

# --- ส่วนรับข้อมูล (Sidebar) ---
with st.sidebar:
    st.header("📋 กรอกข้อมูลการใช้ไฟ")
    avg_bill = st.number_input("ค่าไฟเฉลี่ยต่อเดือน (บาท)", min_value=100, value=4000, step=100)
    unit_price = st.number_input("ค่าไฟต่อหน่วย (บาท)", min_value=1.0, value=4.7, step=0.1)
    
    st.divider()
    st.header("🛠️ ข้อมูลอุปกรณ์")
    panel_watt = st.selectbox("ขนาดวัตต์ของแผง (Wp)", [450, 540, 550, 585, 600], index=2)
    system_cost_per_kw = st.number_input("ราคาติดตั้งประมาณการ (บาทต่อ kWp)", min_value=10000, value=35000, step=1000)
    
    st.divider()
    st.header("🌍 ปัจจัยสภาพแวดล้อม")
    sun_hours = st.slider("ชั่วโมงแดดเฉลี่ยต่อวัน (ชม.)", 3.0, 6.0, 4.2)
    efficiency = st.slider("ประสิทธิภาพรวมของระบบ (%)", 50, 100, 80) / 100

# --- ส่วนการคำนวณ Logic ---
# 1. คำนวณหน่วยไฟทั้งหมดต่อเดือน
total_units_month = avg_bill / unit_price
# 2. ประมาณการหน่วยไฟที่ใช้ช่วงกลางวัน (Daytime Load 60%)
daytime_units_day = (total_units_month / 30) * 0.60
# 3. คำนวณขนาดติดตั้งที่แนะนำ (kWp)
recommended_kwp = daytime_units_day / (sun_hours * efficiency)
# 4. จำนวนแผง
total_panels = math.ceil((recommended_kwp * 1000) / panel_watt)
# 5. ประมาณการเงินที่ประหยัดได้ต่อปี
annual_saving = (recommended_kwp * sun_hours * efficiency) * 365 * unit_price
# 6. งบประมาณการติดตั้งโดยประมาณ
estimated_investment = recommended_kwp * system_cost_per_kw
# 7. ระยะเวลาคืนทุน (ปี)
payback_period = estimated_investment / annual_saving if annual_saving > 0 else 0

# --- ส่วนแสดงผลลัพธ์ (Main Panel) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("ขนาดระบบแนะนำ", f"{recommended_kwp:.2f} kWp")
with col2:
    st.metric("จำนวนแผงที่ใช้", f"{total_panels} แผง")
with col3:
    st.metric("ประหยัดได้/ปี", f"{annual_saving:,.0f} บาท")
with col4:
    st.metric("ระยะเวลาคืนทุน", f"{payback_period:.1f} ปี")

st.divider()

# --- ส่วนรายละเอียดเชิงลึก ---
tab1, tab2 = st.tabs(["📊 ตารางประมาณการ 10 ปี", "📝 คำแนะนำการติดตั้ง"])

with tab1:
    st.write("ตารางแสดงกระแสเงินสดและการคืนทุนสะสม")
    years = list(range(1, 11))
    savings_list = [annual_saving * y for y in years]
    net_profit = [s - estimated_investment for s in savings_list]
    
    df = pd.DataFrame({
        "ปีที่": years,
        "เงินที่ประหยัดสะสม (บาท)": savings_list,
        "กำไร/ขาดทุนสะสม (บาท)": net_profit
    })
    st.dataframe(df, use_container_width=True)
    st.line_chart(df.set_index("ปีที่")["กำไร/ขาดทุนสะสม (บาท)"])

with tab2:
    st.info(f"""
    **ข้อมูลสรุปสำหรับหน้างาน:**
    - **พื้นที่หลังคาที่ต้องการ:** ประมาณ {total_panels * 2.6:.1f} ตารางเมตร (เผื่อทางเดิน Service)
    - **น้ำหนักที่เพิ่มบนหลังคา:** ประมาณ {total_panels * 25:.0f} กิโลกรัม (ไม่รวมโครงสร้าง)
    - **ประเภท Inverter:** ควรเลือก Inverter ขนาด {recommended_kwp:.0f} kW ที่มีมาตรฐาน MEA/PEA
    """)
    
    if recommended_kwp < 5:
        st.warning("⚠️ ขนาดระบบต่ำกว่า 5kWp สามารถติดตั้งแบบ 1 เฟสได้")
    else:
        st.success("✅ ขนาดระบบ 5kWp ขึ้นไป แนะนำให้ตรวจสอบระบบไฟเป็นแบบ 3 เฟส")

# ส่วนท้าย
st.caption("หมายเหตุ: ผลการคำนวณนี้เป็นการประมาณการเบื้องต้น ควรปรึกษาวิศวกรก่อนติดตั้งจริง")
