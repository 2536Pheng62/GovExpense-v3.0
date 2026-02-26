from datetime import datetime, timedelta
from typing import Literal, Optional, Dict, Any

class ExpenseCalculator:
    """
    Calculator for Thai Government Travel Expense Reimbursement.
    Ref: Ministry of Finance Regulations.
    """

    # Per Diem Rates (Baht/Day)
    PER_DIEM_RATES = {
        "C1-C8": 240,
        "C9-C11": 270
    }

    # ============================================================
    # Accommodation Rates (Baht/Night)
    # อ้างอิง: พ.ร.ฎ. ค่าใช้จ่ายในการเดินทางไปราชการ พ.ศ. 2526
    #          ระเบียบกระทรวงการคลัง (อัปเดต 2568)
    # ============================================================

    # --- กรณี 1: การเดินทางทั่วไป (General Travel) ---
    ACCOM_GENERAL = {
        "lump_sum": {
            "C1-C8": 800,       # เหมาจ่าย C8 ลงมา
            "C9-C11": 1_200,    # เหมาจ่าย C9 ขึ้นไป
        },
        "actual": {
            "C1-C8":  {"single": 1_500, "double": 850},
            "C9-C11": {"single": 2_200, "double": 1_200},
        },
    }

    # --- กรณี 2: การเดินทางไปฝึกอบรม (Training) ---
    # หมายเหตุ: สถานที่ราชการ (State) เบิกตามจ่ายจริง ไม่เกินเพดาน General
    #           สถานที่เอกชน (Private) ใช้เพดานพิเศษตามอัตราปี 2568
    ACCOM_TRAINING_PRIVATE = {
        "C1-C8":  {"single": 1_600, "double": 1_000},   # Type B
        "C9-C11": {"single": 2_700, "double": 1_500},   # Type A
    }

    # --- อัตราค่าอาหารและอาหารว่าง (ฝึกอบรม) ---
    # อ้างอิง: ระเบียบกระทรวงการคลังว่าด้วยการเบิกจ่ายค่าใช้จ่ายในการบริหารงานของส่วนราชการ
    TRAINING_RATES = {
        "state": {
            "Type A": {"meal": 400, "snack": 35},
            "Type B": {"meal": 200, "snack": 35},
        },
        "private": {
            "Type A": {"meal": 700, "snack": 50},
            "Type B": {"meal": 400, "snack": 50},
        }
    }

    def calculate_per_diem(
        self,
        start_time: datetime,
        end_time: datetime,
        is_overnight: bool,
        c_level: Literal["C1-C8", "C9-C11"],
        provided_meals: int = 0
    ) -> Dict[str, Any]:
        """
        Calculates per diem allowance based on duration and regulations.
        """
        duration = end_time - start_time
        total_seconds = duration.total_seconds()
        days_count = 0.0

        if is_overnight:
            # Rule 2: Overnight
            # 24 hours = 1 day
            # Remainder > 12 hours = +1 day
            days = int(total_seconds // (24 * 3600))
            remainder_seconds = total_seconds % (24 * 3600)
            
            if remainder_seconds > (12 * 3600):
                days += 1
            
            days_count = float(days)
        else:
            # Rule 3: Day Trip (No Overnight)
            # > 12 hours = 1 day
            # > 6 hours but <= 12 hours = 0.5 day
            # <= 6 hours = 0 day
            if total_seconds > (12 * 3600):
                days_count = 1.0
            elif total_seconds > (6 * 3600):
                days_count = 0.5
            else:
                days_count = 0.0

        # Calculate base allowance
        rate = self.PER_DIEM_RATES.get(c_level, 240)
        total_allowance = days_count * rate

        # Rule 4: Meal Deduction
        # Deduct 1/3 of daily rate per provided meal
        # NOTE: Deduction is calculated from the *full daily entitlement* or just a fixed amount?
        # Standard practice: Deduct (Rate / 3) * meals
        deduction = 0.0
        if provided_meals > 0:
            deduction = (rate / 3) * provided_meals
            # Ensure we don't deduct more than the allowance (though logically shouldn't happen if data is correct)
            total_allowance = max(0, total_allowance - deduction)

        return {
            "days_count": days_count,
            "rate_per_day": rate,
            "base_amount": days_count * rate,
            "provided_meals": provided_meals,
            "deduction": deduction,
            "net_amount": total_allowance
        }

    def validate_accommodation(
        self,
        c_level: Literal["C1-C8", "C9-C11"],
        expense_type: Literal["lump_sum", "actual"],
        nights: int,
        actual_cost: float = 0,
        room_type: Literal["single", "double"] = "single",
        is_vehicle_sleep: bool = False,
        manual_rate: float = 0,
        # --- New params (v2) ---
        trip_type: Literal["general", "training"] = "general",
        training_venue: Literal["state", "private"] = "private",
    ) -> Dict[str, Any]:
        """
        คำนวณและตรวจสอบค่าที่พักตามระเบียบราชการ

        กฎเหล็ก:
          - พักแรมบนยานพาหนะ → 0 บาท (ม.17)
        กรณี General:
          - เหมาจ่าย: C1-C8=800, C9+=1200
          - จ่ายจริง: C1-C8 single≤1500/double≤850, C9+ single≤2200/double≤1200
        กรณี Training (สถานที่เอกชน):
          - C1-C8: double≤1000, single≤1600 (ต้องมีเหตุจำเป็น)
          - C9+:   double≤1500, single≤2700
        กรณี Training (สถานที่ราชการ):
          - ใช้เพดานเดียวกับ General Actual
        """
        warnings: list[str] = []

        # ==============================================================
        # กฎเหล็ก: พักแรมบนยานพาหนะ → ห้ามเบิก (ม.17)
        # ==============================================================
        if is_vehicle_sleep:
            return {
                "type": "vehicle_sleep",
                "nights": 0,
                "rate_per_night": 0,
                "allowed_per_night": 0,
                "total_allowed": 0,
                "reimbursable_amount": 0,
                "is_approved": True,
                "room_type": None,
                "trip_type": trip_type,
                "warnings": [],
                "remark": "พักแรมบนยานพาหนะ — ไม่มีสิทธิ์เบิกค่าที่พัก (ระเบียบฯ ม.17)",
            }

        # ==============================================================
        # กรณี 1: การเดินทางทั่วไป (General)
        # ==============================================================
        if trip_type == "general":
            return self._calc_general_accommodation(
                c_level, expense_type, nights, actual_cost, room_type, manual_rate, warnings
            )

        # ==============================================================
        # กรณี 2: การเดินทางไปฝึกอบรม (Training)
        # ==============================================================
        return self._calc_training_accommodation(
            c_level, expense_type, nights, actual_cost, room_type,
            training_venue, manual_rate, warnings
        )

    # ------------------------------------------------------------------
    # Internal: General Travel Accommodation
    # ------------------------------------------------------------------
    def _calc_general_accommodation(
        self, c_level, expense_type, nights, actual_cost, room_type, manual_rate, warnings
    ) -> Dict[str, Any]:

        if expense_type == "lump_sum":
            rate = manual_rate if manual_rate > 0 else self.ACCOM_GENERAL["lump_sum"].get(c_level, 800)
            reimbursable = rate * nights
            return {
                "type": "lump_sum",
                "nights": nights,
                "rate_per_night": rate,
                "allowed_per_night": rate,
                "total_allowed": reimbursable,
                "reimbursable_amount": reimbursable,
                "is_approved": True,
                "room_type": None,
                "trip_type": "general",
                "warnings": warnings,
                "remark": f"เหมาจ่าย {rate:,.0f} บาท/คืน x {nights} คืน",
            }

        # --- Actual ---
        ceiling_map = self.ACCOM_GENERAL["actual"].get(c_level, {"single": 1_500, "double": 850})
        ceiling = ceiling_map.get(room_type, ceiling_map["single"])
        total_ceiling = ceiling * nights
        reimbursable = min(actual_cost, total_ceiling)
        is_approved = actual_cost <= total_ceiling

        warnings.append("ต้องแนบใบเสร็จรับเงิน (Receipt) และ Folio ประกอบการเบิก")
        if not is_approved:
            warnings.append(
                f"ค่าที่พักจริง ({actual_cost:,.2f} บาท) เกินเพดาน "
                f"({total_ceiling:,.2f} บาท) — เบิกได้ไม่เกินเพดาน"
            )

        return {
            "type": "actual",
            "nights": nights,
            "rate_per_night": ceiling,
            "allowed_per_night": ceiling,
            "total_ceiling": total_ceiling,
            "actual_cost": actual_cost,
            "reimbursable_amount": reimbursable,
            "is_approved": is_approved,
            "room_type": room_type,
            "trip_type": "general",
            "warnings": warnings,
            "remark": (
                f"จ่ายจริง {room_type} เพดาน {ceiling:,.0f} บาท/คืน"
                + ("" if is_approved else " (เกินเพดาน)")
            ),
        }

    # ------------------------------------------------------------------
    # Internal: Training Accommodation
    # ------------------------------------------------------------------
    def _calc_training_accommodation(
        self, c_level, expense_type, nights, actual_cost, room_type,
        training_venue, manual_rate, warnings
    ) -> Dict[str, Any]:

        # --- สถานที่ราชการ (State) → ใช้เพดาน General Actual ---
        if training_venue == "state":
            warnings.append("ฝึกอบรม ณ สถานที่ราชการ — ใช้เพดานจ่ายจริงตามอัตรา General")
            if expense_type == "lump_sum":
                # สถานที่ราชการ ยังจ่ายเหมาได้ตามปกติ
                rate = manual_rate if manual_rate > 0 else self.ACCOM_GENERAL["lump_sum"].get(c_level, 800)
                reimbursable = rate * nights
                return {
                    "type": "lump_sum",
                    "nights": nights,
                    "rate_per_night": rate,
                    "allowed_per_night": rate,
                    "total_allowed": reimbursable,
                    "reimbursable_amount": reimbursable,
                    "is_approved": True,
                    "room_type": None,
                    "trip_type": "training",
                    "training_venue": "state",
                    "warnings": warnings,
                    "remark": f"ฝึกอบรม (สถานที่ราชการ) เหมาจ่าย {rate:,.0f} บาท/คืน",
                }
            else:
                # Actual → ใช้เพดาน General
                ceiling_map = self.ACCOM_GENERAL["actual"].get(c_level, {"single": 1_500, "double": 850})
                ceiling = ceiling_map.get(room_type, ceiling_map["single"])
                total_ceiling = ceiling * nights
                reimbursable = min(actual_cost, total_ceiling)
                is_approved = actual_cost <= total_ceiling
                warnings.append("ต้องแนบใบเสร็จรับเงิน (Receipt) และ Folio ประกอบการเบิก")
                if not is_approved:
                    warnings.append(f"เกินเพดาน — เบิกได้ไม่เกิน {total_ceiling:,.2f} บาท")
                return {
                    "type": "actual",
                    "nights": nights,
                    "rate_per_night": ceiling,
                    "allowed_per_night": ceiling,
                    "total_ceiling": total_ceiling,
                    "actual_cost": actual_cost,
                    "reimbursable_amount": reimbursable,
                    "is_approved": is_approved,
                    "room_type": room_type,
                    "trip_type": "training",
                    "training_venue": "state",
                    "warnings": warnings,
                    "remark": f"ฝึกอบรม (สถานที่ราชการ) จ่ายจริง เพดาน {ceiling:,.0f} บาท/คืน",
                }

        # --- สถานที่เอกชน (Private) → เพดานพิเศษ 2568 ---
        ceiling_map = self.ACCOM_TRAINING_PRIVATE.get(c_level, {"single": 1_600, "double": 1_000})
        ceiling = ceiling_map.get(room_type, ceiling_map["double"])

        # กฎพิเศษ: C1-C8 ต้องพักคู่ เว้นแต่มีเหตุจำเป็น
        if c_level == "C1-C8" and room_type == "single":
            warnings.append(
                "ระดับ C1-C8 ฝึกอบรม ณ สถานที่เอกชน — ต้องพักคู่ (Double) เท่านั้น\n"
                "หากจำเป็นต้องพักเดี่ยว ต้องมีหนังสือรับรองเหตุผลความจำเป็นในการไม่พักคู่"
            )

        warnings.append("ต้องแนบใบเสร็จรับเงิน (Receipt) และ Folio ประกอบการเบิก")

        if expense_type == "lump_sum":
            # ฝึกอบรม เอกชน เหมาจ่าย → ใช้เพดาน Training Private เป็น rate
            rate = ceiling
            reimbursable = rate * nights
            return {
                "type": "lump_sum",
                "nights": nights,
                "rate_per_night": rate,
                "allowed_per_night": rate,
                "total_allowed": reimbursable,
                "reimbursable_amount": reimbursable,
                "is_approved": True,
                "room_type": room_type,
                "trip_type": "training",
                "training_venue": "private",
                "warnings": warnings,
                "remark": f"ฝึกอบรม (เอกชน) เหมาจ่าย {rate:,.0f} บาท/คืน ({room_type})",
            }

        # --- Actual ---
        total_ceiling = ceiling * nights
        reimbursable = min(actual_cost, total_ceiling)
        is_approved = actual_cost <= total_ceiling

        if not is_approved:
            warnings.append(
                f"ค่าที่พักจริง ({actual_cost:,.2f} บาท) เกินเพดาน "
                f"({total_ceiling:,.2f} บาท) — เบิกได้ไม่เกินเพดาน"
            )

        return {
            "type": "actual",
            "nights": nights,
            "rate_per_night": ceiling,
            "allowed_per_night": ceiling,
            "total_ceiling": total_ceiling,
            "actual_cost": actual_cost,
            "reimbursable_amount": reimbursable,
            "is_approved": is_approved,
            "room_type": room_type,
            "trip_type": "training",
            "training_venue": "private",
            "warnings": warnings,
            "remark": (
                f"ฝึกอบรม (เอกชน) จ่ายจริง {room_type} เพดาน {ceiling:,.0f} บาท/คืน"
                + ("" if is_approved else " (เกินเพดาน)")
            ),
        }

    def calculate_transportation(
        self,
        vehicle_type: Literal["private_car", "motorcycle"],
        distance_km: float
    ) -> Dict[str, Any]:
        """
        Calculates private vehicle compensation.
        """
        rate = 4 if vehicle_type == "private_car" else 2
        amount = distance_km * rate
        return {
            "type": vehicle_type,
            "distance_km": distance_km,
            "rate": rate,
            "reimbursable_amount": amount
        }

    def validate_taxi(
        self,
        route_type: Literal["intraprivince", "cross_bkk", "cross_other"],
        actual_cost: float
    ) -> Dict[str, Any]:
        """
        Validates public transport/taxi expenses.
        """
        limit = float('inf')
        if route_type == "cross_bkk":
            limit = 600
        elif route_type == "cross_other":
            limit = 500
        
        reimbursable = min(actual_cost, limit)
        return {
            "type": "taxi",
            "route_type": route_type,
            "actual_cost": actual_cost,
            "limit": limit if limit != float('inf') else "Actual",
            "reimbursable_amount": reimbursable
        }

    def calculate_taxi_meter(
        self,
        distance_km: float,
        traffic_minutes: int = 0,
        booking_fee: bool = False,
        airport_surcharge: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates Taxi Meter fare based on DLT 2023 (2566) regulations.
        Ref: https://taxi.ml.ac.th/
        """
        # 1. Base Fare (Start - 1 km)
        fare = 35.0
        remaining_dist = check_dist = distance_km - 1
        
        if remaining_dist <= 0:
            fare = 35.0
        else:
            # 1-10 km @ 6.5
            dist_step = min(remaining_dist, 9) # 10-1 = 9
            fare += dist_step * 6.5
            remaining_dist -= dist_step
            
            if remaining_dist > 0:
                # 10-20 km @ 7.0
                dist_step = min(remaining_dist, 10)
                fare += dist_step * 7.0
                remaining_dist -= dist_step
                
                if remaining_dist > 0:
                    # 20-40 km @ 8.0
                    dist_step = min(remaining_dist, 20)
                    fare += dist_step * 8.0
                    remaining_dist -= dist_step
                    
                    if remaining_dist > 0:
                        # 40-60 km @ 8.5
                        dist_step = min(remaining_dist, 20)
                        fare += dist_step * 8.5
                        remaining_dist -= dist_step
                        
                        if remaining_dist > 0:
                            # 60-80 km @ 9.0
                            dist_step = min(remaining_dist, 20)
                            fare += dist_step * 9.0
                            remaining_dist -= dist_step
                            
                            if remaining_dist > 0:
                                # > 80 km @ 10.5
                                fare += remaining_dist * 10.5

        # 2. Traffic Surcharge (Speed < 6 km/h)
        fare += traffic_minutes * 3.0
        
        # 3. Extra Surcharges
        surcharges = 0
        if booking_fee:
            surcharges += 20
        if airport_surcharge:
            surcharges += 50
            
        total_fare = fare + surcharges
        
        # Taxi meters usually round to odd integer, but for calculation we keep float then maybe ceil/round
        # DLT rule says round to nearest odd integer usually? Or just use exact calculation for estimation.
        # Let's return exact float for now.
        
        return {
            "distance_km": distance_km,
            "fare_distance": fare_distance,
            "fare_traffic": traffic_minutes * 3.0,
            "surcharges": surcharges,
            "total_fare": total_fare
        }

    def calculate_training_meal_allowance(
        self,
        c_level: Literal["C1-C8", "C9-C11"],
        venue: Literal["state", "private"],
        meal_count: int = 0,
        snack_count: int = 0
    ) -> Dict[str, Any]:
        """
        คำนวณวงเงินค่าอาหารและอาหารว่างสำหรับการฝึกอบรม
        """
        training_type = "Type A" if c_level == "C9-C11" else "Type B"
        rates = self.TRAINING_RATES[venue][training_type]
        
        meal_total = meal_count * rates["meal"]
        snack_total = snack_count * rates["snack"]
        grand_total = meal_total + snack_total
        
        return {
            "training_type": training_type,
            "venue": venue,
            "meal_rate": rates["meal"],
            "snack_rate": rates["snack"],
            "meal_count": meal_count,
            "snack_count": snack_count,
            "meal_total": meal_total,
            "snack_total": snack_total,
            "grand_total": grand_total
        }
