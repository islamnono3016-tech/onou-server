-- =========================================================================
-- نظام تسيير مخزون الإطعام في الإقامات الجامعية
-- University Residence Catering Stock Management Database Schema
-- =========================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- 1. جدول الإعدادات العامة للمؤسسة (General Settings)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

-- 2. جدول فئات المواد (Article Categories)
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- 3. جدول الموردين (Suppliers)
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    phone TEXT,
    address TEXT,
    tax_number TEXT,     -- رقم السجل التجاري / النيف
    lot_number TEXT,     -- رقم الحصة المسندة في دفتر الشروط
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. جدول المواد الغذائية (Articles / Catalog)
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,                               -- رقم الحصة أو الرمز
    name TEXT NOT NULL UNIQUE,               -- اسم المادة
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    unit TEXT NOT NULL DEFAULT 'كلغ',        -- وحدة القياس (كلغ، علبة، لتر...)
    price_ht REAL NOT NULL DEFAULT 0.0,      -- السعر بدون رسوم
    discount_rate REAL NOT NULL DEFAULT 0.0, -- نسبة التخفيض (مثلاً 0.05 لـ 5%)
    discount_amount REAL NOT NULL DEFAULT 0.0,-- قيمة التخفيض
    price_after_discount REAL NOT NULL DEFAULT 0.0, -- السعر بعد التخفيض
    tva_rate REAL NOT NULL DEFAULT 0.0,      -- نسبة الرسم على القيمة المضافة (0، 9، 19)
    price_ttc REAL NOT NULL DEFAULT 0.0,     -- السعر بكامل الرسوم (السعر التعاقدي)
    current_pmp REAL NOT NULL DEFAULT 0.0,   -- التكلفة المتوسطة المرجحة (CMP/PMP)
    safety_stock REAL NOT NULL DEFAULT 0.0,  -- مخزون الأمان (الحد الأدنى للتنبيه)
    initial_stock REAL NOT NULL DEFAULT 0.0, -- الرصيد الافتتاحي السنوي (جانفي)
    current_stock REAL NOT NULL DEFAULT 0.0, -- الرصيد الحي المتوفر حالياً
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. جدول حصص المديرية والموردين (Allocations - الوضعيات الرقابية)
CREATE TABLE IF NOT EXISTS supplier_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    residence_id INTEGER REFERENCES residences(id) DEFAULT 1,
    trimester INTEGER NOT NULL,              -- 1, 2, 3 (الثلاثي)
    year INTEGER NOT NULL DEFAULT 2026,
    lot_name TEXT,                           -- اسم الحصة (مثلاً حصة الخضر والفواكه)
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    allocated_qty REAL NOT NULL DEFAULT 0.0, -- الكمية الممنوحة من المديرية
    contract_price REAL NOT NULL DEFAULT 0.0,-- السعر التعاقدي المعتمد
    notes TEXT,
    UNIQUE(residence_id, trimester, year, supplier_id, article_id)
);

-- 6. جدول وصولات الدخول / الاستلام (Entry Vouchers - Bons d'Entrée)
CREATE TABLE IF NOT EXISTS entry_vouchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    residence_id INTEGER REFERENCES residences(id) DEFAULT 1,
    voucher_number TEXT NOT NULL,            -- رقم وصل الاستلام
    date TEXT NOT NULL,                      -- تاريخ الاستلام YYYY-MM-DD
    voucher_type TEXT NOT NULL DEFAULT 'SUPPLIER', -- 'SUPPLIER' توريد, 'LOAN_IN' إستعارة
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    source_residence TEXT,                   -- الإقامة المعيرة في حالة الاستعارة
    delivery_note_ref TEXT,                  -- رقم وصل تسليم المورد (Bon de livraison)
    total_amount REAL NOT NULL DEFAULT 0.0,  -- القيمة المالية الإجمالية TTC
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. تفاصيل بنود وصل الدخول (Entry Voucher Items)
CREATE TABLE IF NOT EXISTS entry_voucher_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voucher_id INTEGER NOT NULL REFERENCES entry_vouchers(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE RESTRICT,
    quantity REAL NOT NULL CHECK(quantity > 0),
    unit_price_ht REAL NOT NULL DEFAULT 0.0,
    tva_rate REAL NOT NULL DEFAULT 0.0,
    unit_price_ttc REAL NOT NULL DEFAULT 0.0,
    total_price REAL NOT NULL DEFAULT 0.0
);

-- 8. جدول وصولات الإخراج والاستهلاك (Exit Vouchers - Bons de Sortie)
CREATE TABLE IF NOT EXISTS exit_vouchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    residence_id INTEGER REFERENCES residences(id) DEFAULT 1,
    voucher_number TEXT NOT NULL,            -- رقم وصل الإخراج
    date TEXT NOT NULL,                      -- تاريخ الاستهلاك YYYY-MM-DD
    voucher_type TEXT NOT NULL DEFAULT 'KITCHEN', -- 'KITCHEN' استهلاك مطبخ, 'LOAN_OUT' إعارة
    destination_residence TEXT,              -- الإقامة المستعيرة في حالة الإعارة
    total_breakfast_cost REAL NOT NULL DEFAULT 0.0,
    total_lunch_cost REAL NOT NULL DEFAULT 0.0,
    total_dinner_cost REAL NOT NULL DEFAULT 0.0,
    total_amount REAL NOT NULL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. تفاصيل بنود وصل الإخراج (Exit Voucher Items)
CREATE TABLE IF NOT EXISTS exit_voucher_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voucher_id INTEGER NOT NULL REFERENCES exit_vouchers(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE RESTRICT,
    qty_breakfast REAL NOT NULL DEFAULT 0.0, -- كمية فطور الصباح
    qty_lunch REAL NOT NULL DEFAULT 0.0,     -- كمية الغداء
    qty_dinner REAL NOT NULL DEFAULT 0.0,    -- كمية العشاء
    qty_other REAL NOT NULL DEFAULT 0.0,     -- كمية الإعارة أو أخرى
    total_qty REAL NOT NULL CHECK(total_qty > 0),
    unit_price_ttc REAL NOT NULL DEFAULT 0.0,-- السعر المعتمد للتقييم
    total_cost REAL NOT NULL DEFAULT 0.0
);

-- 10. جدول متابعة الوجبات وتعداد التذاكر اليومية (Daily Meals & Tickets Tracking)
CREATE TABLE IF NOT EXISTS daily_meals_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    residence_id INTEGER REFERENCES residences(id) DEFAULT 1,
    date TEXT NOT NULL,                      -- التاريخ YYYY-MM-DD
    -- فطور الصباح
    bf_students INTEGER NOT NULL DEFAULT 0,
    bf_staff INTEGER NOT NULL DEFAULT 0,
    bf_professors INTEGER NOT NULL DEFAULT 0,
    bf_guests INTEGER NOT NULL DEFAULT 0,
    bf_free INTEGER NOT NULL DEFAULT 0,
    bf_total INTEGER NOT NULL DEFAULT 0,
    -- وجبة الغداء
    lu_students INTEGER NOT NULL DEFAULT 0,
    lu_staff INTEGER NOT NULL DEFAULT 0,
    lu_professors INTEGER NOT NULL DEFAULT 0,
    lu_guests INTEGER NOT NULL DEFAULT 0,
    lu_free INTEGER NOT NULL DEFAULT 0,
    lu_total INTEGER NOT NULL DEFAULT 0,
    -- وجبة العشاء
    di_students INTEGER NOT NULL DEFAULT 0,
    di_staff INTEGER NOT NULL DEFAULT 0,
    di_professors INTEGER NOT NULL DEFAULT 0,
    di_guests INTEGER NOT NULL DEFAULT 0,
    di_free INTEGER NOT NULL DEFAULT 0,
    di_total INTEGER NOT NULL DEFAULT 0,
    -- إحصائيات وتكاليف اليوم
    average_daily_meals REAL NOT NULL DEFAULT 0.0, -- (الغداء + العشاء) / 2
    daily_food_expense REAL NOT NULL DEFAULT 0.0,  -- إجمالي تكلفة المواد المستهلكة
    student_daily_cost REAL NOT NULL DEFAULT 0.0,  -- تكلفة إطعام الطالب اليومية
    bf_expense REAL NOT NULL DEFAULT 0.0,
    lu_expense REAL NOT NULL DEFAULT 0.0,
    di_expense REAL NOT NULL DEFAULT 0.0,
    menu_breakfast TEXT,
    menu_lunch TEXT,
    menu_dinner TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, residence_id)
);

-- 11. جدول سجل حركات المخزون الشامل (Stock Movements Audit Trail)
CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    residence_id INTEGER REFERENCES residences(id) DEFAULT 1,
    date TEXT NOT NULL,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    movement_type TEXT NOT NULL, -- INITIAL, SUPPLY_IN, LOAN_IN, BREAKFAST_OUT, LUNCH_OUT, DINNER_OUT, LOAN_OUT, ADJ
    voucher_id INTEGER,
    qty_in REAL NOT NULL DEFAULT 0.0,
    qty_out REAL NOT NULL DEFAULT 0.0,
    unit_price REAL NOT NULL DEFAULT 0.0,
    total_value REAL NOT NULL DEFAULT 0.0,
    balance_after REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. جدول بطاقات الجرد الدوري والشهري (Inventory Snapshots)
CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    residence_id INTEGER REFERENCES residences(id) DEFAULT 1,
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

-- 13. جدول الإقامات الجامعية التابعة للمديرية (Residences / Campuses)
CREATE TABLE IF NOT EXISTS residences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,               -- رمز الإقامة (مثل RES-01)
    name TEXT NOT NULL,                      -- الاسم الرسمي للإقامة
    name_fr TEXT,                            -- الاسم بالفرنسية
    city TEXT DEFAULT 'ورقلة',               -- الولاية / المدينة
    address TEXT,                            -- العنوان الفعلي
    network_ip TEXT DEFAULT '127.0.0.1',      -- عنوان IP للعميل / الإقامة
    director_name TEXT,                      -- اسم مدير الإقامة
    phone TEXT,                              -- رقم الهاتف
    capacity INTEGER DEFAULT 1000,           -- طاقة الاستيعاب بالأسرة
    status TEXT DEFAULT 'ONLINE',            -- حالة الاتصال (ONLINE, OFFLINE)
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. جدول المستخدمين والصلاحيات (Users & Roles)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'STOREKEEPER', -- 'SUPER_ADMIN', 'MANAGER', 'STOREKEEPER'
    residence_id INTEGER REFERENCES residences(id) ON DELETE SET NULL,
    phone TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. جدول أرصدة المواد الخاصة بكل إقامة (Multi-Campus Stock Isolation)
CREATE TABLE IF NOT EXISTS residence_articles (
    residence_id INTEGER NOT NULL REFERENCES residences(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    initial_stock REAL NOT NULL DEFAULT 0.0,
    current_stock REAL NOT NULL DEFAULT 0.0,
    safety_stock REAL NOT NULL DEFAULT 0.0,
    current_pmp REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY(residence_id, article_id)
);

-- 16. جدول رتل المزامنة للعمل دون اتصال (Offline-First Sync Queue)
CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_id TEXT UNIQUE NOT NULL,            -- معرف فريد للعملية UUID
    residence_id INTEGER NOT NULL,           -- رقم الإقامة صاحبة الحركة
    entity_type TEXT NOT NULL,               -- نوع الكيان (entry_voucher, exit_voucher, daily_meals, article)
    action TEXT NOT NULL,                    -- INSERT, UPDATE, DELETE
    entity_id TEXT,                          -- المعرف المحلي
    payload TEXT NOT NULL,                   -- محتوى البيانات بصيغة JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING, SYNCED, FAILED
    retry_count INTEGER DEFAULT 0,
    error_message TEXT
);

-- 17. جدول حالة ونقاط تفتيش المزامنة (Sync Checkpoint State)
CREATE TABLE IF NOT EXISTS sync_state (
    residence_id INTEGER PRIMARY KEY,
    last_push_timestamp TIMESTAMP,
    last_pull_timestamp TIMESTAMP,
    status TEXT DEFAULT 'IDLE'
);

-- 18. جدول حركة الإعارة والاستعارة التبادلية بين الإقامات (Inter-Residence Loans)
CREATE TABLE IF NOT EXISTS residence_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_number TEXT UNIQUE NOT NULL,            -- رقم مرجعي مثل LOAN-2026-0001
    from_residence_id INTEGER NOT NULL REFERENCES residences(id), -- الإقامة المعيرة / المانحة
    to_residence_id INTEGER NOT NULL REFERENCES residences(id),   -- الإقامة المستعيرة / المستفيدة
    date TEXT NOT NULL,                          -- تاريخ الإعارة YYYY-MM-DD
    status TEXT NOT NULL DEFAULT 'PENDING',      -- 'PENDING' في الانتظار, 'RECEIVED' تم الاستلام والتأكيد, 'CANCELLED' ملغاة
    entry_voucher_id INTEGER REFERENCES entry_vouchers(id) ON DELETE SET NULL,
    exit_voucher_id INTEGER REFERENCES exit_vouchers(id) ON DELETE SET NULL,
    notes TEXT,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    received_at TIMESTAMP
);

-- 19. تفاصيل بنود الإعارة والاستعارة (Inter-Residence Loan Items)
CREATE TABLE IF NOT EXISTS residence_loan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES residence_loans(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE RESTRICT,
    quantity REAL NOT NULL CHECK(quantity > 0),
    unit_price_ttc REAL NOT NULL DEFAULT 0.0,
    total_price REAL NOT NULL DEFAULT 0.0
);

-- 20. جدول الأيام المرخصة استثنائياً من المديرية للإقامات (Unlocked Days Override)
CREATE TABLE IF NOT EXISTS unlocked_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    residence_id INTEGER NOT NULL REFERENCES residences(id),
    date TEXT NOT NULL,                         -- التاريخ المرخص YYYY-MM-DD
    unlocked_by TEXT DEFAULT 'DIRECTORATE',     -- اسم المسؤول / المديرية
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,                                 -- سبب الفتح الاستثنائي
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE(residence_id, date)
);

-- الفهارس لتحقيق أقصى سرعة في الاستعلامات (Indices for High Performance)
CREATE INDEX IF NOT EXISTS idx_articles_name ON articles(name);
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category_id);
CREATE INDEX IF NOT EXISTS idx_entry_date ON entry_vouchers(date);
CREATE INDEX IF NOT EXISTS idx_exit_date ON exit_vouchers(date);
CREATE INDEX IF NOT EXISTS idx_movements_date ON stock_movements(date);
CREATE INDEX IF NOT EXISTS idx_movements_article ON stock_movements(article_id);
CREATE INDEX IF NOT EXISTS idx_meals_date ON daily_meals_tracking(date);
CREATE INDEX IF NOT EXISTS idx_inventory_period ON inventory_snapshots(year, month);
CREATE INDEX IF NOT EXISTS idx_movements_res_date ON stock_movements(residence_id, date);
CREATE INDEX IF NOT EXISTS idx_entry_res_date ON entry_vouchers(residence_id, date);
CREATE INDEX IF NOT EXISTS idx_exit_res_date ON exit_vouchers(residence_id, date);
CREATE INDEX IF NOT EXISTS idx_meals_res_date ON daily_meals_tracking(residence_id, date);
CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status, residence_id);
CREATE INDEX IF NOT EXISTS idx_residence_loans_from ON residence_loans(from_residence_id, date);
CREATE INDEX IF NOT EXISTS idx_residence_loans_to ON residence_loans(to_residence_id, date);
CREATE INDEX IF NOT EXISTS idx_residence_loans_status ON residence_loans(status);
CREATE INDEX IF NOT EXISTS idx_unlocked_days_res_date ON unlocked_days(residence_id, date, is_active);

