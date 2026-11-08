from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument, QColor, QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from core.stock_service import StockService
from reports.report_generator import ReportGenerator
from ui.widgets.pagination_bar import PaginationBar
from ui.theme import ThemeManager

class TrimesterSituationWidget(QWidget):
    """
    شاشة وضعية المدخولات والحصص الثلاثية والموردين
    (مطابقة 100% لملف عبد الحميد الوضعية.xlsx المعتمد في مديرية الخدمات الجامعية)
    - العناوين باللون الأحمر في المنتصف وعلى اليمين مطابقة للأسطر 7 و 9
    - ترتيب الأعمدة مطابق تماماً للأعمدة A إلى L
    - سطر المجاميع أسفل الجدول مطابق للسطر 48
    - شريط الإمضاءات الثلاثية مطابق للسطر 50 (مخزني الإطعام، رئيس المصلحة، المدير)
    """

    def __init__(self, stock_service: StockService, report_gen: ReportGenerator, parent=None):
        super().__init__(parent)
        self.stock_svc = stock_service
        self.report_gen = report_gen
        self.situation_data = {}
        self.filtered_items = []

        self.init_ui()
        self.load_situation()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 15)
        layout.setSpacing(10)

        # 1. شريط التحكم والفلاتر والاستيراد
        ctrl_bar = QFrame()
        ctrl_bar.setProperty("class", "content-panel")
        ctrl_bar.setStyleSheet("background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 6px;")
        cb_layout = QHBoxLayout(ctrl_bar)
        cb_layout.setContentsMargins(10, 6, 10, 6)
        cb_layout.setSpacing(8)

        self.spn_year = QSpinBox()
        self.spn_year.setRange(2020, 2035)
        self.spn_year.setValue(2026)
        self.spn_year.valueChanged.connect(self.load_situation)

        self.cmb_trimester = QComboBox()
        self.cmb_trimester.addItem("الثلاثي الأول (جانفي - مارس)", 1)
        self.cmb_trimester.addItem("الثلاثي الثاني (أفريل - جوان)", 2)
        self.cmb_trimester.addItem("الثلاثي الثالث (سبتمبر - ديسمبر)", 3)
        self.cmb_trimester.setCurrentIndex(2)  # الافتراضي الثلاثي الثالث لمطابقة ملف عبد الحميد
        self.cmb_trimester.currentIndexChanged.connect(self.load_situation)

        self.cmb_lot = QComboBox()
        self.cmb_lot.addItem("جميع الحصص والموردين (شامل)", "ALL")
        self.cmb_lot.currentIndexChanged.connect(self.load_situation)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("بحث سريع باسم المادة أو المورد...")
        self.txt_search.textChanged.connect(self.apply_filter)

        btn_refresh = QPushButton("تحديث ⟳")
        btn_refresh.setProperty("class", "btn-secondary")
        btn_refresh.clicked.connect(self.load_situation)

        btn_import = QPushButton("استيراد عبد الحميد الوضعية 📥")
        btn_import.setProperty("class", "btn-secondary")
        btn_import.setStyleSheet("background-color: #0F766E; color: white; font-weight: bold; padding: 5px 12px; border-radius: 4px;")
        btn_import.clicked.connect(self.import_wad3iya_dialog)

        btn_print = QPushButton("طباعة الوضعية 🖨️")
        btn_print.setProperty("class", "btn-secondary")
        btn_print.clicked.connect(self.print_situation)

        btn_export = QPushButton("تصدير Excel (.xlsx) 📑")
        btn_export.setProperty("class", "btn-primary")
        btn_export.clicked.connect(self.export_excel)

        cb_layout.addWidget(QLabel("السنة:"))
        cb_layout.addWidget(self.spn_year)
        cb_layout.addWidget(QLabel("الثلاثي:"))
        cb_layout.addWidget(self.cmb_trimester)
        cb_layout.addWidget(QLabel("الحصة:"))
        cb_layout.addWidget(self.cmb_lot)
        cb_layout.addWidget(self.txt_search, stretch=2)
        cb_layout.addWidget(btn_refresh)
        cb_layout.addWidget(btn_import)
        cb_layout.addWidget(btn_print)
        cb_layout.addWidget(btn_export)
        layout.addWidget(ctrl_bar)

        # 2. بطاقات المؤشرات المالية للثلاثي
        kpi_bar = QHBoxLayout()
        kpi_bar.setSpacing(10)

        self.card_allocated = self.create_kpi_card("إجمالي حصة المديرية الممنوحة", "0.00 دج", "#0284C7")
        self.card_actual = self.create_kpi_card("إجمالي المدخولات الفعلية", "0.00 دج", "#0D9488")
        self.card_deficit = self.create_kpi_card("الفارق المالي (بالنقصان)", "0.00 دج", "#DC2626")
        self.card_excess = self.create_kpi_card("الفارق المالي (بالزيادة)", "0.00 دج", "#16A34A")

        kpi_bar.addWidget(self.card_allocated)
        kpi_bar.addWidget(self.card_actual)
        kpi_bar.addWidget(self.card_deficit)
        kpi_bar.addWidget(self.card_excess)
        layout.addLayout(kpi_bar)

        # 3. لوحة العناوين الرسمية (مطابقة للأسطر 7 و 9 في ملف عبد الحميد الوضعية)
        self.title_banner_card = QFrame()
        self.title_banner_card.setObjectName("title_banner_card")
        self.title_banner_card.setProperty("class", "content-panel")
        self.title_banner_card.setStyleSheet("""
            QFrame#title_banner_card {
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        tb_layout = QVBoxLayout(self.title_banner_card)
        tb_layout.setContentsMargins(6, 6, 6, 6)
        tb_layout.setSpacing(4)

        self.lbl_period_title = QLabel("وضعية المدخولات من سبتمبر الى غاية ديسمبر من سنة 2026")
        self.lbl_period_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_period_title.setStyleSheet("font-family: 'Times New Roman', 'Segoe UI', Tahoma; font-size: 17px; font-weight: bold; color: #C00000; border: none;")

        self.lbl_lot_title = QLabel("حصة المواد الغذائية للمورد / قريشي بلخير")
        self.lbl_lot_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_lot_title.setStyleSheet("font-family: 'Simplified Arabic', 'Segoe UI', Tahoma; font-size: 14px; font-weight: bold; color: #C00000; text-decoration: underline; border: none;")

        tb_layout.addWidget(self.lbl_period_title)
        tb_layout.addWidget(self.lbl_lot_title)
        layout.addWidget(self.title_banner_card)

        # 4. جدول الوضعية الرقابية المطابق للإكسل (Cols A to L)
        self.table = QTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "الرقم", "المواد", "الحصة المسندة", "المورد المتعاقد", "الوحدة", "السعر بكل الرسوم",
            "الكمية الممنوحة", "المبلغ الممنوح دج",
            "المدخولات الفعلية", "المبلغ الفعلي دج",
            "فارق ك (زيادة)", "فارق ك (نقصان)",
            "فارق م (زيادة)", "فارق م (نقصان)"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 95)
        self.table.setColumnWidth(6, 85)
        self.table.setColumnWidth(7, 105)
        self.table.setColumnWidth(8, 85)
        self.table.setColumnWidth(9, 105)
        self.table.setColumnWidth(10, 80)
        self.table.setColumnWidth(11, 80)
        self.table.setColumnWidth(12, 95)
        self.table.setColumnWidth(13, 95)
        self.table.setAlternatingRowColors(True)
        from ui.common_filters import attach_smooth_scroll
        attach_smooth_scroll(self.table)
        layout.addWidget(self.table)

        # 5. سطر المجاميع الفرعية أسفل الجدول (مطابق للسطر 48 في Excel)
        self.totals_bar = QFrame()
        self.totals_bar.setObjectName("totals_bar")
        self.totals_bar.setStyleSheet("""
            QFrame#totals_bar {
                background: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        tot_layout = QHBoxLayout(self.totals_bar)
        tot_layout.setContentsMargins(12, 4, 12, 4)
        tot_layout.setSpacing(16)

        is_dark = ThemeManager.is_dark_mode()
        self.lbl_tot_title = QLabel("المجمـــــــــــــوع:")
        self.lbl_tot_title.setWordWrap(False)
        self.lbl_tot_title.setMinimumWidth(140)
        self.lbl_tot_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #38BDF8; border: none;" if is_dark else "font-weight: bold; font-size: 13px; color: #0F172A; border: none;")

        self.lbl_sum_allocated = QLabel("الممنوح: 0.00 دج")
        self.lbl_sum_allocated.setStyleSheet("font-weight: bold; font-size: 12px; color: #38BDF8; border: none;" if is_dark else "font-weight: bold; font-size: 12px; color: #0284C7; border: none;")

        self.lbl_sum_actual = QLabel("المدخولات: 0.00 دج")
        self.lbl_sum_actual.setStyleSheet("font-weight: bold; font-size: 12px; color: #34D399; border: none;" if is_dark else "font-weight: bold; font-size: 12px; color: #0F2D25; border: none;")

        self.lbl_sum_excess = QLabel("فارق الزيادة: 0.00 دج")
        self.lbl_sum_excess.setStyleSheet("font-weight: bold; font-size: 12px; color: #34D399; border: none;" if is_dark else "font-weight: bold; font-size: 12px; color: #16A34A; border: none;")

        self.lbl_sum_deficit = QLabel("فارق النقصان: 0.00 دج")
        self.lbl_sum_deficit.setStyleSheet("font-weight: bold; font-size: 12px; color: #F87171; border: none;" if is_dark else "font-weight: bold; font-size: 12px; color: #DC2626; border: none;")

        tot_layout.addWidget(self.lbl_tot_title)
        tot_layout.addStretch()
        tot_layout.addWidget(self.lbl_sum_allocated)
        tot_layout.addWidget(self.lbl_sum_actual)
        tot_layout.addWidget(self.lbl_sum_excess)
        tot_layout.addWidget(self.lbl_sum_deficit)
        layout.addWidget(self.totals_bar)

        # 6. شريط تقسيم الصفحات
        self.pagination = PaginationBar(initial_page_size=25, page_size_options=(15, 25, 50, 100))
        self.pagination.page_changed.connect(self.render_page)
        self.pagination.page_size_changed.connect(self.render_page)
        self.pagination.attach_to_table(self.table)
        layout.addWidget(self.pagination)

        # 7. شريط الإمضاءات الرسمية الثلاثية (مطابق تماماً للسطر 50 في ملف عبد الحميد الوضعية)
        self.signatures_panel = QFrame()
        self.signatures_panel.setObjectName("signatures_panel")
        self.signatures_panel.setStyleSheet("""
            QFrame#signatures_panel {
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 10px 16px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        sig_layout = QHBoxLayout(self.signatures_panel)
        sig_layout.setContentsMargins(20, 8, 20, 8)
        sig_layout.setSpacing(25)

        # اليمين: مخزني الاطعام
        box_right = QVBoxLayout()
        box_right.setSpacing(10)
        lbl_r = QLabel("مخزني الاطعام")
        lbl_r.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_r.setStyleSheet("font-weight: bold; font-size: 13px; color: #000000; font-family: 'Simplified Arabic', Tahoma; border: none;")
        dots_r = QLabel("............................................................")
        dots_r.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dots_r.setStyleSheet("color: #94A3B8; font-size: 11px; border: none;")
        box_right.addWidget(lbl_r)
        box_right.addWidget(dots_r)

        # الوسط: رئيس المصلحة
        box_center = QVBoxLayout()
        box_center.setSpacing(10)
        lbl_c = QLabel("رئيس المصلحة")
        lbl_c.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_c.setStyleSheet("font-weight: bold; font-size: 13px; color: #000000; font-family: 'Simplified Arabic', Tahoma; border: none;")
        dots_c = QLabel("............................................................")
        dots_c.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dots_c.setStyleSheet("color: #94A3B8; font-size: 11px; border: none;")
        box_center.addWidget(lbl_c)
        box_center.addWidget(dots_c)

        # اليسار: المديـــــــــــر
        box_left = QVBoxLayout()
        box_left.setSpacing(10)
        lbl_l = QLabel("المديـــــــــــر")
        lbl_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_l.setStyleSheet("font-weight: bold; font-size: 13px; color: #000000; font-family: 'Simplified Arabic', Tahoma; border: none;")
        dots_l = QLabel("............................................................")
        dots_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dots_l.setStyleSheet("color: #94A3B8; font-size: 11px; border: none;")
        box_left.addWidget(lbl_l)
        box_left.addWidget(dots_l)

        sig_layout.addLayout(box_right)
        sig_layout.addLayout(box_center)
        sig_layout.addLayout(box_left)
        layout.addWidget(self.signatures_panel)

    def create_kpi_card(self, title: str, val: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"background: #FFFFFF; border: 1px solid #CBD5E1; border-top: 3px solid {color}; border-radius: 6px; padding: 6px 12px;")
        l = QVBoxLayout(card)
        l.setContentsMargins(4, 4, 4, 4)
        t = QLabel(title); t.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold;")
        v = QLabel(val); v.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        l.addWidget(t); l.addWidget(v)
        card.val_lbl = v
        return card

    def load_situation(self):
        y = self.spn_year.value()
        tri = self.cmb_trimester.currentData()
        lot_sel = self.cmb_lot.currentData() if hasattr(self, "cmb_lot") else "ALL"

        self.situation_data = self.stock_svc.get_trimester_situation(y, tri, lot_name=lot_sel)

        # تحديث قائمة الحصص بدون إطلاق إشارات دائرية
        if hasattr(self, "cmb_lot") and "distinct_lots" in self.situation_data:
            current_choice = self.cmb_lot.currentData() or "ALL"
            self.cmb_lot.blockSignals(True)
            self.cmb_lot.clear()
            self.cmb_lot.addItem("جميع الحصص والموردين (شامل)", "ALL")
            sel_idx = 0
            for i, l_name in enumerate(self.situation_data["distinct_lots"], start=1):
                self.cmb_lot.addItem(l_name, l_name)
                if l_name == current_choice:
                    sel_idx = i
            self.cmb_lot.setCurrentIndex(sel_idx)
            self.cmb_lot.blockSignals(False)

        # تحديث عنوان الفترة باللون الأحمر في المنتصف
        period_title = self.report_gen._get_trimester_period_title(tri, y)
        self.lbl_period_title.setText(period_title)

        # تحديث عنوان الحصة والمورد باللون الأحمر على اليمين وإظهار/إخفاء الأعمدة
        if lot_sel == "ALL":
            self.lbl_lot_title.setText("جميع الحصص والموردين المتعاقدين")
            self.table.setColumnHidden(2, False)  # إظهار الحصة
            self.table.setColumnHidden(3, False)  # إظهار المورد
        else:
            supp_name = ""
            for lot_info in self.situation_data.get("lots", []):
                if lot_info["lot_name"] == lot_sel:
                    supp_name = lot_info.get("supplier_name", "")
                    break
            if supp_name:
                self.lbl_lot_title.setText(f"{lot_sel} للمورد / {supp_name}")
            else:
                self.lbl_lot_title.setText(f"{lot_sel}")
            # عند اختيار حصة محددة، نخفي عمودي الحصة والمورد لتطابق أعمدة الإكسل A-L الـ 12 تماماً
            self.table.setColumnHidden(2, True)
            self.table.setColumnHidden(3, True)

        # تحديث بطاقات المؤشرات
        self.card_allocated.val_lbl.setText(f"{self.situation_data['tot_allocated_amt']:,.2f} دج")
        self.card_actual.val_lbl.setText(f"{self.situation_data['tot_actual_amt']:,.2f} دج")
        self.card_deficit.val_lbl.setText(f"{self.situation_data['tot_diff_amt_deficit']:,.2f} دج")
        self.card_excess.val_lbl.setText(f"{self.situation_data['tot_diff_amt_excess']:,.2f} دج")

        # تحديث شريط المجاميع السفلية
        self.lbl_sum_allocated.setText(f"الممنوح: {self.situation_data['tot_allocated_amt']:,.2f} دج")
        self.lbl_sum_actual.setText(f"المدخولات: {self.situation_data['tot_actual_amt']:,.2f} دج")
        self.lbl_sum_excess.setText(f"فارق الزيادة: {self.situation_data['tot_diff_amt_excess']:,.2f} دج")
        self.lbl_sum_deficit.setText(f"فارق النقصان: {self.situation_data['tot_diff_amt_deficit']:,.2f} دج")

        self.apply_filter()

    def apply_filter(self):
        query = self.txt_search.text().strip().lower()
        items = self.situation_data.get("items", [])
        if not query:
            self.filtered_items = list(items)
        else:
            self.filtered_items = [
                it for it in items 
                if query in it["name"].lower() 
                or query in it.get("supplier_name", "").lower()
                or query in it.get("lot_name", "").lower()
            ]

        self.pagination.set_total_items(len(self.filtered_items), reset_page=True)
        self.render_page()

    def render_page(self):
        start_idx, end_idx = self.pagination.get_slice_range()
        page_items = self.filtered_items[start_idx:end_idx]

        self.table.setRowCount(len(page_items))

        for r, it in enumerate(page_items):
            c_code = QTableWidgetItem(str(it["code"]))
            c_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 0, c_code)

            c_name = QTableWidgetItem(it["name"])
            self.table.setItem(r, 1, c_name)

            self.table.setItem(r, 2, QTableWidgetItem(it.get("lot_name", "")))
            self.table.setItem(r, 3, QTableWidgetItem(it.get("supplier_name", "")))

            c_unit = QTableWidgetItem(it["unit"])
            c_unit.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 4, c_unit)

            p_item = QTableWidgetItem(f"{it['price_ttc']:,.2f}")
            p_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 5, p_item)

            c_alq = QTableWidgetItem(f"{it['allocated_qty']:g}")
            c_alq.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 6, c_alq)

            c_ala = QTableWidgetItem(f"{it['allocated_amt']:,.2f}")
            c_ala.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 7, c_ala)

            c_acq = QTableWidgetItem(f"{it['actual_qty']:g}")
            c_acq.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 8, c_acq)

            is_dark = ThemeManager.is_dark_mode()
            c_aca = QTableWidgetItem(f"{it['actual_amt']:,.2f}")
            c_aca.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            c_aca.setForeground(QColor("#34D399" if is_dark else "#0F2D25"))
            c_aca.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(r, 9, c_aca)

            # الفوارق بالكمية
            q_ex = QTableWidgetItem(f"{it['diff_qty_excess']:g}" if it['diff_qty_excess'] > 0 else "0")
            q_ex.setForeground(QColor("#16A34A"))
            q_ex.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 10, q_ex)

            q_def = QTableWidgetItem(f"{it['diff_qty_deficit']:g}" if it['diff_qty_deficit'] > 0 else "0")
            q_def.setForeground(QColor("#DC2626"))
            q_def.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 11, q_def)

            # الفوارق بالمبلغ
            a_ex = QTableWidgetItem(f"{it['diff_amt_excess']:,.2f}" if it['diff_amt_excess'] > 0 else "0.00")
            a_ex.setForeground(QColor("#16A34A"))
            a_ex.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 12, a_ex)

            a_def = QTableWidgetItem(f"{it['diff_amt_deficit']:,.2f}" if it['diff_amt_deficit'] > 0 else "0.00")
            a_def.setForeground(QColor("#DC2626"))
            a_def.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 13, a_def)

    def import_wad3iya_dialog(self):
        """نافذة اختيار واستيراد ملف عبد الحميد الوضعية.xlsx مع التحديث الفوري"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف عبد الحميد الوضعية المعتمد",
            r"F:\2026\عبد الحميد الوضعية.xlsx",
            "Excel Files (*.xlsx *.xls)"
        )
        if not path:
            return

        try:
            res = self.stock_svc.import_wad3iya_excel(path)
            QMessageBox.information(
                self,
                "اكتمل الاستيراد بنجاح ✔",
                f"تم استيراد وتحديث وضعية عبد الحميد بنجاح!\n\n"
                f"• عدد الموردين المعتمدين: {res['suppliers']}\n"
                f"• المواد الجديدة المستحدثة: {res['articles_created']}\n"
                f"• إجمالي الحصص المسجلة (لـ 3 ثلاثيات): {res['allocations']}"
            )
            self.load_situation()
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الاستيراد", f"تعذر استيراد ملف الوضعية:\n{e}")

    def print_situation(self):
        from core.print_helper import print_html_report
        y = self.spn_year.value()
        tri = self.cmb_trimester.currentData()
        lot_sel = self.cmb_lot.currentData() if hasattr(self, "cmb_lot") else "ALL"
        html = self.report_gen.generate_trimester_situation_html(y, tri, lot_name=lot_sel)
        print_html_report(self, html, is_landscape=True, job_title=f"وضعية الثلاثي {tri} لسنة {y}", direct_print=False)

    def export_excel(self):
        y = self.spn_year.value()
        tri = self.cmb_trimester.currentData()
        lot_sel = self.cmb_lot.currentData() if hasattr(self, "cmb_lot") else "ALL"
        t_name = self.cmb_trimester.currentText().split()[0] + "_" + self.cmb_trimester.currentText().split()[1]
        default_file = f"وضعية_المدخولات_{t_name}_{y}.xlsx"

        path, _ = QFileDialog.getSaveFileName(self, "حفظ ملف الوضعية", default_file, "Excel Files (*.xlsx)")
        if not path:
            return

        try:
            self.report_gen.export_trimester_situation_excel(y, tri, path, lot_name=lot_sel)
            QMessageBox.information(self, "نجاح", f"تم تصدير ملف الوضعية بنجاح إلى:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر تصدير الملف: {e}")

    def refresh_theme(self):
        """تحديث ألوان شريط المجاميع وجدول الوضعية لتناسب المظهر النشط"""
        is_dark = ThemeManager.is_dark_mode()
        c_bg = ThemeManager.get_color("card_bg")
        c_border = ThemeManager.get_color("card_border")

        if hasattr(self, "totals_bar") and self.totals_bar:
            self.totals_bar.setStyleSheet(f"""
                QFrame {{
                    background: {c_bg};
                    border: 1px solid {c_border};
                    border-radius: 6px;
                }}
            """)

        if hasattr(self, "lbl_tot_title") and self.lbl_tot_title:
            self.lbl_tot_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #38BDF8; border: none;" if is_dark else "font-weight: bold; font-size: 13px; color: #0F172A; border: none;")
        if hasattr(self, "lbl_sum_allocated") and self.lbl_sum_allocated:
            self.lbl_sum_allocated.setStyleSheet("font-weight: bold; font-size: 12px; color: #38BDF8; border: none;" if is_dark else "font-weight: bold; font-size: 12px; color: #0284C7; border: none;")
        if hasattr(self, "lbl_sum_actual") and self.lbl_sum_actual:
            self.lbl_sum_actual.setStyleSheet("font-weight: bold; font-size: 12px; color: #34D399; border: none;" if is_dark else "font-weight: bold; font-size: 12px; color: #0F2D25; border: none;")
        if hasattr(self, "lbl_sum_excess") and self.lbl_sum_excess:
            self.lbl_sum_excess.setStyleSheet("font-weight: bold; font-size: 12px; color: #34D399; border: none;" if is_dark else "font-weight: bold; font-size: 12px; color: #16A34A; border: none;")
        if hasattr(self, "lbl_sum_deficit") and self.lbl_sum_deficit:
            self.lbl_sum_deficit.setStyleSheet("font-weight: bold; font-size: 12px; color: #F87171; border: none;" if is_dark else "font-weight: bold; font-size: 12px; color: #DC2626; border: none;")

        self.render_page()
