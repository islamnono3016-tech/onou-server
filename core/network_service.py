import os
import sys
import socket
import threading
import json
import logging
import datetime
import time
from typing import Optional, Dict, Any, List, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import string
import requests

from database.db_manager import DatabaseManager
from core.auth_service import AuthService
from core.residence_service import ResidenceService
from core.config import AppConfig

logger = logging.getLogger(__name__)

def get_local_ip() -> str:
    """الحصول على عنوان IP لجهاز الكمبيوتر على شبكة الوايفاي أو الشبكة المحلية"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class NetworkServer:
    """
    خادم الواجهة البرمجية المركزي لمديرية الخدمات الجامعية (Central Directorate REST API Server)
    يستقبل طلبات المزامنة من الإقامات، ويتحقق من المصادقة، ويدير تبادل البيانات اللحظية
    """

    def __init__(self, port: int = 8050, db_manager: Optional[DatabaseManager] = None):
        self.port = port
        self.db = db_manager or DatabaseManager()
        self.auth_svc = AuthService(self.db)
        self.res_svc = ResidenceService(self.db)
        self.server_thread: Optional[threading.Thread] = None
        self.httpd: Optional[ThreadedHTTPServer] = None
        self.is_running = False
        self.local_ip = get_local_ip()

    def start(self):
        """تشغيل خادم الشبكة في خلفية البرنامج دون تجميد الواجهة الرسومية"""
        if self.is_running:
            return

        auth_svc = self.auth_svc
        res_svc = self.res_svc
        db = self.db
        local_ip = self.local_ip
        port = self.port

        _IP_REQUEST_LOG: Dict[str, List[float]] = {}
        MAX_REQ_PER_MIN = 180
        MAX_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5 MB max request size

        class RequestHandler(BaseHTTPRequestHandler):
            server_version = "ONOU-SecureServer/3.0"
            sys_version = ""

            def _check_rate_limit(self) -> bool:
                client_ip = self.client_address[0] if self.client_address else "unknown"
                now = time.time()
                ts = [t for t in _IP_REQUEST_LOG.get(client_ip, []) if now - t < 60]
                if len(ts) >= MAX_REQ_PER_MIN:
                    _IP_REQUEST_LOG[client_ip] = ts
                    return False
                ts.append(now)
                _IP_REQUEST_LOG[client_ip] = ts
                return True

            def _send_json(self, status_code: int, data: dict):
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                # ترويسات الأمان الصارمة ضد هجمات الويب والاختراق
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("X-XSS-Protection", "1; mode=block")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-ONOU-Token")
                self.end_headers()
                self.wfile.write(body)

            def do_OPTIONS(self):
                self._send_json(200, {"status": "ok"})

            def do_GET(self):
                if not self._check_rate_limit():
                    self._send_json(429, {"error": "Rate limit exceeded. Please slow down."})
                    return
                path = self.path.split("?")[0]
                query_params = {}
                if "?" in self.path:
                    raw_q = self.path.split("?")[1]
                    for pair in raw_q.split("&"):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            query_params[k] = v

                if path == "/api/status":
                    self._send_json(200, {
                        "status": "online",
                        "ip": local_ip,
                        "port": port,
                        "system": "منظومة تسيير مخزون الإطعام الجامعي - مديرية الخدمات الجامعية",
                        "architecture": "Client-Server Multi-Campus Architecture",
                        "version": "3.0",
                        "server_time": datetime.datetime.now().isoformat()
                    })

                elif path == "/api/residences":
                    res_list = res_svc.list_residences(only_active=True)
                    self._send_json(200, {"residences": res_list})

                elif path == "/api/overview":
                    overview = res_svc.get_residences_overview()
                    self._send_json(200, {"overview": overview})

                elif path == "/api/sync/catalog":
                    # إرجاع دليل المواد الرسمي والأسعار للإقامة
                    r_id = int(query_params.get("residence_id", 1))
                    with db.get_connection() as conn:
                        arts = conn.execute("""
                            SELECT a.id, a.code, a.name, a.unit, a.price_ht, a.discount_rate,
                                   a.discount_amount, a.price_after_discount, a.tva_rate, a.price_ttc,
                                   COALESCE(ra.safety_stock, a.safety_stock) as safety_stock
                            FROM articles a
                            LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                            WHERE a.is_active = 1
                            ORDER BY a.id ASC
                        """, (r_id,)).fetchall()
                        self._send_json(200, {"articles": [dict(a) for a in arts]})

                elif path == "/api/directorate/super_dashboard":
                    # لوحة القيادة العليا لمديرية الخدمات
                    overview = res_svc.get_residences_overview()
                    with db.get_connection() as conn:
                        # 1. إجمالي قيمة المخزون الولائي
                        tot_stock_val = conn.execute("""
                            SELECT COALESCE(SUM(ra.current_stock * a.price_ttc), 0)
                            FROM residence_articles ra
                            JOIN articles a ON ra.article_id = a.id
                        """).fetchone()[0]

                        # 2. المواد التي تشهد عجزاً حاداً في أي إقامة (لإجراء تحويلات)
                        deficit_items = conn.execute("""
                            SELECT r.name as residence_name, a.name as article_name, a.unit,
                                   ra.current_stock, ra.safety_stock, a.price_ttc
                            FROM residence_articles ra
                            JOIN residences r ON ra.residence_id = r.id
                            JOIN articles a ON ra.article_id = a.id
                            WHERE ra.current_stock <= (ra.safety_stock * 0.5) AND r.is_active = 1
                            ORDER BY ra.current_stock ASC LIMIT 20
                        """).fetchall()

                        self._send_json(200, {
                            "overview": overview,
                            "total_state_stock_value": tot_stock_val,
                            "critical_deficit_alerts": [dict(d) for d in deficit_items]
                        })

                elif path == "/api/updates/check":
                    if getattr(sys, "frozen", False):
                        base_dir = os.path.dirname(os.path.abspath(sys.executable))
                    else:
                        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

                    ver_file = os.path.join(base_dir, "version.json")
                    ver_info = {
                        "version": "2.8.0",
                        "release_date": "2026-10-18",
                        "title": "نظام تسيير مخزون الإطعام الجامعي - تحديث المطبوعات والشبكة",
                        "changelog": [
                            "رسم خطوط واضحة ودقيقة (Borders) لكافة جداول التقارير والمطبوعات",
                            "ضبط وتنسيق انتهاء كل صفحة بجدول الإمضاءات وبدء كل حصة في صفحة جديدة",
                            "إضافة خاصية الطباعة بفترة مخصصة (من - إلى) لجميع التقارير الـ 8",
                            "تحديث وتثبيت التحديثات تلقائياً عبر الفلاشة وعبر شبكة الوايفاي"
                        ]
                    }
                    if os.path.exists(ver_file):
                        try:
                            with open(ver_file, "r", encoding="utf-8") as vf:
                                ver_info.update(json.load(vf))
                        except Exception:
                            pass

                    # البحث عن حزمة التحديث في مختلف المسارات الممكنة ومحركات الأقراص
                    search_locations = [
                        os.path.join(base_dir, "dist_updates"),
                        base_dir,
                        r"F:\2026\1255",
                        "F:\\"
                    ]
                    for d_letter in string.ascii_uppercase:
                        d_path = f"{d_letter}:\\"
                        if os.path.exists(d_path) and d_path not in search_locations:
                            search_locations.append(d_path)

                    patch_found = False
                    for loc in search_locations:
                        if os.path.exists(loc):
                            try:
                                for f in os.listdir(loc):
                                    if f.endswith(".dou_patch") or f.endswith(".patch") or (f.startswith("update_") and f.endswith(".zip")):
                                        patch_found = True
                                        break
                            except Exception:
                                pass
                        if patch_found:
                            break

                    req_host = self.headers.get("Host", f"{local_ip}:{port}")
                    dl_url = f"http://{req_host}/api/updates/download" if patch_found else ""
                    self._send_json(200, {
                        "version": ver_info.get("version", "2.8.0"),
                        "title": ver_info.get("title", "تحديث البرنامج"),
                        "release_date": ver_info.get("release_date", "2026-10-18"),
                        "changelog": ver_info.get("changelog", []),
                        "download_url": dl_url
                    })

                elif path == "/api/updates/download":
                    if getattr(sys, "frozen", False):
                        base_dir = os.path.dirname(os.path.abspath(sys.executable))
                    else:
                        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

                    search_locations = [
                        os.path.join(base_dir, "dist_updates"),
                        base_dir,
                        r"F:\2026\1255",
                        "F:\\"
                    ]
                    for d_letter in string.ascii_uppercase:
                        d_path = f"{d_letter}:\\"
                        if os.path.exists(d_path) and d_path not in search_locations:
                            search_locations.append(d_path)

                    target_file = None
                    p_files = []
                    for loc in search_locations:
                        if os.path.exists(loc):
                            try:
                                for f in os.listdir(loc):
                                    if f.endswith(".dou_patch") or f.endswith(".patch") or (f.startswith("update_") and f.endswith(".zip")):
                                        p_files.append(os.path.join(loc, f))
                            except Exception:
                                pass

                    if p_files:
                        # اختيار أحدث ملف تعديلاً
                        target_file = max(p_files, key=os.path.getmtime)

                    if target_file and os.path.exists(target_file):
                        try:
                            file_size = os.path.getsize(target_file)
                            self.send_response(200)
                            self.send_header("Content-Type", "application/octet-stream")
                            self.send_header("Content-Length", str(file_size))
                            self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(target_file)}"')
                            self.send_header("Connection", "close")
                            self.end_headers()
                            with open(target_file, "rb") as pf:
                                while True:
                                    chunk = pf.read(65536)
                                    if not chunk:
                                        break
                                    self.wfile.write(chunk)
                        except (ConnectionResetError, BrokenPipeError):
                            pass
                        except Exception as e:
                            logger.error(f"Error streaming patch: {e}")
                    else:
                        self._send_json(404, {"error": "No update package available on server"})

                else:
                    self._send_json(404, {"error": "Endpoint Not Found"})

            def do_POST(self):
                try:
                    if not self._check_rate_limit():
                        self._send_json(429, {"error": "Rate limit exceeded. Please slow down."})
                        return

                    path = self.path.split("?")[0]
                    content_len_hdr = self.headers.get("Content-Length", "0")
                    content_len = int(content_len_hdr) if content_len_hdr else 0

                    if content_len > MAX_PAYLOAD_SIZE:
                        self._send_json(413, {"error": "Payload Too Large (Maximum 5MB allowed)"})
                        return

                    body_bytes = self.rfile.read(content_len) if content_len > 0 else b"{}"

                    try:
                        payload = json.loads(body_bytes.decode("utf-8"))
                    except Exception:
                        payload = {}

                    if path == "/api/auth/login":
                        username = payload.get("username", "")
                        password = payload.get("password", "")
                        try:
                            user = auth_svc.login(username, password)
                            if user:
                                self._send_json(200, {"success": True, "user": user})
                            else:
                                self._send_json(401, {"detail": "اسم المستخدم أو كلمة المرور غير صحيحة"})
                        except PermissionError as pe:
                            self._send_json(403, {"detail": str(pe)})
                        except Exception as e:
                            self._send_json(500, {"detail": str(e)})

                    elif path == "/api/sync/push":
                        # استقبال ومعالجة حركات رتل المزامنة من الإقامة - Accept-All Pattern
                        import json as _json
                        r_id = payload.get("residence_id")
                        items = payload.get("items", [])
                        synced_ids = []

                        with db.get_connection() as conn:
                            # جدول السجل الخام - يضمن حفظ البيانات حتى لو فشلت المعالجة
                            conn.execute("""
                                CREATE TABLE IF NOT EXISTS server_sync_log (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    sync_id TEXT UNIQUE,
                                    residence_id INTEGER,
                                    entity_type TEXT,
                                    action TEXT,
                                    entity_id TEXT,
                                    payload TEXT,
                                    received_at TEXT,
                                    processed INTEGER DEFAULT 0,
                                    process_error TEXT
                                )
                            """)

                            for it in items:
                                sync_id = it.get("sync_id", "")
                                entity_type = it.get("entity_type", "")
                                action = it.get("action", "")
                                entity_id = str(it.get("entity_id", ""))
                                data = it.get("payload", {})
                                now_item = datetime.datetime.now().isoformat()

                                # 1. حفظ البيانات الخام دائماً (Accept-All)
                                try:
                                    conn.execute("""
                                        INSERT OR IGNORE INTO server_sync_log
                                            (sync_id, residence_id, entity_type, action, entity_id, payload, received_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, (sync_id, r_id, entity_type, action, entity_id,
                                          _json.dumps(data, ensure_ascii=False), now_item))
                                except Exception:
                                    pass

                                # 2. محاولة المعالجة (لا تُوقف العملية عند الفشل)
                                processed = False
                                try:
                                    if entity_type == "daily_sheet_full":
                                        from core.stock_service import StockService
                                        stk = StockService(db, residence_id=r_id)
                                        stk.save_daily_sheet_full(
                                            data["date"],
                                            data.get("articles", []),
                                            tickets_input=data.get("tickets"),
                                            menu_input=data.get("menus")
                                        )
                                        processed = True
                                    elif entity_type == "entry_voucher":
                                        from core.stock_service import StockService
                                        stk = StockService(db, residence_id=r_id)
                                        stk.create_entry_voucher(data["voucher"], data["items"])
                                        processed = True
                                    elif entity_type == "exit_voucher":
                                        from core.stock_service import StockService
                                        stk = StockService(db, residence_id=r_id)
                                        stk.create_exit_voucher(data["voucher"], data["items"])
                                        processed = True
                                    else:
                                        processed = True  # نوع غير معروف - نقبله

                                    if processed:
                                        try:
                                            conn.execute(
                                                "UPDATE server_sync_log SET processed=1 WHERE sync_id=?",
                                                (sync_id,)
                                            )
                                        except Exception:
                                            pass

                                except Exception as item_err:
                                    logger.warning(f"Processing warning for {sync_id} ({entity_type}): {item_err}")
                                    try:
                                        conn.execute(
                                            "UPDATE server_sync_log SET process_error=? WHERE sync_id=?",
                                            (str(item_err)[:500], sync_id)
                                        )
                                    except Exception:
                                        pass

                                # 3. يُعدّ مقبولاً دائماً طالما وصلت البيانات للخادم
                                synced_ids.append(sync_id)

                            # تسجيل آخر وقت مزامنة للإقامة
                            now_str = datetime.datetime.now().isoformat()
                            conn.execute("""
                                INSERT INTO sync_state (residence_id, last_push_timestamp, status)
                                VALUES (?, ?, 'ONLINE')
                                ON CONFLICT(residence_id) DO UPDATE SET
                                    last_push_timestamp = excluded.last_push_timestamp,
                                    status = 'ONLINE'
                            """, (r_id, now_str))
                            conn.commit()

                        self._send_json(200, {
                            "success": True,
                            "synced_count": len(synced_ids),
                            "synced_ids": synced_ids
                        })

                    else:
                        self._send_json(404, {"error": "Endpoint not found"})

                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    self._send_json(500, {"error": str(ex)})

            def log_message(self, format, *args):
                pass

        try:
            self.httpd = ThreadedHTTPServer(("0.0.0.0", self.port), RequestHandler)
            self.is_running = True

            self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.server_thread.start()
            logger.info(f"Central Directorate REST API Server running on {self.local_ip}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start Central REST Server on port {self.port}: {e}")

    def stop(self):
        if self.httpd and self.is_running:
            self.is_running = False
            self.httpd.shutdown()
            self.httpd.server_close()

class NetworkClient:
    """
    عميل الشبكة الميداني المعتمد في الإقامات للاتصال بسيرفر المديرية المركزي
    """

    def __init__(self, server_host: Optional[str] = None, port: Optional[int] = None):
        if server_host:
            raw = server_host.strip()
            p = port or 8050
            if raw.startswith("http://") or raw.startswith("https://"):
                d_part = raw.split("://", 1)[1]
                if ":" in d_part or "/" in d_part or p in (80, 443):
                    self.base_url = raw.rstrip("/")
                else:
                    self.base_url = f"{raw.rstrip('/')}:{p}"
            else:
                if ":" in raw:
                    self.base_url = f"http://{raw}"
                elif p == 443:
                    self.base_url = f"https://{raw}"
                else:
                    self.base_url = f"http://{raw}:{p}"
            self.server_host = raw
            self.port = p
        else:
            self.server_host = AppConfig.get("server_host", "127.0.0.1")
            self.port = AppConfig.get("server_port", 8050)
            self.base_url = AppConfig.get_server_url()

    def check_connection(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/status", timeout=AppConfig.get("timeout_seconds", 3.0))
            return r.status_code == 200
        except Exception:
            return False

    def ping(self) -> Tuple[bool, float, str]:
        """فحص زمن الاستجابة (Latency) بالمللي ثانية ورسالة الحالة"""
        t0 = datetime.datetime.now()
        try:
            r = requests.get(f"{self.base_url}/api/status", timeout=AppConfig.get("timeout_seconds", 3.0))
            ms = (datetime.datetime.now() - t0).total_seconds() * 1000.0
            if r.status_code == 200:
                return (True, ms, "متصل بالسيرفر المركزي بنجاح")
            return (False, ms, f"استجابة غير متوقعة: {r.status_code}")
        except requests.exceptions.Timeout:
            return (False, 0.0, "انتهت مهلة الاتصال بالخادم (Timeout)")
        except requests.exceptions.ConnectionError:
            return (False, 0.0, "تعذر الوصول إلى عنوان الخادم (تأكد من عنوان IP والمنفذ)")
        except Exception as e:
            return (False, 0.0, f"خطأ في الاتصال: {e}")

    def login(self, username: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/auth/login"
        r = requests.post(url, json={"username": username, "password": password}, timeout=8.0)
        if r.status_code == 200:
            return r.json()
        elif r.status_code in (401, 403):
            detail = r.json().get("detail", "خطأ في تسجيل الدخول")
            raise PermissionError(detail)
        else:
            raise ConnectionError(f"خطأ في الاتصال بالخادم: {r.status_code}")

    def get_super_dashboard(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/directorate/super_dashboard"
        r = requests.get(url, timeout=10.0)
        if r.status_code == 200:
            return r.json()
        raise ConnectionError(f"تعذر جلب بيانات لوحة التحكم المركزية: {r.status_code}")

    @staticmethod
    def scan_for_servers(port: int = 8050, timeout: float = 0.3) -> List[str]:
        """فحص سريع لشبكة الوايفاي أو الشبكة المحلية للعثور على جهاز السيرفر تلقائياً"""
        local_ip = get_local_ip()
        parts = local_ip.split(".")
        if len(parts) != 4:
            return []

        subnet = f"{parts[0]}.{parts[1]}.{parts[2]}"
        found_servers = []

        def ping_ip(target_ip):
            try:
                r = requests.get(f"http://{target_ip}:{port}/api/status", timeout=timeout)
                if r.status_code == 200:
                    found_servers.append(target_ip)
            except Exception:
                pass

        threads = []
        scan_range = [local_ip] + [f"{subnet}.{i}" for i in range(1, 40) if f"{subnet}.{i}" != local_ip]
        for ip in scan_range:
            t = threading.Thread(target=ping_ip, args=(ip,), daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=timeout + 0.1)

        return list(set(found_servers))
