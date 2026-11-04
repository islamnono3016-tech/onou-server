try:
    from core.time_service import TimeService
except Exception:
    TimeService = None
from typing import List, Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QDateEdit, QMessageBox, QScrollArea, QLineEdit, QStyledItemDelegate, QStyle,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QObject, QEvent, QTimer
from PyQt6.QtGui import QTextDocument, QPainter, QPen, QColor, QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from core.stock_service import StockService, InsufficientStockError
from core.meals_service import MealsService
from reports.report_generator import ReportGenerator
from ui.widgets.pagination_bar import PaginationBar
from ui.common_filters import prompt_save_changes

def get_arabic_weekday(qdate: QDate) -> str:
    days = {
        1: "الإثنين",
        2: "الثلاثاء",
        3: "الأربعاء",
        4: "الخميس",
        5: "الجمعة",
        6: "السبت",
        7: "الأحد"
    }
    return days.get(qdate.dayOfWeek(), "")

class ExcelHeaderDelegate(QStyledItemDelegate):
    """رسم ترويسة الجدول ثنائية المستوى بدقة متطابقة مع ملف الإكسل وتلوين عمود الخلية المحددة"""
    def __init__(self, owner=None, parent=None):
        super().__init__(parent or owner)
        self.owner = owner

    def paint(self, painter: QPainter, option, index):
        painter.save()
        col = index.column()
        row = index.row()

        from ui.theme import ThemeManager
        is_dark = ThemeManager.is_dark_mode()

        owner = self.owner
        curr_col = -1
        if owner and hasattr(owner, "table") and owner.table:
            curr_col = owner.table.currentColumn()

        is_highlighted = False
        if curr_col >= 0:
            if col == curr_col:
                is_highlighted = True
            elif row == 0:
                if curr_col in (3, 4) and col == 3:  # المدخولات (توريد | إستعارة)
                    is_highlighted = True
                elif curr_col in (5, 6, 7, 8) and col == 5:  # مخروجات (الصباح | الغداء | العشاء | إعارة)
                    is_highlighted = True

        if is_highlighted:
            bg_color = QColor("#134E4A" if is_dark else "#CCFBF1")
            fg_color = QColor("#5EEAD4" if is_dark else "#0F766E")
        else:
            bg_color = QColor("#1E293B" if is_dark else "#FFFFFF")
            fg_color = QColor("#F8FAFC" if is_dark else "#000000")

        grid_color = QColor("#334155" if is_dark else "#000000")
        thick_color = QColor("#64748B" if is_dark else "#000000")

        # خلفية الخلية
        painter.fillRect(option.rect, bg_color)

        # نص الترويسة
        text = index.model().data(index, Qt.ItemDataRole.DisplayRole) or ""
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.setPen(fg_color)
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, text)

        # خطوط الشبكة
        r = option.rect
        painter.setPen(QPen(grid_color, 1))
        painter.drawLine(r.left(), r.bottom(), r.right(), r.bottom())
        painter.drawLine(r.left(), r.top(), r.left(), r.bottom())

        # خطوط عمودية عريضة للفصل بين الأقسام الرئيسية
        thick_pen = QPen(thick_color, 2)
        if col in (1, 2, 4, 8):
            painter.setPen(thick_pen)
            painter.drawLine(r.left(), r.top(), r.left(), r.bottom())

        painter.restore()

class ExcelItemDelegate(QStyledItemDelegate):
    """
    رسم خلايا الجدول بنمط الإكسل التام المتوافق مع الوضع المظلم والفاتح:
    - خلايا نظيفة عند انعدام الحركة
    - خطوط شبكة واضحة مع خطوط عمودية عريضة تفصل الأقسام
    - محاذاة دقيقة ومحرر داخلي سلس ومتوافق مع المظهر
    - دعم كامل للتنقل بين الخلايا بمفاتيح الكيبورد بنمط Microsoft Excel (Enter, Shift+Enter, Tab, Shift+Tab, Arrows)
    """
    def __init__(self, owner=None, parent=None):
        super().__init__(parent or owner)
        self.owner = owner
        self.table = getattr(owner, 'table', None) or (parent if isinstance(parent, QTableWidget) else None)

    def createEditor(self, parent, option, index):
        if not self.table and hasattr(self.owner, 'table'):
            self.table = self.owner.table
        elif not self.table and isinstance(parent, QTableWidget):
            self.table = parent

        editor = QLineEdit(parent)
        editor.setProperty("cell_row", index.row())
        editor.setProperty("cell_col", index.column())
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        from ui.theme import ThemeManager
        is_dark = ThemeManager.is_dark_mode()
        bg = "#0F172A" if is_dark else "#FFFFFF"
        fg = "#F8FAFC" if is_dark else "#000000"
        border = "#14B8A6" if is_dark else "#000000"

        editor.setStyleSheet(f"""
            QLineEdit {{
                background: {bg};
                border: 2px solid {border};
                font-family: 'Segoe UI', Tahoma, Arial;
                font-size: 15px;
                font-weight: bold;
                color: {fg};
                padding: 0px;
            }}
        """)
        from ui.common_filters import NumberWheelFilter
        QTimer.singleShot(0, editor.selectAll)
        flt = NumberWheelFilter(editor)
        editor.installEventFilter(flt)
        editor.installEventFilter(self)
        return editor

    def setEditorData(self, editor, index):
        super().setEditorData(editor, index)
        if isinstance(editor, QLineEdit):
            QTimer.singleShot(0, editor.selectAll)

    def eventFilter(self, editor, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            mods = event.modifiers()

            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                direction = "UP" if (mods & Qt.KeyboardModifier.ShiftModifier) else "DOWN"
                self.commit_and_navigate(editor, direction)
                return True

            elif key == Qt.Key.Key_Tab:
                direction = "PREV" if (mods & Qt.KeyboardModifier.ShiftModifier) else "NEXT"
                self.commit_and_navigate(editor, direction)
                return True

            elif key == Qt.Key.Key_Backtab:
                self.commit_and_navigate(editor, "PREV")
                return True

            elif key == Qt.Key.Key_Down:
                self.commit_and_navigate(editor, "DOWN")
                return True

            elif key == Qt.Key.Key_Up:
                self.commit_and_navigate(editor, "UP")
                return True

            elif key == Qt.Key.Key_Left:
                # في التخطيط العربي (RTL): السهم الأيسر يتحرك بصرياً للأمام/اليسار للعمود التالي (NEXT)
                if isinstance(editor, QLineEdit):
                    txt = editor.text()
                    has_sel = editor.hasSelectedText()
                    all_sel = has_sel and (editor.selectedText() == txt)
                    pos = editor.cursorPosition()
                    if not txt or all_sel or (not has_sel and pos >= len(txt)):
                        self.commit_and_navigate(editor, "NEXT")
                        return True

            elif key == Qt.Key.Key_Right:
                # في التخطيط العربي (RTL): السهم الأيمن يتحرك بصرياً للخلف/اليمين للعمود السابق (PREV)
                if isinstance(editor, QLineEdit):
                    txt = editor.text()
                    has_sel = editor.hasSelectedText()
                    all_sel = has_sel and (editor.selectedText() == txt)
                    pos = editor.cursorPosition()
                    if not txt or all_sel or (not has_sel and pos == 0):
                        self.commit_and_navigate(editor, "PREV")
                        return True

        elif event.type() == QEvent.Type.Wheel:
            mods = event.modifiers()
            # عند تدوير عجلة الماوس بشكل طبيعي فوق الخلية المفتوحة للتحرير، يتم تمرير الجدول بسلاسة للأعلى والأسفل
            if not (mods & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
                owner = self.owner
                if not owner and self.table:
                    owner = getattr(self.table, "owner", None) or self.table.window()
                if owner and hasattr(owner, "smooth_scroll") and owner.smooth_scroll:
                    delta_y = event.angleDelta().y()
                    if delta_y != 0:
                        if owner.smooth_scroll.scroll_by_delta(delta_y):
                            return True

        return super().eventFilter(editor, event)

    def commit_and_navigate(self, editor, direction):
        curr_row = editor.property("cell_row")
        curr_col = editor.property("cell_col")
        if curr_row is None or curr_col is None:
            if self.table:
                curr_row = self.table.currentRow()
                curr_col = self.table.currentColumn()
            else:
                curr_row, curr_col = -1, -1

        # حفظ القيمة وإغلاق المحرر الحالي
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QStyledItemDelegate.EndEditHint.NoHint)

        # التوجيه للخلية التالية عبر دورة الأحداث لضمان إغلاق المحرر السابق بسلاسة
        owner = self.owner
        if not owner and self.table:
            owner = getattr(self.table, "owner", None) or self.table.window()

        if owner and hasattr(owner, "navigate_excel_cells") and curr_row >= 0 and curr_col >= 0:
            QTimer.singleShot(0, lambda r=curr_row, c=curr_col, d=direction: owner.navigate_excel_cells(r, c, d))

    def paint(self, painter: QPainter, option, index):
        painter.save()
        col = index.column()
        row = index.row()

        from ui.theme import ThemeManager
        is_dark = ThemeManager.is_dark_mode()

        curr_row = -1
        curr_col = -1
        if self.table:
            curr_row = self.table.currentRow()
            curr_col = self.table.currentColumn()

        is_active_cell = (row == curr_row and col == curr_col and curr_row >= 0 and curr_col >= 0)
        is_crosshair = (curr_row >= 0 and curr_col >= 0) and (row == curr_row or col == curr_col)

        # خلفية الخلية
        if is_active_cell or (option.state & QStyle.StateFlag.State_Selected):
            bg = QColor("#0F766E" if is_dark else "#99F6E4")
        elif is_crosshair:
            bg = QColor("#132E38" if is_dark else "#E6F7F5")
        else:
            bg = QColor("#1E293B" if is_dark else "#FFFFFF")

        painter.fillRect(option.rect, bg)

        # النص المعروض
        text = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        text = str(text).strip() if text is not None else ""

        font = QFont("Segoe UI", 13, QFont.Weight.Bold)
        fg_col = QColor("#F8FAFC" if is_dark else "#000000")
        grid_col = QColor("#334155" if is_dark else "#CBD5E1")
        thick_col = QColor("#64748B" if is_dark else "#000000")

        if is_active_cell:
            fg_col = QColor("#FFFFFF" if is_dark else "#042F2E")
            font.setBold(True)
        elif is_crosshair:
            fg_col = QColor("#E2E8F0" if is_dark else "#0F172A")
            if row == curr_row and col == 0:  # اسم المادة في السطر المحدد يبرز بلون مميز
                font.setBold(True)
                fg_col = QColor("#2DD4BF" if is_dark else "#0D9488")

        if col == 9:  # مخزون آخر مدة (العمود العاشر)
            try:
                val = float(text)
                if val < -1e-6:
                    bg = QColor("#7F1D1D" if is_dark else "#FEE2E2")
                    painter.fillRect(option.rect, bg)
                    painter.setPen(QColor("#F87171" if is_dark else "#DC2626"))
                else:
                    painter.setPen(fg_col)
            except Exception:
                painter.setPen(fg_col)
            font.setBold(True)
        else:
            painter.setPen(fg_col)

        painter.setFont(font)

        rect = option.rect.adjusted(8, 0, -8, 0)
        if col == 0:
            painter.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            align = Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignVCenter
        else:
            align = Qt.AlignmentFlag.AlignCenter
        painter.drawText(rect, align, text)

        # حدود الخلايا
        r = option.rect
        painter.setPen(QPen(grid_col, 1))
        painter.drawLine(r.left(), r.bottom(), r.right(), r.bottom())
        painter.drawLine(r.left(), r.top(), r.left(), r.bottom())

        # خطوط عمودية سميكة (2 بكسل) تفصل أقسام الإكسل بدقة
        thick_pen = QPen(thick_col, 2)
        if col in (1, 2, 4, 8):
            painter.setPen(thick_pen)
            painter.drawLine(r.left(), r.top(), r.left(), r.bottom())

        # إطار الخلية النشطة المحددة (Active Cell Focus Border)
        if is_active_cell:
            focus_pen = QPen(QColor("#2DD4BF" if is_dark else "#0D9488"), 2)
            painter.setPen(focus_pen)
            painter.drawRect(r.adjusted(1, 1, -1, -1))

        painter.restore()

class ExcelTableKeyFilter(QObject):
    """
    مرشح لوحة المفاتيح على جدول ورقة الاستهلاك:
    - يتيح التنقل المباشر بنمط Excel عند تحديد أي خلية
    - يفتح الخلية المستهدفة فوراً للتحرير مع تظليل القيمة للطباعة السريعة
    """
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def eventFilter(self, watched, event):
        if watched == self.owner.table and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            mods = event.modifiers()
            curr_row = self.owner.table.currentRow()
            curr_col = self.owner.table.currentColumn()
            if curr_row < 0:
                curr_row = 0
            editable_cols = getattr(self.owner, "EDITABLE_COLS", [3, 4, 5, 6, 7, 8])
            if not editable_cols:
                return super().eventFilter(watched, event)
            if curr_col not in editable_cols:
                curr_col = editable_cols[0]

            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                direction = "UP" if (mods & Qt.KeyboardModifier.ShiftModifier) else "DOWN"
                self.owner.navigate_excel_cells(curr_row, curr_col, direction)
                return True
            elif key == Qt.Key.Key_Tab:
                direction = "PREV" if (mods & Qt.KeyboardModifier.ShiftModifier) else "NEXT"
                self.owner.navigate_excel_cells(curr_row, curr_col, direction)
                return True
            elif key == Qt.Key.Key_Backtab:
                self.owner.navigate_excel_cells(curr_row, curr_col, "PREV")
                return True
            elif key == Qt.Key.Key_Down:
                self.owner.navigate_excel_cells(curr_row, curr_col, "DOWN")
                return True
            elif key == Qt.Key.Key_Up:
                self.owner.navigate_excel_cells(curr_row, curr_col, "UP")
                return True
            elif key == Qt.Key.Key_Left:
                self.owner.navigate_excel_cells(curr_row, curr_col, "NEXT")
                return True
            elif key == Qt.Key.Key_Right:
                self.owner.navigate_excel_cells(curr_row, curr_col, "PREV")
                return True
            elif key == Qt.Key.Key_Delete:
                item = self.owner.table.item(curr_row, curr_col)
                if item and (item.flags() & Qt.ItemFlag.ItemIsEditable):
                    item.setText("")
                    return True
            elif key == Qt.Key.Key_Backspace:
                item = self.owner.table.item(curr_row, curr_col)
                if item and (item.flags() & Qt.ItemFlag.ItemIsEditable):
                    item.setText("")
                    self.owner.focus_and_edit_cell(curr_row, curr_col)
                    return True
            elif key == Qt.Key.Key_F2:
                self.owner.focus_and_edit_cell(curr_row, curr_col)
                return True

        return super().eventFilter(watched, event)

class DailySheetWidget(QWidget):
    """
    شاشة ورقة الاستهلاك اليومي مطابقة لملفات Excel تماماً:
    - ترويسة ثنائية المستوى مدمجة: إسم المادة | مخزون أول مدة | المدخولات (توريد | إستعارة) | مخروجات (الصباح | الغداء | العشاء | إعارة) | مخزون أخر مدة
    - مظهر وجدول إكسل متكامل: خلايا بيضاء نظيفة فارغة عند الصفر، بدون إطارات أزرار أو حقول عائمة
    - شريط الأيام بالأرقام فقط (01 إلى 31)
    - كامل عرض الشاشة مخصص للمواد لتسهيل التصفح والإدخال السريع
    """

    daily_sheet_saved = pyqtSignal()
    open_general_info_requested = pyqtSignal(str)
    open_loans_requested = pyqtSignal()
    EDITABLE_COLS = [3, 4, 5, 6, 7, 8]

    def __init__(self, stock_service: StockService, meals_service: MealsService, report_gen: ReportGenerator, parent=None, is_directorate: bool = False, current_user: dict = None):
        super().__init__(parent)
        self.stock_svc = stock_service
        self.meals_svc = meals_service
        self.report_gen = report_gen
        self.is_directorate = is_directorate
        self.current_user = current_user or {}
        self.EDITABLE_COLS = [] if self.is_directorate else [3, 4, 5, 6, 7, 8]

        from core.date_lock_service import DateLockService
        self.date_lock_svc = DateLockService(stock_service.db)

        self.articles_data = []
        self.filtered_articles = []
        self.day_buttons = {}
        self.is_dirty = False
        self.current_loaded_date = (TimeService.current_qdate() if TimeService else QDate.currentDate())
        self._is_date_locked = False

        self.init_ui()
        self.load_daily_sheet()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 10, 12, 12)
        root_layout.setSpacing(8)

        # -------------------------------------------------------------
        # 1. شريط التحكم والترويسة العلوية
        # -------------------------------------------------------------
        top_bar = QFrame()
        top_bar.setObjectName("DailyTopBar")
        top_bar.setFixedHeight(48)
        self.top_bar = top_bar
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(12, 4, 12, 4)
        tb_layout.setSpacing(10)

        self.lbl_day_name = QLabel(f"ورقة في : {get_arabic_weekday(TimeService.current_qdate() if TimeService else QDate.currentDate())}")
        self.lbl_day_name.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F2D25;")
        tb_layout.addWidget(self.lbl_day_name)

        btn_prev_day = QPushButton("◀ السابق")
        btn_prev_day.setProperty("class", "btn-secondary")
        btn_prev_day.setStyleSheet("padding: 4px 10px; font-size: 12px;")
        btn_prev_day.clicked.connect(self.prev_day)
        tb_layout.addWidget(btn_prev_day)

        self.dt_picker = QDateEdit(TimeService.current_qdate() if TimeService else QDate.currentDate())
        self.dt_picker.setCalendarPopup(True)
        self.dt_picker.setDisplayFormat("yyyy-MM-dd")
        self.dt_picker.dateChanged.connect(self.on_date_changed)
        tb_layout.addWidget(self.dt_picker)

        btn_next_day = QPushButton("التالي ▶")
        btn_next_day.setProperty("class", "btn-secondary")
        btn_next_day.setStyleSheet("padding: 4px 10px; font-size: 12px;")
        btn_next_day.clicked.connect(self.next_day)
        tb_layout.addWidget(btn_next_day)

        btn_today = QPushButton("اليوم 📅")
        btn_today.setProperty("class", "btn-secondary")
        btn_today.setStyleSheet("padding: 4px 10px; font-size: 12px;")
        btn_today.clicked.connect(lambda: self.dt_picker.setDate(TimeService.current_qdate() if TimeService else QDate.currentDate()))
        tb_layout.addWidget(btn_today)

        tb_layout.addStretch()

        btn_to_info = QPushButton("📊 واجهة معلومات عامة")
        btn_to_info.setProperty("class", "btn-secondary")
        btn_to_info.setStyleSheet("padding: 6px 12px; font-weight: bold;")
        btn_to_info.clicked.connect(self.on_switch_to_general_info_clicked)
        tb_layout.addWidget(btn_to_info)

        btn_to_loans = QPushButton("🔄 حركة الإعارة والاستعارة")
        btn_to_loans.setProperty("class", "btn-secondary")
        btn_to_loans.setStyleSheet("padding: 6px 12px; font-weight: bold;")
        btn_to_loans.clicked.connect(self.open_loans_requested.emit)
        btn_to_loans.setVisible(False)
        tb_layout.addWidget(btn_to_loans)

        self.btn_add_art = QPushButton("➕ إضافة مادة جديدة")
        self.btn_add_art.setProperty("class", "btn-secondary")
        self.btn_add_art.setStyleSheet("padding: 6px 12px; font-weight: bold;")
        self.btn_add_art.clicked.connect(self.open_add_article_dialog)
        if self.is_directorate:
            self.btn_add_art.setEnabled(False)
            self.btn_add_art.setToolTip("خاص بمسؤول مخزن الإقامة الجامعية")
        tb_layout.addWidget(self.btn_add_art)

        self.btn_print = QPushButton("🖨️ طباعة المطبوعة الرسمية")
        self.btn_print.setProperty("class", "btn-secondary")
        self.btn_print.setStyleSheet("padding: 6px 14px; font-weight: bold;")
        self.btn_print.clicked.connect(self.print_daily_sheet)
        tb_layout.addWidget(self.btn_print)

        self.btn_save = QPushButton("💾 حفظ ورقة اليوم وتحديث المخزون")
        self.btn_save.setProperty("class", "btn-primary")
        self.btn_save.setStyleSheet("padding: 6px 16px; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_daily_sheet)
        tb_layout.addWidget(self.btn_save)

        root_layout.addWidget(top_bar)

        # شريط تنبيه خاص بوضع المديرية العامة (الإطلاع والتتبع فقط)
        self.lbl_directorate_banner = QLabel(
            "👁️ وضع الرقابة والمتابعة للمديرية: ورقة الاستهلاك اليومي مقفلة بالكامل أمام حسابات المديرية (للقراءة والتتبع والرقابة الميدانية فقط دون التعديل على القيم)."
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
        root_layout.addWidget(self.lbl_directorate_banner)

        # شريط حالة القفل / الترخيص (يظهر فقط عند الأيام المقيدة أو المرخصة)
        self.lock_banner = QFrame()
        self.lock_banner.setVisible(False)
        lk_layout = QHBoxLayout(self.lock_banner)
        lk_layout.setContentsMargins(12, 4, 12, 4)
        lk_layout.setSpacing(12)
        self.lbl_lock_icon = QLabel("🔒")
        self.lbl_lock_icon.setFixedWidth(22)
        self.lbl_lock_msg = QLabel("")
        self.lbl_lock_msg.setWordWrap(False)
        self.lbl_lock_msg.setStyleSheet("font-size: 12px; font-weight: bold;")
        lk_layout.addWidget(self.lbl_lock_icon)
        lk_layout.addWidget(self.lbl_lock_msg)
        lk_layout.addStretch()
        root_layout.addWidget(self.lock_banner)

        # -------------------------------------------------------------
        # 2. شريط أيام الشهر (01 إلى 31) - أرقام فقط بدون نصوص
        # -------------------------------------------------------------
        days_bar_scroll = QScrollArea()
        days_bar_scroll.setFixedHeight(40)
        days_bar_scroll.setWidgetResizable(True)
        days_bar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        days_bar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        days_bar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        days_widget = QWidget()
        days_layout = QHBoxLayout(days_widget)
        days_layout.setContentsMargins(0, 2, 0, 2)
        days_layout.setSpacing(4)

        for d in range(1, 32):
            btn_d = QPushButton(f"{d:02d}")
            btn_d.setFixedSize(32, 26)
            btn_d.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_d.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    color: #334155;
                    font-size: 11px;
                    font-weight: bold;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                }
            """)
            btn_d.clicked.connect(lambda _, day=d: self.select_day(day))
            days_layout.addWidget(btn_d)
            self.day_buttons[d] = btn_d

        days_bar_scroll.setWidget(days_widget)
        root_layout.addWidget(days_bar_scroll)

        self.days_bar_scroll = days_bar_scroll
        from ui.common_filters import DaysBarWheelFilter
        days_wheel_flt = DaysBarWheelFilter(self.next_day, self.prev_day, self.days_bar_scroll)
        self.days_bar_scroll.installEventFilter(days_wheel_flt)
        self.days_bar_scroll.viewport().installEventFilter(days_wheel_flt)
        days_widget.installEventFilter(days_wheel_flt)

        # -------------------------------------------------------------
        # 3. جدول المواد بنمط Excel المطابق تماماً
        # -------------------------------------------------------------
        table_container = QWidget()
        tc_layout = QVBoxLayout(table_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(0)

        # شريط البحث
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(4, 2, 4, 6)
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 تصفية المواد بالاسم أو الرمز...")
        self.txt_search.textChanged.connect(self.filter_articles)
        self.txt_search.setStyleSheet("padding: 5px 10px; font-size: 12px; border: 1px solid #CBD5E1; border-radius: 4px; background: #FFFFFF;")
        search_layout.addWidget(QLabel("تصفية:"))
        search_layout.addWidget(self.txt_search)
        tc_layout.addWidget(search_frame)

        # جدول الترويسة ثنائي المستوى مطابق للإكسل 100%
        self.header_table = QTableWidget(2, 10)
        self.header_table.setFixedHeight(74)
        self.header_table.setFrameShape(QFrame.Shape.NoFrame)
        self.header_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header_table.horizontalHeader().setVisible(False)
        self.header_table.verticalHeader().setVisible(False)
        self.header_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.header_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.header_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.header_table.setItemDelegate(ExcelHeaderDelegate(owner=self, parent=self.header_table))
        self.header_table.setRowHeight(0, 37)
        self.header_table.setRowHeight(1, 37)

        # دمج خلايا الترويسة:
        # 1. إسم المادة (سطرين)
        self.header_table.setSpan(0, 0, 2, 1)
        it_h_name = QTableWidgetItem("إسم\nالمادة")
        it_h_name.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_table.setItem(0, 0, it_h_name)

        # 2. الوحدة (سطرين)
        self.header_table.setSpan(0, 1, 2, 1)
        it_h_unit = QTableWidgetItem("الوحدة")
        it_h_unit.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_table.setItem(0, 1, it_h_unit)

        # 3. مخزون أول مدة (سطرين)
        self.header_table.setSpan(0, 2, 2, 1)
        it_h_init = QTableWidgetItem("مخزون\nأول مدة")
        it_h_init.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_table.setItem(0, 2, it_h_init)

        # 4. المدخولات (عمودين: توريد | إستعارة)
        self.header_table.setSpan(0, 3, 1, 2)
        it_h_in = QTableWidgetItem("المدخولات")
        it_h_in.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_table.setItem(0, 3, it_h_in)

        sup_label = "توريد 🔒" if self.is_directorate else "توريد"
        it_h_sup = QTableWidgetItem(sup_label)
        it_h_sup.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.is_directorate:
            it_h_sup.setToolTip("المدخولات: للاطلاع والتتبع فقط (لا يمكن للمديرية تعديل القيم)")
        self.header_table.setItem(1, 3, it_h_sup)

        li_label = "إستعارة 🔒" if self.is_directorate else "إستعارة"
        it_h_li = QTableWidgetItem(li_label)
        it_h_li.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.is_directorate:
            it_h_li.setToolTip("المدخولات: للاطلاع والتتبع فقط (لا يمكن للمديرية تعديل القيم)")
        self.header_table.setItem(1, 4, it_h_li)

        # 5. مخروجات (4 أعمدة: الصباح | الغداء | العشاء | إعارة)
        self.header_table.setSpan(0, 5, 1, 4)
        it_h_out = QTableWidgetItem("مخروجات")
        it_h_out.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_table.setItem(0, 5, it_h_out)

        out_titles = ["الصباح 🔒", "الغداء 🔒", "العشاء 🔒", "إعارة 🔒"] if self.is_directorate else ["الصباح", "الغداء", "العشاء", "إعارة"]
        for c_idx, title in enumerate(out_titles, 5):
            it_m = QTableWidgetItem(title)
            it_m.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.is_directorate:
                it_m.setToolTip("المخروجات: للاطلاع والتتبع فقط (لا يمكن للمديرية تعديل القيم)")
            self.header_table.setItem(1, c_idx, it_m)

        # 6. باقي المخزون (سطرين)
        self.header_table.setSpan(0, 9, 2, 1)
        it_h_fin = QTableWidgetItem("باقي\nالمخزون")
        it_h_fin.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_table.setItem(0, 9, it_h_fin)

        self.header_table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 2px solid #000000;
                border-bottom: none;
                font-family: 'Segoe UI', Tahoma, Arial;
            }
        """)
        tc_layout.addWidget(self.header_table)

        # جدول البيانات
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.excel_delegate = ExcelItemDelegate(self, self.table)
        self.table.setItemDelegate(self.excel_delegate)
        self.table_key_filter = ExcelTableKeyFilter(self)
        self.table.installEventFilter(self.table_key_filter)
        from ui.common_filters import SmoothScrollFilter
        self.smooth_scroll = SmoothScrollFilter(self.table, scroll_step=95, duration_ms=200)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked |
            QTableWidget.EditTrigger.SelectedClicked |
            QTableWidget.EditTrigger.AnyKeyPressed
        )
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 2px solid #000000;
                border-top: 1px solid #000000;
                font-family: 'Segoe UI', Tahoma, Arial;
                font-size: 13px;
                color: #000000;
            }
        """)

        # ضبط العرض الافتراضي للأعمدة
        tbl_hdr = self.table.horizontalHeader()
        tbl_hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        tbl_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # إسم المادة يأخذ كل المساحة الحرة

        self.table.setColumnWidth(1, 65)   # الوحدة
        self.table.setColumnWidth(2, 95)   # مخزون أول مدة
        self.table.setColumnWidth(3, 85)   # توريد
        self.table.setColumnWidth(4, 85)   # إستعارة
        self.table.setColumnWidth(5, 80)   # الصباح
        self.table.setColumnWidth(6, 80)   # الغداء
        self.table.setColumnWidth(7, 80)   # العشاء
        self.table.setColumnWidth(8, 80)   # إعارة
        self.table.setColumnWidth(9, 100)  # باقي المخزون

        # مزامنة أحجام الأعمدة والتمرير الأفقي بين الترويسة والبيانات
        tbl_hdr.sectionResized.connect(self.sync_header_widths)
        self.table.horizontalScrollBar().valueChanged.connect(self.header_table.horizontalScrollBar().setValue)
        self.table.itemChanged.connect(self.on_table_item_changed)
        self.table.currentCellChanged.connect(self.on_current_cell_changed)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

        tc_layout.addWidget(self.table)

        # شريط مجاميع المصاريف المباشرة
        self.totals_bar = QFrame()
        self.totals_bar.setStyleSheet("""
            QFrame {
                background: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 2px 8px;
            }
        """)
        tot_layout = QHBoxLayout(self.totals_bar)
        tot_layout.setContentsMargins(8, 4, 8, 4)
        tot_layout.setSpacing(14)

        self.tot_title = QLabel("💰 مجاميع مصاريف الاستهلاك :")
        tot_layout.addWidget(self.tot_title)

        self.lbl_b_title = QLabel("فطور الصباح:")
        tot_layout.addWidget(self.lbl_b_title)
        self.lbl_sum_bf = QLabel("0.00 دج")
        tot_layout.addWidget(self.lbl_sum_bf)

        self.lbl_l_title = QLabel("وجبة الغداء:")
        tot_layout.addWidget(self.lbl_l_title)
        self.lbl_sum_lu = QLabel("0.00 دج")
        tot_layout.addWidget(self.lbl_sum_lu)

        self.lbl_d_title = QLabel("وجبة العشاء:")
        tot_layout.addWidget(self.lbl_d_title)
        self.lbl_sum_di = QLabel("0.00 دج")
        tot_layout.addWidget(self.lbl_sum_di)

        tot_layout.addStretch()

        self.lbl_g_title = QLabel("المجموع الكلي للمصاريف:")
        tot_layout.addWidget(self.lbl_g_title)
        self.lbl_sum_grand = QLabel("0.00 دج")
        tot_layout.addWidget(self.lbl_sum_grand)

        tc_layout.addWidget(self.totals_bar)

        # شريط ملاحظات ورقة الاستهلاك اليومي
        self.notes_bar = QFrame()
        self.notes_bar.setObjectName("dailyNotesBar")
        notes_layout = QHBoxLayout(self.notes_bar)
        notes_layout.setContentsMargins(8, 4, 8, 4)
        notes_layout.setSpacing(10)

        self.lbl_notes_title = QLabel("📝 ملاحظة ورقة اليوم:")
        self.lbl_notes_title.setStyleSheet("font-weight: bold; font-size: 11px;")
        notes_layout.addWidget(self.lbl_notes_title)

        self.txt_daily_notes = QLineEdit()
        self.txt_daily_notes.setPlaceholderText("أدخل هنا أي ملاحظات خاصة بهذا اليوم لتُحفظ وتُطبع مع ورقة الاستهلاك...")
        self.txt_daily_notes.textChanged.connect(self.on_notes_modified)
        notes_layout.addWidget(self.txt_daily_notes)

        tc_layout.addWidget(self.notes_bar)

        # شريط الترقيم
        self.pagination = PaginationBar(initial_page_size=15, page_size_options=(10, 15, 25, 50, 100))
        self.pagination.page_changed.connect(self.render_table_page)
        self.pagination.page_size_changed.connect(self.render_table_page)
        self.pagination.attach_to_table(self.table)
        tc_layout.addWidget(self.pagination)

        root_layout.addWidget(table_container)
        self.refresh_theme()

    def update_day_buttons_style(self):
        """تحديث ألوان أزرار الأيام بما يتطابق مع المظهر النشط (داكن أو فاتح)"""
        from ui.theme import ThemeManager
        curr_day = self.dt_picker.date().day()
        day_bg = ThemeManager.get_color("day_btn_bg")
        day_fg = ThemeManager.get_color("day_btn_text")
        day_border = ThemeManager.get_color("day_btn_border")
        day_hover = ThemeManager.get_color("day_btn_hover")

        for d, btn in self.day_buttons.items():
            if d == curr_day:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0D9488;
                        color: #FFFFFF;
                        font-weight: bold;
                        border: 1px solid #0F766E;
                        border-radius: 4px;
                        padding: 0px;
                    }
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {day_bg};
                        color: {day_fg};
                        font-weight: bold;
                        border: 1px solid {day_border};
                        border-radius: 4px;
                        padding: 0px;
                    }}
                    QPushButton:hover {{
                        background-color: {day_hover};
                    }}
                """)

    def refresh_theme(self):
        """تحديث كامل عناصر ورقة الاستهلاك عند تغيير المظهر العام"""
        from ui.theme import ThemeManager
        c_bg = ThemeManager.get_color("card_bg")
        c_border = ThemeManager.get_color("card_border")
        in_bg = ThemeManager.get_color("input_bg")
        in_fg = ThemeManager.get_color("input_text")
        text_h = ThemeManager.get_color("text_heading")
        grid_thick = ThemeManager.get_color("table_grid_thick")

        if hasattr(self, "top_bar") and self.top_bar:
            self.top_bar.setStyleSheet(f"""
                QFrame#DailyTopBar {{
                    background: {c_bg};
                    border: 1px solid {c_border};
                    border-radius: 8px;
                }}
            """)
        if hasattr(self, "lbl_day_name") and self.lbl_day_name:
            self.lbl_day_name.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {text_h};")
        if hasattr(self, "txt_search") and self.txt_search:
            self.txt_search.setStyleSheet(f"padding: 5px 10px; font-size: 12px; border: 1px solid {c_border}; border-radius: 4px; background: {in_bg}; color: {in_fg};")

        if hasattr(self, "header_table") and self.header_table:
            self.header_table.setStyleSheet(f"""
                QTableWidget {{
                    background-color: {c_bg};
                    border: 2px solid {grid_thick};
                    border-bottom: none;
                    font-family: 'Segoe UI', Tahoma, Arial;
                }}
            """)
            self.header_table.viewport().update()

        if hasattr(self, "table") and self.table:
            self.table.setStyleSheet(f"""
                QTableWidget {{
                    background-color: {c_bg};
                    border: 2px solid {grid_thick};
                    border-top: 1px solid {grid_thick};
                    font-family: 'Segoe UI', Tahoma, Arial;
                    font-size: 13px;
                    color: {in_fg};
                }}
            """)
            self.table.viewport().update()

        is_dark = ThemeManager.is_dark_mode()

        if hasattr(self, "totals_bar") and self.totals_bar:
            self.totals_bar.setStyleSheet(f"""
                QFrame {{
                    background: {c_bg};
                    border: 1px solid {c_border};
                    border-radius: 6px;
                    padding: 2px 8px;
                }}
            """)

        title_color = "#38BDF8" if is_dark else "#0F2D25"
        label_muted = "#94A3B8" if is_dark else "#475569"
        bf_color = "#2DD4BF" if is_dark else "#0D9488"
        lu_color = "#38BDF8" if is_dark else "#0284C7"
        di_color = "#FB7185" if is_dark else "#E11D48"
        grand_title_color = "#F1F5F9" if is_dark else "#0F2D25"
        grand_bg = "#0F172A" if is_dark else "#E2E8F0"
        grand_fg = "#34D399" if is_dark else "#0F2D25"
        grand_border = "1.5px solid #059669" if is_dark else "1px solid #CBD5E1"

        if hasattr(self, "tot_title") and self.tot_title:
            self.tot_title.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {title_color};")
        if hasattr(self, "lbl_b_title") and self.lbl_b_title:
            self.lbl_b_title.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {label_muted};")
        if hasattr(self, "lbl_sum_bf") and self.lbl_sum_bf:
            self.lbl_sum_bf.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {bf_color};")
        if hasattr(self, "lbl_l_title") and self.lbl_l_title:
            self.lbl_l_title.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {label_muted};")
        if hasattr(self, "lbl_sum_lu") and self.lbl_sum_lu:
            self.lbl_sum_lu.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {lu_color};")
        if hasattr(self, "lbl_d_title") and self.lbl_d_title:
            self.lbl_d_title.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {label_muted};")
        if hasattr(self, "lbl_sum_di") and self.lbl_sum_di:
            self.lbl_sum_di.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {di_color};")
        if hasattr(self, "lbl_g_title") and self.lbl_g_title:
            self.lbl_g_title.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {grand_title_color};")
        if hasattr(self, "lbl_sum_grand") and self.lbl_sum_grand:
            self.lbl_sum_grand.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {grand_fg}; background: {grand_bg}; border: {grand_border}; padding: 2px 8px; border-radius: 4px;")

        self.update_day_buttons_style()

    def on_cell_clicked(self, row: int, col: int):
        """فتح محرر الخلية وتحديد النص فور النقر الأولي لتعديل فوري وسريع مع تحديث التلوين المتقاطع"""
        if hasattr(self, "table") and self.table:
            self.table.viewport().update()
        if hasattr(self, "header_table") and self.header_table:
            self.header_table.viewport().update()
        if col in self.EDITABLE_COLS:
            item = self.table.item(row, col)
            if item and (item.flags() & Qt.ItemFlag.ItemIsEditable):
                self.table.editItem(item)

    def on_current_cell_changed(self, curr_row: int, curr_col: int, prev_row: int, prev_col: int):
        """تحديث تلوين السطر والعمود فور تغير الخلية المحددة لتسهيل القراءة وتتبع المادة بنمط Excel Crosshair"""
        if hasattr(self, "table") and self.table:
            self.table.viewport().update()
        if hasattr(self, "header_table") and self.header_table:
            self.header_table.viewport().update()

    def navigate_excel_cells(self, curr_row: int, curr_col: int, direction: str):
        """
        التنقل الذكي السلس بين خلايا الإدخال بنمط مايكروسوفت إكسل (Microsoft Excel):
        - Enter / Down: النزول لنفس العمود في السطر التالي
        - Shift+Enter / Up: الصعود لنفس العمود في السطر السابق
        - Tab / Left: الانتقال للعمود القابل للإدخال التالي (مع الالتفاف للسطر الموالي)
        - Shift+Tab / Backtab / Right: الانتقال للعمود السابق (مع الالتفاف للسطر السابق)
        """
        if not hasattr(self, "table") or self.table is None:
            return
        total_rows = self.table.rowCount()
        if total_rows == 0:
            return

        if not self.EDITABLE_COLS:
            return
        if curr_col not in self.EDITABLE_COLS:
            curr_col = self.EDITABLE_COLS[0]

        idx = self.EDITABLE_COLS.index(curr_col)
        target_row = curr_row
        target_col = curr_col

        if direction == "DOWN":
            target_row = curr_row + 1
            if target_row >= total_rows:
                target_row = total_rows - 1

        elif direction == "UP":
            target_row = curr_row - 1
            if target_row < 0:
                target_row = 0

        elif direction == "NEXT":
            if idx + 1 < len(self.EDITABLE_COLS):
                target_col = self.EDITABLE_COLS[idx + 1]
            else:
                # الالتفاف للسطر التالي عند أول عمود إدخال
                if curr_row + 1 < total_rows:
                    target_row = curr_row + 1
                    target_col = self.EDITABLE_COLS[0]
                else:
                    target_row = curr_row
                    target_col = self.EDITABLE_COLS[-1]

        elif direction == "PREV":
            if idx - 1 >= 0:
                target_col = self.EDITABLE_COLS[idx - 1]
            else:
                # الالتفاف للسطر السابق عند آخر عمود إدخال
                if curr_row - 1 >= 0:
                    target_row = curr_row - 1
                    target_col = self.EDITABLE_COLS[-1]
                else:
                    target_row = 0
                    target_col = self.EDITABLE_COLS[0]

        self.focus_and_edit_cell(target_row, target_col)

    def focus_and_edit_cell(self, row: int, col: int):
        """تحديد الخلية المستهدفة وإظهارها والتمرير إليها وفتح محررها فوراً مع تظليل النص"""
        if not hasattr(self, "table") or self.table is None:
            return
        total_rows = self.table.rowCount()
        if total_rows == 0:
            return
        row = max(0, min(row, total_rows - 1))
        if not self.EDITABLE_COLS:
            return
        if col not in self.EDITABLE_COLS:
            col = self.EDITABLE_COLS[0]

        item = self.table.item(row, col)
        if not item:
            return

        self.table.setFocus()
        self.table.setCurrentCell(row, col)
        self.table.scrollToItem(item, QAbstractItemView.ScrollHint.EnsureVisible)
        self.table.editItem(item)

    def sync_header_widths(self, logicalIndex: int, oldSize: int, newSize: int):
        self.header_table.setColumnWidth(logicalIndex, newSize)

    def sync_all_column_widths(self):
        for c in range(10):
            self.header_table.setColumnWidth(c, self.table.columnWidth(c))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_all_column_widths()

    def select_day(self, day: int):
        curr_dt = self.dt_picker.date()
        max_d = curr_dt.daysInMonth()
        if day <= max_d:
            new_date = QDate(curr_dt.year(), curr_dt.month(), day)
            self.dt_picker.setDate(new_date)

    def on_date_changed(self):
        new_date = self.dt_picker.date()
        old_date = getattr(self, "current_loaded_date", None)
        if old_date and old_date != new_date and self.has_unsaved_changes():
            res = prompt_save_changes(
                self,
                title="تنبيه: حفظ ورقة الاستهلاك ⚠️",
                message="هل تريد حفظ التغييرات على ورقة هذا اليوم قبل الانتقال ليوم آخر؟",
                detail=f"تم تعديل بيانات ورقة يوم ({old_date.toString('yyyy-MM-dd')}) دون الضغط على زر الحفظ."
            )
            if res == "YES":
                if not self.save_changes(for_date=old_date.toString("yyyy-MM-dd")):
                    self.dt_picker.blockSignals(True)
                    self.dt_picker.setDate(old_date)
                    self.dt_picker.blockSignals(False)
                    return
            elif res == "CANCEL":
                self.dt_picker.blockSignals(True)
                self.dt_picker.setDate(old_date)
                self.dt_picker.blockSignals(False)
                return
            else:
                self.is_dirty = False

        curr_dt = self.dt_picker.date()
        weekday_name = get_arabic_weekday(curr_dt)
        self.lbl_day_name.setText(f"ورقة في : {weekday_name}")

        self.update_day_buttons_style()
        curr_day = curr_dt.day()
        if hasattr(self, "days_bar_scroll") and curr_day in self.day_buttons:
            self.days_bar_scroll.ensureWidgetVisible(self.day_buttons[curr_day])
        self.load_daily_sheet()

    def prev_day(self):
        curr = self.dt_picker.date()
        self.dt_picker.setDate(curr.addDays(-1))

    def next_day(self):
        curr = self.dt_picker.date()
        self.dt_picker.setDate(curr.addDays(1))

    def load_daily_sheet(self):
        date_str = self.dt_picker.date().toString("yyyy-MM-dd")
        data = self.stock_svc.get_daily_sheet_data(date_str)

        self.articles_data = data["articles"]
        self.filtered_articles = list(self.articles_data)

        meals = data.get("meals") or {}
        note_text = meals.get("notes") or ""
        if hasattr(self, "txt_daily_notes") and self.txt_daily_notes:
            self.txt_daily_notes.blockSignals(True)
            self.txt_daily_notes.setText(note_text)
            self.txt_daily_notes.blockSignals(False)

        self.pagination.set_total_items(len(self.filtered_articles), reset_page=True)
        self.render_table_page()
        self.update_live_totals()
        self.current_loaded_date = self.dt_picker.date()
        self.is_dirty = False

        # فحص قفل التاريخ وتحديث الواجهة بشكل لحظي
        self._update_date_lock_ui(date_str)

    def filter_articles(self):
        query = self.txt_search.text().strip().lower()
        if not query:
            self.filtered_articles = list(self.articles_data)
        else:
            self.filtered_articles = [a for a in self.articles_data if query in a["name"].lower() or query in a.get("code", "").lower()]
        self.pagination.set_total_items(len(self.filtered_articles), reset_page=True)
        self.render_table_page()

    def render_table_page(self):
        start_idx, end_idx = self.pagination.get_slice_range()
        page_items = self.filtered_articles[start_idx:end_idx]

        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        try:
            self.table.setRowCount(len(page_items))

            for r, it in enumerate(page_items):
                self.table.setRowHeight(r, 38)

                # 0. إسم المادة (محاذاة لليمين طبيعية مطابقة للإكسل)
                it_name = QTableWidgetItem(it["name"])
                it_name.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                it_name.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(r, 0, it_name)

                # 1. الوحدة
                unit_str = it.get("unit") or ""
                it_unit = QTableWidgetItem(unit_str)
                it_unit.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_unit.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(r, 1, it_unit)

                # 2. مخزون أول مدة (فارغ إذا كان صفراً مطابق للإكسل)
                init_stk = it["initial_stock"]
                it_init = QTableWidgetItem(f"{init_stk:g}" if init_stk != 0 else "")
                it_init.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_init.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(r, 2, it_init)

                # 3. توريد (مدخولات)
                sup_qty = it.get("supply_qty", 0.0)
                it_sup = QTableWidgetItem(f"{sup_qty:g}" if sup_qty != 0 else "")
                it_sup.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                _editable = not getattr(self, "_is_date_locked", False)
                _base_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                _cell_flags = (_base_flags | Qt.ItemFlag.ItemIsEditable) if _editable else _base_flags

                # قفل كافة الأعمدة (المدخولات والمخروجات) على المديرية
                _col_editable = _editable and not getattr(self, "is_directorate", False)
                _col_flags = (_base_flags | Qt.ItemFlag.ItemIsEditable) if _col_editable else _base_flags

                it_sup.setFlags(_col_flags)
                if getattr(self, "is_directorate", False):
                    it_sup.setToolTip("وضع المديرية: للقراءة والتتبع والرقابة فقط")
                self.table.setItem(r, 3, it_sup)

                # 4. إستعارة (مدخولات)
                li_qty = it.get("loan_in_qty", 0.0)
                it_li = QTableWidgetItem(f"{li_qty:g}" if li_qty != 0 else "")
                it_li.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_li.setFlags(_col_flags)
                if getattr(self, "is_directorate", False):
                    it_li.setToolTip("وضع المديرية: للقراءة والتتبع والرقابة فقط")
                self.table.setItem(r, 4, it_li)

                # 5. الصباح (مخروجات)
                bf_qty = it.get("bf_qty", 0.0)
                it_bf = QTableWidgetItem(f"{bf_qty:g}" if bf_qty != 0 else "")
                it_bf.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_bf.setFlags(_col_flags)
                if getattr(self, "is_directorate", False):
                    it_bf.setToolTip("وضع المديرية: للقراءة والتتبع والرقابة فقط")
                self.table.setItem(r, 5, it_bf)

                # 6. الغداء (مخروجات)
                lu_qty = it.get("lu_qty", 0.0)
                it_lu = QTableWidgetItem(f"{lu_qty:g}" if lu_qty != 0 else "")
                it_lu.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_lu.setFlags(_col_flags)
                if getattr(self, "is_directorate", False):
                    it_lu.setToolTip("وضع المديرية: للقراءة والتتبع والرقابة فقط")
                self.table.setItem(r, 6, it_lu)

                # 7. العشاء (مخروجات)
                di_qty = it.get("di_qty", 0.0)
                it_di = QTableWidgetItem(f"{di_qty:g}" if di_qty != 0 else "")
                it_di.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_di.setFlags(_col_flags)
                if getattr(self, "is_directorate", False):
                    it_di.setToolTip("وضع المديرية: للقراءة والتتبع والرقابة فقط")
                self.table.setItem(r, 7, it_di)

                # 8. إعارة (مخروجات)
                lo_qty = it.get("loan_out_qty", 0.0)
                it_lo = QTableWidgetItem(f"{lo_qty:g}" if lo_qty != 0 else "")
                it_lo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_lo.setFlags(_col_flags)
                if getattr(self, "is_directorate", False):
                    it_lo.setToolTip("وضع المديرية: للقراءة والتتبع والرقابة فقط")
                self.table.setItem(r, 8, it_lo)

                # 9. باقي المخزون (محسوب آلياً)
                fin_stk = it["final_stock"]
                it_fin = QTableWidgetItem(f"{fin_stk:g}" if fin_stk != 0 else "0")
                it_fin.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_fin.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                if fin_stk < -1e-6:
                    it_fin.setForeground(QColor("#DC2626"))
                    it_fin.setBackground(QColor("#FEE2E2"))
                    it_fin.setToolTip(f"تنبيه: الرصيد سالب ({fin_stk:g})! المخرجات تجاوزت المخزون المتوفر.")
                self.table.setItem(r, 9, it_fin)
        finally:
            self.table.blockSignals(False)
            self.table.setUpdatesEnabled(True)

        self.sync_all_column_widths()

    def on_table_item_changed(self, item: QTableWidgetItem):
        col = item.column()
        if col not in (3, 4, 5, 6, 7, 8):
            return

        row = item.row()
        start_idx, _ = self.pagination.get_slice_range()
        real_idx = start_idx + row
        if real_idx >= len(self.filtered_articles):
            return

        it_dict = self.filtered_articles[real_idx]

        txt = item.text().strip()
        try:
            val = float(txt) if txt else 0.0
            if val < 0:
                val = 0.0
        except ValueError:
            val = 0.0

        init = float(it_dict.get("initial_stock", 0.0) or 0.0)
        sup = float(it_dict.get("supply_qty", 0.0) or 0.0)
        li = float(it_dict.get("loan_in_qty", 0.0) or 0.0)
        avail = max(0.0, init + sup + li)

        # فحص المخروجات لمنع تجاوز المخزون المتوفر
        if col in (5, 6, 7, 8):
            other_out = 0.0
            for c_idx, f_name in [(5, "bf_qty"), (6, "lu_qty"), (7, "di_qty"), (8, "loan_out_qty")]:
                if c_idx != col:
                    other_out += float(it_dict.get(f_name, 0.0) or 0.0)

            max_allowed = max(0.0, round(avail - other_out, 4))
            if val > (max_allowed + 1e-6):
                col_names = {
                    5: "فطور الصباح",
                    6: "الغداء",
                    7: "العشاء",
                    8: "الإعارة"
                }
                art_name = it_dict.get("name", "المادة")
                unit = it_dict.get("unit", "")
                QMessageBox.warning(
                    self,
                    "تنبيه: الكمية المطلوبة تتجاوز المخزون المتوفر ⚠️",
                    f"عفواً، لا يمكن أن تتجاوز الكمية المخرجة رصيد المخزون المتوفر للمادة!\n\n"
                    f"• المادة: {art_name}\n"
                    f"• الخانة: {col_names.get(col, '')}\n"
                    f"• الكمية المدخلة: {val:g} {unit}\n"
                    f"• الحد الأقصى المتاح للصرف: {max_allowed:g} {unit}\n"
                    f"  (المتوفر الكلي: {avail:g} {unit} | مخرجات الوجبات الأخرى: {other_out:g} {unit})\n\n"
                    f"تم ضبط الكمية تلقائياً على الحد الأقصى المتاح ({max_allowed:g} {unit}) لمنع ظهور رصيد سالب."
                )
                val = max_allowed

        elif col in (3, 4):
            other_in = init + (float(it_dict.get("loan_in_qty", 0.0) or 0.0) if col == 3 else float(it_dict.get("supply_qty", 0.0) or 0.0))
            tot_out = (float(it_dict.get("bf_qty", 0.0) or 0.0) +
                       float(it_dict.get("lu_qty", 0.0) or 0.0) +
                       float(it_dict.get("di_qty", 0.0) or 0.0) +
                       float(it_dict.get("loan_out_qty", 0.0) or 0.0))

            min_required = max(0.0, round(tot_out - other_in, 4))
            if val < (min_required - 1e-6):
                col_names = {3: "التوريد", 4: "الاستعارة"}
                art_name = it_dict.get("name", "المادة")
                unit = it_dict.get("unit", "")
                QMessageBox.warning(
                    self,
                    "تنبيه: لا يمكن خفض الوارد دون الاستهلاك ⚠️",
                    f"عفواً، لا يمكن خفض كمية {col_names.get(col, '')} لأن الكميات المصروفة خلال اليوم تتطلب حداً أدنى من الوارد!\n\n"
                    f"• المادة: {art_name}\n"
                    f"• الكمية المدخلة: {val:g} {unit}\n"
                    f"• الحد الأدنى المطلوب لتغطية مصاريف اليوم: {min_required:g} {unit}\n"
                    f"  (إجمالي المصروف اليوم: {tot_out:g} {unit})\n\n"
                    f"تم تعديل الكمية تلقائياً إلى الحد الأدنى المطلوب ({min_required:g} {unit}) لتفادي وقوع المخزون بالسالب."
                )
                val = min_required

        field_map = {
            3: "supply_qty",
            4: "loan_in_qty",
            5: "bf_qty",
            6: "lu_qty",
            7: "di_qty",
            8: "loan_out_qty"
        }
        field = field_map[col]
        it_dict[field] = val

        # إعادة حساب مخزون آخر مدة
        init = float(it_dict.get("initial_stock", 0.0) or 0.0)
        sup = float(it_dict.get("supply_qty", 0.0) or 0.0)
        li = float(it_dict.get("loan_in_qty", 0.0) or 0.0)
        bf = float(it_dict.get("bf_qty", 0.0) or 0.0)
        lu = float(it_dict.get("lu_qty", 0.0) or 0.0)
        di = float(it_dict.get("di_qty", 0.0) or 0.0)
        lo = float(it_dict.get("loan_out_qty", 0.0) or 0.0)

        final_stk = round(init + sup + li - (bf + lu + di + lo), 4)
        it_dict["final_stock"] = final_stk

        p = float(it_dict.get("price_ttc", 0.0) or 0.0)
        it_dict["cost_bf"] = bf * p
        it_dict["cost_lu"] = lu * p
        it_dict["cost_di"] = di * p
        it_dict["total_expense"] = (bf + lu + di) * p

        # تحديث الخلية برقم نظيف أو فارغ عند الصفر وتحديث خانة باقي المخزون (العمود 9)
        self.table.blockSignals(True)
        item.setText(f"{val:g}" if val != 0 else "")
        fin_item = self.table.item(row, 9)
        if fin_item:
            fin_item.setText(f"{final_stk:g}" if final_stk != 0 else "0")
            if final_stk < -1e-6:
                fin_item.setForeground(QColor("#DC2626"))
                fin_item.setBackground(QColor("#FEE2E2"))
                fin_item.setToolTip(f"تنبيه: الرصيد سالب ({final_stk:g})! المخرجات تجاوزت المخزون المتاح.")
            else:
                from ui.theme import ThemeManager
                is_dark = ThemeManager.is_dark_mode()
                fin_item.setForeground(QColor("#F8FAFC" if is_dark else "#0F172A"))
                fin_item.setBackground(QColor("#1E293B" if is_dark else "#F1F5F9"))
                fin_item.setToolTip("")
        self.table.blockSignals(False)

        self.is_dirty = True
        self.update_live_totals()

    def update_live_totals(self):
        tot_bf = sum(it.get("bf_qty", 0.0) * it.get("price_ttc", 0.0) for it in self.articles_data)
        tot_lu = sum(it.get("lu_qty", 0.0) * it.get("price_ttc", 0.0) for it in self.articles_data)
        tot_di = sum(it.get("di_qty", 0.0) * it.get("price_ttc", 0.0) for it in self.articles_data)
        tot_grand = tot_bf + tot_lu + tot_di

        if hasattr(self, "lbl_sum_bf"):
            self.lbl_sum_bf.setText(f"{tot_bf:,.2f} دج")
            self.lbl_sum_lu.setText(f"{tot_lu:,.2f} دج")
            self.lbl_sum_di.setText(f"{tot_di:,.2f} دج")
            self.lbl_sum_grand.setText(f"{tot_grand:,.2f} دج")

    def commit_active_cell_editor(self):
        """تثبيت محتوى أي محرر خلية مفتوح حالياً في الجدول لضمان فحص التغييرات بدقة"""
        if hasattr(self, "table") and self.table:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            fw = app.focusWidget() if app else self.table.focusWidget()
            if not fw:
                fw = self.table.focusWidget()
            if fw and isinstance(fw, QLineEdit):
                row = fw.property("cell_row")
                col = fw.property("cell_col")
                if row is not None and col is not None:
                    txt = fw.text().strip()
                    item = self.table.item(row, col)
                    if item:
                        item.setText(txt)
                        self.on_table_item_changed(item)

    def has_unsaved_changes(self) -> bool:
        """هل توجد تعديلات غير محفوظة في ورقة الاستهلاك الحالية؟"""
        self.commit_active_cell_editor()
        return bool(getattr(self, "is_dirty", False))

    def validate_no_negative_stock(self) -> Tuple[bool, List[str]]:
        """التحقق من عدم وجود أي مادة تتجاوز مخرجاتها الكمية المتوفرة"""
        violations = []
        for it in self.articles_data:
            init = float(it.get("initial_stock", 0.0) or 0.0)
            sup = float(it.get("supply_qty", 0.0) or 0.0)
            li = float(it.get("loan_in_qty", 0.0) or 0.0)
            avail = init + sup + li

            bf = float(it.get("bf_qty", 0.0) or 0.0)
            lu = float(it.get("lu_qty", 0.0) or 0.0)
            di = float(it.get("di_qty", 0.0) or 0.0)
            lo = float(it.get("loan_out_qty", 0.0) or 0.0)
            tot_out = bf + lu + di + lo

            if tot_out > 1e-6 and tot_out > (avail + 1e-6):
                name = it.get("name", f"المادة رقم {it.get('id')}")
                deficit = tot_out - avail
                unit = it.get("unit", "")
                violations.append(
                    f"• {name}: المتاح ({avail:g} {unit}) | المطلوب صرفه ({tot_out:g} {unit}) | العجز ({deficit:g} {unit})"
                )

        return (len(violations) == 0, violations)

    def save_changes(self, for_date: str = None) -> bool:
        """حفظ التغييرات برمجياً وإرجاع True عند النجاح"""
        if getattr(self, "is_directorate", False):
            QMessageBox.information(self, "وضع الرقابة والمتابعة", "حساب المديرية مخصص للاطلاع والتتبع الرقابي فقط ولا يمكن تعديل أو حفظ قيم الاستهلاك.")
            return False
        self.commit_active_cell_editor()
        date_str = for_date or self.dt_picker.date().toString("yyyy-MM-dd")

        valid, violations = self.validate_no_negative_stock()
        if not valid:
            items_str = "\n".join(violations[:8])
            extra = f"\n... و {len(violations) - 8} مواد أخرى" if len(violations) > 8 else ""
            QMessageBox.critical(
                self,
                "خطأ: عجز في المخزون (المخرجات تتجاوز الكمية المتوفرة) ⛔",
                f"لا يمكن حفظ التغييرات لأن الكميات المصروفة تتجاوز المخزون المتوفر للمواد التالية:\n\n"
                f"{items_str}{extra}\n\n"
                "يرجى تصحيح الكميات لتفادي الرصيد السالب."
            )
            return False

        try:
            notes_val = self.txt_daily_notes.text().strip() if hasattr(self, "txt_daily_notes") and self.txt_daily_notes else ""
            self.stock_svc.save_daily_sheet_full(date_str, self.articles_data, tickets_input=None, menu_input=None, notes=notes_val)
            self.is_dirty = False
            self.daily_sheet_saved.emit()
            return True
        except InsufficientStockError as e:
            QMessageBox.critical(self, "منع المخزون السالب ⛔", f"لا يمكن الحفظ:\n{e}")
            return False
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", f"حدث خطأ أثناء حفظ ورقة الاستهلاك:\n{e}")
            return False

    def discard_changes(self):
        """تجاهل التغييرات وإعادة تحميل البيانات الأصلية من قاعدة البيانات"""
        self.is_dirty = False
        self.load_daily_sheet()

    def on_switch_to_general_info_clicked(self):
        if self.has_unsaved_changes():
            res = prompt_save_changes(
                self,
                title="تنبيه: حفظ ورقة الاستهلاك ⚠️",
                message="هل تريد حفظ التغييرات قبل الانتقال لواجهة معلومات عامة؟",
                detail="تم تعديل بيانات ورقة هذا اليوم دون الضغط على زر الحفظ."
            )
            if res == "YES":
                if not self.save_changes():
                    return
            elif res == "CANCEL":
                return
            else:
                self.discard_changes()

        self.open_general_info_requested.emit(self.dt_picker.date().toString("yyyy-MM-dd"))

    def save_daily_sheet_silent(self):
        if not self.has_unsaved_changes():
            return
        if getattr(self, "is_directorate", False):
            return
        self.commit_active_cell_editor()
        valid, violations = self.validate_no_negative_stock()
        if not valid:
            print(f"Notice silent save blocked: negative stock detected for {len(violations)} items")
            return
        date_str = self.dt_picker.date().toString("yyyy-MM-dd")
        try:
            notes_val = self.txt_daily_notes.text().strip() if hasattr(self, "txt_daily_notes") and self.txt_daily_notes else ""
            self.stock_svc.save_daily_sheet_full(date_str, self.articles_data, tickets_input=None, menu_input=None, notes=notes_val)
            self.is_dirty = False
            self.daily_sheet_saved.emit()
        except Exception as e:
            print(f"Notice silent save: {e}")

    def save_daily_sheet(self):
        self.commit_active_cell_editor()
        date_str = self.dt_picker.date().toString("yyyy-MM-dd")

        if getattr(self, "is_directorate", False):
            QMessageBox.information(self, "وضع الرقابة والمتابعة", "حساب المديرية مخصص للاطلاع والتتبع الرقابي فقط ولا يمكن تعديل أو حفظ قيم الاستهلاك.")
            return

        # فحص صلاحية التعديل
        is_editable, msg = self.date_lock_svc.is_date_editable(
            self.stock_svc.residence_id, date_str, self.is_directorate
        )
        if not is_editable:
            QMessageBox.warning(
                self, "⛔ يوم مقفل للتعديل",
                f"{msg}\n\n"
                "يرجى الاتصال بمديرية الخدمات الجامعية للحصول على ترخيص فتح هذا اليوم."
            )
            return

        # التحقق الصارم من عدم تجاوز المخرجات للكمية المتوفرة (منع المخزون السالب)
        valid, violations = self.validate_no_negative_stock()
        if not valid:
            items_str = "\n".join(violations[:8])
            extra = f"\n... و {len(violations) - 8} مواد أخرى" if len(violations) > 8 else ""
            QMessageBox.critical(
                self,
                "خطأ: عجز في المخزون (المخرجات تتجاوز الكمية المتوفرة) ⛔",
                f"لا يمكن حفظ ورقة الاستهلاك لأن الكميات المصروفة تتجاوز المخزون المتوفر للمواد التالية:\n\n"
                f"{items_str}{extra}\n\n"
                "يرجى تصحيح الكميات بحيث لا تتجاوز المخرجات الكمية المتاحة (مخزون أول مدة + توريد + استعارة)."
            )
            return

        try:
            notes_val = self.txt_daily_notes.text().strip() if hasattr(self, "txt_daily_notes") and self.txt_daily_notes else ""
            self.stock_svc.save_daily_sheet_full(date_str, self.articles_data, tickets_input=None, menu_input=None, notes=notes_val)
            self.is_dirty = False
            self.daily_sheet_saved.emit()
            QMessageBox.information(
                self, "نجاح الحفظ",
                f"تم حفظ ورقة الاستهلاك ليوم ({date_str}) بنجاح!\n"
                f"تم تحديث أرصدة المخزون وسجل الحركات ومصاريف الاستهلاك آلياً."
            )
            self.load_daily_sheet()
        except InsufficientStockError as e:
            QMessageBox.critical(self, "منع المخزون السالب ⛔", f"لا يمكن الحفظ:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", f"حدث خطأ أثناء حفظ ورقة الاستهلاك:\n{e}")

    def _update_date_lock_ui(self, date_str: str):
        """تحديث شريط حالة القفل والتعتيم عند تغيير التاريخ"""
        check = self.date_lock_svc.check_date_permission(
            self.stock_svc.residence_id, date_str, self.is_directorate
        )
        is_editable = check["is_editable"]
        reason = check["reason_code"]
        self._is_date_locked = not is_editable

        # تعتيم خلايا الجدول وإخفاء زر الحفظ عند القفل أو في وضع المديرية
        if self.is_directorate:
            is_editable = False
            self.EDITABLE_COLS = []
            self.btn_save.setEnabled(False)
            self.btn_save.setText("💾 ورقة اليوم وتحديث (للمعاينة والرقابة فقط 🔒)")
            self.btn_save.setToolTip("وضع المديرية: للقراءة والتتبع والرقابة الميدانية فقط دون التعديل على القيم")
            if hasattr(self, "btn_add_art") and self.btn_add_art:
                self.btn_add_art.setEnabled(False)
            if hasattr(self, "txt_daily_notes") and self.txt_daily_notes:
                self.txt_daily_notes.setReadOnly(True)
        else:
            self.btn_save.setEnabled(is_editable)
            if hasattr(self, "txt_daily_notes") and self.txt_daily_notes:
                self.txt_daily_notes.setReadOnly(not is_editable)
            if hasattr(self, "btn_add_art") and self.btn_add_art:
                self.btn_add_art.setEnabled(is_editable)
        # تعيين خلايا الجدول للقراءة فقط إذا كان اليوم مقفلاً
        editable_cols = self.EDITABLE_COLS if is_editable else []
        self._current_editable_cols = editable_cols
        # إعادة رسم الجدول لتطبيق أعلام القراءة
        self.render_table_page()

        # تحديث شريط الإخطار
        if reason in ("RECENT_WINDOW", "DIRECTORATE_FULL_ACCESS", "ALL_DAYS_OPEN"):
            self.lock_banner.setVisible(False)
        elif reason == "UNLOCKED_BY_DIRECTORATE":
            self.lock_banner.setVisible(True)
            self.lock_banner.setStyleSheet(
                "background-color: rgba(5, 122, 85, 0.25); border: 1px solid #059669; border-radius: 4px;"
            )
            self.lbl_lock_icon.setText("🔓")
            self.lbl_lock_msg.setText(check["message"])
            self.lbl_lock_msg.setStyleSheet("font-size: 12px; color: #34D399; font-weight: bold;")
        elif not is_editable:
            self.lock_banner.setVisible(True)
            self.lock_banner.setStyleSheet(
                "background-color: rgba(239, 68, 68, 0.18); border: 1px solid #EF4444; border-radius: 4px;"
            )
            self.lbl_lock_icon.setText("🔒")
            self.lbl_lock_msg.setText(check["message"])
            self.lbl_lock_msg.setStyleSheet("font-size: 12px; color: #FCA5A5; font-weight: bold;")
        else:
            self.lock_banner.setVisible(False)

    def print_daily_sheet(self):
        from core.print_helper import print_html_report
        date_str = self.dt_picker.date().toString("yyyy-MM-dd")
        html = self.report_gen.generate_daily_voucher_html_v2(date_str)
        print_html_report(self, html, is_landscape=True, job_title=f"ورقة الاستهلاك اليومي - {date_str}", direct_print=False)

    def on_notes_modified(self):
        self.is_dirty = True

    def on_cell_double_clicked(self, row: int, col: int):
        """عند النقر المزدوج على اسم المادة أو وحدتها، يتم فتح نافذة تعديل المادة فوراً"""
        if col in (0, 1):
            start_idx, _ = self.pagination.get_slice_range()
            real_idx = start_idx + row
            if real_idx < len(self.filtered_articles):
                art_item = self.filtered_articles[real_idx]
                art_id = art_item.get("id")
                # جلب بيانات المادة الكاملة من قاعدة البيانات
                with self.stock_svc.db.get_connection() as conn:
                    cur = conn.execute("SELECT * FROM articles WHERE id = ?", (art_id,))
                    row_data = cur.fetchone()
                    art_full = dict(row_data) if row_data else art_item

                from ui.widgets.articles_widget import ArticleDialog
                dlg = ArticleDialog(self.stock_svc, article_data=art_full, parent=self)
                if dlg.exec():
                    self.load_daily_sheet()

    def open_add_article_dialog(self):
        """إضافة مادة غذائية جديدة مباشرة من شاشة الاستهلاك اليومي"""
        from ui.widgets.articles_widget import ArticleDialog
        dlg = ArticleDialog(self.stock_svc, article_data=None, parent=self)
        if dlg.exec():
            self.load_daily_sheet()

    def set_date(self, qdate: QDate):
        if hasattr(self, 'dt_picker') and qdate and qdate.isValid():
            self.dt_picker.setDate(qdate)

    def set_residence(self, r_id: int, r_name: str = ''):
        self.stock_svc.set_residence(r_id)
        self.meals_svc.set_residence(r_id)
        if hasattr(self, 'report_gen'):
            self.report_gen.set_residence(r_id, r_name)
        self.load_daily_sheet()
