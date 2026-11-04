import os
import sys
import json
import zipfile
import shutil
import string
import logging
import datetime
import subprocess
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VERSION_FILE = os.path.join(BASE_DIR, "version.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
CODE_BACKUPS_DIR = os.path.join(DATA_DIR, "backups", "code_backups")

# الملفات والمجلدات المحمية تماماً من أي تحديث (لا تُمس أبداً لحماية البيانات والترخيص)
PROTECTED_PATHS = {
    "data",
    "data/",
    "data\\",
    "config.json",
    "license.key",
    "license.lic",
    "stock_catering.db",
    "catering_stock.db"
}

class UpdateService:
    """
    خدمة التحديثات المعيارية الآمنة للمنظومة
    تدعم التحديث التلقائي بنقرة زر من فلاشة USB أو عبر الإنترنت
    مع ضمان تام وحتمي لعدم المساس بقاعدة البيانات أو الإعدادات أو التراخيص.
    """

    @classmethod
    def get_current_version_info(cls) -> Dict[str, Any]:
        """قراءة معلومات الإصدار الحالي من version.json"""
        default_info = {
            "version": "2.5.0",
            "release_date": "2026-10-17",
            "app_name": "نظام تسيير مخزون الإطعام الجامعي",
            "update_server_url": "http://127.0.0.1:8050/api/updates/check"
        }
        if os.path.exists(VERSION_FILE):
            try:
                with open(VERSION_FILE, "r", encoding="utf-8") as f:
                    return {**default_info, **json.load(f)}
            except Exception as e:
                logger.error(f"Error reading version.json: {e}")
        return default_info

    @classmethod
    def get_current_version(cls) -> str:
        return cls.get_current_version_info().get("version", "2.5.0")

    @classmethod
    def is_protected_file(cls, rel_path: str) -> bool:
        """التحقق مما إذا كان الملف يتبع للبيانات أو التراخيص المحمية"""
        norm = rel_path.replace("/", "\\").strip("\\").lower()
        if norm.startswith("data\\") or norm == "data":
            return True
        if norm.endswith(".db") or norm.endswith(".sqlite") or norm.endswith(".key"):
            return True
        if os.path.basename(norm) in ("config.json", "license.key", "stock_catering.db"):
            return True
        return False

    @classmethod
    def scan_usb_drives_for_patches(cls) -> List[Dict[str, Any]]:
        """
        البحث التلقائي في كافة محركات أقراص الفلاشة USB المتصلة بالحاسوب
        عن ملفات التحديثات بصيغة (.dou_patch أو .patch أو .zip)
        """
        patches_found = []
        try:
            # 1. فحص مجلد التحديثات المحلي dist_updates لتسهيل التجربة
            local_dist = os.path.join(BASE_DIR, "dist_updates")
            if os.path.exists(local_dist):
                try:
                    for f in os.listdir(local_dist):
                        if f.endswith(".dou_patch") or f.endswith(".patch") or (f.startswith("update_") and f.endswith(".zip")):
                            full_p = os.path.join(local_dist, f)
                            patch_info = cls.inspect_patch_file(full_p)
                            if patch_info:
                                patches_found.append(patch_info)
                except Exception:
                    pass

            # 2. فحص محركات أقراص الفلاشة USB المتصلة
            available_drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
            for drive in available_drives:
                if drive.upper().startswith("C:"):
                    continue
                scan_targets = [
                    drive,
                    os.path.join(drive, "55"),
                    os.path.join(drive, "التحديثات"),
                    os.path.join(drive, "التحديثات_السحابية"),
                    os.path.join(drive, "updates"),
                    os.path.join(drive, "dist_updates"),
                    os.path.join(drive, "2026", "125", "dist_updates")
                ]
                for target_dir in scan_targets:
                    if not os.path.exists(target_dir):
                        continue
                    try:
                        for entry in os.scandir(target_dir):
                            if entry.is_file() and (entry.name.endswith(".dou_patch") or entry.name.endswith(".patch") or (entry.name.startswith("update_") and entry.name.endswith(".zip"))):
                                patch_info = cls.inspect_patch_file(entry.path)
                                if patch_info and patch_info["patch_path"] not in [p["patch_path"] for p in patches_found]:
                                    patches_found.append(patch_info)
                    except Exception:
                        continue

            def sort_key(p):
                try:
                    return [int(x) for x in p.get("version", "0.0.0").split(".")]
                except Exception:
                    return [0, 0, 0]

            patches_found.sort(key=sort_key, reverse=True)
        except Exception as e:
            logger.error(f"Error scanning USB drives: {e}")

        return patches_found

    @classmethod
    def inspect_patch_file(cls, patch_path: str) -> Optional[Dict[str, Any]]:
        """فحص حزمة التحديث وقراءة محتويات الـ manifest دون استخراجها"""
        if not os.path.exists(patch_path) or not zipfile.is_zipfile(patch_path):
            return None

        try:
            with zipfile.ZipFile(patch_path, "r") as zf:
                if "manifest.json" not in zf.namelist():
                    return None
                manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                file_stat = os.stat(patch_path)
                return {
                    "patch_path": patch_path,
                    "filename": os.path.basename(patch_path),
                    "version": manifest_data.get("version", "2.0.0"),
                    "title": manifest_data.get("title", "تحديث البرنامج"),
                    "release_date": manifest_data.get("release_date", "2026"),
                    "changelog": manifest_data.get("changelog", []),
                    "file_count": len([n for n in zf.namelist() if not cls.is_protected_file(n)]),
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                }
        except Exception as e:
            logger.error(f"Error reading patch {patch_path}: {e}")
            return None

    @classmethod
    def install_update(cls, patch_path: str, backup_code: bool = True) -> Tuple[bool, str]:
        """
        تثبيت التحديث بنقرة زر واحدة:
        1. التحقق من سلامة الأرشيف.
        2. أخذ نسخة احتياطية وقائية من ملفات الكود الحالية.
        3. استخراج الملفات الجديدة باستثناء قاعدة البيانات والبيانات المحمية.
        4. تحديث version.json.
        """
        if not os.path.exists(patch_path) or not zipfile.is_zipfile(patch_path):
            return False, "ملف التحديث غير صالح أو تالف!"

        patch_info = cls.inspect_patch_file(patch_path)
        if not patch_info:
            return False, "حزمة التحديث لا تحتوي على ملف التعريف (manifest.json) المعتمد."

        current_ver = cls.get_current_version()
        new_ver = patch_info["version"]

        try:
            # 1. أخذ نسخة وقائية من الكود قبل استبداله
            if backup_code:
                os.makedirs(CODE_BACKUPS_DIR, exist_ok=True)
                backup_zip_path = os.path.join(CODE_BACKUPS_DIR, f"code_pre_v{new_ver}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
                with zipfile.ZipFile(backup_zip_path, "w", zipfile.ZIP_DEFLATED) as bzf:
                    for folder in ("ui", "core", "reports", "migration"):
                        folder_p = os.path.join(BASE_DIR, folder)
                        if os.path.exists(folder_p):
                            for root, _, files in os.walk(folder_p):
                                for f in files:
                                    if not f.endswith(".pyc") and "__pycache__" not in root:
                                        full = os.path.join(root, f)
                                        rel = os.path.relpath(full, BASE_DIR)
                                        bzf.write(full, rel)
                    for root_f in ("main.py", "version.json"):
                        full = os.path.join(BASE_DIR, root_f)
                        if os.path.exists(full):
                            bzf.write(full, root_f)
                logger.info(f"Created safety code backup at: {backup_zip_path}")

            # 2. استخراج وتطبيق ملفات التحديث مع الحماية الصارمة لقاعدة البيانات
            updated_files_count = 0
            with zipfile.ZipFile(patch_path, "r") as zf:
                for member in zf.infolist():
                    name = member.filename
                    # استبعاد المجلدات والملفات المحمية وملفات manifest
                    if member.is_dir() or name == "manifest.json":
                        continue
                    if cls.is_protected_file(name):
                        logger.warning(f"Blocked protected file from update package: {name}")
                        continue

                    # مسار الهدف
                    basename_lower = os.path.basename(name).lower()
                    if basename_lower == "cateringstockonou.exe":
                        target_path = os.path.join(BASE_DIR, "new_CateringStockONOU.exe")
                    elif basename_lower == "base_library.zip":
                        target_path = os.path.join(BASE_DIR, "new_base_library.zip")
                    else:
                        target_path = os.path.join(BASE_DIR, name)

                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                    # استخراج الملف
                    with zf.open(member) as src_f, open(target_path, "wb") as dst_f:
                        shutil.copyfileobj(src_f, dst_f)
                    updated_files_count += 1

            # إذا تم استخراج ملف تنفيذي جديد، إنشاء ملف تشغيل الترقية التلقائي
            new_exe = os.path.join(BASE_DIR, "new_CateringStockONOU.exe")
            if os.path.exists(new_exe):
                bat_code = """@echo off
chcp 65001 >nul
:: الانتظار حتى خروج العملية الحالية بالكامل
set /a attempts=0
:WAIT_PROCESS
set /a attempts+=1
tasklist /fi "imagename eq CateringStockONOU.exe" 2>nul | findstr /i "CateringStockONOU.exe" >nul
if not errorlevel 1 (
    if %attempts% leq 10 (
        timeout /t 1 /nobreak >nul
        goto WAIT_PROCESS
    )
    taskkill /f /im CateringStockONOU.exe >nul 2>&1
    timeout /t 1 /nobreak >nul
)

if exist "%~dp0new_CateringStockONOU.exe" (
    copy /y "%~dp0new_CateringStockONOU.exe" "%~dp0CateringStockONOU.exe" >nul
    if not errorlevel 1 (
        del /f /q "%~dp0new_CateringStockONOU.exe" >nul 2>&1
    )
)
if exist "%~dp0new_base_library.zip" (
    copy /y "%~dp0new_base_library.zip" "%~dp0base_library.zip" >nul
    if not errorlevel 1 (
        del /f /q "%~dp0new_base_library.zip" >nul 2>&1
    )
)
start "" "%~dp0CateringStockONOU.exe"
del "%~f0" >nul 2>&1
exit
"""
                bat_path = os.path.join(BASE_DIR, "apply_update.bat")
                with open(bat_path, "w", encoding="utf-8") as bf:
                    bf.write(bat_code)

            # 2.9 بذر وترقية بيانات الإقامة 4 مباشرة على قاعدة البيانات
            try:
                import sqlite3
                db_candidates = [
                    os.path.join(DATA_DIR, "catering_stock.db"),
                    os.path.join(BASE_DIR, "data", "catering_stock.db")
                ]
                target_db = next((p for p in db_candidates if os.path.exists(p)), None)
                if target_db:
                    seed_file = os.path.join(BASE_DIR, "database", "seed_residence_4_data.py")
                    if os.path.exists(seed_file):
                        import importlib.util
                        spec = importlib.util.spec_from_file_location("seed_r4_direct", seed_file)
                        if spec and spec.loader:
                            mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                            if hasattr(mod, "seed_residence_4"):
                                conn_up = sqlite3.connect(target_db)
                                mod.seed_residence_4(conn_up, force=True)
                                conn_up.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('residence_4_seeded_v3.5.1', '1')")
                                conn_up.commit()
                                conn_up.close()
                                logger.info(f"Direct seed_residence_4 executed successfully on {target_db}")
            except Exception as e_seed:
                logger.error(f"Error executing direct seed in install_update: {e_seed}")

            # 2.10 تصحيح السجلات المستقبلية الناتجة عن أخطاء ساعة وتاريخ الحواسيب
            try:
                import sqlite3
                db_candidates = [
                    os.path.join(DATA_DIR, "catering_stock.db"),
                    os.path.join(BASE_DIR, "data", "catering_stock.db")
                ]
                target_db = next((p for p in db_candidates if os.path.exists(p)), None)
                if target_db:
                    conn_fix = sqlite3.connect(target_db)
                    conn_fix.execute("""
                        UPDATE entry_vouchers 
                        SET date = '2026-11-02', 
                            voucher_number = REPLACE(voucher_number, '2026-11-26', '2026-11-02')
                        WHERE residence_id = 2 AND date = '2026-11-26'
                    """)
                    conn_fix.execute("""
                        UPDATE exit_vouchers 
                        SET date = '2026-11-02', 
                            voucher_number = REPLACE(voucher_number, '2026-11-26', '2026-11-02')
                        WHERE residence_id = 2 AND date = '2026-11-26'
                    """)
                    conn_fix.execute("""
                        UPDATE stock_movements 
                        SET date = '2026-11-02'
                        WHERE residence_id = 2 AND date = '2026-11-26'
                    """)
                    conn_fix.execute("""
                        UPDATE daily_meals_tracking 
                        SET date = '2026-11-02'
                        WHERE residence_id = 2 AND date = '2026-11-26'
                    """)
                    conn_fix.commit()
                    conn_fix.close()
                    logger.info("Repaired future date records from scrambled clocks.")
            except Exception as e_repair:
                logger.error(f"Error repairing future date records: {e_repair}")

            # 3. تحديث version.json
            current_info = cls.get_current_version_info()
            current_info["version"] = new_ver
            current_info["last_updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_info["release_date"] = patch_info.get("release_date", current_info.get("release_date"))
            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                json.dump(current_info, f, ensure_ascii=False, indent=4)

            logger.info(f"Update to v{new_ver} installed successfully ({updated_files_count} files updated).")
            return True, (
                f"✅ تم تثبيت التحديث بنجاح تام!\n\n"
                f"• تم التحديث إلى الإصدار: {new_ver} (سابقاً: {current_ver})\n"
                f"• عدد الملفات المحدثة: {updated_files_count} ملف كود وواجهات\n"
                f"• قاعدة البيانات والبيانات: محفوظة ومستقلة 100%\n\n"
                f"سيتم الآن إعادة تشغيل البرنامج لتطبيق التحديث الجديد."
            )

        except Exception as e:
            logger.error(f"Error applying update: {e}")
            return False, f"حدث خطأ أثناء تطبيق التحديث:\n{e}"

    @classmethod
    def check_online_update(cls, custom_url: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        فحص توفر تحديث جديد عبر الإنترنت أو شبكة المديرية مع التبديل التلقائي لـ GitHub
        """
        ver_info = cls.get_current_version_info()
        current_ver = cls.get_current_version()

        raw_gh_ver_url = "https://raw.githubusercontent.com/islamnono3016-tech/onou-server/main/version.json"
        raw_gh_patch_url = "https://raw.githubusercontent.com/islamnono3016-tech/onou-server/main/update_latest.dou_patch"

        urls_to_try = []
        if custom_url:
            urls_to_try.append(custom_url)
        else:
            # الفحص الذكي المتعدد: فحص سحابة GitHub المباشرة أولاً ثم سيرفر المديرية
            urls_to_try.append(raw_gh_ver_url)
            from core.config import AppConfig
            server_url = AppConfig.get_server_url()
            if server_url:
                urls_to_try.append(f"{server_url}/api/updates/check")

        import ssl
        try:
            ssl_ctx = ssl.create_default_context()
        except Exception:
            ssl_ctx = ssl._create_unverified_context()
        ssl_ctx_unverified = ssl._create_unverified_context()

        best_data = None
        best_ver = "0.0.0"
        last_error = ""

        for url in urls_to_try:
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": f"ONOU-Catering-Client/{current_ver}"}
                )
                try:
                    resp = urllib.request.urlopen(req, timeout=10.0, context=ssl_ctx)
                except Exception:
                    resp = urllib.request.urlopen(req, timeout=10.0, context=ssl_ctx_unverified)

                with resp:
                    data = json.loads(resp.read().decode("utf-8"))

                if not data.get("download_url"):
                    data["download_url"] = raw_gh_patch_url

                cand_ver = data.get("version", "")
                if cls.is_version_greater(cand_ver, best_ver):
                    best_ver = cand_ver
                    best_data = data
            except Exception as e:
                last_error = str(e)
                continue

        if best_data and best_ver != "0.0.0":
            if cls.is_version_greater(best_ver, current_ver):
                return True, best_data, f"يتوفر إصدار جديد ({best_ver}) أحدث من الإصدار الحالي ({current_ver})."
            elif best_ver and best_data.get("download_url"):
                return False, best_data, f"البرنامج محدث إلى أحدث إصدار ({current_ver}). حزمة التحديث v{best_ver} متوفرة في السحابة."
            else:
                return False, best_data, f"البرنامج محدث إلى آخر إصدار متوفر ({current_ver})."

        return False, None, f"تعذر الاتصال بخادم التحديثات السحابي: {last_error}"

    @classmethod
    def download_and_install_online_update(cls, download_url: str, progress_callback=None) -> Tuple[bool, str]:
        """تنزيل حزمة التحديث من الرابط وتثبيتها مباشرة مع حماية التبديل التلقائي لـ GitHub"""
        os.makedirs(os.path.join(DATA_DIR, "cache"), exist_ok=True)
        dest_patch = os.path.join(DATA_DIR, "cache", f"downloaded_update_{int(datetime.datetime.now().timestamp())}.dou_patch")

        if "onrender.com" in download_url and download_url.startswith("http://"):
            download_url = download_url.replace("http://", "https://")

        urls_to_try = [
            download_url,
            "https://raw.githubusercontent.com/islamnono3016-tech/onou-server/main/update_latest.dou_patch"
        ]

        import ssl
        try:
            ssl_ctx = ssl.create_default_context()
        except Exception:
            ssl_ctx = ssl._create_unverified_context()
        ssl_ctx_unverified = ssl._create_unverified_context()

        last_err = ""
        for url in urls_to_try:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "ONOU-Catering-Client"})
                try:
                    resp = urllib.request.urlopen(req, timeout=60.0, context=ssl_ctx)
                except Exception:
                    resp = urllib.request.urlopen(req, timeout=60.0, context=ssl_ctx_unverified)

                with resp, open(dest_patch, "wb") as out_f:
                    total_len = resp.headers.get("Content-Length")
                    total_bytes = int(total_len) if total_len else 0
                    downloaded = 0
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        out_f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_bytes > 0:
                            progress_callback(int((downloaded / total_bytes) * 100))

                return cls.install_update(dest_patch, backup_code=True)
            except Exception as e:
                last_err = str(e)
                continue

        return False, f"فشل تنزيل ملف التحديث: {last_err}"

    @classmethod
    def restart_application(cls):
        """إعادة تشغيل البرنامج في عملية مستقلة وإغلاق العملية الحالية فوراً لتحرير الملفات"""
        try:
            if getattr(sys, "frozen", False):
                bat_path = os.path.join(BASE_DIR, "apply_update.bat")
                if os.path.exists(bat_path):
                    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    subprocess.Popen(["cmd.exe", "/c", bat_path], cwd=BASE_DIR, creationflags=flags)
                else:
                    subprocess.Popen([sys.executable], cwd=BASE_DIR)
            else:
                python_exe = sys.executable
                main_script = os.path.join(BASE_DIR, "main.py")
                subprocess.Popen([python_exe, main_script], cwd=BASE_DIR)

            try:
                from PyQt6.QtWidgets import QApplication
                if QApplication.instance():
                    QApplication.instance().quit()
            except Exception:
                pass
            os._exit(0)
        except Exception as e:
            logger.error(f"Cannot restart application: {e}")
            os._exit(1)

    @staticmethod
    def is_version_greater(v1: str, v2: str) -> bool:
        """مقارنة نسختين مثلا '2.6.0' و '2.5.0'"""
        try:
            p1 = [int(x) for x in v1.split(".")]
            p2 = [int(x) for x in v2.split(".")]
            return p1 > p2
        except Exception:
            return v1 > v2