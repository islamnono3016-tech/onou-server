import sys
import os

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# تفعيل أولوية تحميل حزم وتحديثات بايثون النقية من القرص (ui, core, database, reports)
import importlib.util
import importlib.abc

_APP_PACKAGES = ("ui", "core", "database", "reports")

class _DiskOverrideFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        prefix = fullname.split(".")[0]
        if prefix in _APP_PACKAGES:
            rel_parts = fullname.split(".")
            rel_file = os.path.join(BASE_DIR, *rel_parts) + ".py"
            rel_pkg = os.path.join(BASE_DIR, *rel_parts, "__init__.py")
            if os.path.isfile(rel_file):
                return importlib.util.spec_from_file_location(fullname, rel_file)
            elif os.path.isfile(rel_pkg):
                return importlib.util.spec_from_file_location(fullname, rel_pkg, submodule_search_locations=[os.path.dirname(rel_pkg)])
        return None

if getattr(sys, "frozen", False):
    sys.meta_path.insert(0, _DiskOverrideFinder())




# تهيئة مسارات مكتبات DLL لـ Qt (PyQt5 / PyQt6) لضمان العمل على Windows 7 و 8 و 10 و 11
for _dll_p in [
    os.path.join(BASE_DIR, "PyQt5", "Qt5", "bin"),
    os.path.join(BASE_DIR, "PyQt5"),
    os.path.join(BASE_DIR, "PyQt6", "Qt6", "bin"),
    os.path.join(BASE_DIR, "PyQt6"),
    BASE_DIR
]:
    if os.path.exists(_dll_p):
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(_dll_p)
            except Exception:
                pass
        os.environ["PATH"] = _dll_p + os.pathsep + os.environ.get("PATH", "")

from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database.db_manager import DatabaseManager
from core.auth_service import AuthService
from core.network_service import NetworkServer
from ui.theme import STYLE_SHEET
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
import traceback
from datetime import datetime

def setup_exception_hook():
    """معالج الأخطاء غير المتوقعة العام مع التسجيل في error.log وعرض تنبيه عربي لطيف"""
    def _handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        err_details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log_path = os.path.join(BASE_DIR, "error.log")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*70}\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Unhandled Exception:\n")
                f.write(err_details)
        except Exception:
            pass

        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None,
                "تنبيه تقني ⚠️",
                f"حدث خطأ غير متوقع أثناء معالجة البيانات:\n\n{exc_value}\n\n"
                f"تم حفظ التقرير التقني بأمان في ملف (error.log) بجانب البرنامج.\n"
                f"يمكنك متابعة العمل أو إعادة تشغيل البرنامج إذا تطلب الأمر."
            )
        except Exception:
            pass

    sys.excepthook = _handle_exception

def main():
    setup_exception_hook()
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("نظام تسيير مخزون الإطعام الجامعي")
    app.setOrganizationName("ONOU")

    from ui.common_filters import GlobalSelectAllFilter
    select_all_filter = GlobalSelectAllFilter(app)
    app.installEventFilter(select_all_filter)

    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # تهيئة قاعدة البيانات المحلية وتحديث الجداول
    db_manager = DatabaseManager()

    # مزامنة التوقيت الرسمي الموحد وعزل المنظومة عن أخطاء ساعة وتاريخ الحاسوب
    try:
        from core.time_service import TimeService
        TimeService.initialize()
    except Exception as _te:
        print(f"TimeService init notice: {_te}")

    # تطبيق المظهر العام مع اعتماد الوضع المظلم كالأساسي عند التشغيل
    from ui.theme import ThemeManager
    saved_theme = db_manager.get_setting("app_theme", "DARK")
    if not saved_theme:
        saved_theme = "DARK"
        db_manager.set_setting("app_theme", "DARK")
    ThemeManager.apply_theme(app, saved_theme, db=db_manager)

    from PyQt6.QtGui import QIcon
    icon_path = os.path.join(BASE_DIR, "app_icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(BASE_DIR, "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    font = QFont("Segoe UI", 12)
    font.setBold(True)
    font.setWeight(QFont.Weight.Bold)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    # 0. التحصين الأمني وكشف بيئات الاختراق والتنقيح (Anti-Debug & Anti-Tamper)
    from core.security_hardening import SecurityHardening
    from core.license_service import LicenseService

    # أ. كشف أدوات التنقيح والهندسة العكسية
    has_dbg, dbg_msg = SecurityHardening.check_debugger_present()
    if has_dbg:
        sys.exit(0)

    has_tool, tool_msg = SecurityHardening.check_blacklisted_processes()
    if has_tool:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "تحذير أمني صارم", f"تم رصد أداة تتبع أو قرصنة نشطة:\n{tool_msg}\nتم إيقاف تشغيل المنظومة لحماية البيانات.")
        sys.exit(0)

    # ب. أخذ بصمة كود دوال التحقق في الذاكرة لكشف الحقن (Anti-Memory-Hooking)
    SecurityHardening.snapshot_function_integrity([
        LicenseService.is_licensed,
        LicenseService.verify_activation_key,
        LicenseService.get_machine_code
    ])

    # ج. فحص سلامة الملفات الأساسية ضد التعديل أو التلاعب (Anti-Tamper Check)
    if not getattr(sys, "frozen", False):
        is_intact, int_msg = SecurityHardening.verify_app_integrity()
        if not is_intact:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None, "خرق أمني خطير 🚨",
                f"تم اكتشاف تعديل أو تلاعب غير مصرح به في ملفات النظام الأساسية!\n\n"
                f"التفاصيل: {int_msg}\n\n"
                f"تم حظر التشغيل لحماية قواعد البيانات والتراخيص."
            )
            sys.exit(0)

    # د. فحص سلامة قاعدة البيانات الفيزيائية
    db_ok, db_msg = db_manager.verify_database_integrity()
    if not db_ok:
        print(f"Database integrity notice: {db_msg}")

    # هـ. التحقق الأمني من ترخيص العتاد وحماية البرنامج ضد السرقة (Anti-Theft Hardware Protection)
    is_lic, lic_msg, lic_data = LicenseService.is_licensed()
    if not is_lic:
        from ui.activation_dialog import ActivationDialog
        act_dialog = ActivationDialog(custom_msg=lic_msg)
        if act_dialog.exec() != QDialog.DialogCode.Accepted:
            # تم الإلغاء أو فشل التفعيل -> إغلاق البرنامج فوراً ومنع التشغيل
            sys.exit(0)

        # إعادة فحص الترخيص للتأكد من نجاح التفعيل
        is_lic, lic_msg, lic_data = LicenseService.is_licensed()
        if not is_lic:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "خطأ في الترخيص", f"تعذر تأكيد تفعيل الجهاز:\n{lic_msg}\nتم إيقاف التشغيل.")
            sys.exit(0)

    # 1. فحص معالج الإعداد والتسطيب الأولي (First-Time Setup Wizard)
    from core.config import AppConfig
    cfg = AppConfig.load()
    if not cfg.get("initial_setup_completed", False):
        from ui.widgets.network_settings_dialog import NetworkSettingsDialog
        wizard = NetworkSettingsDialog(db_manager, is_setup_wizard=True)
        if wizard.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        cfg = AppConfig.load()

    # 2. تشغيل خادم الشبكة في الخلفية إذا كان نمط الجهاز خادم مديرية
    network_server = None
    if AppConfig.is_server_mode():
        port = cfg.get("server_port", 8050)
        network_server = NetworkServer(port=port, db_manager=db_manager)
        try:
            network_server.start()
        except Exception as e:
            print(f"Notice: LAN server startup info: {e}")

    # 3. فتح نافذة تسجيل الدخول
    auth_service = AuthService(db_manager)
    login_dialog = LoginDialog(auth_service)

    if login_dialog.exec() == QDialog.DialogCode.Accepted and login_dialog.authenticated_user:
        current_user = login_dialog.authenticated_user
        window = MainWindow(db_manager, current_user=current_user, network_server=network_server)
        window.showMaximized()

        # 4. تشغيل الحارس الأمني الدوري في خلفية المنظومة (Active Background Security Watchdog)
        SecurityHardening.start_background_watchdog(interval_seconds=60)

        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
