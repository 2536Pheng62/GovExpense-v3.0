# 🚀 Deployment Guide — GovExpense on Streamlit Cloud

## 📁 โครงสร้างไฟล์ที่จำเป็นสำหรับ Deploy

```
Cal_allowance/
├── app.py                  ← Entry point (Wizard UI)
├── expense_calculator.py   ← Logic คำนวณ
├── pdf_generator.py        ← สร้าง PDF
├── pdf_preview.py          ← PDF.js preview component
├── bahttext_utils.py       ← แปลงเงินเป็นตัวอักษรไทย
├── requirements.txt        ← Dependencies
├── .gitignore              ← ไฟล์ที่ไม่อัปโหลด
└── assets/
    ├── fonts/
    │   └── THSarabunNew.ttf
    └── garuda.png
```

---

## 1️⃣ เตรียม GitHub Repository

### ขั้นตอน

```bash
# 1. สร้าง .gitignore (ถ้ายังไม่มี)
# ใส่เนื้อหาด้านล่าง

# 2. เริ่ม Git
cd C:\Users\UsEr\OneDrive\Apps\Cal_allowance
git init
git add .
git commit -m "Initial commit: GovExpense v3.0"

# 3. สร้าง Repository บน GitHub
#    - ไปที่ https://github.com/new
#    - ตั้งชื่อ: govexpense (หรือชื่อที่ต้องการ)
#    - เลือก Private หรือ Public ตามต้องการ
#    - ห้ามเลือก "Add README" (เพราะเรามีไฟล์อยู่แล้ว)

# 4. Push ขึ้น GitHub
git remote add origin https://github.com/<YOUR_USERNAME>/govexpense.git
git branch -M main
git push -u origin main
```

### .gitignore ที่แนะนำ

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
.venv/
temp_venv/

# IDE
.vscode/
.idea/

# Output
*.pdf
!assets/**

# OS
.DS_Store
Thumbs.db

# Logs
*.log
*.txt
!requirements.txt
!README.md
```

---

## 2️⃣ Deploy บน Streamlit Cloud

### ขั้นตอน

1. **เปิด** [share.streamlit.io](https://share.streamlit.io)
2. **Sign in** ด้วย GitHub account
3. **กดปุ่ม** "New app"
4. **กรอกข้อมูล:**

   | ช่อง | ค่า |
   |------|-----|
   | Repository | `<YOUR_USERNAME>/govexpense` |
   | Branch | `main` |
   | Main file path | `app.py` |

5. **กด** "Deploy!" — รอ 2-3 นาที
6. **เสร็จ!** แอปจะได้ URL:
   ```
   https://<YOUR_USERNAME>-govexpense-app-xxxxx.streamlit.app
   ```

---

## 3️⃣ ข้อควรระวัง

### ฟอนต์ TH Sarabun New
- ไฟล์ `assets/fonts/THSarabunNew.ttf` **ต้องอยู่ใน Repository**
- Streamlit Cloud ไม่มีฟอนต์ไทยติดตั้ง — แอปจะอ่านจากโฟลเดอร์ `assets/`
- ถ้าต้องการ Bold ให้เพิ่ม `THSarabunNew-Bold.ttf` ด้วย

### ขนาดไฟล์
- GitHub Free รองรับไฟล์ไม่เกิน 100 MB
- ฟอนต์ TTF ขนาด ~1-2 MB ไม่มีปัญหา
- ถ้ามีไฟล์ใหญ่ (เช่น `.pdf` ตัวอย่าง) ให้ใส่ใน `.gitignore`

### Streamlit Cloud Limits (Free Tier)
- 1 GB RAM
- แอปจะ "sleep" หลังไม่มีคนใช้ 7 วัน (กด Reboot ได้)
- รองรับ public URL ให้คนอื่นเข้าใช้ได้

---

## 4️⃣ อัปเดตแอป

หลัง Deploy แล้ว เมื่อต้องการอัปเดต:

```bash
# แก้ไขไฟล์ตามต้องการ แล้ว
git add .
git commit -m "Update: ..."
git push
```

Streamlit Cloud จะ **auto-redeploy** ทุกครั้งที่ Push ขึ้น `main` branch

---

## 5️⃣ ทดสอบ Local ก่อน Deploy

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# ติดตั้ง dependencies
pip install -r requirements.txt

# รัน local
streamlit run app.py
```

เปิดเบราว์เซอร์ที่ `http://localhost:8501`
