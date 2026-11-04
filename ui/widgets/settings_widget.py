from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QComboBox, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QProgressBar,
    QFormLayout, QScrollArea, QCheckBox, QTimeEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTime, QUrl
from PyQt6.QtGui import QCursor, QDesktopServices
import os
import datetime
from database.db_manager import DatabaseManager
from core.backup_service import BackupService
from core.config import AppConfig
from migration.migrate_excel import ExcelMigrator
from ui.common_filters import attach_smooth_scroll

class MigrationWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            migrator = ExcelMigrator()
            res = migrator.run_full_migration(progress_callback=self.progress.emit)
            self.finished.emit(res)
        except Exception as e:
            self.error.emit(str(e))

def get_candidate_official_dbs():
    import string
    candidates = []
    from database.db_manager import BASE_DIR
    for b in [BASE_DIR, os.path.dirname(sys.executable), os.path.abspath(os.path.join(os.path.dirname(sys.executable), ".."))]:
        if b:
            candidates.append(os.path.join(b, "database", "official_catering_stock.db"))
            candidates.append(os.path.join(b, "data", "catering_stock.db"))
            candidates.append(os.path.join(b, "official_catering_stock.db"))
            candidates.append(os.path.join(b, "catering_stock.db"))
    user_prof = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    desktop = os.path.join(user_prof, "Desktop")
    candidates.append(os.path.join(desktop, "official_catering_stock.db"))
    candidates.append(os.path.join(desktop, "catering_stock.db"))
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        candidates.append(os.path.join(local_app, "CateringStockONOU", "database", "official_catering_stock.db"))
        candidates.append(os.path.join(local_app, "CateringStockONOU", "data", "catering_stock.db"))
    for l in string.ascii_uppercase:
        drive = f"{l}:\\"
        if os.path.exists(drive):
            candidates.append(os.path.join(drive, "official_catering_stock.db"))
            candidates.append(os.path.join(drive, "catering_stock.db"))
            candidates.append(os.path.join(drive, "pyinstaller_dist", "CateringStockONOU", "database", "official_catering_stock.db"))
            candidates.append(os.path.join(drive, "CateringStockONOU", "data", "catering_stock.db"))
            candidates.append(os.path.join(drive, "55", "CateringStockONOU", "database", "official_catering_stock.db"))
            candidates.append(os.path.join(drive, "55", "official_catering_stock.db"))
    seen = set()
    valid = []
    for c in candidates:
        norm = os.path.abspath(c)
        if norm not in seen and os.path.exists(norm) and os.path.getsize(norm) > 1000000:
            seen.add(norm)
            valid.append(norm)
    return valid

class PullResidenceWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, residence_id: int, db_manager: DatabaseManager, from_db_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.residence_id = residence_id
        self.db = db_manager
        self.from_db_path = from_db_path

    def run(self):
        try:
            import os
            import logging
            _logger = logging.getLogger(__name__)
            from core.sync_service import SyncService
            sync_svc = SyncService(self.db)

            if self.from_db_path:
                res = sync_svc.restore_residence_from_db_file(self.residence_id, self.from_db_path)
            else:
                # 1. المحاولة الأولى: سحب عبر الشبكة أو السحاب
                res = sync_svc.pull_full_residence_data(self.residence_id)

                # 2. في حال فشل الاتصال بالشبكة (أوفلاين أو انقطاع أو مهلة)، السحب التلقائي من قاعدة البيانات الرسمية
                if not res.get("success"):
                    _logger.warning(f"Online pull failed ({res.get('error')}), initiating smart offline fallback...")
                    candidates = get_candidate_official_dbs()
                    for cand in candidates:
                        fb_res = sync_svc.restore_residence_from_db_file(self.residence_id, cand)
                        if fb_res.get("success"):
                            fb_res["source_mode"] = "OFFLINE_FALLBACK"
                            fb_res["source_file"] = cand
                            res = fb_res
                            break

            if res.get("success"):
                self.finished.emit(res)
            else:
                self.error.emit(res.get("error", "فشلت عملية سحب البيانات"))
        except Exception as e:
            self.error.emit(str(e))


class SettingsWidget(QWidget):
    """شاشة الإعدادات، النسخ الاحتياطي التلقائي واليدوي، وترحيل البيانات"""
    residence_data_pulled = pyqtSignal(int)

    def __init__(self, db_manager: DatabaseManager, parent=None, current_user=None, residence_id=None):
        super().__init__(parent)
        self.db = db_manager
        self.current_user = current_user or {}
        self.residence_id = residence_id
        self.backup_svc = BackupService(self.db)
        self.is_dirty = False
        self.is_loading = False
        self.init_ui()
        self.load_settings()
        self.load_backups_list()

    def get_target_residence_id(self) -> int:
        if self.residence_id:
            try:
                return int(self.residence_id)
            except Exception:
                pass
        if self.current_user and self.current_user.get("residence_id"):
            try:
                return int(self.current_user["residence_id"])
            except Exception:
                pass
        saved = self.db.get_setting("last_active_residence_id")
        if saved:
            try:
                return int(saved)
            except Exception:
                pass
        conf_res = AppConfig.get("residence_id")
        if conf_res:
            try:
                return int(conf_res)
            except Exception:
                pass
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT id FROM residences LIMIT 1").fetchone()
            if row:
                return int(row[0])
        return 1

    def get_target_residence_name(self, r_id: int) -> str:
        try:
            with self.db.get_connection() as conn:
                row = conn.execute("SELECT name FROM residences WHERE id = ?", (r_id,)).fetchone()
                if row and row[0]:
                    return row[0]
        except Exception:
            pass
        return f"الإقامة {r_id}"

    def get_selected_pull_residence_id(self) -> int:
        if hasattr(self, 'cmb_pull_residence') and self.cmb_pull_residence.currentData():
            return int(self.cmb_pull_residence.currentData())
        return self.get_target_residence_id()

    def get_selected_pull_residence_name(self, r_id: int) -> str:
        if hasattr(self, 'cmb_pull_residence') and self.cmb_pull_residence.currentData() == r_id:
            txt = self.cmb_pull_residence.currentText()
            return txt.split(" (معرف")[0] if " (معرف" in txt else txt
        return self.get_target_residence_name(r_id)

    def set_residence(self, residence_id: int, residence_name: Optional[str] = None):
        self.residence_id = residence_id
        if hasattr(self, 'cmb_pull_residence'):
            self.cmb_pull_residence.blockSignals(True)
            for idx in range(self.cmb_pull_residence.count()):
                if self.cmb_pull_residence.itemData(idx) == residence_id:
                    self.cmb_pull_residence.setCurrentIndex(idx)
                    break
            self.cmb_pull_residence.blockSignals(False)


    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        attach_smooth_scroll(scroll)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        # -------------------------------------------------------------
        # 1. إعدادات المؤسسة والنظام
        # -------------------------------------------------------------
        settings_panel = QFrame()
        settings_panel.setProperty("class", "content-panel")
        s_layout = QVBoxLayout(settings_panel)

        s_title = QLabel("إعدادات المؤسسة ونظام المحاسبة المخزنية")
        s_title.setProperty("class", "section-title")
        s_layout.addWidget(s_title)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_residence = QLineEdit()
        self.txt_directorate = QLineEdit()
        self.txt_year = QLineEdit()
        self.cmb_cost_mode = QComboBox()
        self.cmb_cost_mode.addItem("السعر التعاقدي الثابت (المعتمد في دفتر شروط الإقامة)", "FIXED")
        self.cmb_cost_mode.addItem("التكلفة المتوسطة المرجحة التلقائية (PMP/CMP)", "PMP")

        self.cmb_negative_alert = QComboBox()
        self.cmb_negative_alert.addItem("نعم - منع الإخراج إذا كان المخزون غير كافٍ (حماية قصوى)", "1")
        self.cmb_negative_alert.addItem("لا - السماح بالإخراج مع التنبيه فقط", "0")

        self.txt_residence.textChanged.connect(self.on_input_modified)
        self.txt_directorate.textChanged.connect(self.on_input_modified)
        self.txt_year.textChanged.connect(self.on_input_modified)
        self.cmb_cost_mode.currentIndexChanged.connect(self.on_input_modified)
        self.cmb_negative_alert.currentIndexChanged.connect(self.on_input_modified)

        form.addRow("اسم الإقامة الجامعية:", self.txt_residence)
        form.addRow("مديرية الخدمات الجامعية:", self.txt_directorate)
        form.addRow("السنة المالية / الجامعية:", self.txt_year)
        form.addRow("طريقة تقييم تكلفة المخزون:", self.cmb_cost_mode)
        form.addRow("منع الرصيد السالب:", self.cmb_negative_alert)

        s_layout.addLayout(form)

        btn_save_settings = QPushButton("حفظ الإعدادات العامة ✔")
        btn_save_settings.setProperty("class", "btn-primary")
        btn_save_settings.clicked.connect(self.save_settings)
        s_layout.addWidget(btn_save_settings)

        layout.addWidget(settings_panel)

        # -------------------------------------------------------------
        # 2. النسخ الاحتياطي التلقائي واليدوي
        # -------------------------------------------------------------
        backup_panel = QFrame()
        backup_panel.setProperty("class", "content-panel")
        b_layout = QVBoxLayout(backup_panel)

        b_title = QLabel("إدارة النسخ الاحتياطي والأمان (Backup & Restore)")
        b_title.setProperty("class", "section-title")
        b_layout.addWidget(b_title)

        # بطاقة إعدادات النسخ الاحتياطي التلقائي اليومي
        auto_card = QFrame()
        auto_card.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1.5px solid #0D9488;
                border-radius: 8px;
                padding: 14px;
            }
        """)
        ac_layout = QVBoxLayout(auto_card)
        ac_layout.setSpacing(10)

        ac_header = QHBoxLayout()
        lbl_auto_title = QLabel("⏰ إعدادات الحفظ الاحتياطي اليومي التلقائي (خاص بهذا الجهاز)")
        lbl_auto_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2DD4BF;")
        ac_header.addWidget(lbl_auto_title)
        ac_header.addStretch()
        ac_layout.addLayout(ac_header)

        lbl_auto_desc = QLabel("يقوم البرنامج بأخذ نسخة احتياطية آمنة تلقائياً كل يوم في الوقت والمجلد المحددين، لضمان عدم ضياع أي بيانات على هذا الجهاز بشكل مستقل تماماً.")
        lbl_auto_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        lbl_auto_desc.setWordWrap(True)
        ac_layout.addWidget(lbl_auto_desc)

        # خيار التفعيل
        self.chk_auto_backup = QCheckBox("تفعيل الحفظ الاحتياطي اليومي التلقائي لهذا الجهاز")
        self.chk_auto_backup.setStyleSheet("font-weight: bold; font-size: 13px; color: #F8FAFC;")
        self.chk_auto_backup.toggled.connect(self.on_auto_backup_toggled)
        ac_layout.addWidget(self.chk_auto_backup)

        # شبكة إدخال الوقت والمجلد
        auto_form = QFormLayout()
        auto_form.setSpacing(10)

        # 1. تحديد الوقت
        time_box = QHBoxLayout()
        self.time_auto_backup = QTimeEdit()
        self.time_auto_backup.setDisplayFormat("HH:mm")
        self.time_auto_backup.setTime(QTime(16, 0))
        self.time_auto_backup.setFixedHeight(34)
        self.time_auto_backup.setFixedWidth(130)
        self.time_auto_backup.setStyleSheet("font-weight: bold; font-size: 13px;")

        lbl_time_hint = QLabel("💡 التوقيت الموصى به: وقت نهاية الدوام الرسمي (مثلاً 16:00 أو 18:00)")
        lbl_time_hint.setStyleSheet("color: #64748B; font-size: 11px;")

        time_box.addWidget(self.time_auto_backup)
        time_box.addWidget(lbl_time_hint)
        time_box.addStretch()
        auto_form.addRow("⏰ وقت الحفظ اليومي التلقائي:", time_box)

        # 2. تحديد المجلد
        dir_box = QHBoxLayout()
        dir_box.setSpacing(8)

        self.txt_backup_dir = QLineEdit()
        self.txt_backup_dir.setFixedHeight(34)
        self.txt_backup_dir.setPlaceholderText("اختر مجلد الحفظ (قرص محلي D:\\ أو فلاش ديسك USB خارجي)...")

        btn_browse_dir = QPushButton("تصفح واختيار مجلد... 📁")
        btn_browse_dir.setFixedHeight(34)
        btn_browse_dir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_browse_dir.clicked.connect(self.browse_backup_dir)

        btn_open_dir = QPushButton("فتح المجلد ↗️")
        btn_open_dir.setFixedHeight(34)
        btn_open_dir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_open_dir.clicked.connect(self.open_current_backup_dir)

        dir_box.addWidget(self.txt_backup_dir)
        dir_box.addWidget(btn_browse_dir)
        dir_box.addWidget(btn_open_dir)
        auto_form.addRow("📁 مجلد حفظ النسخ الاحتياطية:", dir_box)

        ac_layout.addLayout(auto_form)

        # أزرار حفظ إعدادات الحفظ التلقائي وتجربتها
        auto_btns = QHBoxLayout()
        auto_btns.setSpacing(10)

        btn_save_auto_cfg = QPushButton("حفظ إعدادات الحفظ التلقائي لهذا الجهاز ✔")
        btn_save_auto_cfg.setProperty("class", "btn-primary")
        btn_save_auto_cfg.setFixedHeight(36)
        btn_save_auto_cfg.clicked.connect(self.save_auto_backup_settings)

        btn_test_auto_backup = QPushButton("⚡ تجربة النسخ الفوري الآن في المجلد المختار")
        btn_test_auto_backup.setProperty("class", "btn-secondary")
        btn_test_auto_backup.setFixedHeight(36)
        btn_test_auto_backup.clicked.connect(self.test_auto_backup_now)

        auto_btns.addWidget(btn_save_auto_cfg)
        auto_btns.addWidget(btn_test_auto_backup)
        auto_btns.addStretch()
        ac_layout.addLayout(auto_btns)

        # شارة الحالة للتذكير
        self.lbl_auto_status = QLabel()
        self.lbl_auto_status.setStyleSheet("""
            background-color: rgba(13, 148, 136, 0.15);
            border: 1px solid #0D9488;
            border-radius: 6px;
            padding: 8px 12px;
            color: #5EEAD4;
            font-size: 12px;
            font-weight: bold;
        """)
        ac_layout.addWidget(self.lbl_auto_status)

        b_layout.addWidget(auto_card)

        # أزرار العمليات اليدوية
        lbl_manual_title = QLabel("النسخ الاحتياطي اليدوي الفوري والاسترجاع:")
        lbl_manual_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #CBD5E1; margin-top: 10px;")
        b_layout.addWidget(lbl_manual_title)

        b_btn_layout = QHBoxLayout()
        btn_create_backup = QPushButton("إنشاء نسخة احتياطية فورية الآن 💾")
        btn_create_backup.setProperty("class", "btn-success")
        btn_create_backup.clicked.connect(self.create_backup)

        btn_restore_backup = QPushButton("استرجاع نسخة احتياطية من ملف ↺")
        btn_restore_backup.setProperty("class", "btn-danger")
        btn_restore_backup.clicked.connect(self.restore_backup)

        btn_refresh_list = QPushButton("تحديث قائمة النسخ ⟳")
        btn_refresh_list.setProperty("class", "btn-secondary")
        btn_refresh_list.clicked.connect(self.load_backups_list)

        b_btn_layout.addWidget(btn_create_backup)
        b_btn_layout.addWidget(btn_restore_backup)
        b_btn_layout.addWidget(btn_refresh_list)
        b_btn_layout.addStretch()
        b_layout.addLayout(b_btn_layout)

        # جدول النسخ الاحتياطية المتوفرة
        self.table_backups = QTableWidget()
        self.table_backups.setColumnCount(4)
        self.table_backups.setMinimumHeight(150)
        self.table_backups.setMaximumHeight(240)
        self.table_backups.setHorizontalHeaderLabels(["اسم ملف النسخة الاحتياطية", "النوع", "الحجم", "تاريخ الإنشاء"])
        self.table_backups.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_backups.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_backups.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_backups.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        attach_smooth_scroll(self.table_backups)
        b_layout.addWidget(self.table_backups)

        layout.addWidget(backup_panel)

        # -------------------------------------------------------------
        # 3. الربط الشبكي والسحابي ومزامنة الإقامات (Cloud & Network Sync) 🌐
        # -------------------------------------------------------------
        net_panel = QFrame()
        net_panel.setProperty("class", "content-panel")
        np_layout = QVBoxLayout(net_panel)

        np_title = QLabel("الربط السحابي والشبكي لتبادل البيانات مع الإقامات والمديرية 🌐")
        np_title.setProperty("class", "section-title")
        np_layout.addWidget(np_title)

        np_desc = QLabel(
            "ربط المديرية مع الإقامات الجامعية لتبادل الإعارات، ومزامنة بطاقات الجرد، ومتابعة الاستهلاك اليومي "
            "عبر شبكة الإنترنت (استضافة سحابية Cloud / شبكة مشفرة Tailscale VPN / أو شبكة محلية LAN)."
        )
        np_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        np_desc.setWordWrap(True)
        np_layout.addWidget(np_desc)

        net_card = QFrame()
        net_card.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1.5px solid #6366F1;
                border-radius: 8px;
                padding: 14px;
            }
        """)
        nc_layout = QVBoxLayout(net_card)
        nc_layout.setSpacing(10)

        self.lbl_net_mode = QLabel()
        self.lbl_net_mode.setStyleSheet("font-size: 13px; font-weight: bold; color: #A5B4FC;")
        nc_layout.addWidget(self.lbl_net_mode)

        self.lbl_net_url = QLabel()
        self.lbl_net_url.setStyleSheet("font-size: 12px; color: #CBD5E1;")
        nc_layout.addWidget(self.lbl_net_url)

        self.lbl_net_status = QLabel()
        self.lbl_net_status.setStyleSheet("font-size: 12px; color: #34D399; font-weight: bold;")
        nc_layout.addWidget(self.lbl_net_status)

        net_btns = QHBoxLayout()
        btn_open_net_cfg = QPushButton("⚙️ ضبط إعدادات الربط السحابي والشبكة عبر الإنترنت (Cloud / VPN / Local)")
        btn_open_net_cfg.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #6366F1);
            color: #FFFFFF;
            font-weight: bold;
            font-size: 13px;
            padding: 8px 18px;
            border-radius: 6px;
        """)
        btn_open_net_cfg.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_open_net_cfg.clicked.connect(self.open_network_settings_dialog)
        net_btns.addWidget(btn_open_net_cfg)
        net_btns.addStretch()
        nc_layout.addLayout(net_btns)

        np_layout.addWidget(net_card)
        layout.addWidget(net_panel)

        # -------------------------------------------------------------
        # 4. تحديثات المنظومة والإصدارات (System Updates & Patches)
        # -------------------------------------------------------------
        update_panel = QFrame()
        update_panel.setProperty("class", "content-panel")
        up_layout = QVBoxLayout(update_panel)

        up_title = QLabel("تحديثات المنظومة وترقية الواجهات (System Updates) 🚀")
        up_title.setProperty("class", "section-title")
        up_layout.addWidget(up_title)

        up_desc = QLabel("إرسال وتثبيت تحديثات الواجهات والتقارير بنقرة زر واحدة عبر فلاشة USB أو عبر الإنترنت، مع حماية تامة واستقلالية مطلقة لقاعدة البيانات والبيانات المخزنية.")
        up_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        up_desc.setWordWrap(True)
        up_layout.addWidget(up_desc)

        up_card = QFrame()
        up_card.setStyleSheet("background-color: rgba(15, 23, 42, 0.6); border: 1.5px solid #0284C7; border-radius: 8px; padding: 14px;")
        uc_l = QVBoxLayout(up_card)
        uc_l.setSpacing(10)

        info_row = QHBoxLayout()
        from core.update_service import UpdateService
        curr_ver = UpdateService.get_current_version()
        self.lbl_curr_ver = QLabel(f"📦 الإصدار المثبت حالياً: {curr_ver}")
        self.lbl_curr_ver.setStyleSheet("font-size: 13px; font-weight: bold; color: #38BDF8;")

        lbl_data_safe = QLabel("🛡️ قاعدة البيانات والوصولات مستقلة ومحمية 100%")
        lbl_data_safe.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold;")

        info_row.addWidget(self.lbl_curr_ver)
        info_row.addStretch()
        info_row.addWidget(lbl_data_safe)
        uc_l.addLayout(info_row)

        up_btns = QHBoxLayout()
        up_btns.setSpacing(10)
        btn_open_update_center = QPushButton("فتح مركز التحديثات (فلاشة USB / الإنترنت) 🚀")
        btn_open_update_center.setStyleSheet("background-color: #0284C7; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        btn_open_update_center.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_open_update_center.clicked.connect(self.open_update_dialog)

        btn_quick_usb = QPushButton("فحص وتثبيت فوري من فلاشة USB المتصلة 💾")
        btn_quick_usb.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        btn_quick_usb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_quick_usb.clicked.connect(self.quick_usb_update)

        up_btns.addWidget(btn_open_update_center)
        up_btns.addWidget(btn_quick_usb)
        up_btns.addStretch()
        uc_l.addLayout(up_btns)

        up_layout.addWidget(up_card)
        layout.addWidget(update_panel)

        # -------------------------------------------------------------
        # 4. حالة الترخيص وقفل الأمان بالعتاد (Anti-Theft Node-Locking)
        # -------------------------------------------------------------
        lic_panel = QFrame()
        lic_panel.setProperty("class", "content-panel")
        lp_layout = QVBoxLayout(lic_panel)

        lp_title = QLabel("الأمان وقفل الترخيص بالعتاد (Anti-Theft Protection) 🔐")
        lp_title.setProperty("class", "section-title")
        lp_layout.addWidget(lp_title)

        lic_card = QFrame()
        lic_card.setStyleSheet("background-color: rgba(15, 23, 42, 0.6); border: 1.5px solid #475569; border-radius: 8px; padding: 14px;")
        lc_l = QVBoxLayout(lic_card)
        lc_l.setSpacing(8)

        from core.license_service import LicenseService
        mach_code = LicenseService.get_machine_code()
        is_lic, lic_msg, lic_data = LicenseService.is_licensed()

        lbl_mach = QLabel(f"💻 كود عتاد هذا الحاسوب (Machine Fingerprint): {mach_code}")
        lbl_mach.setStyleSheet("font-size: 13px; font-weight: bold; color: #F8FAFC;")
        lc_l.addWidget(lbl_mach)

        if is_lic:
            licensed_to = lic_data.get("licensed_to", "مديرية الخدمات الجامعية") if lic_data else "معتمد"
            act_date = lic_data.get("activation_date", "2026") if lic_data else ""
            lbl_lic_status = QLabel(f"✅ النسخة مرخصة ومقفلة على عتاد هذا الحاسوب حصرياً | الجهة المرخص لها: {licensed_to} (تاريخ التفعيل: {act_date})")
            lbl_lic_status.setStyleSheet("color: #34D399; font-weight: bold; font-size: 12px;")
        else:
            lbl_lic_status = QLabel("⚠️ هذا الجهاز غير مرخص أو تم نقله من حاسوب آخر دون إذن!")
            lbl_lic_status.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 12px;")
        lc_l.addWidget(lbl_lic_status)

        btn_manage_lic = QPushButton("إدارة وتحديث الترخيص أو تفعيل فلاشة 🔑")
        btn_manage_lic.setStyleSheet("background-color: #334155; color: #FCD34D; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        btn_manage_lic.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_manage_lic.clicked.connect(self.open_activation_dialog)
        lc_l.addWidget(btn_manage_lic)

        lp_layout.addWidget(lic_card)
        layout.addWidget(lic_panel)

        # -------------------------------------------------------------
        # 5. كود مديرية الخدمات الجامعية والأمان الموحد
        # -------------------------------------------------------------
        dir_code_panel = QFrame()
        dir_code_panel.setProperty("class", "content-panel")
        dcp_layout = QVBoxLayout(dir_code_panel)

        dcp_title = QLabel("كود مديرية الخدمات الجامعية والأمان الموحد 🔐")
        dcp_title.setProperty("class", "section-title")
        dcp_layout.addWidget(dcp_title)

        dcp_card = QFrame()
        dcp_card.setStyleSheet("background-color: rgba(15, 23, 42, 0.6); border: 1.5px solid #F59E0B; border-radius: 8px; padding: 14px;")
        dcp_card_l = QVBoxLayout(dcp_card)
        dcp_card_l.setSpacing(8)

        lbl_code_info = QLabel("🏢 كود المديرية هو كود أمان موحد يحمي: واجهة الربط الشبكي، واجهة النسخ الاحتياطي، وواجهة الإعدادات العامة، وهو مطابق دائماً لكلمة مرور المدير العام.")
        lbl_code_info.setStyleSheet("color: #FCD34D; font-weight: bold; font-size: 12px;")
        lbl_code_info.setWordWrap(True)
        dcp_card_l.addWidget(lbl_code_info)

        lbl_code_sub = QLabel("عند تغيير كود المديرية من هنا أو من إدارة المستخدمين، يتغير تلقائياً في كافة هذه الواجهات ليصبح دائماً نفس الكود.")
        lbl_code_sub.setStyleSheet("color: #CBD5E1; font-size: 11px;")
        dcp_card_l.addWidget(lbl_code_sub)

        btn_change_dir_code = QPushButton("🔐 تغيير كود المديرية الموحد (الربط، النسخ الاحتياطي، الإعدادات)...")
        btn_change_dir_code.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D97706, stop:1 #F59E0B); color: #0F172A; font-weight: bold; padding: 8px 16px; border-radius: 6px; font-size: 12px;")
        btn_change_dir_code.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_change_dir_code.clicked.connect(self.open_change_directorate_code_dialog)
        dcp_card_l.addWidget(btn_change_dir_code)

        dcp_layout.addWidget(dcp_card)
        layout.addWidget(dir_code_panel)

        # -------------------------------------------------------------
        # 6. سحب واسترجاع بيانات الإقامة من المديرية (عزل تام وشامل)
        # -------------------------------------------------------------
        pull_panel = QFrame()
        pull_panel.setProperty("class", "content-panel")
        pp_layout = QVBoxLayout(pull_panel)

        pp_title = QLabel("سحب واسترجاع بيانات الإقامة من المديرية 📥")
        pp_title.setProperty("class", "section-title")
        pp_layout.addWidget(pp_title)

        pp_card = QFrame()
        pp_card.setStyleSheet(
            "background-color: rgba(15, 23, 42, 0.7); "
            "border: 1.5px solid #0EA5E9; "
            "border-radius: 8px; padding: 14px;"
        )
        pp_card_l = QVBoxLayout(pp_card)
        pp_card_l.setSpacing(10)

        # اختيار الإقامة المستهدفة بالسحب عبر قائمة منسدلة واضحة
        res_sel_layout = QHBoxLayout()
        res_sel_layout.setSpacing(10)
        lbl_res_sel = QLabel("🏢 اختر الإقامة المراد سحب واسترجاع كافة بياناتها من المديرية:")
        lbl_res_sel.setStyleSheet("color: #F8FAFC; font-weight: bold; font-size: 13px;")
        res_sel_layout.addWidget(lbl_res_sel)

        self.cmb_pull_residence = QComboBox()
        self.cmb_pull_residence.setStyleSheet(
            "background-color: #0F172A; color: #38BDF8; font-weight: bold; font-size: 13px; "
            "border: 1.5px solid #0EA5E9; padding: 6px 14px; border-radius: 6px;"
        )
        curr_t_id = self.get_target_residence_id()
        try:
            with self.db.get_connection() as conn:
                res_rows = conn.execute("SELECT id, name, code FROM residences ORDER BY id ASC").fetchall()
                for r in res_rows:
                    self.cmb_pull_residence.addItem(f"{r['name']} (معرف رقم: {r['id']})", r['id'])
        except Exception:
            pass

        for idx in range(self.cmb_pull_residence.count()):
            if self.cmb_pull_residence.itemData(idx) == curr_t_id:
                self.cmb_pull_residence.setCurrentIndex(idx)
                break

        res_sel_layout.addWidget(self.cmb_pull_residence)
        pp_card_l.addLayout(res_sel_layout)

        # التنبيه والإيضاح
        lbl_pull_desc = QLabel(
            "تتيح هذه الخاصية سحب واسترجاع كافة البيانات التاريخية للإقامة المحددة أعلاه دفعة واحدة من قاعدة بيانات المديرية "
            "(وصولات الدخول، وصولات الخروج، بطاقات اليومية للوجبات، حركات المخزون، وأرصدة المواد).\n"
            "🔒 العملية يدوية تماماً وتتمتع بنظام العزل التام: لا تمس ولا تسحب أي بيانات تخص الإقامات الأخرى إطلاقاً."
        )
        lbl_pull_desc.setStyleSheet("color: #E2E8F0; font-size: 11px; line-height: 1.4;")
        lbl_pull_desc.setWordWrap(True)
        pp_card_l.addWidget(lbl_pull_desc)

        # أزرار السحب الثلاثية (سحابي ذكي + أوفلاين فوري + ملف مخصص)
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        self.btn_pull_residence = QPushButton("📥 سحب جميع بيانات إقامتي من بيانات المديرية (سحابي / محلي)")
        self.btn_pull_residence.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #0EA5E9); "
            "color: #FFFFFF; font-weight: bold; padding: 10px 16px; border-radius: 6px; font-size: 12px;"
        )
        self.btn_pull_residence.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pull_residence.clicked.connect(self.on_pull_residence_clicked)
        btn_box.addWidget(self.btn_pull_residence)

        self.btn_pull_instant_offline = QPushButton("⚡ استرجاع فوري لبيانات الإقامة (أوفلاين بدون إنترنت)")
        self.btn_pull_instant_offline.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981); "
            "color: #FFFFFF; font-weight: bold; padding: 10px 16px; border-radius: 6px; font-size: 12px;"
        )
        self.btn_pull_instant_offline.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pull_instant_offline.clicked.connect(self.on_pull_instant_offline_clicked)
        btn_box.addWidget(self.btn_pull_instant_offline)

        self.btn_pull_res_file = QPushButton("📂 اختيار ملف DB (USB)")
        self.btn_pull_res_file.setStyleSheet(
            "background-color: #1E293B; border: 1px solid #475569; color: #CBD5E1; "
            "font-weight: bold; padding: 10px 12px; border-radius: 6px; font-size: 11px;"
        )
        self.btn_pull_res_file.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pull_res_file.clicked.connect(self.on_pull_residence_from_file_clicked)
        btn_box.addWidget(self.btn_pull_res_file)

        pp_card_l.addLayout(btn_box)

        # تسمية الحالة والتقدم
        self.lbl_pull_status = QLabel("")
        self.lbl_pull_status.setStyleSheet("font-size: 12px; color: #38BDF8;")
        self.lbl_pull_status.setWordWrap(True)
        pp_card_l.addWidget(self.lbl_pull_status)

        pp_layout.addWidget(pp_card)
        layout.addWidget(pull_panel)

        # -------------------------------------------------------------
        # 5. أداة ترحيل ملفات الإكسل القديمة
        # -------------------------------------------------------------
        mig_panel = QFrame()
        mig_panel.setProperty("class", "content-panel")
        m_layout = QVBoxLayout(mig_panel)

        m_title = QLabel("ترحيل واستيراد البيانات من ملفات Excel القديمة (F:\\2026)")
        m_title.setProperty("class", "section-title")
        m_layout.addWidget(m_title)

        m_desc = QLabel("تتيح هذه الأداة قراءة جميع ملفات (FC01 إلى FC12) وملف الوضعية الثلاثية واستيراد المواد والحركات التاريخية مباشرة.")
        m_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        m_layout.addWidget(m_desc)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        m_layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 12px; color: #0D9488;")
        m_layout.addWidget(self.lbl_status)

        self.btn_run_migration = QPushButton("بدء استيراد وترحيل ملفات Excel 🚀")
        self.btn_run_migration.setProperty("class", "btn-primary")
        self.btn_run_migration.clicked.connect(self.start_migration)
        m_layout.addWidget(self.btn_run_migration)

        layout.addWidget(mig_panel)

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

    # -------------------------------------------------------------
    # منطق الإعدادات العامة
    # -------------------------------------------------------------
    def on_input_modified(self, *args):
        if not getattr(self, "is_loading", False):
            self.is_dirty = True

    def has_unsaved_changes(self) -> bool:
        return bool(getattr(self, "is_dirty", False))

    def save_changes(self) -> bool:
        self.save_settings(show_message=False)
        return True

    def discard_changes(self):
        self.load_settings()
        self.is_dirty = False

    def load_settings(self):
        self.is_loading = True
        try:
            self.txt_residence.setText(self.db.get_setting("residence_name") or "")
            self.txt_directorate.setText(self.db.get_setting("directorate_name") or "")
            self.txt_year.setText(self.db.get_setting("academic_year") or "2026")
            self.cmb_cost_mode.setCurrentIndex(0 if self.db.get_setting("cost_calculation_mode") == "FIXED" else 1)
            self.cmb_negative_alert.setCurrentIndex(0 if self.db.get_setting("alert_on_negative_stock") == "1" else 1)

            # تحميل إعدادات الحفظ التلقائي لهذا الجهاز من AppConfig ومن DB
            is_enabled = AppConfig.get("auto_backup_enabled", True)
            time_str = AppConfig.get("auto_backup_time", "16:00")
            custom_dir = AppConfig.get("auto_backup_dir", "")
            if not custom_dir:
                custom_dir = self.backup_svc.get_backup_dir()

            self.chk_auto_backup.setChecked(bool(is_enabled))
            t_parts = time_str.split(":")
            if len(t_parts) == 2:
                try:
                    self.time_auto_backup.setTime(QTime(int(t_parts[0]), int(t_parts[1])))
                except Exception:
                    self.time_auto_backup.setTime(QTime(16, 0))

            self.txt_backup_dir.setText(custom_dir)
            self.update_auto_status_label()
            self.update_network_status_card()
        finally:
            self.is_loading = False
            self.is_dirty = False

    def save_settings(self, show_message: bool = True):
        from ui.widgets.directorate_auth_dialog import DirectorateAuthDialog
        if not DirectorateAuthDialog.verify(self, "حفظ وتعديل إعدادات المؤسسة والنظام", self.db):
            return

        self.db.set_setting("residence_name", self.txt_residence.text().strip())
        self.db.set_setting("directorate_name", self.txt_directorate.text().strip())
        self.db.set_setting("academic_year", self.txt_year.text().strip())
        self.db.set_setting("cost_calculation_mode", self.cmb_cost_mode.currentData())
        self.db.set_setting("alert_on_negative_stock", self.cmb_negative_alert.currentData())
        self.is_dirty = False
        if show_message:
            QMessageBox.information(self, "نجاح", "تم حفظ الإعدادات العامة بنجاح!")

    # -------------------------------------------------------------
    # منطق الحفظ التلقائي اليومي
    # -------------------------------------------------------------
    def on_auto_backup_toggled(self, checked: bool):
        self.time_auto_backup.setEnabled(checked)
        self.txt_backup_dir.setEnabled(checked)
        self.update_auto_status_label()

    def browse_backup_dir(self):
        curr_dir = self.txt_backup_dir.text().strip()
        if not os.path.isdir(curr_dir):
            curr_dir = self.backup_svc.get_backup_dir()

        chosen_dir = QFileDialog.getExistingDirectory(
            self, "اختر مجلد حفظ النسخ الاحتياطية (محلي أو خارجي)", curr_dir
        )
        if chosen_dir:
            self.txt_backup_dir.setText(chosen_dir)
            self.update_auto_status_label()

    def open_current_backup_dir(self):
        target_dir = self.txt_backup_dir.text().strip() or self.backup_svc.get_backup_dir()
        if os.path.isdir(target_dir):
            try:
                os.startfile(target_dir)
            except Exception as e:
                QDesktopServices.openUrl(QUrl.fromLocalFile(target_dir))
        else:
            QMessageBox.warning(self, "تنبيه", f"المجلد المحدد غير موجود حالياً:\n{target_dir}")

    def save_auto_backup_settings(self):
        from ui.widgets.directorate_auth_dialog import DirectorateAuthDialog
        if not DirectorateAuthDialog.verify(self, "تعديل إعدادات الحفظ الاحتياطي اليومي التلقائي", self.db):
            return

        enabled = self.chk_auto_backup.isChecked()
        time_str = self.time_auto_backup.time().toString("HH:mm")
        dir_str = self.txt_backup_dir.text().strip()

        if enabled and dir_str:
            try:
                os.makedirs(dir_str, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "خطأ في المجلد", f"تعذر إنشاء المجلد المحدد:\n{e}")
                return

        # حفظ محلياً في AppConfig خاص بهذا الجهاز
        AppConfig.set("auto_backup_enabled", enabled)
        AppConfig.set("auto_backup_time", time_str)
        AppConfig.set("auto_backup_dir", dir_str)

        # حفظ احتياطي في قاعدة البيانات
        try:
            self.db.set_setting("auto_backup_enabled", "1" if enabled else "0")
            self.db.set_setting("auto_backup_time", time_str)
            self.db.set_setting("auto_backup_dir", dir_str)
        except Exception:
            pass

        self.update_auto_status_label()
        QMessageBox.information(
            self, "تم الحفظ بنجاح",
            f"تم حفظ إعدادات الحفظ الاحتياطي اليومي لهذا الجهاز بنجاح!\n\n"
            f"• الحالة: {'مفعّل ✅' if enabled else 'معطّل ⏸️'}\n"
            f"• التوقيت: الساعة {time_str} يومياً\n"
            f"• المجلد: {dir_str or self.backup_svc.get_backup_dir()}"
        )

    def test_auto_backup_now(self):
        target_dir = self.txt_backup_dir.text().strip() or self.backup_svc.get_backup_dir()
        try:
            os.makedirs(target_dir, exist_ok=True)
            file_path = self.backup_svc.create_backup(custom_path=target_dir, prefix="auto_test")
            self.load_backups_list()
            QMessageBox.information(
                self, "نجاح النسخ التجريبي",
                f"تم إنشاء نسخة احتياطية تجريبية بنجاح في المجلد المحدد!\n\n"
                f"• مسار الملف:\n{file_path}\n\n"
                f"نظام الحفظ التلقائي يعمل بأمان وجاهز تماماً."
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ في النسخ", f"تعذر إنشاء النسخة في المجلد المحدد:\n{e}")

    def update_auto_status_label(self):
        enabled = self.chk_auto_backup.isChecked()
        time_str = self.time_auto_backup.time().toString("HH:mm")
        target_dir = self.txt_backup_dir.text().strip() or self.backup_svc.get_backup_dir()
        last_date = AppConfig.get("last_auto_backup_date", "")

        if enabled:
            last_info = f"  |  ✅ تم الحفظ اليوم بنجاح ({last_date})" if last_date == datetime.date.today().isoformat() else ""
            self.lbl_auto_status.setText(
                f"🟢 الحفظ التلقائي مفعّل: يتم الحفظ يومياً في تمام الساعة [{time_str}] في المجلد: [{target_dir}]{last_info}"
            )
            self.lbl_auto_status.setStyleSheet("""
                background-color: rgba(13, 148, 136, 0.15);
                border: 1px solid #0D9488;
                border-radius: 6px;
                padding: 8px 12px;
                color: #5EEAD4;
                font-size: 12px;
                font-weight: bold;
            """)
        else:
            self.lbl_auto_status.setText("⚪ الحفظ الاحتياطي اليومي التلقائي معطّل حالياً على هذا الجهاز.")
            self.lbl_auto_status.setStyleSheet("""
                background-color: rgba(100, 116, 139, 0.15);
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 8px 12px;
                color: #94A3B8;
                font-size: 12px;
                font-weight: bold;
            """)

    # -------------------------------------------------------------
    # منطق النسخ والاسترجاع اليدوي
    # -------------------------------------------------------------
    def create_backup(self):
        from ui.widgets.directorate_auth_dialog import DirectorateAuthDialog
        if not DirectorateAuthDialog.verify(self, "إنشاء نسخة احتياطية لقاعدة البيانات", self.db):
            return

        try:
            target_dir = self.txt_backup_dir.text().strip() or self.backup_svc.get_backup_dir()
            path = self.backup_svc.create_backup(custom_path=target_dir, prefix="manual_backup")
            QMessageBox.information(self, "نجاح النسخ الاحتياطي", f"تم إنشاء النسخة الاحتياطية بنجاح في:\n{path}")
            self.load_backups_list()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر إنشاء النسخة: {e}")

    def restore_backup(self):
        from ui.widgets.directorate_auth_dialog import DirectorateAuthDialog
        if not DirectorateAuthDialog.verify(self, "استرجاع قاعدة البيانات من نسخة احتياطية (عملية حساسة)", self.db):
            return

        target_dir = self.txt_backup_dir.text().strip() or self.backup_svc.get_backup_dir()
        path, _ = QFileDialog.getOpenFileName(self, "اختر ملف النسخة الاحتياطية", target_dir, "Database Files (*.db)")
        if not path:
            return

        reply = QMessageBox.question(
            self, "تأكيد الاسترجاع",
            "تحذير هام: سيتم استبدال قاعدة البيانات الحالية بالبيانات الموجودة في النسخة المحددة!\nهل أنت متأكد من المتابعة؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.backup_svc.restore_backup(path)
                QMessageBox.information(self, "تم الاسترجاع", "تم استرجاع قاعدة البيانات بنجاح!\nيرجى إعادة تشغيل البرنامج لتطبيق كافة البيانات.")
                self.load_backups_list()
            except Exception as e:
                QMessageBox.critical(self, "خطأ في الاسترجاع", str(e))

    def load_backups_list(self):
        backups = self.backup_svc.list_backups()
        self.table_backups.clearContents()
        self.table_backups.setRowCount(len(backups))
        for r, b in enumerate(backups):
            self.table_backups.setItem(r, 0, QTableWidgetItem(b["filename"]))

            type_item = QTableWidgetItem(b.get("backup_type", "يدوي فوري 💾"))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_backups.setItem(r, 1, type_item)

            size_item = QTableWidgetItem(f"{b['size_kb']} KB")
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_backups.setItem(r, 2, size_item)

            date_item = QTableWidgetItem(b["created_at"])
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_backups.setItem(r, 3, date_item)

    # -------------------------------------------------------------
    # منطق ترحيل الإكسل
    # -------------------------------------------------------------
    def start_migration(self):
        reply = QMessageBox.question(
            self, "تأكيد الترحيل",
            "سيقوم البرنامج بقراءة ملفات الإكسل من F:\\2026 وترحيل كافة المواد والحركات التاريخية.\nهل ترغب في البدء؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_run_migration.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(5)
        self.lbl_status.setText("جاري تهيئة عملية الترحيل...")

        self.worker = MigrationWorker()
        self.worker.progress.connect(self.on_migration_progress)
        self.worker.finished.connect(self.on_migration_finished)
        self.worker.error.connect(self.on_migration_error)
        self.worker.start()

    def on_migration_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.lbl_status.setText(msg)

    def on_migration_finished(self, stats):
        self.btn_run_migration.setEnabled(True)
        self.progress_bar.setValue(100)
        self.lbl_status.setText("اكتمل الترحيل بنجاح تام!")
        QMessageBox.information(
            self, "اكتمل الترحيل",
            f"تم استيراد كافة البيانات بنجاح!\n"
            f"• المواد المستوردة: {stats['articles_imported']} مادة\n"
            f"• وصولات الاستلام: {stats['entry_vouchers']} وصل\n"
            f"• وصولات الإخراج: {stats['exit_vouchers']} وصل\n"
            f"• أيام تذاكر الوجبات: {stats['meal_days_tracked']} يوم"
        )

    def on_migration_error(self, err):
        self.btn_run_migration.setEnabled(True)
        self.lbl_status.setText(f"خطأ أثناء الترحيل: {err}")
        QMessageBox.critical(self, "فشل الترحيل", f"حدث خطأ أثناء قراءة ملفات الإكسل:\n{err}")

    def open_update_dialog(self):
        from ui.update_dialog import UpdateDialog
        dlg = UpdateDialog(parent=self)
        dlg.exec()

    def quick_usb_update(self):
        from core.update_service import UpdateService
        patches = UpdateService.scan_usb_drives_for_patches()
        if not patches:
            QMessageBox.information(
                self, "فحص الفلاشة USB",
                "لم يتم العثور على أي ملف تحديث (.dou_patch) في الفلاشات المتصلة حالياً.\n\n"
                "يرجى وضع ملف التحديث في الفلاشة أو فتح مركز التحديثات لاختيار ملف يدوياً."
            )
            return
        self.open_update_dialog()

    def open_activation_dialog(self):
        from ui.activation_dialog import ActivationDialog
        dlg = ActivationDialog(parent=self)
        if dlg.exec():
            # تحديث حالة الترخيص بعد التفعيل
            from core.license_service import LicenseService
            is_lic, lic_msg, lic_data = LicenseService.is_licensed()
            QMessageBox.information(self, "حالة الترخيص", "تم تحديث ترخيص الجهاز بنجاح!")

    def update_network_status_card(self):
        arch_mode = AppConfig.get("architecture_mode", "standalone")
        server_url = AppConfig.get_server_url()
        res_id = AppConfig.get("residence_id", 1)
        res_name = AppConfig.get("residence_name", "الإقامة الجامعية")
        auto_sync = AppConfig.get("auto_sync_enabled", True)
        sync_interval = AppConfig.get("sync_interval_seconds", 30)

        if arch_mode == "server":
            self.lbl_net_mode.setText("🏢 نمط التشغيل: خادم مركزي للمديرية (Central Directorate Server)")
            self.lbl_net_url.setText(f"📡 رابط الخادم المستضاف / المنفذ: {server_url} | الاستماع على جميع الواجهات 0.0.0.0")
            self.lbl_net_status.setText("🟢 يستقبل اتصالات الإقامات ومزامنة البيانات اللحظية")
        elif arch_mode == "client":
            self.lbl_net_mode.setText(f"🏫 نمط التشغيل: إقامة جامعية زبون (Client) - {res_name} (معرّف: #{res_id})")
            self.lbl_net_url.setText(f"🌐 عنوان خادم المديرية / السحابة المستهدفة: {server_url}")
            status_text = f"🔄 المزامنة التلقائية: {'مفعلة كل ' + str(sync_interval) + ' ثانية' if auto_sync else 'معطلة'}"
            self.lbl_net_status.setText(status_text)
        else:
            self.lbl_net_mode.setText("💻 نمط التشغيل: محلي مستقل (Standalone - Single Campus)")
            self.lbl_net_url.setText(f"ℹ️ رابط الخادم الافتراضي: {server_url}")
            self.lbl_net_status.setText("⚪ يعمل بشكل محلي دون اتصال بشبكة خارجية")

    def open_network_settings_dialog(self):
        from ui.widgets.network_settings_dialog import NetworkSettingsDialog
        if NetworkSettingsDialog.open_with_admin_auth(self.db, parent=self):
            self.update_network_status_card()

    def open_change_directorate_code_dialog(self):
        from ui.widgets.directorate_auth_dialog import DirectorateChangeCodeDialog
        dlg = DirectorateChangeCodeDialog(parent=self, db_manager=self.db)
        dlg.exec()



    def on_pull_residence_clicked(self):
        r_id = self.get_selected_pull_residence_id()
        r_name = self.get_selected_pull_residence_name(r_id)

        reply = QMessageBox.question(
            self,
            "تأكيد سحب بيانات الإقامة من المديرية",
            f"هل تريد سحب جميع بيانات إقامتك من بيانات المديرية؟\n\n"
            f"🏢 الإقامة المعنية: {r_name} (رقم: {r_id})\n\n"
            f"⚠️ ملاحظة هامة:\n"
            f"• سيتم سحب واسترجاع كافة وصولات الدخول والخروج وبطاقات اليومية للوجبات وحركات المخزون الخاصة بإقامتك حصراً.\n"
            f"• لن تتأثر أي إقامة أخرى إطلاقاً بفضل نظام العزل التام.\n"
            f"• يدعم النظام السحب عبر الشبكة/السحاب مع التحويل التلقائي الذكي لقاعدة البيانات الرسمية في حال انقطاع الإنترنت.\n\n"
            f"هل أنت متأكد من رغبتك في سحب البيانات الآن؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_pull_residence.setEnabled(False)
        if hasattr(self, 'btn_pull_instant_offline'):
            self.btn_pull_instant_offline.setEnabled(False)
        self.lbl_pull_status.setText(f"⏳ جاري فحص الاتصال وسحب بيانات {r_name} دفعة واحدة...")
        self.lbl_pull_status.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 12px;")

        self.pull_worker = PullResidenceWorker(r_id, self.db, from_db_path=None, parent=self)
        self.pull_worker.finished.connect(self._on_pull_finished)
        self.pull_worker.error.connect(self._on_pull_error)
        self.pull_worker.start()

    def on_pull_instant_offline_clicked(self):
        r_id = self.get_selected_pull_residence_id()
        r_name = self.get_selected_pull_residence_name(r_id)

        reply = QMessageBox.question(
            self,
            "استرجاع فوري لبيانات الإقامة (أوفلاين بدون إنترنت)",
            f"هل تريد استرجاع جميع بيانات إقامتك فوراً من قاعدة البيانات الرسمية المعتمدة (أوفلاين بدون إنترنت)؟\n\n"
            f"🏢 الإقامة المعنية: {r_name} (رقم: {r_id})\n\n"
            f"⚡ سيتم استخراج وتطبيق كافة السجلات الخاصة بإقامتك حصراً من النسخة المعتمدة.\n\n"
            f"هل تود المتابعة الآن؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        import os
        candidates = get_candidate_official_dbs()
        target_db = candidates[0] if candidates else None

        if not target_db:
            QMessageBox.warning(
                self,
                "الملف غير موجود",
                "لم يتم العثور على ملف قاعدة البيانات الرسمية على الفلاش ديسك H:\\ أو في مجلد البرنامج.\nيرجى التأكد من وصل الفلاش ديسك أو اختيار الملف يدوياً."
            )
            return

        self.btn_pull_residence.setEnabled(False)
        self.btn_pull_instant_offline.setEnabled(False)
        self.lbl_pull_status.setText(f"⏳ جاري الاسترجاع الفوري لبيانات {r_name} من الملف المعتمد...")
        self.lbl_pull_status.setStyleSheet("color: #10B981; font-weight: bold; font-size: 12px;")

        self.pull_worker = PullResidenceWorker(r_id, self.db, from_db_path=target_db, parent=self)
        self.pull_worker.finished.connect(self._on_pull_finished)
        self.pull_worker.error.connect(self._on_pull_error)
        self.pull_worker.start()

    def on_pull_residence_from_file_clicked(self):
        r_id = self.get_selected_pull_residence_id()
        r_name = self.get_selected_pull_residence_name(r_id)

        default_dir = "H:\\" if os.path.exists("H:\\") else os.getcwd()
        db_file, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف قاعدة بيانات المديرية للاسترجاع (USB أو قرص محلي)",
            default_dir,
            "ملفات قاعدة البيانات (*.db *.sqlite);;جميع الملفات (*.*)"
        )
        if not db_file:
            return

        reply = QMessageBox.question(
            self,
            "تأكيد سحب بيانات الإقامة من ملف قاعدة البيانات",
            f"هل تريد سحب جميع بيانات إقامتك من بيانات المديرية في الملف المختار؟\n\n"
            f"📁 الملف: {db_file}\n"
            f"🏢 الإقامة: {r_name} (رقم: {r_id})\n\n"
            f"هل تود المتابعة؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_pull_residence.setEnabled(False)
        if hasattr(self, 'btn_pull_instant_offline'):
            self.btn_pull_instant_offline.setEnabled(False)
        self.lbl_pull_status.setText(f"⏳ جاري قراءة واسترجاع بيانات {r_name} من الملف المختار...")
        self.lbl_pull_status.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 12px;")

        self.pull_worker = PullResidenceWorker(r_id, self.db, from_db_path=db_file, parent=self)
        self.pull_worker.finished.connect(self._on_pull_finished)
        self.pull_worker.error.connect(self._on_pull_error)
        self.pull_worker.start()

    def _on_pull_finished(self, res: dict):
        if hasattr(self, 'btn_pull_residence'):
            self.btn_pull_residence.setEnabled(True)
        if hasattr(self, 'btn_pull_instant_offline'):
            self.btn_pull_instant_offline.setEnabled(True)

        r_id = res.get("residence_id", 0)
        r_name = res.get("residence_name", "الإقامة")
        counts = res.get("counts", {})
        source_mode = res.get("source_mode", "ONLINE")

        mode_text = " (عبر خادم المديرية الشبكي)" if source_mode == "ONLINE" else " (من قاعدة البيانات الرسمية المعتمدة - أوفلاين)"
        self.lbl_pull_status.setText(f"✅ تم سحب واسترجاع جميع بيانات {r_name} بنجاح!{mode_text}")
        self.lbl_pull_status.setStyleSheet("color: #10B981; font-weight: bold; font-size: 12px;")

        details = (
            f"✅ تم سحب واسترجاع جميع بيانات إقامتك من بيانات المديرية بنجاح!\n\n"
            f"🏢 الإقامة المسترجعة: {r_name} (رقم: {r_id})\n"
            f"🌐 طريقة السحب: {mode_text.strip()}\n\n"
            f"📊 تفاصيل السجلات المسترجعة:\n"
            f"  • أوراق الاستهلاك اليومي (خروج مطبخ): {counts.get('exit_vouchers', 0)} ورقة ({counts.get('exit_voucher_items', 0)} مادة مستهلكة)\n"
            f"  • بطاقات تعداد التذاكر والوجبات: {counts.get('daily_meals_tracking', 0)} يوم مسجل\n"
            f"  • وصولات الاستلام والتوريد (دخول): {counts.get('entry_vouchers', 0)} وصل ({counts.get('entry_voucher_items', 0)} مادة)\n"
            f"  • حركات المخزون الإجمالية: {counts.get('stock_movements', 0)} حركة\n"
            f"  • المواد المعتمدة للإقامة: {counts.get('residence_articles', counts.get('articles', 0))} مادة\n"
            f"  • الإعارات والاستعارات: {counts.get('residence_loans', 0)} إعارة\n"
            f"  • محاضر الجرد: {counts.get('inventory_snapshots', 0)} محضر\n\n"
            f"👉 تم الانتقال التلقائي إلى ورقة الاستهلاك اليومي وتعداد التذاكر لآخر تاريخ مسجل للإقامة.\n"
            f"🔒 تم عزل وتطبيق بيانات {r_name} حصراً دون المساس بأي إقامة أخرى نهائياً."
        )

        QMessageBox.information(self, "نجاح سحب البيانات من المديرية", details)
        self.residence_data_pulled.emit(r_id)

    def _on_pull_error(self, err_msg: str):
        if hasattr(self, 'btn_pull_residence'):
            self.btn_pull_residence.setEnabled(True)
        if hasattr(self, 'btn_pull_instant_offline'):
            self.btn_pull_instant_offline.setEnabled(True)
        self.lbl_pull_status.setText(f"❌ تعذر السحب: {err_msg}")
        self.lbl_pull_status.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 12px;")

        QMessageBox.warning(
            self,
            "تعذر سحب البيانات",
            f"تعذر إتمام سحب بيانات الإقامة:\n{err_msg}\n\n"
            f"💡 إرشاد فوري:\n"
            f"يمكنك النقر على الزر الأخضر: '⚡ استرجاع فوري لبيانات الإقامة (أوفلاين بدون إنترنت)' لاسترجاعها فوراً من الفلاش ديسك دون الحاجة لإنترنت."
        )
