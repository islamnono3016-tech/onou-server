from PyQt6.QtGui import QPixmap, QIcon
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QButtonGroup,
    QStatusBar, QFrame, QComboBox, QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer, QDate, QTime
from database.db_manager import DatabaseManager
import os
from core.stock_service import StockService
from core.meals_service import MealsService
from core.residence_service import ResidenceService
from core.auth_service import AuthService
from core.backup_service import BackupService
from core.network_service import get_local_ip
from core.config import AppConfig
from core.sync_service import SyncWorker, SyncService, AllResidencesSyncThread
from reports.report_generator import ReportGenerator

from ui.widgets.dashboard_widget import DashboardWidget
from ui.widgets.daily_sheet_widget import DailySheetWidget
from ui.widgets.general_info_widget import GeneralInfoWidget
from ui.widgets.residence_loans_widget import ResidenceLoansWidget
from ui.widgets.articles_widget import ArticlesWidget
from ui.widgets.entry_voucher_widget import EntryVoucherWidget
from ui.widgets.exit_voucher_widget import ExitVoucherWidget
from ui.widgets.matrix_tracking_widget import MatrixTrackingWidget
from ui.widgets.trimester_situation_widget import TrimesterSituationWidget
from ui.widgets.reports_widget import ReportsWidget
from ui.widgets.settings_widget import SettingsWidget
from ui.widgets.bon_commande_widget import BonCommandeWidget
from ui.widgets.residence_manager_widget import ResidenceManagerWidget
from ui.widgets.network_settings_dialog import NetworkSettingsDialog
from ui.update_dialog import UpdateDialog
from ui.common_filters import prompt_save_changes

class MainWindow(QMainWindow):
    """
    النافذة الرئيسية لنظام تسيير مخزون الإطعام متعدد الإقامات
    تدعم الإشراف المركزي للمدير العام والتخصيص المستقل لكل إقامة جامعية
    """

    def __init__(self, db_manager: DatabaseManager, current_user: Optional[Dict[str, Any]] = None, network_server=None):
        super().__init__()
        self.db = db_manager
        self.current_user = current_user or {
            "id": 1,
            "username": "admin",
            "full_name": "مدير الخدمات الجامعية (مسؤول النظام)",
            "role": "SUPER_ADMIN",
            "residence_id": None,
            "residence_name": "جميع الإقامات"
        }
        self.network_server = network_server

        self.res_svc = ResidenceService(self.db)
        self.auth_svc = AuthService(self.db)

        # تحديد الإقامة الابتدائية النشطة
        user_res_id = self.current_user.get("residence_id")
        if not user_res_id and self.current_user.get("role") != "SUPER_ADMIN":
            user_res_id = AppConfig.get("residence_id")

        if user_res_id:
            self.current_residence_id = int(user_res_id)
            res_row = self.res_svc.get_residence(self.current_residence_id)
            self.current_residence_name = res_row["name"] if res_row else "الإقامة المخصصة"
        else:
            all_res = self.res_svc.list_residences(only_active=True)
            saved_res_id = self.db.get_setting("last_active_residence_id")
            selected_res = None
            if saved_res_id:
                try:
                    selected_res = self.res_svc.get_residence(int(saved_res_id))
                except Exception:
                    pass
            if not selected_res and all_res:
                selected_res = next((r for r in all_res if r.get("code") == "RES-07" or "العبيدي" in r.get("name", "")), all_res[0])

            if selected_res:
                self.current_residence_id = selected_res["id"]
                self.current_residence_name = selected_res["name"]
            else:
                self.current_residence_id = 1
                self.current_residence_name = "الإقامة الجامعية"

        self.stock_svc = StockService(self.db, residence_id=self.current_residence_id)
        self.meals_svc = MealsService(self.db, residence_id=self.current_residence_id)
        self.report_gen = ReportGenerator(self.db, residence_id=self.current_residence_id)

        self.setWindowTitle("نظام تسيير مخزون الإطعام في الإقامات الجامعية - الربط الموحد 2026")
        self.resize(1320, 840)
        self.setMinimumSize(1024, 620)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.loaded_pages = {0}
        self.dirty_pages = set()
        self.sync_svc = SyncService(self.db)
        self.sync_worker = None
        self.backup_svc = BackupService(self.db)

        # تثبيت مرشح حماية وتثبيت قيم حقول الإدخال عند تحريك عجلة الفأرة على التطبيق كاملاً
        from PyQt6.QtWidgets import QApplication
        q_app = QApplication.instance()
        if q_app and not getattr(q_app, "_wheel_input_protection_installed", False):
            q_app._wheel_input_protection_installed = True
            from ui.common_filters import GlobalSelectAllFilter
            self._global_input_filter = GlobalSelectAllFilter(q_app)
            q_app.installEventFilter(self._global_input_filter)

        # مؤقت الحفظ الاحتياطي التلقائي اليومي لهذا الجهاز (يفحص كل 30 ثانية)
        self.auto_backup_timer = QTimer(self)
        self.auto_backup_timer.timeout.connect(self.check_auto_backup)
        self.auto_backup_timer.start(30000)
        QTimer.singleShot(2500, self.check_auto_backup)

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. الشريط الجانبي (Sidebar)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(3)

        # ترويسة الشريط الجانبي مع الشعار الرسمي
        sb_header = QFrame()
        sb_header.setObjectName("SidebarHeader")
        sb_h_layout = QHBoxLayout(sb_header)
        sb_h_layout.setContentsMargins(10, 8, 10, 8)
        sb_h_layout.setSpacing(8)

        # شعار الديوان الوطني للخدمات الجامعية
        lbl_logo = QLabel()
        lbl_logo.setObjectName("SidebarLogo")
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "onou_logo_report.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.getcwd(), "assets", "onou_logo_report.png")
        if os.path.exists(logo_path):
            pm = QPixmap(logo_path)
            if not pm.isNull():
                lbl_logo.setPixmap(pm.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                lbl_logo.setFixedSize(32, 32)
        sb_h_layout.addWidget(lbl_logo)

        titles_col = QVBoxLayout()
        titles_col.setContentsMargins(0, 0, 0, 0)
        titles_col.setSpacing(2)

        lbl_app_title = QLabel("مخزون الإطعام")
        lbl_app_title.setObjectName("SidebarTitle")
        lbl_app_sub = QLabel("مديرية الخدمات الجامعية ورقلة قطب")
        lbl_app_sub.setObjectName("SidebarSubtitle")

        titles_col.addWidget(lbl_app_title)
        titles_col.addWidget(lbl_app_sub)
        sb_h_layout.addLayout(titles_col)
        sb_layout.addWidget(sb_header)

        # أزرار التنقل (Navigation Buttons)
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        is_admin = self.is_directorate_session()

        nav_items = []
        if is_admin:
            nav_items.append(("🏢 مركز قيادة الإقامات والرقابة", 0))

        offset = 1 if is_admin else 0
        operational_items = [
            ("لوحة القيادة والمؤشرات", 0 + offset),
            ("ورقة الاستهلاك اليومي (01-31)", 1 + offset),
            ("معلومات عامة وتعداد التذاكر 📋", 2 + offset),
            ("حركة الإعارة والاستعارة بين الإقامات 🔄", 3 + offset),
            ("قائمة الأسعار ودليل المواد", 4 + offset),
            ("وصولات الاستلام والتوريد", 5 + offset),
            ("وصولات الإخراج والتحويلات", 6 + offset),
            ("شبكات التتبع الشهرية (31 يوم)", 7 + offset),
            ("وضعية الحصص والموردين (عبد الحميد الوضعية) 📋", 8 + offset),
            ("مركز السجلات والتقارير والطباعة", 9 + offset),
            ("📋 بونات الطلب — Bons de Commande", 10 + offset),
            ("النسخ الاحتياطي والإعدادات", 11 + offset),
        ]
        nav_items.extend(operational_items)

        hidden_nav_keywords = [
            "حركة الإعارة والاستعارة",
            "وصولات الاستلام والتوريد",
            "وصولات الإخراج والتحويلات",
            "وضعية الحصص والموردين"
        ]

        self.nav_buttons = []
        for text, page_idx in nav_items:
            btn = QPushButton(f"  {text}")
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            if page_idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda _, idx=page_idx: self.switch_page(idx))
            self.btn_group.addButton(btn, page_idx)
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

            # إخفاء الأزرار المحددة حالياً حسب طلب المستخدم
            if any(k in text for k in hidden_nav_keywords):
                btn.setVisible(False)

        sb_layout.addStretch()

        try:
            from core.update_service import UpdateService
            curr_ver = UpdateService.get_current_version()
        except Exception:
            curr_ver = "2.8.0"
        lbl_version = QLabel(f"الإصدار {curr_ver} - شبكة الوايفاي المركزية")
        lbl_version.setStyleSheet("color: #64748B; font-size: 11px; padding: 10px 16px;")
        sb_layout.addWidget(lbl_version)

        main_layout.addWidget(sidebar)

        # 2. المنطقة الرئيسية (Header + Content Stack)
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # شريط العنوان العلوي (Header)
        header_bar = QFrame()
        header_bar.setObjectName("HeaderBar")
        hb_layout = QHBoxLayout(header_bar)
        hb_layout.setContentsMargins(15, 6, 15, 6)
        hb_layout.setSpacing(10)

        # عناوين الإقامة والمديرية والتبديل السريع
        titles_widget = QWidget()
        titles_box = QVBoxLayout(titles_widget)
        titles_box.setContentsMargins(0, 0, 0, 0)
        titles_box.setSpacing(3)
        self.lbl_res = QLabel(self.current_residence_name)
        self.lbl_res.setObjectName("ResidenceTitle")
        self.lbl_dir = QLabel("مديرية الخدمات الجامعية ورقلة قطب")
        self.lbl_dir.setObjectName("DirectorateSubtitle")

        self.lbl_switch = None
        if is_admin:
            self.lbl_res.setVisible(False)
            titles_widget.setMinimumWidth(380)
            titles_widget.setMaximumWidth(460)
            self.cmb_residence_switch = QComboBox()
            self.cmb_residence_switch.setObjectName("ResidenceSwitchCombo")
            self.cmb_residence_switch.setMinimumWidth(380)
            self.cmb_residence_switch.setMaximumWidth(460)
            self.cmb_residence_switch.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            if self.cmb_residence_switch.view():
                self.cmb_residence_switch.view().setMinimumWidth(400)
                self.cmb_residence_switch.view().setTextElideMode(Qt.TextElideMode.ElideNone)
            self.populate_residence_switcher()
            self.cmb_residence_switch.currentIndexChanged.connect(self.on_residence_combo_changed)
            titles_box.addWidget(self.cmb_residence_switch)
        else:
            titles_box.addWidget(self.lbl_res)

        titles_box.addWidget(self.lbl_dir)
        hb_layout.addWidget(titles_widget)

        if is_admin:
            self.btn_sync_all_residences = QPushButton("🔄 تحديث كافة الإقامات")
            self.btn_sync_all_residences.setObjectName("BtnSyncAllResidences")
            self.btn_sync_all_residences.setToolTip("تحديث ومزامنة بيانات كافة الإقامات التسع فورياً من الخادم المركزي أو الفلاش ديسك")
            self.btn_sync_all_residences.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_sync_all_residences.setStyleSheet("""
                QPushButton#BtnSyncAllResidences {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                    color: #FFFFFF;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 6px 12px;
                    border: 1px solid #34D399;
                }
                QPushButton#BtnSyncAllResidences:hover {
                    background: #047857;
                }
            """)
            self.btn_sync_all_residences.clicked.connect(self.on_sync_all_residences_clicked)
            hb_layout.addWidget(self.btn_sync_all_residences)

        hb_layout.addStretch()

        # معلومات المستخدم وشارة الدور
        user_widget = QWidget()
        user_box = QVBoxLayout(user_widget)
        user_box.setContentsMargins(0, 0, 0, 0)
        user_box.setSpacing(2)
        u_name = self.current_user.get("full_name", "")
        if len(u_name) > 22 and "(" in u_name:
            u_name = u_name.split("(")[0].strip()
        self.user_name_lbl = QLabel(f"👤 {u_name}")
        self.user_name_lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
        role_title = "مسؤول النظام والمدير العام ⭐" if is_admin else f"مسير مخزون ({self.current_residence_name})"
        self.user_role_lbl = QLabel(role_title)
        self.user_role_lbl.setStyleSheet("font-size: 10px;")
        user_box.addWidget(self.user_name_lbl)
        user_box.addWidget(self.user_role_lbl)
        hb_layout.addWidget(user_widget)

        hb_layout.addSpacing(8)

        # التاريخ والوقت
        self.lbl_clock = QLabel()
        self.update_clock()
        hb_layout.addWidget(self.lbl_clock)

        hb_layout.addSpacing(8)

        # زر التبديل السريع بين الوضع المظلم والوضع الفاتح
        self.btn_theme_toggle = QPushButton()
        self.btn_theme_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        hb_layout.addWidget(self.btn_theme_toggle)

        # زر التحديثات وترقية المنظومة بنقرة زر
        self.btn_updates = QPushButton("🚀 التحديثات")
        self.btn_updates.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_updates.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0284C7, stop:1 #0369A1);
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                border: 1px solid #38BDF8;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0369A1, stop:1 #075985);
            }
        """)
        self.btn_updates.clicked.connect(self.open_update_dialog)
        hb_layout.addWidget(self.btn_updates)

        # زر إعدادات الربط الشبكي والمزامنة (محمي بكود المديرية لغير المسؤولين)
        self.btn_net_settings = QPushButton("🌐 الربط")
        self.btn_net_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_net_settings.clicked.connect(self.open_network_settings)
        hb_layout.addWidget(self.btn_net_settings)

        # زر المزامنة الفورية — أحادي الاتجاه حسب دور المستخدم
        is_admin_btn = (self.current_user.get("role") == "SUPER_ADMIN")
        sync_btn_text = "🔄 سحب من الإقامات" if is_admin_btn else "🔄 إرسال للمديرية"
        sync_btn_tip = "سحب أحدث البيانات من جميع الإقامات إلى المديرية فوراً" if is_admin_btn else "إرسال البيانات المحلية إلى المديرية فوراً"
        self.btn_sync_now = QPushButton(sync_btn_text)
        self.btn_sync_now.setToolTip(sync_btn_tip)
        self.btn_sync_now.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_now.clicked.connect(self.trigger_manual_sync)
        hb_layout.addWidget(self.btn_sync_now)

        self.update_theme_button_ui()

        content_layout.addWidget(header_bar)

        # 3. مكدس الصفحات (Stacked Pages)
        self.stack = QStackedWidget()

        if is_admin:
            self.res_manager_page = ResidenceManagerWidget(self.res_svc, self.auth_svc)
            self.res_manager_page.switch_to_residence_requested.connect(self.on_director_enter_residence)
            self.stack.addWidget(self.res_manager_page)  # 0

        self.dashboard_page = DashboardWidget(
            self.stock_svc,
            residence_id=self.current_residence_id,
            residence_name=self.current_residence_name
        )
        self.daily_sheet_page = DailySheetWidget(
            self.stock_svc, self.meals_svc, self.report_gen,
            is_directorate=is_admin,
            current_user=self.current_user
        )
        self.daily_sheet_page.daily_sheet_saved.connect(self.mark_pages_dirty)
        self.general_info_page = GeneralInfoWidget(
            self.stock_svc, self.meals_svc, self.report_gen,
            is_directorate=is_admin,
            current_user=self.current_user
        )
        self.general_info_page.general_info_saved.connect(self.mark_pages_dirty)

        self.loans_page = ResidenceLoansWidget(self.stock_svc, current_user=self.current_user)
        self.loans_page.loan_saved.connect(self.mark_pages_dirty)
        self.loans_page.loan_confirmed.connect(self.on_loan_confirmed)

        # ربط التنقل السريع بين ورقة الاستهلاك ومعلومات عامة وحركة الإعارة
        self.daily_sheet_page.open_general_info_requested.connect(self.on_switch_to_general_info)
        self.daily_sheet_page.open_loans_requested.connect(self.on_switch_to_loans)
        self.general_info_page.open_daily_sheet_requested.connect(self.on_switch_to_daily_sheet)

        self.articles_page = ArticlesWidget(self.stock_svc)
        self.articles_page.article_saved.connect(self.on_articles_prices_saved)
        self.entry_page = EntryVoucherWidget(
            self.stock_svc,
            is_directorate=is_admin,
            current_user=self.current_user
        )
        self.exit_page = ExitVoucherWidget(
            self.stock_svc,
            is_directorate=is_admin,
            current_user=self.current_user
        )
        self.matrix_page = MatrixTrackingWidget(self.stock_svc)
        self.trimester_page = TrimesterSituationWidget(self.stock_svc, self.report_gen)
        self.reports_page = ReportsWidget(self.report_gen, is_directorate=is_admin, current_user=self.current_user)
        self.bon_commande_page = BonCommandeWidget(self.db, self.current_user)
        self.settings_page = SettingsWidget(
            self.db,
            current_user=self.current_user,
            residence_id=self.current_residence_id
        )
        if hasattr(self.settings_page, "residence_data_pulled"):
            self.settings_page.residence_data_pulled.connect(self.on_residence_data_pulled)

        self.stack.addWidget(self.dashboard_page)       # 0 + offset
        self.stack.addWidget(self.daily_sheet_page)     # 1 + offset
        self.stack.addWidget(self.general_info_page)    # 2 + offset
        self.stack.addWidget(self.loans_page)           # 3 + offset
        self.stack.addWidget(self.articles_page)        # 4 + offset
        self.stack.addWidget(self.entry_page)           # 5 + offset
        self.stack.addWidget(self.exit_page)            # 6 + offset
        self.stack.addWidget(self.matrix_page)          # 7 + offset
        self.stack.addWidget(self.trimester_page)       # 8 + offset
        self.stack.addWidget(self.reports_page)         # 9 + offset
        self.stack.addWidget(self.bon_commande_page)    # 10 + offset
        self.stack.addWidget(self.settings_page)        # 11 + offset

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_container)

        self.setCentralWidget(main_widget)

        # 4. شريط الحالة السفلي (Status Bar)
        self.status = QStatusBar()
        self.status.showMessage(f"جاهز للعمل  |  الإقامة النشطة: {self.current_residence_name}")

        self.lbl_net_status = QPushButton("🌐 جاري التحقق من الشبكة...")
        self.lbl_net_status.setStyleSheet("background: transparent; border: none; font-weight: bold; font-size: 11px; padding: 0 10px;")
        self.lbl_net_status.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_net_status.clicked.connect(self.open_network_settings)
        self.status.addPermanentWidget(self.lbl_net_status)

        self.setStatusBar(self.status)

        # مؤقت الساعة
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

        self.init_sync_worker()

    def update_theme_button_ui(self):
        """تحديث شكل زر التبديل وألوان عناصر الترويسة العلوية"""
        from ui.theme import ThemeManager
        is_dark = ThemeManager.is_dark_mode()
        if is_dark:
            self.btn_theme_toggle.setText("☀️ فاتح")
            self.btn_theme_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #334155;
                    color: #F8FAFC;
                    border: 1px solid #475569;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #475569;
                    color: #FFFFFF;
                }
            """)
        else:
            self.btn_theme_toggle.setText("🌙 داكن")
            self.btn_theme_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #0F2D25;
                    color: #FFFFFF;
                    border: 1px solid #0D9488;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1A4237;
                }
            """)

        if hasattr(self, "btn_net_settings") and self.btn_net_settings:
            if is_dark:
                self.btn_net_settings.setStyleSheet("""
                    QPushButton {
                        background-color: #1E293B;
                        color: #38BDF8;
                        border: 1px solid #334155;
                        border-radius: 6px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #334155;
                    }
                """)
            else:
                self.btn_net_settings.setStyleSheet("""
                    QPushButton {
                        background-color: #F0FDF4;
                        color: #0F766E;
                        border: 1px solid #99F6E4;
                        border-radius: 6px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #CCFBF1;
                    }
                """)

        if hasattr(self, "btn_sync_now") and self.btn_sync_now:
            if is_dark:
                self.btn_sync_now.setStyleSheet("""
                    QPushButton {
                        background-color: #064E3B;
                        color: #6EE7B7;
                        border: 1px solid #059669;
                        border-radius: 6px;
                        padding: 4px 10px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #047857;
                        color: #FFFFFF;
                    }
                """)
            else:
                self.btn_sync_now.setStyleSheet("""
                    QPushButton {
                        background-color: #ECFDF5;
                        color: #047857;
                        border: 1px solid #A7F3D0;
                        border-radius: 6px;
                        padding: 4px 10px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #D1FAE5;
                    }
                """)

        # تحديث نصوص عناصر الترويسة العلوية
        if hasattr(self, "lbl_res") and self.lbl_res:
            self.lbl_res.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {ThemeManager.get_color('text_heading')};")
        if hasattr(self, "lbl_dir") and self.lbl_dir:
            self.lbl_dir.setStyleSheet(f"font-size: 11px; color: {ThemeManager.get_color('text_secondary')};")
        if hasattr(self, "lbl_switch") and self.lbl_switch:
            self.lbl_switch.setStyleSheet(f"font-weight: bold; font-size: 11px; color: {ThemeManager.get_color('text_primary')};")
        if hasattr(self, "user_name_lbl") and self.user_name_lbl:
            self.user_name_lbl.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {ThemeManager.get_color('text_primary')};")
        if hasattr(self, "user_role_lbl") and self.user_role_lbl:
            self.user_role_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {ThemeManager.get_color('accent')};")
        if hasattr(self, "lbl_clock") and self.lbl_clock:
            self.lbl_clock.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {ThemeManager.get_color('text_secondary')};")
        if hasattr(self, "cmb_residence_switch") and self.cmb_residence_switch:
            self.cmb_residence_switch.style().unpolish(self.cmb_residence_switch)
            self.cmb_residence_switch.style().polish(self.cmb_residence_switch)

    def toggle_theme(self):
        """التبديل بين الوضع المظلم والوضع الفاتح وحفظ التفضيل"""
        from PyQt6.QtWidgets import QApplication
        from ui.theme import ThemeManager
        app = QApplication.instance()
        new_theme = ThemeManager.toggle_theme(app, db=self.db)
        self.update_theme_button_ui()

        # إشعار كافة الصفحات بالتبديل لإعادة رسم الجداول والعناصر الخاصة بتباين فائق
        for p_name in ["daily_sheet_page", "general_info_page", "articles_page", "matrix_page", "trimester_page"]:
            if hasattr(self, p_name):
                p = getattr(self, p_name)
                if hasattr(p, "refresh_theme"):
                    p.refresh_theme()

    def populate_residence_switcher(self):
        self.cmb_residence_switch.blockSignals(True)
        self.cmb_residence_switch.clear()
        residences = self.res_svc.list_residences(only_active=True)
        curr_idx = 0
        for idx, r in enumerate(residences):
            self.cmb_residence_switch.addItem(f"🏢 {r['name']}  [{r['code']}]", r["id"])
            if r["id"] == self.current_residence_id:
                curr_idx = idx
        self.cmb_residence_switch.setCurrentIndex(curr_idx)
        self.cmb_residence_switch.blockSignals(False)

    def on_residence_combo_changed(self):
        curr_res_id = self.current_residence_id
        new_res_id = self.cmb_residence_switch.currentData()
        if new_res_id == curr_res_id:
            return

        if not self.check_and_prompt_unsaved():
            self.cmb_residence_switch.blockSignals(True)
            for idx in range(self.cmb_residence_switch.count()):
                if self.cmb_residence_switch.itemData(idx) == curr_res_id:
                    self.cmb_residence_switch.setCurrentIndex(idx)
                    break
            self.cmb_residence_switch.blockSignals(False)
            return

        res_row = self.res_svc.get_residence(new_res_id)
        if res_row:
            try:
                self.db.set_setting("last_active_residence_id", str(new_res_id))
            except Exception:
                pass
            self.set_active_residence(new_res_id, res_row["name"])

    def on_director_enter_residence(self, r_id: int, r_name: str):
        """عند نقر المدير على زر الدخول والمتابعة خطوة بخطوة من بطاقة الإقامة"""
        if not self.check_and_prompt_unsaved():
            return
        self.set_active_residence(r_id, r_name)
        # الانتقال لورقة الاستهلاك اليومي أو لوحة القيادة لهذه الإقامة
        is_admin = self.is_directorate_session()
        target_page = 2 if is_admin else 1  # ورقة الاستهلاك اليومي
        self.switch_page(target_page)
        self._restore_nav_button(target_page)

    def set_active_residence(self, r_id: int, r_name: str):
        self.current_residence_id = r_id
        self.current_residence_name = r_name
        self.lbl_res.setText(r_name)

        # تحديث الخدمات مع عزل تام لكل إقامة
        self.stock_svc.set_residence(r_id)
        self.meals_svc.set_residence(r_id)
        self.report_gen.set_residence(r_id, r_name)
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.set_residence(r_id, r_name)
        if hasattr(self, "reports_page"):
            self.reports_page.set_residence(r_id, r_name)
        if hasattr(self, "general_info_page"):
            self.general_info_page.set_residence(r_id)
        if hasattr(self, "loans_page"):
            self.loans_page.set_residence(r_id)
        if hasattr(self, "trimester_page"):
            self.trimester_page.stock_svc.set_residence(r_id)
            self.trimester_page.report_gen.set_residence(r_id, r_name)
        if hasattr(self, "entry_page"):
            self.entry_page.set_residence(r_id)
        if hasattr(self, "exit_page"):
            self.exit_page.set_residence(r_id)
        if hasattr(self, "daily_sheet_page"):
            self.daily_sheet_page.set_residence(r_id, r_name)
        if hasattr(self, "articles_page") and hasattr(self.articles_page, "set_residence"):
            self.articles_page.set_residence(r_id, r_name)
        if hasattr(self, "settings_page") and hasattr(self.settings_page, "set_residence"):
            self.settings_page.set_residence(r_id, r_name)

        # مزامنة الكومبوبوكس إن وجد
        if hasattr(self, "cmb_residence_switch"):
            self.cmb_residence_switch.blockSignals(True)
            for idx in range(self.cmb_residence_switch.count()):
                if self.cmb_residence_switch.itemData(idx) == r_id:
                    self.cmb_residence_switch.setCurrentIndex(idx)
                    break
            self.cmb_residence_switch.blockSignals(False)

        # تحديث شريط الحالة
        ip_txt = get_local_ip()
        self.status.showMessage(f"تم التبديل بنجاح  |  🌐 خادم الوايفاي: {ip_txt}:8050  |  الإقامة الحالية: {self.current_residence_name}")

        # تحديد كافة الصفحات الأخرى كـ dirty لإعادة تحميلها ببيانات الإقامة الجديدة
        self.dirty_pages = set(range(self.stack.count()))
        curr_idx = self.stack.currentIndex()
        self.load_page_data(curr_idx)
        self.dirty_pages.discard(curr_idx)

    def on_switch_to_loans(self):
        is_admin = self.is_directorate_session()
        offset = 1 if is_admin else 0
        target = 3 + offset
        if hasattr(self, "loans_page"):
            self.loans_page.refresh_all_data()
        self.switch_page(target)
        self._restore_nav_button(target)

    def on_loan_confirmed(self):
        """عند تأكيد استلام إعارة، يتم تحديث صفحات المخزون وورقة الاستهلاك تلقائياً"""
        self.mark_pages_dirty()
        if hasattr(self, "daily_sheet_page"):
            self.daily_sheet_page.load_daily_sheet()

    def on_switch_to_general_info(self, date_str: str):
        is_admin = self.is_directorate_session()
        offset = 1 if is_admin else 0
        target = 2 + offset
        if hasattr(self, "general_info_page"):
            self.general_info_page.set_date_from_str(date_str)
            self.general_info_page.load_data()
        self.switch_page(target)
        self._restore_nav_button(target)

    def on_switch_to_daily_sheet(self, date_str: str):
        is_admin = self.is_directorate_session()
        offset = 1 if is_admin else 0
        target = 1 + offset
        qd = QDate.fromString(date_str, "yyyy-MM-dd")
        if qd.isValid() and hasattr(self, "daily_sheet_page"):
            self.daily_sheet_page.dt_picker.setDate(qd)
        self.switch_page(target)
        self._restore_nav_button(target)

    def refresh_current_page_data(self):
        idx = self.stack.currentIndex()
        self.load_page_data(idx)

    def check_and_prompt_unsaved(self) -> bool:
        """
        فحص ما إذا كانت الصفحة الحالية تتضمن تعديلات غير محفوظة.
        إذا وجدت تعديلات، تظهر للمستخدم رسالة منبثقة تسأله عما إذا كان يريد حفظ التغييرات:
        - "YES": حفظ التغييرات فوراً والمتابعة.
        - "NO": تجاهل التغييرات والمتابعة.
        - "CANCEL": إلغاء الانتقال والبقاء في الصفحة الحالية.
        """
        curr_widget = self.stack.currentWidget()
        if not curr_widget or not hasattr(curr_widget, "has_unsaved_changes"):
            return True

        if not curr_widget.has_unsaved_changes():
            return True

        page_title = "الصفحة الحالية"
        curr_idx = self.stack.currentIndex()
        if hasattr(self, "btn_group") and self.btn_group.button(curr_idx):
            btn_txt = self.btn_group.button(curr_idx).text().strip()
            if btn_txt:
                page_title = f"[{btn_txt}]"

        res = prompt_save_changes(
            self,
            title="حفظ التغييرات ⚠️",
            message=f"هل تريد حفظ التغييرات التي قمت بها في {page_title}؟",
            detail="لقد قمت بتعديل حقول الإدخال دون الضغط على زر الحفظ.\nهل ترغب في حفظ التغييرات الآن قبل مغادرة الصفحة؟"
        )

        if res == "YES":
            if hasattr(curr_widget, "save_changes"):
                success = curr_widget.save_changes()
                return bool(success)
            return True
        elif res == "NO":
            if hasattr(curr_widget, "discard_changes"):
                curr_widget.discard_changes()
            return True
        else:  # CANCEL
            return False

    def _restore_nav_button(self, page_idx: int):
        """إعادة تحديد زر الصفحة في الشريط الجانبي في حال إلغاء الانتقال"""
        if hasattr(self, "btn_group"):
            btn = self.btn_group.button(page_idx)
            if btn:
                self.btn_group.blockSignals(True)
                btn.setChecked(True)
                self.btn_group.blockSignals(False)

    def switch_page(self, index: int):
        curr_idx = self.stack.currentIndex()
        if index == curr_idx:
            return

        # التحقق من وجود تعديلات غير محفوظة في الصفحة الحالية
        if not self.check_and_prompt_unsaved():
            self._restore_nav_button(curr_idx)
            return

        is_admin = self.is_directorate_session()
        offset = 1 if is_admin else 0

        # حماية واجهة النسخ الاحتياطي والإعدادات بكود المديرية الموحد
        if index == (11 + offset):
            from ui.widgets.directorate_auth_dialog import DirectorateAuthDialog
            if not DirectorateAuthDialog.verify(self, "الدخول إلى واجهة النسخ الاحتياطي والإعدادات", self.db):
                self._restore_nav_button(curr_idx)
                return

        # 1. التبديل البصري الفوري بنقرة واحدة دون أي تجميد (0 ميلي ثانية)
        self.stack.setCurrentIndex(index)

        # 2. تحميل البيانات
        if index == (2 + offset) and hasattr(self, "general_info_page"):
            self.general_info_page.load_data()
        elif index == (3 + offset) and hasattr(self, "loans_page"):
            self.loans_page.refresh_all_data()
        elif index not in self.loaded_pages or index in self.dirty_pages:
            self.load_page_data(index)
            self.loaded_pages.add(index)
            self.dirty_pages.discard(index)

    def load_page_data(self, index: int):
        """تحميل بيانات صفحة معينة عند الحاجة فقط"""
        is_admin = self.is_directorate_session()
        offset = 1 if is_admin else 0

        if is_admin and index == 0:
            if hasattr(self, "res_manager_page"):
                self.res_manager_page.load_data()
        elif index == (0 + offset):
            if hasattr(self, "dashboard_page"):
                self.dashboard_page.load_data()
        elif index == (1 + offset):
            if hasattr(self, "daily_sheet_page"):
                self.daily_sheet_page.load_daily_sheet()
        elif index == (2 + offset):
            if hasattr(self, "general_info_page"):
                self.general_info_page.load_data()
        elif index == (3 + offset):
            if hasattr(self, "loans_page"):
                self.loans_page.refresh_all_data()
        elif index == (4 + offset):
            if hasattr(self, "articles_page"):
                self.articles_page.load_articles()
        elif index == (5 + offset):
            if hasattr(self, "entry_page"):
                if hasattr(self.entry_page, "load_vouchers_history"):
                    self.entry_page.load_vouchers_history()
                elif hasattr(self.entry_page, "load_vouchers"):
                    self.entry_page.load_vouchers()
        elif index == (6 + offset):
            if hasattr(self, "exit_page"):
                if hasattr(self.exit_page, "load_history"):
                    self.exit_page.load_history()
                elif hasattr(self.exit_page, "load_vouchers"):
                    self.exit_page.load_vouchers()
        elif index == (7 + offset):
            if hasattr(self, "matrix_page"):
                self.matrix_page.load_current_tab_data()
        elif index == (8 + offset):
            if hasattr(self, "trimester_page"):
                self.trimester_page.load_situation()
        elif index == (9 + offset):
            if hasattr(self, "reports_page"):
                self.reports_page.refresh_current_tab()
        elif index == (10 + offset):
            if hasattr(self, "bon_commande_page"):
                self.bon_commande_page.refresh()
        elif index == (11 + offset):
            if hasattr(self, "settings_page"):
                if hasattr(self.settings_page, "load_settings"):
                    self.settings_page.load_settings()

    def on_articles_prices_saved(self):
        """تحديث فوري وشامل لكافة الواجهات والبيانات عند تعديل الأسعار"""
        self.mark_pages_dirty()
        if hasattr(self, "daily_sheet_page"):
            self.daily_sheet_page.load_daily_sheet()
        if hasattr(self, "general_info_page"):
            self.general_info_page.load_data()
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.load_data()
        if hasattr(self, "matrix_page"):
            self.matrix_page.load_current_tab_data()
        if hasattr(self, "trimester_page"):
            self.trimester_page.load_situation()
        if hasattr(self, "reports_page"):
            self.reports_page.refresh_current_tab()

    def mark_pages_dirty(self):
        """عند حدوث تعديل في المخزون أو التذاكر، يتم تعليم الصفحات الأخرى لتحديثها عند زيارتها"""
        curr_idx = self.stack.currentIndex()
        self.dirty_pages = set(range(self.stack.count()))
        self.dirty_pages.discard(curr_idx)
        # إشعار خيط المزامنة بالإرسال الفوري اللحظي فوراً بمجرد الحفظ
        if hasattr(self, "sync_worker") and self.sync_worker:
            self.sync_worker.trigger_immediate_sync()

    def update_clock(self):
        try:
            from core.time_service import TimeService
            curr_d = TimeService.current_qdate().toString("yyyy-MM-dd")
            curr_t = TimeService.current_qtime().toString("HH:mm")
            status = TimeService.get_status_info()
            if status.get("synced"):
                self.lbl_clock.setText(f"🌐 {curr_d}  {curr_t}")
                self.lbl_clock.setToolTip(f"توقيت عالمي رسمي موحد (UTC+1)\nالمصدر: {status.get('source')}\nالإزاحة: {status.get('offset_seconds')} ثانية")
            else:
                self.lbl_clock.setText(f"📅 {curr_d}  {curr_t}")
                self.lbl_clock.setToolTip("توقيت محلي (جاري المزامنة...)")
        except Exception:
            curr_d = QDate.currentDate().toString("yyyy-MM-dd")
            curr_t = QTime.currentTime().toString("HH:mm")
            self.lbl_clock.setText(f"📅 {curr_d}  {curr_t}")

    # -------------------------------------------------------------
    # إدارة المزامنة والربط الشبكي والاستقلالية التامة
    # -------------------------------------------------------------
    def is_directorate_session(self) -> bool:
        """
        فحص ما إذا كانت الجلسة الحالية تمثل المديرية المركزية:
        - أي حساب إدارة مركزية أو مدير عام أو مراقب تسيير (SUPER_ADMIN, ADMIN, DIRECTORATE, DIRECTOR...) وبدون إقامة محددة.
        - أو إذا كان نمط التطبيق خادم مديرية DIRECTORATE_SERVER.
        - حسابات الإقامات (STOREKEEPER / RESIDENCE_USER أو أي حساب بـ residence_id محدد) هي جلسة إقامة دائماً.
        """
        if not hasattr(self, "current_user") or not self.current_user:
            return AppConfig.get("app_mode") == "DIRECTORATE_SERVER"

        res_id = self.current_user.get("residence_id")
        if res_id is not None and str(res_id).strip() not in ("", "0", "None"):
            return False

        role = str(self.current_user.get("role") or "").upper()
        if role in ("STOREKEEPER", "RESIDENCE_USER"):
            return False

        if role in ("SUPER_ADMIN", "ADMIN", "DIRECTORATE", "DIRECTOR", "CHEF_SERVICE", "CONTROLLER", "GESTIONNAIRE", "INSPECTOR") or "ADMIN" in role or "DIRECT" in role:
            return True

        return AppConfig.get("app_mode") == "DIRECTORATE_SERVER"


    def on_sync_all_residences_clicked(self):
        """مزامنة وتحديث كافة الإقامات التسع للمديرية دفعة واحدة"""
        is_online = self.sync_worker.sync_svc.is_server_reachable() if self.sync_worker else False

        if not is_online:
            usb_candidates = [r"H:\official_catering_stock.db", r"H:\data\official_catering_stock.db"]
            found_usb = None
            for p in usb_candidates:
                if os.path.exists(p):
                    found_usb = p
                    break

            if found_usb:
                ans = QMessageBox.question(
                    self,
                    "تحديث شامل (أوفلاين بدون إنترنت)",
                    f"تعذر الاتصال بالخادم المركزي السحابي في الوقت الحالي.\nتم العثور على قاعدة بيانات الإقامات في الفلاش ديسك:\n{found_usb}\n\nهل ترغب في تحديث ومزامنة بيانات كافة الإقامات التسع من الفلاش ديسك؟",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if ans == QMessageBox.StandardButton.Yes:
                    self._start_all_residences_sync(mode="FILE", db_path=found_usb)
                return
            else:
                QMessageBox.warning(
                    self,
                    "تعذر الاتصال",
                    "تعذر الاتصال بالخادم المركزي السحابي، ولم يتم العثور على فلاش ديسك H:\\ به قاعدة البيانات.\nيرجى التحقق من اتصال الإنترنت أو إدخال الفلاش ديسك."
                )
                return

        self._start_all_residences_sync(mode="SERVER")

    def _start_all_residences_sync(self, mode="SERVER", db_path=None):
        if hasattr(self, "_all_sync_thread") and self._all_sync_thread.isRunning():
            return

        if hasattr(self, "btn_sync_all_residences"):
            self.btn_sync_all_residences.setEnabled(False)
            self.btn_sync_all_residences.setText("⏳ جارٍ التحديث...")

        prog = QProgressDialog("جارٍ الاتصال ومزامنة بيانات كافة الإقامات...", "إلغاء", 0, 9, self)
        prog.setWindowTitle("مزامنة وتحديث كافة الإقامات")
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.setMinimumDuration(0)
        prog.setValue(0)
        prog.show()

        sync_svc = self.sync_worker.sync_svc if self.sync_worker else SyncService(self.db)
        thread = AllResidencesSyncThread(sync_svc, mode=mode, db_path=db_path, parent=self)
        self._all_sync_thread = thread

        def on_prog(curr, tot, name):
            prog.setMaximum(tot)
            prog.setValue(curr)
            prog.setLabelText(f"جارٍ تحديث ({curr}/{tot}): {name}...")

        def on_done(res):
            prog.close()
            if hasattr(self, "btn_sync_all_residences"):
                self.btn_sync_all_residences.setEnabled(True)
                self.btn_sync_all_residences.setText("🔄 تحديث كافة الإقامات")

            if res.get("success"):
                synced_cnt = res.get("synced_count", 0)
                tot_cnt = res.get("total_residences", 9)
                msg = f"✅ تم بنجاح تحديث ومزامنة بيانات ({synced_cnt} من أصل {tot_cnt}) إقامات جامعية.\nكافة الجداول، البطاقات، والتقارير محدثة بالكامل الآن."
                QMessageBox.information(self, "اكتمل التحديث الشامل", msg)
                self.mark_pages_dirty()
                self.refresh_current_page_data()
                if hasattr(self, "res_manager_page"):
                    try:
                        self.res_manager_page.load_data()
                    except Exception:
                        pass
            else:
                QMessageBox.warning(self, "تنبيه", f"تعذر إكمال التحديث الشامل:\n{res.get('error', 'خطأ غير معروف')}")

        def on_err(err_str):
            prog.close()
            if hasattr(self, "btn_sync_all_residences"):
                self.btn_sync_all_residences.setEnabled(True)
                self.btn_sync_all_residences.setText("🔄 تحديث كافة الإقامات")
            QMessageBox.critical(self, "خطأ في المزامنة", f"حدث خطأ أثناء المزامنة:\n{err_str}")

        prog.canceled.connect(thread.cancel)
        thread.progress.connect(on_prog)
        thread.finished.connect(on_done)
        thread.error.connect(on_err)
        thread.start()

    def init_sync_worker(self):
        """
        تهيئة خيط المزامنة بنمط محكم وأحادي الاتجاه:
        - المديرية المركزية: سيرفر المديرية مع حساب SUPER_ADMIN (سحب وتحديث بيانات الإقامات)
        - الإقامات: إرسال (push) فقط إلى الخادم المركزي — لا تسحب شيئاً لمنع الكتابة فوق مدخلاتها
        """
        is_directorate = self.is_directorate_session()

        if is_directorate:
            try:
                AppConfig.set("app_mode", "DIRECTORATE_SERVER")
            except Exception:
                pass

        worker_res_id = None if is_directorate else self.current_residence_id

        self.sync_worker = SyncWorker(
            residence_id=worker_res_id,
            is_directorate=is_directorate,
            parent=self
        )
        self.sync_worker.connectivity_changed.connect(self.on_connectivity_changed)
        self.sync_worker.sync_finished.connect(self.on_sync_finished)
        # إشارة خاصة للمديرية: تحديث الواجهة فور وصول بيانات جديدة من إقامة
        self.sync_worker.new_residence_data_received.connect(self.on_new_residence_data)
        self.sync_worker.start()
        self.update_sync_ui(is_online=False)

    def trigger_manual_sync(self):
        """تشغيل المزامنة الفورية يدوياً بضغطة زر"""
        is_directorate = self.is_directorate_session()

        if is_directorate:
            # المديرية: إعادة ضبط مؤشر السحب لاستقبال جميع الأحداث من جديد
            try:
                self.db.set_setting("last_pulled_sync_event_id", "0")
            except Exception:
                pass
            self.status.showMessage("🔄 جارٍ سحب أحدث البيانات من جميع الإقامات...", 5000)
        else:
            self.status.showMessage("🔄 جارٍ إرسال البيانات المحفوظة إلى الخادم المركزي...", 5000)

        if self.sync_worker:
            if is_directorate:
                self.sync_worker.trigger_full_all_sync()
            else:
                self.sync_worker.trigger_immediate_sync()
        else:
            self.init_sync_worker()

    def on_connectivity_changed(self, is_online: bool):
        self.update_sync_ui(is_online)

    def on_sync_finished(self, synced_count: int, left_count: int):
        self.update_sync_ui(is_online=True)
        is_admin = self.is_directorate_session()
        if synced_count > 0:
            if is_admin:
                msg = f"✅ المديرية: تم استقبال ({synced_count}) حركة من الإقامات وتحديث البيانات."
            else:
                msg = f"✅ تم إرسال ({synced_count}) حركة إلى المديرية بنجاح."
            self.status.showMessage(msg, 6000)
            self.mark_pages_dirty()
            try:
                self.refresh_current_page_data()
            except Exception:
                pass
        else:
            if is_admin:
                self.status.showMessage("✅ المديرية متصلة — لا توجد بيانات جديدة من الإقامات.", 3000)
            else:
                self.status.showMessage("✅ متصل بالمديرية — جميع البيانات مرسلة بنجاح.", 3000)

    def on_new_residence_data(self, pulled_count: int):
        """يُستدعى في المديرية عند وصول بيانات جديدة من إقامة — يُحدّث الواجهة فوراً دون الحاجة لتبديل الإقامة"""
        try:
            from core.cache_service import CacheService
            CacheService.invalidate_all()

            # 1. تحديث الصفحة الحالية المعروضة
            self.refresh_current_page_data()

            # 2. تحديث صفحات المتابعة والبطاقات فوراً لضمان تناسق الأرقام
            if hasattr(self, "res_manager_page"):
                try:
                    self.res_manager_page.load_data()
                except Exception:
                    pass

            if hasattr(self, "dashboard_page"):
                try:
                    self.dashboard_page.load_data()
                except Exception:
                    pass

            if hasattr(self, "daily_sheet_page"):
                try:
                    if not getattr(self.daily_sheet_page, "is_dirty", False):
                        self.daily_sheet_page.load_daily_sheet()
                except Exception:
                    pass

            if hasattr(self, "general_info_page"):
                try:
                    if not getattr(self.general_info_page, "is_dirty", False):
                        self.general_info_page.load_data()
                except Exception:
                    pass

            if hasattr(self, "matrix_page"):
                try:
                    self.matrix_page.load_current_tab_data()
                except Exception:
                    pass

            # 3. تعليم باقي الصفحات كـ dirty لتحديثها عند التبديل إليها
            curr_idx = self.stack.currentIndex()
            self.dirty_pages = set(range(self.stack.count()))
            self.dirty_pages.discard(curr_idx)

            self.status.showMessage(f"🟢 تم استقبال وتحديث بيانات الإقامات تلقائياً على الشاشة ({pulled_count} حركة جديدة)", 5000)
        except Exception as e:
            logger.error(f"Error in on_new_residence_data: {e}")

    def on_residence_data_pulled(self, r_id: int):
        """يُستدعى عند نجاح سحب واسترجاع بيانات الإقامة لتحديث الواجهة فورياً والتحويل التلقائي للإقامة المسترجعة"""
        try:
            from core.cache_service import CacheService
            CacheService.invalidate_all()
        except Exception:
            pass
        self.dirty_pages = set(range(self.stack.count()))

        r_name = ""
        try:
            res_row = self.res_svc.get_residence(r_id)
            if res_row and res_row.get("name"):
                r_name = res_row["name"]
        except Exception:
            pass
        if not r_name:
            r_name = f"الإقامة {r_id}"

        # تبديل الإقامة النشطة فورياً للإقامة المسحوبة حتى تظهر كافة سجلاتها ومخزونها أمام المستخدم مباشرة
        self.set_active_residence(r_id, r_name)

        # الانتقال التلقائي لأحدث تاريخ مسجل به بيانات استهلاك وتذاكر
        latest = self.stock_svc.get_latest_active_date(r_id)
        if latest:
            qd = QDate.fromString(latest, "yyyy-MM-dd")
            if hasattr(self, "daily_sheet_page"):
                self.daily_sheet_page.set_date(qd)
            if hasattr(self, "general_info_page"):
                self.general_info_page.set_date(qd)

        # التبديل فورياً إلى صفحة ورقة الاستهلاك اليومي ليرى المستخدم أوراقه وتذاكره مباشرة
        is_admin = self.is_directorate_session()
        daily_idx = 1 + (1 if is_admin else 0)
        self.switch_page(daily_idx)
        self._restore_nav_button(daily_idx)

        self.refresh_current_page_data()

    def update_sync_ui(self, is_online: bool):
        is_admin = self.is_directorate_session()
        pending = self.sync_svc.get_pending_count(None if is_admin else self.current_residence_id)
        if is_online:
            if pending > 0:
                self.lbl_net_status.setText(f"🟢 متصل بالخادم (جاري إرسال {pending} حركة معلقة)")
                self.lbl_net_status.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11px;")
            else:
                role_label = "المديرية - مزامنة تامة لجميع الإقامات" if is_admin else "متصل بالخادم (مزامنة تامة)"
                self.lbl_net_status.setText(f"🟢 {role_label}")
                self.lbl_net_status.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")
        else:
            if pending > 0:
                self.lbl_net_status.setText(f"🟡 وضع محلي غير متصل ({pending} حركات معلقة بالمخزن)")
                self.lbl_net_status.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 11px;")
            else:
                self.lbl_net_status.setText("⚪ وضع محلي غير متصل بالخادم (0 معلقة)")
                self.lbl_net_status.setStyleSheet("color: #94A3B8; font-weight: bold; font-size: 11px;")

    def open_network_settings(self):
        from ui.widgets.network_settings_dialog import NetworkSettingsDialog
        if NetworkSettingsDialog.open_with_admin_auth(self.db, parent=self):
            is_online = self.sync_svc.is_server_reachable()
            self.update_sync_ui(is_online)

    def open_update_dialog(self):
        """فتح نافذة التحديثات المستقلة وتثبيت الترقيات من فلاشة USB أو الشبكة"""
        dlg = UpdateDialog(parent=self)
        dlg.exec()

    def check_auto_backup(self):
        """فحص وتنفيذ الحفظ الاحتياطي اليومي التلقائي لهذا الجهاز في الخلفية"""
        try:
            created_path = self.backup_svc.check_and_run_daily_backup()
            if created_path:
                filename = os.path.basename(created_path)
                folder = os.path.dirname(created_path)
                self.status.showMessage(f"💾 تم إنشاء النسخة الاحتياطية اليومية بنجاح: {filename} في [{folder}]", 12000)
                if hasattr(self, "settings_page"):
                    self.settings_page.load_backups_list()
                    self.settings_page.update_auto_status_label()
        except Exception:
            pass

    def closeEvent(self, event):
        if not self.check_and_prompt_unsaved():
            event.ignore()
            return

        if self.sync_worker:
            self.sync_worker.stop()
        if hasattr(self, "auto_backup_timer") and self.auto_backup_timer:
            self.auto_backup_timer.stop()
        super().closeEvent(event)