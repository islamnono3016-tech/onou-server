#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خادم الربط السحابي المركزي - مديرية الخدمات الجامعية
ONOU Central Cloud & Mesh Sync Server (Python 3.8+)

يمكن تشغيل هذا الخادم على:
1. جهاز حاسوب في المديرية متصل بشبكة Tailscale Mesh VPN (مجاني ومباشر بدون IP ثابت).
2. جهاز حاسوب في المديرية عبر Cloudflare Tunnel (رابط https عالمي فوري).
3. سيرفر سحابي مستقل (Cloud VPS - Ubuntu/Debian/Windows).

الاستخدام:
    python tools/cloud_server.py --port 8050 --db data/catering_stock.db
"""

import os
import sys
import time
import signal
import logging
import argparse
import datetime
from pathlib import Path

# إضافة المجلد الرئيسي للمشروع إلى مسارات بايثون
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db_manager import DatabaseManager
from core.network_service import NetworkServer, get_local_ip
from core.config import AppConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / "cloud_server.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("CloudServer")

BANNER = """
================================================================================
   الجمهورية الجزائرية الديمقراطية الشعبية - وزارة التعليم العالي والبحث العلمي
             الديوان الوطني للخدمات الجامعية - ONOU 2026
        خادم المزامنة والربط السحابي المركزي (Central Cloud Server)
================================================================================
"""

def print_dashboard(host: str, port: int, db_path: str, local_ip: str):
    print(BANNER)
    print(f"  [+] حالة الخادم:          متصل ويعمل بنجاح (ONLINE)")
    print(f"  [+] العنوان المحلي:        http://{local_ip}:{port}")
    print(f"  [+] منفذ الاستماع:         {port} (على جميع الواجهات 0.0.0.0)")
    print(f"  [+] قاعدة البيانات:        {db_path}")
    print(f"  [+] وقت بدء التشغيل:       {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    print("  [✓] نقاط النهاية البرمجية النشطة (Active REST Endpoints):")
    print(f"      - فحص الحالة:         GET  http://localhost:{port}/api/status")
    print(f"      - دليل المواد:        GET  http://localhost:{port}/api/sync/catalog?residence_id=X")
    print(f"      - رتل المزامنة:       POST http://localhost:{port}/api/sync/push")
    print(f"      - قائمة الإقامات:     GET  http://localhost:{port}/api/residences")
    print(f"      - إحصائيات المخزون:   GET  http://localhost:{port}/api/directorate/super_dashboard")
    print("-" * 80)
    print("  [*] خيارات الربط عبر الإنترنت للإقامات (Remote Connection Options):")
    print("      1. شبكة Tailscale VPN: استخدم عنوان الـ IP المخصص للحاسوب (مثال: 100.x.y.z:8050)")
    print("      2. نفق Cloudflare Tunnel: استخدم الدومين العام (مثال: https://stock.onou-dou.dz)")
    print("      3. خادم VPS مباشر:      استخدم IP السيرفر الثابت (مثال: http://194.x.y.z:8050)")
    print("=" * 80)
    print("  [i] اضغط Ctrl + C لإيقاف الخادم بأمان في أي وقت.\n")

def main():
    default_port = int(os.environ.get("PORT", 8050))
    default_db = os.environ.get("DB_PATH", str(BASE_DIR / "data" / "catering_stock.db"))

    parser = argparse.ArgumentParser(description="ONOU Central Cloud & Sync Server")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port to listen on (default: {default_port})")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind to")
    parser.add_argument("--db", type=str, default=default_db, help="Path to SQLite database")
    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db_manager = DatabaseManager(db_path=db_path)

    # تشغيل الخادم المركزي
    server = NetworkServer(port=args.port, db_manager=db_manager)
    server.start()

    local_ip = get_local_ip()
    print_dashboard(args.host, args.port, db_path, local_ip)

    # معالجة إشارات الإيقاف بسلاسة
    running = True

    def signal_handler(sig, frame):
        nonlocal running
        print("\n\n  [!] جاري إيقاف الخادم السحابي بأمان...")
        running = False
        server.stop()
        print("  [✓] تم إيقاف الخادم بنجاح. مع السلامة!")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    try:
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception:
        pass

    while running:
        time.sleep(1)

if __name__ == "__main__":
    main()
