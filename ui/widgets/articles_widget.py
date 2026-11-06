from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QLineEdit, QComboBox, QDialog, QFormLayout, QDoubleSpinBox,
    QMessageBox, QTabWidget, QFileDialog, QCheckBox, QProgressDialog, QApplication
)
from typing import Optional
from core.sync_service import SyncService
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextDocument, QColor
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from core.stock_service import StockService
from reports.report_generator import ReportGenerator
from ui.widgets.pagination_bar import PaginationBar
from ui.theme import ThemeManager

class ArticleDialog(QDialog):
    """نافذة إضافة أو تعديل مادة غذائية مع حسابات التخفيض والرسوم بدقة وعزل تسعير كل إقامة"""

    def __init__(self, stock_service: StockService, article_data=None, residence_id: Optional[int] = None, residence_name: str = "", parent=None):
        super().__init__(parent)
        self.stock_svc = stock_service
        self.article_data = article_data or {}
        self.residence_id = residence_id or getattr(stock_service, "residence_id", 1)
        self.residence_name = residence_name
        if not self.residence_name:
            try:
                with self.stock_svc.db.get_connection() as conn:
                    r_row = conn.execute("SELECT name FROM residences WHERE id = ?", (self.residence_id,)).fetchone()
                    if r_row:
                        self.residence_name = r_row["name"]
            except Exception:
                self.residence_name = f"الإقامة {self.residence_id}"

        self.setWindowTitle("تعديل مادة غذائية" if article_data else "إضافة مادة غذائية جديدة")
        self.resize(520, 580)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # لافتة تعريفية بالإقامة المستهدفة بالتسعير
        lbl_res_banner = QLabel(f"🏢 تسعير خاص بـ: {self.residence_name}")
        lbl_res_banner.setStyleSheet(
            "background: rgba(14, 165, 233, 0.12); color: #0284C7; font-weight: bold; "
            "font-size: 13px; padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(14, 165, 233, 0.3);"
        )
        layout.addWidget(lbl_res_banner)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_code = QLineEdit(str(self.article_data.get("code") or ""))
        self.txt_name = QLineEdit(self.article_data.get("name") or "")

        self.cmb_category = QComboBox()
        with self.stock_svc.db.get_connection() as conn:
            cats = conn.execute("SELECT id, name FROM categories ORDER BY id").fetchall()
            for c in cats:
                self.cmb_category.addItem(c["name"], c["id"])
        if self.article_data.get("category_id"):
            for i in range(self.cmb_category.count()):
                if self.cmb_category.itemData(i) == self.article_data["category_id"]:
                    self.cmb_category.setCurrentIndex(i)
                    break

        self.txt_unit = QComboBox()
        self.txt_unit.setEditable(True)
        self.txt_unit.addItems(["كلغ", "لتر", "علبة", "قارورة", "وحدة", "حزمة", "خبزة", "حبة", "كيس", "بيضة", "دلو"])
        if self.article_data.get("unit"):
            self.txt_unit.setCurrentText(self.article_data["unit"])

        # 1. سعر بدون رسوم (HT)
        self.spn_price_ht = QDoubleSpinBox()
        self.spn_price_ht.setRange(0.0, 999999.0)
        self.spn_price_ht.setDecimals(2)
        self.spn_price_ht.setValue(float(self.article_data.get("price_ht", 0.0)))

        # 2. نسبة التخفيض (%)
        self.spn_discount = QDoubleSpinBox()
        self.spn_discount.setRange(0.0, 100.0)
        self.spn_discount.setDecimals(2)
        self.spn_discount.setSuffix(" %")
        disc_val = float(self.article_data.get("discount_rate", 0.0)) * 100.0
        self.spn_discount.setValue(disc_val)

        # 3. قيمة التخفيض المحسوبة
        self.lbl_discount_amt = QLabel("0.00 دج")
        self.lbl_discount_amt.setStyleSheet("font-weight: bold; color: #E11D48;")

        # 4. السعر بعد التخفيض
        self.lbl_price_after = QLabel("0.00 دج")
        self.lbl_price_after.setStyleSheet("font-weight: bold; color: #0284C7;")

        # 5. ض ق م (TVA)
        self.spn_tva = QComboBox()
        self.spn_tva.addItems(["0 %", "9 %", "19 %"])
        tva_val = int(self.article_data.get("tva_rate", 0))
        self.spn_tva.setCurrentText(f"{tva_val} %")

        # 6. السعر بكامل الرسوم (TTC)
        self.lbl_calculated_ttc = QLabel("0.00 دج")
        self.lbl_calculated_ttc.setStyleSheet("font-size: 16px; font-weight: bold; color: #0D9488;")

        # المخزون والأمان
        self.spn_safety = QDoubleSpinBox()
        self.spn_safety.setRange(0.0, 99999.0)
        self.spn_safety.setValue(float(self.article_data.get("safety_stock", 10.0)))

        self.spn_initial = QDoubleSpinBox()
        self.spn_initial.setRange(0.0, 99999.0)
        self.spn_initial.setValue(float(self.article_data.get("initial_stock", 0.0)))
        if self.article_data:
            self.spn_initial.setEnabled(False)

        form.addRow("رقم الحصة / الرمز:", self.txt_code)
        form.addRow("اسم المادة الغذائية *:", self.txt_name)
        form.addRow("الفئة:", self.cmb_category)
        form.addRow("وحدة القياس:", self.txt_unit)
        form.addRow("سعر بدون رسوم (HT):", self.spn_price_ht)
        form.addRow("نسبة التخفيض (%):", self.spn_discount)
        form.addRow("قيمة التخفيض المحسوبة:", self.lbl_discount_amt)
        form.addRow("السعر بعد التخفيض:", self.lbl_price_after)
        form.addRow("ض.ق.م (TVA):", self.spn_tva)
        form.addRow("السعر بكامل الرسوم (TTC):", self.lbl_calculated_ttc)
        form.addRow("مخزون الأمان (الحد الأدنى):", self.spn_safety)
        if not self.article_data:
            form.addRow("الرصيد الافتتاحي الأولي:", self.spn_initial)

        layout.addLayout(form)

        # ربط التغييرات لحساب السعر التلقائي
        self.spn_price_ht.valueChanged.connect(self.calculate_all_prices)
        self.spn_discount.valueChanged.connect(self.calculate_all_prices)
        self.spn_tva.currentTextChanged.connect(self.calculate_all_prices)
        self.calculate_all_prices()

        self.chk_apply_all = QCheckBox("تعميم هذه الأسعار على جميع الإقامات أيضاً")
        self.chk_apply_all.setStyleSheet("color: #94A3B8; font-size: 12px; margin-top: 4px; font-weight: 500;")
        layout.addWidget(self.chk_apply_all)

        # أزرار الحفظ والإلغاء
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("حفظ التغييرات ✔")
        btn_save.setProperty("class", "btn-primary")
        btn_save.setStyleSheet("padding: 8px 18px; font-weight: bold;")
        btn_save.clicked.connect(self.save_data)

        btn_cancel = QPushButton("إلغاء ✖")
        btn_cancel.setProperty("class", "btn-secondary")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def calculate_all_prices(self):
        p_ht = self.spn_price_ht.value()
        disc_pct = self.spn_discount.value() / 100.0
        disc_amt = p_ht * disc_pct
        p_after = p_ht - disc_amt

        tva_str = self.spn_tva.currentText().replace("%", "").strip()
        tva_val = float(tva_str) if tva_str else 0.0
        p_ttc = p_after * (1.0 + (tva_val / 100.0))

        self.lbl_discount_amt.setText(f"{disc_amt:,.2f} دج")
        self.lbl_price_after.setText(f"{p_after:,.2f} دج")
        self.lbl_calculated_ttc.setText(f"{p_ttc:,.2f} دج")

        return p_ht, disc_pct, disc_amt, p_after, tva_val, p_ttc

    def save_data(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال اسم المادة الغذائية!")
            return

        p_ht, disc_pct, disc_amt, p_after, tva_val, p_ttc = self.calculate_all_prices()

        data = {
            "id": self.article_data.get("id"),
            "code": self.txt_code.text().strip(),
            "name": name,
            "category_id": self.cmb_category.currentData(),
            "unit": self.txt_unit.currentText(),
            "price_ht": p_ht,
            "discount_rate": disc_pct,
            "discount_amount": disc_amt,
            "price_after_discount": p_after,
            "tva_rate": tva_val,
            "price_ttc": p_ttc,
            "safety_stock": self.spn_safety.value(),
            "initial_stock": self.spn_initial.value()
        }
        try:
            self.stock_svc.save_article(
                data,
                residence_id=self.residence_id,
                apply_to_all_residences=self.chk_apply_all.isChecked()
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر حفظ المادة: {e}")


class ArticlesWidget(QWidget):
    """
    شاشة قائمة الأسعار ودليل المواد
    مطابقة تماماً لورقة 'الأسعار' في ملفات Excel مع الأعمدة الرسمية:
    (رقم الحصة | إسم المادة | الوحدة | سعر بدون رسوم | نسبة التخفيض | قيمة التخفيض | السعر بعد التخفيض | ض ق م / TVA | السعر بكامل الرسوم)
    تتيح التعديل المباشر داخل الجدول مع زر حفظ التغييرات وعزل تام لأسعار كل إقامة.
    """

    article_saved = pyqtSignal()
    residence_changed = pyqtSignal(int, str)

    def __init__(self, stock_service: StockService, is_directorate: bool = False, parent=None):
        super().__init__(parent)
        self.stock_svc = stock_service
        self.is_directorate = is_directorate
        self.sync_svc = SyncService(self.stock_svc.db)
        self.current_residence_id = getattr(self.stock_svc, "residence_id", 1)
        self.current_residence_name = ""
        self.modified_articles = {} # art_id -> dict of modified prices

        try:
            with self.stock_svc.db.get_connection() as conn:
                r_row = conn.execute("SELECT name FROM residences WHERE id = ?", (self.current_residence_id,)).fetchone()
                if r_row:
                    self.current_residence_name = r_row["name"]
        except Exception:
            self.current_residence_name = f"الإقامة {self.current_residence_id}"

        self.report_gen = ReportGenerator(self.stock_svc.db)
        self.all_articles = []
        self.init_ui()
        self.load_articles()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(15, 12, 15, 15)
        root_layout.setSpacing(10)

        # التبويبات الرئيسية
        self.tabs = QTabWidget()

        # -------------------------------------------------------------
        # التبويب 1: قائمة الأسعار الرسمية (مطابقة لورقة Excel)
        # -------------------------------------------------------------
        tab_price_list = QWidget()
        pl_layout = QVBoxLayout(tab_price_list)
        pl_layout.setContentsMargins(10, 10, 10, 10)
        pl_layout.setSpacing(10)

        # عنوان ورقة الأسعار مطابق للإكسل
        title_box = QFrame()
        title_box.setProperty("class", "content-panel")
        tb_h_layout = QHBoxLayout(title_box)
        tb_h_layout.setContentsMargins(4, 4, 4, 4)

        lbl_excel_title = QLabel("قائمة الأسعار")
        lbl_excel_title.setProperty("class", "page-title")
        self.lbl_excel_sub = QLabel(f"جدول الأسعار التعاقدية والتخفيضات والرسوم - {self.current_residence_name}")
        self.lbl_excel_sub.setStyleSheet("font-size: 11px; color: #38BDF8; margin-right: 15px; font-weight: bold;")

        tb_h_layout.addWidget(lbl_excel_title)
        tb_h_layout.addWidget(self.lbl_excel_sub)
        tb_h_layout.addStretch()

        # أزرار الإجراءات في شريط العنوان
        btn_print_price = QPushButton("🖨️ طباعة قائمة الأسعار")
        btn_print_price.setProperty("class", "btn-secondary")
        btn_print_price.clicked.connect(self.print_price_list)
        tb_h_layout.addWidget(btn_print_price)

        btn_export_excel = QPushButton("📑 تصدير إلى Excel")
        btn_export_excel.setProperty("class", "btn-secondary")
        btn_export_excel.clicked.connect(self.export_price_list_excel)
        tb_h_layout.addWidget(btn_export_excel)

        btn_import_excel = QPushButton("📥 استيراد من Excel")
        btn_import_excel.setProperty("class", "btn-secondary")
        btn_import_excel.setStyleSheet("font-weight: bold; background: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; color: #34D399;")
        btn_import_excel.setToolTip("استيراد الأسعار مباشرة من ملف Excel (مثل prix.xls) وتحديث الواجهات فوراً")
        btn_import_excel.clicked.connect(self.import_price_list_excel)
        tb_h_layout.addWidget(btn_import_excel)

        btn_add = QPushButton("+ إضافة مادة جديدة")
        btn_add.setProperty("class", "btn-primary")
        btn_add.clicked.connect(self.open_add_dialog)
        tb_h_layout.addWidget(btn_add)

        pl_layout.addWidget(title_box)

        # شريط التصفية والبحث
        filter_bar = QFrame()
        filter_bar.setProperty("class", "content-panel")
        fb_layout = QHBoxLayout(filter_bar)
        fb_layout.setContentsMargins(10, 6, 10, 6)
        fb_layout.setSpacing(10)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 بحث فوري باسم المادة الغذائية أو رقم الحصة...")
        self.txt_search.textChanged.connect(self.load_articles)
        fb_layout.addWidget(self.txt_search, stretch=3)

        self.cmb_category = QComboBox()
        self.cmb_category.addItem("جميع الفئات الغذائية", None)
        with self.stock_svc.db.get_connection() as conn:
            cats = conn.execute("SELECT id, name FROM categories ORDER BY id").fetchall()
            for c in cats:
                self.cmb_category.addItem(c["name"], c["id"])
        self.cmb_category.currentIndexChanged.connect(self.load_articles)
        fb_layout.addWidget(self.cmb_category, stretch=2)

        # في وضع المديرية: إظهار قائمة اختيار الإقامات للتبديل السريع بين أسعار الإقامات المختلفة
        if self.is_directorate:
            self.lbl_res_filter = QLabel("🏢 الإقامة:")
            self.lbl_res_filter.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 12px; margin-right: 5px;")
            self.cmb_residence_filter = QComboBox()
            self.cmb_residence_filter.setStyleSheet("font-weight: bold; padding: 4px 10px; border: 1px solid #0284C7; border-radius: 6px;")
            with self.stock_svc.db.get_connection() as conn:
                res_list = conn.execute("SELECT id, name FROM residences ORDER BY id").fetchall()
                for r in res_list:
                    self.cmb_residence_filter.addItem(r["name"], r["id"])
            for idx in range(self.cmb_residence_filter.count()):
                if self.cmb_residence_filter.itemData(idx) == self.current_residence_id:
                    self.cmb_residence_filter.setCurrentIndex(idx)
                    break
            self.cmb_residence_filter.currentIndexChanged.connect(self.on_residence_filter_changed)
            fb_layout.addWidget(self.lbl_res_filter)
            fb_layout.addWidget(self.cmb_residence_filter, stretch=2)

        # زر حفظ التغييرات السعرية البارز
        self.btn_save_changes = QPushButton("💾 حفظ التغييرات")
        self.btn_save_changes.setProperty("class", "btn-primary")
        self.btn_save_changes.setStyleSheet("background-color: #059669; color: white; font-weight: bold; font-size: 13px; padding: 6px 20px; border-radius: 6px;")
        self.btn_save_changes.setToolTip("حفظ كافة تعديلات الأسعار في قاعدة البيانات وتحديث كافة الواجهات بالقيم الجديدة فوراً")
        self.btn_save_changes.clicked.connect(self.save_all_price_changes)
        fb_layout.addWidget(self.btn_save_changes)

        # زر سحب الأسعار المحدثة من السيرفر/المديرية
        self.btn_pull_prices = QPushButton("🔄 سحب الأسعار المحدثة")
        self.btn_pull_prices.setProperty("class", "btn-secondary")
        self.btn_pull_prices.setStyleSheet("font-weight: bold; background: rgba(14, 165, 233, 0.15); border: 1px solid #0284C7; color: #38BDF8;")
        self.btn_pull_prices.setToolTip("سحب وتحديث الأسعار المعتمدة من الخادم/المديرية لإقامتك")
        self.btn_pull_prices.clicked.connect(self.pull_updated_prices)
        fb_layout.addWidget(self.btn_pull_prices)

        btn_refresh = QPushButton("تحديث ⟳")
        btn_refresh.setProperty("class", "btn-secondary")
        btn_refresh.clicked.connect(self.load_articles)
        fb_layout.addWidget(btn_refresh)

        pl_layout.addWidget(filter_bar)

        # جدول قائمة الأسعار (مطابق لأعمدة ورقة الأسعار في Excel تماماً)
        self.table_prices = QTableWidget()
        self.table_prices.setColumnCount(9)
        self.table_prices.setHorizontalHeaderLabels([
            "رقم الحصة",
            "إسم المادة",
            "الوحدة",
            "سعر بدون رسوم ✏️",
            "نسبة التخفيض ✏️",
            "قيمة التخفيض",
            "السعر بعد التخفيض",
            "ض ق م / TVA ✏️",
            "السعر بكامل الرسوم"
        ])

        # ضبط مقاسات الأعمدة بدقة
        hdr = self.table_prices.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # اسم المادة يتمدد

        self.table_prices.setColumnWidth(0, 90)   # رقم الحصة
        self.table_prices.setColumnWidth(2, 65)   # الوحدة
        self.table_prices.setColumnWidth(3, 125)  # سعر بدون رسوم
        self.table_prices.setColumnWidth(4, 100)  # نسبة التخفيض
        self.table_prices.setColumnWidth(5, 105)  # قيمة التخفيض
        self.table_prices.setColumnWidth(6, 120)  # السعر بعد التخفيض
        self.table_prices.setColumnWidth(7, 100)  # ض ق م TVA
        self.table_prices.setColumnWidth(8, 135)  # السعر بكامل الرسوم

        self.table_prices.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_prices.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked | QTableWidget.EditTrigger.EditKeyPressed)
        self.table_prices.cellDoubleClicked.connect(self.on_table_cell_double_clicked)
        self.table_prices.itemChanged.connect(self.on_price_cell_changed)
        self.table_prices.verticalHeader().setDefaultSectionSize(30)
        from ui.common_filters import attach_smooth_scroll
        attach_smooth_scroll(self.table_prices)
        pl_layout.addWidget(self.table_prices)

        # شريط تقسيم الصفحات
        self.pagination_prices = PaginationBar(initial_page_size=15, page_size_options=(10, 15, 25, 50, 100))
        self.pagination_prices.page_changed.connect(self.render_prices_page)
        self.pagination_prices.page_size_changed.connect(self.render_prices_page)
        self.pagination_prices.attach_to_table(self.table_prices)
        pl_layout.addWidget(self.pagination_prices)

        # شريط التلميح والتحكم السفلي
        bottom_box = QHBoxLayout()
        lbl_hint = QLabel("💡 تلميح: يمكنك تعديل (سعر بدون رسوم، نسبة التخفيض، ض ق م) مباشرة في خلايا الجدول ثم النقر على '💾 حفظ التغييرات'، أو النقر المزدوج على اسم المادة لفتح نافذة التعديل.")
        lbl_hint.setStyleSheet("color: #64748B; font-size: 11px;")
        bottom_box.addWidget(lbl_hint)
        bottom_box.addStretch()

        btn_delete = QPushButton("🗑️ حذف المادة المحددة")
        btn_delete.setProperty("class", "btn-secondary")
        btn_delete.setStyleSheet("background-color: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.4); font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        btn_delete.setToolTip("حذف أو إخفاء المادة المحددة بأمان من قائمة الأسعار")
        btn_delete.clicked.connect(self.delete_selected_article)
        bottom_box.addWidget(btn_delete)

        btn_edit = QPushButton("تعديل المادة المحددة ✏")
        btn_edit.setProperty("class", "btn-secondary")
        btn_edit.clicked.connect(self.open_edit_dialog)
        bottom_box.addWidget(btn_edit)
        pl_layout.addLayout(bottom_box)

        self.tabs.addTab(tab_price_list, "📋 قائمة الأسعار (مطابقة تماماً لورقة الأسعار في Excel)")

        # -------------------------------------------------------------
        # التبويب 2: دليل المواد والمخزون الحي وحصص الأمان
        # -------------------------------------------------------------
        tab_inventory = QWidget()
        inv_layout = QVBoxLayout(tab_inventory)
        inv_layout.setContentsMargins(10, 10, 10, 10)
        inv_layout.setSpacing(10)

        self.table_stock = QTableWidget()
        self.table_stock.setColumnCount(9)
        self.table_stock.setHorizontalHeaderLabels([
            "الحصة", "اسم المادة الغذائية", "الفئة", "الوحدة", "السعر TTC",
            "المخزون المتوفر", "مخزون الأمان", "الرصيد الأولي", "الحالة"
        ])
        hdr_s = self.table_stock.horizontalHeader()
        hdr_s.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr_s.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_stock.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_stock.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_stock.doubleClicked.connect(self.open_edit_dialog)
        from ui.common_filters import attach_smooth_scroll
        attach_smooth_scroll(self.table_stock)
        inv_layout.addWidget(self.table_stock)

        self.pagination_stock = PaginationBar(initial_page_size=15, page_size_options=(10, 15, 25, 50, 100))
        self.pagination_stock.page_changed.connect(self.render_stock_page)
        self.pagination_stock.page_size_changed.connect(self.render_stock_page)
        self.pagination_stock.attach_to_table(self.table_stock)
        inv_layout.addWidget(self.pagination_stock)

        self.tabs.addTab(tab_inventory, "📦 دليل المواد والمخزون الحي وحصص الأمان")

        root_layout.addWidget(self.tabs)

    def on_residence_filter_changed(self, index: int):
        """معالجة اختيار الإقامة من القائمة في وضع المديرية"""
        if not hasattr(self, "cmb_residence_filter") or self.cmb_residence_filter is None:
            return
        r_id = self.cmb_residence_filter.currentData()
        r_name = self.cmb_residence_filter.currentText()
        if r_id and r_id != self.current_residence_id:
            self.set_residence(r_id, r_name)
            self.residence_changed.emit(r_id, r_name)

    def set_residence(self, r_id: int, r_name: str):
        """استقبال تغيير الإقامة النشطة وضبط عرض أسعارها حصراً"""
        self.current_residence_id = r_id
        self.current_residence_name = r_name
        self.modified_articles.clear()
        if hasattr(self, "lbl_excel_sub"):
            self.lbl_excel_sub.setText(f"جدول الأسعار التعاقدية والتخفيضات والرسوم - {r_name}")
        if hasattr(self, "cmb_residence_filter") and self.cmb_residence_filter:
            self.cmb_residence_filter.blockSignals(True)
            for idx in range(self.cmb_residence_filter.count()):
                if self.cmb_residence_filter.itemData(idx) == r_id:
                    self.cmb_residence_filter.setCurrentIndex(idx)
                    break
            self.cmb_residence_filter.blockSignals(False)
        self.load_articles()

    def load_articles(self):
        search = self.txt_search.text().strip()
        cat_id = self.cmb_category.currentData()
        r_id = getattr(self, "current_residence_id", None) or self.stock_svc.residence_id
        self.all_articles = self.stock_svc.get_articles(search=search, category_id=cat_id, residence_id=r_id)

        self.pagination_prices.set_total_items(len(self.all_articles), reset_page=True)
        self.pagination_stock.set_total_items(len(self.all_articles), reset_page=True)

        self.render_prices_page()
        self.render_stock_page()

    def render_prices_page(self):
        self.table_prices.blockSignals(True)
        start_idx, end_idx = self.pagination_prices.get_slice_range()
        page_items = self.all_articles[start_idx:end_idx]

        self.table_prices.setRowCount(len(page_items))
        for r, art in enumerate(page_items):
            art_id = art["id"]
            is_modified = art_id in self.modified_articles
            mod_data = self.modified_articles.get(art_id, {})

            p_ht = mod_data.get("price_ht", art["price_ht"])
            disc_rate = mod_data.get("discount_rate", float(art.get("discount_rate") or 0.0))
            disc_amt = mod_data.get("discount_amount", float(art.get("discount_amount") or (p_ht * disc_rate)))
            p_after = mod_data.get("price_after_discount", float(art.get("price_after_discount") or (p_ht - disc_amt)))
            tva_val = mod_data.get("tva_rate", float(art.get("tva_rate") or 0.0))
            p_ttc = mod_data.get("price_ttc", art["price_ttc"])

            # 0. رقم الحصة
            c_code = QTableWidgetItem(str(art.get("code") or "-"))
            c_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            c_code.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table_prices.setItem(r, 0, c_code)

            # 1. إسم المادة
            c_name = QTableWidgetItem(art["name"])
            c_name.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            c_name.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table_prices.setItem(r, 1, c_name)

            # 2. الوحدة
            c_unit = QTableWidgetItem(art.get("unit") or "كلغ")
            c_unit.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            c_unit.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table_prices.setItem(r, 2, c_unit)

            # 3. سعر بدون رسوم (قابل للتعديل المباشر)
            c_ht = QTableWidgetItem(f"{p_ht:,.2f}")
            c_ht.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            c_ht.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
            c_ht.setData(Qt.ItemDataRole.UserRole, art_id)
            self.table_prices.setItem(r, 3, c_ht)

            # 4. نسبة التخفيض (قابلة للتعديل المباشر)
            c_dr = QTableWidgetItem(f"{int(disc_rate * 100)}%")
            c_dr.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            c_dr.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
            self.table_prices.setItem(r, 4, c_dr)

            # 5. قيمة التخفيض (محسوبة تلقائياً)
            c_da = QTableWidgetItem(f"{disc_amt:,.2f}")
            c_da.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            c_da.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table_prices.setItem(r, 5, c_da)

            # 6. السعر بعد التخفيض (محسوب تلقائياً)
            c_pa = QTableWidgetItem(f"{p_after:,.2f}")
            c_pa.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            c_pa.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table_prices.setItem(r, 6, c_pa)

            # 7. ض ق م / TVA (قابلة للتعديل المباشر)
            c_tva = QTableWidgetItem(f"{int(tva_val)}%")
            c_tva.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            c_tva.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
            self.table_prices.setItem(r, 7, c_tva)

            # 8. السعر بكامل الرسوم (TTC - محسوب تلقائياً)
            is_dark = ThemeManager.is_dark_mode()
            ttc_color = QColor("#34D399") if is_dark else QColor("#059669")
            c_ttc = QTableWidgetItem(f"{p_ttc:,.2f}")
            c_ttc.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            c_ttc.setForeground(ttc_color)
            font = c_ttc.font()
            font.setBold(True)
            c_ttc.setFont(font)
            c_ttc.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table_prices.setItem(r, 8, c_ttc)

            if is_modified:
                for c in range(9):
                    cell = self.table_prices.item(r, c)
                    if cell:
                        cell.setBackground(QColor(16, 185, 129, 45))

        self.table_prices.blockSignals(False)

    def on_table_cell_double_clicked(self, row: int, col: int):
        """النقر المزدوج على اسم المادة أو الحصة يفتح نافذة التعديل الشامل"""
        if col in (0, 1, 2):
            self.open_edit_dialog()

    def on_price_cell_changed(self, item: QTableWidgetItem):
        """معالجة التعديل المباشر في خلايا الأسعار وإعادة الحساب فوراً"""
        if not item:
            return
        col = item.column()
        if col not in (3, 4, 7):
            return

        row = item.row()
        c_ht_item = self.table_prices.item(row, 3)
        if not c_ht_item:
            return

        art_id = c_ht_item.data(Qt.ItemDataRole.UserRole)
        if not art_id:
            return

        # استخراج القيم المدخلة بأمان
        try:
            p_ht_str = self.table_prices.item(row, 3).text().replace(",", "").replace(" ", "").strip()
            p_ht = max(0.0, float(p_ht_str)) if p_ht_str else 0.0
        except ValueError:
            p_ht = 0.0

        try:
            disc_str = self.table_prices.item(row, 4).text().replace("%", "").replace(" ", "").strip()
            disc_val = max(0.0, float(disc_str)) if disc_str else 0.0
            disc_rate = disc_val / 100.0 if disc_val > 1.0 else disc_val
        except ValueError:
            disc_rate = 0.0

        try:
            tva_str = self.table_prices.item(row, 7).text().replace("%", "").replace(" ", "").strip()
            tva_val = max(0.0, float(tva_str)) if tva_str else 0.0
        except ValueError:
            tva_val = 0.0

        disc_amt = p_ht * disc_rate
        p_after = p_ht - disc_amt
        p_ttc = p_after * (1.0 + (tva_val / 100.0))

        self.table_prices.blockSignals(True)
        # تحديث الخلايا المحسوبة
        c_da = self.table_prices.item(row, 5)
        if c_da:
            c_da.setText(f"{disc_amt:,.2f}")
        c_pa = self.table_prices.item(row, 6)
        if c_pa:
            c_pa.setText(f"{p_after:,.2f}")
        c_ttc = self.table_prices.item(row, 8)
        if c_ttc:
            c_ttc.setText(f"{p_ttc:,.2f}")

        # تظليل السطر المعدل
        for c in range(self.table_prices.columnCount()):
            cell = self.table_prices.item(row, c)
            if cell:
                cell.setBackground(QColor(16, 185, 129, 45))
        self.table_prices.blockSignals(False)

        # تسجيل التعديل
        self.modified_articles[art_id] = {
            "id": art_id,
            "price_ht": p_ht,
            "discount_rate": disc_rate,
            "discount_amount": disc_amt,
            "price_after_discount": p_after,
            "tva_rate": tva_val,
            "price_ttc": p_ttc
        }

        # تحديث نص زر الحفظ
        n = len(self.modified_articles)
        self.btn_save_changes.setText(f"💾 حفظ التغييرات ({n})")
        self.btn_save_changes.setStyleSheet("background-color: #059669; color: white; font-weight: bold; font-size: 13px; padding: 6px 20px; border-radius: 6px; border: 2px solid #34D399;")

    def save_all_price_changes(self):
        """حفظ كافة التغييرات السعرية المدخلة وتحديث المنظومة بالقيم الجديدة"""
        if not self.modified_articles:
            QMessageBox.information(
                self, "تنبيه",
                "لم تقم بتعديل أي أسعار في الجدول بعد.\nيمكنك تعديل خانات (سعر بدون رسوم، نسبة التخفيض، ض ق م) مباشرة في الجدول ثم النقر على حفظ التغييرات."
            )
            return

        r_id = self.current_residence_id
        res_name = self.current_residence_name or f"الإقامة {r_id}"

        reply = QMessageBox.question(
            self, "تأكيد الحفظ",
            f"هل تريد حفظ التعديلات السعرية لـ {len(self.modified_articles)} مادة لـ:\n{res_name}\n\nسيتم تحديث كافة الواجهات وورقة الاستهلاك بالقيم والأسعار الجديدة فوراً.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            for art_id, data in self.modified_articles.items():
                self.stock_svc.save_article(data, residence_id=r_id, apply_to_all_residences=False, auto_recalculate=False)

            # إعادة حساب وتحديث كافة تكاليف ورقة الاستهلاك ومصاريف الإطعام
            self.stock_svc.recalculate_residence_costs_from_prices(r_id)

            saved_count = len(self.modified_articles)
            self.modified_articles.clear()
            self.btn_save_changes.setText("💾 حفظ التغييرات")
            self.btn_save_changes.setStyleSheet("background-color: #059669; color: white; font-weight: bold; font-size: 13px; padding: 6px 20px; border-radius: 6px;")

            # مزامنة الأسعار وتكاليف الإقامة المحدثة مع السحابة فوراً في خيط مستقل
            try:
                import threading
                def _async_cloud_push(target_rid):
                    try:
                        self.sync_svc.push_residence_prices(target_rid)
                        self.sync_svc.push_full_residence_data(target_rid)
                    except Exception as ex_sync:
                        print(f"Async cloud push after save_all_price_changes notice: {ex_sync}")
                threading.Thread(target=_async_cloud_push, args=(r_id,), daemon=True).start()
            except Exception:
                pass

            self.load_articles()
            self.article_saved.emit()

            QMessageBox.information(
                self, "نجاح الحفظ",
                f"تم بنجاح حفظ أسعار {saved_count} مادة لـ {res_name}!\nتم تحديث ورقة الاستهلاك والوصولات وكافة الواجهات بالقيم الجديدة، وحفظ الأسعار في السحابة أيضاً."
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", f"حدث خطأ أثناء حفظ الأسعار: {e}")

    def render_stock_page(self):
        start_idx, end_idx = self.pagination_stock.get_slice_range()
        page_items = self.all_articles[start_idx:end_idx]

        self.table_stock.setRowCount(len(page_items))
        for r, art in enumerate(page_items):
            c_code = QTableWidgetItem(str(art.get("code") or "-"))
            c_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_stock.setItem(r, 0, c_code)

            c_name = QTableWidgetItem(art["name"])
            c_name.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_stock.setItem(r, 1, c_name)

            c_cat = QTableWidgetItem(art.get("category_name") or "-")
            c_cat.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_stock.setItem(r, 2, c_cat)

            c_unit = QTableWidgetItem(art.get("unit") or "كلغ")
            c_unit.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_stock.setItem(r, 3, c_unit)

            c_price = QTableWidgetItem(f"{art['price_ttc']:,.2f}")
            c_price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_stock.setItem(r, 4, c_price)

            curr = art["current_stock"]
            safe = art["safety_stock"]

            c_cur = QTableWidgetItem(f"{curr:,.2f}")
            c_cur.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if curr <= safe:
                c_cur.setForeground(QColor("#EF4444"))
                f = c_cur.font()
                f.setBold(True)
                c_cur.setFont(f)
            self.table_stock.setItem(r, 5, c_cur)

            c_safe = QTableWidgetItem(f"{safe:,.2f}")
            c_safe.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_stock.setItem(r, 6, c_safe)

            c_init = QTableWidgetItem(f"{art['initial_stock']:,.2f}")
            c_init.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_stock.setItem(r, 7, c_init)

            if curr <= 0:
                status_txt = "نفد المخزون ❌"
                status_col = QColor("#EF4444")
            elif curr <= safe:
                status_txt = "تنبيه أمان ⚠️"
                status_col = QColor("#F59E0B")
            else:
                status_txt = "متوفر آمن ✔"
                status_col = QColor("#10B981")

            c_st = QTableWidgetItem(status_txt)
            c_st.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            c_st.setForeground(status_col)
            font = c_st.font()
            font.setBold(True)
            c_st.setFont(font)
            self.table_stock.setItem(r, 8, c_st)

    def refresh_theme(self):
        """إعادة رسم الجداول عند تبديل المظهر لضمان وضوح الألوان والتباين"""
        self.render_prices_page()
        self.render_stock_page()

    def get_selected_article(self):
        curr_tab = self.tabs.currentIndex()
        tbl = self.table_prices if curr_tab == 0 else self.table_stock
        pag = self.pagination_prices if curr_tab == 0 else self.pagination_stock

        row = tbl.currentRow()
        if row < 0:
            return None

        start_idx, _ = pag.get_slice_range()
        real_idx = start_idx + row
        if 0 <= real_idx < len(self.all_articles):
            return self.all_articles[real_idx]
        return None

    def open_add_dialog(self):
        dlg = ArticleDialog(
            self.stock_svc,
            residence_id=self.current_residence_id,
            residence_name=self.current_residence_name,
            parent=self
        )
        if dlg.exec():
            self.load_articles()
            self.article_saved.emit()

    def delete_selected_article(self):
        """حذف أو إخفاء المادة المحددة من جدول الأسعار ودليل المواد"""
        art = self.get_selected_article()
        if not art:
            QMessageBox.warning(self, "تنبيه", "يرجى تحديد مادة غذائية من الجدول أولاً لحذفها!")
            return

        art_id = art["id"]
        art_name = art["name"]
        art_code = str(art.get("code") or "-")

        reply = QMessageBox.question(
            self, "تأكيد حذف المادة",
            f"هل أنت متأكد من حذف المادة الغذائية التالية؟\n\n📌 {art_name} (رقم الحصة: {art_code})\n\n"
            "سيتم حذف المادة أو إخفاؤها بأمان ولن تظهر في قائمة الأسعار أو وصولات الإدخال والإخراج.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            res = self.stock_svc.delete_article(art_id, residence_id=self.current_residence_id)
            if res.get("success"):
                self.load_articles()
                self.article_saved.emit()
                QMessageBox.information(self, "نجاح الحذف", res.get("message", "تم حذف المادة بنجاح."))
            else:
                QMessageBox.warning(self, "تعذر الحذف", res.get("error", "حدث خطأ أثناء محاولة الحذف."))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف:\n{e}")

    def open_edit_dialog(self):
        art = self.get_selected_article()
        if not art:
            QMessageBox.warning(self, "تنبيه", "يرجى تحديد مادة غذائية من الجدول أولاً!")
            return

        dlg = ArticleDialog(
            self.stock_svc,
            article_data=art,
            residence_id=self.current_residence_id,
            residence_name=self.current_residence_name,
            parent=self
        )
        if dlg.exec():
            self.load_articles()
            self.article_saved.emit()

    def pull_updated_prices(self):
        """سحب وتحديث الأسعار المعتمدة من الخادم/المديرية للإقامة المحددة"""
        r_id = self.current_residence_id
        res_name = self.current_residence_name or f"الإقامة {r_id}"

        prog = QProgressDialog(f"جاري سحب الأسعار المحدثة لـ {res_name} من السيرفر...", "إلغاء", 0, 0, self)
        prog.setWindowTitle("سحب وتحديث الأسعار")
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.show()
        QApplication.processEvents()

        result = self.sync_svc.pull_residence_prices(r_id)
        prog.close()

        if result.get("success"):
            self.load_articles()
            self.article_saved.emit()
            QMessageBox.information(
                self, "نجاح سحب الأسعار",
                f"تم بنجاح سحب وتحديث الأسعار المعتمدة لـ:\n{res_name}\nعدد المواد المحدثة: {result.get('count', 0)}"
            )
        else:
            QMessageBox.warning(
                self, "فشل السحب",
                f"تعذر سحب الأسعار من السيرفر:\n{result.get('error', 'خطأ غير معروف')}"
            )

    def print_price_list(self):
        from core.print_helper import print_html_report
        html = self.report_gen.generate_price_list_html(residence_id=self.current_residence_id)
        print_html_report(self, html, is_landscape=False, job_title="دليل المواد والأسعار المعتمدة", direct_print=False)

    def import_price_list_excel(self):
        """استيراد وتطبيق الأسعار مباشرة من ملف Excel (مثل prix.xls) وتحديث الحسابات والواجهات فوراً"""
        default_dir = r"C:\Users\pc\Desktop\الإقامات\العبيدي"
        if not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~/Desktop")

        filename, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف Excel لقائمة الأسعار",
            default_dir,
            "ملفات إكسل (*.xls *.xlsx)"
        )
        if not filename:
            return

        try:
            import xlrd
            wb = xlrd.open_workbook(filename)
            sheet_name = 'الأسعار' if 'الأسعار' in wb.sheet_names() else wb.sheet_names()[0]
            sheet = wb.sheet_by_name(sheet_name)
            is_xlrd = True
        except Exception:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(filename, data_only=True)
                sheet_name = 'الأسعار' if 'الأسعار' in wb.sheetnames else wb.sheetnames[0]
                sheet = wb[sheet_name]
                is_xlrd = False
            except Exception as ex_open:
                QMessageBox.critical(self, "خطأ في قراءة الملف", f"تعذر فتح ملف Excel:\n{ex_open}")
                return

        r_id = self.current_residence_id
        res_name = self.current_residence_name or f"الإقامة {r_id}"

        reply = QMessageBox.question(
            self, "تأكيد استيراد الأسعار",
            f"هل تريد استيراد وتطبيق الأسعار من ورقة '{sheet_name}' لـ:\n🏢 {res_name}\n\nسيتم تحديث كافة الأسعار والواجهات والحسابات فوراً.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        updated_count = 0
        try:
            with self.stock_svc.db.get_connection() as conn:
                total_rows = sheet.nrows if is_xlrd else sheet.max_row
                for r in range(3, total_rows):
                    if is_xlrd:
                        name = str(sheet.cell_value(r, 1)).strip()
                        if not name:
                            continue
                        def _get_val(c):
                            try:
                                return float(sheet.cell_value(r, c))
                            except Exception:
                                return 0.0
                        p_ht = _get_val(3)
                        disc_rate = _get_val(4)
                        tva = _get_val(7)
                        p_ttc = _get_val(8)
                    else:
                        row_cells = list(sheet.iter_rows(min_row=r+1, max_row=r+1, values_only=True))[0]
                        name = str(row_cells[1] or "").strip()
                        if not name:
                            continue
                        def _get_val_open(idx):
                            try:
                                return float(row_cells[idx]) if row_cells[idx] is not None else 0.0
                            except Exception:
                                return 0.0
                        p_ht = _get_val_open(3)
                        disc_rate = _get_val_open(4)
                        tva = _get_val_open(7)
                        p_ttc = _get_val_open(8)

                    disc_amt = round(p_ht * disc_rate, 4)
                    p_after = round(p_ht - disc_amt, 4)
                    if p_ttc <= 0:
                        p_ttc = round(p_after * (1.0 + tva), 4)

                    art_id = r - 2
                    cur_find = conn.execute("SELECT id FROM articles WHERE id = ? OR name = ?", (art_id, name)).fetchone()
                    if cur_find:
                        real_id = cur_find[0]
                        conn.execute("""
                            INSERT INTO residence_articles (
                                residence_id, article_id, initial_stock, current_stock, safety_stock, current_pmp,
                                price_ht, discount_rate, discount_amount, price_after_discount, tva_rate, price_ttc
                            ) VALUES (?, ?, 0.0, 0.0, 10.0, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(residence_id, article_id) DO UPDATE SET
                                price_ht = excluded.price_ht,
                                discount_rate = excluded.discount_rate,
                                discount_amount = excluded.discount_amount,
                                price_after_discount = excluded.price_after_discount,
                                tva_rate = excluded.tva_rate,
                                price_ttc = excluded.price_ttc
                        """, (r_id, real_id, p_ttc, p_ht, disc_rate, disc_amt, p_after, tva, p_ttc))

                        conn.execute("""
                            UPDATE articles SET
                                price_ht = ?, discount_rate = ?, discount_amount = ?,
                                price_after_discount = ?, tva_rate = ?, price_ttc = ?, current_pmp = ?
                            WHERE id = ?
                        """, (p_ht, disc_rate, disc_amt, p_after, tva, p_ttc, p_ttc, real_id))
                        updated_count += 1
                conn.commit()

            self.stock_svc.recalculate_residence_costs_from_prices(r_id)
            from core.cache_service import CacheService
            CacheService.invalidate_all()

            try:
                import threading
                def _sync_import(target_rid):
                    try:
                        self.sync_svc.push_residence_prices(target_rid)
                        self.sync_svc.push_full_residence_data(target_rid)
                    except Exception:
                        pass
                threading.Thread(target=_sync_import, args=(r_id,), daemon=True).start()
            except Exception:
                pass

            self.load_articles()
            self.article_saved.emit()

            QMessageBox.information(
                self, "نجاح الاستيراد",
                f"تم بنجاح استيراد وتطبيق أسعار {updated_count} مادة لـ {res_name} من ملف Excel!\nتم تحديث ورقة الاستهلاك والوصولات والحسابات فوراً."
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الاستيراد", f"حدث خطأ أثناء استيراد الأسعار:\n{e}")

    def export_price_list_excel(self):
        res_suffix = f"_{self.current_residence_name}" if self.current_residence_name else ""
        filename, _ = QFileDialog.getSaveFileName(
            self, "حفظ قائمة الأسعار بصيغة Excel",
            f"قائمة_الأسعار_2026{res_suffix}.xlsx",
            "ملفات إكسل (*.xlsx)"
        )
        if filename:
            try:
                self.report_gen.export_price_list_to_excel(filename, residence_id=self.current_residence_id)
                QMessageBox.information(self, "نجاح التصدير", f"تم تصدير قائمة الأسعار بنجاح إلى:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ في التصدير", f"حدث خطأ أثناء تصدير الملف:\n{e}")
