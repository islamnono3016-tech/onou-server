import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QCheckBox, QFrame,
    QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QFont

from core.config import AppConfig
from core.sync_service import SyncService
from core.network_service import NetworkClient, get_local_ip
from core.residence_service import ResidenceService
from database.db_manager import DatabaseManager

class NetworkSettingsDialog(QDialog):
    """
    نافذة إعدادات الربط الشبكي والمعمارية السحابية / المحلية
    (Client-Server Architecture Configuration & Sync Dashboard)
    """

    settings_saved = pyqtSignal()

    def __init__(self, db_manager: DatabaseManager, parent=None, is_setup_wizard: bool = False):
        super().__init__(parent)
        self.db = db_manager
        self.res_svc = ResidenceService(self.db)
        self.sync_svc = SyncService(self.db)
        self.is_setup_wizard = is_setup_wizard

        if is_setup_wizard:
            self.setWindowTitle("معالج الإعداد الأولي وتسطيب النظام - ONOU 2026")
        else:
            self.setWindowTitle("إعدادات الربط الشبكي والمزامنة المركزية - ONOU 2026")
        self.resize(600, 640)
        self.setMinimumSize(580, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        from ui.theme import ThemeManager
        c_bg = ThemeManager.get_color("card_bg")
        c_border = ThemeManager.get_color("card_border")
        c_head = ThemeManager.get_color("text_heading")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # 1. الترويسة
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet(f"background: {c_bg}; border: 1px solid {c_border}; border-radius: 8px; padding: 12px;")
        h_layout = QVBoxLayout(hdr_frame)
        h_layout.setSpacing(4)

        if self.is_setup_wizard:
            lbl_t = QLabel("🛠️ معالج تثبيت وتهيئة المنظومة لأول مرة (Setup Wizard)")
            lbl_t.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #10B981;")
            lbl_s = QLabel("يرجى تحديد دور هذا الجهاز واختيار الإقامة المخصصة له.\nسيتم حفظ وتثبيت هذه الإعدادات وقفلها، ولا يمكن تغييرها لاحقاً إلا من طرف مديرية الخدمات الجامعية.")
            lbl_s.setStyleSheet("font-size: 11px; color: #E2E8F0; line-height: 1.4;")
        else:
            lbl_t = QLabel("🌐 معمارية المنظومة والربط بين المديرية والإقامات")
            lbl_t.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {c_head};")
            lbl_s = QLabel("تحديد دور هذا الجهاز (خادم مركزي للمديرية أو محطة عميل بالإقامة) وضبط المزامنة التلقائية.")
            lbl_s.setStyleSheet("font-size: 11px; color: #94A3B8;")

        h_layout.addWidget(lbl_t)
        h_layout.addWidget(lbl_s)
        layout.addWidget(hdr_frame)

        # 2. نمط التشغيل (Architecture Mode)
        mode_box = QGroupBox("1. نمط تشغيل هذا الجهاز (App Mode)")
        mode_box.setStyleSheet(f"font-weight: bold; color: {c_head};")
        mb_layout = QFormLayout(mode_box)
        mb_layout.setContentsMargins(14, 14, 14, 14)
        mb_layout.setSpacing(10)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItem("مديرية الخدمات الجامعية (خادم مركزي - Directorate HQ)", "DIRECTORATE_SERVER")
        self.cmb_mode.addItem("إقامة جامعية (محطة عميل مستقلة - Residence Client)", "RESIDENCE_CLIENT")
        self.cmb_mode.addItem("وضع مستقل أحادي (Standalone Local Mode)", "STANDALONE")
        self.cmb_mode.currentIndexChanged.connect(self.on_mode_changed)

        mb_layout.addRow("الدور والنمط:", self.cmb_mode)
        layout.addWidget(mode_box)

        # 3. إعدادات السيرفر والاتصال (Server Settings)
        self.srv_box = QGroupBox("2. إعدادات الخادم المركزي والاستضافة السحابية عبر الإنترنت (Cloud Server)")
        self.srv_box.setStyleSheet(f"font-weight: bold; color: {c_head};")
        sb_layout = QFormLayout(self.srv_box)
        sb_layout.setContentsMargins(14, 14, 14, 14)
        sb_layout.setSpacing(10)

        # بطاقة إرشادية للربط عبر الإنترنت المباشر
        lbl_cloud_tip = QLabel(
            "💡 للربط عبر الإنترنت المباشر دون الحاجة لأي برامج وسيطة (بدون Tailscale أو VPN):\n"
            "• أدخل رابط الاستضافة السحابية الخاص بمديريتكم (مثال: https://stock.onou.dz أو http://194.163.50.20:8050)\n"
            "• ستتصل الإقامة بالخادم وتتبادل المعطيات عبر أي شبكة واي فاي (Wi-Fi) أو 4G بشكل طبيعي وتلقائي."
        )
        lbl_cloud_tip.setWordWrap(True)
        lbl_cloud_tip.setStyleSheet(
            "background-color: rgba(13, 148, 136, 0.15); border: 1px solid #0D9488; "
            "border-radius: 6px; padding: 8px; font-size: 11px; color: #5EEAD4; font-weight: bold;"
        )
        sb_layout.addRow(lbl_cloud_tip)

        self.txt_host = QLineEdit()
        self.txt_host.setPlaceholderText("مثال: onou-server.onrender.com أو https://onou-server.onrender.com")
        self.txt_host.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.txt_host.textChanged.connect(self.on_host_changed)

        self.spn_port = QSpinBox()
        self.spn_port.setRange(1, 65535)
        self.spn_port.setValue(443)
        self.spn_port.setMinimumWidth(90)   # يضمن عرضاً كافياً لـ 5 أرقام
        self.spn_port.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.cmb_residence = QComboBox()
        self.populate_residences()

        sb_layout.addRow("🌐 رابط أو عنوان الخادم السحابي:", self.txt_host)
        sb_layout.addRow("منفذ الشبكة (Port):", self.spn_port)
        sb_layout.addRow("الإقامة التابع لها هذا الجهاز:", self.cmb_residence)

        layout.addWidget(self.srv_box)

        # 4. المزامنة والاستقلالية التامة (Auto-Sync & Offline Resilience)
        sync_box = QGroupBox("3. المزامنة والاستقلالية دون إنترنت (Offline Sync Outbox)")
        sync_box.setStyleSheet(f"font-weight: bold; color: {c_head};")
        sc_layout = QVBoxLayout(sync_box)
        sc_layout.setContentsMargins(14, 12, 14, 12)
        sc_layout.setSpacing(8)

        self.chk_auto_sync = QCheckBox("تفعيل المزامنة التلقائية في الخلفية عند توفر الاتصال")
        self.chk_auto_sync.setChecked(True)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("دورة فحص الاتصال والمزامنة (بالثواني):"))
        self.spn_interval = QSpinBox()
        self.spn_interval.setRange(1, 600)
        self.spn_interval.setValue(5)
        interval_layout.addWidget(self.spn_interval)
        interval_layout.addStretch()

        sc_layout.addWidget(self.chk_auto_sync)
        sc_layout.addLayout(interval_layout)

        # أزرار فحص ومزامنة فورية
        sync_btns = QHBoxLayout()
        sync_btns.setSpacing(10)

        self.btn_ping = QPushButton("فحص الاتصال 🌐")
        self.btn_ping.setFixedHeight(34)
        self.btn_ping.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ping.clicked.connect(self.ping_server)

        self.btn_push_now = QPushButton("مزامنة المعلقات 🔄")
        self.btn_push_now.setFixedHeight(34)
        self.btn_push_now.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_push_now.clicked.connect(self.sync_push_now)

        self.btn_pull_catalog = QPushButton("سحب الدليل 📥")
        self.btn_pull_catalog.setFixedHeight(34)
        self.btn_pull_catalog.setVisible(False)  # الإقامات لا تسحب أي بيانات من الخارج

        sync_btns.addWidget(self.btn_ping)
        sync_btns.addWidget(self.btn_push_now)
        sync_btns.addWidget(self.btn_pull_catalog)
        sc_layout.addLayout(sync_btns)

        # حالة الرتل المعلق
        self.lbl_queue_status = QLabel("حالة الرتل: جاري التحقق...")
        self.lbl_queue_status.setStyleSheet("font-size: 11px; color: #0284C7; font-weight: bold;")
        sc_layout.addWidget(self.lbl_queue_status)

        layout.addWidget(sync_box)

        # 5. أزرار الحفظ والإغلاق
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_save = QPushButton("حفظ الإعدادات وتطبيقها ✔")
        self.btn_save.setObjectName("BtnLogin")
        self.btn_save.setFixedHeight(38)
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self.save_settings)

        self.btn_close = QPushButton("إغلاق ❌")
        self.btn_close.setFixedHeight(38)
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def populate_residences(self):
        self.cmb_residence.clear()
        res_list = self.res_svc.list_residences(only_active=True)
        for r in res_list:
            self.cmb_residence.addItem(f"{r['name']} ({r['code']})", r["id"])

    def load_current_settings(self):
        cfg = AppConfig.load()
        mode = cfg.get("app_mode", "RESIDENCE_CLIENT")
        idx = self.cmb_mode.findData(mode)
        if idx >= 0:
            self.cmb_mode.setCurrentIndex(idx)

        host = cfg.get("server_host", "onou-server.onrender.com")
        if not host or host in ("127.0.0.1", "localhost"):
            host = "onou-server.onrender.com"
        self.txt_host.setText(host)

        port = cfg.get("server_port", 443)
        self.spn_port.setValue(port)

        res_id = cfg.get("residence_id", 1)
        r_idx = self.cmb_residence.findData(res_id)
        if r_idx >= 0:
            self.cmb_residence.setCurrentIndex(r_idx)

        self.chk_auto_sync.setChecked(cfg.get("auto_sync", True))
        interval = cfg.get("sync_interval_seconds", 5)
        self.spn_interval.setValue(interval)

        self.update_queue_label()
        self.on_mode_changed()

    def update_queue_label(self):
        res_id = self.cmb_residence.currentData() or 1
        pending = self.sync_svc.get_pending_count(res_id)
        if pending == 0:
            self.lbl_queue_status.setText("🟢 جميع الحركات المحلية متزامنة ومطابقة تماماً مع خادم المديرية (0 معلقة).")
            self.lbl_queue_status.setStyleSheet("font-size: 11px; color: #10B981; font-weight: bold;")
        else:
            self.lbl_queue_status.setText(f"🟡 يوجد {pending} حركة مسجلة محلياً بانتظار الإرسال إلى سيرفر المديرية.")
            self.lbl_queue_status.setStyleSheet("font-size: 11px; color: #F59E0B; font-weight: bold;")

    def on_mode_changed(self):
        mode = self.cmb_mode.currentData()
        is_client = (mode == "RESIDENCE_CLIENT")
        self.srv_box.setEnabled(is_client)
        self.btn_push_now.setEnabled(is_client)
        self.btn_pull_catalog.setVisible(False)

    def on_host_changed(self, text: str):
        t = text.strip().lower()
        if t.startswith("https://"):
            self.spn_port.blockSignals(True)
            self.spn_port.setValue(443)
            self.spn_port.setEnabled(False)
            self.spn_port.blockSignals(False)
        else:
            self.spn_port.setEnabled(True)
            if self.spn_port.value() == 443:
                self.spn_port.setValue(8050)

    def get_current_url(self) -> str:
        raw = self.txt_host.text().strip()
        port = self.spn_port.value()
        if not raw:
            raw = "127.0.0.1"
        if raw.startswith("https://"):
            domain_part = raw.split("://", 1)[1]
            if ":" in domain_part:
                return raw.rstrip("/")
            return raw.rstrip("/")
        if raw.startswith("http://"):
            domain_part = raw.split("://", 1)[1]
            if ":" in domain_part or port in (80, 443):
                return raw.rstrip("/")
            return f"{raw.rstrip('/')}:{port}"
        if ":" in raw:
            return f"http://{raw}"
        if port == 443:
            return f"https://{raw}"
        return f"http://{raw}:{port}"

    def ping_server(self):
        host = self.txt_host.text().strip()
        port = self.spn_port.value()
        url = self.get_current_url()

        client = NetworkClient(server_host=host, port=port)
        ok, ms, msg = client.ping()
        if ok:
            QMessageBox.information(
                self, "نجاح الاتصال بالسيرفر السحابي ⚡",
                f"✅ تم الاتصال بنجاح بالخادم المركزي على الرابط:\n{url}\n\n"
                f"• سرعة الاستجابة (Latency): {ms:.1f} مللي ثانية\n"
                f"• الحالة: الخادم يعمل وجاهز لتبادل البيانات."
            )
        else:
            QMessageBox.warning(
                self, "تعذر الاتصال بالخادم ❌",
                f"تعذر الوصول إلى الخادم على العنوان:\n{url}\n\n"
                f"• التفاصيل: {msg}\n\n"
                f"يرجى التأكد من تشغيل السيرفر بالمديرية أو الاستضافة وتوفر اتصال الإنترنت."
            )

    def sync_push_now(self):
        url = self.get_current_url()
        res_id = self.cmb_residence.currentData() or 1

        synced, left = self.sync_svc.push_pending(res_id, base_url=url)
        self.update_queue_label()
        if synced > 0:
            QMessageBox.information(self, "نجاح المزامنة", f"تم بنجاح إرسال ومزامنة {synced} حركة إلى الخادم المركزي.\nالمتبقي: {left}")
        elif left > 0:
            QMessageBox.warning(self, "تنبيه المزامنة", f"لم تتمكن المزامنة من الإرسال (تأكد من عمل الخادم). المتبقي: {left}")
        else:
            QMessageBox.information(self, "مكتمل", "لا توجد أي حركات معلقة بانتظار المزامنة.")

    def pull_catalog_now(self):
        url = self.get_current_url()
        res_id = self.cmb_residence.currentData() or 1

        cnt = self.sync_svc.pull_server_catalog(res_id, base_url=url)
        if cnt > 0:
            QMessageBox.information(self, "تم التحديث", f"تم سحب وتحديث {cnt} مادة من دليل المواد والأسعار المعتمدة بالمديرية.")
        else:
            QMessageBox.warning(self, "فشل السحب", "تعذر سحب الدليل من الخادم أو لا توجد تحديثات جديدة.")

    def save_settings(self):
        mode = self.cmb_mode.currentData()
        host = self.txt_host.text().strip()
        port = self.spn_port.value()
        res_id = self.cmb_residence.currentData()
        res_name = self.cmb_residence.currentText()

        AppConfig.save({
            "initial_setup_completed": True,
            "app_mode": mode,
            "server_host": host,
            "server_port": port,
            "residence_id": res_id,
            "residence_name": res_name,
            "auto_sync": self.chk_auto_sync.isChecked(),
            "sync_interval_seconds": self.spn_interval.value()
        })

        if self.is_setup_wizard:
            QMessageBox.information(
                self,
                "اكتمل التثبيت بنجاح",
                "✅ تم تثبيت وضبط إعدادات المنظومة بنجاح!\nتم قفل الإعدادات لهذا الجهاز ولا يمكن تعديلها إلا من طرف مديرية الخدمات."
            )
        else:
            QMessageBox.information(self, "تم الحفظ", "تم حفظ وتحديث إعدادات الربط الشبكي بنجاح ✔")

        self.settings_saved.emit()
        self.accept()

    @classmethod
    def open_with_admin_auth(cls, db_manager: DatabaseManager, parent=None) -> bool:
        """
        التحقق الصارم من كود مديرية الخدمات الجامعية الموحد قبل فتح نافذة تعديل إعدادات الربط
        """
        from ui.widgets.directorate_auth_dialog import DirectorateAuthDialog

        if not DirectorateAuthDialog.verify(parent, "تعديل إعدادات الربط الشبكي والمزامنة السحابية", db=db_manager):
            return False

        dlg = cls(db_manager, parent=parent, is_setup_wizard=False)
        return dlg.exec() == QDialog.DialogCode.Accepted

