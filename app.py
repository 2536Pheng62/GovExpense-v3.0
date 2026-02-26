"""
GovExpense — ระบบคำนวณค่าใช้จ่ายเดินทางไปราชการ (Wizard Edition)
=================================================================
Streamlit Web Application แบบ Step-by-step Wizard
รองรับ Deploy บน Streamlit Cloud

Author : GovExpense Team
Version: 3.0 (Wizard)
"""

import streamlit as st
from datetime import datetime, date, time
import os

from expense_calculator import ExpenseCalculator
from pdf_generator import GovDocumentGenerator
from pdf_preview import render_pdf_preview
from distance_utils import calculate_road_distance

# =====================================================================
# PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title="GovExpense: ระบบเบิกจ่ายราชการ",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# THAI HELPER
# =====================================================================
THAI_MONTHS_SHORT = [
    "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
]
THAI_MONTHS_FULL = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

def thai_date(d, fmt="short"):
    """วันที่แบบ พ.ศ."""
    be = d.year + 543
    if fmt == "num":
        return f"{d.day:02d}/{d.month:02d}/{be}"
    if fmt == "long":
        return f"{d.day} {THAI_MONTHS_FULL[d.month]} {be}"
    return f"{d.day} {THAI_MONTHS_SHORT[d.month]} {be}"


# =====================================================================
# GLOBAL CSS — Soft & Eye-Friendly Palette
# =====================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans Thai', sans-serif; }
.stApp { background-color: #f8f9fa; }
section[data-testid="stSidebar"] { background-color: #f0f4f8; }

/* ── Progress Bar ── */
.wizard-progress {
    display: flex; justify-content: center; gap: 0.4rem;
    padding: 1rem 0 1.5rem; margin-bottom: 0.5rem;
}
.wiz-step {
    display: flex; align-items: center; gap: 0.45rem;
    padding: 0.45rem 1rem; border-radius: 2rem;
    font-size: 0.85rem; font-weight: 500;
    color: #8a96a6; background: #e8eef4;
    transition: all 0.25s ease;
}
.wiz-step.active {
    background: linear-gradient(135deg, #4a8ec2, #2a5075);
    color: #fff; font-weight: 600;
    box-shadow: 0 3px 10px rgba(42,80,117,0.18);
}
.wiz-step.done {
    background: #d4edda; color: #2d6a4f; font-weight: 600;
}
.wiz-dot {
    width: 1.5rem; height: 1.5rem; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 700;
    background: #cbd5e1; color: #fff;
}
.wiz-step.active .wiz-dot { background: rgba(255,255,255,0.3); }
.wiz-step.done .wiz-dot { background: #5caa80; }

/* ── Cards ── */
.card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 1rem; padding: 1.8rem 2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    margin-bottom: 1.2rem;
}
.card-title {
    font-size: 1.25rem; font-weight: 700; color: #2a5075;
    margin: 0 0 1rem; padding-bottom: 0.6rem;
    border-bottom: 2px solid #e2e8f0;
}
.summary-total {
    text-align: center; padding: 1.5rem;
    background: linear-gradient(135deg, #f2f8f5, #e8f2ed);
    border-radius: 1rem; border: 2px solid #5caa80;
    margin: 1rem 0;
}
.summary-total h1 { color: #2d6a4f; margin: 0; }
.metric-row {
    display: flex; justify-content: center; gap: 1.5rem;
    flex-wrap: wrap; margin: 1rem 0;
}
.metric-box {
    flex: 1; min-width: 180px; max-width: 260px;
    background: #f0f4f8; border-radius: 0.8rem;
    padding: 1rem 1.2rem; text-align: center;
    border: 1px solid #d8e0e8;
}
.metric-box .label { font-size: 0.82rem; color: #6b7f94; }
.metric-box .value { font-size: 1.4rem; font-weight: 700; color: #2a5075; }

/* ── Notice ── */
.notice-box {
    background: linear-gradient(135deg, #fef9f1, #fdf0db);
    border: 1px solid #e6c97a; border-radius: 1rem;
    padding: 1.5rem 1.8rem; margin: 1.5rem 0;
    font-size: 0.88rem; color: #5e4520; line-height: 1.65;
}
.notice-box strong { color: #7c5b20; }

/* ── Streamlit overrides ── */
div[data-testid="stMetric"] {
    background: #f0f4f8; padding: 0.8rem 1rem;
    border-radius: 0.6rem; border: 1px solid #d8e0e8;
}
div[data-testid="stMetric"] label { color: #4a6274 !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #2a5075 !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# SESSION STATE DEFAULTS
# =====================================================================
DEFAULTS = {
    "step": 1,
    # Step 1 — Trip
    "full_name": "นายสมชาย ใจดี",
    "position": "นักวิชาการคอมพิวเตอร์",
    "c_level": "C1-C8",
    "department": "กรมธนารักษ์",
    "purpose": "เข้าร่วมประชุมวิชาการ",
    "province": "เชียงใหม่",
    "start_date": date.today(),
    "start_time": time(8, 0),
    "end_date": date.today(),
    "end_time": time(16, 0),
    "is_overnight": True,
    "provided_meals": 0,
    "order_no": "",
    "order_date": date.today(),
    "loan_no": "",
    "loan_date": date.today(),
    # Step 2 — Accommodation
    "trip_type": "general",
    "training_venue": "private",
    "accom_method": "lump_sum",
    "room_type": "single",
    "actual_cost": 0.0,
    "manual_rate": 800,
    "nights": 0,
    "training_meals": 0,
    "training_snacks": 0,
    # Step 3 — Transport
    "transport_origin": "",
    "transport_dest": "",
    "transport_items": [],
    "tmp_dist": 0.0,
    "tmp_taxi_fare": 0.0,
    # Results (computed at step 4)
    "per_diem_res": None,
    "accom_res": None,
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# =====================================================================
# 77 PROVINCES
# =====================================================================
THAI_PROVINCES = [
    "กระบี่", "กรุงเทพมหานคร", "กาญจนบุรี", "กาฬสินธุ์",
    "กำแพงเพชร", "ขอนแก่น", "จันทบุรี", "ฉะเชิงเทรา",
    "ชลบุรี", "ชัยนาท", "ชัยภูมิ", "ชุมพร",
    "เชียงราย", "เชียงใหม่", "ตรัง", "ตราด",
    "ตาก", "นครนายก", "นครปฐม", "นครพนม",
    "นครราชสีมา", "นครศรีธรรมราช", "นครสวรรค์", "นนทบุรี",
    "นราธิวาส", "น่าน", "บึงกาฬ", "บุรีรัมย์",
    "ปทุมธานี", "ประจวบคีรีขันธ์", "ปราจีนบุรี", "ปัตตานี",
    "พระนครศรีอยุธยา", "พะเยา", "พังงา", "พัทลุง",
    "พิจิตร", "พิษณุโลก", "เพชรบุรี", "เพชรบูรณ์",
    "แพร่", "ภูเก็ต", "มหาสารคาม", "มุกดาหาร",
    "แม่ฮ่องสอน", "ยโสธร", "ยะลา", "ร้อยเอ็ด",
    "ระนอง", "ระยอง", "ราชบุรี", "ลพบุรี",
    "ลำปาง", "ลำพูน", "เลย", "ศรีสะเกษ",
    "สกลนคร", "สงขลา", "สตูล", "สมุทรปราการ",
    "สมุทรสงคราม", "สมุทรสาคร", "สระแก้ว", "สระบุรี",
    "สิงห์บุรี", "สุโขทัย", "สุพรรณบุรี", "สุราษฎร์ธานี",
    "สุรินทร์", "หนองคาย", "หนองบัวลำภู", "อ่างทอง",
    "อำนาจเจริญ", "อุดรธานี", "อุตรดิตถ์", "อุทัยธานี",
    "อุบลราชธานี",
]

VEHICLE_OPTIONS = {
    "private_car": "🚗 รถยนต์ส่วนบุคคล",
    "motorcycle": "🏍️ รถจักรยานยนต์ส่วนบุคคล",
    "tuk_tuk": "🛺 รถ 3 ล้อเครื่อง (Tuk-Tuk)",
    "taxi": "🚖 รถแท็กซี่",
    "train": "🚆 รถไฟ",
    "bus": "🚌 รถทัวร์/รถเมล์",
    "skytrain": "🚈 รถไฟฟ้า (BTS/MRT)",
    "van": "🚐 รถตู้สาธารณะ",
    "boat": "⛵ เรือ",
    "airplane": "✈️ เครื่องบิน",
    "other": "📦 อื่น ๆ",
}


# =====================================================================
# NAVIGATION HELPERS
# =====================================================================
def go_to(step: int):
    st.session_state.step = step

def render_progress():
    """Render wizard progress indicators."""
    labels = ["ข้อมูลเดินทาง", "ค่าที่พัก", "ค่าพาหนะ", "สรุป & PDF"]
    icons = ["📅", "🏨", "🚗", "📄"]
    current = st.session_state.step
    parts = []
    for i, (label, icon) in enumerate(zip(labels, icons), 1):
        if i < current:
            cls = "done"
        elif i == current:
            cls = "active"
        else:
            cls = ""
        parts.append(
            f'<div class="wiz-step {cls}">'
            f'<span class="wiz-dot">{"✓" if i < current else i}</span>'
            f'{icon} {label}</div>'
        )
    st.markdown(f'<div class="wizard-progress">{"".join(parts)}</div>', unsafe_allow_html=True)


def nav_buttons(back=True, next_label="ถัดไป ➡️", next_step=None, back_step=None):
    """Render back/next navigation buttons."""
    cols = st.columns([1, 1] if back else [1])
    if back:
        with cols[0]:
            if st.button("⬅️ ย้อนกลับ", use_container_width=True):
                go_to(back_step or st.session_state.step - 1)
                st.rerun()
        btn_col = cols[1]
    else:
        btn_col = cols[0]
    with btn_col:
        if st.button(next_label, type="primary", use_container_width=True):
            go_to(next_step or st.session_state.step + 1)
            st.rerun()


# =====================================================================
# STEP 1 — ข้อมูลการเดินทาง
# =====================================================================
def step_trip_info():
    st.markdown('<div class="card"><div class="card-title">📅 ข้อมูลการเดินทาง</div>', unsafe_allow_html=True)

    # --- ผู้เดินทาง ---
    st.markdown("##### 👤 ข้อมูลผู้เดินทาง")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.full_name = st.text_input("ชื่อ-นามสกุล", st.session_state.full_name)
        st.session_state.position = st.text_input("ตำแหน่ง", st.session_state.position)
    with c2:
        st.session_state.c_level = st.selectbox(
            "ระดับตำแหน่ง", ["C1-C8", "C9-C11"],
            index=0 if st.session_state.c_level == "C1-C8" else 1,
        )
        st.session_state.department = st.text_input("สังกัด", st.session_state.department)

    st.markdown("---")

    # --- รายละเอียดการเดินทาง ---
    st.markdown("##### 🗺️ รายละเอียดการเดินทาง")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.purpose = st.text_input("วัตถุประสงค์", st.session_state.purpose)
        idx = THAI_PROVINCES.index(st.session_state.province) if st.session_state.province in THAI_PROVINCES else 13
        st.session_state.province = st.selectbox("จังหวัดปลายทาง", THAI_PROVINCES, index=idx)
    with c2:
        st.session_state.order_no = st.text_input("เลขที่คำสั่ง", st.session_state.order_no)
        st.session_state.order_date = st.date_input("ลงวันที่คำสั่ง", st.session_state.order_date)
        st.caption(f"📅 {thai_date(st.session_state.order_date, 'long')}")

    st.markdown("---")

    # --- วันเวลา ---
    st.markdown("##### 🕐 วันเวลาเดินทาง")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.start_date = st.date_input("วันเริ่มต้น", st.session_state.start_date)
        st.caption(f"📅 {thai_date(st.session_state.start_date, 'long')}")
        st.session_state.start_time = st.time_input("เวลาเริ่มต้น", st.session_state.start_time)
    with c2:
        st.session_state.end_date = st.date_input("วันสิ้นสุด", st.session_state.end_date)
        st.caption(f"📅 {thai_date(st.session_state.end_date, 'long')}")
        st.session_state.end_time = st.time_input("เวลาสิ้นสุด", st.session_state.end_time)

    start_dt = datetime.combine(st.session_state.start_date, st.session_state.start_time)
    end_dt = datetime.combine(st.session_state.end_date, st.session_state.end_time)

    if start_dt >= end_dt:
        st.error("⛔ เวลาเริ่มต้นต้องน้อยกว่าเวลาสิ้นสุด")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    dur = end_dt - start_dt
    st.info(
        f"⏱️ รวมเวลาเดินทาง: **{dur.days} วัน {dur.seconds // 3600} ชั่วโมง**\n\n"
        f"ออก: {thai_date(start_dt)} {st.session_state.start_time.strftime('%H:%M')} น.  →  "
        f"กลับ: {thai_date(end_dt)} {st.session_state.end_time.strftime('%H:%M')} น."
    )

    st.markdown("---")

    # --- เบี้ยเลี้ยง ---
    st.markdown("##### 🍽️ ข้อมูลเบี้ยเลี้ยง")
    c1, c2 = st.columns(2)
    with c1:
        overnight_type = st.radio(
            "ลักษณะการเดินทาง",
            ["พักค้างคืน (ค้างแรม)", "ไป-กลับ (ไม่พักค้างคืน)"],
            index=0 if st.session_state.is_overnight else 1,
            horizontal=True
        )
        st.session_state.is_overnight = (overnight_type == "พักค้างคืน (ค้างแรม)")
    with c2:
        st.session_state.provided_meals = st.number_input(
            "มื้ออาหารที่รัฐจัดให้", 0, 10, st.session_state.provided_meals,
            help="หักมื้อละ 1/3 ของเบี้ยเลี้ยง",
        )

    st.markdown("---")

    # --- ข้อมูลสัญญาเงินยืม ---
    st.markdown("##### 💰 สัญญาเงินยืม (ถ้ามี)")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.loan_no = st.text_input("สัญญาเงินยืมเลขที่", st.session_state.loan_no)
    with c2:
        st.session_state.loan_date = st.date_input("ลงวันที่สัญญาเงินยืม", st.session_state.loan_date)
        st.caption(f"📅 {thai_date(st.session_state.loan_date, 'long')}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Auto-calc nights for step 2
    st.session_state.nights = max(0, (st.session_state.end_date - st.session_state.start_date).days)

    nav_buttons(back=False, next_label="ถัดไป: ค่าที่พัก ➡️", next_step=2)


# =====================================================================
# STEP 2 — ค่าที่พัก
# =====================================================================
def step_accommodation():
    calc = ExpenseCalculator()
    st.markdown('<div class="card"><div class="card-title">🏨 ค่าเช่าที่พัก</div>', unsafe_allow_html=True)

    # --- ประเภทการเดินทาง ---
    trip_label = st.radio(
        "ประเภทการเดินทาง",
        ["ทั่วไป (General)", "ฝึกอบรม (Training)"],
        index=0 if st.session_state.trip_type == "general" else 1,
        horizontal=True,
    )
    st.session_state.trip_type = "general" if "ทั่วไป" in trip_label else "training"

    if st.session_state.trip_type == "training":
        venue_label = st.radio(
            "สถานที่จัดอบรม",
            ["สถานที่เอกชน (Private)", "สถานที่ราชการ (State)"],
            index=0 if st.session_state.training_venue == "private" else 1,
            horizontal=True,
        )
        st.session_state.training_venue = "state" if "ราชการ" in venue_label else "private"

    st.markdown("---")

    # --- วิธีเบิก ---
    method_options = ["เหมาจ่าย (Lump Sum)", "จ่ายจริง (Actual)", "พักบนยานพาหนะ/ไม่มีค่าที่พัก"]
    
    # Auto-select 'no cost' if not overnight
    if not st.session_state.is_overnight:
        st.session_state.accom_method = "vehicle_sleep"
        st.session_state.nights = 0
        method_idx = 2
    else:
        method_idx = {"lump_sum": 0, "actual": 1, "vehicle_sleep": 2}.get(st.session_state.accom_method, 0)
    
    method_label = st.radio("รูปแบบการเบิก", method_options, index=method_idx, horizontal=True)
    if "เหมาจ่าย" in method_label:
        st.session_state.accom_method = "lump_sum"
    elif "จ่ายจริง" in method_label:
        st.session_state.accom_method = "actual"
    else:
        st.session_state.accom_method = "vehicle_sleep"

    st.session_state.nights = st.number_input(
        "จำนวนคืน", 0, 30, st.session_state.nights,
    )

    if st.session_state.accom_method == "actual":
        st.session_state.room_type = st.selectbox(
            "ประเภทห้อง",
            ["single", "double"],
            format_func=lambda x: "ห้องเดี่ยว (Single)" if x == "single" else "ห้องคู่ (Double)",
            index=0 if st.session_state.room_type == "single" else 1,
        )
        st.session_state.actual_cost = st.number_input(
            "ค่าที่พักตามใบเสร็จจริง (บาท)", 0.0, step=100.0,
            value=st.session_state.actual_cost,
        )
    elif st.session_state.accom_method == "lump_sum":
        rates = [500, 800, 1000, 1200, 1500, 1600, 2700]
        default_rate = st.session_state.manual_rate if st.session_state.manual_rate in rates else 800
        st.session_state.manual_rate = st.selectbox(
            "อัตราเหมาจ่าย (บาท/คืน)", rates,
            index=rates.index(default_rate),
        )

    # --- คำนวณ ---
    is_vehicle = st.session_state.accom_method == "vehicle_sleep"
    if is_vehicle:
        accom_res = calc.validate_accommodation(
            st.session_state.c_level, "lump_sum",
            st.session_state.nights, is_vehicle_sleep=True,
            trip_type=st.session_state.trip_type,
        )
    else:
        accom_res = calc.validate_accommodation(
            st.session_state.c_level,
            st.session_state.accom_method,
            st.session_state.nights,
            st.session_state.actual_cost,
            st.session_state.room_type,
            manual_rate=st.session_state.manual_rate,
            trip_type=st.session_state.trip_type,
            training_venue=st.session_state.training_venue,
        )
    st.session_state.accom_res = accom_res

    st.markdown("---")
    st.markdown("#### ผลการตรวจสอบ")
    if accom_res.get("remark"):
        st.caption(f"📋 {accom_res['remark']}")
    for w in accom_res.get("warnings", []):
        st.warning(w, icon="⚠️")
    st.metric("เบิกค่าที่พักได้", f"{accom_res['reimbursable_amount']:,.2f} บาท")

    # --- Training Meals ---
    if st.session_state.trip_type == "training":
        st.markdown("---")
        st.markdown("##### 🍽️ งบประมาณค่าอาหาร (สำหรับจัดฝึกอบรม)")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.training_meals = st.number_input("จำนวนมื้ออาหารหลัก", 0, 50, st.session_state.training_meals)
        with c2:
            st.session_state.training_snacks = st.number_input("จำนวนมื้ออาหารว่าง", 0, 100, st.session_state.training_snacks)
            
        meal_res = calc.calculate_training_meal_allowance(
            st.session_state.c_level,
            st.session_state.training_venue,
            st.session_state.training_meals,
            st.session_state.training_snacks
        )
        st.session_state.training_meal_res = meal_res
        st.info(
            f"📋 อัตราเพดาน: อาหาร {meal_res['meal_rate']} ฿/มื้อ | ว่าง {meal_res['snack_rate']} ฿/มื้อ\n\n"
            f"**รวมวงเงินงบประมาณ: {meal_res['grand_total']:,.2f} บาท**"
        )
    else:
        st.session_state.training_meal_res = None

    st.markdown('</div>', unsafe_allow_html=True)
    nav_buttons(back=True, next_label="ถัดไป: ค่าพาหนะ ➡️", next_step=3, back_step=1)


# =====================================================================
# STEP 3 — ค่าพาหนะ
# =====================================================================
def step_transport():
    calc = ExpenseCalculator()
    st.markdown('<div class="card"><div class="card-title">🚗 ค่าพาหนะ</div>', unsafe_allow_html=True)

    # --- เพิ่มรายการ ---
    st.markdown("##### ➕ เพิ่มรายการค่าพาหนะ")
    c1, c2 = st.columns(2)
    with c1:
        t_key = st.selectbox("ประเภทพาหนะ", list(VEHICLE_OPTIONS.keys()), format_func=lambda x: VEHICLE_OPTIONS[x])
        t_desc = st.text_input("รายละเอียดเส้นทาง", placeholder="เช่น บ้าน-สนามบินดอนเมือง")
    with c2:
        t_dist = 0.0
        t_cost = 0.0
        if t_key in ("private_car", "motorcycle"):
            # UI for Smart Distance
            with st.expander("📍 คำนวณระยะทางอัตโนมัติ"):
                # Use department and province as defaults if not set
                d_orig = st.session_state.get("transport_origin") or st.session_state.department
                d_dest = st.session_state.get("transport_dest") or st.session_state.province
                
                c_orig = st.text_input("ต้นทาง", d_orig, key="smart_orig")
                c_dest = st.text_input("ปลายทาง", d_dest, key="smart_dest")
                
                if st.button("🔍 คำนวณระยะทาง"):
                    with st.spinner("กำลังค้นหาเส้นทาง..."):
                        res = calculate_road_distance(c_orig, c_dest)
                        if res["error"]:
                            st.error(res["error"])
                        else:
                            st.session_state.transport_origin = c_orig
                            st.session_state.transport_dest = c_dest
                            st.session_state["tmp_dist"] = res["distance"]
                            st.success(f"ระยะทาง: {res['distance']} กม.")
                            st.rerun()
            
            # Use calculated distance if available
            val_dist = st.session_state.get("tmp_dist", 0.0)
            t_dist = st.number_input("ระยะทาง (กม.)", 0.0, step=1.0, value=float(val_dist))
            rate = 4 if t_key == "private_car" else 2
            st.caption(f"อัตราชดเชย: {rate} บาท/กม.")
        elif t_key == "taxi":
            st.info("💡 ระบุค่าโดยสารที่ต้องการเบิก")
            # Get value from session state if set by taxi calc
            val_taxi = st.session_state.get("tmp_taxi_fare", 0.0)
            t_cost = st.number_input("ค่าโดยสาร (บาท)", 0.0, step=10.0, value=float(val_taxi))
        else:
            t_cost = st.number_input("ค่าโดยสารตามตั๋ว/ใบเสร็จ (บาท)", 0.0, step=10.0)

    # Taxi meter calculator
    if t_key == "taxi":
        with st.expander("🚖 เครื่องคำนวณมิเตอร์"):
            tm_dist = st.number_input("ระยะทาง (กม.)", 0.0, step=1.0, key="tm_d")
            tm_traffic = st.number_input("เวลารถติด (นาที)", 0, step=5, key="tm_t")
            tm_booking = st.checkbox("เรียกผ่านแอป (+20 บาท)")
            tm_airport = st.checkbox("รถจอดสนามบิน (+50 บาท)")
            tm_res = calc.calculate_taxi_meter(tm_dist, tm_traffic, tm_booking, tm_airport)
            
            fare_total = tm_res['total_fare']
            st.success(f"ค่ามิเตอร์รวม: **{fare_total:,.2f} บาท**")
            
            if st.button("ตกลง (OK) — ใช้ยอดเงินนี้", type="secondary"):
                st.session_state["tmp_taxi_fare"] = fare_total
                st.rerun()

    if st.button("➕ เพิ่มรายการ", type="primary"):
        if not t_desc:
            st.error("กรุณาระบุรายละเอียดเส้นทาง")
        else:
            reimbursable = t_cost
            if t_key in ("private_car", "motorcycle"):
                res = calc.calculate_transportation(t_key, t_dist)
                reimbursable = res["reimbursable_amount"]
            st.session_state.transport_items.append({
                "type": t_key,
                "type_display": VEHICLE_OPTIONS[t_key],
                "route_desc": t_desc,
                "distance_km": t_dist,
                "cost_input": t_cost,
                "reimbursable_amount": reimbursable,
            })
            if "tmp_dist" in st.session_state:
                del st.session_state["tmp_dist"]
            if "tmp_taxi_fare" in st.session_state:
                del st.session_state["tmp_taxi_fare"]
            st.rerun()

    # --- รายการที่บันทึกแล้ว ---
    st.markdown("---")
    st.markdown("##### 📋 รายการที่บันทึกไว้")

    if st.session_state.transport_items:
        for i, item in enumerate(st.session_state.transport_items):
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.write(f"**{item['type_display']}** — {item['route_desc']}")
            with c2:
                st.write(f"{item['reimbursable_amount']:,.2f} บาท")
            with c3:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.transport_items.pop(i)
                    st.rerun()

        total_trans = sum(it["reimbursable_amount"] for it in st.session_state.transport_items)
        st.metric("รวมค่าพาหนะ", f"{total_trans:,.2f} บาท")

        if st.button("ล้างรายการทั้งหมด"):
            st.session_state.transport_items = []
            st.rerun()
    else:
        st.info("ยังไม่มีรายการค่าพาหนะ", icon="ℹ️")

    st.markdown('</div>', unsafe_allow_html=True)
    nav_buttons(back=True, next_label="ถัดไป: สรุป & PDF ➡️", next_step=4, back_step=2)


# =====================================================================
# STEP 4 — สรุป & PDF
# =====================================================================
def step_summary():
    calc = ExpenseCalculator()

    # --- Compute per diem ---
    start_dt = datetime.combine(st.session_state.start_date, st.session_state.start_time)
    end_dt = datetime.combine(st.session_state.end_date, st.session_state.end_time)

    per_diem_res = calc.calculate_per_diem(
        start_dt, end_dt,
        st.session_state.is_overnight,
        st.session_state.c_level,
        st.session_state.provided_meals,
    )
    st.session_state.per_diem_res = per_diem_res

    # Re-compute accom if missing
    if st.session_state.accom_res is None:
        is_vehicle = st.session_state.accom_method == "vehicle_sleep"
        if is_vehicle:
            accom_res = calc.validate_accommodation(
                st.session_state.c_level, "lump_sum",
                st.session_state.nights, is_vehicle_sleep=True,
                trip_type=st.session_state.trip_type,
            )
        else:
            accom_res = calc.validate_accommodation(
                st.session_state.c_level,
                st.session_state.accom_method,
                st.session_state.nights,
                st.session_state.actual_cost,
                st.session_state.room_type,
                manual_rate=st.session_state.manual_rate,
                trip_type=st.session_state.trip_type,
                training_venue=st.session_state.training_venue,
            )
        st.session_state.accom_res = accom_res

    accom_res = st.session_state.accom_res
    total_trans = sum(it["reimbursable_amount"] for it in st.session_state.transport_items)
    
    # Training Budget
    meal_budget = 0.0
    if st.session_state.trip_type == "training" and st.session_state.get("training_meal_res"):
        meal_budget = st.session_state.training_meal_res["grand_total"]

    grand_total = per_diem_res["net_amount"] + accom_res["reimbursable_amount"] + total_trans + meal_budget

    # --- แสดงยอดรวม ---
    st.markdown('<div class="card"><div class="card-title">📄 สรุปค่าใช้จ่าย</div>', unsafe_allow_html=True)

    # Metric Row
    cols_count = 4 if meal_budget > 0 else 3
    metrics = [
        {"label": "ค่าเบี้ยเลี้ยง", "value": f"{per_diem_res['net_amount']:,.2f} ฿"},
        {"label": "ค่าที่พัก", "value": f"{accom_res['reimbursable_amount']:,.2f} ฿"},
        {"label": "ค่าพาหนะ", "value": f"{total_trans:,.2f} ฿"},
    ]
    if meal_budget > 0:
        metrics.append({"label": "งบอาหารอบรม", "value": f"{meal_budget:,.2f} ฿"})

    metric_html = "".join([f'<div class="metric-box"><div class="label">{m["label"]}</div><div class="value">{m["value"]}</div></div>' for m in metrics])
    
    st.markdown(f"""
    <div class="metric-row">
        {metric_html}
    </div>
    <div class="summary-total"><h1>รวมทั้งสิ้น {grand_total:,.2f} บาท</h1></div>
    """, unsafe_allow_html=True)

    # --- รายละเอียดย่อ ---
    with st.expander("📋 รายละเอียดเพิ่มเติม", expanded=False):
        st.write(f"**ผู้เดินทาง:** {st.session_state.full_name} ({st.session_state.position})")
        st.write(f"**ระดับ:** {st.session_state.c_level} | **สังกัด:** {st.session_state.department}")
        st.write(f"**จังหวัด:** {st.session_state.province} | **วัตถุประสงค์:** {st.session_state.purpose}")
        st.write(f"**เดินทาง:** {thai_date(start_dt, 'long')} {st.session_state.start_time.strftime('%H:%M')} น. → {thai_date(end_dt, 'long')} {st.session_state.end_time.strftime('%H:%M')} น.")
        
        # Calculate raw duration
        dur = end_dt - start_dt
        d, h, m = dur.days, dur.seconds // 3600, (dur.seconds % 3600) // 60
        st.write(f"**ระยะเวลาเดินทางจริง:** {f'{d} วัน ' if d > 0 else ''}{h} ชั่วโมง {m} นาที")
        st.write(f"**จำนวนวันเบี้ยเลี้ยง (ตามระเบียบ):** {per_diem_res['days_count']} วัน ({'กรณีค้างคืน' if st.session_state.is_overnight else 'กรณีไป-กลับ'})")
        
        st.write(f"**เบี้ยเลี้ยง:** {per_diem_res['days_count']} วัน x {per_diem_res['rate_per_day']} บาท, หักมื้ออาหาร {per_diem_res['provided_meals']} มื้อ")
        st.write(f"**ที่พัก:** {accom_res.get('remark', '-')}")
        if meal_budget > 0:
            m_res = st.session_state.training_meal_res
            st.write(f"**งบอาหารอบรม:** อาหาร {m_res['meal_count']} มื้อ, ว่าง {m_res['snack_count']} มื้อ (รวม {meal_budget:,.2f} บาท)")
        if st.session_state.transport_items:
            st.write("**พาหนะ:**")
            for it in st.session_state.transport_items:
                st.write(f"  - {it['type_display']}: {it['route_desc']} — {it['reimbursable_amount']:,.2f} บาท")

    st.markdown('</div>', unsafe_allow_html=True)

    # --- Disclaimer ---
    st.markdown("""
    <div class="notice-box">
        <strong>📌 ข้อพึงระวัง:</strong>
        รูปแบบ PDF เป็นเพียงเอกสารอ้างอิงเบื้องต้น อาจแตกต่างจากแบบฟอร์มจริงของแต่ละหน่วยงาน
        <strong>แนะนำให้พิจารณาจาก "ผลการคำนวณ" เป็นหลัก</strong> และตรวจสอบกับเจ้าหน้าที่การเงินก่อนยื่นเบิก
    </div>
    """, unsafe_allow_html=True)

    # --- สร้าง PDF ---
    st.markdown("### 📤 สร้างเอกสาร PDF")

    if st.button("📄 สร้างไฟล์ PDF", type="primary", use_container_width=True):
        with st.spinner("กำลังสร้างเอกสาร PDF..."):
            transaction_data = {
                "transaction_id": f"TX-{int(datetime.now().timestamp())}",
                "traveler_info": {
                    "full_name": st.session_state.full_name,
                    "position_title": st.session_state.position,
                    "c_level": st.session_state.c_level,
                    "department": st.session_state.department,
                },
                "trip_info": {
                    "purpose": st.session_state.purpose,
                    "destination_province": st.session_state.province,
                    "start_time": start_dt.isoformat(),
                    "end_time": end_dt.isoformat(),
                    "is_overnight": st.session_state.is_overnight,
                    "provided_meals": st.session_state.provided_meals,
                    "order_no": st.session_state.order_no,
                    "order_date": thai_date(st.session_state.order_date, 'long'),
                },
                "loan_contract_no": st.session_state.loan_no,
                "loan_date": thai_date(st.session_state.loan_date, 'long'),
                "expenses": {
                    "per_diem": per_diem_res,
                    "accommodation": accom_res,
                    "transportation": st.session_state.transport_items,
                },
            }

            try:
                gen = GovDocumentGenerator()
                output_file = "GovExpense_Request.pdf"
                gen.generate(transaction_data, output_file)

                with open(output_file, "rb") as f:
                    pdf_bytes = f.read()

                st.success("✅ สร้างไฟล์ PDF สำเร็จ!")

                now = datetime.now()
                fname = f"GovExpense_{now.year + 543}{now.strftime('%m%d')}.pdf"
                st.download_button(
                    "⬇️ ดาวน์โหลดไฟล์ PDF",
                    data=pdf_bytes,
                    file_name=fname,
                    mime="application/pdf",
                    type="primary",
                )

                st.markdown("---")
                st.markdown("### 🔍 ตัวอย่างเอกสาร")
                render_pdf_preview(pdf_bytes, height=850, page_scale=1.3)

            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {e}")
                st.info("ตรวจสอบว่ามีไฟล์ฟอนต์ TH Sarabun New อยู่ใน assets/fonts/")

    # --- Navigation ---
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ ย้อนกลับ", use_container_width=True):
            go_to(3)
            st.rerun()
    with c2:
        if st.button("🔄 เริ่มใหม่", use_container_width=True):
            for key, val in DEFAULTS.items():
                st.session_state[key] = val
            st.rerun()


# =====================================================================
# MAIN ROUTER
# =====================================================================
def main():
    # Title
    st.markdown(
        '<h2 style="text-align:center; color:#2a5075; margin-bottom:0;">'
        '🏛️ GovExpense — ระบบเบิกจ่ายเดินทางไปราชการ</h2>',
        unsafe_allow_html=True,
    )

    # Font check
    if not os.path.exists(os.path.join("assets", "fonts", "THSarabunNew.ttf")):
        st.warning("⚠️ ไม่พบฟอนต์ TH Sarabun New — PDF อาจแสดงผลไม่ถูกต้อง", icon="⚠️")

    render_progress()

    step = st.session_state.step
    if step == 1:
        step_trip_info()
    elif step == 2:
        step_accommodation()
    elif step == 3:
        step_transport()
    elif step == 4:
        step_summary()

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; color:#8a96a6; font-size:0.78rem; padding-bottom:0.5rem;">'
        'GovExpense v3.0 (Wizard) · พัฒนาเพื่อหน่วยงานราชการไทย · '
        'ฟอนต์ TH Sarabun New ตามมาตรฐาน สลค.<br>'
        '⚠️ ผลการคำนวณเป็นเพียงข้อมูลอ้างอิง — กรุณาตรวจสอบกับเจ้าหน้าที่การเงินก่อนยื่นเบิก'
        '</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
