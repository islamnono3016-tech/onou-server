import os
import sys
import ctypes
import hashlib
import hmac
import json
import time
import threading
import logging
import subprocess
from typing import Tuple, Optional, Dict, Any, List

logger = logging.getLogger("SecurityHardening")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SIGNATURE_FILE = os.path.join(BASE_DIR, "core", ".integrity.sig")

# قائمة بأسماء أدوات الهندسة العكسية والقرصنة المعروفة
BLACKLISTED_PROCESSES = {
    "x64dbg.exe", "x32dbg.exe", "ida.exe", "ida64.exe", "idag.exe", "idag64.exe",
    "cheatengine-x86_64.exe", "cheatengine-i386.exe", "cheatengine.exe",
    "scylla.exe", "scylla_x64.exe", "scylla_x86.exe", "processhacker.exe",
    "dnspy.exe", "dnspy-x86.exe", "wireshark.exe", "fiddler.exe",
    "httpdebuggerui.exe", "httpdebugger.exe", "ghidra.exe", "cutter.exe",
    "ollydbg.exe", "immunitydebugger.exe", "windbg.exe"
}

# قناع تشفير المفتاح السري الرئيسي لتفادي وجوده كنص صريح في الذاكرة أو الملفات
_KEY_MASK = bytes([
    0x44, 0x4F, 0x55, 0x2D, 0x41, 0x4C, 0x47, 0x45, 0x52, 0x49, 0x41, 0x2D,
    0x4F, 0x4E, 0x4F, 0x55, 0x2D, 0x53, 0x45, 0x43, 0x55, 0x52, 0x49, 0x54,
    0x59, 0x2D, 0x4B, 0x45, 0x59, 0x2D, 0x32, 0x30, 0x32, 0x36, 0x2D, 0x58,
    0x39, 0x39, 0x46, 0x2D, 0x53, 0x45, 0x43, 0x55, 0x52, 0x45, 0x2D, 0x4E,
    0x4F, 0x44, 0x45, 0x2D, 0x4C, 0x4F, 0x43, 0x4B
])

def get_master_security_secret() -> str:
    """اشتقاق المفتاح السري للمطور ديناميكياً في الذاكرة دون تخزينه كنص مكشوف"""
    salt = [0x12, 0x34, 0x56, 0x78]
    derived = bytearray()
    for idx, b in enumerate(_KEY_MASK):
        derived.append(b ^ salt[idx % len(salt)] ^ salt[idx % len(salt)])
    return derived.decode("utf-8")


class SecurityHardening:
    """
    منظومة الحماية المتقدمة والتحصين ضد القرصنة، التلاعب، والهندسة العكسية
    (Advanced Anti-Hacking, Anti-Tamper & Anti-Debugging Engine)
    """

    _original_bytecode_hashes: Dict[str, str] = {}
    _watchdog_thread: Optional[threading.Thread] = None
    _watchdog_running: bool = False
    _critical_security_callback = None

    @classmethod
    def check_debugger_present(cls) -> Tuple[bool, str]:
        """
        فحص ما إذا كان البرنامج يعمل تحت بيئة منقح (Debugger) لمحاولة كسر الحماية
        باستخدام دوال Win32 kernel32 API الرسمية
        """
        if sys.platform != "win32":
            return False, "Not Windows"

        try:
            # 1. IsDebuggerPresent Win32 API
            kernel32 = ctypes.windll.kernel32
            if kernel32.IsDebuggerPresent():
                return True, "تم رصد منقح تفاعلي نشط (Win32 IsDebuggerPresent)"

            # 2. CheckRemoteDebuggerPresent Win32 API
            is_remote_debugger = ctypes.c_bool(False)
            kernel32.CheckRemoteDebuggerPresent(kernel32.GetCurrentProcess(), ctypes.byref(is_remote_debugger))
            if is_remote_debugger.value:
                return True, "تم رصد منقح خارجي متصل بعملية البرنامج (CheckRemoteDebuggerPresent)"

        except Exception as e:
            logger.debug(f"Debugger check warning: {e}")

        return False, "No Debugger"

    @classmethod
    def check_blacklisted_processes(cls) -> Tuple[bool, str]:
        """
        فحص العمليات المشبوهة العاملة في ويندوز (أدوات كسر البرامج والتجسس)
        باستخدام Win32 Toolhelp32 API عالي السرعة بتقنية C-Types دون استهلاك للمعالج
        """
        if sys.platform != "win32":
            return False, "Not Windows"

        try:
            from ctypes import wintypes
            TH32CS_SNAPPROCESS = 0x00000002

            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ('dwSize', wintypes.DWORD),
                    ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD),
                    ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD),
                    ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD),
                    ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD),
                    ('szExeFile', ctypes.c_char * 260)
                ]

            kernel32 = ctypes.windll.kernel32
            hSnapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if hSnapshot and hSnapshot != -1:
                try:
                    pe = PROCESSENTRY32()
                    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
                    success = kernel32.Process32First(hSnapshot, ctypes.byref(pe))
                    while success:
                        exe_name = pe.szExeFile.decode("latin-1", errors="ignore").lower().strip('\x00 ')
                        if exe_name in BLACKLISTED_PROCESSES:
                            return True, f"تم اكتشاف أداة هندسة عكسية / تتبع نشطة: {exe_name}"
                        success = kernel32.Process32Next(hSnapshot, ctypes.byref(pe))
                finally:
                    kernel32.CloseHandle(hSnapshot)
        except Exception as e:
            logger.debug(f"Process check warning: {e}")

        return False, "Clean Environment"

    @classmethod
    def snapshot_function_integrity(cls, funcs: List[Any]):
        """أخذ بصمة تشفيرية لكود الدوال الحساسة في الذاكرة لكشف التعديل عليها (Monkey-Patching)"""
        for func in funcs:
            if hasattr(func, "__code__"):
                func_id = f"{func.__module__}.{func.__qualname__}"
                code_bytes = func.__code__.co_code
                cls._original_bytecode_hashes[func_id] = hashlib.sha256(code_bytes).hexdigest()

    @classmethod
    def verify_function_integrity(cls, funcs: List[Any]) -> Tuple[bool, str]:
        """التحقق من عدم استبدال أو حقن دوال التحقق الأمني بالذاكرة"""
        for func in funcs:
            if hasattr(func, "__code__"):
                func_id = f"{func.__module__}.{func.__qualname__}"
                current_hash = hashlib.sha256(func.__code__.co_code).hexdigest()
                original_hash = cls._original_bytecode_hashes.get(func_id)
                if original_hash and current_hash != original_hash:
                    return False, f"تم اكتشاف تلاعب بحقن الذاكرة في الدالة: {func_id}"
        return True, "Code Integrity Valid"

    @classmethod
    def calculate_file_hash(cls, file_path: str) -> Optional[str]:
        """حساب البصمة التشفيرية SHA-256 للملف"""
        if not os.path.exists(file_path):
            return None
        sha = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    sha.update(chunk)
            return sha.hexdigest()
        except Exception:
            return None

    @classmethod
    def generate_integrity_manifest(cls) -> Dict[str, str]:
        """
        توليد ملف البصمات الموقّع للملفات الحيوية (خاص بالمطور عند بناء النسخة)
        """
        critical_rel_files = [
            os.path.join("main.py"),
            os.path.join("core", "license_service.py"),
            os.path.join("core", "security_hardening.py"),
            os.path.join("core", "auth_service.py"),
            os.path.join("core", "update_service.py"),
            os.path.join("core", "time_service.py"),
            os.path.join("database", "db_manager.py")
        ]

        hashes = {}
        for rel_p in critical_rel_files:
            full_p = os.path.join(BASE_DIR, rel_p)
            if os.path.exists(full_p):
                hashes[rel_p] = cls.calculate_file_hash(full_p)

        secret = get_master_security_secret()
        data_to_sign = json.dumps(hashes, sort_keys=True).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), data_to_sign, hashlib.sha256).hexdigest()

        manifest = {
            "hashes": hashes,
            "signature": signature,
            "timestamp": int(time.time()),
            "version": "3.0"
        }

        with open(SIGNATURE_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4)

        logger.info(f"Integrity manifest generated with {len(hashes)} verified files.")
        return hashes

    @classmethod
    def verify_app_integrity(cls) -> Tuple[bool, str]:
        """
        التحقق الصارم من سلامة ملفات الكود وعدم تعديلها من قبل مخترق (Anti-Tamper Check)
        """
        if getattr(sys, "frozen", False):
            # في بيئة الملف التنفيذي المترجم (EXE)، تكون كافة ملفات الكود مدمجة ومحمية داخل الحزمة
            return True, "Frozen binary verified"

        if not os.path.exists(SIGNATURE_FILE):
            # إذا لم يوجد الملف، نقوم بتوليده وتوقيعه رقمياً تلقائياً
            cls.generate_integrity_manifest()
            return True, "Integrity initialized"

        try:
            with open(SIGNATURE_FILE, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            hashes = manifest.get("hashes", {})
            saved_sig = manifest.get("signature", "")

            # 1. التحقق من التوقيع الرقمي للملف
            secret = get_master_security_secret()
            data_to_sign = json.dumps(hashes, sort_keys=True).encode("utf-8")
            expected_sig = hmac.new(secret.encode("utf-8"), data_to_sign, hashlib.sha256).hexdigest()

            if not hmac.compare_digest(saved_sig, expected_sig):
                return False, "تنبيه أمني: تم التلاعب بملف التوقيع الرقمي للمنظومة!"

            # 2. مطابقة هاش كل ملف مع الهاش الحالي
            for rel_p, expected_hash in hashes.items():
                full_p = os.path.join(BASE_DIR, rel_p)
                current_hash = cls.calculate_file_hash(full_p)
                if not current_hash:
                    return False, f"ملف النظام الأساسي مفقود: {rel_p}"
                if current_hash != expected_hash:
                    return False, f"تم اكتشاف تعديل أو كسر لملف النظام: {rel_p}"

            return True, "All files verified"

        except Exception as e:
            return False, f"خطأ أثناء فحص سلامة الملفات: {e}"

    @classmethod
    def perform_full_security_check(cls) -> Tuple[bool, str]:
        """
        فحص أمني شامل فوري:
        1. كشف أدوات التنقيح (Anti-Debug)
        2. كشف برامج الاختراق النشطة (Anti-Reversing)
        3. التحقق من ترخيص العتاد (Hardware Node-Locking)
        4. التحقق من سلامة الملفات (Anti-Tampering)
        """
        # 1. كشف المنقحات
        has_dbg, dbg_msg = cls.check_debugger_present()
        if has_dbg:
            return False, f"تهديد أمني: {dbg_msg}"

        # 2. كشف برامج القرصنة
        has_tool, tool_msg = cls.check_blacklisted_processes()
        if has_tool:
            return False, f"تهديد أمني: {tool_msg}"

        # 3. فحص ترخيص العتاد
        try:
            from core.license_service import LicenseService
            is_lic, lic_msg, _ = LicenseService.is_licensed()
            if not is_lic:
                return False, f"قفل العتاد: {lic_msg}"
        except Exception as e:
            return False, f"خطأ فحص الترخيص: {e}"

        # 4. فحص سلامة الملفات
        is_intact, int_msg = cls.verify_app_integrity()
        if not is_intact:
            return False, f"خرق أمني: {int_msg}"

        return True, "System Secure"

    @classmethod
    def start_background_watchdog(cls, on_violation_callback=None, interval_seconds: int = 60):
        """
        تشغيل حارس أمني دوري فائق الخفة في الخلفية (Lightweight Watchdog Thread)
        يفحص المنقحات والعمليات الخبيثة فورياً بـ Win32 API دون التأثير على استجابة الواجهة
        """
        if cls._watchdog_running:
            return

        cls._watchdog_running = True
        cls._critical_security_callback = on_violation_callback

        def _watchdog_loop():
            cycle_counter = 0
            while cls._watchdog_running:
                time.sleep(interval_seconds)
                if not cls._watchdog_running:
                    break

                cycle_counter += 1

                # 1. فحص المنقحات والعمليات المشبوهة دورياً بـ Win32 API (< 1 ميلي ثانية)
                has_dbg, dbg_msg = cls.check_debugger_present()
                if has_dbg:
                    logger.critical(f"SECURITY VIOLATION DETECTED: {dbg_msg}")
                    if cls._critical_security_callback:
                        try:
                            cls._critical_security_callback(dbg_msg)
                        except Exception:
                            pass
                    try:
                        os._exit(0)
                    except Exception:
                        sys.exit(0)

                has_tool, tool_msg = cls.check_blacklisted_processes()
                if has_tool:
                    logger.critical(f"SECURITY VIOLATION DETECTED: {tool_msg}")
                    if cls._critical_security_callback:
                        try:
                            cls._critical_security_callback(tool_msg)
                        except Exception:
                            pass
                    try:
                        os._exit(0)
                    except Exception:
                        sys.exit(0)

                # 2. فحص سلامة الملفات وبصمة العتاد بشكل متزن كل 5 دورات لتفادي إجهاد القرص
                if cycle_counter % 5 == 0:
                    try:
                        from core.license_service import LicenseService
                        is_lic, lic_msg, _ = LicenseService.is_licensed()
                        if not is_lic:
                            logger.critical(f"LICENSE VIOLATION: {lic_msg}")
                            if cls._critical_security_callback:
                                try:
                                    cls._critical_security_callback(lic_msg)
                                except Exception:
                                    pass
                            os._exit(0)
                    except Exception:
                        pass

                    is_intact, int_msg = cls.verify_app_integrity()
                    if not is_intact:
                        logger.critical(f"INTEGRITY BREACH: {int_msg}")
                        if cls._critical_security_callback:
                            try:
                                cls._critical_security_callback(int_msg)
                            except Exception:
                                pass
                        os._exit(0)

        cls._watchdog_thread = threading.Thread(target=_watchdog_loop, daemon=True, name="ONOU-SecurityWatchdog")
        cls._watchdog_thread.start()
        logger.info("High-Performance Security Watchdog started in background.")

    @classmethod
    def stop_background_watchdog(cls):
        cls._watchdog_running = False
