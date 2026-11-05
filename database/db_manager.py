import sqlite3
import os
import sys
import logging
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    meipass = getattr(sys, "_MEIPASS", BASE_DIR)
    SCHEMA_PATH = os.path.join(meipass, "database", "schema.sql")
    if not os.path.exists(SCHEMA_PATH):
        SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "catering_stock.db")


class SmartRow:
    """
    صف ذكي فائق التوافق يجمع بين مزايا sqlite3.Row و Python dict:
    - يدعم الفهرسة الرقمية: row[0], row[1] (يمنع أخطاء KeyError: 0)
    - يدعم الفهرسة النصية: row['name'], row['residence_id']
    - يدعم التابع الآمن: row.get('col', default)
    - يدعم التحويل المباشر: dict(row), tuple(row), list(row)
    - يدعم دوال المعاجم: row.keys(), row.values(), row.items()
    """
    __slots__ = ("_cols", "_data")

    def __init__(self, cursor: sqlite3.Cursor, row: tuple):
        self._cols = {col[0]: idx for idx, col in enumerate(cursor.description)}
        self._data = row

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[key]
        idx = self._cols.get(key)
        if idx is not None:
            return self._data[idx]
        key_str = str(key).lower()
        for col_name, c_idx in self._cols.items():
            if col_name.lower() == key_str:
                return self._data[c_idx]
        raise KeyError(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, IndexError, TypeError):
            return default

    def keys(self):
        return list(self._cols.keys())

    def values(self):
        return list(self._data)

    def items(self):
        return [(k, self._data[idx]) for k, idx in self._cols.items()]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        if key in self._cols:
            return True
        key_str = str(key).lower()
        return any(c.lower() == key_str for c in self._cols)

    def __repr__(self):
        return f"<SmartRow {dict(self.items())}>"


def _dict_row_factory(cursor: sqlite3.Cursor, row: tuple):
    return SmartRow(cursor, row)

class ManagedConnection:
    """مغلف لاتصال SQLite يضمن الالتزام بالمعاملات وإغلاق الاتصال تلقائياً فور الانتهاء"""
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def __enter__(self) -> sqlite3.Connection:
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                if self._conn.in_transaction:
                    self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()


    def __getattr__(self, name):
        return getattr(self._conn, name)

class DatabaseManager:
    """إدارة الاتصال وقاعدة البيانات لبرنامج مخزون الإطعام الجامعي"""
    _instance = None

    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_manager(db_path)
        return cls._instance

    def _init_manager(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        need_official_seed = False
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            need_official_seed = True
        else:
            try:
                _test_c = sqlite3.connect(self.db_path)
                _cur = _test_c.execute("SELECT COUNT(*) FROM stock_movements")
                _cnt = _cur.fetchone()[0]
                _test_c.close()
                if _cnt == 0:
                    need_official_seed = True
            except Exception:
                pass

        if need_official_seed:
            official_backup = os.path.join(BASE_DIR, "database", "official_catering_stock.db")
            if os.path.exists(official_backup) and os.path.getsize(official_backup) > 100000:
                import shutil
                try:
                    shutil.copy2(official_backup, self.db_path)
                    logger.info(f"Initialized database from official snapshot: {official_backup}")
                except Exception as ex_init:
                    logger.warning(f"Could not copy official snapshot: {ex_init}")

        # اتصال دائم يبقي ذاكرة WAL المشتركة نشطة ويمنع تفريغ وإعادة بناء الملفات عند كل إغلاق على وسائط التخزين
        self._keep_alive = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        self._keep_alive.execute("PRAGMA journal_mode = WAL;")
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.row_factory = _dict_row_factory   # كل الصفوف تُعاد كـ dict يدعم .get() بأمان
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -64000;")      # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY;")       # In-memory temp tables & sorting
        return ManagedConnection(conn)


    def init_database(self):
        """إنشاء الجداول وترقيتها وتطبيق الفهارس المتقدمة وضبط إعدادات السرعة الفائقة"""
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.row_factory = SmartRow
        try:
            # تفعيل نمط WAL للسرعة ودعم القراءة والكتابة المتزامنة
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA cache_size = -64000;")
            conn.execute("PRAGMA temp_store = MEMORY;")

            # 1. التحقق من وجود الجداول الأساسية
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
            if not cur.fetchone():
                with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)

            # ???? ??? ?????? ?????? ??????? ???????? ????? (RES-04) ?????? ??? ?????? (0 ???? ????? ??? ???? ??????)
            self._migrate_residence_4_data(conn)
            self._fix_future_scrambled_records(conn)

            # ?????? ?? ??? ????? ?????? ????? ???????? ???????? ??? ?? ????? (0 ???? ?????)
            ver_cur = conn.execute("SELECT value FROM settings WHERE key='schema_version'")
            ver_row = ver_cur.fetchone()
            if ver_row and ver_row["value"] == "2026.11.03.2":
                return

            # 2. ترقية الأعمدة الناقصة لجميع الجداول بأمان (Safe Schema Migration)
            self._ensure_table_column(conn, "residences", "name_fr", "TEXT")
            self._ensure_table_column(conn, "entry_vouchers", "residence_id", "INTEGER DEFAULT 1")
            self._ensure_table_column(conn, "exit_vouchers", "residence_id", "INTEGER DEFAULT 1")
            self._ensure_table_column(conn, "stock_movements", "residence_id", "INTEGER DEFAULT 1")
            self._ensure_table_column(conn, "daily_meals_tracking", "residence_id", "INTEGER DEFAULT 1")
            self._ensure_table_column(conn, "daily_meals_tracking", "bf_expense", "REAL DEFAULT 0.0")
            self._ensure_table_column(conn, "daily_meals_tracking", "lu_expense", "REAL DEFAULT 0.0")
            self._ensure_table_column(conn, "daily_meals_tracking", "di_expense", "REAL DEFAULT 0.0")
            self._ensure_table_column(conn, "daily_meals_tracking", "menu_breakfast", "TEXT")
            self._ensure_table_column(conn, "daily_meals_tracking", "menu_lunch", "TEXT")
            self._ensure_table_column(conn, "daily_meals_tracking", "menu_dinner", "TEXT")
            self._ensure_table_column(conn, "supplier_allocations", "residence_id", "INTEGER DEFAULT 1")
            self._ensure_table_column(conn, "supplier_allocations", "lot_name", "TEXT")
            self._ensure_table_column(conn, "inventory_snapshots", "residence_id", "INTEGER DEFAULT 1")

            # 2.1 ترقية القيود الفريدة متعددة الإقامات
            self._migrate_multitenant_unique_constraints(conn)
            # 2.2 ترقية وإنشاء جداول حركة الإعارة والاستعارة بين الإقامات
            self._migrate_residence_loans(conn)
            # 2.3 ترقية وإنشاء جدول الأيام المرخصة استثنائياً من المديرية
            self._migrate_unlocked_days(conn)
            # 2.4 تطبيق التقريب العلوي لمعدل الوجبات (78.5 -> 79, 120.5 -> 121)
            self._migrate_round_up_meals(conn)
            # 2.5 حذف وتطهير أي حركات أو وصولات مسجلة قبل تاريخ 01/09/2026
            self._migrate_clean_pre_0901_records(conn)
            # 2.5.1 تصحيح ومزامنة مصاريف وحسابات الإطعام والتكلفة اليومية لكافة الإقامات
            self._migrate_synchronize_meals_calculations(conn)
            # 2.6 بذر وترحيل بيانات الإقامة الجامعية حساني محمد بن إبراهيم (RES-04)
            self._migrate_residence_4_data(conn)

            # بذر الإعدادات الافتراضية
            default_settings = [
                ("residence_name", "الإقامة الجامعية محمد الطاهر العبيدي بورقلة", "اسم الإقامة الجامعية"),
                ("directorate_name", "مديرية الخدمات الجامعية ورقلة قطب", "اسم المديرية التابعة لها"),
                ("onou_name", "الديوان الوطني للخدمات الجامعية", "اسم الديوان الوطني"),
                ("academic_year", "2026", "السنة المالية / الجامعية الحالية"),
                ("cost_calculation_mode", "FIXED", "طريقة حساب تكلفة المخزون: FIXED (السعر التعاقدي) أو PMP (التكلفة المتوسطة المرجحة)"),
                ("alert_on_negative_stock", "1", "منع الإخراج إذا كان المخزون غير كافٍ (1 نعم، 0 لا)"),
                ("app_theme", "DARK", "مظهر النظام العام (DARK/LIGHT)")
            ]
            for key, val, desc in default_settings:
                conn.execute(
                    "INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)",
                    (key, val, desc)
                )

            # تحديث اسم المديرية تلقائياً إلى التسمية الرسمية الجديدة: ورقلة قطب
            conn.execute("""
                UPDATE settings SET value = 'مديرية الخدمات الجامعية ورقلة قطب'
                WHERE key = 'directorate_name' AND (value LIKE '%بورقلة%' OR value = 'مديرية الخدمات الجامعية ورقلة');
            """)

            # بذر الفئات الأساسية للمواد
            default_categories = [
                ("لحوم ودواجن وأسماك", "اللحوم الحمراء، البيضاء، والأسماك الطازجة والمجمدة"),
                ("خضر وفواكه طازجة", "الخضروات والفواكه الموسمية بجميع أنواعها"),
                ("مواد غذائية عامة وبقالة", "السكر، الزيت، الفرينة، الكسكسي، العجائن والبقوليات"),
                ("حليب ومشتقاته وأجبان", "الحليب، اللبن، الرايب، الياغورت، والأجبان"),
                ("مخبوزات وحلويات", "الخبز، البسكويت، والحلويات"),
                ("توابل ومعلبات ومشروبات", "صلصة الطماطم، التوابل، المشروبات وماء الزهر")
            ]
            for cat_name, cat_desc in default_categories:
                conn.execute(
                    "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
                    (cat_name, cat_desc)
                )

            # بذر المستخدم الإداري الافتراضي في حالة قاعدة بيانات جديدة
            u_cnt = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
            from core.auth_service import AuthService
            admin_hash = AuthService.hash_password("admin123")
            if u_cnt and u_cnt["cnt"] == 0:
                conn.execute(
                    "INSERT INTO users (username, password_hash, full_name, role, is_active) VALUES (?, ?, ?, ?, 1)",
                    ("admin", admin_hash, "مدير الخدمات الجامعية (مسؤول النظام)", "SUPER_ADMIN")
                )
            
            # ضمان وجود هاش كود المديرية في جدول settings ومطابقته للمدير العام
            admin_row = conn.execute("SELECT password_hash FROM users WHERE role = 'SUPER_ADMIN' OR LOWER(username) = 'admin' LIMIT 1").fetchone()
            current_admin_hash = admin_row["password_hash"] if admin_row else admin_hash
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value, description) VALUES ('directorate_code_hash', ?, 'كود التحقق الأمني الموحد لمديرية الخدمات')",
                (current_admin_hash,)
            )

            # بذر الإقامات الرسمية إذا كان الجدول فارغاً
            r_cnt = conn.execute("SELECT COUNT(*) as cnt FROM residences").fetchone()
            if r_cnt and r_cnt["cnt"] == 0:
                default_residences = [
                    (1, "RES-01", "الإقامة الجامعية بن الشيخ التلي", "ورقلة", "مدير الإقامة", 1000),
                    (2, "RES-02", "الإقامة الجامعية بن دحمان بشير", "ورقلة", "مدير الإقامة", 2000),
                    (3, "RES-03", "الإقامة الجامعية بن مالك محمد حسان", "ورقلة", "مدير الإقامة", 1000),
                    (4, "RES-04", "الإقامة الجامعية حساني محمد بن إبراهيم", "ورقلة", "مدير الإقامة", 1000),
                    (5, "RES-05", "الإقامة الجامعية قربشي محمد الناجي", "ورقلة", "مدير الإقامة", 1000),
                    (6, "RES-06", "الإقامة الجامعية لخضاري محمد الأخضر", "ورقلة", "مدير الإقامة", 1000),
                    (7, "RES-07", "الإقامة الجامعية محمد الطاهر العبيدي", "ورقلة", "مدير الإقامة", 1500),
                ]
                for rid, code, name, city, dname, cap in default_residences:
                    conn.execute("""
                        INSERT OR IGNORE INTO residences (id, code, name, city, director_name, capacity, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    """, (rid, code, name, city, dname, cap))

            # 3. إنشاء الفهارس المركبة لتسريع البحث والتقارير الفورية بنسبة 1000%
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mov_res_date_art ON stock_movements(residence_id, date, article_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mov_res_art_type ON stock_movements(residence_id, article_id, movement_type);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mov_date_mvtype ON stock_movements(date, movement_type, article_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ev_res_date_type ON exit_vouchers(residence_id, date, voucher_type);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entry_res_date_type ON entry_vouchers(residence_id, date, voucher_type);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_meals_res_date ON daily_meals_tracking(residence_id, date);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evi_voucher_art ON entry_voucher_items(voucher_id, article_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_xvi_voucher_art ON exit_voucher_items(voucher_id, article_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ra_res_art ON residence_articles(residence_id, article_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_art_active_cat ON articles(is_active, category_id);")

            # 4. إنشاء جداول بونات الطلب (Bons de Commande)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bon_commande (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    residence_id INTEGER NOT NULL,
                    lot_index INTEGER NOT NULL,
                    bon_number TEXT DEFAULT '',
                    period_label TEXT DEFAULT '',
                    period_start TEXT DEFAULT '',
                    period_end TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    updated_at TEXT DEFAULT (datetime('now','localtime')),
                    UNIQUE(residence_id, lot_index)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bon_commande_qty (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bon_id INTEGER NOT NULL REFERENCES bon_commande(id) ON DELETE CASCADE,
                    product_num INTEGER NOT NULL,
                    col_index INTEGER NOT NULL,
                    quantity REAL DEFAULT 0,
                    UNIQUE(bon_id, product_num, col_index)
                )
            """)
            conn.execute("INSERT OR REPLACE INTO settings (key, value, description) VALUES ('schema_version', '2026.11.03.2', 'إصدار بنية قاعدة البيانات');")
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _ensure_table_column(conn: sqlite3.Connection, table_name: str, col_name: str, col_type: str):
        """فحص وإضافة عمود إذا لم يكن موجوداً دون التأثير على البيانات الحالية"""
        try:
            t_cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if t_cur.fetchone():
                cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
                if col_name not in cols:
                    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};")
                    conn.commit()
        except Exception as e:
            logger.debug(f"Migration error on {table_name}.{col_name}: {e}")

    @staticmethod
    def _migrate_multitenant_unique_constraints(conn: sqlite3.Connection):
        """ترقية القيود الفريدة لضمان العزل التام بين الإقامات وتفادي تعارض التواريخ والحصص"""
        try:
            # 1. daily_meals_tracking: التحقق من القيد المركب
            cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='daily_meals_tracking'")
            row = cur.fetchone()
            if row and ("date TEXT NOT NULL UNIQUE" in row["sql"] or ("UNIQUE(date)" in row["sql"] and "residence_id" not in row["sql"].split("UNIQUE")[1])):
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS daily_meals_tracking_v2 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        residence_id INTEGER NOT NULL DEFAULT 1,
                        date TEXT NOT NULL,
                        bf_students INTEGER NOT NULL DEFAULT 0,
                        bf_staff INTEGER NOT NULL DEFAULT 0,
                        bf_professors INTEGER NOT NULL DEFAULT 0,
                        bf_guests INTEGER NOT NULL DEFAULT 0,
                        bf_free INTEGER NOT NULL DEFAULT 0,
                        bf_total INTEGER NOT NULL DEFAULT 0,
                        lu_students INTEGER NOT NULL DEFAULT 0,
                        lu_staff INTEGER NOT NULL DEFAULT 0,
                        lu_professors INTEGER NOT NULL DEFAULT 0,
                        lu_guests INTEGER NOT NULL DEFAULT 0,
                        lu_free INTEGER NOT NULL DEFAULT 0,
                        lu_total INTEGER NOT NULL DEFAULT 0,
                        di_students INTEGER NOT NULL DEFAULT 0,
                        di_staff INTEGER NOT NULL DEFAULT 0,
                        di_professors INTEGER NOT NULL DEFAULT 0,
                        di_guests INTEGER NOT NULL DEFAULT 0,
                        di_free INTEGER NOT NULL DEFAULT 0,
                        di_total INTEGER NOT NULL DEFAULT 0,
                        average_daily_meals REAL NOT NULL DEFAULT 0.0,
                        daily_food_expense REAL NOT NULL DEFAULT 0.0,
                        student_daily_cost REAL NOT NULL DEFAULT 0.0,
                        bf_expense REAL NOT NULL DEFAULT 0.0,
                        lu_expense REAL NOT NULL DEFAULT 0.0,
                        di_expense REAL NOT NULL DEFAULT 0.0,
                        menu_breakfast TEXT DEFAULT '',
                        menu_lunch TEXT DEFAULT '',
                        menu_dinner TEXT DEFAULT '',
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(residence_id, date)
                    );
                """)
                conn.execute("""
                    INSERT OR IGNORE INTO daily_meals_tracking_v2 (
                        id, residence_id, date,
                        bf_students, bf_staff, bf_professors, bf_guests, bf_free, bf_total,
                        lu_students, lu_staff, lu_professors, lu_guests, lu_free, lu_total,
                        di_students, di_staff, di_professors, di_guests, di_free, di_total,
                        average_daily_meals, daily_food_expense, student_daily_cost,
                        bf_expense, lu_expense, di_expense,
                        menu_breakfast, menu_lunch, menu_dinner, notes, created_at
                    )
                    SELECT 
                        id, COALESCE(residence_id, 1), date,
                        bf_students, bf_staff, bf_professors, bf_guests, bf_free, bf_total,
                        lu_students, lu_staff, lu_professors, lu_guests, lu_free, lu_total,
                        di_students, di_staff, di_professors, di_guests, di_free, di_total,
                        average_daily_meals, daily_food_expense, student_daily_cost,
                        COALESCE(bf_expense, 0.0), COALESCE(lu_expense, 0.0), COALESCE(di_expense, 0.0),
                        COALESCE(menu_breakfast, ''), COALESCE(menu_lunch, ''), COALESCE(menu_dinner, ''),
                        notes, created_at
                    FROM daily_meals_tracking;
                """)
                conn.execute("DROP TABLE daily_meals_tracking;")
                conn.execute("ALTER TABLE daily_meals_tracking_v2 RENAME TO daily_meals_tracking;")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_meals_res_date ON daily_meals_tracking(residence_id, date);")
                conn.commit()

            # 2. inventory_snapshots: التحقق من القيد المركب
            cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='inventory_snapshots'")
            row = cur.fetchone()
            if row and "UNIQUE(year, month, article_id)" in row["sql"]:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS inventory_snapshots_v2 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        residence_id INTEGER NOT NULL DEFAULT 1,
                        year INTEGER NOT NULL,
                        month INTEGER NOT NULL,
                        article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                        initial_stock REAL NOT NULL DEFAULT 0.0,
                        total_supply_in REAL NOT NULL DEFAULT 0.0,
                        total_loan_in REAL NOT NULL DEFAULT 0.0,
                        total_consumption_out REAL NOT NULL DEFAULT 0.0,
                        total_loan_out REAL NOT NULL DEFAULT 0.0,
                        theoretical_final_stock REAL NOT NULL DEFAULT 0.0,
                        physical_final_stock REAL NOT NULL DEFAULT 0.0,
                        discrepancy REAL NOT NULL DEFAULT 0.0,
                        unit_price_ttc REAL NOT NULL DEFAULT 0.0,
                        total_value REAL NOT NULL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(residence_id, year, month, article_id)
                    );
                """)
                conn.execute("""
                    INSERT OR IGNORE INTO inventory_snapshots_v2 (
                        id, residence_id, year, month, article_id,
                        initial_stock, total_supply_in, total_loan_in, total_consumption_out, total_loan_out,
                        theoretical_final_stock, physical_final_stock, discrepancy, unit_price_ttc, total_value, created_at
                    )
                    SELECT 
                        id, COALESCE(residence_id, 1), year, month, article_id,
                        initial_stock, total_supply_in, total_loan_in, total_consumption_out, total_loan_out,
                        theoretical_final_stock, physical_final_stock, discrepancy, unit_price_ttc, total_value, created_at
                    FROM inventory_snapshots;
                """)
                conn.execute("DROP TABLE inventory_snapshots;")
                conn.execute("ALTER TABLE inventory_snapshots_v2 RENAME TO inventory_snapshots;")
                conn.commit()

            # 3. supplier_allocations: التحقق من القيد المركب
            cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='supplier_allocations'")
            row = cur.fetchone()
            if row and "UNIQUE(trimester, year, supplier_id, article_id)" in row["sql"]:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS supplier_allocations_v2 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        residence_id INTEGER NOT NULL DEFAULT 1,
                        trimester INTEGER NOT NULL DEFAULT 1,
                        year INTEGER NOT NULL DEFAULT 2026,
                        lot_name TEXT,
                        supplier_id INTEGER REFERENCES suppliers(id) ON DELETE CASCADE,
                        article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                        allocated_qty REAL NOT NULL DEFAULT 0.0,
                        contract_price REAL NOT NULL DEFAULT 0.0,
                        notes TEXT,
                        excel_actual_qty REAL NOT NULL DEFAULT 0.0,
                        UNIQUE(residence_id, trimester, year, supplier_id, article_id)
                    );
                """)
                conn.execute("""
                    INSERT OR IGNORE INTO supplier_allocations_v2 (
                        id, residence_id, trimester, year, lot_name, supplier_id, article_id,
                        allocated_qty, contract_price, notes, excel_actual_qty
                    )
                    SELECT 
                        id, COALESCE(residence_id, 1), trimester, year, lot_name, supplier_id, article_id,
                        allocated_qty, contract_price, notes, COALESCE(excel_actual_qty, 0.0)
                    FROM supplier_allocations;
                """)
                conn.execute("DROP TABLE supplier_allocations;")
                conn.execute("ALTER TABLE supplier_allocations_v2 RENAME TO supplier_allocations;")
                conn.commit()
        except Exception as e:
            logger.error(f"Migration error for multi-tenant unique constraints: {e}")

    def _migrate_residence_loans(self, conn: sqlite3.Connection):
        """إنشاء جداول وفهارس حركة الإعارة والاستعارة بين الإقامات بأمان"""
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS residence_loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_number TEXT UNIQUE NOT NULL,
                    from_residence_id INTEGER NOT NULL REFERENCES residences(id),
                    to_residence_id INTEGER NOT NULL REFERENCES residences(id),
                    date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    entry_voucher_id INTEGER REFERENCES entry_vouchers(id) ON DELETE SET NULL,
                    exit_voucher_id INTEGER REFERENCES exit_vouchers(id) ON DELETE SET NULL,
                    notes TEXT,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    received_at TIMESTAMP
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS residence_loan_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_id INTEGER NOT NULL REFERENCES residence_loans(id) ON DELETE CASCADE,
                    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE RESTRICT,
                    quantity REAL NOT NULL CHECK(quantity > 0),
                    unit_price_ttc REAL NOT NULL DEFAULT 0.0,
                    total_price REAL NOT NULL DEFAULT 0.0
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_residence_loans_from ON residence_loans(from_residence_id, date);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_residence_loans_to ON residence_loans(to_residence_id, date);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_residence_loans_status ON residence_loans(status);")
            conn.commit()
            logger.info("Residence loans tables and indexes verified successfully.")
        except Exception as e:
            logger.error(f"Error migrating residence loans tables: {e}")

    @staticmethod
    def _migrate_unlocked_days(conn: sqlite3.Connection):
        """إنشاء جدول الأيام المرخصة استثنائياً من المديرية للإقامات الجامعية"""
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS unlocked_days (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    residence_id INTEGER NOT NULL REFERENCES residences(id),
                    date TEXT NOT NULL,
                    unlocked_by TEXT DEFAULT 'DIRECTORATE',
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(residence_id, date)
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_unlocked_days_res_date ON unlocked_days(residence_id, date, is_active);")
            conn.commit()
            logger.info("Unlocked days table and index verified successfully.")
        except Exception as e:
            logger.error(f"Error migrating unlocked days table: {e}")

    @staticmethod
    def _migrate_round_up_meals(conn: sqlite3.Connection):
        """تطبيق التقريب العلوي على معدلات الوجبات المسجلة سابقاً (78.5 -> 79, 120.5 -> 121)"""
        try:
            conn.execute("""
                UPDATE daily_meals_tracking
                SET average_daily_meals = ROUND(average_daily_meals + 0.499999)
                WHERE average_daily_meals > 0 
                  AND average_daily_meals != CAST(average_daily_meals AS INTEGER);
            """)
            conn.commit()
            logger.info("Daily meals tracking round-up migration completed successfully.")
        except Exception as e:
            logger.error(f"Error in round-up meals migration: {e}")

    @staticmethod
    def _migrate_clean_pre_0901_records(conn: sqlite3.Connection):
        """
        حذف وتطهير أي حركات أو وصولات أو وجبات مسجلة قبل تاريخ 01/09/2026،
        لتكون بداية التتبع المحاسبي المعتمد رسمياً لكافة الإقامات هي 01/09/2026.
        """
        try:
            conn.execute("DELETE FROM entry_voucher_items WHERE voucher_id IN (SELECT id FROM entry_vouchers WHERE date < '2026-09-01')")
            conn.execute("DELETE FROM entry_vouchers WHERE date < '2026-09-01'")
            conn.execute("DELETE FROM exit_voucher_items WHERE voucher_id IN (SELECT id FROM exit_vouchers WHERE date < '2026-09-01')")
            conn.execute("DELETE FROM exit_vouchers WHERE date < '2026-09-01'")
            conn.execute("DELETE FROM stock_movements WHERE date < '2026-09-01'")
            conn.execute("DELETE FROM daily_meals_tracking WHERE date < '2026-09-01'")
            conn.commit()
            logger.info("Successfully cleaned all vouchers, movements and meals before 2026-09-01.")
        except Exception as e:
            logger.error(f"Error in _migrate_clean_pre_0901_records: {e}")

    @staticmethod
    def _migrate_synchronize_meals_calculations(conn: sqlite3.Connection):
        """
        تصحيح ومزامنة كافة حسابات الإطعام وتكاليف الوجبات ومجموع المصاريف لجميع الإقامات:
        1. تفعيل كافة المواد الغذائية المستخدمة في الإطعام والفطور (مثل حليب غبرة 500غ كود 114).
        2. مطابقة مصاريف الفطور والغداء والعشاء وإجمالي المصاريف مع وصولات خروج المطبخ المعتمدة KITCHEN.
        3. ضمان المعادلة الحسابية الصارمة: م المصاريف = مصاريف الفطور + مصاريف الغداء + مصاريف العشاء.
        4. حساب معدل الوجبات والتكلفة اليومية للطالب بدقة متناهية.
        """
        try:
            # 0. تفعيل كافة المواد الغذائية المستهلكة في الإطعام والفطور أو التي تمتلك رصيد مخزون
            conn.execute("""
                UPDATE articles
                SET is_active = 1
                WHERE id = 114
                   OR current_stock > 0
                   OR EXISTS (SELECT 1 FROM exit_voucher_items WHERE article_id = articles.id)
                   OR EXISTS (SELECT 1 FROM entry_voucher_items WHERE article_id = articles.id)
                   OR EXISTS (SELECT 1 FROM residence_articles WHERE article_id = articles.id AND (current_stock > 0 OR initial_stock > 0));
            """)

            # 1. تحديث مصاريف الوجبات ومجموع المصاريف من وصولات المطبخ KITCHEN الفعلية
            conn.execute("""
                UPDATE daily_meals_tracking
                SET 
                    bf_expense = (
                        SELECT COALESCE(total_breakfast_cost, 0)
                        FROM exit_vouchers 
                        WHERE date = daily_meals_tracking.date 
                          AND residence_id = daily_meals_tracking.residence_id 
                          AND voucher_type = 'KITCHEN'
                    ),
                    lu_expense = (
                        SELECT COALESCE(total_lunch_cost, 0)
                        FROM exit_vouchers 
                        WHERE date = daily_meals_tracking.date 
                          AND residence_id = daily_meals_tracking.residence_id 
                          AND voucher_type = 'KITCHEN'
                    ),
                    di_expense = (
                        SELECT COALESCE(total_dinner_cost, 0)
                        FROM exit_vouchers 
                        WHERE date = daily_meals_tracking.date 
                          AND residence_id = daily_meals_tracking.residence_id 
                          AND voucher_type = 'KITCHEN'
                    ),
                    daily_food_expense = (
                        SELECT COALESCE(total_amount, 0)
                        FROM exit_vouchers 
                        WHERE date = daily_meals_tracking.date 
                          AND residence_id = daily_meals_tracking.residence_id 
                          AND voucher_type = 'KITCHEN'
                    )
                WHERE EXISTS (
                    SELECT 1 FROM exit_vouchers 
                    WHERE date = daily_meals_tracking.date 
                      AND residence_id = daily_meals_tracking.residence_id 
                      AND voucher_type = 'KITCHEN'
                );
            """)

            # 2. للحالات التي لا يوجد فيها وصل خروج مطبخ ولكن مسجل مصاريف للوجبات:
            conn.execute("""
                UPDATE daily_meals_tracking
                SET daily_food_expense = COALESCE(bf_expense, 0) + COALESCE(lu_expense, 0) + COALESCE(di_expense, 0)
                WHERE NOT EXISTS (
                    SELECT 1 FROM exit_vouchers 
                    WHERE date = daily_meals_tracking.date 
                      AND residence_id = daily_meals_tracking.residence_id 
                      AND voucher_type = 'KITCHEN'
                ) AND (COALESCE(bf_expense, 0) + COALESCE(lu_expense, 0) + COALESCE(di_expense, 0)) > 0;
            """)

            # 3. إعادة حساب معدل الوجبات والتكلفة اليومية للطالب بدقة كاملة
            conn.execute("""
                UPDATE daily_meals_tracking
                SET 
                    average_daily_meals = CASE 
                        WHEN di_total = 0 THEN CAST(lu_total AS REAL)
                        ELSE (CAST(lu_total AS REAL) + CAST(di_total AS REAL)) / 2.0
                    END,
                    student_daily_cost = CASE 
                        WHEN di_total > 0 AND (lu_total + di_total) > 0 THEN daily_food_expense / CAST(lu_total + di_total AS REAL)
                        WHEN lu_total > 0 THEN daily_food_expense / CAST(lu_total AS REAL)
                        ELSE 0.0
                    END;
            """)
            conn.commit()
            logger.info("Successfully synchronized all meals calculations for all residences.")
        except Exception as e:
            logger.error(f"Error in _migrate_synchronize_meals_calculations: {e}")

    @staticmethod
    def _migrate_residence_4_data(conn: sqlite3.Connection):
        """ترحيل وبذر كافة بيانات الإقامة الجامعية حساني محمد بن إبراهيم (RES-04) لشهر سبتمبر وأكتوبر 2026"""
        try:
            cur = conn.execute("SELECT value FROM settings WHERE key='residence_4_seeded_v3.5.1'")
            row = cur.fetchone()
            if row and row["value"] == "1":
                return

            seed_func = None
            seed_py = os.path.join(BASE_DIR, "database", "seed_residence_4_data.py")
            if os.path.exists(seed_py):
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("seed_res_4_disk", seed_py)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        if hasattr(mod, "seed_residence_4"):
                            seed_func = mod.seed_residence_4
                            logger.info("Loaded seed_residence_4 dynamically from disk.")
                except Exception as ex_d:
                    logger.warning(f"Failed loading seed from disk: {ex_d}")

            if not seed_func:
                from database.seed_residence_4_data import seed_residence_4
                seed_func = seed_residence_4

            stats = seed_func(conn, force=True)
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('residence_4_seeded_v3.5.1', '1')")
            conn.commit()
            logger.info(f"Residence 4 seeded successfully: {stats}")
        except Exception as e:
            logger.error(f"Error in _migrate_residence_4_data: {e}")


    @staticmethod
    def _fix_future_scrambled_records(conn: sqlite3.Connection):
        """تصحيح السجلات المستقبلية الناتجة عن أخطاء ساعة وتاريخ بعض الحواسيب"""
        try:
            cur = conn.execute("SELECT value FROM settings WHERE key='future_records_fixed_v3.5.2'")
            row = cur.fetchone()
            if row and row["value"] == "1":
                return

            # تصحيح سجلات الإقامة 2 التي سجلت بتاريخ 2026-11-26 بدلاً من 2026-11-02
            conn.execute("""
                UPDATE entry_vouchers 
                SET date = '2026-11-02', 
                    voucher_number = REPLACE(voucher_number, '2026-11-26', '2026-11-02')
                WHERE residence_id = 2 AND date = '2026-11-26'
            """)
            conn.execute("""
                UPDATE exit_vouchers 
                SET date = '2026-11-02', 
                    voucher_number = REPLACE(voucher_number, '2026-11-26', '2026-11-02')
                WHERE residence_id = 2 AND date = '2026-11-26'
            """)
            conn.execute("""
                UPDATE stock_movements 
                SET date = '2026-11-02'
                WHERE residence_id = 2 AND date = '2026-11-26'
            """)
            conn.execute("""
                UPDATE daily_meals_tracking 
                SET date = '2026-11-02'
                WHERE residence_id = 2 AND date = '2026-11-26'
            """)
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('future_records_fixed_v3.5.2', '1')")
            conn.commit()
            logger.info("Fixed future scrambled records for v3.5.2 successfully.")
        except Exception as e:
            logger.error(f"Error in _fix_future_scrambled_records: {e}")

    def get_setting(self, key: str, default: str = "") -> str:

        with self.get_connection() as conn:
            cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value))
            )
            conn.commit()

    def verify_database_integrity(self) -> Tuple[bool, str]:
        """التحقق الأمني من سلامة قاعدة البيانات الفيزيائية وعدم تعرضها للتلاعب"""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                res = conn.execute("PRAGMA integrity_check").fetchone()
                if res and res[0] == "ok":
                    return True, "Database OK"
                return False, f"تلف أو تلاعب في قاعدة البيانات: {res[0] if res else 'Unknown'}"
        except Exception as e:
            return False, f"تعذر فحص قاعدة البيانات: {e}"