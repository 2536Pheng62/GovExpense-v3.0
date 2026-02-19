import os
from typing import Dict, Any, List
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import textwrap

from expense_calculator import ExpenseCalculator
try:
    from bahttext import bahttext
except ImportError:
    from bahttext_utils import bahttext

class GovDocumentGenerator:
    """
    Generates Thai Government Travel Expense Forms (8708, 4231) using ReportLab Platypus.
    Supports:
    - Automatic Page Breaks for long content
    - Embedding Images (Garuda)
    - Complex Table layouts
    - Thai Font support (TH Sarabun New)
    """
    
    # ==================================================================
    # Thai Government Document Standard - Font & Size Constants
    # ==================================================================
    # มาตรฐานเอกสารราชการไทย:
    #   - ฟอนต์: TH Sarabun New (TTF เท่านั้น, ห้ามใช้ Helvetica/Arial)
    #   - เนื้อหา (Body):     10 pt  | leading = 10 * 1.4 = 14 pt
    #   - หัวข้อ (Header):    14 pt  | leading = 14 * 1.4 ≈ 20 pt (ตัวหนา)
    #   - หมายเหตุ (Footer):   8 pt  | leading =  8 * 1.4 ≈ 11 pt
    #   - ตาราง (Table):      10 pt  | leading = 10 * 1.4 = 14 pt
    # ==================================================================
    FONT_NAME = "THSarabunNew"
    FONT_BOLD = "THSarabunNew-Bold"
    FONT_PATH = os.path.join("assets", "fonts", "THSarabunNew.ttf")
    FONT_BOLD_PATH = os.path.join("assets", "fonts", "THSarabunNew-Bold.ttf")
    GARUDA_PATH = os.path.join("assets", "garuda.png")

    # Font sizes (pt)
    FONT_SIZE_BODY = 10       # เนื้อหา/ข้อความทั่วไป
    FONT_SIZE_HEADER = 14     # หัวข้อ/ชื่อเรื่อง (ตัวหนา)
    FONT_SIZE_FOOTER = 8      # หมายเหตุ/ข้อความเล็ก
    FONT_SIZE_TABLE = 10      # ตาราง

    # Leading multiplier (ระยะห่างบรรทัด = font_size * LEADING_RATIO)
    # 1.4 เหมาะสำหรับภาษาไทย — ป้องกันสระบน/วรรณยุกต์/สระล่าง ทับกัน
    LEADING_RATIO = 1.4

    def __init__(self):
        self._register_font()
        self.styles = self._get_styles()

    def _register_font(self):
        """Registers the Thai font. Raises error if TTF not found (Thai Gov Standard requires TTF only)."""
        font_path = os.path.abspath(self.FONT_PATH)
        bold_path = os.path.abspath(self.FONT_BOLD_PATH)

        if not os.path.exists(font_path):
            raise FileNotFoundError(
                f"[Thai Gov Standard] ไม่พบไฟล์ฟอนต์ TTF ที่ '{font_path}'\n"
                f"ระบบต้องใช้ฟอนต์ TH Sarabun New เท่านั้น ห้ามใช้ Default Font (Helvetica/Arial)"
            )

        try:
            pdfmetrics.registerFont(TTFont(self.FONT_NAME, font_path))
            # Register bold variant (use dedicated bold file if available, otherwise same TTF)
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont(self.FONT_BOLD, bold_path))
            else:
                pdfmetrics.registerFont(TTFont(self.FONT_BOLD, font_path))
            # Register font family for <b> tag support in Paragraphs
            from reportlab.pdfbase.pdfmetrics import registerFontFamily
            registerFontFamily(
                self.FONT_NAME,
                normal=self.FONT_NAME,
                bold=self.FONT_BOLD,
                italic=self.FONT_NAME,
                boldItalic=self.FONT_BOLD,
            )
            self.font_available = True
        except Exception as e:
            raise RuntimeError(
                f"[Thai Gov Standard] โหลดฟอนต์ TTF ไม่สำเร็จ: {e}\n"
                f"ห้ามใช้ Default Font (Helvetica/Arial) ในเอกสารราชการ"
            )

    def _get_styles(self):
        """
        Defines ParagraphStyles for Thai Government Standard documents.
        มาตรฐานเอกสารราชการไทย - กำหนด Style ขนาดฟอนต์และ Leading อย่างเคร่งครัด
        """
        styles = getSampleStyleSheet()

        # ห้ามใช้ Default Font
        font_name = self.FONT_NAME
        font_bold = self.FONT_BOLD

        # Helper: คำนวณ leading จาก font_size
        def _leading(size):
            return round(size * self.LEADING_RATIO)

        # 1. Standard Body Text (เนื้อหา) — 10 pt, leading 14 pt
        styles.add(ParagraphStyle(
            name='ThaiBody',
            fontName=font_name,
            fontSize=self.FONT_SIZE_BODY,            # 10 pt
            leading=_leading(self.FONT_SIZE_BODY),    # 14 pt
            alignment=TA_LEFT,
            firstLineIndent=0,
            spaceBefore=1,
            spaceAfter=2,
        ))

        # 1.1 Justified Body Text — inherits 10 pt
        styles.add(ParagraphStyle(
            name='ThaiJustified',
            parent=styles['ThaiBody'],
            alignment=TA_JUSTIFY,
        ))

        # 2. Header / Title (หัวข้อ) — 14 pt Bold, leading 20 pt
        styles.add(ParagraphStyle(
            name='ThaiTitle',
            parent=styles['Heading1'],
            fontName=font_bold,
            fontSize=self.FONT_SIZE_HEADER,           # 14 pt
            leading=_leading(self.FONT_SIZE_HEADER),   # 20 pt
            alignment=TA_CENTER,
            spaceBefore=2,
            spaceAfter=4,
        ))

        # 3. Small Caption / Footer (หมายเหตุ) — 8 pt, leading 11 pt
        styles.add(ParagraphStyle(
            name='ThaiCaption',
            fontName=font_name,
            fontSize=self.FONT_SIZE_FOOTER,            # 8 pt
            leading=_leading(self.FONT_SIZE_FOOTER),   # 11 pt
            alignment=TA_RIGHT,
            rightIndent=0,
            spaceBefore=0,
            spaceAfter=1,
        ))

        # 4. Table Content (ตาราง) — 10 pt, leading 14 pt
        styles.add(ParagraphStyle(
            name='ThaiTable',
            fontName=font_name,
            fontSize=self.FONT_SIZE_TABLE,             # 10 pt
            leading=_leading(self.FONT_SIZE_TABLE),    # 14 pt
            alignment=TA_LEFT,
        ))

        # 5. Indented Text (ย่อหน้า) — inherits 10 pt, first-line indent
        styles.add(ParagraphStyle(
            name='ThaiIndent',
            parent=styles['ThaiBody'],
            firstLineIndent=1.5*cm,
            alignment=TA_JUSTIFY,
            spaceBefore=1,
            spaceAfter=2,
        ))

        return styles

    def _thai_month(self, month_num, short=False):
        months = [
            "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]
        short_months = [
            "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
            "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
        ]
        return short_months[month_num] if short else months[month_num]

    def generate(self, data: Dict[str, Any], output_path="GovExpense_Form.pdf"):
        """Main entry point to build the PDF."""
        # A4 Size: 210mm x 297mm
        # มาตรฐานราชการไทย: ขอบซ้าย 25mm, ขอบขวา 15mm, บน 20mm, ล่าง 15mm
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2.5*cm,
            rightMargin=1.5*cm,
            topMargin=2.0*cm,
            bottomMargin=1.5*cm
        )
        
        story = []
        
        # --- Part 1: Form 8708 ส่วนที่ ๑ (Request) ---
        story.extend(self._build_part1_story(data, doc.width))
        
        # --- Page 2: Approval & Notes Section ---
        story.append(PageBreak())
        story.extend(self._build_approval_page(data, doc.width))

        # --- Part 2: Form 8708 ส่วนที่ ๒ (Evidence of Payment) ---
        story.append(PageBreak())
        story.extend(self._build_form_8708_part2_story(data, doc.width))
        
        # --- Part 3: Form 4231 (Certificate - Optional) ---
        no_receipt_items = self._get_no_receipt_items(data)
        if no_receipt_items:
            story.append(PageBreak())
            story.extend(self._build_form_4231_story(data, no_receipt_items, doc.width))

        # Build
        doc.build(story)
        return output_path

    # ... (Part 1 logic remains same) ...

    def _build_part1_story(self, data, available_width):
        """Builds Form 8708 Part 1 (ส่วนที่ ๑): ใบเบิกค่าใช้จ่ายในการเดินทางไปราชการ
        Layout matches the official Thai government form image."""
        story = []
        s = self.styles
        font = self.FONT_NAME
        font_b = self.FONT_BOLD
        fs = self.FONT_SIZE_BODY
        fs_sm = self.FONT_SIZE_FOOTER
        _ld = lambda sz: round(sz * self.LEADING_RATIO)
        dot = "............"
        dots = ".............................."

        # --- Styles local to this form ---
        sBody = s['ThaiBody']
        sCenter = ParagraphStyle('P1Center', parent=sBody, alignment=TA_CENTER)
        sRight = ParagraphStyle('P1Right', parent=sBody, alignment=TA_RIGHT)
        sIndent = s['ThaiIndent']
        sSmall = ParagraphStyle('P1Small', parent=sBody, fontSize=fs_sm, leading=_ld(fs_sm))
        sSmallRight = ParagraphStyle('P1SmallR', parent=sSmall, alignment=TA_RIGHT)
        sTitleBold = s['ThaiTitle']

        user = data['traveler_info']
        trip = data['trip_info']
        expenses = data['expenses']

        # ============================================================
        # Row 1: ชื่อส่วนราชการ (left) + แบบ 8708 / ส่วนที่ ๑ (right)
        # ============================================================
        dept_name = user.get('department', dots)
        row1_left = Paragraph(
            f"ชื่อส่วนราชการ <u>{dept_name}</u> เจ้าของงบประมาณ",
            sSmall
        )
        row1_right = Paragraph(
            f"แบบ 8708<br/>ส่วนที่ ๑",
            sSmallRight
        )
        header_row = Table(
            [[row1_left, row1_right]],
            colWidths=[available_width * 0.65, available_width * 0.35]
        )
        header_row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_row)
        story.append(Spacer(1, 0.2 * cm))

        # ============================================================
        # Title: ใบเบิกค่าใช้จ่ายในการเดินทางไปราชการ
        # ============================================================
        story.append(Paragraph("ใบเบิกค่าใช้จ่ายในการเดินทางไปราชการ", sTitleBold))
        story.append(Spacer(1, 0.1 * cm))

        # ============================================================
        # ที่ทำการ ......... วันที่ ... เดือน ... พ.ศ. ...
        # ============================================================
        now = datetime.now()
        thai_year = now.year + 543
        office_date_str = (
            f"ที่ทำการ <u>{dept_name}</u>"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"วันที่ <u> {now.day} </u> เดือน <u> {self._thai_month(now.month)} </u> พ.ศ. <u> {thai_year} </u>"
        )
        story.append(Paragraph(office_date_str, sCenter))
        story.append(Spacer(1, 0.2 * cm))

        # ============================================================
        # เรื่อง / เรียน
        # ============================================================
        story.append(Paragraph("เรื่อง  ขออนุมัติเบิกค่าใช้จ่ายในการเดินทางไปราชการ", sBody))
        story.append(Paragraph("เรียน  อธิบดี / หัวหน้าส่วนราชการ", sBody))
        story.append(Spacer(1, 0.15 * cm))

        # ============================================================
        # Paragraph 1: ตามคำสั่ง/บันทึกที่ ...
        # ============================================================
        order_no = trip.get('order_no', dots)
        order_date = trip.get('order_date', dots)
        txt1 = (
            f"ตามคำสั่ง/บันทึกที่ <u> {order_no} </u> "
            f"ลงวันที่ <u> {order_date} </u> "
            f"ได้อนุมัติให้ ข้าพเจ้า <u> {user['full_name']} </u> "
            f"ตำแหน่ง <u> {user['position_title']} </u> "
            f"สังกัด <u> {user['department']} </u> "
            f"เดินทางไปปฏิบัติราชการ ณ จังหวัด <u> {trip['destination_province']} </u> "
            f"เพื่อ <u> {trip['purpose']} </u>"
        )
        story.append(Paragraph(txt1, sIndent))

        # ============================================================
        # Paragraph 2: โดยออกเดินทางจาก ...
        # ============================================================
        start = datetime.fromisoformat(trip['start_time'])
        departure_from = trip.get('departure_from', 'home')  # home / office
        chk_home = "☑" if departure_from == 'home' else "☐"
        chk_office = "☑" if departure_from == 'office' else "☐"
        txt2 = (
            f"โดยออกเดินทางจาก {chk_home} บ้านพัก {chk_office} สำนักงาน "
            f"ตั้งแต่วันที่ <u> {start.day} </u> "
            f"เดือน <u> {self._thai_month(start.month)} </u> "
            f"พ.ศ. <u> {start.year + 543} </u> "
            f"เวลา <u> {start.strftime('%H:%M')} </u> น."
        )
        story.append(Paragraph(txt2, sIndent))

        # ============================================================
        # Paragraph 3: และกลับถึง ...
        # ============================================================
        end = datetime.fromisoformat(trip['end_time'])
        txt3 = (
            f"และกลับถึง {chk_home} บ้านพัก {chk_office} สำนักงาน "
            f"วันที่ <u> {end.day} </u> "
            f"เดือน <u> {self._thai_month(end.month)} </u> "
            f"พ.ศ. <u> {end.year + 543} </u> "
            f"เวลา <u> {end.strftime('%H:%M')} </u> น."
        )
        story.append(Paragraph(txt3, sIndent))

        # ============================================================
        # Paragraph 4: รวมเวลาไปราชการ
        # ============================================================
        days = expenses['per_diem'].get('days_count', 0)
        hours = int((days % 1) * 24)
        txt4 = f"รวมเวลาไปราชการครั้งนี้ <u> {int(days)} </u> วัน <u> {hours} </u> ชั่วโมง"
        story.append(Paragraph(txt4, sIndent))
        story.append(Spacer(1, 0.15 * cm))

        # ============================================================
        # Expense intro + Total
        # ============================================================
        # Calculate total first
        total = 0
        pd_exp = expenses['per_diem']
        acc_exp = expenses['accommodation']
        trans_list = expenses['transportation']
        if pd_exp['net_amount'] > 0:
            total += pd_exp['net_amount']
        if acc_exp['reimbursable_amount'] > 0:
            total += acc_exp['reimbursable_amount']
        for tr in trans_list:
            total += tr['reimbursable_amount']

        txt_intro = (
            f"ข้าพเจ้าขอเบิกค่าใช้จ่ายในการเดินทางไปราชการครั้งนี้ "
            f"จำนวน <u> {total:,.2f} </u> บาท ดังรายละเอียดดังนี้"
        )
        story.append(Paragraph(txt_intro, sIndent))
        story.append(Spacer(1, 0.1 * cm))

        # ============================================================
        # Expense Table
        # ============================================================
        table_data = [["ลำดับ", "รายการ", "จำนวนเงิน\n(บาท)", "หมายเหตุ"]]
        idx = 1

        if pd_exp['net_amount'] > 0:
            desc = f"ค่าเบี้ยเลี้ยง ({pd_exp['rate_per_day']} บาท x {pd_exp['days_count']} วัน)"
            table_data.append([str(idx), desc, f"{pd_exp['net_amount']:,.2f}", ""])
            idx += 1

        if acc_exp['reimbursable_amount'] > 0:
            acc_type = "เหมาจ่าย" if acc_exp['type'] == "lump_sum" else "จ่ายจริง"
            desc = f"ค่าที่พัก ({acc_type}) {acc_exp['nights']} คืน"
            table_data.append([str(idx), desc, f"{acc_exp['reimbursable_amount']:,.2f}", ""])
            idx += 1

        for tr in trans_list:
            desc = f"ค่าพาหนะ ({tr.get('type_display', tr['type'])})"
            if tr.get('route_desc'):
                desc += f" - {tr['route_desc']}"
            table_data.append([str(idx), desc, f"{tr['reimbursable_amount']:,.2f}", ""])
            idx += 1

        # Total row
        table_data.append(["", "รวมเงินทั้งสิ้น", f"{total:,.2f}", ""])

        c_no = 1.0 * cm
        c_amt = 2.5 * cm
        c_rem = 2.0 * cm
        c_desc = available_width - (c_no + c_amt + c_rem)

        tbl = Table(table_data, colWidths=[c_no, c_desc, c_amt, c_rem], repeatRows=1)
        tbl.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), font, self.FONT_SIZE_TABLE),
            ('LEADING', (0, 0), (-1, -1), _ld(self.FONT_SIZE_TABLE)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('SPAN', (0, -1), (1, -1)),
            ('ALIGN', (0, -1), (1, -1), 'RIGHT'),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.1 * cm))

        # ============================================================
        # ตัวอักษร (... bahttext ...)
        # ============================================================
        try:
            bt_text = bahttext(total)
        except:
            bt_text = "-"
        story.append(Paragraph(
            f"ตัวอักษร ( {bt_text} )",
            sCenter
        ))
        story.append(Spacer(1, 0.15 * cm))

        # ============================================================
        # Certification Text (2 lines)
        # ============================================================
        story.append(Paragraph(
            "ข้าพเจ้าขอรับรองว่ารายจ่ายดังกล่าวข้างต้นเป็นจริงทุกประการ และเป็นผู้มีสิทธิเบิกค่าใช้จ่ายในการเดินทางบริบูรณ์",
            sIndent
        ))
        story.append(Paragraph(
            "ข้าพเจ้าขอรับรองว่ารายจ่ายข้างต้นนี้ไม่อาจเรียกใบเสร็จรับเงินจากผู้รับเงินได้ "
            "และข้าพเจ้าได้จ่ายไปในงานของทางราชการโดยแท้จริง",
            sIndent
        ))
        story.append(Spacer(1, 0.4 * cm))

        # ============================================================
        # Signature: ผู้ขอรับเงิน (right aligned)
        # ============================================================
        sig_width = 7.0 * cm
        spacer_width = available_width - sig_width

        sig_data = [
            [Paragraph("ลงชื่อ............................................ผู้ขอรับเงิน", sCenter)],
            [Paragraph(f"( {user['full_name']} )", sCenter)],
            [Paragraph(f"ตำแหน่ง {user['position_title']}", sCenter)],
        ]
        sig_inner = Table(sig_data, colWidths=[sig_width])
        sig_inner.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))

        layout = Table([[None, sig_inner]], colWidths=[spacer_width, sig_width])
        layout.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        story.append(KeepTogether(layout))

        return story

    # =================================================================
    # Page 2: Approval / Verification / Notes  (ส่วนตรวจสอบ + อนุมัติ + หมายเหตุ)
    # =================================================================
    def _build_approval_page(self, data, available_width):
        """Builds page 2: Verification, Approval signatures, and Notes.
        Matches the official form layout with:
          - Top: reviewer + authorizer verification block (boxed)
          - Middle: approval decision + authorizer signature
          - Bottom: หมายเหตุ (notes on regulations)
        """
        from reportlab.platypus import HRFlowable

        story = []
        s = self.styles
        font = self.FONT_NAME
        font_b = self.FONT_BOLD
        fs = self.FONT_SIZE_BODY
        fs_sm = self.FONT_SIZE_FOOTER
        _ld = lambda sz: round(sz * self.LEADING_RATIO)
        sBody = s['ThaiBody']
        sCenter = ParagraphStyle('A_Center', parent=sBody, alignment=TA_CENTER)
        sIndent = s['ThaiIndent']
        sTitleBold = s['ThaiTitle']
        sSmall = ParagraphStyle('A_Small', parent=sBody, fontSize=fs_sm, leading=_ld(fs_sm))
        sBullet = ParagraphStyle('A_Bullet', parent=sSmall, leftIndent=1.0*cm, bulletIndent=0.3*cm)

        user = data['traveler_info']

        # --- Calculate total ---
        expenses = data['expenses']
        total_amount = (
            expenses['per_diem']['net_amount'] +
            expenses['accommodation']['reimbursable_amount'] +
            sum(item['reimbursable_amount'] for item in expenses['transportation'])
        )
        try:
            bt_text = bahttext(total_amount)
        except:
            bt_text = "-"

        dots = "......................................"
        dot_line = "............................................."

        # ============================================================
        # Section 1: Verification Block (boxed area)
        # กรอบตรวจสอบหลักฐานการจ่ายเงิน และอนุมัติ
        # ============================================================
        story.append(Paragraph(
            "ที่ทำการตรวจสอบหลักฐานการจ่ายเงินค่าใช้จ่ายในการเดินทางไปราชการ",
            sBody
        ))
        story.append(Paragraph(
            "เห็นควรอนุมัติจ่ายเงินได้",
            sBody
        ))
        story.append(Spacer(1, 0.2*cm))

        # Two-column signature block: ผู้ตรวจสอบ (left) + ผู้อนุมัติ (right)
        half_w = available_width * 0.48
        gap_w = available_width * 0.04

        left_sigs = [
            [Paragraph("ลงชื่อ" + dot_line, sCenter)],
            [Paragraph("(" + dot_line + ")", sCenter)],
            [Paragraph("ตำแหน่ง" + dot_line, sCenter)],
        ]
        right_sigs = [
            [Paragraph("ลงชื่อ" + dot_line, sCenter)],
            [Paragraph("(" + dot_line + ")", sCenter)],
            [Paragraph("ตำแหน่ง" + dot_line, sCenter)],
        ]

        left_tbl = Table(left_sigs, colWidths=[half_w])
        left_tbl.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ]))

        right_tbl = Table(right_sigs, colWidths=[half_w])
        right_tbl.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ]))

        # Labels above the signature columns
        label_row = Table(
            [[Paragraph("ผู้ตรวจสอบ", sCenter), None, Paragraph("ผู้อนุมัติ", sCenter)]],
            colWidths=[half_w, gap_w, half_w]
        )
        label_row.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        story.append(label_row)
        story.append(Spacer(1, 0.2*cm))

        sig_row = Table(
            [[left_tbl, None, right_tbl]],
            colWidths=[half_w, gap_w, half_w]
        )
        sig_row.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(sig_row)
        story.append(Spacer(1, 0.5*cm))

        # ============================================================
        # Section 2: Verification text + Approval decision
        # ============================================================
        # Horizontal line separator
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceAfter=0.3*cm))

        verify_txt = (
            f"ได้ตรวจสอบใบเบิกค่าใช้จ่ายในการเดินทางไปราชการแล้ว "
            f"จำนวน <u> {total_amount:,.2f} </u> บาท"
        )
        story.append(Paragraph(verify_txt, sIndent))

        # Checkbox line
        story.append(Paragraph(
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "☑ ถูกต้องตามที่เบิกทุกประการ",
            sBody
        ))
        story.append(Spacer(1, 0.35*cm))

        # Authorizer signature (right-aligned)
        sig_width = 7.0 * cm
        spacer_width = available_width - sig_width

        auth_sig = [
            [Paragraph("ลงชื่อ" + dot_line + "ผู้อนุมัติ", sCenter)],
            [Paragraph("(" + dot_line + ")", sCenter)],
            [Paragraph("ตำแหน่ง" + dot_line, sCenter)],
        ]
        auth_tbl = Table(auth_sig, colWidths=[sig_width])
        auth_tbl.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ]))

        auth_layout = Table([[None, auth_tbl]], colWidths=[spacer_width, sig_width])
        auth_layout.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story.append(auth_layout)
        story.append(Spacer(1, 0.5*cm))

        # ============================================================
        # Section 3: Horizontal line + หมายเหตุ (Notes)
        # ============================================================
        story.append(HRFlowable(width="100%", thickness=1.0, color=colors.black, spaceAfter=0.3*cm))

        story.append(Paragraph("หมายเหตุ", ParagraphStyle(
            'NoteHeader', parent=sBody, fontName=font_b, spaceBefore=2, spaceAfter=3
        )))

        notes = [
            "การเบิกค่าใช้จ่ายในการเดินทางไปราชการให้เบิกจ่ายตามสิทธิตามพระราชกฤษฎีกาค่าใช้จ่ายในการเดินทางไปราชการ "
            "พ.ศ. ๒๕ฦ๓ และระเบียบกระทรวงการคลังว่าด้วยการเบิกค่าใช้จ่ายในการเดินทางไปราชการ",

            "ค่าเบี้ยเลี้ยงเดินทาง ต้องหักมื้ออาหารที่ทางราชการจัดเลี้ยงให้ "
            "โดยหักมื้อละ 1/3 ของอัตราเบี้ยเลี้ยงเดินทางต่อวันต่อมื้อ",

            "กรณีเดินทางไปราชการโดยรถยนต์ส่วนบุคคล ให้เบิกค่าชดเชยตามระยะทางจริง ทั้งนี้ ผู้เบิกต้องแนบสำเนา "
            "คำสั่งอนุมัติให้ใช้รถยนต์ส่วนบุคคลประกอบด้วย",

            "การเบิกค่าเช่าที่พักแบบเหมาจ่าย ให้ออกใบรับรองแทนใบเสร็จรับเงิน (แบบ บก.111) ประกอบการเบิกจ่าย "
            "และให้ผู้เบิกลงชื่อรับรองในใบรับรองแทนใบเสร็จรับเงินด้วย",
        ]

        for note_text in notes:
            story.append(Paragraph(
                f"<bullet>&bull;</bullet>{note_text}",
                sBullet
            ))
            story.append(Spacer(1, 0.06*cm))

        return story

    def _build_form_8708_part2_story(self, data, available_width):
        """Builds Form 8708 Part 2: Evidence of Payment (ใบสำคัญรับเงิน/หลักฐานการจ่าย)."""
        story = []
        s = self.styles
        
        # 1. Header (Part 2)
        story.append(Paragraph("ส่วนที่ 2", s['ThaiCaption']))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("หลักฐานการจ่ายเงินค่าใช้จ่ายในการเดินทางไปราชการ", s['ThaiTitle']))
        
        story.append(Paragraph(f"ส่วนราชการ {data['traveler_info']['department']}", s['ThaiTitle']))
        story.append(Paragraph(f"จังหวัด {data['trip_info']['destination_province']}", s['ThaiTitle']))
        story.append(Spacer(1, 0.3*cm))
        
        # 2. Reference Info
        loan_no = data.get("loan_contract_no", "..........")
        loan_date = data.get("loan_date", "..........")
        
        txt_ref = f"ประกอบฎีกา/รายงาน............................................. สัญญาเงินยืมเลขที่ {loan_no} วันที่ {loan_date}"
        story.append(Paragraph(txt_ref, s['ThaiBody']))
        
        txt_name = f"ชื่อผู้เดินทาง {data['traveler_info']['full_name']} สังกัด {data['traveler_info']['department']}"
        story.append(Paragraph(txt_name, s['ThaiBody']))
        
        txt_amt_text = "จำนวนเงินรวมทั้งสิ้น (ตัวอักษร) ...................................................................................................................."
        story.append(Paragraph(txt_amt_text, s['ThaiBody']))
        
        # Calculate Total again
        expenses = data['expenses']
        total_amount = (
            expenses['per_diem']['net_amount'] + 
            expenses['accommodation']['reimbursable_amount'] + 
            sum(item['reimbursable_amount'] for item in expenses['transportation'])
        )
        try:
             baht_text_val = bahttext(total_amount)
        except:
             baht_text_val = "-"
             
        # Overlay Baht Text
        story.append(Paragraph(f"(   {baht_text_val}   )", ParagraphStyle('Centered', parent=s['ThaiBody'], alignment=TA_CENTER)))
        story.append(Spacer(1, 0.3*cm))
        
        story.append(Paragraph("ข้าพเจ้าขอรับรองว่ารายจ่ายข้างต้นนี้ไม่อาจเรียกใบเสร็จรับเงินจากผู้รับได้ และข้าพเจ้าได้จ่ายไปในงานของทางราชการโดยแท้", s['ThaiBody']))
        story.append(Spacer(1, 0.6*cm))
        
        # 3. Signatures
        sig_width = 7.5*cm
        spacer_width = available_width - sig_width
        
        user = data['traveler_info']
        sig_content = [
            [Paragraph("ลงชื่อ...................................................ผู้จ่ายเงิน", s['ThaiBody'])],
            [Paragraph(f"( {user['full_name']} )", s['ThaiBody'])],
            [Paragraph(f"ตำแหน่ง {user['position_title']}", s['ThaiBody'])],
        ]
        sig_table = Table(sig_content, colWidths=[sig_width])
        sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        
        container = Table([[None, sig_table]], colWidths=[spacer_width, sig_width])
        story.append(container)
        story.append(Spacer(1, 0.4*cm))

        # 4. Detailed Expense Table
        story.append(Paragraph("รายละเอียดรายการจ่ายเงิน", s['ThaiTitle'])) # Sub-header
        
        table_data = [["ลำดับ", "รายการ", "จำนวนเงิน", "หมายเหตุ"]]
        idx = 1
        
        # Per Diem
        pd = expenses['per_diem']
        if pd['net_amount'] > 0:
            table_data.append([str(idx), f"ค่าเบี้ยเลี้ยง ({pd['days_count']} วัน)", f"{pd['net_amount']:,.2f}", ""])
            idx += 1
            
        # Accommodation
        acc = expenses['accommodation']
        if acc['reimbursable_amount'] > 0:
            desc = "ค่าเช่าที่พัก"
            if acc['type'] == 'lump_sum':
                 desc += " (เหมาจ่าย)"
            table_data.append([str(idx), desc, f"{acc['reimbursable_amount']:,.2f}", ""])
            idx += 1
            
        # Transport
        for t in expenses['transportation']:
            desc = f"ค่าพาหนะ ({t.get('type_display', t['type'])})"
            table_data.append([str(idx), desc, f"{t['reimbursable_amount']:,.2f}", ""])
            idx += 1

        # Total
        table_data.append(["", "รวมเงิน", f"{total_amount:,.2f}", ""])
        
        # Table Style
        c_no = 1.0*cm
        c_amt = 2.5*cm
        c_rem = 2.5*cm
        c_desc = available_width - (c_no + c_amt + c_rem)
        
        t = Table(table_data, colWidths=[c_no, c_desc, c_amt, c_rem], repeatRows=1)
        t.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), s['ThaiTable'].fontName, self.FONT_SIZE_TABLE),
            ('LEADING', (0,0), (-1,-1), round(self.FONT_SIZE_TABLE * self.LEADING_RATIO)),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.Color(0.92, 0.92, 0.92)),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('ALIGN', (2,1), (2,-1), 'RIGHT'),
            ('SPAN', (0,-1), (1,-1)),
            ('ALIGN', (0,-1), (0,-1), 'RIGHT'),
        ]))
        story.append(t)
        
        return story

    def _build_form_4231_story(self, data, items, available_width):
        """Builds Form 4231 story (Certificate in lieu of receipt)."""
        story = []
        s = self.styles
        
        story.append(Paragraph("ใบรับรองแทนใบเสร็จรับเงิน (แบบ บก.111)", s['ThaiTitle']))
        story.append(Paragraph(f"ส่วนราชการ {data['traveler_info']['department']}", s['ThaiTitle']))
        story.append(Spacer(1, 0.3*cm))
        
        # Table
        table_data = [["วัน/เดือน/ปี", "รายละเอียดรายจ่าย", "จำนวนเงิน", "หมายเหตุ"]]
        total = 0
        for item in items:
             desc = item['description']
             d = datetime.fromisoformat(item['date'])
             date_str = f"{d.day:02d}/{d.month:02d}/{d.year + 543}"
             amt = item['amount']
             table_data.append([date_str, desc, f"{amt:,.2f}", ""])
             total += amt

        table_data.append(["", "รวมเป็นเงิน", f"{total:,.2f}", ""])

        # Col Widths
        c_date = 2.5*cm
        c_amt = 2.5*cm
        c_rem = 2.0*cm
        c_desc = available_width - (c_date + c_amt + c_rem)
        
        t = Table(table_data, colWidths=[c_date, c_desc, c_amt, c_rem], repeatRows=1)
        t.setStyle(TableStyle([
             ('FONT', (0,0), (-1,-1), s['ThaiTable'].fontName, self.FONT_SIZE_TABLE),
             ('LEADING', (0,0), (-1,-1), round(self.FONT_SIZE_TABLE * self.LEADING_RATIO)),
             ('GRID', (0,0), (-1,-1), 0.5, colors.black),
             ('BACKGROUND', (0,0), (-1,0), colors.Color(0.92, 0.92, 0.92)),
             ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
             ('TOPPADDING', (0,0), (-1,-1), 2),
             ('BOTTOMPADDING', (0,0), (-1,-1), 2),
             ('ALIGN', (2,1), (2,-1), 'RIGHT'), # Amount
             ('SPAN', (0,-1), (1,-1)),
             ('ALIGN', (0,-1), (0,-1), 'RIGHT'),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))
        
        # Certification Text
        story.append(Paragraph("ข้าพเจ้าขอรับรองว่ารายจ่ายข้างต้นนี้ไม่อาจเรียกใบเสร็จรับเงินจากผู้รับได้ และข้าพเจ้าได้จ่ายไปในงานของทางราชการโดยแท้", s['ThaiBody']))
        story.append(Spacer(1, 0.4*cm))
        
        # Signatures
        sig_width = 7.5*cm
        spacer_width = available_width - sig_width
        
        user = data['traveler_info']
        sig_data = [
            [Paragraph("ลงชื่อ...................................................ผู้เบิก", s['ThaiBody'])],
            [Paragraph(f"( {user['full_name']} )", s['ThaiBody'])],
            [Paragraph(f"ตำแหน่ง {user['position_title']}", s['ThaiBody'])],
        ]
        sig_inner = Table(sig_data, colWidths=[sig_width])
        sig_inner.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        
        container = Table([[None, sig_inner]], colWidths=[spacer_width, sig_width])
        story.append(container)
        
        return story

    def _get_no_receipt_items(self, data):
        # ... logic similar to previous ...
        items = []
        for trans in data["expenses"]["transportation"]:
            if trans["type"] in ["taxi", "motorcycle"]:
                items.append({
                    "date": data["trip_info"]["end_time"],
                    "description": f"ค่าพาหนะ ({trans.get('type_display', trans['type'])}) {trans.get('route_desc', '')}",
                    "amount": trans["reimbursable_amount"],
                    "remark": ""
                })
        accom = data["expenses"]["accommodation"]
        if accom["type"] == "lump_sum":
             items.append({
                "date": data["trip_info"]["end_time"],
                "description": f"ค่าเช่าที่พัก (เหมาจ่าย) {accom['nights']} คืน",
                "amount": accom["reimbursable_amount"],
                "remark": ""
            })
        return items
