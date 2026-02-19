import math

def bahttext(number):
    """
    Converts a number to Thai Baht text format.
    Example: 120.50 -> หนึ่งร้อยยี่สิบบาทห้าสิบสตางค์
    """
    if not isinstance(number, (int, float)):
        return "จำนวนเงินไม่ถูกต้อง"

    if number < 0:
        return "ลบ" + bahttext(-number)

    if number == 0:
        return "ศูนย์บาทถ้วน"

    number_str = "{:.2f}".format(number)
    baht_part, satang_part = number_str.split('.')
    
    baht_text = _convert_to_thai_num(baht_part)
    satang_text = _convert_to_thai_num(satang_part)

    result = ""
    if baht_text:
        result += baht_text + "บาท"
    
    if satang_text and satang_text != "ศูนย์":
        result += satang_text + "สตางค์"
    else:
        result += "ถ้วน"

    return result

def _convert_to_thai_num(number_str):
    """
    Helper to convert a string of digits to Thai text.
    """
    if not number_str or int(number_str) == 0:
        return ""

    thai_nums = ["ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
    unit_names = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]

    length = len(number_str)
    result = ""
    
    # Handle numbers larger than million by recursion
    if length > 7:
        overflow_part = number_str[:-6]
        main_part = number_str[-6:]
        return _convert_to_thai_num(overflow_part) + "ล้าน" + _convert_to_thai_num(main_part)

    for i, digit in enumerate(number_str):
        d = int(digit)
        position = length - i - 1
        
        if d == 0:
            continue
            
        if position == 1 and d == 1:
            # Standard rule: 10 is "sip", not "nueng sip"
            # But 210 is "song roi sip"
            # Exception: if it's the only digit in the tens place (like 10-19)
            # Actually, standard logic:
            # 1 at tens place is never pronounced "neung", just empty string + "sip" output below
            pass 
        elif position == 1 and d == 2:
            result += "ยี่"
        elif position == 0 and d == 1 and length > 1:
            result += "เอ็ด"
        else:
            result += thai_nums[d]
            
        if position == 1 and d == 1:
            result += "สิบ"
        elif position == 1:
            result += "สิบ"
        else:
            result += unit_names[position]

    return result
