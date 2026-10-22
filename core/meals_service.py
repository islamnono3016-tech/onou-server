import sqlite3
import datetime
from typing import List, Dict, Any, Optional
from database.db_manager import DatabaseManager

class MealsService:
    """محرك متابعة إحصائيات الوجبات وتعداد التذاكر وتكلفة وجبة الطالب"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None, residence_id: int = 1):
        self.db = db_manager or DatabaseManager()
        self.residence_id = residence_id

    def set_residence(self, residence_id: int):
        self.residence_id = residence_id

    def get_daily_record(self, date_str: str, residence_id: Optional[int] = None) -> Dict[str, Any]:
        """جلب أو إنشاء سجل الوجبات ليوم محدد مع جلب مصاريف الاستهلاك المحسوبة"""
        r_id = residence_id or self.residence_id
        with self.db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM daily_meals_tracking WHERE date = ? AND residence_id = ?", (date_str, r_id))
            row = cur.fetchone()
            if row:
                return dict(row)
            
            # حساب مصاريف اليوم من وصولات الإخراج إن وجدت
            exp_cur = conn.execute("""
                SELECT COALESCE(SUM(total_amount), 0) FROM exit_vouchers 
                WHERE date = ? AND voucher_type = 'KITCHEN' AND residence_id = ?
            """, (date_str, r_id))
            exp_val = exp_cur.fetchone()[0]

            return {
                "date": date_str,
                "bf_students": 0, "bf_staff": 0, "bf_professors": 0, "bf_guests": 0, "bf_free": 0, "bf_total": 0,
                "lu_students": 0, "lu_staff": 0, "lu_professors": 0, "lu_guests": 0, "lu_free": 0, "lu_total": 0,
                "di_students": 0, "di_staff": 0, "di_professors": 0, "di_guests": 0, "di_free": 0, "di_total": 0,
                "average_daily_meals": 0.0,
                "daily_food_expense": exp_val,
                "student_daily_cost": 0.0,
                "notes": ""
            }

    def save_daily_record(self, data: Dict[str, Any]) -> None:
        """
        حفظ أعداد التذاكر وحساب المعدل وتكلفة إطعام الطالب وفق معايير الخدمات الجامعية
        """
        date_str = data["date"]

        # 1. حساب مجاميع الوجبات
        bf_stud = int(data.get("bf_students", 0))
        bf_staf = int(data.get("bf_staff", 0))
        bf_prof = int(data.get("bf_professors", 0))
        bf_gues = int(data.get("bf_guests", 0))
        bf_free = int(data.get("bf_free", 0))
        bf_total = bf_stud + bf_staf + bf_prof + bf_gues + bf_free

        lu_stud = int(data.get("lu_students", 0))
        lu_staf = int(data.get("lu_staff", 0))
        lu_prof = int(data.get("lu_professors", 0))
        lu_gues = int(data.get("lu_guests", 0))
        lu_free = int(data.get("lu_free", 0))
        lu_total = lu_stud + lu_staf + lu_prof + lu_gues + lu_free

        di_stud = int(data.get("di_students", 0))
        di_staf = int(data.get("di_staff", 0))
        di_prof = int(data.get("di_professors", 0))
        di_gues = int(data.get("di_guests", 0))
        di_free = int(data.get("di_free", 0))
        di_total = di_stud + di_staf + di_prof + di_gues + di_free

        # 2. حساب معدل الوجبات: =IF(العشاء=0, الغداء, (الغداء + العشاء)/2)
        if di_total == 0:
            avg_meals = float(lu_total)
        else:
            avg_meals = (lu_total + di_total) / 2.0

        # 3. جلب أو تحديث المصاريف اليومية
        daily_expense = float(data.get("daily_food_expense", 0.0))
        r_id = data.get("residence_id") or self.residence_id
        if daily_expense == 0.0:
            with self.db.get_connection() as conn:
                exp_cur = conn.execute("""
                    SELECT COALESCE(SUM(total_amount), 0) FROM exit_vouchers 
                    WHERE date = ? AND voucher_type = 'KITCHEN' AND residence_id = ?
                """, (date_str, r_id))
                daily_expense = float(exp_cur.fetchone()[0])

        # 4. حساب تكلفة وجبة الطالب اليومية: =IF(المعدل=0, 0, (المصاريف / المعدل) / 2)
        student_cost = 0.0
        if avg_meals > 0:
            student_cost = (daily_expense / avg_meals) / 2.0

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO daily_meals_tracking (
                    date, residence_id,
                    bf_students, bf_staff, bf_professors, bf_guests, bf_free, bf_total,
                    lu_students, lu_staff, lu_professors, lu_guests, lu_free, lu_total,
                    di_students, di_staff, di_professors, di_guests, di_free, di_total,
                    average_daily_meals, daily_food_expense, student_daily_cost, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(residence_id, date) DO UPDATE SET
                    bf_students = excluded.bf_students,
                    bf_staff = excluded.bf_staff,
                    bf_professors = excluded.bf_professors,
                    bf_guests = excluded.bf_guests,
                    bf_free = excluded.bf_free,
                    bf_total = excluded.bf_total,
                    lu_students = excluded.lu_students,
                    lu_staff = excluded.lu_staff,
                    lu_professors = excluded.lu_professors,
                    lu_guests = excluded.lu_guests,
                    lu_free = excluded.lu_free,
                    lu_total = excluded.lu_total,
                    di_students = excluded.di_students,
                    di_staff = excluded.di_staff,
                    di_professors = excluded.di_professors,
                    di_guests = excluded.di_guests,
                    di_free = excluded.di_free,
                    di_total = excluded.di_total,
                    average_daily_meals = excluded.average_daily_meals,
                    daily_food_expense = excluded.daily_food_expense,
                    student_daily_cost = excluded.student_daily_cost,
                    notes = excluded.notes,
                    residence_id = excluded.residence_id
            """, (
                date_str, r_id,
                bf_stud, bf_staf, bf_prof, bf_gues, bf_free, bf_total,
                lu_stud, lu_staf, lu_prof, lu_gues, lu_free, lu_total,
                di_stud, di_staf, di_prof, di_gues, di_free, di_total,
                avg_meals, daily_expense, student_cost, data.get("notes", "")
            ))
            conn.commit()

    def get_monthly_activity_report(self, year: Optional[int] = None, month: Optional[int] = None, residence_id: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        توليد تقرير النشاط بالأرقام (مكافئ ورقة النشاط بالأرقام)
        يدعم العرض الشهري الافتراضي أو فترة مخصصة من تاريخ إلى تاريخ
        """
        r_id = residence_id or self.residence_id
        
        if start_date and end_date:
            d_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            d_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            rep_year = year or d_start.year
            rep_month = month or d_start.month
        else:
            rep_year = year or datetime.date.today().year
            rep_month = month or datetime.date.today().month
            if rep_month in [1, 3, 5, 7, 8, 10, 12]: last_day = 31
            elif rep_month in [4, 6, 9, 11]: last_day = 30
            else: last_day = 29 if (rep_year % 4 == 0 and (rep_year % 100 != 0 or rep_year % 400 == 0)) else 28
            d_start = datetime.date(rep_year, rep_month, 1)
            d_end = datetime.date(rep_year, rep_month, last_day)

        days_list = []
        tot_bf_count = 0
        tot_lu_count = 0
        tot_di_count = 0
        tot_expense = 0.0

        with self.db.get_connection() as conn:
            cur_d = d_start
            while cur_d <= d_end:
                d_str = cur_d.isoformat()
                d_day = cur_d.day
                row = conn.execute("SELECT * FROM daily_meals_tracking WHERE date = ? AND residence_id = ?", (d_str, r_id)).fetchone()
                
                # جلب مصاريف كل وجبة على حدة من وصولات الإخراج لهذا اليوم
                v_row = conn.execute("""
                    SELECT 
                        COALESCE(SUM(total_breakfast_cost), 0) as bf_exp,
                        COALESCE(SUM(total_lunch_cost), 0) as lu_exp,
                        COALESCE(SUM(total_dinner_cost), 0) as di_exp,
                        COALESCE(SUM(total_amount), 0) as tot_exp
                    FROM exit_vouchers 
                    WHERE date = ? AND voucher_type = 'KITCHEN' AND residence_id = ?
                """, (d_str, r_id)).fetchone()

                bf_c = row["bf_total"] if row else 0
                lu_c = row["lu_total"] if row else 0
                di_c = row["di_total"] if row else 0
                avg_m = row["average_daily_meals"] if row else (lu_c if di_c == 0 else (lu_c + di_c)/2.0)
                d_exp = row["daily_food_expense"] if (row and row["daily_food_expense"] > 0) else v_row["tot_exp"]
                s_cost = row["student_daily_cost"] if row else (0.0 if avg_m == 0 else (d_exp / avg_m) / 2.0)

                tot_bf_count += bf_c
                tot_lu_count += lu_c
                tot_di_count += di_c
                tot_expense += d_exp

                days_list.append({
                    "day": d_day,
                    "date": d_str,
                    "bf_count": bf_c,
                    "bf_expense": v_row["bf_exp"],
                    "lu_count": lu_c,
                    "lu_expense": v_row["lu_exp"],
                    "di_count": di_c,
                    "di_expense": v_row["di_exp"],
                    "average_meals": avg_m,
                    "total_expense": d_exp,
                    "student_cost": s_cost
                })
                cur_d += datetime.timedelta(days=1)

        avg_student_cost = (tot_expense / ((tot_lu_count + tot_di_count) / 2.0) / 2.0) if (tot_lu_count + tot_di_count) > 0 else 0.0

        return {
            "year": rep_year,
            "month": rep_month,
            "start_date": d_start.isoformat(),
            "end_date": d_end.isoformat(),
            "days": days_list,
            "totals": {
                "total_breakfast": tot_bf_count,
                "total_lunch": tot_lu_count,
                "total_dinner": tot_di_count,
                "total_meals": tot_bf_count + tot_lu_count + tot_di_count,
                "total_expense": tot_expense,
                "average_student_cost": avg_student_cost
            }
        }

    def get_monthly_menus_report(self, year: Optional[int] = None, month: Optional[int] = None, residence_id: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """جلب قوائم الوجبات (فطور، غداء، عشاء) لكل يوم (مكافئ ورقة النشاط بالوجبة) - يدعم الفترة المخصصة"""
        r_id = residence_id or self.residence_id
        
        if start_date and end_date:
            d_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            d_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            rep_year = year or datetime.date.today().year
            rep_month = month or datetime.date.today().month
            if rep_month in [1, 3, 5, 7, 8, 10, 12]: last_day = 31
            elif rep_month in [4, 6, 9, 11]: last_day = 30
            else: last_day = 29 if (rep_year % 4 == 0 and (rep_year % 100 != 0 or rep_year % 400 == 0)) else 28
            d_start = datetime.date(rep_year, rep_month, 1)
            d_end = datetime.date(rep_year, rep_month, last_day)

        res = []
        with self.db.get_connection() as conn:
            cur_d = d_start
            while cur_d <= d_end:
                d_str = cur_d.isoformat()
                d_day = cur_d.day
                row = conn.execute("SELECT menu_breakfast, menu_lunch, menu_dinner FROM daily_meals_tracking WHERE date = ? AND residence_id = ?", (d_str, r_id)).fetchone()
                res.append({
                    "day": d_day,
                    "date": d_str,
                    "menu_breakfast": row["menu_breakfast"] if (row and row["menu_breakfast"]) else "",
                    "menu_lunch": row["menu_lunch"] if (row and row["menu_lunch"]) else "",
                    "menu_dinner": row["menu_dinner"] if (row and row["menu_dinner"]) else ""
                })
                cur_d += datetime.timedelta(days=1)
        return res
