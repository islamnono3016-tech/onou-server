from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QMessageBox,
    QTabWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QDate
import datetime
from core.stock_service import StockService, InsufficientStockError
from ui.common_filters import attach_smooth_scroll

class ExitVoucherWidget(QWidget):
    """شاشة وصولات الإخراج والاستهلاك اليومي للمطبخ (Bons de Sortie)"""

    def __init__(self, stock_service: StockService, parent=None, is_directorate: bool = False, current_user: dict = None):
        super().__init__(parent)
        self.stock_svc = stock_service
        self.is_directorate = is_directorate
        self.current_user = current_user or {}
        self.exit_items = []
        self.init_ui()
        self.load_articles_list()
        self.load_history()
        self.apply_directorate_restrictions()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # شريط تنبيه خاص بوضع المديرية العامة
        self.lbl_directorate_banner = QLabel(
            "👁️ وضع الرقابة والتتبع (المديرية): يقتصر دور المديرية على متابعة ومعاينة وصولات الإخراج لجميع الإقامات دون إمكانية إنشاء وصولات خروج (خاصة بالإقامات)."
        )
        self.lbl_directorate_banner.setStyleSheet("""
            background-color: rgba(2, 132, 199, 0.12);
            border: 1px solid #0284C7;
            border-radius: 6px;
            padding: 8px 14px;
            color: #0369A1;
            font-size: 12px;
            font-weight: bold;
        """)
        self.lbl_directorate_banner.setWordWrap(True)
        self.lbl_directorate_banner.setVisible(self.is_directorate)
        layout.addWidget(self.lbl_directorate_banner)

        self.tabs = QTabWidget()

        # تبويب 1: وصل استهلاك جديد
        tab_new_scroll = QScrollArea()
        tab_new_scroll.setWidgetResizable(True)
        tab_new_scroll.setFrameShape(QFrame.Shape.NoFrame)
        tab_new = QWidget()
        self.init_new_tab(tab_new)
        tab_new_scroll.setWidget(tab_new)
        attach_smooth_scroll(tab_new_scroll)
        self.tabs.addTab(tab_new_scroll, "تسجيل وصل إخراج واستهلاك مطبخ +")

        # تبويب 2: سجل وصولات الاستهلاك السابقة
        tab_history = QWidget()
        self.init_history_tab(tab_history)
        self.tabs.addTab(tab_history, "سجل وصولات الإخراج السابقة 📜")

        layout.addWidget(self.tabs)

    def init_new_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setSpacing(14)

        # 1. رأس الوصل
        header_panel = QFrame()
        header_panel.setProperty("class", "content-panel")
        h_layout = QHBoxLayout(header_panel)

        self.dt_exit = QDateEdit(QDate.currentDate())
        self.dt_exit.setCalendarPopup(True)
        self.dt_exit.setDisplayFormat("yyyy-MM-dd")

        self.txt_num = QLineEdit()
        self.txt_num.setPlaceholderText("رقم وصل الإخراج (مثال: BS-2026-001)")

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("استهلاك مطبخ الإقامة (فطور، غداء، عشاء)", "KITCHEN")
        self.cmb_type.addItem("إعارة لإقامة جامعية أخرى", "LOAN_OUT")
        self.cmb_type.currentIndexChanged.connect(self.on_type_changed)

        self.txt_dest = QLineEdit()
        self.txt_dest.setPlaceholderText("اسم الإقامة المستعيرة")
        self.txt_dest.setVisible(False)

        h_layout.addWidget(QLabel("تاريخ الاستهلاك:"))
        h_layout.addWidget(self.dt_exit)
        h_layout.addWidget(QLabel("نوع الإخراج:"))
        h_layout.addWidget(self.cmb_type)
        h_layout.addWidget(self.txt_dest)
        h_layout.addWidget(QLabel("رقم الوصل:"))
        h_layout.addWidget(self.txt_num)

        layout.addWidget(header_panel)

        # 2. إضافة مادة وتوزيع الكميات على الوجبات مع فحص المخزون
        item_panel = QFrame()
        item_panel.setProperty("class", "content-panel")
        i_layout = QVBoxLayout(item_panel)

        row1 = QHBoxLayout()
        self.cmb_articles = QComboBox()
        self.cmb_articles.setEditable(True)
        self.cmb_articles.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cmb_articles.currentIndexChanged.connect(self.on_article_selected)

        self.lbl_available_stock = QLabel("المتوفر في المخزن: 0.00")
        self.lbl_available_stock.setStyleSheet("font-size: 13px; font-weight: bold; color: #0284C7;")

        row1.addWidget(QLabel("المادة الغذائية:"))
        row1.addWidget(self.cmb_articles, stretch=3)
        row1.addWidget(self.lbl_available_stock, stretch=2)
        i_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.spn_bf = QDoubleSpinBox()
        self.spn_bf.setRange(0.0, 99999.0); self.spn_bf.setDecimals(2)

        self.spn_lu = QDoubleSpinBox()
        self.spn_lu.setRange(0.0, 99999.0); self.spn_lu.setDecimals(2)

        self.spn_di = QDoubleSpinBox()
        self.spn_di.setRange(0.0, 99999.0); self.spn_di.setDecimals(2)

        self.spn_other = QDoubleSpinBox()
        self.spn_other.setRange(0.0, 99999.0); self.spn_other.setDecimals(2)

        btn_add_item = QPushButton("+ إضافة لجدول الإخراج")
        btn_add_item.setProperty("class", "btn-primary")
        btn_add_item.clicked.connect(self.add_item_to_exit)

        row2.addWidget(QLabel("فطور الصباح:"))
        row2.addWidget(self.spn_bf)
        row2.addWidget(QLabel("الغداء:"))
        row2.addWidget(self.spn_lu)
        row2.addWidget(QLabel("العشاء:"))
        row2.addWidget(self.spn_di)
        row2.addWidget(QLabel("إعارة/أخرى:"))
        row2.addWidget(self.spn_other)
        row2.addWidget(btn_add_item)
        i_layout.addLayout(row2)

        layout.addWidget(item_panel)

        # 3. جدول بنود الإخراج
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(9)
        self.table_items.setMinimumHeight(200)
        self.table_items.setHorizontalHeaderLabels([
            "اسم المادة", "الوحدة", "فطور الصباح", "الغداء", "العشاء", "إعارة", "إجمالي الكمية", "السعر TTC", "التكلفة الإجمالية"
        ])
        self.table_items.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_items.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        attach_smooth_scroll(self.table_items)
        layout.addWidget(self.table_items)

        # 4. التذييل والمجاميع
        bottom_box = QHBoxLayout()
        self.lbl_totals_breakdown = QLabel("فطور: 0.00 دج | غداء: 0.00 دج | عشاء: 0.00 دج | الإجمالي: 0.00 دج")
        self.lbl_totals_breakdown.setProperty("class", "section-title")
        bottom_box.addWidget(self.lbl_totals_breakdown)
        bottom_box.addStretch()

        self.btn_save = QPushButton("حفظ وصل الاستهلاك وخصم المخزون آلياً ✔")
        self.btn_save.setProperty("class", "btn-success")
        self.btn_save.setStyleSheet("padding: 10px 24px; font-size: 14px;")
        self.btn_save.clicked.connect(self.save_exit_voucher)
        bottom_box.addWidget(self.btn_save)

        layout.addLayout(bottom_box)

    def init_history_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(7)
        self.table_history.setHorizontalHeaderLabels([
            "رقم الوصل", "التاريخ", "النوع", "تكلفة الفطور", "تكلفة الغداء", "تكلفة العشاء", "المبلغ الكلي دج"
        ])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        attach_smooth_scroll(self.table_history)
        layout.addWidget(self.table_history)

        from ui.widgets.pagination_bar import PaginationBar
        self.pagination_history = PaginationBar(initial_page_size=15, page_size_options=(10, 15, 25, 50))
        self.pagination_history.page_changed.connect(self.render_history_page)
        self.pagination_history.page_size_changed.connect(self.render_history_page)
        self.pagination_history.attach_to_table(self.table_history)
        layout.addWidget(self.pagination_history)

    def on_type_changed(self):
        is_loan = self.cmb_type.currentData() == "LOAN_OUT"
        self.txt_dest.setVisible(is_loan)

    def load_articles_list(self):
        self.cmb_articles.clear()
        articles = self.stock_svc.get_articles()
        self.articles_dict = {}
        for a in articles:
            self.cmb_articles.addItem(a["name"], a["id"])
            self.articles_dict[a["id"]] = a
        self.on_article_selected()

    def on_article_selected(self):
        art_id = self.cmb_articles.currentData()
        if art_id in self.articles_dict:
            art = self.articles_dict[art_id]
            stk = art["current_stock"]
            color = "#DC2626" if stk <= art["safety_stock"] else "#0284C7"
            self.lbl_available_stock.setText(f"المتوفر في المخزن: {stk:g} {art['unit']}")
            self.lbl_available_stock.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {color};")

    def add_item_to_exit(self):
        art_id = self.cmb_articles.currentData()
        if not art_id or art_id not in self.articles_dict:
            return
        art = self.articles_dict[art_id]

        q_bf = self.spn_bf.value()
        q_lu = self.spn_lu.value()
        q_di = self.spn_di.value()
        q_ot = self.spn_other.value()
        tot_q = q_bf + q_lu + q_di + q_ot

        if tot_q <= 0:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال كمية استهلاك واحدة على الأقل!")
            return

        # فحص كفاية المخزون مع مراعاة ما تم اختياره مسبقاً في نفس الجدول
        already_added = sum(float(it.get("total_qty", 0.0)) for it in self.exit_items if it.get("article_id") == art_id)
        current_avail = float(art.get("current_stock", 0.0) or 0.0)
        remaining_avail = max(0.0, current_avail - already_added)

        if tot_q > (remaining_avail + 1e-6):
            prev_info = f"\n(تمت إضافة {already_added:g} {art.get('unit', '')} سابقاً في هذا الوصل)" if already_added > 0 else ""
            QMessageBox.critical(
                self, "منع المخزون السالب ⛔",
                f"لا يمكن صرف المادة '{art['name']}'!\n\n"
                f"الكمية المطلوبة: {tot_q:g} {art.get('unit', '')}\n"
                f"الرصيد المتبقي المتاح للصرف: {remaining_avail:g} {art.get('unit', '')}{prev_info}"
            )
            return

        price = art["price_ttc"]
        tot_cost = tot_q * price

        self.exit_items.append({
            "article_id": art_id,
            "name": art["name"],
            "unit": art["unit"],
            "qty_breakfast": q_bf,
            "qty_lunch": q_lu,
            "qty_dinner": q_di,
            "qty_other": q_ot,
            "total_qty": tot_q,
            "unit_price_ttc": price,
            "total_cost": tot_cost
        })

        # تصفير الخانات
        self.spn_bf.setValue(0.0)
        self.spn_lu.setValue(0.0)
        self.spn_di.setValue(0.0)
        self.spn_other.setValue(0.0)
        self.refresh_items_table()

    def refresh_items_table(self):
        self.table_items.setRowCount(len(self.exit_items))
        tot_bf_c = 0.0; tot_lu_c = 0.0; tot_di_c = 0.0; grand_tot = 0.0

        for r, it in enumerate(self.exit_items):
            self.table_items.setItem(r, 0, QTableWidgetItem(it["name"]))
            self.table_items.setItem(r, 1, QTableWidgetItem(it["unit"]))
            self.table_items.setItem(r, 2, QTableWidgetItem(f"{it['qty_breakfast']:g}" if it['qty_breakfast'] > 0 else "-"))
            self.table_items.setItem(r, 3, QTableWidgetItem(f"{it['qty_lunch']:g}" if it['qty_lunch'] > 0 else "-"))
            self.table_items.setItem(r, 4, QTableWidgetItem(f"{it['qty_dinner']:g}" if it['qty_dinner'] > 0 else "-"))
            self.table_items.setItem(r, 5, QTableWidgetItem(f"{it['qty_other']:g}" if it['qty_other'] > 0 else "-"))
            self.table_items.setItem(r, 6, QTableWidgetItem(f"{it['total_qty']:g}"))
            self.table_items.setItem(r, 7, QTableWidgetItem(f"{it['unit_price_ttc']:,.2f}"))
            self.table_items.setItem(r, 8, QTableWidgetItem(f"{it['total_cost']:,.2f} دج"))

            tot_bf_c += it["qty_breakfast"] * it["unit_price_ttc"]
            tot_lu_c += it["qty_lunch"] * it["unit_price_ttc"]
            tot_di_c += it["qty_dinner"] * it["unit_price_ttc"]
            grand_tot += it["total_cost"]

        self.lbl_totals_breakdown.setText(
            f"فطور: {tot_bf_c:,.2f} دج | غداء: {tot_lu_c:,.2f} دج | عشاء: {tot_di_c:,.2f} دج | الإجمالي: {grand_tot:,.2f} دج"
        )

    def has_unsaved_changes(self) -> bool:
        """هل توجد بنود مضافة في وصل الإخراج لم يتم حفظها؟"""
        return bool(self.exit_items)

    def save_changes(self) -> bool:
        return self.save_exit_voucher()

    def discard_changes(self):
        """إلغاء وتفريغ البنود غير المحفوظة"""
        self.exit_items.clear()
        self.refresh_items_table()
        self.txt_num.clear()

    def save_exit_voucher(self) -> bool:
        if getattr(self, "is_directorate", False):
            QMessageBox.information(self, "وضع الرقابة والمتابعة", "حساب المديرية مخصص للاطلاع والتتبع الرقابي فقط ولا يمكن إنشاء أو تعديل وصولات الإخراج.")
            return False
        if not self.exit_items:
            QMessageBox.warning(self, "تنبيه", "يرجى إضافة مادة واحدة على الأقل إلى وصل الإخراج!")
            return False

        date_str = self.dt_exit.date().toString("yyyy-MM-dd")
        v_type = self.cmb_type.currentData()
        v_num = self.txt_num.text().strip() or f"BS-{date_str}-{datetime.datetime.now().strftime('%H%M%S')}"

        voucher_data = {
            "voucher_number": v_num,
            "date": date_str,
            "voucher_type": v_type,
            "destination_residence": self.txt_dest.text().strip() if v_type == "LOAN_OUT" else ""
        }

        try:
            self.stock_svc.create_exit_voucher(voucher_data, self.exit_items)
            QMessageBox.information(self, "نجاح", f"تم تسجيل وصل الإخراج رقم ({v_num}) وخصم الكميات من المخزون بنجاح!")
            self.exit_items.clear()
            self.refresh_items_table()
            self.txt_num.clear()
            self.load_articles_list()
            self.load_history()
            return True
        except InsufficientStockError as e:
            QMessageBox.critical(self, "خطأ في المخزون", str(e))
            return False
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ وصل الإخراج: {e}")
            return False

    def load_vouchers(self):
        """توافقية الاستدعاء لتحميل سجل وصولات الخروج"""
        self.load_history()

    def load_history(self):
        with self.stock_svc.db.get_connection() as conn:
            r_id = getattr(self.stock_svc, "residence_id", None)
            if r_id:
                cur = conn.execute("""
                    SELECT * FROM exit_vouchers 
                    WHERE residence_id = ?
                    ORDER BY date DESC, id DESC
                """, (r_id,))
            else:
                cur = conn.execute("""
                    SELECT * FROM exit_vouchers 
                    ORDER BY date DESC, id DESC
                """)
            self.all_history_exits = cur.fetchall()

        self.pagination_history.set_total_items(len(self.all_history_exits), reset_page=True)
        self.render_history_page()

    def render_history_page(self):
        start_idx, end_idx = self.pagination_history.get_slice_range()
        page_rows = self.all_history_exits[start_idx:end_idx]

        self.table_history.setRowCount(len(page_rows))
        for r, v in enumerate(page_rows):
            self.table_history.setItem(r, 0, QTableWidgetItem(v["voucher_number"]))
            self.table_history.setItem(r, 1, QTableWidgetItem(v["date"]))
            type_str = "استهلاك مطبخ" if v["voucher_type"] == "KITCHEN" else "إعارة خارجية"
            self.table_history.setItem(r, 2, QTableWidgetItem(type_str))
            self.table_history.setItem(r, 3, QTableWidgetItem(f"{v['total_breakfast_cost']:,.2f}"))
            self.table_history.setItem(r, 4, QTableWidgetItem(f"{v['total_lunch_cost']:,.2f}"))
            self.table_history.setItem(r, 5, QTableWidgetItem(f"{v['total_dinner_cost']:,.2f}"))
            self.table_history.setItem(r, 6, QTableWidgetItem(f"{v['total_amount']:,.2f} دج"))

    def set_residence(self, residence_id: int):
        self.stock_svc.set_residence(residence_id)
        self.load_articles_list()
        self.load_history()
        self.apply_directorate_restrictions()

    def set_directorate_mode(self, is_directorate: bool):
        self.is_directorate = is_directorate
        self.apply_directorate_restrictions()

    def apply_directorate_restrictions(self):
        """قفل شاشة وصولات الإخراج للمديرية (للقراءة والتتبع فقط)"""
        if not getattr(self, "is_directorate", False):
            return
        if hasattr(self, "lbl_directorate_banner"):
            self.lbl_directorate_banner.setVisible(True)
        if hasattr(self, "btn_save") and self.btn_save:
            self.btn_save.setEnabled(False)
            self.btn_save.setText("حفظ وصل الاستهلاك (للمعاينة فقط 🔒)")
            self.btn_save.setToolTip("وضع المديرية: للمعاينة والتتبع فقط")
        if hasattr(self, "tabs"):
            self.tabs.setCurrentIndex(1)
