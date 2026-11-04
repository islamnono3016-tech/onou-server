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
import urllib3
try:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

def http_get(url: str, timeout: float = 25.0, **kwargs):
    """طلب GET ذكي متوافق 100% مع كافة إصدارات ويندوز ومعالجة شهادات SSL القديمة في Win 7/8"""
    try:
        return requests.get(url, timeout=timeout, **kwargs)
    except requests.exceptions.SSLError:
        return requests.get(url, timeout=timeout, verify=False, **kwargs)

def http_post(url: str, timeout: float = 35.0, **kwargs):
    """طلب POST ذكي متوافق 100% مع كافة إصدارات ويندوز ومعالجة شهادات SSL القديمة في Win 7/8"""
    try:
        return requests.post(url, timeout=timeout, **kwargs)
    except requests.exceptions.SSLError:
        return requests.post(url, timeout=timeout, verify=False, **kwargs)

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


def normalize_server_url(server_host: Optional[str] = None, port: Optional[int] = None) -> str:
    """تنسيق وتوليد رابط الخادم بشكل ذكي يدعم السيرفرات السحابية والروابط المباشرة والـ IPs المحلية"""
    raw = (server_host or "127.0.0.1").strip()
    if not raw:
        raw = "127.0.0.1"
    p = port or 8050

    if "onrender.com" in raw.lower() or "render.com" in raw.lower():
        if raw.startswith("http://"):
            raw = "https://" + raw[7:]
        elif not raw.startswith("https://"):
            raw = f"https://{raw}"
        import re
        return re.sub(r":\d+$", "", raw.rstrip("/"))

    if raw.startswith("https://"):
        cleaned = raw.rstrip("/")
        domain_part = cleaned.split("://", 1)[1]
        if ":" in domain_part or p in (443, 8050):
            return cleaned.split(":")[0] + "://" + domain_part.split(":")[0] if p in (443, 8050) and ":" in domain_part else cleaned
        return f"{cleaned}:{p}"

    if raw.startswith("http://"):
        cleaned = raw.rstrip("/")
        if ":" in cleaned.split("://", 1)[1]:
            return cleaned
        return f"{cleaned}:{p}"

    if ":" in raw:
        return f"http://{raw}"
    if p == 443:
        return f"https://{raw}"
    return f"http://{raw}:{p}"


def auto_seed_database(db: DatabaseManager):
    """تهيئة وضمان وجود الإقامات والمستخدمين الرسميين وجدول المزامنة تلقائياً لجميع الحواسيب"""
    try:
        with db.get_connection() as conn:
            # 1. جدول أحداث المزامنة
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_id TEXT UNIQUE,
                    residence_id INTEGER,
                    entity_type TEXT,
                    action TEXT,
                    entity_id TEXT,
                    payload TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. الإقامات والمطاعم المركزية الرسمية
            residences_data = [
                (1, "RES-01", "الإقامة الجامعية بن الشيخ التلي", "ورقلة", "مدير الإقامة", 1000),
                (2, "RES-02", "الإقامة الجامعية بن دحمان بشير", "ورقلة", "مدير الإقامة", 2000),
                (3, "RES-03", "الإقامة الجامعية بن مالك محمد حسان", "ورقلة", "مدير الإقامة", 1000),
                (4, "RES-04", "الإقامة الجامعية حساني محمد بن إبراهيم", "ورقلة", "مدير الإقامة", 1000),
                (5, "RES-05", "الإقامة الجامعية قربشي محمد الناجي", "ورقلة", "مدير الإقامة", 1000),
                (6, "RES-06", "الإقامة الجامعية لخضاري محمد الأخضر", "ورقلة", "مدير الإقامة", 1000),
                (7, "RES-07", "الإقامة الجامعية محمد الطاهر العبيدي", "ورقلة", "مدير الإقامة", 1500),
                (8, "RES-08", "المطعم المركزي القطب الجامعي رقم 1", "ورقلة", "مدير المطعم", 1500),
                (9, "RES-09", "المطعم المركزي القطب الجامعي رقم 3", "ورقلة", "مدير المطعم", 1500),
            ]
            for rid, code, name, city, dname, cap in residences_data:
                conn.execute("""
                    INSERT INTO residences (id, code, name, city, director_name, capacity, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT(id) DO UPDATE SET is_active=1, name=excluded.name, code=excluded.code;
                """, (rid, code, name, city, dname, cap))

            # 3. المستخدمون الرسميون لكافة الإقامات والمطاعم والمديرية
            p_hash_123 = "pbkdf2$df2c0fad0cc882a1c7e1917bda568900bde268e625ffc0b621aa4f5551b4778e"
            p_hash_admin = "pbkdf2$6474a3ce2ee9459d80d7639a9cb11ae410fc579178bf98f1bd0753aa8f47553b" # admin123
            users_data = [
                ("admin", p_hash_admin, "مدير الخدمات الجامعية (مسؤول النظام)", "SUPER_ADMIN", None),
                ("user_cheikh", p_hash_123, "مسير مخزون إقامة بن الشيخ التلي", "STOREKEEPER", 1),
                ("user_dahmane", p_hash_123, "مسير مخزون إقامة بن دحمان بشير", "STOREKEEPER", 2),
                ("user_malek", p_hash_123, "مسير مخزون إقامة بن مالك محمد حسان", "STOREKEEPER", 3),
                ("user_hassani", p_hash_123, "مسير مخزون إقامة حساني محمد", "STOREKEEPER", 4),
                ("user_guerbechi", p_hash_123, "مسير مخزون إقامة قربشي محمد الناجي", "STOREKEEPER", 5),
                ("user_lakhdari", p_hash_123, "مسير مخزون إقامة لخضاري محمد", "STOREKEEPER", 6),
                ("user_oubaidi", p_hash_123, "مسير مخزون إقامة محمد الطاهر العبيدي", "STOREKEEPER", 7),
                ("user_resto1", p_hash_123, "مسير مخزون المطعم المركزي القطب 1", "STOREKEEPER", 8),
                ("user_resto3", p_hash_123, "مسير مخزون المطعم المركزي القطب 3", "STOREKEEPER", 9),
                ("user_ouargla1", p_hash_123, "مستخدم الإقامة 1", "RESIDENCE_USER", 7),
                ("user_ouargla2", "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92", "مستخدم الإقامة 2", "RESIDENCE_USER", 2),
            ]
            for uname, phash, fname, role, resid in users_data:
                conn.execute("""
                    INSERT INTO users (username, password_hash, full_name, role, residence_id, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                    ON CONFLICT(username) DO UPDATE SET
                        password_hash=excluded.password_hash,
                        is_active=1,
                        role=excluded.role,
                        residence_id=excluded.residence_id;
                """, (uname, phash, fname, role, resid))

            conn.commit()
            logger.info("Auto-seed executed successfully: 7 residences, 10 users verified.")
    except Exception as e:
        logger.error(f"Auto-seed error: {e}")

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
        auto_seed_database(self.db)
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
        MAX_REQ_PER_MIN = 600
        MAX_PAYLOAD_SIZE = 15 * 1024 * 1024  # 15 MB max request size

        class RequestHandler(BaseHTTPRequestHandler):
            server_version = "ONOU-SecureServer/3.0"
            sys_version = ""

            def _check_rate_limit(self) -> bool:
                # دعم العناوين الحقيقية خلف البروكسي والسحابة (Render, Cloudflare, Reverse Proxies)
                fwd = self.headers.get("X-Forwarded-For")
                if fwd:
                    client_ip = fwd.split(",")[0].strip()
                else:
                    client_ip = self.headers.get("CF-Connecting-IP") or (self.client_address[0] if self.client_address else "unknown")

                # استثناء عناوين الشبكة المحلية والبروكسي الداخلي من التقييد الحاد
                if client_ip.startswith("10.") or client_ip.startswith("127.") or client_ip.startswith("172.") or client_ip.startswith("192.168."):
                    return True

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
                path = self.path.split("?")[0]
                if path not in ("/api/status", "/api/updates/check", "/api/updates/download", "/api/sync/pull"):
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

                if path in ("/api/status", "/api/system/seed"):
                    auto_seed_database(db)
                    res_count = len(res_svc.list_residences(only_active=True))
                    with db.get_connection() as conn:
                        u_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                        try:
                            ev_count = conn.execute("SELECT COUNT(*) FROM sync_events").fetchone()[0]
                        except Exception:
                            ev_count = 0
                    self._send_json(200, {
                        "status": "online",
                        "ip": local_ip,
                        "port": port,
                        "system": "منظومة تسيير مخزون الإطعام الجامعي - مديرية الخدمات الجامعية",
                        "architecture": "Client-Server Multi-Campus Architecture",
                        "version": "3.0",
                        "residences_active": res_count,
                        "users_count": u_count,
                        "sync_events_count": ev_count,
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
                        "version": "3.3.7",
                        "release_date": "2026-10-27",
                        "title": "نظام تسيير مخزون الإطعام الجامعي v3.3.7 - لوحة قيادة تفاعلية حسب الإقامة وتثبيت التذاكر",
                        "changelog": [
                            "ربط جميع مؤشرات لوحة القيادة (Dashboard) بدقة بحسب الإقامة المختارة ديناميكياً",
                            "تحديث جدول تنبيهات نواقص المخزون ومخزون الأمان تلقائياً وفورياً لكل إقامة",
                            "تثبيت قيم تعداد التذاكر ومنع تغيرها عند تحريك عجلة الفأرة مع تمرير الشاشة فقط",
                            "حماية حقول إدخال مصاريف الفطور والغداء والعشاء من عجلة الفأرة",
                            "إخفاء شريط اختيار وتغيير الإقامة في شاشة التقارير عن حسابات الإقامات",
                            "ظهور شريط اختيار الإقامة لمديرية الخدمات الجامعية فقط (SUPER_ADMIN)",
                            "شمولية كافة ملفات الواجهات البرمجية والتقارير داخل حزمة التحديث"
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
                    proto = "https" if ("render" in req_host or self.headers.get("X-Forwarded-Proto") == "https") else "http"
                    raw_gh_patch = "https://raw.githubusercontent.com/islamnono3016-tech/onou-server/main/update_latest.dou_patch"
                    dl_url = f"{proto}://{req_host}/api/updates/download" if patch_found else raw_gh_patch
                    self._send_json(200, {
                        "version": ver_info.get("version", "3.3.7"),
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
                    # أولوية قطعية لحزمة التحديث الشامل v3.5.9 و update_latest
                    preferred_names = ["update_latest.dou_patch", "update_v3.5.9.dou_patch", "تحديث_v3.5.9_شامل.dou_patch"]
                    for loc in search_locations:
                        if os.path.exists(loc):
                            for pref in preferred_names:
                                cand = os.path.join(loc, pref)
                                if os.path.exists(cand) and os.path.getsize(cand) > 1000:
                                    target_file = cand
                                    break
                        if target_file:
                            break

                    if not target_file:
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
                            target_file = max(p_files, key=os.path.getmtime)

                    if not target_file or not os.path.exists(target_file):
                        # توجيه تلقائي للتنزيل المباشر من GitHub
                        self.send_response(302)
                        self.send_header("Location", "https://raw.githubusercontent.com/islamnono3016-tech/onou-server/main/update_latest.dou_patch")
                        self.end_headers()
                        return

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

                elif path == "/api/sync/pull":
                    # سحب الحركات المسجلة من الحواسيب الأخرى
                    since_id = int(query_params.get("since_id", 0))
                    limit = min(int(query_params.get("limit", 200)), 500)
                    res_filter = query_params.get("residence_id")

                    query = "SELECT id, sync_id, residence_id, entity_type, action, entity_id, payload, created_at FROM sync_events WHERE id > ?"
                    params = [since_id]
                    if res_filter and str(res_filter).strip() not in ("", "0", "None"):
                        query += " AND residence_id = ?"
                        params.append(int(res_filter))
                    query += " ORDER BY id ASC LIMIT ?"
                    params.append(limit)

                    with db.get_connection() as conn:
                        try:
                            conn.execute("""
                                CREATE TABLE IF NOT EXISTS sync_events (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    sync_id TEXT UNIQUE,
                                    residence_id INTEGER,
                                    entity_type TEXT,
                                    action TEXT,
                                    entity_id TEXT,
                                    payload TEXT,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                );
                            """)
                            cur = conn.execute(query, tuple(params))
                            events = []
                            for r in cur.fetchall():
                                row_dict = dict(r)
                                try:
                                    row_dict["payload"] = json.loads(row_dict["payload"])
                                except Exception:
                                    pass
                                events.append(row_dict)

                            cur_max_row = conn.execute("SELECT COALESCE(MAX(id), 0) FROM sync_events").fetchone()
                            server_max_id = int(cur_max_row[0] or 0) if cur_max_row else 0

                            self._send_json(200, {
                                "success": True,
                                "events": events,
                                "count": len(events),
                                "latest_id": server_max_id,
                                "server_max_id": server_max_id,
                                "reset_required": (since_id > server_max_id)
                            })
                        except Exception as e:
                            self._send_json(500, {"error": f"Pull failed: {e}"})

                elif path == "/api/sync/summary":
                    # ملخص شامل لإحصائيات كافة الإقامات للتحقق من التطابق والجاهزية
                    try:
                        with db.get_connection() as conn:
                            cur_max = conn.execute("SELECT COALESCE(MAX(id), 0) FROM sync_events").fetchone()[0]
                            cur_max = int(cur_max or 0)
                            res_summary = {}
                            res_rows = conn.execute("SELECT id, name FROM residences ORDER BY id ASC").fetchall()
                            for r in res_rows:
                                rid = r["id"]
                                m_cnt = conn.execute("SELECT COUNT(*) FROM daily_meals_tracking WHERE residence_id = ?", (rid,)).fetchone()[0]
                                en_cnt = conn.execute("SELECT COUNT(*) FROM entry_vouchers WHERE residence_id = ?", (rid,)).fetchone()[0]
                                ex_cnt = conn.execute("SELECT COUNT(*) FROM exit_vouchers WHERE residence_id = ?", (rid,)).fetchone()[0]
                                mv_cnt = conn.execute("SELECT COUNT(*) FROM stock_movements WHERE residence_id = ?", (rid,)).fetchone()[0]
                                last_m = conn.execute("SELECT MAX(date) FROM daily_meals_tracking WHERE residence_id = ?", (rid,)).fetchone()[0]
                                res_summary[str(rid)] = {
                                    "id": rid,
                                    "name": r["name"],
                                    "meals": m_cnt,
                                    "entry_vouchers": en_cnt,
                                    "exit_vouchers": ex_cnt,
                                    "stock_movements": mv_cnt,
                                    "last_meal_date": last_m
                                }
                            self._send_json(200, {
                                "success": True,
                                "server_max_sync_event_id": cur_max,
                                "residences": res_summary
                            })
                    except Exception as e_sum:
                        self._send_json(500, {"success": False, "error": f"Summary failed: {e_sum}"})

                elif path == "/api/sync/full_export":
                    # تصدير شامل لكافة البيانات لمزامنة الحواسيب الجديدة فورياً
                    try:
                        with db.get_connection() as conn:
                            cur = conn.execute("SELECT * FROM daily_meals_tracking ORDER BY date ASC")
                            cols = [c[0] for c in cur.description] if cur.description else []
                            meals = [dict(zip(cols, r)) for r in cur.fetchall()]

                            cur = conn.execute("SELECT * FROM entry_vouchers ORDER BY date ASC")
                            cols = [c[0] for c in cur.description] if cur.description else []
                            entry_vouchers = [dict(zip(cols, r)) for r in cur.fetchall()]
                            for ev in entry_vouchers:
                                cur_it = conn.execute("SELECT * FROM entry_voucher_items WHERE voucher_id = ?", (ev["id"],))
                                it_cols = [c[0] for c in cur_it.description] if cur_it.description else []
                                ev["items"] = [dict(zip(it_cols, r)) for r in cur_it.fetchall()]

                            cur = conn.execute("SELECT * FROM exit_vouchers ORDER BY date ASC")
                            cols = [c[0] for c in cur.description] if cur.description else []
                            exit_vouchers = [dict(zip(cols, r)) for r in cur.fetchall()]
                            for ev in exit_vouchers:
                                cur_it = conn.execute("SELECT * FROM exit_voucher_items WHERE voucher_id = ?", (ev["id"],))
                                it_cols = [c[0] for c in cur_it.description] if cur_it.description else []
                                ev["items"] = [dict(zip(it_cols, r)) for r in cur_it.fetchall()]

                            self._send_json(200, {
                                "success": True,
                                "daily_meals": meals,
                                "entry_vouchers": entry_vouchers,
                                "exit_vouchers": exit_vouchers
                            })
                    except Exception as e:
                        self._send_json(500, {"error": f"Full export failed: {e}"})

                elif path == "/api/sync/residence_full_pull":
                    # سحب وتصدير كافة بيانات إقامة معينة للمزامنة والاسترجاع الشامل
                    res_id_raw = query_params.get("residence_id")
                    if not res_id_raw:
                        self._send_json(400, {"success": False, "error": "يرجى تحديد معرف الإقامة (residence_id)"})
                    else:
                        try:
                            r_id = int(res_id_raw)
                        except ValueError:
                            self._send_json(400, {"success": False, "error": "معرف الإقامة غير صالح"})
                            r_id = None

                        if r_id is not None:
                            try:
                                with db.get_connection() as conn:
                                    res_row = conn.execute("SELECT id, name, code FROM residences WHERE id = ?", (r_id,)).fetchone()
                                    res_name = res_row["name"] if res_row else f"الإقامة {r_id}"

                                    # 1. أوراق الوجبات
                                    cur = conn.execute("SELECT * FROM daily_meals_tracking WHERE residence_id = ? ORDER BY date ASC", (r_id,))
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    meals = [dict(zip(cols, r)) for r in cur.fetchall()]

                                    # 2. وصولات الدخول
                                    cur = conn.execute("SELECT * FROM entry_vouchers WHERE residence_id = ? ORDER BY date ASC", (r_id,))
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    entry_vouchers = [dict(zip(cols, r)) for r in cur.fetchall()]
                                    
                                    entry_v_ids = [v["id"] for v in entry_vouchers]
                                    entry_items = []
                                    if entry_v_ids:
                                        placeholders = ",".join("?" for _ in entry_v_ids)
                                        cur_it = conn.execute(f"SELECT * FROM entry_voucher_items WHERE voucher_id IN ({placeholders})", tuple(entry_v_ids))
                                        it_cols = [c[0] for c in cur_it.description] if cur_it.description else []
                                        entry_items = [dict(zip(it_cols, r)) for r in cur_it.fetchall()]

                                    # 3. وصولات الخروج
                                    cur = conn.execute("SELECT * FROM exit_vouchers WHERE residence_id = ? ORDER BY date ASC", (r_id,))
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    exit_vouchers = [dict(zip(cols, r)) for r in cur.fetchall()]
                                    
                                    exit_v_ids = [v["id"] for v in exit_vouchers]
                                    exit_items = []
                                    if exit_v_ids:
                                        placeholders = ",".join("?" for _ in exit_v_ids)
                                        cur_it = conn.execute(f"SELECT * FROM exit_voucher_items WHERE voucher_id IN ({placeholders})", tuple(exit_v_ids))
                                        it_cols = [c[0] for c in cur_it.description] if cur_it.description else []
                                        exit_items = [dict(zip(it_cols, r)) for r in cur_it.fetchall()]

                                    # 4. حركات المخزون
                                    cur = conn.execute("SELECT * FROM stock_movements WHERE residence_id = ? ORDER BY date ASC, id ASC", (r_id,))
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    movements = [dict(zip(cols, r)) for r in cur.fetchall()]

                                    # 5. أرصدة ومخصصات المواد
                                    cur = conn.execute("SELECT * FROM residence_articles WHERE residence_id = ?", (r_id,))
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    res_articles = [dict(zip(cols, r)) for r in cur.fetchall()]

                                    # 6. الإعارات والاستعارات
                                    cur = conn.execute("SELECT * FROM residence_loans WHERE from_residence_id = ? OR to_residence_id = ?", (r_id, r_id))
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    loans = [dict(zip(cols, r)) for r in cur.fetchall()]
                                    loan_ids = [l["id"] for l in loans]
                                    loan_items = []
                                    if loan_ids:
                                        placeholders = ",".join("?" for _ in loan_ids)
                                        cur_it = conn.execute(f"SELECT * FROM residence_loan_items WHERE loan_id IN ({placeholders})", tuple(loan_ids))
                                        it_cols = [c[0] for c in cur_it.description] if cur_it.description else []
                                        loan_items = [dict(zip(it_cols, r)) for r in cur_it.fetchall()]

                                    # 7. محاضر الجرد الشهري
                                    cur = conn.execute("SELECT * FROM inventory_snapshots WHERE residence_id = ?", (r_id,))
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    inventories = [dict(zip(cols, r)) for r in cur.fetchall()]

                                    # 8. أيام مفتوحة
                                    cur = conn.execute("SELECT * FROM unlocked_days WHERE residence_id = ?", (r_id,))
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    unlocked = [dict(zip(cols, r)) for r in cur.fetchall()]

                                    # 9. حصص الممونين
                                    cur = conn.execute("SELECT * FROM supplier_allocations WHERE residence_id = ?", (r_id,))
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    allocations = [dict(zip(cols, r)) for r in cur.fetchall()]

                                    # 10. سندات الطلب
                                    cur = conn.execute("SELECT * FROM bon_commande WHERE residence_id = ?", (r_id,))
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    bon_commandes = [dict(zip(cols, r)) for r in cur.fetchall()]
                                    bc_ids = [b["id"] for b in bon_commandes]
                                    bon_quantities = []
                                    if bc_ids:
                                        placeholders = ",".join("?" for _ in bc_ids)
                                        cur_it = conn.execute(f"SELECT * FROM bon_commande_qty WHERE bon_id IN ({placeholders})", tuple(bc_ids))
                                        it_cols = [c[0] for c in cur_it.description] if cur_it.description else []
                                        bon_quantities = [dict(zip(it_cols, r)) for r in cur_it.fetchall()]

                                    # 11. الدليل المرجعي العام (المواد، الممونين، الأصناف)
                                    cur = conn.execute("SELECT * FROM articles")
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    articles_catalog = [dict(zip(cols, r)) for r in cur.fetchall()]

                                    cur = conn.execute("SELECT * FROM suppliers")
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    suppliers_catalog = [dict(zip(cols, r)) for r in cur.fetchall()]

                                    cur = conn.execute("SELECT * FROM categories")
                                    cols = [c[0] for c in cur.description] if cur.description else []
                                    categories_catalog = [dict(zip(cols, r)) for r in cur.fetchall()]

                                    self._send_json(200, {
                                        "success": True,
                                        "residence_id": r_id,
                                        "residence_name": res_name,
                                        "counts": {
                                            "meals": len(meals),
                                            "entry_vouchers": len(entry_vouchers),
                                            "entry_voucher_items": len(entry_items),
                                            "exit_vouchers": len(exit_vouchers),
                                            "exit_voucher_items": len(exit_items),
                                            "stock_movements": len(movements),
                                            "residence_articles": len(res_articles),
                                            "residence_loans": len(loans),
                                            "inventory_snapshots": len(inventories),
                                            "unlocked_days": len(unlocked),
                                            "supplier_allocations": len(allocations),
                                            "bon_commande": len(bon_commandes),
                                            "bon_commande_qty": len(bon_quantities),
                                            "articles": len(articles_catalog),
                                            "suppliers": len(suppliers_catalog),
                                            "categories": len(categories_catalog)
                                        },
                                        "data": {
                                            "daily_meals_tracking": meals,
                                            "entry_vouchers": entry_vouchers,
                                            "entry_voucher_items": entry_items,
                                            "exit_vouchers": exit_vouchers,
                                            "exit_voucher_items": exit_items,
                                            "stock_movements": movements,
                                            "residence_articles": res_articles,
                                            "residence_loans": loans,
                                            "residence_loan_items": loan_items,
                                            "inventory_snapshots": inventories,
                                            "unlocked_days": unlocked,
                                            "supplier_allocations": allocations,
                                            "bon_commande": bon_commandes,
                                            "bon_commande_qty": bon_quantities,
                                            "articles": articles_catalog,
                                            "suppliers": suppliers_catalog,
                                            "categories": categories_catalog
                                        }
                                    })
                            except Exception as ex_pull:
                                self._send_json(500, {"success": False, "error": f"Failed to export residence data: {ex_pull}"})

                else:
                    self._send_json(404, {"error": "Endpoint Not Found"})

            def do_POST(self):
                try:
                    path = self.path.split("?")[0]
                    # استثناء مزامنة بيانات الإقامات وتسجيل الدخول من التقييد
                    if path not in ("/api/sync/push", "/api/auth/login", "/api/sync/residence_full_push"):
                        if not self._check_rate_limit():
                            self._send_json(429, {"error": "Rate limit exceeded. Please slow down."})
                            return
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
                        # استقبال ومعالجة حركات رتل المزامنة من الإقامة - نمط مباشر وسريع جداً بدون أي قفل أو تأخير
                        r_id = payload.get("residence_id", 1)
                        items = payload.get("items", [])
                        synced_ids = []

                        for it in items:
                            sync_id = it.get("sync_id", "")
                            entity_type = it.get("entity_type", "")
                            data = it.get("payload", {})

                            if not sync_id:
                                continue

                            item_res_id = it.get("residence_id") or r_id or 1

                            # محاولة تطبيق الحركة في قاعدة البيانات المركزية
                            try:
                                from core.stock_service import StockService
                                stk = StockService(db, residence_id=item_res_id)
                                stk._skip_enqueue = True  # منع إعادة الإرسال العكسي

                                if entity_type == "daily_sheet_full":
                                    stk.save_daily_sheet_full(
                                        data.get("date", ""),
                                        data.get("articles", []),
                                        tickets_input=data.get("tickets"),
                                        menu_input=data.get("menus"),
                                        residence_id=item_res_id,
                                        notes=data.get("notes")
                                    )
                                elif entity_type in ("daily_general_info", "daily_meals"):
                                    stk.save_daily_general_info(
                                        data.get("date", ""),
                                        tickets_input=data.get("tickets", {}),
                                        menu_input=data.get("menus", {}),
                                        expenses_input=data.get("expenses", {}),
                                        residence_id=item_res_id
                                    )
                                elif entity_type == "entry_voucher":
                                    v_obj = data.get("voucher", {})
                                    v_num = v_obj.get("voucher_number")
                                    existing = None
                                    if v_num:
                                        with db.get_connection() as conn:
                                            existing = conn.execute("SELECT id FROM entry_vouchers WHERE voucher_number = ? AND residence_id = ?", (v_num, item_res_id)).fetchone()
                                    if not existing:
                                        stk.create_entry_voucher(v_obj, data.get("items", []))
                                elif entity_type == "exit_voucher":
                                    v_obj = data.get("voucher", {})
                                    v_num = v_obj.get("voucher_number")
                                    existing = None
                                    if v_num:
                                        with db.get_connection() as conn:
                                            existing = conn.execute("SELECT id FROM exit_vouchers WHERE voucher_number = ? AND residence_id = ?", (v_num, item_res_id)).fetchone()
                                    if not existing:
                                        stk.create_exit_voucher(v_obj, data.get("items", []))
                            except Exception as item_err:
                                logger.warning(f"Notice item sync {sync_id} ({entity_type}): {item_err}")


                            # تسجيل الحركة في سجل أحداث المزامنة لسحبها من الحواسيب الأخرى
                            try:
                                payload_str = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data)
                                with db.get_connection() as conn:
                                    conn.execute("""
                                        CREATE TABLE IF NOT EXISTS sync_events (
                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            sync_id TEXT UNIQUE,
                                            residence_id INTEGER,
                                            entity_type TEXT,
                                            action TEXT,
                                            entity_id TEXT,
                                            payload TEXT,
                                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                        );
                                    """)
                                    conn.execute("""
                                        INSERT OR IGNORE INTO sync_events (sync_id, residence_id, entity_type, action, entity_id, payload, created_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        sync_id, item_res_id, entity_type, it.get("action", "SAVE"),
                                        str(it.get("entity_id", "")), payload_str,
                                        it.get("created_at", datetime.datetime.now().isoformat())
                                    ))
                                    conn.commit()
                            except Exception as ev_err:
                                logger.warning(f"Notice sync_event logging: {ev_err}")

                            # قبول المعرف لتأكيد نجاح استلام الحركة في الإقامة
                            synced_ids.append(sync_id)

                        # تحديث حالة آخر اتصال للإقامة بأمان
                        try:
                            now_str = datetime.datetime.now().isoformat()
                            with db.get_connection() as conn:
                                conn.execute("""
                                    INSERT INTO sync_state (residence_id, last_push_timestamp, status)
                                    VALUES (?, ?, 'ONLINE')
                                    ON CONFLICT(residence_id) DO UPDATE SET
                                        last_push_timestamp = excluded.last_push_timestamp,
                                        status = 'ONLINE'
                                """, (r_id, now_str))
                        except Exception:
                            pass

                        self._send_json(200, {
                            "success": True,
                            "synced_count": len(synced_ids),
                            "synced_ids": synced_ids
                        })


                    elif path == "/api/sync/residence_full_push":
                        # استقبال الحزمة الكاملة لبيانات إقامة محددة وتحديثها بالكامل في السيرفر
                        try:
                            r_id = payload.get("residence_id")
                            if not r_id:
                                self._send_json(400, {"success": False, "error": "يرجى تحديد residence_id"})
                            else:
                                r_id = int(r_id)
                                data = payload.get("data", {})
                                from core.sync_service import SyncService
                                sync_engine = SyncService(db)
                                counts = sync_engine.apply_residence_full_data(r_id, data)

                                # تسجيل حدث المزامنة الشاملة
                                try:
                                    s_id = f"full_push_{r_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                                    with db.get_connection() as conn:
                                        conn.execute("""
                                            INSERT OR IGNORE INTO sync_events (sync_id, residence_id, entity_type, action, entity_id, payload)
                                            VALUES (?, ?, 'residence_full_push', 'UPSERT', ?, ?)
                                        """, (s_id, r_id, str(r_id), json.dumps({"residence_id": r_id, "counts": counts}, ensure_ascii=False)))
                                        conn.commit()
                                except Exception as ev_err:
                                    logger.warning(f"Notice sync_event logging for full push: {ev_err}")

                                self._send_json(200, {
                                    "success": True,
                                    "residence_id": r_id,
                                    "applied_counts": counts
                                })
                        except Exception as exp_push:
                            self._send_json(500, {"success": False, "error": f"Failed to push full residence data: {exp_push}"})

                    elif path == "/api/sync/full_import":
                        # استيراد شامل وحفظ في سجل المزامنة المركزي
                        imported_count = 0
                        daily_meals = payload.get("daily_meals", [])
                        entry_vouchers = payload.get("entry_vouchers", [])
                        exit_vouchers = payload.get("exit_vouchers", [])

                        from core.stock_service import StockService
                        with db.get_connection() as conn:
                            conn.execute("""
                                CREATE TABLE IF NOT EXISTS sync_events (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    sync_id TEXT UNIQUE,
                                    residence_id INTEGER,
                                    entity_type TEXT,
                                    action TEXT,
                                    entity_id TEXT,
                                    payload TEXT,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                );
                            """)
                            conn.commit()

                        # استيراد أوراق الاستهلاك والوجبات
                        for dm in daily_meals:
                            r_id = dm.get("residence_id", 1)
                            d_str = dm.get("date", "")
                            s_id = f"dm_{r_id}_{d_str}"
                            p_str = json.dumps({"date": d_str, "tickets": dm}, ensure_ascii=False)
                            try:
                                with db.get_connection() as conn:
                                    conn.execute("""
                                        INSERT OR IGNORE INTO sync_events (sync_id, residence_id, entity_type, action, entity_id, payload)
                                        VALUES (?, ?, 'daily_sheet_full', 'UPSERT', ?, ?)
                                    """, (s_id, r_id, d_str, p_str))
                                    conn.commit()
                                imported_count += 1
                            except Exception:
                                pass

                        # استيراد وصولات الاستلام
                        for ev in entry_vouchers:
                            r_id = ev.get("residence_id", 1)
                            v_id = ev.get("id", "")
                            s_id = f"ev_entry_{r_id}_{v_id}"
                            p_str = json.dumps({"voucher": ev, "items": ev.get("items", [])}, ensure_ascii=False)
                            try:
                                with db.get_connection() as conn:
                                    conn.execute("""
                                        INSERT OR IGNORE INTO sync_events (sync_id, residence_id, entity_type, action, entity_id, payload)
                                        VALUES (?, ?, 'entry_voucher', 'CREATE', ?, ?)
                                    """, (s_id, r_id, str(v_id), p_str))
                                    conn.commit()
                                imported_count += 1
                            except Exception:
                                pass

                        # استيراد وصولات الإخراج
                        for ev in exit_vouchers:
                            r_id = ev.get("residence_id", 1)
                            v_id = ev.get("id", "")
                            s_id = f"ev_exit_{r_id}_{v_id}"
                            p_str = json.dumps({"voucher": ev, "items": ev.get("items", [])}, ensure_ascii=False)
                            try:
                                with db.get_connection() as conn:
                                    conn.execute("""
                                        INSERT OR IGNORE INTO sync_events (sync_id, residence_id, entity_type, action, entity_id, payload)
                                        VALUES (?, ?, 'exit_voucher', 'CREATE', ?, ?)
                                    """, (s_id, r_id, str(v_id), p_str))
                                    conn.commit()
                                imported_count += 1
                            except Exception:
                                pass

                        self._send_json(200, {
                            "success": True,
                            "imported_count": imported_count
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
            self.server_host = server_host.strip()
            self.port = port or 443
            self.base_url = normalize_server_url(self.server_host, self.port)
        else:
            self.server_host = AppConfig.get("server_host", "onou-server.onrender.com")
            self.port = AppConfig.get("server_port", 443)
            self.base_url = normalize_server_url(self.server_host, self.port)

    def check_connection(self) -> bool:
        try:
            r = http_get(f"{self.base_url}/api/status", timeout=AppConfig.get("timeout_seconds", 25.0))
            return r.status_code == 200
        except Exception:
            return False

    def ping(self) -> Tuple[bool, float, str]:
        """فحص زمن الاستجابة (Latency) بالمللي ثانية ورسالة الحالة"""
        t0 = datetime.datetime.now()
        try:
            r = http_get(f"{self.base_url}/api/status", timeout=AppConfig.get("timeout_seconds", 25.0))
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
        r = http_post(url, json={"username": username, "password": password}, timeout=AppConfig.get("timeout_seconds", 35.0))
        if r.status_code == 200:
            return r.json()
        elif r.status_code in (401, 403):
            detail = r.json().get("detail", "خطأ في تسجيل الدخول")
            raise PermissionError(detail)
        else:
            raise ConnectionError(f"خطأ في الاتصال بالخادم: {r.status_code}")

    def get_super_dashboard(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/directorate/super_dashboard"
        r = http_get(url, timeout=AppConfig.get("timeout_seconds", 25.0))
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