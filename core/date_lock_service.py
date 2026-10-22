import datetime
import logging
from typing import Optional, List, Dict, Any, Tuple
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DateLockedError(Exception):
    """خطأ محاولة إدخال أو تعديل البيانات على يوم مغلق تجاوز الـ 3 أيام دون ترخيص من المديرية"""
    def __init__(self, target_date: str, message: str = ""):
        self.target_date = target_date
        msg = message or f"عذراً، يوم ({target_date}) مغلق للتعديل. يسمح فقط بتعديل آخر 3 أيام. يرجى طلب ترخيص من المديرية لفتح هذا اليوم."
        super().__init__(msg)

class DateLockService:
    """
    خدمة الرقابة الزمنية وإقفال الأيام (Date Lock & Directorate Override Service)
    
    القواعد المحاسبية والرقابية:
    1. الإقامات الجامعية: يسمح لها بتعديل وإدخال المعلومات لآخر 3 أيام فقط (اليوم، الأمس، وقبل الأمس).
    2. الأيام الأقدم من 3 أيام تقفل تلقائياً وتصبح للقراءة والطباعة فقط لمنع التلاعب في الحسابات الماضية.
    3. المديرية المركزية (Directorate / Super Admin):
       - تمتلك صلاحية كاملة لتعديل أي يوم بدون قيود.
       - تمتلك الصلاحية الحصرية لـ "فتح وترخيص" أي يوم مغلق لأي إقامة معينة، مع تسجيل سبب الفتح وتاريخه.
    """

    ALLOWED_WINDOW_DAYS = 3  # آخر 3 أيام تقويمية (اليوم الحالي + يومين سابقين)

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()

    def check_date_permission(
        self,
        residence_id: int,
        target_date: str,
        is_directorate: bool = False
    ) -> Dict[str, Any]:
        """
        التحقق الشامل من صلاحية إدخال وتعديل البيانات ليوم محدد.
        
        المخرجات:
        - is_editable: bool (هل يمكن التعديل والحفظ؟)
        - reason_code: str (رمز الحالة)
        - message: str (نص رسالة التوضيح والتنبيه للمستخدم)
        - unlocked_info: dict / None (معلومات الترخيص إذا كان مفتوحاً من المديرية)
        """
        # 1. إذا كان المستخدم من الإدارة المركزية / المديرية -> متاح دائماً
        if is_directorate:
            return {
                "is_editable": True,
                "reason_code": "DIRECTORATE_FULL_ACCESS",
                "message": "صلاحية المديرية المركزية (إشراف ورقابة كاملة على كافة التواريخ)",
                "unlocked_info": None
            }

        try:
            t_date = datetime.date.fromisoformat(target_date)
        except Exception:
            return {
                "is_editable": False,
                "reason_code": "INVALID_DATE",
                "message": f"صيغة التاريخ غير صالحة ({target_date}).",
                "unlocked_info": None
            }

        today = datetime.date.today()
        diff_days = (today - t_date).days

        # 2. فحص الأيام المستقبلية
        if diff_days < 0:
            # التحقق هل منحته المديرية ترخيصاً مسبقاً
            unlocked = self.get_unlocked_entry(residence_id, target_date)
            if unlocked:
                return {
                    "is_editable": True,
                    "reason_code": "UNLOCKED_BY_DIRECTORATE",
                    "message": f"يوم مستقبلي مفتوح بترخيص استثنائي من المديرية ({unlocked.get('notes') or ''})",
                    "unlocked_info": unlocked
                }
            return {
                "is_editable": False,
                "reason_code": "LOCKED_FUTURE",
                "message": "لا يمكن تسجيل أو تعديل استهلاك يوم مستقبلي قبل حلول موعده.",
                "unlocked_info": None
            }

        # 3. فحص نافذة آخر 3 أيام النظامية (اليوم: 0، الأمس: 1، قبل الأمس: 2)
        if diff_days < self.ALLOWED_WINDOW_DAYS:
            return {
                "is_editable": True,
                "reason_code": "RECENT_WINDOW",
                "message": f"متاح للتعديل (ضمن المهلة النظامية لآخر 3 أيام - مضى {diff_days} يوم)",
                "unlocked_info": None
            }

        # 4. الأيام التي تجاوزت 3 أيام -> فحص هل توجد رخصة استثنائية من المديرية لهذه الإقامة
        unlocked = self.get_unlocked_entry(residence_id, target_date)
        if unlocked:
            notes = unlocked.get("notes") or "مصرح بالتعديل والمراجعة"
            by = unlocked.get("unlocked_by") or "المديرية"
            return {
                "is_editable": True,
                "reason_code": "UNLOCKED_BY_DIRECTORATE",
                "message": f"هذا اليوم مفتوح استثنائياً بترخيص من {by} | السبب: {notes}",
                "unlocked_info": unlocked
            }

        # 5. اليوم مغلق
        return {
            "is_editable": False,
            "reason_code": "LOCKED_TOO_OLD",
            "message": f"ورقة هذا اليوم مغلقة (مر عليها {diff_days} يوماً). التعديل مقيد بآخر 3 أيام فقط. يرجى طلب ترخيص من المديرية لفتح هذا اليوم.",
            "unlocked_info": None
        }

    def is_date_editable(self, residence_id: int, target_date: str, is_directorate: bool = False) -> Tuple[bool, str]:
        """دالة مختصرة وسريعة للتحقق تعيد (is_editable, message)"""
        res = self.check_date_permission(residence_id, target_date, is_directorate)
        return res["is_editable"], res["message"]

    def unlock_date(
        self,
        residence_id: int,
        date_str: str,
        unlocked_by: str = "المديرية المركزية",
        notes: str = ""
    ) -> bool:
        """
        منح ترخيص وفتح يوم مغلق لإقامة معينة لإدخال وتصحيح المعلومات
        (صلاحية حصرية للمديرية)
        """
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO unlocked_days (residence_id, date, unlocked_by, notes, is_active, unlocked_at)
                VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(residence_id, date) DO UPDATE SET
                    is_active = 1,
                    unlocked_by = excluded.unlocked_by,
                    notes = excluded.notes,
                    unlocked_at = CURRENT_TIMESTAMP
            """, (residence_id, date_str, unlocked_by, notes))
            conn.commit()
            logger.info(f"Date {date_str} successfully UNLOCKED for residence_id={residence_id} by {unlocked_by}")
            return True

    def unlock_date_range(
        self,
        residence_id: int,
        start_date_str: str,
        end_date_str: str,
        unlocked_by: str = "المديرية المركزية",
        notes: str = ""
    ) -> List[str]:
        """
        منح ترخيص وفتح فترة زمنية (من تاريخ إلى تاريخ) دفعة واحدة لإقامة معينة
        يعيد قائمة التواريخ التي تم فتحها بنجاح
        """
        try:
            d_start = datetime.date.fromisoformat(start_date_str)
            d_end = datetime.date.fromisoformat(end_date_str)
        except Exception as e:
            logger.error(f"Invalid date format in unlock_date_range: {e}")
            return []

        if d_start > d_end:
            d_start, d_end = d_end, d_start

        unlocked_dates = []
        curr = d_start
        with self.db.get_connection() as conn:
            while curr <= d_end:
                d_str = curr.isoformat()
                conn.execute("""
                    INSERT INTO unlocked_days (residence_id, date, unlocked_by, notes, is_active, unlocked_at)
                    VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(residence_id, date) DO UPDATE SET
                        is_active = 1,
                        unlocked_by = excluded.unlocked_by,
                        notes = excluded.notes,
                        unlocked_at = CURRENT_TIMESTAMP
                """, (residence_id, d_str, unlocked_by, notes))
                unlocked_dates.append(d_str)
                curr += datetime.timedelta(days=1)
            conn.commit()

        logger.info(f"Date range [{start_date_str} to {end_date_str}] ({len(unlocked_dates)} days) UNLOCKED for residence_id={residence_id}")
        return unlocked_dates

    def lock_date(self, residence_id: int, date_str: str) -> bool:
        """
        إعادة قفل يوم تم فتحه سابقاً (إلغاء الترخيص الاستثنائي)
        """
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE unlocked_days
                SET is_active = 0
                WHERE residence_id = ? AND date = ?
            """, (residence_id, date_str))
            conn.commit()
            logger.info(f"Date {date_str} successfully LOCKED back for residence_id={residence_id}")
            return True

    def lock_dates(self, entries: List[Tuple[int, str]]) -> int:
        """
        إلغاء تراخيص قائمة من الأيام دفعة واحدة [(residence_id, date_str), ...]
        يعيد عدد الأيام التي تم قفلها
        """
        if not entries:
            return 0
        count = 0
        with self.db.get_connection() as conn:
            for res_id, d_str in entries:
                conn.execute("""
                    UPDATE unlocked_days
                    SET is_active = 0
                    WHERE residence_id = ? AND date = ?
                """, (res_id, d_str))
                count += 1
            conn.commit()
        logger.info(f"Successfully LOCKED back {count} days in batch")
        return count

    def get_unlocked_entry(self, residence_id: int, date_str: str) -> Optional[Dict[str, Any]]:
        """جلب تفاصيل ترخيص الفتح ليوم محدد إذا كان نشطاً"""
        with self.db.get_connection() as conn:
            cur = conn.execute("""
                SELECT u.*, r.name as residence_name, r.code as residence_code
                FROM unlocked_days u
                JOIN residences r ON u.residence_id = r.id
                WHERE u.residence_id = ? AND u.date = ? AND u.is_active = 1
            """, (residence_id, date_str))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_unlocked_days(self, residence_id: Optional[int] = None, only_active: bool = True) -> List[Dict[str, Any]]:
        """
        جلب قائمة كافة الأيام المرخصة المفتوحة استثنائياً للمديرية
        """
        with self.db.get_connection() as conn:
            sql = """
                SELECT u.*, r.name as residence_name, r.code as residence_code
                FROM unlocked_days u
                JOIN residences r ON u.residence_id = r.id
                WHERE 1=1
            """
            params = []
            if residence_id:
                sql += " AND u.residence_id = ?"
                params.append(residence_id)
            if only_active:
                sql += " AND u.is_active = 1"

            sql += " ORDER BY u.unlocked_at DESC, u.date DESC"
            cur = conn.execute(sql, tuple(params))
            return [dict(r) for r in cur.fetchall()]
