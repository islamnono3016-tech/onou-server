from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QMessageBox,
    QTabWidget, QScrollArea, QDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QCursor
import datetime
from typing import Optional, Dict, Any, List
from core.stock_service import StockService
from ui.common_filters import attach_smooth_scroll


class VoucherDetailsDialog(QDialog):
    """نافذة معاينة وتتبع بنود وصل الدخول (مخصصة للرقابة والمتابعة من طرف المديرية)"""

    def __init__(self, voucher_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"معاينة تفاصيل وصل الدخول: {voucher_data.get('voucher_number', '')}")
        self.setMinimumSize(780, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # بطاقة رأس الوصل
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 10px;")
        hc_layout = QVBoxLayout(header_card)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel(f"<b>رقم الوصل:</b> {voucher_data.get('voucher_number', '-')}"))
        r1.addWidget(QLabel(f"<b>التاريخ:</b> {voucher_data.get('date', '-')}"))
        r1.addWidget(QLabel(f"<b>الإقامة:</b> {voucher_data.get('residence_name', 'الإقامة الجامعية')}"))
        hc_layout.addLayout(r1)

        r2 = QHBoxLayout()
        v_type_str = "توريد رسمي من مورد" if voucher_data.get("voucher_type") == "SUPPLIER" else "إستعارة من إقامة أخرى"
        r2.addWidget(QLabel(f"<b>نوع الحركة:</b> {v_type_str}"))
        src_name = voucher_data.get("supplier_name") if voucher_data.get("voucher_type") == "SUPPLIER" else (voucher_data.get("source_residence") or "-")
        r2.addWidget(QLabel(f"<b>المورد / المصدر:</b> {src_name}"))
        r2.addWidget(QLabel(f"<b>رقم وصل التسليم (BL):</b> {voucher_data.get('delivery_note_ref') or '-'}"))
        hc_layout.addLayout(r2)

        layout.addWidget(header_card)

        # جدول البنود
        lbl_tbl = QLabel("<b>قائمة المواد المستلمة بالوصل (للاطلاع والرقابة):</b>")
        layout.addWidget(lbl_tbl)

        tbl = QTableWidget()
        tbl.setColumnCount(6)
        tbl.setHorizontalHeaderLabels([
            "رمز المادة", "اسم المادة الغذائية", "الوحدة", "الكمية الموردة", "السعر الفردي TTC", "المبلغ الإجمالي"
        ])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        attach_smooth_scroll(tbl)

        items = voucher_data.get("items", [])
        tbl.setRowCount(len(items))
        tot_sum = 0.0
        for row, it in enumerate(items):
            tbl.setItem(row, 0, QTableWidgetItem(str(it.get("article_code") or "-")))
            tbl.setItem(row, 1, QTableWidgetItem(it.get("article_name") or "-"))
            tbl.setItem(row, 2, QTableWidgetItem(it.get("unit") or "-"))

            q_item = QTableWidgetItem(f"{float(it.get('quantity', 0.0)):g}")
            q_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tbl.setItem(row, 3, q_item)

            p_item = QTableWidgetItem(f"{float(it.get('unit_price_ttc', 0.0)):,.2f} دج")
            p_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tbl.setItem(row, 4, p_item)

            t_val = float(it.get("total_price", 0.0))
            tot_sum += t_val
            tot_item = QTableWidgetItem(f"{t_val:,.2f} دج")
            tot_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tbl.setItem(row, 5, tot_item)

        layout.addWidget(tbl)

        # تذييل النافذة
        footer_layout = QHBoxLayout()
        lbl_tot = QLabel(f"<b>المبلغ الإجمالي للوصل:</b> {tot_sum:,.2f} دج")
        lbl_tot.setStyleSheet("font-size: 15px; font-weight: bold; color: #0D9488;")
        footer_layout.addWidget(lbl_tot)
        footer_layout.addStretch()

        btn_close = QPushButton("إغلاق المعاينة ✖")
        btn_close.setFixedHeight(34)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.clicked.connect(self.accept)
        footer_layout.addWidget(btn_close)

        layout.addLayout(footer_layout)


class EntryVoucherWidget(QWidget):
    """شاشة وصولات الاستلام والتوريد والاستعارة (Bons d'Entrée) - المدخولات"""

    def __init__(self, stock_service: StockService, parent=None, is_directorate: bool = False, current_user: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.stock_svc = stock_service
        self.is_directorate = is_directorate
        self.current_user = current_user or {}
        self.residence_id = stock_service.residence_id
        self.voucher_items: List[Dict[str, Any]] = []

        self.init_ui()
        self.load_suppliers()
        self.load_articles_list()
        self.load_vouchers_history()
        self.apply_directorate_restrictions()

    def set_residence(self, residence_id: int):
        """تحديث الإقامة النشطة لسجل الوصولات وتتبع المدخولات"""
        self.residence_id = residence_id
        self.load_vouchers_history()

    def set_directorate_mode(self, is_directorate: bool, current_user: Optional[Dict[str, Any]] = None):
        self.is_directorate = is_directorate
        if current_user:
            self.current_user = current_user
        self.apply_directorate_restrictions()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # شريط تنبيه خاص بوضع المديرية العامة (الإطلاع والتتبع فقط)
        self.lbl_directorate_banner = QLabel(
            "👁️ وضع الرقابة والتتبع (المديرية): يقتصر دور مديرية الخدمات الجامعية على الإطلاع وتتبع سجل المدخولات لجميع الإقامات دون إمكانية تعديل القيم أو إضافة وصولات جديدة (خاص بالإقامات الجامعية)."
        )
        self.lbl_directorate_banner.setStyleSheet("""
            background-color: rgba(2, 132, 199, 0.12);
            border: 1px solid #0284C7;
            border-radius: 6px;
            padding: 9px 14px;
            color: #0369A1;
            font-size: 12px;
            font-weight: bold;
        """)
        self.lbl_directorate_banner.setWordWrap(True)
        self.lbl_directorate_banner.setVisible(self.is_directorate)
        layout.addWidget(self.lbl_directorate_banner)

        self.tabs = QTabWidget()

        # تبويب 1: تسجيل وصل استلام جديد
        tab_new_scroll = QScrollArea()
        tab_new_scroll.setWidgetResizable(True)
        tab_new_scroll.setFrameShape(QFrame.Shape.NoFrame)
        tab_new = QWidget()
        self.init_new_voucher_tab(tab_new)
        tab_new_scroll.setWidget(tab_new)
        attach_smooth_scroll(tab_new_scroll)
        self.tabs.addTab(tab_new_scroll, "تسجيل وصل استلام جديد +")

        # تبويب 2: سجل وصولات الاستلام السابقة
        tab_history = QWidget()
        self.init_history_tab(tab_history)
        self.tabs.addTab(tab_history, "سجل وصولات الاستلام السابقة 📜")

        layout.addWidget(self.tabs)

    def init_new_voucher_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setSpacing(14)

        # 1. رأس الوصل
        header_panel = QFrame()
        header_panel.setProperty("class", "content-panel")
        h_layout = QHBoxLayout(header_panel)
        h_layout.setSpacing(15)

        self.dt_entry = QDateEdit(QDate.currentDate())
        self.dt_entry.setCalendarPopup(True)
        self.dt_entry.setDisplayFormat("yyyy-MM-dd")

        self.txt_num = QLineEdit()
        self.txt_num.setPlaceholderText("رقم الوصل (مثال: BE-2026-001)")

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("توريد من مورد (سند تسليم رسمي)", "SUPPLIER")
        self.cmb_type.addItem("إستعارة من إقامة جامعية أخرى", "LOAN_IN")
        self.cmb_type.currentIndexChanged.connect(self.on_type_changed)

        self.cmb_supplier = QComboBox()
        self.txt_source = QLineEdit()
        self.txt_source.setPlaceholderText("اسم الإقامة المعيرة")
        self.txt_source.setVisible(False)

        self.txt_bl_ref = QLineEdit()
        self.txt_bl_ref.setPlaceholderText("رقم وصل التسليم (Bon de livraison)")

        h_layout.addWidget(QLabel("تاريخ الاستلام:"))
        h_layout.addWidget(self.dt_entry)
        h_layout.addWidget(QLabel("نوع الحركة:"))
        h_layout.addWidget(self.cmb_type)
        h_layout.addWidget(QLabel("المورد / المصدر:"))
        h_layout.addWidget(self.cmb_supplier)
        h_layout.addWidget(self.txt_source)
        h_layout.addWidget(QLabel("رقم BL:"))
        h_layout.addWidget(self.txt_bl_ref)

        layout.addWidget(header_panel)

        # 2. إضافة بند إلى الوصل
        item_panel = QFrame()
        item_panel.setProperty("class", "content-panel")
        i_layout = QHBoxLayout(item_panel)

        self.cmb_articles = QComboBox()
        self.cmb_articles.setEditable(True)
        self.cmb_articles.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cmb_articles.currentIndexChanged.connect(self.on_article_selected)

        self.spn_qty = QDoubleSpinBox()
        self.spn_qty.setRange(0.01, 99999.0)
        self.spn_qty.setValue(1.0)
        self.spn_qty.setDecimals(2)

        self.spn_price = QDoubleSpinBox()
        self.spn_price.setRange(0.0, 999999.0)
        self.spn_price.setDecimals(2)
        self.spn_price.setSuffix(" دج")

        self.btn_add_item = QPushButton("+ إضافة البند للوصل")
        self.btn_add_item.setProperty("class", "btn-primary")
        self.btn_add_item.clicked.connect(self.add_item_to_voucher)

        i_layout.addWidget(QLabel("المادة الغذائية:"))
        i_layout.addWidget(self.cmb_articles, stretch=3)
        i_layout.addWidget(QLabel("الكمية:"))
        i_layout.addWidget(self.spn_qty, stretch=1)
        i_layout.addWidget(QLabel("السعر TTC:"))
        i_layout.addWidget(self.spn_price, stretch=1)
        i_layout.addWidget(self.btn_add_item)

        layout.addWidget(item_panel)

        # 3. جدول بنود الوصل
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(6)
        self.table_items.setMinimumHeight(200)
        self.table_items.setHorizontalHeaderLabels([
            "اسم المادة", "الوحدة", "الكمية الموردة", "السعر الفردي TTC", "المبلغ الإجمالي", "إجراء"
        ])
        self.table_items.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_items.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        attach_smooth_scroll(self.table_items)
        layout.addWidget(self.table_items)

        # 4. تذييل الوصل والإجمالي وأزرار الحفظ
        bottom_box = QHBoxLayout()
        self.lbl_total_voucher = QLabel("الإجمالي العام للوصل: 0.00 دج")
        self.lbl_total_voucher.setStyleSheet("font-size: 16px; font-weight: bold; color: #0D9488;")
        bottom_box.addWidget(self.lbl_total_voucher)
        bottom_box.addStretch()

        self.btn_save = QPushButton("حفظ الوصل وتحديث المخزون الحي ✔")
        self.btn_save.setProperty("class", "btn-success")
        self.btn_save.setStyleSheet("padding: 10px 24px; font-size: 14px;")
        self.btn_save.clicked.connect(self.save_voucher)
        bottom_box.addWidget(self.btn_save)

        layout.addLayout(bottom_box)

    def init_history_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(8)
        self.table_history.setHorizontalHeaderLabels([
            "رقم الوصل", "التاريخ", "الإقامة الجامعية", "النوع", "المورد / المصدر", "رقم BL", "المبلغ الإجمالي", "معاينة البنود 🔍"
        ])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_history.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        attach_smooth_scroll(self.table_history)
        layout.addWidget(self.table_history)

        from ui.widgets.pagination_bar import PaginationBar
        self.pagination_history = PaginationBar(initial_page_size=15, page_size_options=(10, 15, 25, 50))
        self.pagination_history.page_changed.connect(self.render_history_page)
        self.pagination_history.page_size_changed.connect(self.render_history_page)
        self.pagination_history.attach_to_table(self.table_history)
        layout.addWidget(self.pagination_history)

    def apply_directorate_restrictions(self):
        """تطبيق قواعد الرقابة: منع المديرية من التعديل وحصرها في الإطلاع والتتبع فقط"""
        if self.is_directorate:
            self.lbl_directorate_banner.setVisible(True)
            self.btn_save.setEnabled(False)
            self.btn_save.setText("🔒 تسجيل وحفظ الوصولات محصور بالإقامات (للمديرية الإطلاع والتتبع فقط)")
            self.btn_save.setStyleSheet("background-color: #64748B; color: #F1F5F9; padding: 10px 24px; font-size: 13px; border-radius: 6px;")
            self.btn_add_item.setEnabled(False)
            self.dt_entry.setEnabled(False)
            self.txt_num.setReadOnly(True)
            self.cmb_type.setEnabled(False)
            self.cmb_supplier.setEnabled(False)
            self.txt_source.setReadOnly(True)
            self.txt_bl_ref.setReadOnly(True)
            self.cmb_articles.setEnabled(False)
            self.spn_qty.setEnabled(False)
            self.spn_price.setEnabled(False)
            self.tabs.setCurrentIndex(1)
            self.tabs.setTabText(0, "تسجيل وصل استلام جديد (محظور للمديرية 🔒)")
            self.tabs.setTabText(1, "سجل وصولات الاستلام وتتبع الإقامات 📜👁️")
        else:
            self.lbl_directorate_banner.setVisible(False)
            self.btn_save.setEnabled(True)
            self.btn_save.setText("حفظ الوصل وتحديث المخزون الحي ✔")
            self.btn_save.setStyleSheet("padding: 10px 24px; font-size: 14px;")
            self.btn_add_item.setEnabled(True)
            self.dt_entry.setEnabled(True)
            self.txt_num.setReadOnly(False)
            self.cmb_type.setEnabled(True)
            self.cmb_supplier.setEnabled(True)
            self.txt_source.setReadOnly(False)
            self.txt_bl_ref.setReadOnly(False)
            self.cmb_articles.setEnabled(True)
            self.spn_qty.setEnabled(True)
            self.spn_price.setEnabled(True)
            self.tabs.setTabText(0, "تسجيل وصل استلام جديد +")
            self.tabs.setTabText(1, "سجل وصولات الاستلام السابقة 📜")

    def on_type_changed(self):
        is_supp = self.cmb_type.currentData() == "SUPPLIER"
        self.cmb_supplier.setVisible(is_supp)
        self.txt_source.setVisible(not is_supp)

    def load_suppliers(self):
        self.cmb_supplier.clear()
        with self.stock_svc.db.get_connection() as conn:
            cur = conn.execute("SELECT id, name FROM suppliers ORDER BY id")
            for r in cur.fetchall():
                self.cmb_supplier.addItem(r["name"], r["id"])

    def load_articles_list(self):
        self.cmb_articles.clear()
        articles = self.stock_svc.get_articles(residence_id=self.residence_id)
        self.articles_dict = {}
        for a in articles:
            self.cmb_articles.addItem(a["name"], a["id"])
            self.articles_dict[a["id"]] = a

    def on_article_selected(self):
        art_id = self.cmb_articles.currentData()
        if art_id in self.articles_dict:
            self.spn_price.setValue(self.articles_dict[art_id]["price_ttc"])

    def add_item_to_voucher(self):
        if self.is_directorate:
            return
        art_id = self.cmb_articles.currentData()
        if not art_id or art_id not in self.articles_dict:
            return
        art = self.articles_dict[art_id]
        qty = self.spn_qty.value()
        price = self.spn_price.value()

        # تحقق إن كانت المادة موجودة مسبقاً في القائمة
        for it in self.voucher_items:
            if it["article_id"] == art_id:
                it["quantity"] += qty
                it["total_price"] = it["quantity"] * price
                self.refresh_items_table()
                return

        self.voucher_items.append({
            "article_id": art_id,
            "name": art["name"],
            "unit": art["unit"],
            "quantity": qty,
            "unit_price_ttc": price,
            "total_price": qty * price
        })
        self.refresh_items_table()

    def refresh_items_table(self):
        self.table_items.setRowCount(len(self.voucher_items))
        total_sum = 0.0
        for r, it in enumerate(self.voucher_items):
            self.table_items.setItem(r, 0, QTableWidgetItem(it["name"]))
            self.table_items.setItem(r, 1, QTableWidgetItem(it["unit"]))
            self.table_items.setItem(r, 2, QTableWidgetItem(f"{it['quantity']:g}"))
            self.table_items.setItem(r, 3, QTableWidgetItem(f"{it['unit_price_ttc']:,.2f}"))
            self.table_items.setItem(r, 4, QTableWidgetItem(f"{it['total_price']:,.2f} دج"))

            if not self.is_directorate:
                btn_del = QPushButton("حذف ✖")
                btn_del.setProperty("class", "btn-danger")
                btn_del.clicked.connect(lambda _, idx=r: self.remove_item(idx))
                self.table_items.setCellWidget(r, 5, btn_del)
            else:
                lbl_lock = QLabel("محمي 🔒")
                lbl_lock.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_lock.setStyleSheet("color: #94A3B8; font-size: 11px;")
                self.table_items.setCellWidget(r, 5, lbl_lock)

            total_sum += it["total_price"]

        self.lbl_total_voucher.setText(f"الإجمالي العام للوصل: {total_sum:,.2f} دج")

    def remove_item(self, idx):
        if self.is_directorate:
            return
        if 0 <= idx < len(self.voucher_items):
            self.voucher_items.pop(idx)
            self.refresh_items_table()

    def has_unsaved_changes(self) -> bool:
        if self.is_directorate:
            return False
        return bool(self.voucher_items)

    def save_changes(self) -> bool:
        return self.save_voucher()

    def discard_changes(self):
        self.voucher_items.clear()
        self.refresh_items_table()
        self.txt_num.clear()
        self.txt_bl_ref.clear()

    def save_voucher(self) -> bool:
        if self.is_directorate:
            QMessageBox.warning(
                self, "صلاحية مقيدة ⛔",
                "لا تملك مديرية الخدمات الجامعية صلاحية إضافة أو تعديل المدخولات.\n\n"
                "• هذه الصلاحية مسندة حصراً لمسؤولي مخازن الإقامات الجامعية.\n"
                "• يقتصر دور المديرية على الإطلاع والتتبع والرقابة الميدانية فقط دون التعديل على القيم."
            )
            return False

        if not self.voucher_items:
            QMessageBox.warning(self, "تنبيه", "يرجى إضافة مادة واحدة على الأقل إلى الوصل!")
            return False

        date_str = self.dt_entry.date().toString("yyyy-MM-dd")
        v_type = self.cmb_type.currentData()
        v_num = self.txt_num.text().strip() or f"BE-{date_str}-{datetime.datetime.now().strftime('%H%M%S')}"

        voucher_data = {
            "voucher_number": v_num,
            "date": date_str,
            "voucher_type": v_type,
            "supplier_id": self.cmb_supplier.currentData() if v_type == "SUPPLIER" else None,
            "source_residence": self.txt_source.text().strip() if v_type == "LOAN_IN" else "",
            "delivery_note_ref": self.txt_bl_ref.text().strip(),
            "residence_id": self.residence_id
        }

        try:
            self.stock_svc.create_entry_voucher(voucher_data, self.voucher_items)
            QMessageBox.information(self, "نجاح", f"تم تسجيل وصل الاستلام رقم ({v_num}) وتحديث المخزون بنجاح!")
            self.voucher_items.clear()
            self.refresh_items_table()
            self.txt_num.clear()
            self.txt_bl_ref.clear()
            self.load_vouchers_history()
            return True
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ الوصل: {e}")
            return False

    def load_vouchers(self):
        """توافقية الاستدعاء لتحميل سجل وصولات الدخول"""
        self.load_vouchers_history()

    def load_vouchers_history(self):
        with self.stock_svc.db.get_connection() as conn:
            r_id = getattr(self, "residence_id", None) or self.stock_svc.residence_id
            if r_id:
                cur = conn.execute("""
                    SELECT ev.*, s.name as supplier_name, r.name as residence_name
                    FROM entry_vouchers ev
                    LEFT JOIN suppliers s ON ev.supplier_id = s.id
                    LEFT JOIN residences r ON ev.residence_id = r.id
                    WHERE ev.residence_id = ?
                    ORDER BY ev.date DESC, ev.id DESC
                """, (r_id,))
            else:
                cur = conn.execute("""
                    SELECT ev.*, s.name as supplier_name, r.name as residence_name
                    FROM entry_vouchers ev
                    LEFT JOIN suppliers s ON ev.supplier_id = s.id
                    LEFT JOIN residences r ON ev.residence_id = r.id
                    ORDER BY ev.date DESC, ev.id DESC
                """)
            # get_connection() now returns plain dicts via _dict_row_factory
            self.all_history_vouchers = cur.fetchall()

        self.pagination_history.set_total_items(len(self.all_history_vouchers), reset_page=True)
        self.render_history_page()

    def render_history_page(self):
        start_idx, end_idx = self.pagination_history.get_slice_range()
        page_rows = self.all_history_vouchers[start_idx:end_idx]

        self.table_history.setRowCount(len(page_rows))
        for r, v in enumerate(page_rows):
            # v is a plain dict from _dict_row_factory — supports .get() safely
            self.table_history.setItem(r, 0, QTableWidgetItem(str(v.get("voucher_number", ""))))
            self.table_history.setItem(r, 1, QTableWidgetItem(str(v.get("date", ""))))
            res_str = v.get("residence_name") or f"إقامة رقم {v.get('residence_id', 1)}"
            self.table_history.setItem(r, 2, QTableWidgetItem(res_str))
            type_str = "توريد مورد" if v.get("voucher_type") == "SUPPLIER" else "إستعارة"
            self.table_history.setItem(r, 3, QTableWidgetItem(type_str))
            src_str = v.get("supplier_name") if v.get("voucher_type") == "SUPPLIER" else (v.get("source_residence") or "-")
            self.table_history.setItem(r, 4, QTableWidgetItem(src_str or "-"))
            self.table_history.setItem(r, 5, QTableWidgetItem(v.get("delivery_note_ref") or "-"))
            self.table_history.setItem(r, 6, QTableWidgetItem(f"{v.get('total_amount', 0):,.2f} دج"))

            btn_view = QPushButton("معاينة البنود 🔍")
            btn_view.setStyleSheet("background-color: #0284C7; color: white; border-radius: 4px; padding: 4px 8px; font-weight: bold;")
            btn_view.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_view.clicked.connect(lambda _, v_id=v.get("id"): self.show_voucher_details(v_id))
            self.table_history.setCellWidget(r, 7, btn_view)

    def show_voucher_details(self, voucher_id: int):
        v_data = self.stock_svc.get_entry_voucher_details(voucher_id)
        if not v_data:
            QMessageBox.warning(self, "تنبيه", "تعذر جلب تفاصيل هذا الوصل!")
            return
        dlg = VoucherDetailsDialog(v_data, parent=self)
        dlg.exec()
