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
        now_str = datetime.datetime.now().isoformat()
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

        # حظر قطعي لا رجعة فيه: سحب البيانات حصري للمديرية المركزية فقط
        # أي حاسوب إقامة (سواء نمط CLIENT أو محدد به رقم إقامة) يُمنع منعاً باتاً من سحب وتعديل بياناته
        cfg_mode = AppConfig.get("app_mode", "")
        cfg_res_id = AppConfig.get("residence_id")

        if AppConfig.is_client_mode() or cfg_mode == "RESIDENCE_CLIENT":
            logger.info("🚫 سحب البيانات محظور: هذا الجهاز حاسوب إقامة ولا يسحب أي بيانات من الخارج.")
            return 0

        if cfg_res_id and int(cfg_res_id) > 0 and cfg_mode != "DIRECTORATE_SERVER":
            logger.info(f"🚫 سحب البيانات محظور: هذا الجهاز مرتبط بالإقامة {cfg_res_id} ولا يسحب أي بيانات.")
            return 0

        # المديرية فقط في وضع الخادم ومع تصريح المديرية هي من يملك صلاحية السحب
        is_true_directorate = (cfg_mode == "DIRECTORATE_SERVER") and (is_directorate or getattr(self, "is_directorate", False))
        if not is_true_directorate:
            logger.info("🚫 سحب البيانات محظور: السحب متاح لمركز قيادة المديرية المركزية فقط.")
            return 0
        url = base_url or AppConfig.get_server_url()
        last_id = int(self.db.get_setting("last_pulled_sync_event_id", "0") or "0")
        endpoint = f"{url}/api/sync/pull?since_id={last_id}&limit=200"
        if residence_id:
            endpoint += f"&residence_id={residence_id}"

        try:
            r = http_get(endpoint, timeout=AppConfig.get("timeout_seconds", 25.0))
            if r.status_code != 200:
                return 0
            data = r.json()
            latest_on_server = int(data.get("latest_id", 0) or 0)
            if last_id > latest_on_server:
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
                except Exception as ev_err:
                    logger.warning(f"Error applying pulled sync event {ev.get('id')}: {ev_err}")

            latest_id = data.get("latest_id", last_id)
            self.db.set_setting("last_pulled_sync_event_id", str(latest_id))
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
        self._last_pulled_id = 0  # آخر معرف تم سحبه (لكشف التحديثات الجديدة)
        self._consecutive_failures = 0

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

                    is_dir_server = (AppConfig.get("app_mode") == "DIRECTORATE_SERVER") and (not AppConfig.get("residence_id") or AppConfig.get("residence_id") == 0) and self.is_directorate

                    if is_dir_server:
                        # ═══════════════════════════════════════════════════════
                        # وضع المديرية المركزية: سحب أحدث بيانات الإقامات
                        # ═══════════════════════════════════════════════════════
                        pulled = self.sync_svc.pull_updates(residence_id=None, is_directorate=True)
                        if pulled > 0:
                            self.new_residence_data_received.emit(0)

                        # وفي حال تم تسجيل أي حركة في المديرية، تُرسل أيضاً
                        pending_cnt = self.sync_svc.get_pending_count(None)
                        if pending_cnt > 0 or self._trigger_now:
                            pushed, _ = self.sync_svc.push_pending(None)
                    else:
                        # ═══════════════════════════════════════════════════════
                        # وضع الإقامة: إرسال (push) فقط إلى المديرية
                        # الإقامة لا تسحب أي بيانات من أي مصدر آخر لحماية مدخلاتها
                        # ═══════════════════════════════════════════════════════
                        res_id = self.residence_id or AppConfig.get("residence_id")
                        pending_cnt = self.sync_svc.get_pending_count(res_id)
                        if pending_cnt > 0 or self._trigger_now:
                            pushed, _ = self.sync_svc.push_pending(res_id)

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
            interval = max(5, AppConfig.get("sync_interval_seconds", 5))
            for _ in range(max(1, interval)):
                if not self.is_running:
                    break
                if self._trigger_now:
                    break
                self.msleep(1000)
