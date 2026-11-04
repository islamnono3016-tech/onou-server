try:
    from core.time_service import TimeService
except Exception:
    TimeService = None
import uuid
import json
import logging
import datetime
from typing import Optional, Dict, Any, List, Tuple
import requests

from PyQt6.QtCore import QThread, pyqtSignal, QMutex

from database.db_manager import DatabaseManager
from core.config import AppConfig
from core.network_service import http_get, http_post

logger = logging.getLogger(__name__)

class SyncService:
    """
    محرك المزامنة والاستقلالية التامة عند انقطاع الشبكة (Offline-First Sync Engine)
    يحفظ كل الحركات محلياً في رتل المزامنة (Outbox Pattern)، ويتيح العمل الميداني المستمر
    وعند استعادة الاتصال بالمديرية تتم المزامنة آلياً في الخلفية (Background Auto-sync).
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()

    def enqueue(self, residence_id: int, entity_type: str, action: str,
                entity_id: str, payload: Dict[str, Any]) -> str:
        """
        إضافة حركة إلى رتل المزامنة محلياً عند تسجيلها
        """
        sync_id = str(uuid.uuid4())
        payload_str = json.dumps(payload, ensure_ascii=False)

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO sync_queue (sync_id, residence_id, entity_type, action, entity_id, payload, status)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
            """, (sync_id, residence_id, entity_type, action, str(entity_id), payload_str))
            conn.commit()

        logger.info(f"Enqueued sync action {action} on {entity_type} (ID: {entity_id}) for residence {residence_id}")
        return sync_id

    def get_pending_count(self, residence_id: Optional[int] = None) -> int:
        """عدد الحركات المعلقة في رتل المزامنة"""
        query = "SELECT COUNT(*) FROM sync_queue WHERE status IN ('PENDING', 'FAILED') AND retry_count < 30"
        params = []
        if residence_id:
            query += " AND residence_id = ?"
            params.append(residence_id)

        with self.db.get_connection() as conn:
            cur = conn.execute(query, tuple(params))
            return cur.fetchone()[0]

    def get_pending_items(self, residence_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """جلب الحركات المعلقة بالترتيب الزمني للإرسال"""
        query = "SELECT * FROM sync_queue WHERE status IN ('PENDING', 'FAILED') AND retry_count < 30"
        params = []
        if residence_id:
            query += " AND residence_id = ?"
            params.append(residence_id)
        query += " ORDER BY id ASC LIMIT ?"
        params.append(limit)

        with self.db.get_connection() as conn:
            cur = conn.execute(query, tuple(params))
            items = []
            for r in cur.fetchall():
                it = dict(r)
                try:
                    it["payload"] = json.loads(it["payload"])
                except Exception:
                    pass
                items.append(it)
            return items

    def mark_synced(self, sync_ids: List[str]) -> None:
        """تحديث حالة الحركات الناجحة إلى منتهية"""
        if not sync_ids:
            return
        now_str = TimeService.iso_now() if TimeService else datetime.datetime.now().isoformat()
        placeholders = ",".join("?" for _ in sync_ids)
        with self.db.get_connection() as conn:
            conn.execute(f"""
                UPDATE sync_queue
                SET status = 'SYNCED', synced_at = ?
                WHERE sync_id IN ({placeholders})
            """, [now_str] + sync_ids)
            conn.commit()

    def mark_failed(self, sync_id: str, error_msg: str) -> None:
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE sync_queue
                SET status = 'FAILED', retry_count = retry_count + 1, error_message = ?
                WHERE sync_id = ?
            """, (error_msg, sync_id))
            conn.commit()

    def reset_failed_queue(self, residence_id: Optional[int] = None) -> int:
        """إعادة الحركات المتعثرة تلقائياً إلى رتل الإرسال النشط عند توفر الاتصال"""
        query = "UPDATE sync_queue SET status = 'PENDING' WHERE status = 'FAILED' AND retry_count < 30"
        params = []
        if residence_id:
            query += " AND residence_id = ?"
            params.append(residence_id)
        with self.db.get_connection() as conn:
            cur = conn.execute(query, tuple(params))
            conn.commit()
            return cur.rowcount

    def is_server_reachable(self, base_url: Optional[str] = None) -> bool:
        """فحص سريع لحالة توفر سيرفر المديرية عبر الشبكة"""
        url = base_url or AppConfig.get_server_url()
        try:
            r = http_get(f"{url}/api/status", timeout=AppConfig.get("timeout_seconds", 25.0))
            # الأكواد 200 تعني اتصال سليم، و 429 تعني أن السيرفر متصل وشغال ولكنه يطلب التهدئة
            return r.status_code in (200, 429)
        except Exception:
            return False

    def push_pending(self, residence_id: Optional[int] = None, base_url: Optional[str] = None) -> Tuple[int, int]:
        """
        إرسال الحركات المعلقة دفعة واحدة إلى سيرفر المديرية
        تجميع الحركات حسب الإقامة لضمان حفظ كل حركة تحت إقامتها الصحيحة وتوزيعها فورياً لباقي الأجهزة
        """
        url = base_url or AppConfig.get_server_url()
        pending = self.get_pending_items(residence_id, limit=100)
        if not pending:
            return (0, 0)

        push_endpoint = f"{url}/api/sync/push"

        from collections import defaultdict
        grouped = defaultdict(list)
        for it in pending:
            r_id = it.get("residence_id") or residence_id or 1
            it["residence_id"] = r_id
            grouped[r_id].append(it)

        total_synced = 0
        for r_id, items_group in grouped.items():
            payload = {
                "residence_id": r_id,
                "items": items_group
            }
            try:
                r = http_post(push_endpoint, json=payload, timeout=AppConfig.get("timeout_seconds", 35.0))
                if r.status_code == 200:
                    resp_data = r.json()
                    synced_ids = resp_data.get("synced_ids", [item["sync_id"] for item in items_group])
                    self.mark_synced(synced_ids)
                    total_synced += len(synced_ids)
                    logger.info(f"Successfully pushed {len(synced_ids)} items for residence {r_id} to central server")
                elif r.status_code == 429:
                    logger.warning(f"Server rate limit (429) for residence {r_id}; will retry next cycle without marking failed.")
                    # لا نعلّمها كـ FAILED بل نتركها لتُرسل في الدورة القادمة
                    break
                else:
                    err_msg = f"Server returned status {r.status_code}: {r.text}"
                    for it in items_group:
                        self.mark_failed(it["sync_id"], err_msg)
            except Exception as e:
                logger.warning(f"Failed to push sync items for residence {r_id} (Offline Mode): {e}")

        return (total_synced, self.get_pending_count(residence_id))

    def pull_updates(self, residence_id: Optional[int] = None, base_url: Optional[str] = None, is_directorate: bool = False) -> int:
        """
        سحب الحركات المسجلة من الإقامات - مخصص حصرياً للمديرية المركزية فقط.
        الإقامات لا تسحب أي بيانات من أي جهة أخرى نهائياً لضمان الاستقلالية التامة وحماية مدخلاتها.
        """
        from core.config import AppConfig

        # سحب وتحديث البيانات متاح لكافة حواسيب ومكاتب المديرية المركزية
        cfg_mode = AppConfig.get("app_mode", "")
        cfg_res_id = AppConfig.get("residence_id")

        is_true_directorate = is_directorate or getattr(self, "is_directorate", False) or (cfg_mode == "DIRECTORATE_SERVER")

        if not is_true_directorate:
            if AppConfig.is_client_mode() or cfg_mode == "RESIDENCE_CLIENT":
                logger.info("🚫 سحب البيانات محظور: هذا الجهاز حاسوب إقامة ولا يسحب أي بيانات من الخارج.")
                return 0

            if cfg_res_id and int(cfg_res_id) > 0:
                logger.info(f"🚫 سحب البيانات محظور: هذا الجهاز مرتبط بالإقامة {cfg_res_id} ولا يسحب أي بيانات.")
                return 0

            logger.info("🚫 سحب البيانات محظور: السحب متاح لمركز قيادة المديرية المركزية فقط.")
            return 0
        url = base_url or AppConfig.get_server_url()
        last_id = int(self.db.get_setting("last_pulled_sync_event_id", "0") or "0")

        # فحص استكشافي ذكي (Active Probe) لكشف ما إذا كان مؤشر الجهاز يسبق الخادم المركزي أو إذا تمت إعادة تشغيل الخادم
        if last_id > 0:
            try:
                r_probe = http_get(f"{url}/api/sync/pull?since_id=0&limit=1", timeout=8.0)
                if r_probe.status_code == 200:
                    probe_data = r_probe.json()
                    server_true_max = int(probe_data.get("latest_id", 0) or 0)
                    if last_id > server_true_max:
                        logger.info(f"Local sync pointer ({last_id}) is ahead of server true max ({server_true_max}). Auto-resetting pointer to 0.")
                        self.db.set_setting("last_pulled_sync_event_id", "0")
                        last_id = 0
            except Exception as e_pr:
                logger.debug(f"Probe notice: {e_pr}")

        endpoint = f"{url}/api/sync/pull?since_id={last_id}&limit=200"
        if residence_id:
            endpoint += f"&residence_id={residence_id}"

        try:
            r = http_get(endpoint, timeout=AppConfig.get("timeout_seconds", 25.0))
            if r.status_code != 200:
                return 0
            data = r.json()
            latest_on_server = int(data.get("latest_id", 0) or 0)
            reset_req = data.get("reset_required", False)
            if reset_req or (last_id > latest_on_server):
                logger.info(f"Sync event pointer reset (local={last_id}, server={latest_on_server}, reset_req={reset_req}). Resetting to 0.")
                self.db.set_setting("last_pulled_sync_event_id", "0")
                return self.pull_updates(residence_id, base_url, is_directorate=is_directorate)

            events = data.get("events", [])
            if not events:
                return 0

            applied_count = 0
            from core.stock_service import StockService
            for ev in events:
                try:
                    r_id = ev.get("residence_id") or residence_id or 1
                    stk = StockService(self.db, residence_id=r_id)
                    stk._skip_enqueue = True  # منع إعادة الإرسال العكسي

                    entity_type = ev.get("entity_type", "")
                    payload = ev.get("payload", {})
                    if isinstance(payload, str):
                        try:
                            payload = json.loads(payload)
                        except Exception:
                            payload = {}

                    if entity_type == "daily_sheet_full":
                        stk.save_daily_sheet_full(
                            payload.get("date", ""),
                            payload.get("articles", []),
                            tickets_input=payload.get("tickets"),
                            menu_input=payload.get("menus"),
                            residence_id=r_id,
                            notes=payload.get("notes")
                        )
                        applied_count += 1
                    elif entity_type in ("daily_general_info", "daily_meals"):
                        stk.save_daily_general_info(
                            payload.get("date", ""),
                            tickets_input=payload.get("tickets", {}),
                            menu_input=payload.get("menus", {}),
                            expenses_input=payload.get("expenses", {}),
                            residence_id=r_id
                        )
                        applied_count += 1
                    elif entity_type == "entry_voucher":
                        v_obj = payload.get("voucher", {})
                        v_num = v_obj.get("voucher_number")
                        existing = None
                        if v_num:
                            with self.db.get_connection() as conn:
                                existing = conn.execute("SELECT id FROM entry_vouchers WHERE voucher_number = ? AND residence_id = ?", (v_num, r_id)).fetchone()
                        if not existing:
                            stk.create_entry_voucher(v_obj, payload.get("items", []))
                        applied_count += 1
                    elif entity_type == "exit_voucher":
                        v_obj = payload.get("voucher", {})
                        v_num = v_obj.get("voucher_number")
                        existing = None
                        if v_num:
                            with self.db.get_connection() as conn:
                                existing = conn.execute("SELECT id FROM exit_vouchers WHERE voucher_number = ? AND residence_id = ?", (v_num, r_id)).fetchone()
                        if not existing:
                            stk.create_exit_voucher(v_obj, payload.get("items", []))
                        applied_count += 1
                    elif entity_type == "residence_full_push":
                        # حدث رفع حزمة شاملة من إقامة: سحب وتطبيق حزمة الإقامة المعنية فوراً
                        self.pull_full_residence_data(r_id, base_url=url)
                        applied_count += 1
                except Exception as ev_err:
                    logger.warning(f"Error applying pulled sync event {ev.get('id')}: {ev_err}")

            latest_id = data.get("latest_id", last_id)
            self.db.set_setting("last_pulled_sync_event_id", str(latest_id))
            if applied_count > 0:
                try:
                    from core.cache_service import CacheService
                    CacheService.invalidate_all()
                except Exception:
                    pass
            logger.info(f"Pulled and applied {applied_count} sync events (latest ID: {latest_id})")
            return applied_count
        except Exception as e:
            logger.warning(f"Failed to pull sync updates: {e}")
            return 0

    def pull_server_catalog(self, residence_id: int, base_url: Optional[str] = None, is_directorate: bool = False) -> int:
        """سحب دليل المواد والأسعار - محظور على الإقامات لحماية بياناتها"""
        logger.info("🚫 سحب الدليل معطل: الإقامات لا تسحب أي بيانات من الخارج.")
        return 0
    def _orig_pull_server_catalog(self, residence_id: int, base_url: Optional[str] = None) -> int:
        url = base_url or AppConfig.get_server_url()
        try:
            r = http_get(f"{url}/api/sync/catalog?residence_id={residence_id}", timeout=AppConfig.get("timeout_seconds", 25.0))
            if r.status_code == 200:
                data = r.json()
                articles = data.get("articles", [])
                if not articles:
                    return 0

                with self.db.get_connection() as conn:
                    for a in articles:
                        conn.execute("""
                            UPDATE articles SET
                                name = ?, unit = ?, price_ht = ?, discount_rate = ?,
                                discount_amount = ?, price_after_discount = ?,
                                tva_rate = ?, price_ttc = ?, safety_stock = ?
                            WHERE id = ?
                        """, (
                            a["name"], a["unit"], a.get("price_ht", 0.0), a.get("discount_rate", 0.0),
                            a.get("discount_amount", 0.0), a.get("price_after_discount", 0.0),
                            a.get("tva_rate", 0.0), a["price_ttc"], a.get("safety_stock", 10.0),
                            a["id"]
                        ))
                    conn.commit()
                return len(articles)
            return 0
        except Exception as e:
            logger.warning(f"Notice pull catalog: {e}")
            return 0

    def apply_residence_full_data(self, residence_id: int, data: Dict[str, Any]) -> Dict[str, int]:
        """
        تطبيق وحفظ الحزمة الكاملة لبيانات إقامة محددة حصراً داخل قاعدة البيانات المحلية.
        يضمن العزل التام: لا يمس أي إقامة أخرى إطلاقاً!
        """
        with self.db.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = OFF;")
            try:
                # 1. تنظيف بيانات هذه الإقامة حصراً
                conn.execute("DELETE FROM entry_voucher_items WHERE voucher_id IN (SELECT id FROM entry_vouchers WHERE residence_id = ?)", (residence_id,))
                conn.execute("DELETE FROM entry_vouchers WHERE residence_id = ?", (residence_id,))
                conn.execute("DELETE FROM exit_voucher_items WHERE voucher_id IN (SELECT id FROM exit_vouchers WHERE residence_id = ?)", (residence_id,))
                conn.execute("DELETE FROM exit_vouchers WHERE residence_id = ?", (residence_id,))
                conn.execute("DELETE FROM stock_movements WHERE residence_id = ?", (residence_id,))
                conn.execute("DELETE FROM daily_meals_tracking WHERE residence_id = ?", (residence_id,))
                conn.execute("DELETE FROM residence_articles WHERE residence_id = ?", (residence_id,))
                conn.execute("DELETE FROM residence_loan_items WHERE loan_id IN (SELECT id FROM residence_loans WHERE from_residence_id = ? OR to_residence_id = ?)", (residence_id, residence_id))
                conn.execute("DELETE FROM residence_loans WHERE from_residence_id = ? OR to_residence_id = ?", (residence_id, residence_id))
                conn.execute("DELETE FROM inventory_snapshots WHERE residence_id = ?", (residence_id,))
                conn.execute("DELETE FROM unlocked_days WHERE residence_id = ?", (residence_id,))
                conn.execute("DELETE FROM supplier_allocations WHERE residence_id = ?", (residence_id,))
                conn.execute("DELETE FROM bon_commande_qty WHERE bon_id IN (SELECT id FROM bon_commande WHERE residence_id = ?)", (residence_id,))
                conn.execute("DELETE FROM bon_commande WHERE residence_id = ?", (residence_id,))
    
                counts = {}
    
                # 2. إدراج القوائم المرجعية العامة إن وجدت (فئات، ممونين، مواد)
                for tbl in ["categories", "suppliers", "articles"]:
                    rows = data.get(tbl, [])
                    if rows:
                        cols = list(rows[0].keys())
                        placeholders = ",".join("?" for _ in cols)
                        sql = f"INSERT OR REPLACE INTO {tbl} ({','.join(cols)}) VALUES ({placeholders})"
                        val_list = [tuple(r.get(c) for c in cols) for r in rows]
                        conn.executemany(sql, val_list)
                        counts[tbl] = len(rows)
    
                # 3. إدراج بيانات الإقامة المعنية
                tbl_order = [
                    "daily_meals_tracking",
                    "entry_vouchers",
                    "entry_voucher_items",
                    "exit_vouchers",
                    "exit_voucher_items",
                    "stock_movements",
                    "residence_articles",
                    "residence_loans",
                    "residence_loan_items",
                    "inventory_snapshots",
                    "unlocked_days",
                    "supplier_allocations",
                    "bon_commande",
                    "bon_commande_qty"
                ]
    
                for tbl in tbl_order:
                    rows = data.get(tbl, [])
                    if rows:
                        cols = list(rows[0].keys())
                        placeholders = ",".join("?" for _ in cols)
                        sql = f"INSERT OR REPLACE INTO {tbl} ({','.join(cols)}) VALUES ({placeholders})"
                        val_list = [tuple(r.get(c) for c in cols) for r in rows]
                        conn.executemany(sql, val_list)
                        counts[tbl] = len(rows)
                    else:
                        counts[tbl] = 0
    
                # 4. تفريغ رتل المزامنة المعلق للإقامة لمنع إعادة رفع حركات قديمة
                conn.execute("DELETE FROM sync_queue WHERE residence_id = ?", (residence_id,))
                conn.commit()
            finally:
                try:
                    conn.execute("PRAGMA foreign_keys = ON;")
                except Exception:
                    pass

        try:
            from core.cache_service import CacheService
            CacheService.invalidate_all()
        except Exception:
            pass

        return counts

    def pull_full_residence_data(self, residence_id: int, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        طلب وسحب الحزمة الكاملة لبيانات إقامة محددة من سيرفر المديرية عبر الشبكة،
        ثم تطبيقها في قاعدة البيانات المحلية.
        """
        url = base_url or AppConfig.get_server_url()
        timeout = AppConfig.get("timeout_seconds", 35.0)
        try:
            endpoint = f"{url}/api/sync/residence_full_pull?residence_id={residence_id}"
            logger.info(f"Connecting to Directorate server for residence full pull: {endpoint}")
            r = http_get(endpoint, timeout=timeout)
            if r.status_code != 200:
                err_msg = f"فشل الاتصال بسيرفر المديرية (رمز الاستجابة: {r.status_code})"
                try:
                    err_json = r.json()
                    if "error" in err_json:
                        err_msg += f": {err_json['error']}"
                except Exception:
                    pass
                return {"success": False, "error": err_msg}

            resp_json = r.json()
            if not resp_json.get("success"):
                return {"success": False, "error": resp_json.get("error", "فشل غير معروف من سيرفر المديرية")}

            data = resp_json.get("data", {})
            counts = self.apply_residence_full_data(residence_id, data)
            return {
                "success": True,
                "residence_id": residence_id,
                "residence_name": resp_json.get("residence_name", f"الإقامة {residence_id}"),
                "counts": counts
            }
        except Exception as e:
            logger.exception("Error in pull_full_residence_data")
            return {"success": False, "error": f"تعذر سحب البيانات عبر الشبكة: {str(e)}"}

    def restore_residence_from_db_file(self, residence_id: int, db_path: str) -> Dict[str, Any]:
        """
        سحب واسترجاع بيانات إقامة محددة مباشرة من ملف قاعدة بيانات المديرية (مثال: من فلاش ديسك USB).
        """
        import sqlite3
        import os
        if not os.path.exists(db_path):
            return {"success": False, "error": f"الملف المحدد غير موجود: {db_path}"}

        try:
            src = sqlite3.connect(db_path)
            src.row_factory = sqlite3.Row

            res_row = src.execute("SELECT id, name FROM residences WHERE id = ?", (residence_id,)).fetchone()
            res_name = res_row["name"] if res_row else f"الإقامة {residence_id}"

            data = {}
            for tbl in ["categories", "suppliers", "articles"]:
                try:
                    cur = src.execute(f"SELECT * FROM {tbl}")
                    cols = [c[0] for c in cur.description] if cur.description else []
                    data[tbl] = [dict(zip(cols, r)) for r in cur.fetchall()]
                except Exception:
                    data[tbl] = []

            # daily_meals_tracking
            cur = src.execute("SELECT * FROM daily_meals_tracking WHERE residence_id = ?", (residence_id,))
            cols = [c[0] for c in cur.description] if cur.description else []
            data["daily_meals_tracking"] = [dict(zip(cols, r)) for r in cur.fetchall()]

            # entry_vouchers & items
            cur = src.execute("SELECT * FROM entry_vouchers WHERE residence_id = ?", (residence_id,))
            cols = [c[0] for c in cur.description] if cur.description else []
            entry_vouchers = [dict(zip(cols, r)) for r in cur.fetchall()]
            data["entry_vouchers"] = entry_vouchers

            ev_ids = [v["id"] for v in entry_vouchers]
            if ev_ids:
                placeholders = ",".join("?" for _ in ev_ids)
                cur = src.execute(f"SELECT * FROM entry_voucher_items WHERE voucher_id IN ({placeholders})", tuple(ev_ids))
                cols = [c[0] for c in cur.description] if cur.description else []
                data["entry_voucher_items"] = [dict(zip(cols, r)) for r in cur.fetchall()]
            else:
                data["entry_voucher_items"] = []

            # exit_vouchers & items
            cur = src.execute("SELECT * FROM exit_vouchers WHERE residence_id = ?", (residence_id,))
            cols = [c[0] for c in cur.description] if cur.description else []
            exit_vouchers = [dict(zip(cols, r)) for r in cur.fetchall()]
            data["exit_vouchers"] = exit_vouchers

            ex_ids = [v["id"] for v in exit_vouchers]
            if ex_ids:
                placeholders = ",".join("?" for _ in ex_ids)
                cur = src.execute(f"SELECT * FROM exit_voucher_items WHERE voucher_id IN ({placeholders})", tuple(ex_ids))
                cols = [c[0] for c in cur.description] if cur.description else []
                data["exit_voucher_items"] = [dict(zip(cols, r)) for r in cur.fetchall()]
            else:
                data["exit_voucher_items"] = []

            # stock_movements
            cur = src.execute("SELECT * FROM stock_movements WHERE residence_id = ?", (residence_id,))
            cols = [c[0] for c in cur.description] if cur.description else []
            data["stock_movements"] = [dict(zip(cols, r)) for r in cur.fetchall()]

            # residence_articles
            cur = src.execute("SELECT * FROM residence_articles WHERE residence_id = ?", (residence_id,))
            cols = [c[0] for c in cur.description] if cur.description else []
            data["residence_articles"] = [dict(zip(cols, r)) for r in cur.fetchall()]

            # residence_loans & items
            cur = src.execute("SELECT * FROM residence_loans WHERE from_residence_id = ? OR to_residence_id = ?", (residence_id, residence_id))
            cols = [c[0] for c in cur.description] if cur.description else []
            loans = [dict(zip(cols, r)) for r in cur.fetchall()]
            data["residence_loans"] = loans

            loan_ids = [l["id"] for l in loans]
            if loan_ids:
                placeholders = ",".join("?" for _ in loan_ids)
                cur = src.execute(f"SELECT * FROM residence_loan_items WHERE loan_id IN ({placeholders})", tuple(loan_ids))
                cols = [c[0] for c in cur.description] if cur.description else []
                data["residence_loan_items"] = [dict(zip(cols, r)) for r in cur.fetchall()]
            else:
                data["residence_loan_items"] = []

            # inventory_snapshots
            cur = src.execute("SELECT * FROM inventory_snapshots WHERE residence_id = ?", (residence_id,))
            cols = [c[0] for c in cur.description] if cur.description else []
            data["inventory_snapshots"] = [dict(zip(cols, r)) for r in cur.fetchall()]

            # unlocked_days
            try:
                cur = src.execute("SELECT * FROM unlocked_days WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                data["unlocked_days"] = [dict(zip(cols, r)) for r in cur.fetchall()]
            except Exception:
                data["unlocked_days"] = []

            # supplier_allocations
            try:
                cur = src.execute("SELECT * FROM supplier_allocations WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                data["supplier_allocations"] = [dict(zip(cols, r)) for r in cur.fetchall()]
            except Exception:
                data["supplier_allocations"] = []

            # bon_commande & items
            try:
                cur = src.execute("SELECT * FROM bon_commande WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                bcs = [dict(zip(cols, r)) for r in cur.fetchall()]
                data["bon_commande"] = bcs
                bc_ids = [b["id"] for b in bcs]
                if bc_ids:
                    placeholders = ",".join("?" for _ in bc_ids)
                    cur = src.execute(f"SELECT * FROM bon_commande_qty WHERE bon_id IN ({placeholders})", tuple(bc_ids))
                    cols = [c[0] for c in cur.description] if cur.description else []
                    data["bon_commande_qty"] = [dict(zip(cols, r)) for r in cur.fetchall()]
                else:
                    data["bon_commande_qty"] = []
            except Exception:
                data["bon_commande"] = []
                data["bon_commande_qty"] = []

            src.close()

            counts = self.apply_residence_full_data(residence_id, data)
            return {
                "success": True,
                "residence_id": residence_id,
                "residence_name": res_name,
                "counts": counts
            }
        except Exception as e:
            logger.exception("Error in restore_residence_from_db_file")
            return {"success": False, "error": f"فشل استخراج البيانات من ملف قاعدة البيانات: {str(e)}"}

    def push_full_residence_data(self, residence_id: int, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        رفع وتثبيت الحزمة الكاملة لبيانات إقامة محددة مباشرة إلى خادم المديرية المركزي.
        يأخذ كافة السجلات المحلية للإقامة ويرسلها في حزمة واحدة.
        """
        url = base_url or AppConfig.get_server_url()
        timeout = AppConfig.get("timeout_seconds", 60.0)

        try:
            with self.db.get_connection() as conn:
                res_row = conn.execute("SELECT id, name FROM residences WHERE id = ?", (residence_id,)).fetchone()
                res_name = res_row["name"] if res_row else f"الإقامة {residence_id}"

                cur = conn.execute("SELECT * FROM daily_meals_tracking WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                meals = [dict(zip(cols, r)) for r in cur.fetchall()]

                cur = conn.execute("SELECT * FROM entry_vouchers WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                entry_vouchers = [dict(zip(cols, r)) for r in cur.fetchall()]
                ev_ids = [v["id"] for v in entry_vouchers]
                entry_items = []
                if ev_ids:
                    placeholders = ",".join("?" for _ in ev_ids)
                    cur_it = conn.execute(f"SELECT * FROM entry_voucher_items WHERE voucher_id IN ({placeholders})", tuple(ev_ids))
                    it_cols = [c[0] for c in cur_it.description] if cur_it.description else []
                    entry_items = [dict(zip(it_cols, r)) for r in cur_it.fetchall()]

                cur = conn.execute("SELECT * FROM exit_vouchers WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                exit_vouchers = [dict(zip(cols, r)) for r in cur.fetchall()]
                ex_ids = [v["id"] for v in exit_vouchers]
                exit_items = []
                if ex_ids:
                    placeholders = ",".join("?" for _ in ex_ids)
                    cur_it = conn.execute(f"SELECT * FROM exit_voucher_items WHERE voucher_id IN ({placeholders})", tuple(ex_ids))
                    it_cols = [c[0] for c in cur_it.description] if cur_it.description else []
                    exit_items = [dict(zip(it_cols, r)) for r in cur_it.fetchall()]

                cur = conn.execute("SELECT * FROM stock_movements WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                movements = [dict(zip(cols, r)) for r in cur.fetchall()]

                cur = conn.execute("SELECT * FROM residence_articles WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                res_articles = [dict(zip(cols, r)) for r in cur.fetchall()]

                cur = conn.execute("SELECT * FROM residence_loans WHERE from_residence_id = ? OR to_residence_id = ?", (residence_id, residence_id))
                cols = [c[0] for c in cur.description] if cur.description else []
                loans = [dict(zip(cols, r)) for r in cur.fetchall()]
                loan_ids = [l["id"] for l in loans]
                loan_items = []
                if loan_ids:
                    placeholders = ",".join("?" for _ in loan_ids)
                    cur_it = conn.execute(f"SELECT * FROM residence_loan_items WHERE loan_id IN ({placeholders})", tuple(loan_ids))
                    it_cols = [c[0] for c in cur_it.description] if cur_it.description else []
                    loan_items = [dict(zip(it_cols, r)) for r in cur_it.fetchall()]

                cur = conn.execute("SELECT * FROM inventory_snapshots WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                inventories = [dict(zip(cols, r)) for r in cur.fetchall()]

                cur = conn.execute("SELECT * FROM unlocked_days WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                unlocked = [dict(zip(cols, r)) for r in cur.fetchall()]

                cur = conn.execute("SELECT * FROM supplier_allocations WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                allocations = [dict(zip(cols, r)) for r in cur.fetchall()]

                cur = conn.execute("SELECT * FROM bon_commande WHERE residence_id = ?", (residence_id,))
                cols = [c[0] for c in cur.description] if cur.description else []
                bon_commandes = [dict(zip(cols, r)) for r in cur.fetchall()]
                bc_ids = [b["id"] for b in bon_commandes]
                bon_quantities = []
                if bc_ids:
                    placeholders = ",".join("?" for _ in bc_ids)
                    cur_it = conn.execute(f"SELECT * FROM bon_commande_qty WHERE bon_id IN ({placeholders})", tuple(bc_ids))
                    it_cols = [c[0] for c in cur_it.description] if cur_it.description else []
                    bon_quantities = [dict(zip(it_cols, r)) for r in cur_it.fetchall()]

            payload = {
                "residence_id": residence_id,
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
                    "bon_commande_qty": bon_quantities
                }
            }

            endpoint = f"{url}/api/sync/residence_full_push"
            logger.info(f"Pushing full residence data to {endpoint} ({len(meals)} meals, {len(entry_vouchers)} entry, {len(exit_vouchers)} exit)...")
            r = http_post(endpoint, json=payload, timeout=timeout)
            if r.status_code == 200:
                res_data = r.json()
                if res_data.get("success"):
                    with self.db.get_connection() as conn:
                        now_str = TimeService.iso_now() if TimeService else datetime.datetime.now().isoformat()
                        conn.execute("UPDATE sync_queue SET status = 'SYNCED', synced_at = ? WHERE residence_id = ?", (now_str, residence_id))
                        conn.commit()
                    return {
                        "success": True,
                        "residence_id": residence_id,
                        "residence_name": res_name,
                        "counts": {
                            "daily_meals_tracking": len(meals),
                            "entry_vouchers": len(entry_vouchers),
                            "exit_vouchers": len(exit_vouchers),
                            "stock_movements": len(movements)
                        }
                    }
                else:
                    return {"success": False, "error": res_data.get("error", "فشل غير معروف من السيرفر")}
            else:
                return {"success": False, "error": f"استجابة غير صحيحة من السيرفر (كود: {r.status_code})"}
        except Exception as e:
            logger.exception("Error in push_full_residence_data")
            return {"success": False, "error": f"تعذر رفع البيانات: {e}"}

    def check_and_enforce_parity(self, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        التحقق التلقائي الذكي من تطابق بيانات كافة الإقامات بين قاعدة البيانات المحلية وخادم المديرية.
        إذا كان أي حاسوب مديرية تنقصه بيانات لأي إقامة، يتم سحبها فوراً وتحديثها لضمان التطابق التام 100%.
        """
        url = base_url or AppConfig.get_server_url()
        try:
            r = http_get(f"{url}/api/sync/summary", timeout=15.0)
            if r.status_code != 200:
                return {"success": False, "error": f"Server summary error: {r.status_code}"}
            sum_data = r.json()
            if not sum_data.get("success"):
                return {"success": False, "error": "Summary failed"}

            server_residences = sum_data.get("residences", {})
            out_of_sync = []

            with self.db.get_connection() as conn:
                for rid_str, s_info in server_residences.items():
                    rid = int(rid_str)
                    local_meals = conn.execute("SELECT COUNT(*) FROM daily_meals_tracking WHERE residence_id = ?", (rid,)).fetchone()[0]
                    local_entry = conn.execute("SELECT COUNT(*) FROM entry_vouchers WHERE residence_id = ?", (rid,)).fetchone()[0]
                    local_exit = conn.execute("SELECT COUNT(*) FROM exit_vouchers WHERE residence_id = ?", (rid,)).fetchone()[0]

                    if (local_meals < s_info.get("meals", 0) or
                        local_entry < s_info.get("entry_vouchers", 0) or
                        local_exit < s_info.get("exit_vouchers", 0)):
                        out_of_sync.append((rid, s_info.get("name", f"الإقامة {rid}"), local_meals, s_info.get("meals", 0)))

            synced_count = 0
            if out_of_sync:
                logger.info(f"Parity check: Found {len(out_of_sync)} residences out of sync: {out_of_sync}. Auto-syncing missing data...")
                for rid, name, loc_m, srv_m in out_of_sync:
                    pull_res = self.pull_full_residence_data(rid, base_url=url)
                    if pull_res.get("success"):
                        synced_count += 1
                        logger.info(f"Parity restored for Residence {rid} ({name})")

            server_max = sum_data.get("server_max_sync_event_id", 0)
            if server_max:
                curr_last = int(self.db.get_setting("last_pulled_sync_event_id", "0") or "0")
                if curr_last > server_max or curr_last == 0:
                    self.db.set_setting("last_pulled_sync_event_id", str(server_max))

            return {
                "success": True,
                "out_of_sync_count": len(out_of_sync),
                "synced_count": synced_count
            }
        except Exception as e:
            logger.warning(f"Notice parity check: {e}")
            return {"success": False, "error": str(e)}

    def sync_all_residences_from_server(self, base_url: Optional[str] = None, progress_cb: Optional[Any] = None) -> Dict[str, Any]:
        """
        تحديث ومزامنة شاملة لكافة الإقامات التسع من الخادم المركزي للمديرية.
        مخصص لمكاتب وحواسيب المديرية لضمان تطابق كامل ودقيق للبيانات عبر كل أجهزة المديرية.
        """
        url = base_url or AppConfig.get_server_url()
        with self.db.get_connection() as conn:
            res_rows = conn.execute("SELECT id, name, code FROM residences ORDER BY id ASC").fetchall()

        if not res_rows:
            return {"success": False, "error": "لا توجد إقامات مسجلة في قاعدة البيانات"}

        total = len(res_rows)
        synced_count = 0
        details = {}

        logger.info(f"Starting complete sync for all {total} residences from Directorate server: {url}")
        for idx, r in enumerate(res_rows):
            r_id = r["id"]
            r_name = r["name"]
            if progress_cb:
                try:
                    progress_cb(idx + 1, total, r_name)
                except Exception:
                    pass

            res = self.pull_full_residence_data(r_id, base_url=url)
            if res.get("success"):
                synced_count += 1
                details[r_id] = {"name": r_name, "success": True, "counts": res.get("counts", {})}
            else:
                details[r_id] = {"name": r_name, "success": False, "error": res.get("error")}

        # مزامنة مؤشر الأحداث إلى أحدث حدث موجود على السيرفر
        try:
            r_st = http_get(f"{url}/api/sync/pull?since_id=0&limit=1", timeout=12.0)
            if r_st.status_code == 200:
                latest_id = r_st.json().get("latest_id", 0)
                if latest_id:
                    self.db.set_setting("last_pulled_sync_event_id", str(latest_id))
        except Exception as e_ev:
            logger.warning(f"Notice setting last_pulled_sync_event_id after full sync: {e_ev}")

        try:
            from core.cache_service import CacheService
            CacheService.invalidate_all()
        except Exception:
            pass

        return {
            "success": synced_count > 0,
            "synced_count": synced_count,
            "total_residences": total,
            "details": details
        }

    def sync_all_residences_from_db_file(self, db_path: str, progress_cb: Optional[Any] = None) -> Dict[str, Any]:
        """
        تحديث ومزامنة شاملة لكافة الإقامات التسع محلياً بدون إنترنت من ملف قاعدة بيانات (مثال: فلاش ديسك USB).
        """
        import os
        import sqlite3
        if not os.path.exists(db_path):
            return {"success": False, "error": f"الملف غير موجود: {db_path}"}

        try:
            src = sqlite3.connect(db_path)
            res_rows = src.execute("SELECT id, name FROM residences ORDER BY id ASC").fetchall()
            src.close()
        except Exception as e:
            return {"success": False, "error": f"تعذر قراءة قاعدة البيانات المحددة: {e}"}

        if not res_rows:
            return {"success": False, "error": "لم يتم العثور على أي إقامات في الملف المحدد"}

        total = len(res_rows)
        synced_count = 0
        details = {}

        for idx, (r_id, r_name) in enumerate(res_rows):
            if progress_cb:
                try:
                    progress_cb(idx + 1, total, r_name)
                except Exception:
                    pass

            res = self.restore_residence_from_db_file(r_id, db_path)
            if res.get("success"):
                synced_count += 1
                details[r_id] = {"name": r_name, "success": True, "counts": res.get("counts", {})}
            else:
                details[r_id] = {"name": r_name, "success": False, "error": res.get("error")}

        try:
            from core.cache_service import CacheService
            CacheService.invalidate_all()
        except Exception:
            pass

        return {
            "success": synced_count > 0,
            "synced_count": synced_count,
            "total_residences": total,
            "details": details
        }

class SyncWorker(QThread):
    """
    خيط مزامنة خلفي غير متزامن في الخلفية لضمان عدم تجميد واجهة المستخدم.

    نظام المزامنة أحادي الاتجاه (Unidirectional Sync):
    - الإقامات: ترسل (push) فقط إلى المديرية لا تسحب أي بيانات من أي مصدر
    - المديرية:  تسحب (pull) فقط من الإقامات لا ترسل أي بيانات محلية
    """
    connectivity_changed = pyqtSignal(bool)   # True: متصل بالسيرفر | False: غير متصل (أوفلاين)
    sync_finished = pyqtSignal(int, int)       # (عدد الحركات المتزامنة, عدد المتبقي)
    sync_error = pyqtSignal(str)
    # إشارة خاصة: تُطلق في المديرية عند وصول بيانات جديدة من إقامة
    new_residence_data_received = pyqtSignal(int)  # residence_id

    def __init__(self, residence_id: Optional[int] = None, is_directorate: bool = False, parent=None):
        super().__init__(parent)
        self.residence_id = residence_id
        self.is_directorate = is_directorate
        self.sync_svc = SyncService()
        self.sync_svc.is_directorate = is_directorate
        self.is_running = True
        self.last_online_state: Optional[bool] = None
        self._trigger_now = False
        self._force_full_sync = False
        self._last_pulled_id = 0  # آخر معرف تم سحبه (لكشف التحديثات الجديدة)
        self._consecutive_failures = 0

    def trigger_full_all_sync(self):
        """طلب تحديث شامل وفوري لكافة الإقامات في الخلفية"""
        self._force_full_sync = True
        self._trigger_now = True

    def trigger_immediate_sync(self):
        self._trigger_now = True

    def stop(self):
        self.is_running = False
        self.wait(2000)

    def run(self):
        while self.is_running:
            try:
                # 1. فحص الاتصال بالخادم مع نظام تثبيت الحالة ومنع التذبذب (Anti-Flicker)
                raw_online = self.sync_svc.is_server_reachable()
                if raw_online:
                    self._consecutive_failures = 0
                    if self.last_online_state is not True:
                        self.last_online_state = True
                        self.connectivity_changed.emit(True)
                else:
                    self._consecutive_failures += 1
                    # لا نعلن انقطاع الاتصال إلا بعد 3 إخفاقات متتالية لتفادي التذبذب بسبب تقلبات الشبكة
                    if self._consecutive_failures >= 3 and self.last_online_state is not False:
                        self.last_online_state = False
                        self.connectivity_changed.emit(False)

                is_online = (self.last_online_state is True)
                if is_online:
                    # إعادة تنشيط أي حركات معلقة أو متعثرة عند توفر الاتصال
                    self.sync_svc.reset_failed_queue(self.residence_id)

                    pushed = 0
                    pulled = 0

                    is_dir_server = self.is_directorate or (AppConfig.get("app_mode") == "DIRECTORATE_SERVER" and not self.residence_id)

                    if is_dir_server:
                        # ═══════════════════════════════════════════════════════
                        # وضع المديرية المركزية: تطابق تام لكافة حواسيب المديرية
                        # ═══════════════════════════════════════════════════════
                        # 1. التحقق التلقائي الذكي من تطابق كافة الإقامات (Parity Check) عند بدء التشغيل أو بطلب دوري
                        self._dir_cycle_count = getattr(self, "_dir_cycle_count", 0) + 1
                        if not getattr(self, "_dir_startup_parity_done", False) or self._dir_cycle_count % 30 == 0 or getattr(self, "_force_full_sync", False):
                            self._dir_startup_parity_done = True
                            self._force_full_sync = False
                            parity_res = self.sync_svc.check_and_enforce_parity()
                            if parity_res.get("synced_count", 0) > 0:
                                pulled += parity_res.get("synced_count", 0)
                                self.new_residence_data_received.emit(pulled)

                        # 2. سحب الحركات التزايدية المستمرة من الإقامات فورياً
                        pulled_inc = self.sync_svc.pull_updates(residence_id=None, is_directorate=True)
                        if pulled_inc > 0:
                            pulled += pulled_inc
                            self.new_residence_data_received.emit(pulled_inc)

                        # 3. إرسال أي حركات مسجلة من المديرية
                        pending_cnt = self.sync_svc.get_pending_count(None)
                        if pending_cnt > 0 or self._trigger_now:
                            pushed, _ = self.sync_svc.push_pending(None)
                    else:
                        # ═══════════════════════════════════════════════════════
                        # وضع الإقامة: الاسترجاع التلقائي عند التسطيب الجديد + إرسال
                        # ═══════════════════════════════════════════════════════
                        res_id = self.residence_id or AppConfig.get("residence_id")

                        # التحقق الذكي: إذا كان الحاسوب جديداً أو فارغاً (0 وجبات مسجلة محلياً للإقامة)
                        if res_id and not getattr(self, "_residence_restore_checked", False):
                            self._residence_restore_checked = True
                            try:
                                with self.sync_svc.db.get_connection() as conn:
                                    m_cnt = conn.execute("SELECT COUNT(*) FROM daily_meals_tracking WHERE residence_id = ?", (int(res_id),)).fetchone()[0]
                                if m_cnt == 0:
                                    logger.info(f"SyncWorker: Residence {res_id} has 0 local meals. Auto-checking Directorate server for existing data...")
                                    restore_res = self.sync_svc.pull_full_residence_data(int(res_id))
                                    if restore_res.get("success"):
                                        counts = restore_res.get("counts", {})
                                        retrieved_meals = counts.get("daily_meals_tracking", 0)
                                        if retrieved_meals > 0:
                                            logger.info(f"SyncWorker: Successfully auto-restored {retrieved_meals} meals for residence {res_id} from Directorate!")
                                            self.new_residence_data_received.emit(retrieved_meals)
                                            self.sync_finished.emit(retrieved_meals, 0)
                            except Exception as e_rst:
                                logger.warning(f"Notice residence auto-restore check: {e_rst}")

                        # إرسال الحركات المحفوظة محلياً في الرتل
                        pending_cnt = self.sync_svc.get_pending_count(res_id)
                        if pending_cnt > 0 or self._trigger_now:
                            pushed, _ = self.sync_svc.push_pending(res_id)
                            # عند حفظ ورقة اليوم أو طلب المزامنة الفورية للإقامة، رفع الحزمة الكاملة للإقامة لضمان تطابق مخزون أول مدة والسجلات فورياً
                            if self._trigger_now and res_id:
                                try:
                                    self.sync_svc.push_full_residence_data(int(res_id))
                                except Exception as e_pf:
                                    logger.warning(f"SyncWorker: push_full_residence_data notice: {e_pf}")

                    if pushed > 0 or pulled > 0 or self._trigger_now:
                        left = self.sync_svc.get_pending_count(self.residence_id)
                        self.sync_finished.emit(pushed + pulled, left)
                        self._trigger_now = False

            except Exception as e:
                self.sync_error.emit(str(e))

            # النوم حتى الدورة القادمة
            # المديرية تتحقق كل 8 ثواني لاستقبال بيانات الإقامات فوراً
            # الإقامات تتحقق كل 10 ثواني لإرسال ما تراكم في الرتل
            # المديرية تتحقق كل ثانيتين لسحب بيانات الإقامات بمجرد حفظها فوراً
            # الإقامات تتحقق كل 4 ثوانٍ لإرسال أي حركات معلقة
            interval = 3 if is_dir_server else max(4, AppConfig.get("sync_interval_seconds", 5))
            for _ in range(max(1, interval)):
                if not self.is_running:
                    break
                if self._trigger_now:
                    break
                self.msleep(1000)


class AllResidencesSyncThread(QThread):
    """
    خيط مزامنة خلفي غير متزامن لتحديث كافة الإقامات دفعة واحدة دون تجميد واجهة المستخدم
    """
    progress = pyqtSignal(int, int, str)  # (current, total, residence_name)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, sync_service: SyncService, mode: str = "SERVER", db_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.sync_svc = sync_service
        self.mode = mode
        self.db_path = db_path
        self._is_canceled = False

    def cancel(self):
        self._is_canceled = True

    def run(self):
        try:
            def cb(curr, tot, name):
                if not self._is_canceled:
                    self.progress.emit(curr, tot, name)

            if self.mode == "SERVER":
                res = self.sync_svc.sync_all_residences_from_server(progress_cb=cb)
            else:
                res = self.sync_svc.sync_all_residences_from_db_file(self.db_path or "", progress_cb=cb)

            self.finished.emit(res)
        except Exception as e:
            logger.exception("Error in AllResidencesSyncThread")
            self.error.emit(str(e))
