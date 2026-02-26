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
    
    FONT_NAME = "THSarabunNew"
    FONT_BOLD = "THSarabunNew-Bold" # Assuming you might add bold font later
    FONT_PATH = os.path.join("assets", "fonts", "THSarabunNew.ttf")
    GARUDA_PATH = os.path.join("assets", "garuda.png")

    def __init__(self):
        self._register_font()
        self.styles = self._get_styles()

    def _register_font(self):
        """Registers the Thai font. Fallbacks to Helvetica if not found."""
        if os.path.exists(self.FONT_PATH):
            try:
                pdfmetrics.registerFont(TTFont(self.FONT_NAME, self.FONT_PATH))
                # For this example, we use the same font for bold if bold file not present
                # In production, register THSarabunNew-Bold.ttf
                pdfmetrics.registerFont(TTFont(self.FONT_BOLD, self.FONT_PATH)) 
                self.font_available = True
            except Exception as e:
                print(f"Error loading font: {e}")
                self.font_available = False
        else:
            print(f"Warning: Thai font not found at {self.FONT_PATH}. Using Helvetica.")
            self.font_available = False

    def _get_styles(self):
        """Defines ParagraphStyles for the document."""
        styles = getSampleStyleSheet()
        
        # Base Font Name
        font_name = self.FONT_NAME if self.font_available else "Helvetica"
        
        # 1. Standard Body Text
        styles.add(ParagraphStyle(
            name='ThaiBody',
            fontName=font_name,
            fontSize=12,
            leading=13,
            alignment=TA_LEFT,
            firstLineIndent=0,
            spaceAfter=0,
        ))
        
        # 1.1 Justified Body Text
        styles.add(ParagraphStyle(
            name='ThaiJustified',
            parent=styles['ThaiBody'],
            alignment=TA_JUSTIFY,
        ))

        # 2. Header / Title
        styles.add(ParagraphStyle(
            name='ThaiTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=14,
            leading=16,
            alignment=TA_CENTER,
            spaceAfter=5,
        ))

        # 3. Small Caption (e.g. form number top right)
        styles.add(ParagraphStyle(
            name='ThaiCaption',
            fontName=font_name,
            fontSize=12,
            leading=14,
            alignment=TA_RIGHT,
            rightIndent=0,
        ))

        # 4. Table Content
        styles.add(ParagraphStyle(
            name='ThaiTable',
            fontName=font_name,
            fontSize=12,
            leading=13,
            alignment=TA_LEFT,
        ))
        
        # 5. Indented Text
        styles.add(ParagraphStyle(
            name='ThaiIndent',
            parent=styles['ThaiBody'],
            firstLineIndent=1.5*cm, 
            alignment=TA_JUSTIFY,
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
        # Margins: Left 30mm, Right 20mm
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=3.0*cm,
            rightMargin=2.0*cm,
            topMargin=1.5 * cm,
            bottomMargin=1.0 * cm
        )
        
        story = []
        
        # --- Part 1: Form 8708 (Request) ---
        story.extend(self._build_part1_story(data, doc.width))
        
        # --- Part 2: Form 8708 (Evidence of Payment/Clearance) ---
        # "Bai Clear" usually implies this form
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
        """Builds Form 8708 Part 1: Request (ใบเบิกค่าใช้จ่าย)."""
        story = []
        s = self.styles
        
        # 1. Top Right Form Number
        story.append(Paragraph("แบบ 8708", s['ThaiCaption']))
        story.append(Spacer(1, 0.2*cm))

        # 2. Header with Logo (Table Layout)
        # Check if Garuda exists
        header_data = []
        if os.path.exists(self.GARUDA_PATH):
            im = Image(self.GARUDA_PATH, width=2.2*cm, height=2.0*cm) # Reduced further
            header_data = [[im]]
            # Center the logo in a table
            t_logo = Table(header_data, colWidths=[available_width], style=[
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ])
            story.append(t_logo)
        
        # Add Title below logo
        story.append(Paragraph("ใบเบิกค่าใช้จ่ายในการเดินทางไปราชการ", s['ThaiTitle']))
        story.append(Paragraph(f"ที่ทำการ {data['traveler_info']['department']}", s['ThaiTitle']))
        
        # 3. Date
        now = datetime.now()
        date_str = f"วันที่ {now.day} เดือน {self._thai_month(now.month)} พ.ศ. {now.year + 543}"
        story.append(Paragraph(date_str, s['ThaiBody'])) 
        story.append(Spacer(1, 0.2*cm))
        
        # 4. Subject & Dear
        story.append(Paragraph("เรื่อง  ขออนุมัติเบิกค่าใช้จ่ายในการเดินทางไปราชการ", s['ThaiBody']))
        story.append(Paragraph("เรียน  อธิบดีกรมธนารักษ์ (หรือหัวหน้าส่วนราชการ)", s['ThaiBody']))
        story.append(Spacer(1, 0.2*cm))

        # 5. Body Text
        user = data['traveler_info']
        trip = data['trip_info']
        
        # Paragraph 1
        order_no = trip.get('order_no', '..........................................')
        order_date = trip.get('order_date', '..........................................')
        txt1 = f"ตามคำสั่ง/บันทึกที่ {order_no} ลงวันที่ {order_date} ได้อนุมัติให้ ข้าพเจ้า {user['full_name']} ตำแหน่ง {user['position_title']} สังกัด {user['department']} เดินทางไปปฏิบัติราชการ ณ จังหวัด {trip['destination_province']} เพื่อ {trip['purpose']}"
        story.append(Paragraph(txt1, s['ThaiIndent']))
        
        # Paragraph 2: Departure
        start = datetime.fromisoformat(trip['start_time'])
        txt2 = f"โดยออกเดินทางจาก {'[ / ]' if True else '[ ]'} บ้านพัก {'[ ]'} สำนักงาน {'[ ]'} ประเทศไทย ตั้งแต่วันที่ {start.day} เดือน {self._thai_month(start.month)} พ.ศ. {start.year+543} เวลา {start.strftime('%H:%M')} น."
        story.append(Paragraph(txt2, s['ThaiIndent']))

        # Paragraph 3: Return
        end = datetime.fromisoformat(trip['end_time'])
        txt3 = f"และกลับถึง {'[ / ]' if True else '[ ]'} บ้านพัก {'[ ]'} สำนักงาน {'[ ]'} ประเทศไทย วันที่ {end.day} เดือน {self._thai_month(end.month)} พ.ศ. {end.year+543} เวลา {end.strftime('%H:%M')} น."
        story.append(Paragraph(txt3, s['ThaiIndent']))
        
        # Paragraph 4: Duration
        days = data['expenses']['per_diem'].get('days_count', 0)
        txt4 = f"รวมเวลาไปราชการครั้งนี้ {int(days)} วัน {int((days%1)*24)} ชั่วโมง"
        story.append(Paragraph(txt4, s['ThaiIndent']))
        story.append(Spacer(1, 0.2*cm))

        # 6. Expenses Table
        story.append(Paragraph("ข้าพเจ้าขอเบิกค่าใช้จ่ายในการเดินทางไปราชการ ดังนี้", s['ThaiIndent']))
        story.append(Spacer(1, 0.1*cm))
        
        # Build Table Data
        table_data = []
        table_data.append(["ลำดับ", "รายการ", "จำนวนเงิน", "หมายเหตุ"])
        
        expenses = data['expenses']
        total = 0
        idx = 1
        
        # Per Diem
        pd = expenses['per_diem']
        if pd['net_amount'] > 0:
            desc = f"ค่าเบี้ยเลี้ยง ({pd['rate_per_day']} บาท x {pd['days_count']} วัน)"
            table_data.append([str(idx), desc, f"{pd['net_amount']:,.2f}", ""])
            total += pd['net_amount']
            idx += 1
            
        # Accommodation
        acc = expenses['accommodation']
        if acc['reimbursable_amount'] > 0:
            acc_type = "เหมาจ่าย" if acc['type'] == "lump_sum" else "จ่ายจริง"
            desc = f"ค่าที่พัก ({acc_type}) {acc['nights']} คืน"
            table_data.append([str(idx), desc, f"{acc['reimbursable_amount']:,.2f}", ""])
            total += acc['reimbursable_amount']
            idx += 1
            
        # Transport
        for t in expenses['transportation']:
            desc = f"ค่าพาหนะ ({t.get('type_display', t['type'])})"
            if t.get('route_desc'):
                desc += f" - {t['route_desc']}"
            table_data.append([str(idx), desc, f"{t['reimbursable_amount']:,.2f}", ""])
            total += t['reimbursable_amount']
            idx += 1
            
        # Total Row
        table_data.append(["", "รวมเงินทั้งสิ้น", f"{total:,.2f}", ""])
        
        # Table Layout
        c_no = 1.2*cm
        c_amt = 3.0*cm
        c_rem = 3.0*cm
        c_desc = available_width - (c_no + c_amt + c_rem)
        
        col_widths = [c_no, c_desc, c_amt, c_rem]
        
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), s['ThaiTable'].fontName, 12),
            ('ALIGN', (0,0), (-1,0), 'CENTER'), # Header Center
            ('ALIGN', (-2,1), (-2,-1), 'RIGHT'), # Amount Right
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('SPAN', (0,-1), (1,-1)), 
            ('ALIGN', (0,-1), (0,-1), 'RIGHT'),
            ('FONT', (0,-1), (-1,-1), s['ThaiTable'].fontName, 12),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ]))
        
        story.append(t)
        story.append(Spacer(1, 0.2*cm))
        
        # Baht Text with centered dashed format
        try:
            bt_text = bahttext(total)
        except:
            bt_text = "-"
        story.append(Paragraph(f"( ตัวอักษร )  (  {bt_text}  )", ParagraphStyle('Centered', parent=s['ThaiBody'], alignment=TA_CENTER)))
        story.append(Spacer(1, 0.4*cm))

        # 7. Signatures
        sig_width = 8.5*cm
        spacer_width = available_width - sig_width
        
        sig_content = [
            [Paragraph("ลงชื่อ...................................................ผู้ขอรับเงิน", s['ThaiBody'])],
            [Paragraph(f"( {user['full_name']} )", s['ThaiBody'])],
            [Paragraph(f"ตำแหน่ง {user['position_title']}", s['ThaiBody'])],
            [Spacer(1, 0.3*cm)],
            [Paragraph("ลงชื่อ...................................................ผู้จ่ายเงิน/ตรวจสอบ", s['ThaiBody'])],
            [Paragraph("(...................................................)", s['ThaiBody'])],
            [Paragraph("ตำแหน่ง...................................................", s['ThaiBody'])],
        ]
        
        sig_inner_table = Table(sig_content, colWidths=[sig_width])
        sig_inner_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
        # Main layout table to push signature block to right
        layout_table = Table([[None, sig_inner_table]], colWidths=[spacer_width, sig_width])
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
        story.append(layout_table)
        
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
        story.append(Spacer(1, 0.5*cm))
        
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
        story.append(Spacer(1, 0.5*cm))
        
        story.append(Paragraph("ข้าพเจ้าขอรับรองว่ารายจ่ายข้างต้นนี้ไม่อาจเรียกใบเสร็จรับเงินจากผู้รับได้ และข้าพเจ้าได้จ่ายไปในงานของทางราชการโดยแท้", s['ThaiBody']))
        story.append(Spacer(1, 0.5*cm))
        
        # 3. Signatures
        sig_width = 8.5*cm
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
        story.append(Spacer(1, 1*cm))

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
        c_no = 1.2*cm
        c_amt = 3.0*cm
        c_rem = 3.0*cm
        c_desc = available_width - (c_no + c_amt + c_rem)
        
        t = Table(table_data, colWidths=[c_no, c_desc, c_amt, c_rem], repeatRows=1)
        t.setStyle(TableStyle([
            ('FONT', (0,0), (-1,-1), s['ThaiTable'].fontName, 14),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
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
        story.append(Spacer(1, 0.5*cm))
        
        # Table
        table_data = [["วัน/เดือน/ปี", "รายละเอียดรายจ่าย", "จำนวนเงิน", "หมายเหตุ"]]
        total = 0
        for item in items:
             desc = item['description']
             date_str = datetime.fromisoformat(item['date']).strftime('%d/%m/%Y')
             amt = item['amount']
             table_data.append([date_str, desc, f"{amt:,.2f}", ""])
             total += amt

        table_data.append(["", "รวมเป็นเงิน", f"{total:,.2f}", ""])

        # Col Widths
        c_date = 3.0*cm
        c_amt = 3.0*cm
        c_rem = 2.0*cm
        c_desc = available_width - (c_date + c_amt + c_rem)
        
        t = Table(table_data, colWidths=[c_date, c_desc, c_amt, c_rem], repeatRows=1)
        t.setStyle(TableStyle([
             ('FONT', (0,0), (-1,-1), s['ThaiTable'].fontName, 12),
             ('GRID', (0,0), (-1,-1), 0.5, colors.black),
             ('ALIGN', (2,1), (2,-1), 'RIGHT'), # Amount
             ('SPAN', (0,-1), (1,-1)),
             ('ALIGN', (0,-1), (0,-1), 'RIGHT'),
        ]))
        story.append(t)
        story.append(Spacer(1, 1*cm))
        
        # Certification Text
        story.append(Paragraph("ข้าพเจ้าขอรับรองว่ารายจ่ายข้างต้นนี้ไม่อาจเรียกใบเสร็จรับเงินจากผู้รับได้ และข้าพเจ้าได้จ่ายไปในงานของทางราชการโดยแท้", s['ThaiBody']))
        story.append(Spacer(1, 1*cm))
        
        # Signatures
        sig_width = 8.5*cm
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
