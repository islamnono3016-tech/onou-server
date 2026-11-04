from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from typing import Optional
from database.db_manager import DatabaseManager
from core.auth_service import AuthService

class DirectorateAuthDialog(QDialog):
    """
    نافذة التحقق الأمني الموحدة الخاصة بمديرية الخدمات الجامعية
    لحماية واجهة الربط الشبكي، واجهة النسخ الاحتياطي، وواجهة الإعدادات بكود موحد.
    """

    def __init__(self, parent=None, action_name: str = "هذه العملية المحمية", db_manager: Optional[DatabaseManager] = None):
        super().__init__(parent)
        self.db = db_manager or DatabaseManager()
        self.action_name = action_name
        self.is_authenticated = False

        self.setWindowTitle("🔐 تحقق أمني - كود مديرية الخدمات الجامعية")
        self.setFixedSize(480, 290)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.init_ui()

    def init_ui(self):
        from ui.theme import ThemeManager
        c_bg = ThemeManager.get_color("card_bg")
        c_border = ThemeManager.get_color("card_border")
        c_text = ThemeManager.get_color("text_main")

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c_bg};
            }}
            QLabel {{
                color: {c_text};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # 1. بطاقة الترويسة والتوضيح
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1.5px solid #F59E0B;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setSpacing(4)

        lbl_title = QLabel("🏢 مديرية الخدمات الجامعية - حماية الإعدادات والبيانات")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #FCD34D;")

        lbl_desc = QLabel(f"🔒 تتطلب متابعة [{self.action_name}] إدخال كود المديرية المعتمد.")
        lbl_desc.setStyleSheet("font-size: 11px; color: #E2E8F0;")
        lbl_desc.setWordWrap(True)

        h_layout.addWidget(lbl_title)
        h_layout.addWidget(lbl_desc)
        layout.addWidget(header_card)

        # 2. حقل إدخال الكود مع زر إظهار/إخفاء
        lbl_prompt = QLabel("أدخل كود / كلمة مرور المديرية للمتابعة:")
        lbl_prompt.setStyleSheet("font-weight: bold; font-size: 12px; color: #CBD5E1;")
        layout.addWidget(lbl_prompt)

        input_box = QHBoxLayout()
        input_box.setSpacing(6)

        self.txt_code = QLineEdit()
        self.txt_code.setFixedHeight(38)
        self.txt_code.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_code.setPlaceholderText("أدخل كود المديرية...")
        self.txt_code.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.txt_code.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.txt_code.setStyleSheet("""
            QLineEdit {
                background-color: #0F172A;
                border: 1.5px solid #475569;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 14px;
                font-weight: bold;
                color: #FFFFFF;
                letter-spacing: 2px;
            }
            QLineEdit:focus {
                border-color: #F59E0B;
            }
        """)
        self.txt_code.returnPressed.connect(self.verify_and_accept)
        input_box.addWidget(self.txt_code)

        self.btn_toggle_eye = QPushButton("👁️")
        self.btn_toggle_eye.setFixedSize(38, 38)
        self.btn_toggle_eye.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_eye.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                border: 1px solid #475569;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        self.btn_toggle_eye.clicked.connect(self.toggle_echo_mode)
        input_box.addWidget(self.btn_toggle_eye)

        layout.addLayout(input_box)

        # 3. أزرار التحكم
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        self.btn_submit = QPushButton("تأكيد الدخول 🔒")
        self.btn_submit.setFixedHeight(40)
        self.btn_submit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_submit.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D97706, stop:1 #F59E0B);
                color: #0F172A;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #FBBF24;
            }
        """)
        self.btn_submit.clicked.connect(self.verify_and_accept)

        self.btn_cancel = QPushButton("إلغاء ❌")
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #E2E8F0;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #475569;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(self.btn_submit)
        btn_box.addWidget(self.btn_cancel)
        layout.addLayout(btn_box)

    def toggle_echo_mode(self):
        if self.txt_code.echoMode() == QLineEdit.EchoMode.Password:
            self.txt_code.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_eye.setText("🔒")
        else:
            self.txt_code.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_eye.setText("👁️")

    def verify_and_accept(self):
        code = self.txt_code.text().strip()
        if not code:
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى كتابة كود المديرية أولاً.")
            self.txt_code.setFocus()
            return

        if AuthService.verify_directorate_code(code, self.db):
            self.is_authenticated = True
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "تم رفض الإذن ❌",
                "كود المديرية غير صحيح!\nلا تملك صلاحية الوصول إلى هذه الواجهة المحمية."
            )
            self.txt_code.selectAll()
            self.txt_code.setFocus()

    @classmethod
    def verify(cls, parent=None, action_name: str = "هذه العملية المحمية", db: Optional[DatabaseManager] = None) -> bool:
        """دالة مختصرة لطلب كود المديرية والتحقق منه فورا"""
        dlg = cls(parent=parent, action_name=action_name, db_manager=db)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.is_authenticated:
            return True
        return False


class DirectorateChangeCodeDialog(QDialog):
    """
    نافذة تغيير وتحديث كود المديرية الموحد
    (عند تغييره يتغير كود حساب المدير العام، واجهة الربط، واجهة النسخ الاحتياطي، والإعدادات تلقائياً)
    """

    def __init__(self, parent=None, db_manager: Optional[DatabaseManager] = None):
        super().__init__(parent)
        self.db = db_manager or DatabaseManager()

        self.setWindowTitle("🔐 تغيير كود المديرية الموحد")
        self.setFixedSize(500, 360)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.init_ui()

    def init_ui(self):
        from ui.theme import ThemeManager
        c_bg = ThemeManager.get_color("card_bg")
        c_text = ThemeManager.get_color("text_main")

        self.setStyleSheet(f"""
            QDialog {{ background-color: {c_bg}; }}
            QLabel {{ color: {c_text}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        # الترويسة
        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1.5px solid #10B981;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        ic_l = QVBoxLayout(info_card)
        ic_l.setSpacing(4)

        t_lbl = QLabel("🏢 كود المديرية الموحد (الربط، النسخ الاحتياطي، والإعدادات)")
        t_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #34D399;")
        d_lbl = QLabel("تغيير هذا الكود سيغير تلقائياً كود فتح واجهة الربط الشبكي، واجهة النسخ الاحتياطي، والإعدادات، وكذلك كلمة مرور حساب المسؤول العام (admin).")
        d_lbl.setStyleSheet("font-size: 11px; color: #CBD5E1;")
        d_lbl.setWordWrap(True)

        ic_l.addWidget(t_lbl)
        ic_l.addWidget(d_lbl)
        layout.addWidget(info_card)

        # الحقول
        layout.addWidget(QLabel("1. كود المديرية الحالي:"))
        self.txt_curr = QLineEdit()
        self.txt_curr.setFixedHeight(34)
        self.txt_curr.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_curr.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.txt_curr.setPlaceholderText("أدخل الكود الحالي...")
        layout.addWidget(self.txt_curr)

        layout.addWidget(QLabel("2. كود المديرية الجديد:"))
        self.txt_new = QLineEdit()
        self.txt_new.setFixedHeight(34)
        self.txt_new.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_new.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.txt_new.setPlaceholderText("أدخل الكود الجديد (4 أحرف/أرقام على الأقل)...")
        layout.addWidget(self.txt_new)

        layout.addWidget(QLabel("3. تأكيد كود المديرية الجديد:"))
        self.txt_confirm = QLineEdit()
        self.txt_confirm.setFixedHeight(34)
        self.txt_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_confirm.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.txt_confirm.setPlaceholderText("أعد إدخال الكود الجديد للتأكيد...")
        layout.addWidget(self.txt_confirm)

        # الأزرار
        btns = QHBoxLayout()
        btns.setSpacing(10)

        btn_save = QPushButton("حفظ وتحديث كود المديرية الموحد ✔")
        btn_save.setFixedHeight(40)
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #10B981; }
        """)
        btn_save.clicked.connect(self.save_new_code)

        btn_cancel = QPushButton("إلغاء ❌")
        btn_cancel.setFixedHeight(40)
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #E2E8F0;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #475569;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def save_new_code(self):
        curr = self.txt_curr.text().strip()
        new_c = self.txt_new.text().strip()
        conf = self.txt_confirm.text().strip()

        if not curr or not new_c or not conf:
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى تعبئة كافة الحقول المطلوبة.")
            return

        if not AuthService.verify_directorate_code(curr, self.db):
            QMessageBox.critical(self, "خطأ في التحقق", "كود المديرية الحالي غير صحيح!")
            self.txt_curr.selectAll()
            self.txt_curr.setFocus()
            return

        if len(new_c) < 4:
            QMessageBox.warning(self, "كود قصير", "يرجى اختيار كود يحتوي على 4 خانات على الأقل لضمان الأمان.")
            self.txt_new.setFocus()
            return

        if new_c != conf:
            QMessageBox.critical(self, "عدم تطابق", "كود المديرية الجديد وتأكيده غير متطابقين!")
            self.txt_confirm.setFocus()
            return

        try:
            AuthService.set_directorate_code(new_c, self.db)
            QMessageBox.information(
                self,
                "تم تحديث كود المديرية بنجاح ✅",
                "تم بنجاح تغيير وتوحيد كود المديرية في المنظومة بالكامل!\n\n"
                "• تم تحديث كود واجهة الربط الشبكي\n"
                "• تم تحديث كود واجهة النسخ الاحتياطي\n"
                "• تم تحديث كود واجهة الإعدادات العامة\n"
                "• تم تحديث كلمة مرور حساب المدير العام (admin)\n\n"
                "أصبح هذا الكود الجديد هو المعتمد لكافة هذه الواجهات دائماً."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ الكود:\n{e}")
