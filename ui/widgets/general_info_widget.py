try:

    from core.time_service import TimeService

except Exception:

    TimeService = None

import math

from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,

    QPushButton, QDateEdit, QSpinBox, QDoubleSpinBox, QMessageBox,

    QScrollArea, QGridLayout, QLineEdit, QFileDialog, QAbstractScrollArea

)

from PyQt6.QtCore import Qt, QDate, pyqtSignal, QObject, QEvent, QTimer

from PyQt6.QtGui import QTextDocument, QValidator

from PyQt6.QtPrintSupport import QPrinter, QPrintDialog



from core.stock_service import StockService

from core.meals_service import MealsService

from reports.report_generator import ReportGenerator

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



class TicketSpinBoxKeyFilter(QObject):

    """مرشح التنقل بلوحة المفاتيح بنمط إكسل لشبكة إدخال التذاكر وحماية عجلة الفأرة"""

    def __init__(self, owner, row_idx: int, col_idx: int):

        super().__init__(owner)

        self.owner = owner

        self.row_idx = row_idx

        self.col_idx = col_idx



    def eventFilter(self, watched, event):

        if event.type() in (QEvent.Type.Wheel, QEvent.Wheel):

            p = watched.parent() if hasattr(watched, 'parent') else None

            while p:

                if isinstance(p, QAbstractScrollArea):

                    p.wheelEvent(event)

                    return True

                p = p.parent()

            event.ignore()

            return True



        if event.type() == QEvent.Type.KeyPress:

            key = event.key()

            mods = event.modifiers()



            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):

                direction = "UP" if (mods & Qt.KeyboardModifier.ShiftModifier) else "DOWN"

                self.owner.navigate_ticket_cells(self.row_idx, self.col_idx, direction)

                return True

            elif key == Qt.Key.Key_Tab:

                direction = "PREV" if (mods & Qt.KeyboardModifier.ShiftModifier) else "NEXT"

                self.owner.navigate_ticket_cells(self.row_idx, self.col_idx, direction)

                return True

            elif key == Qt.Key.Key_Backtab:

                self.owner.navigate_ticket_cells(self.row_idx, self.col_idx, "PREV")

                return True

        return super().eventFilter(watched, event)



class TicketCountSpinBox(QSpinBox):

    """

    حقل إدخال مخصص لتعداد التذاكر:

    يظهر فارغاً تماماً عندما تكون القيمة 0 لتسهيل وتسريع الإدخال البصري،

    ويقبل التعديل المباشر أو مسح الرقم ليعود فارغاً وقيمته 0.

    محمي تماماً من التغيير العرضي عند تدوير عجلة الفأرة، وتمرر الحركة لتحريك الشاشة.

    """

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setRange(0, 99999)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.setFixedHeight(38)



    def wheelEvent(self, event):

        p = self.parent()

        while p:

            if isinstance(p, QAbstractScrollArea):

                p.wheelEvent(event)

                return

            p = p.parent()

        event.ignore()



    def textFromValue(self, val: int) -> str:

        return "" if val == 0 else str(val)



    def valueFromText(self, text: str) -> int:

        t = text.strip()

        if not t:

            return 0

        try:

            return int(t)

        except Exception:

            return 0



    def validate(self, text: str, pos: int):

        if not text.strip():

            return (QValidator.State.Acceptable, text, pos)

        return super().validate(text, pos)



    def fixup(self, text: str) -> str:

        if not text.strip():

            return ""

        return super().fixup(text)



class NoWheelDoubleSpinBox(QDoubleSpinBox):

    """حقل إدخال مبالغ ومصاريف يمنع تغيير القيمة عند تدوير عجلة الفأرة ويوجه التمرير للشاشة"""

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)



    def wheelEvent(self, event):

        p = self.parent()

        while p:

            if isinstance(p, QAbstractScrollArea):

                p.wheelEvent(event)

                return

            p = p.parent()

        event.ignore()



class GeneralInfoWidget(QWidget):

    """

    واجهة معلومات عامة وتعداد التذاكر (مفصولة ومستقلة تماماً عن ورقة الاستهلاك اليومي)

    تتضمن:

    1. مجاميع المصاريف اليومية (محسوبة آلياً من ورقة الاستهلاك)

    2. تعداد التذاكر لجميع الفئات (طلبة، عمال، أساتذة، ضيوف، مجان) للوجبات الثلاث

    3. معدل الوجبات وتكلفة الوجبات وتكلفة إطعام الطالب اليومية

    4. قائمة الأكل المقدم (المنيو اليومي: فطور، غداء، عشاء)

    """



    general_info_saved = pyqtSignal()

    open_daily_sheet_requested = pyqtSignal(str)



    def __init__(self, stock_service: StockService, meals_service: MealsService, report_gen: ReportGenerator, parent=None, is_directorate: bool = False, current_user: dict = None):

        super().__init__(parent)

        self.stock_svc = stock_service

        self.meals_svc = meals_service

        self.report_gen = report_gen

        self.is_directorate = is_directorate

        self.current_user = current_user or {}



        self.day_buttons = {}

        self.ticket_inputs = {}

        self.row_totals = {}

        self.tot_bf_exp = 0.0

        self.tot_lu_exp = 0.0

        self.tot_di_exp = 0.0

        self.grand_exp = 0.0

        self.is_dirty = False

        self.is_loading = False

        self.current_loaded_date = (TimeService.current_qdate() if TimeService else QDate.currentDate())



        self.init_ui()

        self.load_data()

        self.apply_directorate_restrictions()



    def init_ui(self):

        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(12, 10, 12, 12)

        root_layout.setSpacing(8)



        # -------------------------------------------------------------

        # 1. شريط التحكم والترويسة العلوية

        # -------------------------------------------------------------

        top_bar = QFrame()

        top_bar.setObjectName("GeneralInfoTopBar")

        top_bar.setFixedHeight(48)

        self.top_bar = top_bar

        tb_layout = QHBoxLayout(top_bar)

        tb_layout.setContentsMargins(12, 4, 12, 4)

        tb_layout.setSpacing(10)



        self.lbl_day_name = QLabel(f"معلومات عامة ليوم : {get_arabic_weekday(TimeService.current_qdate() if TimeService else QDate.currentDate())}")

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



        btn_to_daily = QPushButton("📋 ورقة الاستهلاك اليومي")

        btn_to_daily.setProperty("class", "btn-secondary")

        btn_to_daily.setStyleSheet("padding: 6px 12px; font-weight: bold;")

        btn_to_daily.clicked.connect(self.on_switch_to_daily_sheet_clicked)

        tb_layout.addWidget(btn_to_daily)



        self.btn_print = QPushButton("🖨️ طباعة المطبوعة الرسمية")

        self.btn_print.setProperty("class", "btn-secondary")

        self.btn_print.setStyleSheet("padding: 6px 14px; font-weight: bold;")

        self.btn_print.clicked.connect(self.print_report)

        tb_layout.addWidget(self.btn_print)



        if self.is_directorate:
            self.btn_cloud_sync = QPushButton("☁️ قراءة وتحديث من السحابة ⟳")
            self.btn_cloud_sync.setProperty("class", "btn-secondary")
            self.btn_cloud_sync.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #38BDF8); color: #FFFFFF; font-size: 12px; font-weight: bold; border-radius: 6px; padding: 6px 14px; border: 1px solid #7DD3FC;")
            self.btn_cloud_sync.setToolTip("قراءة أحدث البيانات لهذه الإقامة مباشرة من السحابة وتحديث الشاشة فورياً")
            self.btn_cloud_sync.clicked.connect(self.pull_all_days_from_cloud)
            tb_layout.addWidget(self.btn_cloud_sync)
        else:
            self.btn_cloud_sync = QPushButton("☁️ سحب كافة الأيام من السحابة 📥")
            self.btn_cloud_sync.setProperty("class", "btn-secondary")
            self.btn_cloud_sync.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981); color: #FFFFFF; font-size: 12px; font-weight: bold; border-radius: 6px; padding: 6px 14px; border: 1px solid #34D399;")
            self.btn_cloud_sync.setToolTip("سحب واسترجاع كافة الأيام السابقة والبيانات المخزونة في السحابة ووضعها في قاعدة البيانات المحلية (مفيد عند تثبيت البرنامج في حاسوب جديد)")
            self.btn_cloud_sync.clicked.connect(self.pull_all_days_from_cloud)
            tb_layout.addWidget(self.btn_cloud_sync)

        self.btn_save = QPushButton("💾 حفظ معلومات عامة")

        self.btn_save.setProperty("class", "btn-primary")

        self.btn_save.setStyleSheet("padding: 6px 18px; font-weight: bold;")

        self.btn_save.clicked.connect(self.save_data)

        if self.is_directorate:

            self.btn_save.setEnabled(False)

            self.btn_save.setText("💾 حفظ معلومات عامة (للمعاينة والرقابة فقط 🔒)")

            self.btn_save.setToolTip("وضع المديرية: للقراءة والاطلاع والرقابة فقط دون إمكانية تعديل التذاكر أو المصاريف")

        tb_layout.addWidget(self.btn_save)



        root_layout.addWidget(top_bar)



        # شريط تنبيه خاص بوضع المديرية العامة (الإطلاع والتتبع فقط)

        self.lbl_directorate_banner = QLabel(

            "👁️ وضع الرقابة والمتابعة للمديرية: شاشة تعداد التذاكر ومصاريف الوجبات للقراءة والتدقيق والتتبع لجميع الإقامات (القيم مقفلة للمعاينة فقط دون إمكانية التعديل)."

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



        # -------------------------------------------------------------

        # 2. شريط أيام الشهر (أرقام فقط من 01 إلى 31)

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

        # 3. المنطقة الرئيسية داخل ScrollArea بمساحة واسعة وتصميم منظم

        # -------------------------------------------------------------

        main_scroll = QScrollArea()

        main_scroll.setWidgetResizable(True)

        main_scroll.setFrameShape(QFrame.Shape.NoFrame)



        scroll_content = QWidget()

        sc_layout = QHBoxLayout(scroll_content)

        sc_layout.setContentsMargins(0, 4, 0, 4)

        sc_layout.setSpacing(14)



        # =============================================================

        # الجانب الأيمن: التذاكر وقائمة الطعام (الأكثر تفاعلاً)

        # =============================================================

        right_panel = QVBoxLayout()

        right_panel.setSpacing(12)



        self.ticket_hdr_labels = []

        self.cat_labels = []

        self.menu_labels = []

        self.exp_labels = []

        self.cost_labels = []



        # بطاقة 1: تعداد التذاكر

        tickets_card = QFrame()

        self.tickets_card = tickets_card

        tc_layout = QVBoxLayout(tickets_card)

        tc_layout.setContentsMargins(16, 14, 16, 14)

        tc_layout.setSpacing(10)



        tc_header = QLabel("🎫 تعداد التذاكر (المستفيدين من الإطعام)")

        self.tc_header = tc_header

        tc_layout.addWidget(tc_header)



        grid_tickets = QGridLayout()

        grid_tickets.setHorizontalSpacing(10)

        grid_tickets.setVerticalSpacing(8)



        # رؤوس أعمدة جدول التذاكر

        headers = ["الفئة المستفيدة", "فطور الصباح", "وجبة الغداء", "وجبة العشاء", "المجموع"]

        for ci, h_title in enumerate(headers):

            h_lbl = QLabel(h_title)

            h_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.ticket_hdr_labels.append(h_lbl)

            grid_tickets.addWidget(h_lbl, 0, ci)



        categories = [

            ("طلبة", "students"),

            ("عمال", "staff"),

            ("أساتذة", "professors"),

            ("ضيوف", "guests"),

            ("مجان", "free")

        ]



        for ri, (cat_label, cat_key) in enumerate(categories, 1):

            lbl_cat = QLabel(cat_label)

            self.cat_labels.append(lbl_cat)

            grid_tickets.addWidget(lbl_cat, ri, 0)



            for ci, meal in enumerate(["bf", "lu", "di"], 1):

                spn = TicketCountSpinBox()

                spn.setStyleSheet("""

                    QSpinBox {

                        padding: 4px; font-size: 15px; font-weight: bold;

                        border: 1px solid #CBD5E1; border-radius: 4px; background: #FFFFFF;

                    }

                    QSpinBox:focus { border: 1.5px solid #0D9488; background: #F0FDFA; }

                """)

                spn.valueChanged.connect(self.recalc_stats)

                spn.valueChanged.connect(self.on_input_modified)

                flt = TicketSpinBoxKeyFilter(self, ri - 1, ci - 1)

                spn.installEventFilter(flt)

                if hasattr(spn, "lineEdit") and spn.lineEdit():

                    spn.lineEdit().installEventFilter(flt)

                grid_tickets.addWidget(spn, ri, ci)

                self.ticket_inputs[f"{meal}_{cat_key}"] = spn



            # مجموع السطر لكل فئة

            lbl_row_tot = QLabel("0")

            lbl_row_tot.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl_row_tot.setStyleSheet("font-weight: bold; font-size: 12px; color: #0F2D25; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px;")

            grid_tickets.addWidget(lbl_row_tot, ri, 4)

            self.row_totals[cat_key] = lbl_row_tot



        # سطر المجموع النهائي أسفل الأعمدة

        lbl_tot_title = QLabel("المجموع الكلي")

        self.lbl_tot_title = lbl_tot_title

        lbl_tot_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #0F2D25; padding: 6px;")

        grid_tickets.addWidget(lbl_tot_title, 6, 0)



        self.lbl_tot_t_bf = QLabel("0")

        self.lbl_tot_t_bf.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid_tickets.addWidget(self.lbl_tot_t_bf, 6, 1)



        self.lbl_tot_t_lu = QLabel("0")

        self.lbl_tot_t_lu.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid_tickets.addWidget(self.lbl_tot_t_lu, 6, 2)



        self.lbl_tot_t_di = QLabel("0")

        self.lbl_tot_t_di.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid_tickets.addWidget(self.lbl_tot_t_di, 6, 3)



        self.lbl_tot_t_all = QLabel("0")

        self.lbl_tot_t_all.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid_tickets.addWidget(self.lbl_tot_t_all, 6, 4)



        tc_layout.addLayout(grid_tickets)

        right_panel.addWidget(tickets_card)



        # بطاقة 2: قائمة الأكل المقدم (المنيو اليومي)

        menu_card = QFrame()

        self.menu_card = menu_card

        mc_layout = QVBoxLayout(menu_card)

        mc_layout.setContentsMargins(16, 14, 16, 14)

        mc_layout.setSpacing(8)



        mc_header = QLabel("🍲 قائمة الأكل المقدم (المنيو اليومي)")

        self.mc_header = mc_header

        mc_layout.addWidget(mc_header)



        mc_grid = QGridLayout()

        mc_grid.setHorizontalSpacing(10)

        mc_grid.setVerticalSpacing(8)



        lbl_m_bf = QLabel("فطور الصباح:")

        self.menu_labels.append(lbl_m_bf)

        mc_grid.addWidget(lbl_m_bf, 0, 0)

        self.txt_menu_bf = QLineEdit()

        self.txt_menu_bf.setPlaceholderText("حليب، قهوة، خبز، مربى، زبدة...")

        self.txt_menu_bf.textChanged.connect(self.on_input_modified)

        mc_grid.addWidget(self.txt_menu_bf, 0, 1)



        lbl_m_lu = QLabel("وجبة الغداء:")

        self.menu_labels.append(lbl_m_lu)

        mc_grid.addWidget(lbl_m_lu, 1, 0)

        self.txt_menu_lu = QLineEdit()

        self.txt_menu_lu.setPlaceholderText("شوربة، كسكسي باللحم، سلطة، فاكهة موسمية...")

        self.txt_menu_lu.textChanged.connect(self.on_input_modified)

        mc_grid.addWidget(self.txt_menu_lu, 1, 1)



        lbl_m_di = QLabel("وجبة العشاء:")

        self.menu_labels.append(lbl_m_di)

        mc_grid.addWidget(lbl_m_di, 2, 0)

        self.txt_menu_di = QLineEdit()

        self.txt_menu_di.setPlaceholderText("حريرة، أرز بالدجاج، ياغورت، خبز...")

        self.txt_menu_di.textChanged.connect(self.on_input_modified)

        mc_grid.addWidget(self.txt_menu_di, 2, 1)



        mc_layout.addLayout(mc_grid)

        right_panel.addWidget(menu_card)



        sc_layout.addLayout(right_panel, 6)



        # =============================================================

        # الجانب الأيسر: مجاميع المصاريف ومعدلات التكلفة

        # =============================================================

        left_panel = QVBoxLayout()

        left_panel.setSpacing(12)



        # بطاقة 3: مجاميع المصاريف

        exp_card = QFrame()

        self.exp_card = exp_card

        ec_layout = QVBoxLayout(exp_card)

        ec_layout.setContentsMargins(16, 14, 16, 14)

        ec_layout.setSpacing(10)



        header_row = QHBoxLayout()

        ec_header = QLabel("💰 مجاميع المصاريف اليومية")

        self.ec_header = ec_header

        header_row.addWidget(ec_header, 1)



        btn_reload_sheet_exp = QPushButton("🔄 استيراد من ورقة الاستهلاك")

        btn_reload_sheet_exp.setProperty("class", "btn-secondary")

        btn_reload_sheet_exp.setStyleSheet("font-size: 11px; padding: 4px 8px; font-weight: bold;")

        btn_reload_sheet_exp.setToolTip("إعادة جلب وحساب مجاميع المصاريف مباشرة من الكميات المسجلة في ورقة استهلاك اليوم")

        btn_reload_sheet_exp.clicked.connect(self.import_expenses_from_daily_sheet)

        header_row.addWidget(btn_reload_sheet_exp)



        ec_layout.addLayout(header_row)



        grid_exp = QGridLayout()

        grid_exp.setHorizontalSpacing(10)

        grid_exp.setVerticalSpacing(8)



        lbl_e_bf = QLabel("مجموع مصاريف فطور الصباح :")

        self.exp_labels.append(lbl_e_bf)

        grid_exp.addWidget(lbl_e_bf, 0, 0)

        self.spn_exp_bf = NoWheelDoubleSpinBox()

        self.spn_exp_bf.setRange(0.0, 99999999.0)

        self.spn_exp_bf.setDecimals(2)

        self.spn_exp_bf.setSuffix(" دج")

        self.spn_exp_bf.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.spn_exp_bf.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)

        self.spn_exp_bf.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.spn_exp_bf.valueChanged.connect(self.recalc_stats)

        self.spn_exp_bf.valueChanged.connect(self.on_input_modified)

        grid_exp.addWidget(self.spn_exp_bf, 0, 1)



        lbl_e_lu = QLabel("مجموع مصاريف وجبة الغداء :")

        self.exp_labels.append(lbl_e_lu)

        grid_exp.addWidget(lbl_e_lu, 1, 0)

        self.spn_exp_lu = NoWheelDoubleSpinBox()

        self.spn_exp_lu.setRange(0.0, 99999999.0)

        self.spn_exp_lu.setDecimals(2)

        self.spn_exp_lu.setSuffix(" دج")

        self.spn_exp_lu.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.spn_exp_lu.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)

        self.spn_exp_lu.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.spn_exp_lu.valueChanged.connect(self.recalc_stats)

        self.spn_exp_lu.valueChanged.connect(self.on_input_modified)

        grid_exp.addWidget(self.spn_exp_lu, 1, 1)



        lbl_e_di = QLabel("مجموع مصاريف وجبة العشاء :")

        self.exp_labels.append(lbl_e_di)

        grid_exp.addWidget(lbl_e_di, 2, 0)

        self.spn_exp_di = NoWheelDoubleSpinBox()

        self.spn_exp_di.setRange(0.0, 99999999.0)

        self.spn_exp_di.setDecimals(2)

        self.spn_exp_di.setSuffix(" دج")

        self.spn_exp_di.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.spn_exp_di.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)

        self.spn_exp_di.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.spn_exp_di.valueChanged.connect(self.recalc_stats)

        self.spn_exp_di.valueChanged.connect(self.on_input_modified)

        grid_exp.addWidget(self.spn_exp_di, 2, 1)



        line_e = QFrame()

        line_e.setFrameShape(QFrame.Shape.HLine)

        self.line_e = line_e

        grid_exp.addWidget(line_e, 3, 0, 1, 2)



        lbl_e_tot = QLabel("المجموع الكلي للمصاريف =")

        self.exp_labels.append(lbl_e_tot)

        grid_exp.addWidget(lbl_e_tot, 4, 0)

        self.lbl_exp_total = QLabel("0.00 دج")

        self.lbl_exp_total.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        grid_exp.addWidget(self.lbl_exp_total, 4, 1)



        ec_layout.addLayout(grid_exp)



        lbl_exp_hint = QLabel("💡 تُحسب هذه المصاريف تلقائياً من ورقة الاستهلاك اليومي. ويمكنك أيضاً تعديلها أو إدخالها يدوياً هنا مباشرة وتُحسب التكاليف والمعدلات فورياً.")

        lbl_exp_hint.setWordWrap(True)

        self.lbl_exp_hint = lbl_exp_hint

        ec_layout.addWidget(lbl_exp_hint)



        left_panel.addWidget(exp_card)



        # بطاقة 4: معدل الوجبات والتكلفة

        cost_card = QFrame()

        self.cost_card = cost_card

        cc_layout = QVBoxLayout(cost_card)

        cc_layout.setContentsMargins(16, 14, 16, 14)

        cc_layout.setSpacing(10)



        cc_header = QLabel("📈 معدل الوجبات والتكلفة اليومية")

        self.cc_header = cc_header

        cc_layout.addWidget(cc_header)



        grid_cost = QGridLayout()

        grid_cost.setHorizontalSpacing(10)

        grid_cost.setVerticalSpacing(8)



        lbl_c_avg = QLabel("معدل الوجبات المقدمة :")

        self.cost_labels.append(lbl_c_avg)

        grid_cost.addWidget(lbl_c_avg, 0, 0)

        self.lbl_avg_meals = QLabel("0.0")

        self.lbl_avg_meals.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        grid_cost.addWidget(self.lbl_avg_meals, 0, 1)



        lbl_c_bf = QLabel("تكلفة فطور الصباح :")

        self.cost_labels.append(lbl_c_bf)

        grid_cost.addWidget(lbl_c_bf, 1, 0)

        self.lbl_cost_bf = QLabel("0.00 دج")

        self.lbl_cost_bf.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        grid_cost.addWidget(self.lbl_cost_bf, 1, 1)



        lbl_c_lu = QLabel("تكلفة وجبـة الغذاء :")

        self.cost_labels.append(lbl_c_lu)

        grid_cost.addWidget(lbl_c_lu, 2, 0)

        self.lbl_cost_lu = QLabel("0.00 دج")

        self.lbl_cost_lu.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        grid_cost.addWidget(self.lbl_cost_lu, 2, 1)



        lbl_c_di = QLabel("تكلفة وجبة العشاء :")

        self.cost_labels.append(lbl_c_di)

        grid_cost.addWidget(lbl_c_di, 3, 0)

        self.lbl_cost_di = QLabel("0.00 دج")

        self.lbl_cost_di.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        grid_cost.addWidget(self.lbl_cost_di, 3, 1)



        line_c = QFrame()

        line_c.setFrameShape(QFrame.Shape.HLine)

        self.line_c = line_c

        grid_cost.addWidget(line_c, 4, 0, 1, 2)



        lbl_c_daily = QLabel("تكلفة الوجبة اليومية :")

        self.cost_labels.append(lbl_c_daily)

        grid_cost.addWidget(lbl_c_daily, 5, 0)

        self.lbl_cost_daily = QLabel("0.00 دج")

        self.lbl_cost_daily.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        grid_cost.addWidget(self.lbl_cost_daily, 5, 1)



        cc_layout.addLayout(grid_cost)

        left_panel.addWidget(cost_card)



        sc_layout.addLayout(left_panel, 4)



        main_scroll.setWidget(scroll_content)

        root_layout.addWidget(main_scroll)

        from ui.common_filters import SmoothScrollFilter

        self.smooth_scroll = SmoothScrollFilter(main_scroll, scroll_step=95, duration_ms=200)



        self.refresh_theme()



    def navigate_ticket_cells(self, curr_row: int, curr_col: int, direction: str):

        """التنقل بين حقول إدخال التذاكر بنمط إكسل"""

        target_row = curr_row

        target_col = curr_col



        if direction == "DOWN":

            target_row = min(4, curr_row + 1)

        elif direction == "UP":

            target_row = max(0, curr_row - 1)

        elif direction == "NEXT":

            if curr_col + 1 < 3:

                target_col = curr_col + 1

            else:

                if curr_row + 1 < 5:

                    target_row = curr_row + 1

                    target_col = 0

        elif direction == "PREV":

            if curr_col - 1 >= 0:

                target_col = curr_col - 1

            else:

                if curr_row - 1 >= 0:

                    target_row = curr_row - 1

                    target_col = 2



        categories = ["students", "staff", "professors", "guests", "free"]

        meals = ["bf", "lu", "di"]

        target_key = f"{meals[target_col]}_{categories[target_row]}"

        spn = self.ticket_inputs.get(target_key)

        if spn:

            spn.setFocus()

            if hasattr(spn, "lineEdit") and spn.lineEdit():

                QTimer.singleShot(0, spn.lineEdit().selectAll)

            else:

                QTimer.singleShot(0, spn.selectAll)



    def select_day(self, day: int):

        curr_dt = self.dt_picker.date()

        max_d = curr_dt.daysInMonth()

        if day <= max_d:

            new_date = QDate(curr_dt.year(), curr_dt.month(), day)

            self.dt_picker.setDate(new_date)



    def set_date_from_str(self, date_str: str):

        qd = QDate.fromString(date_str, "yyyy-MM-dd")

        if qd.isValid():

            self.dt_picker.setDate(qd)



    def update_day_buttons_style(self):

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

        """تحديث كامل عناصر واجهة معلومات عامة عند تغيير المظهر العام"""

        from ui.theme import ThemeManager

        is_dark = ThemeManager.is_dark_mode()

        c_bg = ThemeManager.get_color("card_bg")

        c_border = ThemeManager.get_color("card_border")

        header_bg = ThemeManager.get_color("card_header_bg")

        in_bg = ThemeManager.get_color("input_bg")

        in_fg = ThemeManager.get_color("input_text")

        in_border = ThemeManager.get_color("input_border")

        text_h = ThemeManager.get_color("text_heading")

        text_p = ThemeManager.get_color("text_primary")

        text_s = ThemeManager.get_color("text_secondary")



        # 1. Top bar

        if hasattr(self, "top_bar") and self.top_bar:

            self.top_bar.setStyleSheet(f"""

                QFrame#GeneralInfoTopBar {{

                    background: {c_bg};

                    border: 1px solid {c_border};

                    border-radius: 8px;

                }}

            """)

        if hasattr(self, "lbl_day_name") and self.lbl_day_name:

            self.lbl_day_name.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {text_h};")



        # 2. Day buttons

        self.update_day_buttons_style()



        # 3. Cards styling

        card_style = f"""

            QFrame {{

                background: {c_bg};

                border: 1px solid {c_border};

                border-radius: 8px;

            }}

        """

        for card in [getattr(self, "tickets_card", None),

                     getattr(self, "menu_card", None),

                     getattr(self, "exp_card", None),

                     getattr(self, "cost_card", None)]:

            if card:

                card.setStyleSheet(card_style)



        header_style = f"""

            font-size: 14px;

            font-weight: bold;

            color: {text_h};

            background: {header_bg};

            padding: 8px 12px;

            border-radius: 6px;

            border: 1px solid {c_border};

        """

        for hdr in [getattr(self, "tc_header", None),

                    getattr(self, "mc_header", None),

                    getattr(self, "ec_header", None),

                    getattr(self, "cc_header", None)]:

            if hdr:

                hdr.setStyleSheet(header_style)



        # 4. Ticket headers & categories

        th_bg = "#0F172A" if is_dark else "#F1F5F9"

        th_fg = "#F1F5F9" if is_dark else "#1E293B"

        for h_lbl in getattr(self, "ticket_hdr_labels", []):

            h_lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {th_fg}; background: {th_bg}; border-radius: 4px; padding: 6px;")



        for c_lbl in getattr(self, "cat_labels", []):

            c_lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {text_p}; padding-right: 6px;")



        # SpinBoxes in tickets

        for spn in self.ticket_inputs.values():

            spn.setStyleSheet(f"""

                QSpinBox {{

                    padding: 4px; font-size: 15px; font-weight: bold;

                    border: 1px solid {in_border}; border-radius: 4px;

                    background: {in_bg}; color: {in_fg};

                }}

                QSpinBox:focus {{

                    border: 1.5px solid #0D9488;

                    background: {'#132E2B' if is_dark else '#F0FDFA'};

                }}

            """)



        # Row totals

        row_tot_bg = "#0F172A" if is_dark else "#F8FAFC"

        row_tot_fg = "#38BDF8" if is_dark else "#0F2D25"

        for lbl in self.row_totals.values():

            lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {row_tot_fg}; background: {row_tot_bg}; border: 1px solid {c_border}; border-radius: 4px; padding: 4px;")



        if hasattr(self, "lbl_tot_title") and self.lbl_tot_title:

            self.lbl_tot_title.setStyleSheet(f"font-weight: bold; font-size: 15px; color: {text_h}; padding: 6px;")



        # Totals columns

        if hasattr(self, "lbl_tot_t_bf") and self.lbl_tot_t_bf:

            if is_dark:

                self.lbl_tot_t_bf.setStyleSheet("font-weight: bold; font-size: 15px; color: #2DD4BF; background: #132E2B; border: 1.5px solid #134E4A; border-radius: 4px; padding: 5px;")

            else:

                self.lbl_tot_t_bf.setStyleSheet("font-weight: bold; font-size: 15px; color: #0D9488; background: #F0FDFA; border: 1.5px solid #CCFBF1; border-radius: 4px; padding: 5px;")



        if hasattr(self, "lbl_tot_t_lu") and self.lbl_tot_t_lu:

            if is_dark:

                self.lbl_tot_t_lu.setStyleSheet("font-weight: bold; font-size: 15px; color: #38BDF8; background: #0C2A44; border: 1.5px solid #0369A1; border-radius: 4px; padding: 5px;")

            else:

                self.lbl_tot_t_lu.setStyleSheet("font-weight: bold; font-size: 15px; color: #0284C7; background: #F0F9FF; border: 1.5px solid #BAE6FD; border-radius: 4px; padding: 5px;")



        if hasattr(self, "lbl_tot_t_di") and self.lbl_tot_t_di:

            if is_dark:

                self.lbl_tot_t_di.setStyleSheet("font-weight: bold; font-size: 15px; color: #FB7185; background: #3B1219; border: 1.5px solid #9F1239; border-radius: 4px; padding: 5px;")

            else:

                self.lbl_tot_t_di.setStyleSheet("font-weight: bold; font-size: 15px; color: #E11D48; background: #FFF1F2; border: 1.5px solid #FECDD3; border-radius: 4px; padding: 5px;")



        if hasattr(self, "lbl_tot_t_all") and self.lbl_tot_t_all:

            all_bg = "#0D9488" if is_dark else "#0F2D25"

            self.lbl_tot_t_all.setStyleSheet(f"font-weight: bold; font-size: 16px; color: #FFFFFF; background: {all_bg}; border-radius: 4px; padding: 5px;")



        # 5. Menu Card items

        menu_inp_css = f"padding: 7px 12px; font-size: 14px; border: 1px solid {in_border}; border-radius: 4px; background: {in_bg}; color: {in_fg};"

        for inp in [getattr(self, "txt_menu_bf", None), getattr(self, "txt_menu_lu", None), getattr(self, "txt_menu_di", None)]:

            if inp:

                inp.setStyleSheet(menu_inp_css)



        for lbl in getattr(self, "menu_labels", []):

            lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {text_p};")



        # 6. Expenses Card items

        for lbl in getattr(self, "exp_labels", []):

            lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {text_p};")



        exp_bf_col = "#2DD4BF" if is_dark else "#0D9488"

        exp_lu_col = "#38BDF8" if is_dark else "#0284C7"

        exp_di_col = "#FB7185" if is_dark else "#E11D48"



        if hasattr(self, "spn_exp_bf") and self.spn_exp_bf:

            self.spn_exp_bf.setStyleSheet(f"""

                QDoubleSpinBox {{

                    font-size: 15px; font-weight: bold; color: {exp_bf_col};

                    border: 1px solid {in_border}; border-radius: 4px; padding: 5px 8px; background: {in_bg};

                }}

                QDoubleSpinBox:focus {{ border: 1.5px solid {exp_bf_col}; background: {'#132E2B' if is_dark else '#F0FDFA'}; }}

            """)

        if hasattr(self, "spn_exp_lu") and self.spn_exp_lu:

            self.spn_exp_lu.setStyleSheet(f"""

                QDoubleSpinBox {{

                    font-size: 15px; font-weight: bold; color: {exp_lu_col};

                    border: 1px solid {in_border}; border-radius: 4px; padding: 5px 8px; background: {in_bg};

                }}

                QDoubleSpinBox:focus {{ border: 1.5px solid {exp_lu_col}; background: {'#0C2A44' if is_dark else '#F0F9FF'}; }}

            """)

        if hasattr(self, "spn_exp_di") and self.spn_exp_di:

            self.spn_exp_di.setStyleSheet(f"""

                QDoubleSpinBox {{

                    font-size: 15px; font-weight: bold; color: {exp_di_col};

                    border: 1px solid {in_border}; border-radius: 4px; padding: 5px 8px; background: {in_bg};

                }}

                QDoubleSpinBox:focus {{ border: 1.5px solid {exp_di_col}; background: {'#3B1219' if is_dark else '#FFF1F2'}; }}

            """)



        if hasattr(self, "lbl_exp_total") and self.lbl_exp_total:

            exp_tot_bg = "#0F172A" if is_dark else "#F1F5F9"

            exp_tot_fg = "#38BDF8" if is_dark else "#0F2D25"

            self.lbl_exp_total.setStyleSheet(f"""

                font-size: 18px; font-weight: bold; color: {exp_tot_fg};

                background: {exp_tot_bg}; border: 1px solid {c_border};

                border-radius: 6px; padding: 6px 10px;

            """)



        if hasattr(self, "lbl_exp_hint") and self.lbl_exp_hint:

            hint_bg = "#162235" if is_dark else "#F8FAFC"

            hint_fg = "#94A3B8" if is_dark else "#475569"

            self.lbl_exp_hint.setStyleSheet(f"font-size: 13px; color: {hint_fg}; background: {hint_bg}; border: 1px solid {c_border}; padding: 6px 8px; border-radius: 4px;")



        if hasattr(self, "line_e") and self.line_e:

            self.line_e.setStyleSheet(f"color: {c_border};")

        if hasattr(self, "line_c") and self.line_c:

            self.line_c.setStyleSheet(f"color: {c_border};")



        # 7. Cost Card items

        for lbl in getattr(self, "cost_labels", []):

            lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {text_p};")



        if hasattr(self, "lbl_avg_meals") and self.lbl_avg_meals:

            if is_dark:

                self.lbl_avg_meals.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8; background: #0C2A44; border: 1px solid #0369A1; border-radius: 4px; padding: 4px 10px;")

            else:

                self.lbl_avg_meals.setStyleSheet("font-size: 16px; font-weight: bold; color: #0284C7; background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 4px; padding: 4px 10px;")



        for lbl in [getattr(self, "lbl_cost_bf", None), getattr(self, "lbl_cost_lu", None), getattr(self, "lbl_cost_di", None)]:

            if lbl:

                lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {text_s};")



        if hasattr(self, "lbl_cost_daily") and self.lbl_cost_daily:

            if is_dark:

                self.lbl_cost_daily.setStyleSheet("""

                    font-size: 17px; font-weight: bold; color: #F87171;

                    background: #3B1219; border: 1px solid #7F1D1D;

                    border-radius: 6px; padding: 5px 10px;

                """)

            else:

                self.lbl_cost_daily.setStyleSheet("""

                    font-size: 17px; font-weight: bold; color: #DC2626;

                    background: #FEF2F2; border: 1px solid #FECACA;

                    border-radius: 6px; padding: 5px 10px;

                """)



    def on_date_changed(self):

        new_date = self.dt_picker.date()

        old_date = getattr(self, "current_loaded_date", None)

        if old_date and old_date != new_date and self.has_unsaved_changes():

            res = prompt_save_changes(

                self,

                title="تنبيه: حفظ معلومات عامة ⚠️",

                message="هل تريد حفظ التغييرات على معلومات هذا اليوم قبل الانتقال ليوم آخر؟",

                detail=f"تم تعديل بيانات تذاكر أو مصاريف يوم ({old_date.toString('yyyy-MM-dd')}) دون الضغط على زر الحفظ."

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

        self.lbl_day_name.setText(f"معلومات عامة ليوم : {weekday_name}")



        curr_day = curr_dt.day()

        self.update_day_buttons_style()

        if hasattr(self, "days_bar_scroll") and curr_day in self.day_buttons:

            self.days_bar_scroll.ensureWidgetVisible(self.day_buttons[curr_day])

        self.load_data()



    def prev_day(self):

        curr = self.dt_picker.date()

        self.dt_picker.setDate(curr.addDays(-1))



    def next_day(self):

        curr = self.dt_picker.date()

        self.dt_picker.setDate(curr.addDays(1))



    def load_data(self):

        self.is_loading = True

        date_str = self.dt_picker.date().toString("yyyy-MM-dd")

        data = self.stock_svc.get_daily_sheet_data(date_str)



        # 1. تحديث المصاريف

        self.tot_bf_exp = data.get("tot_bf_expense", 0.0)

        self.tot_lu_exp = data.get("tot_lu_expense", 0.0)

        self.tot_di_exp = data.get("tot_di_expense", 0.0)

        self.grand_exp = data.get("grand_total_expense", 0.0)



        self.spn_exp_bf.blockSignals(True)

        self.spn_exp_lu.blockSignals(True)

        self.spn_exp_di.blockSignals(True)

        self.spn_exp_bf.setValue(self.tot_bf_exp)

        self.spn_exp_lu.setValue(self.tot_lu_exp)

        self.spn_exp_di.setValue(self.tot_di_exp)

        self.spn_exp_bf.blockSignals(False)

        self.spn_exp_lu.blockSignals(False)

        self.spn_exp_di.blockSignals(False)



        # 2. ملء بيانات التذاكر

        meals = data.get("meals", {})

        for key, spn in self.ticket_inputs.items():

            spn.blockSignals(True)

            spn.setValue(int(meals.get(key, 0)))

            spn.blockSignals(False)



        # 3. ملء قائمة الطعام

        self.txt_menu_bf.blockSignals(True)

        self.txt_menu_lu.blockSignals(True)

        self.txt_menu_di.blockSignals(True)

        self.txt_menu_bf.setText(meals.get("menu_breakfast") or "")

        self.txt_menu_lu.setText(meals.get("menu_lunch") or "")

        self.txt_menu_di.setText(meals.get("menu_dinner") or "")

        self.txt_menu_bf.blockSignals(False)

        self.txt_menu_lu.blockSignals(False)

        self.txt_menu_di.blockSignals(False)



        self.recalc_stats()

        self.current_loaded_date = self.dt_picker.date()

        self.is_dirty = False

        self.is_loading = False



    def import_expenses_from_daily_sheet(self):

        date_str = self.dt_picker.date().toString("yyyy-MM-dd")

        data = self.stock_svc.get_daily_sheet_data(date_str)

        bf = data.get("tot_bf_expense", 0.0)

        lu = data.get("tot_lu_expense", 0.0)

        di = data.get("tot_di_expense", 0.0)



        self.spn_exp_bf.setValue(bf)

        self.spn_exp_lu.setValue(lu)

        self.spn_exp_di.setValue(di)

        self.recalc_stats()



        if (bf + lu + di) == 0:

            QMessageBox.information(

                self, "تنبيه ورقة الاستهلاك",

                f"لم يتم تسجيل كميات استهلاك (فطور/غداء/عشاء) في ورقة الاستهلاك ليوم ({date_str}).\n"

                f"يمكنك إدخال الكميات في ورقة الاستهلاك، أو إدخال مبالغ المصاريف هنا يدوياً مباشرة."

            )



    def recalc_stats(self):

        cats = ["students", "staff", "professors", "guests", "free"]



        tot_bf_t = sum(self.ticket_inputs[f"bf_{k}"].value() for k in cats)

        tot_lu_t = sum(self.ticket_inputs[f"lu_{k}"].value() for k in cats)

        tot_di_t = sum(self.ticket_inputs[f"di_{k}"].value() for k in cats)



        # مجاميع السطور لكل فئة

        for k in cats:

            row_sum = (self.ticket_inputs[f"bf_{k}"].value() +

                       self.ticket_inputs[f"lu_{k}"].value() +

                       self.ticket_inputs[f"di_{k}"].value())

            if k in self.row_totals:

                self.row_totals[k].setText(str(row_sum))



        self.lbl_tot_t_bf.setText(str(tot_bf_t))

        self.lbl_tot_t_lu.setText(str(tot_lu_t))

        self.lbl_tot_t_di.setText(str(tot_di_t))

        self.lbl_tot_t_all.setText(str(tot_bf_t + tot_lu_t + tot_di_t))



        # معدل الوجبات بدقة تامة مطابق لـ FC09

        tot_lu_di = tot_lu_t + tot_di_t

        if tot_di_t == 0:

            avg_m = float(tot_lu_t)

        elif tot_lu_di > 0:

            avg_m = float(tot_lu_di / 2.0)

        else:

            avg_m = 0.0

        self.lbl_avg_meals.setText(f"{avg_m:g}" if avg_m > 0 else "0")



        # أخذ قيم المصاريف المباشرة من الحقول القابلة للتعديل

        self.tot_bf_exp = self.spn_exp_bf.value()

        self.tot_lu_exp = self.spn_exp_lu.value()

        self.tot_di_exp = self.spn_exp_di.value()

        self.grand_exp = self.tot_bf_exp + self.tot_lu_exp + self.tot_di_exp



        self.lbl_exp_total.setText(f"{self.grand_exp:,.2f} دج")



        cost_bf = (self.tot_bf_exp / tot_bf_t) if tot_bf_t > 0 else 0.0

        cost_lu = (self.tot_lu_exp / tot_lu_t) if tot_lu_t > 0 else 0.0

        cost_di = (self.tot_di_exp / tot_di_t) if tot_di_t > 0 else 0.0

        if tot_di_t > 0 and tot_lu_di > 0:

            stud_daily_cost = self.grand_exp / float(tot_lu_di)

        elif tot_lu_t > 0:

            stud_daily_cost = self.grand_exp / float(tot_lu_t)

        else:

            stud_daily_cost = 0.0



        self.lbl_cost_bf.setText(f"{cost_bf:,.2f} دج")

        self.lbl_cost_lu.setText(f"{cost_lu:,.2f} دج")

        self.lbl_cost_di.setText(f"{cost_di:,.2f} دج")

        self.lbl_cost_daily.setText(f"{stud_daily_cost:,.2f} دج")



    def on_input_modified(self):

        """رصد أي تعديل في حقول الإدخال لتتبع حالة الحفظ"""

        if not getattr(self, "is_loading", False):

            self.is_dirty = True



    def has_unsaved_changes(self) -> bool:

        """هل توجد تعديلات غير محفوظة في شاشة معلومات عامة؟"""

        return bool(getattr(self, "is_dirty", False))



    def on_switch_to_daily_sheet_clicked(self):

        """عند النقر على زر الانتقال لورقة الاستهلاك اليومي"""

        if self.has_unsaved_changes():

            res = prompt_save_changes(

                self,

                title="تنبيه: حفظ معلومات عامة ⚠️",

                message="هل تريد حفظ التغييرات قبل الانتقال لورقة الاستهلاك اليومي؟",

                detail="تم تعديل بيانات تذاكر أو مصاريف هذا اليوم دون الضغط على زر الحفظ."

            )

            if res == "YES":

                if not self.save_changes():

                    return

            elif res == "CANCEL":

                return

            else:

                self.discard_changes()



        self.open_daily_sheet_requested.emit(self.dt_picker.date().toString("yyyy-MM-dd"))



    def save_changes(self, for_date: str = None) -> bool:

        """حفظ التغييرات برمجياً وإرجاع True عند النجاح"""

        if getattr(self, "is_directorate", False):

            QMessageBox.information(self, "وضع الرقابة والمتابعة", "حساب المديرية مخصص للاطلاع والتتبع الرقابي فقط ولا يمكن تعديل أو حفظ تعداد التذاكر أو المصاريف.")

            return False

        date_str = for_date or self.dt_picker.date().toString("yyyy-MM-dd")

        tickets_data = {k: spn.value() for k, spn in self.ticket_inputs.items()}

        menu_data = {

            "menu_breakfast": self.txt_menu_bf.text().strip(),

            "menu_lunch": self.txt_menu_lu.text().strip(),

            "menu_dinner": self.txt_menu_di.text().strip()

        }

        expenses_data = {

            "bf_expense": self.spn_exp_bf.value(),

            "lu_expense": self.spn_exp_lu.value(),

            "di_expense": self.spn_exp_di.value(),

            "grand_total": self.spn_exp_bf.value() + self.spn_exp_lu.value() + self.spn_exp_di.value()

        }



        try:

            self.stock_svc.save_daily_general_info(date_str, tickets_data, menu_data, expenses_input=expenses_data)

            self.is_dirty = False

            self.general_info_saved.emit()

            return True

        except Exception as e:

            QMessageBox.critical(self, "خطأ في الحفظ", f"حدث خطأ أثناء حفظ معلومات عامة:\n{e}")

            return False



    def discard_changes(self):

        """تجاهل التغييرات وإعادة تحميل البيانات الأصلية من قاعدة البيانات"""

        self.is_dirty = False

        self.load_data()



    def save_data(self):

        date_str = self.dt_picker.date().toString("yyyy-MM-dd")

        if self.save_changes():

            # رفع الحزمة الكاملة للإقامة في الخلفية لضمان وصول جميع الأيام المحفوظة مع كافة الأيام السابقة فوراً للسحابة
            import threading
            def _push_all_days():
                try:
                    from core.sync_service import SyncService
                    SyncService(self.stock_svc.db).push_full_residence_data(self.stock_svc.residence_id)
                except Exception:
                    pass
            threading.Thread(target=_push_all_days, daemon=True).start()

            QMessageBox.information(

                self, "نجاح الحفظ والمزامنة السحابية ☁️",

                f"تم حفظ بيانات معلومات عامة وتعداد التذاكر ليوم ({date_str}) بنجاح!\n\n"

                f"☁️ تم رفع وتأمين كافة الأيام السابقة والحالية مباشرة في السحابة لحمايتها من الضياع ومطابقتها مع المديرية فورياً."

            )

            self.load_data()



    def print_report(self):

        from core.print_helper import print_html_report

        date_str = self.dt_picker.date().toString("yyyy-MM-dd")

        html = self.report_gen.generate_daily_voucher_html_v2(date_str)

        print_html_report(self, html, is_landscape=True, job_title=f"ورقة الاستهلاك اليومي - {date_str}", direct_print=False)





    def set_directorate_mode(self, is_directorate: bool):

        self.is_directorate = is_directorate

        self.apply_directorate_restrictions()



    def apply_directorate_restrictions(self):

        """قفل شاشة معلومات عامة وتعداد التذاكر بالكامل للمديرية (للقراءة والتتبع فقط)"""

        if not getattr(self, "is_directorate", False):

            return



        if hasattr(self, "lbl_directorate_banner"):

            self.lbl_directorate_banner.setVisible(True)



        if hasattr(self, "btn_save") and self.btn_save:

            self.btn_save.setEnabled(False)

            self.btn_save.setText("💾 حفظ معلومات عامة (للمعاينة والرقابة فقط 🔒)")

            self.btn_save.setToolTip("وضع المديرية: للقراءة والاطلاع والرقابة فقط دون إمكانية تعديل التذاكر أو المصاريف")



        for spn in self.ticket_inputs.values():

            spn.setReadOnly(True)

            spn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            spn.setToolTip("تعداد التذاكر: للقراءة والتدقيق فقط (لا يمكن للمديرية التعديل)")



        for txt in [getattr(self, "txt_menu_bf", None), getattr(self, "txt_menu_lu", None), getattr(self, "txt_menu_di", None)]:

            if txt:

                txt.setReadOnly(True)

                txt.setToolTip("قائمة الوجبات: للقراءة والمتابعة فقط")



        for spn in [getattr(self, "spn_exp_bf", None), getattr(self, "spn_exp_lu", None), getattr(self, "spn_exp_di", None)]:

            if spn:

                spn.setReadOnly(True)

                spn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

                spn.setToolTip("المصاريف اليومية: للقراءة والتدقيق فقط")

    def pull_all_days_from_cloud(self):
        """سحب واسترجاع كافة الأيام والبيانات من السحابة وتطبيقها محلياً"""
        from PyQt6.QtWidgets import QMessageBox, QProgressDialog
        from PyQt6.QtCore import Qt
        from core.sync_service import SyncService

        r_id = getattr(self.stock_svc, "residence_id", 1)
        res_name = f"الإقامة {r_id}"
        sync_s = SyncService(self.stock_svc.db)

        if not sync_s.is_server_reachable():
            QMessageBox.warning(
                self, "لا يوجد اتصال بالسحابة ☁️",
                "تعذر الاتصال بالخادم السحابي للمديرية.\nيرجى التأكد من توفر شبكة الإنترنت والمحاولة مجدداً."
            )
            return

        prog = QProgressDialog(f"جاري سحب وتحديث كافة الأيام والبيانات من السحابة ({res_name})...", None, 0, 0, self)
        prog.setWindowTitle("مزامنة السحابة المباشرة")
        prog.setWindowModality(Qt.WindowModality.ApplicationModal)
        prog.setCancelButton(None)
        prog.show()
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            res = sync_s.pull_full_residence_data(r_id)
            prog.close()

            if res.get("success"):
                counts = res.get("counts", {})
                m_cnt = counts.get("daily_meals_tracking", 0)
                QMessageBox.information(
                    self, "تم سحب البيانات بنجاح ☁️",
                    f"تم سحب وتحديث كافة الأيام بنجاح من السحابة لـ {res_name}!\n\n"
                    f"• عدد وجبات الأيام المسحوبة: {m_cnt} وجبة\n"
                    f"• وصولات الاستلام (الدخول): {counts.get('entry_vouchers', 0)}\n"
                    f"• وصولات الصرف (الخروج): {counts.get('exit_vouchers', 0)}\n"
                    f"• سجل حركات المخزون: {counts.get('stock_movements', 0)}\n\n"
                    f"تمت مزامنة وتحديث قاعدة البيانات المحلية بالكامل."
                )
                self.load_data()
            else:
                QMessageBox.critical(
                    self, "خطأ في السحب",
                    f"تعذر استرجاع البيانات من السحابة:\n{res.get('error', 'خطأ غير معروف')}"
                )
        except Exception as e:
            prog.close()
            QMessageBox.critical(self, "خطأ غير متوقع", f"حدث خطأ أثناء السحب من السحابة:\n{e}")

    def set_residence(self, residence_id: int):

        self.stock_svc.set_residence(residence_id)

        self.meals_svc.set_residence(residence_id)

        self.load_data()

        self.apply_directorate_restrictions()


    def set_date(self, qdate: QDate):
        if hasattr(self, 'dt_picker') and qdate and qdate.isValid():
            self.dt_picker.setDate(qdate)
