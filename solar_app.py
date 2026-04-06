import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse
import pydeck as pdk

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Solar Assistant | วิเคราะห์ระบบจำหน่ายไฟฟ้า",
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

# --- ข้อมูลจำลอง Map Data (Solar 15, EV 20 - อ.สมเด็จ จ.กาฬสินธุ์) ---
def get_simulated_grid_data():
    base_lat, base_lon = 16.7115, 103.7477
    
    # 1. ข้อมูลหม้อแปลง (Transformer Nodes)
    transformers = pd.DataFrame({
        'id': ['TR-01', 'TR-02'],
        'lat': [16.7130, 16.7100],
        'lon': [103.7485, 103.7465],
        'capacity_kva': [160, 250],
        'type': 'Transformer',
        'color_rgb': [[0, 0, 255, 255]] * 2 # สีน้ำเงิน
    })
    
    # 2. ข้อมูล Solar (15 รายการ)
    solar_data = pd.DataFrame({
        'id': [f'S-{i:02d}' for i in range(1, 16)],
        'lat': base_lat + np.random.randn(15) * 0.006,
        'lon': base_lon + np.random.randn(15) * 0.006,
        'capacity_kw': np.random.choice([3, 5, 10], 15),
        'type': 'Solar PV',
        'color_rgb': [[255, 75, 75, 200]] * 15, # สีแดง
        'assigned_tr': np.random.choice(['TR-01', 'TR-02'], 15)
    })
    
    # 3. ข้อมูล EV วงจรที่ 2 (20 รายการ)
    ev_data = pd.DataFrame({
        'id': [f'EV-{i:02d}' for i in range(1, 21)],
        'lat': base_lat + np.random.randn(20) * 0.006,
        'lon': base_lon + np.random.randn(20) * 0.006,
        'capacity_kw': np.random.choice([7, 11], 20),
        'type': 'EV Circuit 2',
        'color_rgb': [[46, 125, 50, 230]] * 20, # สีเขียว
        'assigned_tr': np.random.choice(['TR-01', 'TR-02'], 20)
    })
    
    points = pd.concat([solar_data, ev_data], ignore_index=True)
    
    # สร้างเส้นทางการจ่ายไฟ (Line Strings)
    paths = []
    for _, row in points.iterrows():
        tr = transformers[transformers['id'] == row['assigned_tr']].iloc[0]
        paths.append({
            'from_lat': tr['lat'], 'from_lon': tr['lon'],
            'to_lat': row['lat'], 'to_lon': row['lon'],
            'tr_id': tr['id'],
            'type': row['type']
        })
        
    return transformers, points, pd.DataFrame(paths)

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
    .status-card {
        padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem; border: 1px solid #eee;
        background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.markdown(f"""
    <div class="app-header">
        <div style="display: flex; align-items: center; gap: 2rem;">
            <img src="https://lh3.googleusercontent.com/d/1RDUD8icYRqrf1s_HuwCsKABQjoD8OP0n" style="width:120px; border-radius:10px;">
            <div>
                <h1 style="color:white; margin:0; font-size:2.2rem;">Grid Balance & Solar Analyzer</h1>
                <p style="font-size:1.1rem; opacity:0.9;">วิเคราะห์ภาระหม้อแปลงและจุดบาลานซ์โครงข่าย (อ.สมเด็จ)</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["💡 คำนวณรายบ้าน", "🗺️ วิเคราะห์โครงข่าย (Network Analysis)"])

with tab1:
    with st.sidebar:
        st.header("⚙️ Settings")
        unit_price = st.number_input("ค่าไฟฟ้า (บาท/หน่วย)", value=4.7)
        phase = st.radio("ระบบไฟ", ["1 Phase", "3 Phase"])
        sun_h = st.slider("ชั่วโมงแดด", 3.0, 6.0, 4.2)

    st.info("กรุณาระบุข้อมูลการใช้ไฟในหน้าต่างแอปเพื่อรับคำแนะนำรายบุคคล")
    # (โค้ดส่วนคำนวณรายบ้านยังคงอยู่ตามโครงสร้างเดิม)

with tab2:
    st.markdown("### 🗺️ Network Visualization: Solar + EV Integration")
    st.write("แสดงความสัมพันธ์ระหว่างหม้อแปลง (TR) กับผู้ใช้ไฟ Solar และ EV (รวม 35 ราย)")
    
    tr_df, pt_df, path_df = get_simulated_grid_data()
    
    # แผนที่ Pydeck
    view_state = pdk.ViewState(latitude=16.7115, longitude=103.7477, zoom=14.5)
    
    # ชั้นข้อมูลเส้นจ่ายไฟ
    line_layer = pdk.Layer(
        "LineLayer",
        path_df,
        get_source_position="[from_lon, from_lat]",
        get_target_position="[to_lon, to_lat]",
        get_color="[150, 150, 150, 100]",
        get_width=2,
    )
    
    # ชั้นข้อมูลจุดติดตั้ง
    point_layer = pdk.Layer(
        "ScatterplotLayer",
        pt_df,
        get_position="[lon, lat]",
        get_color="color_rgb",
        get_radius=50,
        pickable=True
    )
    
    # ชั้นข้อมูลหม้อแปลง
    tr_layer = pdk.Layer(
        "ScatterplotLayer",
        tr_df,
        get_position="[lon, lat]",
        get_color="color_rgb",
        get_radius=120,
        pickable=True
    )

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=view_state,
        layers=[line_layer, point_layer, tr_layer],
        tooltip={"text": "{id} | {type}\nCapacity: {capacity_kw}{capacity_kva} units"}
    ))

    # คำอธิบายสัญลักษณ์
    st.markdown("""
        <div style="display:flex; gap:15px; margin-bottom:20px;">
            <div style="display:flex; align-items:center; gap:5px;"><div style="width:15px;height:15px;background:#0000FF;border-radius:50%;"></div><span>Transformer</span></div>
            <div style="display:flex; align-items:center; gap:5px;"><div style="width:15px;height:15px;background:#FF4B4B;border-radius:50%;"></div><span>Solar PV (15 ราย)</span></div>
            <div style="display:flex; align-items:center; gap:5px;"><div style="width:15px;height:15px;background:#2E7D32;border-radius:50%;"></div><span>EV Circuit 2 (20 ราย)</span></div>
        </div>
    """, unsafe_allow_html=True)

    # --- ส่วนวิเคราะห์บาลานซ์หม้อแปลง ---
    st.markdown("### ⚡ Transformer Load & Balance Report")
    
    cols = st.columns(len(tr_df))
    for i, (_, tr) in enumerate(tr_df.iterrows()):
        with cols[i]:
            # กรองข้อมูลที่ต่อกับหม้อแปลงเครื่องนี้
            tr_points = pt_df[pt_df['assigned_tr'] == tr['id']]
            ev_load = tr_points[tr_points['type'] == 'EV Circuit 2']['capacity_kw'].sum()
            solar_gen = tr_points[tr_points['type'] == 'Solar PV']['capacity_kw'].sum()
            
            # การประเมินภาระ (Load Estimation)
            # คิด Net Load = โหลด EV - (กำลังผลิต Solar * 0.5 เพื่อเผื่อช่วงเมฆบัง)
            net_impact = ev_load - (solar_gen * 0.5)
            usage_pct = (ev_load / tr['capacity_kva']) * 100
            
            st.markdown(f"""
                <div class="status-card">
                    <h4>🏪 {tr['id']} ({tr['capacity_kva']} kVA)</h4>
                    <p><b>Load EV:</b> {ev_load} kW</p>
                    <p><b>Solar Gen:</b> {solar_gen} kW</p>
                    <hr>
                    <p><b>Utilization (EV Only):</b> {usage_pct:.1f}%</p>
                </div>
            """, unsafe_allow_html=True)
            
            # แจ้งเตือนความเหมาะสม
            if usage_pct > 80:
                st.error(f"🚨 วิกฤต: {tr['id']} โหลด EV สูงเกินไป ควรเพิ่มขนาดหม้อแปลง")
            elif usage_pct > 60:
                st.warning(f"⚠️ เสี่ยง: {tr['id']} เริ่มหนาแน่น ควรติดตามการบาลานซ์เฟส")
            else:
                st.success(f"✅ ปกติ: {tr['id']} มีพื้นที่เหลือรองรับโหลดเพิ่มได้")

    # ตารางข้อมูลสรุป
    with st.expander("ดูตารางข้อมูลโครงข่ายทั้งหมด"):
        st.dataframe(pt_df[['id', 'type', 'capacity_kw', 'assigned_tr', 'lat', 'lon']], use_container_width=True)

st.divider()
st.caption("Solar Assistant v6.3 | Network Load Balancing & Infrastructure Planning")
