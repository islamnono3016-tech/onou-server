import sqlite3
import hashlib
import hmac
import datetime
import time
from typing import Optional, List, Dict, Any
from database.db_manager import DatabaseManager

_AUTH_SALT = "ONOU_DOU_SECURE_AUTH_SALT_2026"
_LOGIN_ATTEMPTS: Dict[str, List[float]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_TIME_SECONDS = 300  # قفل الحساب لمدة 5 دقائق بعد 5 محاولات خاطئة

class AuthService:
    """إدارة المستخدمين، تسجيل الدخول، والتحقق من الصلاحيات مع حماية متقدمة ضد هجمات القوة الغاشمة (Brute Force)"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()

    @staticmethod
    def hash_password(password: str, salt: str = _AUTH_SALT) -> str:
        """تشفير كلمة المرور باستخدام PBKDF2-HMAC-SHA256 مع 100,000 دورة لصد هجمات فك التشفير"""
        return "pbkdf2$" + hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        ).hex()

    @classmethod
    def verify_password(cls, password: str, stored_hash: str) -> bool:
        """مقارنة كلمة المرور بزمن ثابت (Constant-Time) لمنع هجمات التوقيت (Timing Attacks)"""
        if not stored_hash:
            return False
        if stored_hash.startswith("pbkdf2$"):
            expected = cls.hash_password(password)
            return hmac.compare_digest(stored_hash, expected)
        # التوافق التلقائي مع الهاش القديم SHA-256
        legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(stored_hash, legacy_hash)

    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """التحقق من بيانات الدخول مع الحماية من هجمات التخمين والقوة الغاشمة"""
        u_clean = username.strip().lower()
        now = time.time()

        # 1. فحص قفل الحساب (Brute Force Protection)
        attempts = [t for t in _LOGIN_ATTEMPTS.get(u_clean, []) if now - t < LOCKOUT_TIME_SECONDS]
        _LOGIN_ATTEMPTS[u_clean] = attempts

        if len(attempts) >= MAX_FAILED_ATTEMPTS:
            oldest = attempts[0]
            remaining = int(LOCKOUT_TIME_SECONDS - (now - oldest))
            raise PermissionError(
                f"⚠️ تم قفل الحساب مؤقتاً لحمايته من محاولات الاختراق المتكررة.\n"
                f"يرجى الانتظار {remaining} ثانية ثم المحاولة مجدداً."
            )

        with self.db.get_connection() as conn:
            cur = conn.execute("""
                SELECT u.*, r.name as residence_name, r.code as residence_code, r.is_active as res_active
                FROM users u
                LEFT JOIN residences r ON u.residence_id = r.id
                WHERE LOWER(u.username) = ?
            """, (u_clean,))
            row = cur.fetchone()
            cur.close()

            # التحقق من المستخدم وكلمة المرور
            if not row or not self.verify_password(password, row["password_hash"]):
                _LOGIN_ATTEMPTS.setdefault(u_clean, []).append(now)
                return None

            user = dict(row)
            if not user.get("is_active", 1):
                raise PermissionError("حساب المستخدم هذا معطل من قبل مدير النظام")

            # إذا كان المستخدم مرتبطاً بإقامة، نتأكد أنها نشطة
            if user.get("residence_id") and user.get("res_active") == 0:
                raise PermissionError(f"الإقامة ({user.get('residence_name')}) معطلة حالياً من قبل الإدارة المركزية")

            # تصفير المحاولات الفاشلة بعد الدخول الناجح
            _LOGIN_ATTEMPTS.pop(u_clean, None)

            # ترقية الهاش القديم تلقائياً إلى PBKDF2 فائق الأمان
            if not user.get("password_hash", "").startswith("pbkdf2$"):
                new_hash = self.hash_password(password)
                conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user["id"]))
                conn.commit()
                user["password_hash"] = new_hash

            # تحديث تاريخ آخر دخول
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user["id"]))
            conn.commit()

            return user




    def list_users(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.execute("""
                SELECT u.id, u.username, u.full_name, u.role, u.residence_id, u.phone, u.is_active, u.last_login,
                       COALESCE(r.name, 'جميع الإقامات (إشراف كامل)') as residence_name
                FROM users u
                LEFT JOIN residences r ON u.residence_id = r.id
                ORDER BY u.role DESC, u.id ASC
            """)
            return [dict(r) for r in cur.fetchall()]

    def create_user(self, username: str, password: str, full_name: str, role: str = "RESIDENCE_USER", residence_id: Optional[int] = None, phone: str = "") -> int:
        pwd_hash = self.hash_password(password)
        with self.db.get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO users (username, password_hash, full_name, role, residence_id, phone, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (username.strip(), pwd_hash, full_name.strip(), role, residence_id, phone.strip()))
            conn.commit()
            return cur.lastrowid

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cur = conn.execute("""
                SELECT u.*, COALESCE(r.name, 'جميع الإقامات (إشراف كامل)') as residence_name
                FROM users u
                LEFT JOIN residences r ON u.residence_id = r.id
                WHERE u.id = ?
            """, (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def update_user(self, user_id: int, username: str, full_name: str, role: str = "RESIDENCE_USER",
                    residence_id: Optional[int] = None, phone: str = "", is_active: int = 1) -> None:
        u_clean = username.strip()
        fn_clean = full_name.strip()
        if not u_clean:
            raise ValueError("اسم المستخدم لا يمكن أن يكون فارغاً.")
        if not fn_clean:
            raise ValueError("الاسم الكامل للمستخدم لا يمكن أن يكون فارغاً.")

        if user_id == 1:
            if not is_active:
                raise ValueError("لا يمكن تعطيل حساب المسؤول الرئيسي للنظام (admin).")
            if role != "SUPER_ADMIN":
                raise ValueError("لا يمكن تغيير صلاحية المسؤول الرئيسي للنظام عن مدير عام مسؤول (SUPER_ADMIN).")

        with self.db.get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM users WHERE LOWER(username) = LOWER(?) AND id != ?",
                (u_clean, user_id)
            ).fetchone()
            if existing:
                raise ValueError(f"اسم المستخدم '{u_clean}' مستخدم بالفعل لحساب آخر. يرجى اختيار اسم مختلف.")

            conn.execute("""
                UPDATE users SET
                    username = ?, full_name = ?, role = ?, residence_id = ?, phone = ?, is_active = ?
                WHERE id = ?
            """, (u_clean, fn_clean, role, residence_id, phone.strip(), int(is_active), user_id))
            conn.commit()

    def reset_password(self, user_id: int, new_password: str) -> None:
        pwd_hash = self.hash_password(new_password)
        with self.db.get_connection() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user_id))
            conn.commit()

    def delete_user(self, user_id: int) -> None:
        if user_id == 1:
            raise ValueError("لا يمكن حذف حساب المسؤول الرئيسي للنظام (admin)")
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
