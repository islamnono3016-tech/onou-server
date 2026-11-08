try:
    from core.time_service import TimeService
except Exception:
    TimeService = None
from typing import Optional, Dict, Any
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QDateEdit, QMessageBox, QTextBrowser, QFileDialog,
    QTabWidget, QComboBox, QSpinBox, QCheckBox, QLineEdit,
    QToolButton, QCalendarWidget, QDialog
)
from PyQt6.QtCore import Qt, QDate, QTimer, QEvent, QObject, pyqtSignal, QPoint
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from reports.report_generator import ReportGenerator
from ui.common_filters import attach_smooth_scroll

class ClickSelectLineEdit(QLineEdit):
    """حقل إدخال يحدد كامل النص تلقائياً فور النقر أو التركيز لتسهيل الكتابة المباشرة بالكيبورد"""
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        QTimer.singleShot(0, self.selectAll)

class SmartDateBox(QWidget):
    """حقل إدخال تاريخ ذكي يدعم الكتابة المباشرة بالكيبورد بأي صيغة مع زر التقويم المنبثق"""
    dateChanged = pyqtSignal(QDate)

    def __init__(self, initial_date=None, parent=None):
        super().__init__(parent)
        self._date = initial_date or (TimeService.current_qdate() if TimeService else QDate.currentDate())
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.edit = ClickSelectLineEdit()
        self.edit.setText(self._date.toString("yyyy-MM-dd"))
        self.edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit.setPlaceholderText("YYYY-MM-DD")
        self.edit.setStyleSheet("""
            QLineEdit {
                background: #1E293B;
                color: #F8FAFC;
                border: 1.5px solid #475569;
                border-radius: 5px;
                padding: 3px 6px;
                font-weight: bold;
                font-size: 13px;
                min-width: 95px;
            }
            QLineEdit:focus {
                border: 1.5px solid #2DD4BF;
                background: #0F172A;
                color: #FFFFFF;
            }
            QLineEdit:disabled {
                background: #334155;
                color: #64748B;
                border-color: #334155;
            }
        """)
        self.edit.textChanged.connect(self._on_text_changed)
        self.edit.editingFinished.connect(self._on_editing_finished)

        self.btn = QToolButton()
        self.btn.setText("📅")
        self.btn.setToolTip("اختيار من التقويم")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setStyleSheet("""
            QToolButton {
                background: #334155;
                color: #FFFFFF;
                border: 1px solid #475569;
                border-radius: 5px;
                padding: 3px 6px;
                font-size: 12px;
            }
            QToolButton:hover {
                background: #0D9488;
                border-color: #14B8A6;
            }
            QToolButton:disabled {
                background: #1E293B;
                color: #475569;
                border-color: #334155;
            }
        """)
        self.btn.clicked.connect(self._open_calendar)

        layout.addWidget(self.edit)
        layout.addWidget(self.btn)

    def lineEdit(self):
        return self.edit

    def setCalendarPopup(self, val):
        pass

    def setDisplayFormat(self, fmt):
        pass

    def setKeyboardTracking(self, val):
        pass

    def _parse_text(self, text):
        raw = text.strip().replace('/', '-').replace('.', '-').replace(' ', '')
        parts = [p for p in raw.split('-') if p]
        if len(parts) == 3:
            p0, p1, p2 = parts
            if len(p0) == 4 and p0.isdigit() and p1.isdigit() and p2.isdigit():
                d = QDate(int(p0), int(p1), int(p2))
                if d.isValid(): return d
            elif len(p2) == 4 and p0.isdigit() and p1.isdigit() and p2.isdigit():
                d = QDate(int(p2), int(p1), int(p0))
                if d.isValid(): return d
            elif len(p0) <= 2 and len(p1) <= 2 and (len(p2) == 2 or len(p2) == 4) and p0.isdigit() and p1.isdigit() and p2.isdigit():
                yr = int(p2) if len(p2) == 4 else (2000 + int(p2))
                d = QDate(yr, int(p1), int(p0))
                if d.isValid(): return d
        elif len(parts) == 2:
            p0, p1 = parts
            if p0.isdigit() and p1.isdigit():
                yr = self._date.year() if (self._date and self._date.isValid()) else (TimeService.current_qdate() if TimeService else QDate.currentDate()).year()
                d = QDate(yr, int(p1), int(p0))
                if d.isValid(): return d
        elif len(raw) == 8 and raw.isdigit():
            d1 = QDate(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
            if d1.isValid() and int(raw[:4]) >= 2000: return d1
            d2 = QDate(int(raw[4:8]), int(raw[2:4]), int(raw[:2]))
            if d2.isValid(): return d2
        return None

    def _on_text_changed(self, text):
        d = self._parse_text(text)
        if d and d != self._date:
            self._date = d
            self.dateChanged.emit(self._date)

    def _on_editing_finished(self):
        d = self._parse_text(self.edit.text())
        if d:
            self._date = d
            self.edit.setText(self._date.toString("yyyy-MM-dd"))
            self.dateChanged.emit(self._date)
        else:
            self.edit.setText(self._date.toString("yyyy-MM-dd"))

    def _open_calendar(self):
        cal_dialog = QDialog(self, Qt.WindowType.Popup)
        cal_layout = QHBoxLayout(cal_dialog)
        cal_layout.setContentsMargins(4, 4, 4, 4)
        cal = QCalendarWidget()
        cal.setSelectedDate(self._date)
        cal.clicked.connect(lambda d: (
            self.setDate(d),
            cal_dialog.accept()
        ))
        cal_layout.addWidget(cal)
        pos = self.mapToGlobal(QPoint(0, self.height() + 2))
        cal_dialog.move(pos)
        cal_dialog.exec()

    def date(self):
        return self._date

    def setDate(self, d):
        if d and d.isValid():
            self._date = d
            self.edit.blockSignals(True)
            self.edit.setText(d.toString("yyyy-MM-dd"))
            self.edit.blockSignals(False)
            self.dateChanged.emit(d)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.edit.setEnabled(enabled)
        self.btn.setEnabled(enabled)

class ReportsWidget(QWidget):
    """
    مركز الطباعة وتوليد التقارير الرسمية الشامل
    يحتوي على جميع مخرجات الطباعة الرسمية المعتمدة في ملفات الإكسل (ONOU):
    1. ورقة الاستهلاك اليومي (مطبوعة) - تدعم الفترة المخصصة
    2. سجل النشاط بالأرقام (النشاط بالأرقام) - تدعم الفترة المخصصة
    3. سجل النشاط بالوجبة والقوائم الغذائية (النشاط بالوجبة) - تدعم الفترة المخصصة
    4. بطاقة الجرد الشهري العام (جرد) - تدعم الفترة المخصصة
    5. الجدول التفصيلي للكميات (جدول تفصيلي) - تدعم الفترة المخصصة
    6. بطاقة متابعة الوجبات الغذائية (بطاقة متابعة الوجبات) - تدعم الفترة المخصصة
    7. بطاقة حركة المخزون للمادة (بطاقة مخزون) - تدعم الفترة المخصصة
    8. وضعية الحصص الثلاثية والموردين - تدعم الفترة المخصصة
    """

    def __init__(self, report_generator: ReportGenerator, is_directorate: bool = True, current_user: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.report_gen = report_generator
        self.is_directorate = is_directorate
        self.current_user = current_user or {}
        self.current_html = ""
        self.res_bar = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 15)
        layout.setSpacing(10)

        # 🏛️ شريط اختيار وتأكيد الإقامة الجامعية النشطة للتقارير والطباعة
        res_bar = QFrame()
        res_bar.setObjectName("ReportsResBar")
        res_bar.setStyleSheet("""
            #ReportsResBar {
                background-color: #1E293B;
                border: 1.5px solid #0F766E;
                border-radius: 8px;
                padding: 4px 10px;
            }
        """)
        res_layout = QHBoxLayout(res_bar)
        res_layout.setContentsMargins(8, 4, 8, 4)
        res_layout.setSpacing(10)

        lbl_res_icon = QLabel("🏢")
        lbl_res_icon.setStyleSheet("font-size: 16px;")
        res_layout.addWidget(lbl_res_icon)

        lbl_res_title = QLabel("الإقامة الجامعية النشطة لاحتساب وطباعة التقارير:")
        lbl_res_title.setStyleSheet("font-weight: bold; color: #2DD4BF; font-size: 13px;")
        res_layout.addWidget(lbl_res_title)

        self.cmb_residence_filter = QComboBox()
        self.cmb_residence_filter.setObjectName("ReportsResCombo")
        self.cmb_residence_filter.setMinimumWidth(380)
        self.cmb_residence_filter.setStyleSheet("""
            QComboBox {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1.5px solid #38BDF8;
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #0F172A;
                color: #F8FAFC;
                selection-background-color: #0D9488;
                font-size: 13px;
                padding: 4px;
            }
        """)
        self.populate_residences_combo()
        self.cmb_residence_filter.currentIndexChanged.connect(self.on_report_residence_changed)
        res_layout.addWidget(self.cmb_residence_filter)

        res_layout.addStretch()

        lbl_badge = QLabel("🛡️ عزل تام للبيانات والحسابات لكل إقامة على حدة")
        lbl_badge.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: bold; background: rgba(56, 189, 248, 0.12); border: 1px solid #0284C7; padding: 4px 10px; border-radius: 5px;")
        res_layout.addWidget(lbl_badge)

        layout.addWidget(res_bar)
        self.res_bar = res_bar
        self.res_bar.setVisible(self.is_directorate)

        self.tabs = QTabWidget()

        # تبويب 1: ورقة الاستهلاك اليومي (مطبوعة)
        self.tab_daily = QWidget()
        self.init_daily_tab(self.tab_daily)
        self.tabs.addTab(self.tab_daily, "1. ورقة الاستهلاك اليومي (مطبوعة) 📄")

        # تبويب 2: سجل النشاط بالأرقام (النشاط بالأرقام)
        self.tab_act_nums = QWidget()
        self.init_act_nums_tab(self.tab_act_nums)
        self.tabs.addTab(self.tab_act_nums, "2. سجل النشاط بالأرقام (النشاط بالأرقام) 📊")

        # تبويب 3: سجل النشاط بالوجبة والقوائم الغذائية (النشاط بالوجبة)
        self.tab_act_meals = QWidget()
        self.init_act_meals_tab(self.tab_act_meals)
        self.tabs.addTab(self.tab_act_meals, "3. النشاط بالوجبة والقوائم (النشاط بالوجبة) 🍲")

        # تبويب 4: بطاقة الجرد الشهري العام (جرد)
        self.tab_jard = QWidget()
        self.init_jard_tab(self.tab_jard)
        self.tabs.addTab(self.tab_jard, "4. بطاقة الجرد الشهري العام (جرد) 📋")

        # تبويب 5: الجدول التفصيلي للكميات (جدول تفصيلي)
        self.tab_detailed = QWidget()
        self.init_detailed_tab(self.tab_detailed)
        self.tabs.addTab(self.tab_detailed, "5. الجدول التفصيلي للكميات (جدول تفصيلي) 📑")

        # تبويب 6: بطاقة متابعة الوجبات الغذائية (بطاقة متابعة الوجبات)
        self.tab_meals = QWidget()
        self.init_meals_tab(self.tab_meals)
        self.tabs.addTab(self.tab_meals, "6. بطاقة متابعة الوجبات الغذائية 🍽️")

        # تبويب 7: بطاقة حركة المخزون للمادة (بطاقة مخزون)
        self.tab_stock_card = QWidget()
        self.init_stock_card_tab(self.tab_stock_card)
        self.tabs.addTab(self.tab_stock_card, "7. بطاقة حركة المخزون لمادة (بطاقة مخزون) 📦")

        # تبويب 8: وضعية المدخولات الثلاثية (وضعية الموردين)
        self.tab_situation = QWidget()
        self.init_situation_tab(self.tab_situation)
        self.tabs.addTab(self.tab_situation, "8. وضعية الحصص الثلاثية والموردين 🏢")

        layout.addWidget(self.tabs)

        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.generate_daily_preview()

    def _create_date_range_controls(self, on_change_callback):
        """إنشاء إطار وبطاقة عناصر التحكم في الفترة المخصصة (من - إلى) مع إمكانية الكتابة المباشرة بالكيبورد"""
        today = TimeService.current_qdate() if TimeService else QDate.currentDate()
        first_of_month = QDate(today.year(), today.month(), 1)

        box = QFrame()
        box.setObjectName("DateRangeBox")
        box.setStyleSheet("""
            #DateRangeBox {
                background-color: rgba(15, 118, 110, 0.16);
                border: 1.5px solid #0D9488;
                border-radius: 8px;
                padding: 2px 6px;
            }
            #DateRangeBox:hover {
                border: 1.5px solid #14B8A6;
            }
        """)
        box_layout = QHBoxLayout(box)
        box_layout.setContentsMargins(6, 2, 6, 2)
        box_layout.setSpacing(6)

        chk = QCheckBox("تحديد فترة مخصصة:")
        chk.setCursor(Qt.CursorShape.PointingHandCursor)
        chk.setStyleSheet("font-weight: bold; color: #2DD4BF; font-size: 12px;")

        lbl_from = QLabel("من:")
        lbl_from.setStyleSheet("font-weight: bold; color: #E2E8F0; font-size: 12px;")

        dt_from = SmartDateBox(first_of_month)
        dt_from.setFixedWidth(130)
        dt_from.setEnabled(False)
        dt_from.lineEdit().returnPressed.connect(lambda: on_change_callback() if chk.isChecked() else None)

        lbl_to = QLabel("إلى:")
        lbl_to.setStyleSheet("font-weight: bold; color: #E2E8F0; font-size: 12px;")

        dt_to = SmartDateBox(today)
        dt_to.setFixedWidth(130)
        dt_to.setEnabled(False)
        dt_to.lineEdit().returnPressed.connect(lambda: on_change_callback() if chk.isChecked() else None)

        chk.toggled.connect(lambda checked: (
            dt_from.setEnabled(checked),
            dt_to.setEnabled(checked),
            on_change_callback()
        ))
        dt_from.dateChanged.connect(lambda: on_change_callback() if chk.isChecked() else None)
        dt_to.dateChanged.connect(lambda: on_change_callback() if chk.isChecked() else None)

        box_layout.addWidget(chk)
        box_layout.addWidget(lbl_from)
        box_layout.addWidget(dt_from)
        box_layout.addWidget(lbl_to)
        box_layout.addWidget(dt_to)

        return box, chk, dt_from, dt_to

    @staticmethod
    def _create_separator():
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #334155; max-height: 1px;")
        return sep

    @staticmethod
    def _create_action_buttons(refresh_slot, html_slot, excel_slot=None, print_slot=None, print_text="طباعة المطبوعة 🖨️"):
        row = QHBoxLayout()
        row.setSpacing(10)

        # 1. زر التحديث والمعاينة
        btn_ref = QPushButton("⟳ تحديث وعرض التقرير")
        btn_ref.setProperty("class", "btn-secondary")
        btn_ref.setMinimumHeight(34)
        btn_ref.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ref.setStyleSheet("background-color: #1E293B; border: 1.5px solid #475569; color: #F8FAFC; font-weight: bold; border-radius: 6px; padding: 6px 14px;")
        btn_ref.clicked.connect(refresh_slot)
        row.addWidget(btn_ref)

        # 2. زر الطباعة (الأساسي)
        btn_prt = None
        if print_slot:
            btn_prt = QPushButton(print_text)
            btn_prt.setProperty("class", "btn-primary")
            btn_prt.setStyleSheet("background-color: #0D9488; border: 1.5px solid #0F766E; color: #FFFFFF; font-weight: bold; min-width: 140px; border-radius: 6px; padding: 6px 14px;")
            btn_prt.setMinimumHeight(34)
            btn_prt.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_prt.clicked.connect(print_slot)
            row.addWidget(btn_prt)

        # 3. زر تصدير Excel
        btn_xls = None
        if excel_slot:
            btn_xls = QPushButton("تصدير إلى Excel 📑")
            btn_xls.setProperty("class", "btn-primary")
            btn_xls.setStyleSheet("background-color: #059669; border: 1.5px solid #047857; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 6px 14px;")
            btn_xls.setMinimumHeight(34)
            btn_xls.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_xls.clicked.connect(excel_slot)
            row.addWidget(btn_xls)

        # 4. زر حفظ كملف HTML
        btn_exp = QPushButton("حفظ كملف HTML 🌐")
        btn_exp.setProperty("class", "btn-secondary")
        btn_exp.setMinimumHeight(34)
        btn_exp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exp.setStyleSheet("background-color: #334155; border: 1.5px solid #475569; color: #E2E8F0; font-weight: bold; border-radius: 6px; padding: 6px 12px;")
        btn_exp.clicked.connect(html_slot)
        row.addWidget(btn_exp)

        row.addStretch()

        return row, btn_ref, btn_exp, btn_xls, btn_prt

    # -------------------------------------------------------------
    # 1. ورقة الاستهلاك اليومي (مطبوعة)
    # -------------------------------------------------------------
    def init_daily_tab(self, parent):
        l = QVBoxLayout(parent)
        l.setSpacing(8)

        bar = QFrame(); bar.setProperty("class", "content-panel")
        bar_layout = QVBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(8)

        # الصف الأول: اختيار التاريخ والفترة المخصصة
        row_filters = QHBoxLayout()
        row_filters.setSpacing(10)

        self.dt_daily = SmartDateBox(TimeService.current_qdate() if TimeService else QDate.currentDate())
        self.dt_daily.setFixedWidth(145)
        self.dt_daily.lineEdit().returnPressed.connect(self.generate_daily_preview)
        self.dt_daily.dateChanged.connect(self.generate_daily_preview)

        btn_prev = QPushButton("◀ اليوم السابق")
        btn_prev.setMinimumHeight(32)
        btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_prev.clicked.connect(lambda: self.dt_daily.setDate(self.dt_daily.date().addDays(-1)))

        btn_next = QPushButton("اليوم التالي ▶")
        btn_next.setMinimumHeight(32)
        btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_next.clicked.connect(lambda: self.dt_daily.setDate(self.dt_daily.date().addDays(1)))

        range_box, self.chk_daily_range, self.dt_daily_from, self.dt_daily_to = self._create_date_range_controls(self.generate_daily_preview)
        self.chk_daily_range.toggled.connect(lambda checked: (
            self.dt_daily.setEnabled(not checked),
            btn_prev.setEnabled(not checked),
            btn_next.setEnabled(not checked)
        ))

        lbl_title = QLabel("تاريخ ورقة الاستهلاك:")
        lbl_title.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")

        row_filters.addWidget(lbl_title)
        row_filters.addWidget(btn_prev)
        row_filters.addWidget(self.dt_daily)
        row_filters.addWidget(btn_next)
        row_filters.addStretch()
        row_filters.addWidget(range_box)
        bar_layout.addLayout(row_filters)

        # فاصل
        bar_layout.addWidget(self._create_separator())

        # الصف الثاني: شريط الإجراءات
        row_actions, _, _, _, _ = self._create_action_buttons(
            refresh_slot=self.generate_daily_preview,
            html_slot=self.export_html,
            excel_slot=self.export_daily_excel,
            print_slot=self.print_current,
            print_text="طباعة ورقة الاستهلاك 🖨️"
        )
        bar_layout.addLayout(row_actions)
        l.addWidget(bar)

        self.browser_daily = QTextBrowser()
        self.browser_daily.setStyleSheet("background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")
        attach_smooth_scroll(self.browser_daily)
        l.addWidget(self.browser_daily)

    def generate_daily_preview(self):
        if hasattr(self, "chk_daily_range") and self.chk_daily_range.isChecked():
            s_date = self.dt_daily_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_daily_to.date().toString("yyyy-MM-dd")
            self.current_html = self.report_gen.generate_daily_voucher_html_v2(start_date=s_date, end_date=e_date)
        else:
            d_str = self.dt_daily.date().toString("yyyy-MM-dd")
            self.current_html = self.report_gen.generate_daily_voucher_html_v2(date_str=d_str)
        self.browser_daily.setHtml(self.current_html)

    def export_daily_excel(self):
        if hasattr(self, "chk_daily_range") and self.chk_daily_range.isChecked():
            s_date = self.dt_daily_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_daily_to.date().toString("yyyy-MM-dd")
            path, _ = QFileDialog.getSaveFileName(self, "تصدير ورقة الاستهلاك إلى Excel", f"ورقة_الاستهلاك_{s_date}_إلى_{e_date}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_daily_voucher_excel(save_path=path, start_date=s_date, end_date=e_date)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف ورقة الاستهلاك بنجاح إلى:\n{path}")
        else:
            d_str = self.dt_daily.date().toString("yyyy-MM-dd")
            path, _ = QFileDialog.getSaveFileName(self, "تصدير ورقة الاستهلاك إلى Excel", f"ورقة_الاستهلاك_{d_str}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_daily_voucher_excel(date_str=d_str, save_path=path)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف ورقة الاستهلاك بنجاح إلى:\n{path}")

    # -------------------------------------------------------------
    # 2. سجل النشاط بالأرقام (النشاط بالأرقام)
    # -------------------------------------------------------------
    def init_act_nums_tab(self, parent):
        l = QVBoxLayout(parent)
        l.setSpacing(8)

        bar = QFrame(); bar.setProperty("class", "content-panel")
        bar_layout = QVBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(8)

        # الصف الأول: الفلاتر
        row_filters = QHBoxLayout()
        row_filters.setSpacing(10)

        self.spn_an_year = QSpinBox(); self.spn_an_year.setRange(2020, 2035); self.spn_an_year.setValue(2026)
        self.spn_an_year.setFixedWidth(110); self.spn_an_year.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cmb_an_month = QComboBox()
        self.cmb_an_month.setFixedWidth(145)
        for m, name in enumerate(["01 - جانفي", "02 - فيفري", "03 - مارس", "04 - أفريل", "05 - ماي", "06 - جوان", "07 - جويلية", "08 - أوت", "09 - سبتمبر", "10 - أكتوبر", "11 - نوفمبر", "12 - ديسمبر"], 1):
            self.cmb_an_month.addItem(name, m)
        self.cmb_an_month.setCurrentIndex((TimeService.current_qdate() if TimeService else QDate.currentDate()).month() - 1)

        self.spn_an_year.valueChanged.connect(self.generate_act_nums_preview)
        self.cmb_an_month.currentIndexChanged.connect(self.generate_act_nums_preview)

        range_box, self.chk_an_range, self.dt_an_from, self.dt_an_to = self._create_date_range_controls(self.generate_act_nums_preview)
        self.chk_an_range.toggled.connect(lambda checked: (
            self.spn_an_year.setEnabled(not checked),
            self.cmb_an_month.setEnabled(not checked)
        ))

        lbl_year = QLabel("السنة:"); lbl_year.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        lbl_month = QLabel("الشهر:"); lbl_month.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")

        row_filters.addWidget(lbl_year); row_filters.addWidget(self.spn_an_year)
        row_filters.addWidget(lbl_month); row_filters.addWidget(self.cmb_an_month)
        row_filters.addStretch()
        row_filters.addWidget(range_box)
        bar_layout.addLayout(row_filters)

        # فاصل
        bar_layout.addWidget(self._create_separator())

        # الصف الثاني: الأزرار
        row_actions, _, _, _, _ = self._create_action_buttons(
            refresh_slot=self.generate_act_nums_preview,
            html_slot=self.export_html,
            excel_slot=self.export_act_nums_excel,
            print_slot=self.print_current,
            print_text="طباعة النشاط بالأرقام 🖨️"
        )
        bar_layout.addLayout(row_actions)
        l.addWidget(bar)

        self.browser_act_nums = QTextBrowser()
        self.browser_act_nums.setStyleSheet("background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")
        attach_smooth_scroll(self.browser_act_nums)
        l.addWidget(self.browser_act_nums)

    def generate_act_nums_preview(self):
        if hasattr(self, "chk_an_range") and self.chk_an_range.isChecked():
            s_date = self.dt_an_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_an_to.date().toString("yyyy-MM-dd")
            self.current_html = self.report_gen.generate_activity_numbers_html(start_date=s_date, end_date=e_date)
        else:
            y = self.spn_an_year.value()
            m = self.cmb_an_month.currentData()
            self.current_html = self.report_gen.generate_activity_numbers_html(year=y, month=m)
        self.browser_act_nums.setHtml(self.current_html)

    def export_act_nums_excel(self):
        if hasattr(self, "chk_an_range") and self.chk_an_range.isChecked():
            s_date = self.dt_an_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_an_to.date().toString("yyyy-MM-dd")
            path, _ = QFileDialog.getSaveFileName(self, "تصدير النشاط بالأرقام إلى Excel", f"النشاط_بالأرقام_{s_date}_إلى_{e_date}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_activity_numbers_excel(save_path=path, start_date=s_date, end_date=e_date)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف النشاط بالأرقام بنجاح إلى:\n{path}")
        else:
            y = self.spn_an_year.value()
            m = self.cmb_an_month.currentData()
            path, _ = QFileDialog.getSaveFileName(self, "تصدير النشاط بالأرقام إلى Excel", f"النشاط_بالأرقام_{m:02d}_{y}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_activity_numbers_excel(year=y, month=m, save_path=path)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف النشاط بالأرقام بنجاح إلى:\n{path}")

    # -------------------------------------------------------------
    # 3. سجل النشاط بالوجبة والقوائم الغذائية (النشاط بالوجبة)
    # -------------------------------------------------------------
    def init_act_meals_tab(self, parent):
        l = QVBoxLayout(parent)
        l.setSpacing(8)

        bar = QFrame(); bar.setProperty("class", "content-panel")
        bar_layout = QVBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(8)

        # الصف الأول: الفلاتر
        row_filters = QHBoxLayout()
        row_filters.setSpacing(10)

        self.spn_am_year = QSpinBox(); self.spn_am_year.setRange(2020, 2035); self.spn_am_year.setValue(2026)
        self.spn_am_year.setFixedWidth(110); self.spn_am_year.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cmb_am_month = QComboBox()
        self.cmb_am_month.setFixedWidth(145)
        for m, name in enumerate(["01 - جانفي", "02 - فيفري", "03 - مارس", "04 - أفريل", "05 - ماي", "06 - جوان", "07 - جويلية", "08 - أوت", "09 - سبتمبر", "10 - أكتوبر", "11 - نوفمبر", "12 - ديسمبر"], 1):
            self.cmb_am_month.addItem(name, m)
        self.cmb_am_month.setCurrentIndex((TimeService.current_qdate() if TimeService else QDate.currentDate()).month() - 1)

        self.spn_am_year.valueChanged.connect(self.generate_act_meals_preview)
        self.cmb_am_month.currentIndexChanged.connect(self.generate_act_meals_preview)

        range_box, self.chk_am_range, self.dt_am_from, self.dt_am_to = self._create_date_range_controls(self.generate_act_meals_preview)
        self.chk_am_range.toggled.connect(lambda checked: (
            self.spn_am_year.setEnabled(not checked),
            self.cmb_am_month.setEnabled(not checked)
        ))

        lbl_year = QLabel("السنة:"); lbl_year.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        lbl_month = QLabel("الشهر:"); lbl_month.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")

        row_filters.addWidget(lbl_year); row_filters.addWidget(self.spn_am_year)
        row_filters.addWidget(lbl_month); row_filters.addWidget(self.cmb_am_month)
        row_filters.addStretch()
        row_filters.addWidget(range_box)
        bar_layout.addLayout(row_filters)

        # فاصل
        bar_layout.addWidget(self._create_separator())

        # الصف الثاني: الأزرار
        row_actions, _, _, _, _ = self._create_action_buttons(
            refresh_slot=self.generate_act_meals_preview,
            html_slot=self.export_html,
            excel_slot=self.export_act_meals_excel,
            print_slot=self.print_current,
            print_text="طباعة النشاط بالوجبة 🖨️"
        )
        bar_layout.addLayout(row_actions)
        l.addWidget(bar)

        self.browser_act_meals = QTextBrowser()
        self.browser_act_meals.setStyleSheet("background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")
        attach_smooth_scroll(self.browser_act_meals)
        l.addWidget(self.browser_act_meals)

    def generate_act_meals_preview(self):
        if hasattr(self, "chk_am_range") and self.chk_am_range.isChecked():
            s_date = self.dt_am_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_am_to.date().toString("yyyy-MM-dd")
            self.current_html = self.report_gen.generate_activity_meals_html(start_date=s_date, end_date=e_date)
        else:
            y = self.spn_am_year.value()
            m = self.cmb_am_month.currentData()
            self.current_html = self.report_gen.generate_activity_meals_html(year=y, month=m)
        self.browser_act_meals.setHtml(self.current_html)

    def export_act_meals_excel(self):
        if hasattr(self, "chk_am_range") and self.chk_am_range.isChecked():
            s_date = self.dt_am_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_am_to.date().toString("yyyy-MM-dd")
            path, _ = QFileDialog.getSaveFileName(self, "تصدير النشاط بالوجبة إلى Excel", f"النشاط_بالوجبة_{s_date}_إلى_{e_date}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_activity_meals_excel(save_path=path, start_date=s_date, end_date=e_date)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف النشاط بالوجبة بنجاح إلى:\n{path}")
        else:
            y = self.spn_am_year.value()
            m = self.cmb_am_month.currentData()
            path, _ = QFileDialog.getSaveFileName(self, "تصدير النشاط بالوجبة إلى Excel", f"النشاط_بالوجبة_{m:02d}_{y}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_activity_meals_excel(year=y, month=m, save_path=path)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف النشاط بالوجبة بنجاح إلى:\n{path}")

    # -------------------------------------------------------------
    # 4. بطاقة الجرد الشهري العام (جرد)
    # -------------------------------------------------------------
    def init_jard_tab(self, parent):
        l = QVBoxLayout(parent)
        l.setSpacing(8)

        bar = QFrame(); bar.setProperty("class", "content-panel")
        bar_layout = QVBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(8)

        # الصف الأول: الفلاتر
        row_filters = QHBoxLayout()
        row_filters.setSpacing(10)

        self.spn_jard_year = QSpinBox(); self.spn_jard_year.setRange(2020, 2035); self.spn_jard_year.setValue(2026)
        self.spn_jard_year.setFixedWidth(110); self.spn_jard_year.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cmb_jard_month = QComboBox()
        self.cmb_jard_month.setFixedWidth(145)
        for m, name in enumerate(["01 - جانفي", "02 - فيفري", "03 - مارس", "04 - أفريل", "05 - ماي", "06 - جوان", "07 - جويلية", "08 - أوت", "09 - سبتمبر", "10 - أكتوبر", "11 - نوفمبر", "12 - ديسمبر"], 1):
            self.cmb_jard_month.addItem(name, m)
        self.cmb_jard_month.setCurrentIndex((TimeService.current_qdate() if TimeService else QDate.currentDate()).month() - 1)

        self.spn_jard_year.valueChanged.connect(self.generate_jard_preview)
        self.cmb_jard_month.currentIndexChanged.connect(self.generate_jard_preview)

        range_box, self.chk_jard_range, self.dt_jard_from, self.dt_jard_to = self._create_date_range_controls(self.generate_jard_preview)
        self.chk_jard_range.toggled.connect(lambda checked: (
            self.spn_jard_year.setEnabled(not checked),
            self.cmb_jard_month.setEnabled(not checked)
        ))

        lbl_year = QLabel("السنة:"); lbl_year.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        lbl_month = QLabel("الشهر:"); lbl_month.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")

        row_filters.addWidget(lbl_year); row_filters.addWidget(self.spn_jard_year)
        row_filters.addWidget(lbl_month); row_filters.addWidget(self.cmb_jard_month)
        row_filters.addStretch()
        row_filters.addWidget(range_box)
        bar_layout.addLayout(row_filters)

        # فاصل
        bar_layout.addWidget(self._create_separator())

        # الصف الثاني: الأزرار
        row_actions, _, _, _, _ = self._create_action_buttons(
            refresh_slot=self.generate_jard_preview,
            html_slot=self.export_html,
            excel_slot=self.export_jard_excel,
            print_slot=self.print_current,
            print_text="طباعة بطاقة الجرد 🖨️"
        )
        bar_layout.addLayout(row_actions)
        l.addWidget(bar)

        self.browser_jard = QTextBrowser()
        self.browser_jard.setStyleSheet("background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")
        attach_smooth_scroll(self.browser_jard)
        l.addWidget(self.browser_jard)

    def generate_jard_preview(self):
        if hasattr(self, "chk_jard_range") and self.chk_jard_range.isChecked():
            s_date = self.dt_jard_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_jard_to.date().toString("yyyy-MM-dd")
            self.current_html = self.report_gen.generate_monthly_inventory_html(start_date=s_date, end_date=e_date)
        else:
            y = self.spn_jard_year.value()
            m = self.cmb_jard_month.currentData()
            self.current_html = self.report_gen.generate_monthly_inventory_html(year=y, month=m)
        self.browser_jard.setHtml(self.current_html)

    def export_jard_excel(self):
        if hasattr(self, "chk_jard_range") and self.chk_jard_range.isChecked():
            s_date = self.dt_jard_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_jard_to.date().toString("yyyy-MM-dd")
            path, _ = QFileDialog.getSaveFileName(self, "تصدير بطاقة الجرد إلى Excel", f"جرد_{s_date}_إلى_{e_date}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_monthly_inventory_excel(save_path=path, start_date=s_date, end_date=e_date)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف الجرد بنجاح إلى:\n{path}")
        else:
            y = self.spn_jard_year.value()
            m = self.cmb_jard_month.currentData()
            path, _ = QFileDialog.getSaveFileName(self, "تصدير بطاقة الجرد إلى Excel", f"جرد_{m:02d}_{y}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_monthly_inventory_excel(year=y, month=m, save_path=path)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف الجرد بنجاح إلى:\n{path}")

    # -------------------------------------------------------------
    # 5. الجدول التفصيلي للكميات (جدول تفصيلي)
    # -------------------------------------------------------------
    def init_detailed_tab(self, parent):
        l = QVBoxLayout(parent)
        l.setSpacing(8)

        bar = QFrame(); bar.setProperty("class", "content-panel")
        bar_layout = QVBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(8)

        # الصف الأول: الفلاتر
        row_filters = QHBoxLayout()
        row_filters.setSpacing(10)

        self.spn_det_year = QSpinBox(); self.spn_det_year.setRange(2020, 2035); self.spn_det_year.setValue(2026)
        self.spn_det_year.setFixedWidth(110); self.spn_det_year.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cmb_det_month = QComboBox()
        self.cmb_det_month.setFixedWidth(145)
        for m, name in enumerate(["01 - جانفي", "02 - فيفري", "03 - مارس", "04 - أفريل", "05 - ماي", "06 - جوان", "07 - جويلية", "08 - أوت", "09 - سبتمبر", "10 - أكتوبر", "11 - نوفمبر", "12 - ديسمبر"], 1):
            self.cmb_det_month.addItem(name, m)
        self.cmb_det_month.setCurrentIndex((TimeService.current_qdate() if TimeService else QDate.currentDate()).month() - 1)

        self.spn_det_year.valueChanged.connect(self.generate_detailed_preview)
        self.cmb_det_month.currentIndexChanged.connect(self.generate_detailed_preview)

        range_box, self.chk_det_range, self.dt_det_from, self.dt_det_to = self._create_date_range_controls(self.generate_detailed_preview)
        self.chk_det_range.toggled.connect(lambda checked: (
            self.spn_det_year.setEnabled(not checked),
            self.cmb_det_month.setEnabled(not checked)
        ))

        lbl_year = QLabel("السنة:"); lbl_year.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        lbl_month = QLabel("الشهر:"); lbl_month.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")

        row_filters.addWidget(lbl_year); row_filters.addWidget(self.spn_det_year)
        row_filters.addWidget(lbl_month); row_filters.addWidget(self.cmb_det_month)
        row_filters.addStretch()
        row_filters.addWidget(range_box)
        bar_layout.addLayout(row_filters)

        # فاصل
        bar_layout.addWidget(self._create_separator())

        # الصف الثاني: الأزرار
        row_actions, _, _, _, _ = self._create_action_buttons(
            refresh_slot=self.generate_detailed_preview,
            html_slot=self.export_html,
            excel_slot=self.export_detailed_excel,
            print_slot=self.print_current,
            print_text="طباعة الجدول التفصيلي 🖨️"
        )
        bar_layout.addLayout(row_actions)
        l.addWidget(bar)

        self.browser_detailed = QTextBrowser()
        self.browser_detailed.setStyleSheet("background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")
        attach_smooth_scroll(self.browser_detailed)
        l.addWidget(self.browser_detailed)

    def generate_detailed_preview(self):
        if hasattr(self, "chk_det_range") and self.chk_det_range.isChecked():
            s_date = self.dt_det_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_det_to.date().toString("yyyy-MM-dd")
            self.current_html = self.report_gen.generate_detailed_table_html(start_date=s_date, end_date=e_date)
        else:
            y = self.spn_det_year.value()
            m = self.cmb_det_month.currentData()
            self.current_html = self.report_gen.generate_detailed_table_html(year=y, month=m)
        self.browser_detailed.setHtml(self.current_html)

    def export_detailed_excel(self):
        if hasattr(self, "chk_det_range") and self.chk_det_range.isChecked():
            s_date = self.dt_det_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_det_to.date().toString("yyyy-MM-dd")
            path, _ = QFileDialog.getSaveFileName(self, "تصدير الجدول التفصيلي إلى Excel", f"جدول_تفصيلي_{s_date}_إلى_{e_date}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_detailed_table_excel(save_path=path, start_date=s_date, end_date=e_date)
                QMessageBox.information(self, "نجاح", f"تم تصدير الجدول التفصيلي بنجاح إلى:\n{path}")
        else:
            y = self.spn_det_year.value()
            m = self.cmb_det_month.currentData()
            path, _ = QFileDialog.getSaveFileName(self, "تصدير الجدول التفصيلي إلى Excel", f"جدول_تفصيلي_{m:02d}_{y}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_detailed_table_excel(year=y, month=m, save_path=path)
                QMessageBox.information(self, "نجاح", f"تم تصدير الجدول التفصيلي بنجاح إلى:\n{path}")

    # -------------------------------------------------------------
    # 6. بطاقة متابعة الوجبات الغذائية (بطاقة متابعة الوجبات)
    # -------------------------------------------------------------
    def init_meals_tab(self, parent):
        l = QVBoxLayout(parent)
        l.setSpacing(8)

        bar = QFrame(); bar.setProperty("class", "content-panel")
        bar_layout = QVBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(8)

        # الصف الأول: الفلاتر
        row_filters = QHBoxLayout()
        row_filters.setSpacing(10)

        self.spn_meals_year = QSpinBox(); self.spn_meals_year.setRange(2020, 2035); self.spn_meals_year.setValue(2026)
        self.spn_meals_year.setFixedWidth(110); self.spn_meals_year.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cmb_meals_month = QComboBox()
        self.cmb_meals_month.setFixedWidth(145)
        for m, name in enumerate(["01 - جانفي", "02 - فيفري", "03 - مارس", "04 - أفريل", "05 - ماي", "06 - جوان", "07 - جويلية", "08 - أوت", "09 - سبتمبر", "10 - أكتوبر", "11 - نوفمبر", "12 - ديسمبر"], 1):
            self.cmb_meals_month.addItem(name, m)
        self.cmb_meals_month.setCurrentIndex((TimeService.current_qdate() if TimeService else QDate.currentDate()).month() - 1)

        self.spn_meals_year.valueChanged.connect(self.generate_meals_preview)
        self.cmb_meals_month.currentIndexChanged.connect(self.generate_meals_preview)

        range_box, self.chk_meals_range, self.dt_meals_from, self.dt_meals_to = self._create_date_range_controls(self.generate_meals_preview)
        self.chk_meals_range.toggled.connect(lambda checked: (
            self.spn_meals_year.setEnabled(not checked),
            self.cmb_meals_month.setEnabled(not checked)
        ))

        lbl_year = QLabel("السنة:"); lbl_year.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        lbl_month = QLabel("الشهر:"); lbl_month.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")

        row_filters.addWidget(lbl_year); row_filters.addWidget(self.spn_meals_year)
        row_filters.addWidget(lbl_month); row_filters.addWidget(self.cmb_meals_month)
        row_filters.addStretch()
        row_filters.addWidget(range_box)
        bar_layout.addLayout(row_filters)

        # فاصل
        bar_layout.addWidget(self._create_separator())

        # الصف الثاني: الأزرار
        row_actions, _, _, _, _ = self._create_action_buttons(
            refresh_slot=self.generate_meals_preview,
            html_slot=self.export_html,
            excel_slot=self.export_meals_excel,
            print_slot=self.print_current,
            print_text="طباعة بطاقة متابعة الوجبات 🖨️"
        )
        bar_layout.addLayout(row_actions)
        l.addWidget(bar)

        self.browser_meals = QTextBrowser()
        self.browser_meals.setStyleSheet("background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")
        attach_smooth_scroll(self.browser_meals)
        l.addWidget(self.browser_meals)

    def generate_meals_preview(self):
        if hasattr(self, "chk_meals_range") and self.chk_meals_range.isChecked():
            s_date = self.dt_meals_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_meals_to.date().toString("yyyy-MM-dd")
            self.current_html = self.report_gen.generate_meal_tracking_html(start_date=s_date, end_date=e_date)
        else:
            y = self.spn_meals_year.value()
            m = self.cmb_meals_month.currentData()
            self.current_html = self.report_gen.generate_meal_tracking_html(year=y, month=m)
        self.browser_meals.setHtml(self.current_html)

    def export_meals_excel(self):
        if hasattr(self, "chk_meals_range") and self.chk_meals_range.isChecked():
            s_date = self.dt_meals_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_meals_to.date().toString("yyyy-MM-dd")
            path, _ = QFileDialog.getSaveFileName(self, "تصدير بطاقة متابعة الوجبات إلى Excel", f"بطاقة_متابعة_الوجبات_{s_date}_إلى_{e_date}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_meal_tracking_excel(save_path=path, start_date=s_date, end_date=e_date)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف متابعة الوجبات بنجاح إلى:\n{path}")
        else:
            y = self.spn_meals_year.value()
            m = self.cmb_meals_month.currentData()
            path, _ = QFileDialog.getSaveFileName(self, "تصدير بطاقة متابعة الوجبات إلى Excel", f"بطاقة_متابعة_الوجبات_{m:02d}_{y}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_meal_tracking_excel(year=y, month=m, save_path=path)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف متابعة الوجبات بنجاح إلى:\n{path}")

    # -------------------------------------------------------------
    # 7. بطاقة حركة المخزون للمادة (بطاقة مخزون)
    # -------------------------------------------------------------
    def init_stock_card_tab(self, parent):
        l = QVBoxLayout(parent)
        l.setSpacing(8)

        bar = QFrame(); bar.setProperty("class", "content-panel")
        bar_layout = QVBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(8)

        # الصف الأول: الفلاتر
        # الصف الأول: الفترة الزمنية والفترة المخصصة
        row_period = QHBoxLayout()
        row_period.setSpacing(10)

        lbl_year = QLabel("السنة:"); lbl_year.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        self.spn_sc_year = QSpinBox(); self.spn_sc_year.setRange(2020, 2035); self.spn_sc_year.setValue(2026)
        self.spn_sc_year.setFixedWidth(110); self.spn_sc_year.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_month = QLabel("الشهر:"); lbl_month.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        self.cmb_sc_month = QComboBox()
        self.cmb_sc_month.setFixedWidth(135)
        for m, name in enumerate(["01 - جانفي", "02 - فيفري", "03 - مارس", "04 - أفريل", "05 - ماي", "06 - جوان", "07 - جويلية", "08 - أوت", "09 - سبتمبر", "10 - أكتوبر", "11 - نوفمبر", "12 - ديسمبر"], 1):
            self.cmb_sc_month.addItem(name, m)
        self.cmb_sc_month.setCurrentIndex((TimeService.current_qdate() if TimeService else QDate.currentDate()).month() - 1)

        range_box, self.chk_sc_range, self.dt_sc_from, self.dt_sc_to = self._create_date_range_controls(self.generate_stock_card_preview)
        self.chk_sc_range.toggled.connect(lambda checked: (
            self.spn_sc_year.setEnabled(not checked),
            self.cmb_sc_month.setEnabled(not checked)
        ))

        self.spn_sc_year.valueChanged.connect(self.generate_stock_card_preview)
        self.cmb_sc_month.currentIndexChanged.connect(self.generate_stock_card_preview)

        row_period.addWidget(lbl_year)
        row_period.addWidget(self.spn_sc_year)
        row_period.addWidget(lbl_month)
        row_period.addWidget(self.cmb_sc_month)
        row_period.addStretch()
        row_period.addWidget(range_box)
        bar_layout.addLayout(row_period)

        # فاصل
        bar_layout.addWidget(self._create_separator())

        # الصف الثاني: الأزرار مع وضع المادة في الوسط
        row_actions = QHBoxLayout()
        row_actions.setSpacing(10)

        # 1. زر التحديث على اليمين
        btn_ref = QPushButton("⟳ تحديث وعرض التقرير")
        btn_ref.setProperty("class", "btn-secondary")
        btn_ref.setMinimumHeight(34)
        btn_ref.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ref.setStyleSheet("background-color: #1E293B; border: 1.5px solid #475569; color: #F8FAFC; font-weight: bold; border-radius: 6px; padding: 6px 14px;")
        btn_ref.clicked.connect(self.generate_stock_card_preview)
        row_actions.addWidget(btn_ref)

        # 2. اختيار المادة في الوسط
        lbl_art = QLabel("المادة:"); lbl_art.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        self.cmb_sc_article = QComboBox()
        self.cmb_sc_article.setEditable(True)
        self.cmb_sc_article.setMinimumWidth(280)
        self.cmb_sc_article.view().setMinimumWidth(360)
        articles = self.report_gen.stock_svc.get_articles()
        for a in articles:
            self.cmb_sc_article.addItem(f"{a['name']} ({a['unit']})", a["id"])
        self.cmb_sc_article.currentIndexChanged.connect(self.generate_stock_card_preview)

        row_actions.addSpacing(6)
        row_actions.addWidget(lbl_art)
        row_actions.addWidget(self.cmb_sc_article, stretch=1)
        row_actions.addSpacing(10)

        # 3. زر حفظ كملف HTML
        btn_exp = QPushButton("حفظ كملف HTML 🌐")
        btn_exp.setProperty("class", "btn-secondary")
        btn_exp.setMinimumHeight(34)
        btn_exp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exp.setStyleSheet("background-color: #334155; border: 1.5px solid #475569; color: #E2E8F0; font-weight: bold; border-radius: 6px; padding: 6px 12px;")
        btn_exp.clicked.connect(self.export_html)
        row_actions.addWidget(btn_exp)

        # 4. زر تصدير Excel
        btn_xls = QPushButton("تصدير إلى Excel 📑")
        btn_xls.setProperty("class", "btn-primary")
        btn_xls.setStyleSheet("background-color: #059669; border: 1.5px solid #047857; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 6px 14px;")
        btn_xls.setMinimumHeight(34)
        btn_xls.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_xls.clicked.connect(self.export_stock_card_excel)
        row_actions.addWidget(btn_xls)

        # 5. زر طباعة بطاقة المخزون
        btn_prt = QPushButton("طباعة بطاقة المخزون 🖨️")
        btn_prt.setProperty("class", "btn-primary")
        btn_prt.setStyleSheet("background-color: #0D9488; border: 1.5px solid #0F766E; color: #FFFFFF; font-weight: bold; min-width: 140px; border-radius: 6px; padding: 6px 14px;")
        btn_prt.setMinimumHeight(34)
        btn_prt.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_prt.clicked.connect(self.print_current)
        row_actions.addWidget(btn_prt)

        bar_layout.addLayout(row_actions)
        l.addWidget(bar)

        self.browser_stock_card = QTextBrowser()
        self.browser_stock_card.setStyleSheet("background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")
        attach_smooth_scroll(self.browser_stock_card)
        l.addWidget(self.browser_stock_card)

    def generate_stock_card_preview(self):
        art_id = self.cmb_sc_article.currentData()
        if not art_id:
            return
        if hasattr(self, "chk_sc_range") and self.chk_sc_range.isChecked():
            s_date = self.dt_sc_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_sc_to.date().toString("yyyy-MM-dd")
            self.current_html = self.report_gen.generate_stock_card_html(article_id=art_id, start_date=s_date, end_date=e_date)
        else:
            y = self.spn_sc_year.value()
            m = self.cmb_sc_month.currentData()
            self.current_html = self.report_gen.generate_stock_card_html(article_id=art_id, year=y, month=m)
        self.browser_stock_card.setHtml(self.current_html)

    def export_stock_card_excel(self):
        art_id = self.cmb_sc_article.currentData()
        if not art_id:
            return
        art_name = self.cmb_sc_article.currentText().split("(")[0].strip()
        if hasattr(self, "chk_sc_range") and self.chk_sc_range.isChecked():
            s_date = self.dt_sc_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_sc_to.date().toString("yyyy-MM-dd")
            path, _ = QFileDialog.getSaveFileName(self, "تصدير بطاقة المخزون إلى Excel", f"بطاقة_مخزون_{art_name}_{s_date}_إلى_{e_date}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_stock_card_excel(article_id=art_id, save_path=path, start_date=s_date, end_date=e_date)
                QMessageBox.information(self, "نجاح", f"تم تصدير بطاقة المخزون بنجاح إلى:\n{path}")
        else:
            y = self.spn_sc_year.value()
            m = self.cmb_sc_month.currentData()
            path, _ = QFileDialog.getSaveFileName(self, "تصدير بطاقة المخزون إلى Excel", f"بطاقة_مخزون_{art_name}_{m:02d}_{y}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_stock_card_excel(article_id=art_id, year=y, month=m, save_path=path)
                QMessageBox.information(self, "نجاح", f"تم تصدير بطاقة المخزون بنجاح إلى:\n{path}")

    # -------------------------------------------------------------
    # 8. وضعية المدخولات والحصص الثلاثية والموردين
    # -------------------------------------------------------------
    def init_situation_tab(self, parent):
        l = QVBoxLayout(parent)
        l.setSpacing(8)

        bar = QFrame(); bar.setProperty("class", "content-panel")
        bar_layout = QVBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        bar_layout.setSpacing(8)

        # الصف الأول: الفترة الزمنية والفترة المخصصة
        row_period = QHBoxLayout()
        row_period.setSpacing(10)

        lbl_year = QLabel("السنة:"); lbl_year.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        self.spn_sit_year = QSpinBox(); self.spn_sit_year.setRange(2020, 2035); self.spn_sit_year.setValue(2026)
        self.spn_sit_year.setFixedWidth(110); self.spn_sit_year.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_tri = QLabel("الثلاثي:"); lbl_tri.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        self.cmb_sit_tri = QComboBox()
        self.cmb_sit_tri.setMinimumWidth(220)
        self.cmb_sit_tri.addItem("الثلاثي الأول (جانفي - مارس)", 1)
        self.cmb_sit_tri.addItem("الثلاثي الثاني (أفريل - جوان)", 2)
        self.cmb_sit_tri.addItem("الثلاثي الثالث (جويلية - ديسمبر)", 3)

        range_box, self.chk_sit_range, self.dt_sit_from, self.dt_sit_to = self._create_date_range_controls(self.on_situation_period_changed)
        self.chk_sit_range.toggled.connect(lambda checked: (
            self.spn_sit_year.setEnabled(not checked),
            self.cmb_sit_tri.setEnabled(not checked)
        ))

        self.spn_sit_year.valueChanged.connect(self.on_situation_period_changed)
        self.cmb_sit_tri.currentIndexChanged.connect(self.on_situation_period_changed)

        row_period.addWidget(lbl_year)
        row_period.addWidget(self.spn_sit_year)
        row_period.addWidget(lbl_tri)
        row_period.addWidget(self.cmb_sit_tri)
        row_period.addStretch()
        row_period.addWidget(range_box)
        bar_layout.addLayout(row_period)

        # فاصل
        bar_layout.addWidget(self._create_separator())

        # الصف الثاني: الأزرار مع وضع الحصة / المورد في الوسط تماماً (مكان الدائرة الحمراء)
        row_actions = QHBoxLayout()
        row_actions.setSpacing(10)

        # 1. زر التحديث على اليمين
        btn_ref = QPushButton("⟳ تحديث وعرض التقرير")
        btn_ref.setProperty("class", "btn-secondary")
        btn_ref.setMinimumHeight(34)
        btn_ref.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ref.setStyleSheet("background-color: #1E293B; border: 1.5px solid #475569; color: #F8FAFC; font-weight: bold; border-radius: 6px; padding: 6px 14px;")
        btn_ref.clicked.connect(self.on_situation_period_changed)
        row_actions.addWidget(btn_ref)

        # 2. الحصة / المورد في الوسط (المكان المحدد بالدائرة الحمراء تماماً)
        lbl_lot = QLabel("الحصة / المورد:"); lbl_lot.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 13px;")
        self.cmb_sit_lot = QComboBox()
        self.cmb_sit_lot.setMinimumWidth(280)
        self.cmb_sit_lot.view().setMinimumWidth(360)
        self.cmb_sit_lot.addItem("جميع الحصص والموردين (شامل)", "ALL")
        self.cmb_sit_lot.currentIndexChanged.connect(self.generate_situation_preview)

        row_actions.addSpacing(6)
        row_actions.addWidget(lbl_lot)
        row_actions.addWidget(self.cmb_sit_lot, stretch=1)
        row_actions.addSpacing(10)

        # 3. زر حفظ كملف HTML
        btn_exp = QPushButton("حفظ كملف HTML 🌐")
        btn_exp.setProperty("class", "btn-secondary")
        btn_exp.setMinimumHeight(34)
        btn_exp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exp.setStyleSheet("background-color: #334155; border: 1.5px solid #475569; color: #E2E8F0; font-weight: bold; border-radius: 6px; padding: 6px 12px;")
        btn_exp.clicked.connect(self.export_html)
        row_actions.addWidget(btn_exp)

        # 4. زر تصدير Excel
        btn_xls = QPushButton("تصدير إلى Excel 📑")
        btn_xls.setProperty("class", "btn-primary")
        btn_xls.setStyleSheet("background-color: #059669; border: 1.5px solid #047857; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 6px 14px;")
        btn_xls.setMinimumHeight(34)
        btn_xls.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_xls.clicked.connect(self.export_situation_excel)
        row_actions.addWidget(btn_xls)

        # 5. زر طباعة وضعية الحصص
        btn_prt = QPushButton("طباعة وضعية الحصص 🖨️")
        btn_prt.setProperty("class", "btn-primary")
        btn_prt.setStyleSheet("background-color: #0D9488; border: 1.5px solid #0F766E; color: #FFFFFF; font-weight: bold; min-width: 140px; border-radius: 6px; padding: 6px 14px;")
        btn_prt.setMinimumHeight(34)
        btn_prt.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_prt.clicked.connect(self.print_current)
        row_actions.addWidget(btn_prt)

        bar_layout.addLayout(row_actions)
        l.addWidget(bar)

        self.browser_situation = QTextBrowser()
        self.browser_situation.setStyleSheet("background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")
        attach_smooth_scroll(self.browser_situation)
        l.addWidget(self.browser_situation)

        # تحميل الحصص والتقرير فورياً عند بناء التبويب
        self.on_situation_period_changed()

    def on_situation_period_changed(self):
        if hasattr(self, "chk_sit_range") and self.chk_sit_range.isChecked():
            s_date = self.dt_sit_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_sit_to.date().toString("yyyy-MM-dd")
            sit = self.report_gen.stock_svc.get_trimester_situation(start_date=s_date, end_date=e_date, residence_id=self.report_gen.residence_id)
        else:
            y = self.spn_sit_year.value()
            tri = self.cmb_sit_tri.currentData()
            sit = self.report_gen.stock_svc.get_trimester_situation(year=y, trimester=tri, residence_id=self.report_gen.residence_id)

        if hasattr(self, "cmb_sit_lot") and "distinct_lots" in sit:
            curr = self.cmb_sit_lot.currentData() or "ALL"
            self.cmb_sit_lot.blockSignals(True)
            self.cmb_sit_lot.clear()
            self.cmb_sit_lot.addItem("جميع الحصص والموردين (شامل)", "ALL")
            sel_idx = 0
            for i, l_name in enumerate(sit["distinct_lots"], start=1):
                self.cmb_sit_lot.addItem(l_name, l_name)
                if l_name == curr:
                    sel_idx = i
            self.cmb_sit_lot.setCurrentIndex(sel_idx)
            self.cmb_sit_lot.blockSignals(False)
        self.generate_situation_preview()

    def generate_situation_preview(self):
        lot_sel = self.cmb_sit_lot.currentData() if hasattr(self, "cmb_sit_lot") else "ALL"
        if hasattr(self, "chk_sit_range") and self.chk_sit_range.isChecked():
            s_date = self.dt_sit_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_sit_to.date().toString("yyyy-MM-dd")
            self.current_html = self.report_gen.generate_trimester_situation_html(lot_name=lot_sel, start_date=s_date, end_date=e_date)
        else:
            y = self.spn_sit_year.value()
            tri = self.cmb_sit_tri.currentData()
            self.current_html = self.report_gen.generate_trimester_situation_html(year=y, trimester=tri, lot_name=lot_sel)
        self.browser_situation.setHtml(self.current_html)

    def export_situation_excel(self):
        lot_sel = self.cmb_sit_lot.currentData() if hasattr(self, "cmb_sit_lot") else "ALL"
        if hasattr(self, "chk_sit_range") and self.chk_sit_range.isChecked():
            s_date = self.dt_sit_from.date().toString("yyyy-MM-dd")
            e_date = self.dt_sit_to.date().toString("yyyy-MM-dd")
            path, _ = QFileDialog.getSaveFileName(self, "تصدير الوضعية إلى Excel", f"وضعية_المدخولات_{s_date}_إلى_{e_date}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_trimester_situation_excel(save_path=path, lot_name=lot_sel, start_date=s_date, end_date=e_date)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف الوضعية بنجاح إلى:\n{path}")
        else:
            y = self.spn_sit_year.value()
            tri = self.cmb_sit_tri.currentData()
            path, _ = QFileDialog.getSaveFileName(self, "تصدير الوضعية إلى Excel", f"وضعية_الثلاثي_{tri}_{y}.xlsx", "Excel Files (*.xlsx)")
            if path:
                self.report_gen.export_trimester_situation_excel(year=y, trimester=tri, save_path=path, lot_name=lot_sel)
                QMessageBox.information(self, "نجاح", f"تم تصدير ملف الوضعية بنجاح إلى:\n{path}")

    # -------------------------------------------------------------
    # إجراءات عامة: التبديل، الطباعة، وحفظ HTML
    # -------------------------------------------------------------
    def on_tab_changed(self, idx):
        if idx == 0: self.generate_daily_preview()
        elif idx == 1: self.generate_act_nums_preview()
        elif idx == 2: self.generate_act_meals_preview()
        elif idx == 3: self.generate_jard_preview()
        elif idx == 4: self.generate_detailed_preview()
        elif idx == 5: self.generate_meals_preview()
        elif idx == 6: self.generate_stock_card_preview()
        elif idx == 7: self.on_situation_period_changed()

    def set_directorate_mode(self, is_directorate: bool):
        """ضبط وضع المديرية أو الإقامة لشريط اختيار الإقامة"""
        self.is_directorate = is_directorate
        if hasattr(self, "res_bar") and self.res_bar:
            self.res_bar.setVisible(is_directorate)

    def populate_residences_combo(self):
        if not hasattr(self, "cmb_residence_filter"):
            return
        self.cmb_residence_filter.blockSignals(True)
        self.cmb_residence_filter.clear()
        try:
            with self.report_gen.db.get_connection() as conn:
                rows = conn.execute("SELECT id, name, code FROM residences WHERE is_active = 1 ORDER BY id ASC").fetchall()
                curr_id = self.report_gen.residence_id
                curr_idx = 0
                for idx, r in enumerate(rows):
                    self.cmb_residence_filter.addItem(f"🏢 {r['name']}  [{r['code']}]", r["id"])
                    if r["id"] == curr_id:
                        curr_idx = idx
                self.cmb_residence_filter.setCurrentIndex(curr_idx)
        except Exception:
            pass
        self.cmb_residence_filter.blockSignals(False)

    def on_report_residence_changed(self):
        if not hasattr(self, "cmb_residence_filter"):
            return
        r_id = self.cmb_residence_filter.currentData()
        if not r_id:
            return
        with self.report_gen.db.get_connection() as conn:
            row = conn.execute("SELECT name FROM residences WHERE id = ?", (r_id,)).fetchone()
            r_name = row["name"] if row else ""
        self.set_residence(r_id, r_name)

        # مزامنة الواجهة الرئيسية إن كانت معروضة
        top = self.window()
        if top and hasattr(top, "set_active_residence") and top.current_residence_id != r_id:
            top.set_active_residence(r_id, r_name)

    def set_residence(self, r_id: int, r_name: str):
        self.report_gen.set_residence(r_id, r_name)
        if hasattr(self, "cmb_residence_filter"):
            self.cmb_residence_filter.blockSignals(True)
            for i in range(self.cmb_residence_filter.count()):
                if self.cmb_residence_filter.itemData(i) == r_id:
                    self.cmb_residence_filter.setCurrentIndex(i)
                    break
            self.cmb_residence_filter.blockSignals(False)
        self.refresh_current_tab()

    def reload_articles_list(self):
        """إعادة تحميل قائمة المواد عند تبديل الإقامة"""
        if hasattr(self, "cmb_sc_article"):
            self.cmb_sc_article.blockSignals(True)
            self.cmb_sc_article.clear()
            articles = self.report_gen.stock_svc.get_articles()
            for a in articles:
                self.cmb_sc_article.addItem(f"{a['name']} ({a['unit']})", a["id"])
            self.cmb_sc_article.blockSignals(False)

    def refresh_current_tab(self):
        self.reload_articles_list()
        self.on_tab_changed(self.tabs.currentIndex())

    def print_current(self):
        from core.print_helper import print_html_report
        idx = self.tabs.currentIndex()
        # تبويب 6 (بطاقة متابعة الوجبات الغذائية): بطاقة شهرية عمودية تطبع بالوضع العمودي Portrait
        is_landscape = (idx != 5)
        title = self.tabs.tabText(idx).replace("📄", "").replace("📊", "").replace("🍽️", "").replace("📈", "").replace("📋", "").replace("🔍", "").replace("📦", "").replace("🚚", "").replace("🍲", "").replace("📑", "").replace("🏢", "").strip()
        print_html_report(self, self.current_html, is_landscape=is_landscape, job_title=title, direct_print=False)

    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "حفظ التقرير بصيغة HTML", "تقرير_رسمي.html", "HTML Files (*.html)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.current_html)
            QMessageBox.information(self, "نجاح", f"تم حفظ ملف HTML بنجاح في:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر حفظ الملف: {e}")
