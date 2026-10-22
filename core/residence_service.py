import sqlite3
import datetime
from typing import Optional, List, Dict, Any
from database.db_manager import DatabaseManager

def get_french_residence_name(name_ar: str, name_fr: Optional[str] = None, city: str = "ورقلة") -> str:
    """توليد أو استرجاع الاسم الرسمي للإقامة باللغة الفرنسية للمطبوعات والوثائق الرسمية"""
    if name_fr and name_fr.strip():
        return name_fr.strip()

    city_clean = (city or "ورقلة").strip()
    city_fr = "OUARGLA" if "ورقلة" in city_clean or "ورقلة" in (name_ar or "") else city_clean.upper()

    name_ar = name_ar or ""
    if "بن الشيخ" in name_ar or "التلي" in name_ar:
        return f"RESIDENCE UNIVERSITAIRE BEN CHEIKH ETTELI {city_fr}".strip()
    elif "بن دحمان" in name_ar or "بشير" in name_ar or "2000" in name_ar:
        return f"RESIDENCE UNIVERSITAIRE BEN DAHMANE BACHIR {city_fr}".strip()
    elif "بن مالك" in name_ar or "حسان" in name_ar:
        return f"RESIDENCE UNIVERSITAIRE BEN MALEK MOHAMMED HASSEN {city_fr}".strip()
    elif "حساني" in name_ar or "إبراهيم" in name_ar or "إيراهيم" in name_ar:
        return f"RESIDENCE UNIVERSITAIRE HASSANI MOHAMMED BEN BRAHIM {city_fr}".strip()
    elif "قربشي" in name_ar or "الناجي" in name_ar:
        return f"RESIDENCE UNIVERSITAIRE GUERBECHI MOHAMMED ENNADJI {city_fr}".strip()
    elif "لخضاري" in name_ar or "الأخضر" in name_ar:
        return f"RESIDENCE UNIVERSITAIRE LAKHDARI MOHAMMED EL AKHDAR {city_fr}".strip()
    elif "محمد الطاهر" in name_ar or "العبيدي" in name_ar or "الطاشر" in name_ar:
        return f"RESIDENCE UNIVERSITAIRE MOHAMMED TAHAR OUBAIDI {city_fr}".strip()
    elif "1500" in name_ar:
        return f"RESIDENCE UNIVERSITAIRE 1500 LITS {city_fr}".strip()
    elif "1000" in name_ar:
        return f"RESIDENCE UNIVERSITAIRE 1000 LITS {city_fr}".strip()
    elif "500" in name_ar:
        return f"RESIDENCE UNIVERSITAIRE 500 LITS {city_fr}".strip()
    else:
        clean_ar = name_ar.replace("الإقامة الجامعية", "").replace("الاقامة الجامعية", "").replace("إقامة", "").replace("اقامة", "").strip()
        return f"RESIDENCE UNIVERSITAIRE {clean_ar} {city_fr}".strip()

class ResidenceService:
    """إدارة الإقامات الجامعية، الرقابة المركزية، ومقارنة المؤشرات بين الإقامات"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()

    def list_residences(self, only_active: bool = False) -> List[Dict[str, Any]]:
        query = "SELECT * FROM residences WHERE 1=1"
        if only_active:
            query += " AND is_active = 1"
        query += " ORDER BY id ASC"

        with self.db.get_connection() as conn:
            cur = conn.execute(query)
            return [dict(r) for r in cur.fetchall()]

    def get_residence(self, residence_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM residences WHERE id = ?", (residence_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def create_residence(self, data: Dict[str, Any]) -> int:
        """إنشاء إقامة جديدة وبذر دليل المواد الخاص بها برصيد أولي 0"""
        name_ar = data["name"].strip()
        city = data.get("city", "ورقلة").strip()
        name_fr = data.get("name_fr", "").strip()
        if not name_fr:
            name_fr = get_french_residence_name(name_ar, city=city)

        with self.db.get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO residences (code, name, name_fr, city, address, director_name, phone, capacity, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                data["code"].strip(),
                name_ar,
                name_fr,
                city,
                data.get("address", "").strip(),
                data.get("director_name", "").strip(),
                data.get("phone", "").strip(),
                int(data.get("capacity", 1000))
            ))
            new_id = cur.lastrowid

            # تهيئة أرصدة المواد الـ 98 للإقامة الجديدة
            conn.execute("""
                INSERT OR IGNORE INTO residence_articles (residence_id, article_id, initial_stock, current_stock, safety_stock, current_pmp)
                SELECT ?, id, 0.0, 0.0, safety_stock, price_ttc FROM articles;
            """, (new_id,))

            conn.commit()
            return new_id

    def update_residence(self, residence_id: int, data: Dict[str, Any]) -> None:
        name_ar = data["name"].strip()
        city = data.get("city", "ورقلة").strip()
        name_fr = data.get("name_fr", "").strip()
        if not name_fr:
            name_fr = get_french_residence_name(name_ar, city=city)

        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE residences SET
                    code = ?, name = ?, name_fr = ?, city = ?, address = ?, director_name = ?,
                    phone = ?, capacity = ?, is_active = ?
                WHERE id = ?
            """, (
                data["code"].strip(),
                name_ar,
                name_fr,
                city,
                data.get("address", "").strip(),
                data.get("director_name", "").strip(),
                data.get("phone", "").strip(),
                int(data.get("capacity", 1000)),
                int(data.get("is_active", 1)),
                residence_id
            ))
            conn.commit()

    def toggle_residence_status(self, residence_id: int, is_active: int) -> None:
        with self.db.get_connection() as conn:
            conn.execute("UPDATE residences SET is_active = ? WHERE id = ?", (is_active, residence_id))
            conn.commit()

    def delete_residence(self, residence_id: int) -> None:
        if residence_id == 1:
            raise ValueError("لا يمكن حذف الإقامة الرئيسية الافتراضية")

        with self.db.get_connection() as conn:
            # التحقق من وجود حركات مسجلة
            has_moves = conn.execute("SELECT COUNT(*) FROM stock_movements WHERE residence_id = ?", (residence_id,)).fetchone()[0]
            if has_moves > 0:
                raise ValueError("لا يمكن حذف هذه الإقامة لوجود حركات مخزنية ووصولات مسجلة باسمها. يمكنك تعطيلها بدلاً من ذلك.")

            conn.execute("DELETE FROM residence_articles WHERE residence_id = ?", (residence_id,))
            conn.execute("DELETE FROM users WHERE residence_id = ?", (residence_id,))
            conn.execute("DELETE FROM residences WHERE id = ?", (residence_id,))
            conn.commit()

    def get_residences_overview(self) -> List[Dict[str, Any]]:
        """
        لوحة المؤشرات الرقابية للمدير العام:
        تجميع مقارن لجميع الإقامات (قيمة المخزون، مصاريف اليوم، وجبات اليوم، تكلفة الطالب)
        """
        today_str = datetime.date.today().isoformat()
        residences = self.list_residences()
        overview = []

        with self.db.get_connection() as conn:
            for res in residences:
                r_id = res["id"]

                # 1. إجمالي قيمة المخزون الحالي في هذه الإقامة
                stk_cur = conn.execute("""
                    SELECT COALESCE(SUM(ra.current_stock * a.price_ttc), 0)
                    FROM residence_articles ra
                    JOIN articles a ON ra.article_id = a.id
                    WHERE ra.residence_id = ?
                """, (r_id,))
                stock_val = stk_cur.fetchone()[0]
                stk_cur.close()

                # 2. المواد التي اقترب مخزونها من النفاذ
                low_stk_cur = conn.execute("""
                    SELECT COUNT(*)
                    FROM residence_articles
                    WHERE residence_id = ? AND current_stock <= safety_stock AND current_stock > 0
                """, (r_id,))
                low_stk_count = low_stk_cur.fetchone()[0]
                low_stk_cur.close()

                # 3. إحصائيات اليوم الغذائي لهذه الإقامة
                meal_cur = conn.execute("""
                    SELECT daily_food_expense, average_daily_meals, student_daily_cost
                    FROM daily_meals_tracking
                    WHERE residence_id = ? AND date = ?
                """, (r_id, today_str))
                m_row = meal_cur.fetchone()
                meal_cur.close()

                today_exp = m_row["daily_food_expense"] if m_row else 0.0
                today_avg_meals = m_row["average_daily_meals"] if m_row else 0.0
                today_student_cost = m_row["student_daily_cost"] if m_row else 0.0

                # 4. عدد المستخدمين التابعين لهذه الإقامة
                u_cur = conn.execute("SELECT COUNT(*) FROM users WHERE residence_id = ?", (r_id,))
                u_cnt = u_cur.fetchone()[0]
                u_cur.close()


                overview.append({
                    "id": r_id,
                    "code": res["code"],
                    "name": res["name"],
                    "city": res["city"],
                    "director_name": res["director_name"] or "غير محدد",
                    "capacity": res["capacity"],
                    "is_active": res["is_active"],
                    "stock_value": stock_val,
                    "low_stock_count": low_stk_count,
                    "today_expense": today_exp,
                    "today_avg_meals": today_avg_meals,
                    "today_student_cost": today_student_cost,
                    "users_count": u_cnt
                })

        return overview

    def get_deficit_and_transfer_proposals(self) -> List[Dict[str, Any]]:
        """
        اقتراح التحويلات بين المخازن (Inter-Campus Stock Transfer Proposals):
        فحص كل المواد التي وصل مخزونها في أي إقامة إلى حد الأمان أو أقل،
        والبحث عن إقامة أخرى لديها فائض لتقديم اقتراح تحويل فوري بين الإقامات.
        """
        proposals = []
        with self.db.get_connection() as conn:
            deficits = conn.execute("""
                SELECT ra.residence_id, r.name as residence_name, r.city,
                       ra.article_id, a.code as article_code, a.name as article_name, a.unit,
                       ra.current_stock, ra.safety_stock, a.price_ttc
                FROM residence_articles ra
                JOIN residences r ON ra.residence_id = r.id
                JOIN articles a ON ra.article_id = a.id
                WHERE ra.current_stock <= ra.safety_stock AND r.is_active = 1
                ORDER BY (ra.safety_stock - ra.current_stock) DESC
            """).fetchall()

            for def_item in deficits:
                art_id = def_item["article_id"]
                cur_res_id = def_item["residence_id"]
                needed_qty = max(0.0, def_item["safety_stock"] - def_item["current_stock"])

                surplus = conn.execute("""
                    SELECT ra.residence_id, r.name as residence_name, ra.current_stock, ra.safety_stock
                    FROM residence_articles ra
                    JOIN residences r ON ra.residence_id = r.id
                    WHERE ra.article_id = ? AND ra.residence_id != ? AND r.is_active = 1
                          AND ra.current_stock > (ra.safety_stock * 1.2)
                    ORDER BY (ra.current_stock - ra.safety_stock) DESC
                    LIMIT 1
                """, (art_id, cur_res_id)).fetchone()

                donor_name = surplus["residence_name"] if surplus else "لا يوجد فائض متاح"
                donor_id = surplus["residence_id"] if surplus else None
                surplus_qty = max(0.0, (surplus["current_stock"] - surplus["safety_stock"])) if surplus else 0.0
                suggested_transfer = min(needed_qty, surplus_qty) if surplus else 0.0

                proposals.append({
                    "residence_id": cur_res_id,
                    "residence_name": def_item["residence_name"],
                    "article_id": art_id,
                    "article_code": def_item["article_code"],
                    "article_name": def_item["article_name"],
                    "unit": def_item["unit"],
                    "current_stock": def_item["current_stock"],
                    "safety_stock": def_item["safety_stock"],
                    "deficit_qty": needed_qty,
                    "donor_residence_id": donor_id,
                    "donor_residence_name": donor_name,
                    "available_surplus": surplus_qty,
                    "suggested_transfer_qty": suggested_transfer,
                    "status": "مطلوب تحويل عاجل 🔄" if suggested_transfer > 0 else "عجز - يتطلب توريد جديد ⚠️"
                })

        return proposals

