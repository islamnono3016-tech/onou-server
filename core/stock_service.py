import sqlite3
import datetime
from typing import List, Dict, Any, Optional, Tuple
from database.db_manager import DatabaseManager

class InsufficientStockError(Exception):
    """خطأ عدم كفاية المخزون لمنع الرصيد السالب"""
    def __init__(self, article_name: str, requested: float, available: float):
        self.article_name = article_name
        self.requested = requested
        self.available = available
        super().__init__(f"المخزون غير كافٍ للمادة '{article_name}': الكمية المطلوبة ({requested}) تتجاوز المتوفر ({available})")

class StockService:
    """محرك إدارة العمليات المحاسبية والمخزنية"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None, residence_id: int = 1):
        self.db = db_manager or DatabaseManager()
        self.residence_id = residence_id

    def set_residence(self, residence_id: int):
        self.residence_id = residence_id

    def get_residences_list(self, only_active: bool = True) -> List[Dict[str, Any]]:
        from core.cache_service import CacheService
        return CacheService.get_residences(self.db, only_active=only_active)

    def _enqueue_sync(self, entity_type: str, action: str, entity_id: Any, payload: Dict[str, Any], residence_id: Optional[int] = None):
        """إضافة حركة إلى رتل المزامنة في الخلفية عند العمل كعميل إقامة"""
        try:
            from core.config import AppConfig
            if AppConfig.is_client_mode() or AppConfig.get("auto_sync", True):
                r_id = residence_id or self.residence_id
                from core.sync_service import SyncService
                sync_s = SyncService(self.db)
                sync_s.enqueue(
                    residence_id=r_id,
                    entity_type=entity_type,
                    action=action,
                    entity_id=str(entity_id),
                    payload=payload
                )
        except Exception:
            pass

    # -------------------------------------------------------------
    # إدارة المواد والأسعار (Articles & Catalog)
    # -------------------------------------------------------------
    def get_articles(self, search: str = "", category_id: Optional[int] = None, only_active: bool = True, residence_id: Optional[int] = None) -> List[Dict[str, Any]]:
        r_id = residence_id or self.residence_id
        from core.cache_service import CacheService
        all_articles = CacheService.get_articles(self.db, residence_id=r_id, only_active=only_active)
        
        if not search and category_id is None:
            return all_articles
            
        results = all_articles
        if category_id is not None:
            results = [a for a in results if a.get("category_id") == category_id]
        if search:
            s = search.lower().strip()
            results = [a for a in results if s in (a.get("name") or "").lower() or s in (a.get("code") or "").lower()]
        return results

    def get_article(self, article_id: int, residence_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        r_id = residence_id or self.residence_id
        with self.db.get_connection() as conn:
            cur = conn.execute("""
                SELECT a.id, a.code, a.name, a.category_id, a.unit,
                       a.price_ht, a.discount_rate, a.discount_amount, a.price_after_discount,
                       a.tva_rate, a.price_ttc,
                       COALESCE(ra.current_pmp, a.current_pmp, a.price_ttc) as current_pmp,
                       COALESCE(ra.safety_stock, a.safety_stock) as safety_stock,
                       COALESCE(ra.initial_stock, a.initial_stock) as initial_stock,
                       COALESCE(ra.current_stock, a.current_stock) as current_stock,
                       a.is_active, c.name as category_name
                FROM articles a
                LEFT JOIN categories c ON a.category_id = c.id
                LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                WHERE a.id = ?
            """, (r_id, article_id))
            row = cur.fetchone()
            return dict(row) if row else None

    def save_article(self, data: Dict[str, Any]) -> int:
        """إضافة أو تعديل مادة مع حساب الأسعار تلقائياً"""
        price_ht = float(data.get("price_ht", 0.0))
        discount_rate = float(data.get("discount_rate", 0.0)) # مثلاً 0.05
        discount_amount = price_ht * discount_rate
        price_after_discount = price_ht - discount_amount
        tva_rate = float(data.get("tva_rate", 0.0)) # 0, 9, 19
        price_ttc = price_after_discount * (1.0 + (tva_rate / 100.0))

        article_id = data.get("id")
        with self.db.get_connection() as conn:
            if article_id:
                conn.execute("""
                    UPDATE articles SET
                        code = ?, name = ?, category_id = ?, unit = ?,
                        price_ht = ?, discount_rate = ?, discount_amount = ?,
                        price_after_discount = ?, tva_rate = ?, price_ttc = ?,
                        safety_stock = ?, is_active = ?
                    WHERE id = ?
                """, (
                    data.get("code", ""), data["name"], data.get("category_id"),
                    data.get("unit", "كلغ"), price_ht, discount_rate, discount_amount,
                    price_after_discount, tva_rate, price_ttc,
                    float(data.get("safety_stock", 0.0)), int(data.get("is_active", 1)),
                    article_id
                ))
            else:
                initial_stock = float(data.get("initial_stock", 0.0))
                cur = conn.execute("""
                    INSERT INTO articles (
                        code, name, category_id, unit,
                        price_ht, discount_rate, discount_amount,
                        price_after_discount, tva_rate, price_ttc,
                        current_pmp, safety_stock, initial_stock, current_stock, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get("code", ""), data["name"], data.get("category_id"),
                    data.get("unit", "كلغ"), price_ht, discount_rate, discount_amount,
                    price_after_discount, tva_rate, price_ttc,
                    price_ttc, float(data.get("safety_stock", 0.0)),
                    initial_stock, initial_stock, int(data.get("is_active", 1))
                ))
                article_id = cur.lastrowid
                if initial_stock > 0:
                    conn.execute("""
                        INSERT INTO stock_movements (
                            date, article_id, movement_type, voucher_id,
                            qty_in, qty_out, unit_price, total_value, balance_after
                        ) VALUES (?, ?, 'INITIAL', NULL, ?, 0, ?, ?, ?)
                    """, (
                        datetime.date.today().isoformat(), article_id,
                        initial_stock, price_ttc, initial_stock * price_ttc, initial_stock
                    ))
            conn.commit()
            return article_id

    # -------------------------------------------------------------
    # وصولات الدخول / التوريد والاستعارة (Entry Vouchers)
    # -------------------------------------------------------------
    def create_entry_voucher(self, voucher: Dict[str, Any], items: List[Dict[str, Any]]) -> int:
        """
        تسجيل وصل دخول بضاعة مع زيادة المخزون آلياً وتحديث PMP وسجل الحركات
        """
        total_amount = 0.0
        calculated_items = []
        for it in items:
            q = float(it["quantity"])
            p_ht = float(it.get("unit_price_ht", 0.0))
            tva = float(it.get("tva_rate", 0.0))
            p_ttc = float(it.get("unit_price_ttc", 0.0))
            if p_ttc <= 0 and p_ht > 0:
                p_ttc = p_ht * (1.0 + (tva / 100.0))
            item_tot = q * p_ttc
            total_amount += item_tot
            calculated_items.append({
                "article_id": it["article_id"],
                "quantity": q,
                "unit_price_ht": p_ht,
                "tva_rate": tva,
                "unit_price_ttc": p_ttc,
                "total_price": item_tot
            })

        voucher_type = voucher.get("voucher_type", "SUPPLIER") # SUPPLIER أو LOAN_IN
        v_date = voucher["date"]
        r_id = voucher.get("residence_id") or self.residence_id

        with self.db.get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO entry_vouchers (
                    voucher_number, date, voucher_type, supplier_id,
                    source_residence, delivery_note_ref, total_amount, notes, residence_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                voucher.get("voucher_number", f"BE-{v_date}"),
                v_date, voucher_type, voucher.get("supplier_id"),
                voucher.get("source_residence", ""),
                voucher.get("delivery_note_ref", ""),
                total_amount, voucher.get("notes", ""),
                r_id
            ))
            voucher_id = cur.lastrowid

            for it in calculated_items:
                conn.execute("""
                    INSERT INTO entry_voucher_items (
                        voucher_id, article_id, quantity,
                        unit_price_ht, tva_rate, unit_price_ttc, total_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    voucher_id, it["article_id"], it["quantity"],
                    it["unit_price_ht"], it["tva_rate"], it["unit_price_ttc"], it["total_price"]
                ))

                # تحديث رصيد المادة والتكلفة المتوسطة PMP للإقامة
                art_cur = conn.execute("""
                    SELECT a.name, a.price_ttc,
                           COALESCE(ra.current_stock, a.current_stock) as current_stock,
                           COALESCE(ra.current_pmp, a.current_pmp, a.price_ttc) as current_pmp
                    FROM articles a
                    LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                    WHERE a.id = ?
                """, (r_id, it["article_id"]))
                art_row = art_cur.fetchone()
                old_stock = art_row["current_stock"] if art_row else 0.0
                old_pmp = (art_row["current_pmp"] if art_row else 0.0) or (art_row["price_ttc"] if art_row else it["unit_price_ttc"])
                new_stock = old_stock + it["quantity"]

                # معادلة PMP:
                if new_stock > 0:
                    new_pmp = ((old_stock * old_pmp) + (it["quantity"] * it["unit_price_ttc"])) / new_stock
                else:
                    new_pmp = it["unit_price_ttc"]

                if r_id == 1:
                    conn.execute("""
                        UPDATE articles 
                        SET current_stock = ?, current_pmp = ?
                        WHERE id = ?
                    """, (new_stock, new_pmp, it["article_id"]))

                conn.execute("""
                    INSERT INTO residence_articles (residence_id, article_id, current_stock, current_pmp)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(residence_id, article_id) DO UPDATE SET
                        current_stock = excluded.current_stock,
                        current_pmp = excluded.current_pmp
                """, (r_id, it["article_id"], new_stock, new_pmp))

                # إضافة حركة إلى سجل المراجعة مع تحديد الإقامة
                m_type = "SUPPLY_IN" if voucher_type == "SUPPLIER" else "LOAN_IN"
                conn.execute("""
                    INSERT INTO stock_movements (
                        date, article_id, movement_type, voucher_id,
                        qty_in, qty_out, unit_price, total_value, balance_after, residence_id
                    ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                """, (
                    v_date, it["article_id"], m_type, voucher_id,
                    it["quantity"], it["unit_price_ttc"], it["total_price"], new_stock, r_id
                ))

            conn.commit()
            from core.cache_service import CacheService
            CacheService.invalidate_articles(r_id)
            self._enqueue_sync("entry_voucher", "CREATE", voucher_id, {"voucher": voucher, "items": items})
            return voucher_id

    def get_next_voucher_number(self, voucher_kind: str = "ENTRY", year: Optional[int] = None) -> str:
        """
        توليد رقم تسلسلي تلقائي ومنظم للوصولات لمنع تكرار أو تداخل الأرقام
        (مثال: BE-2026-0001 أو BS-2026-0001)
        """
        target_year = year or datetime.date.today().year
        prefix = "BE" if voucher_kind.upper() == "ENTRY" else "BS"
        tbl = "entry_vouchers" if voucher_kind.upper() == "ENTRY" else "exit_vouchers"
        r_id = self.residence_id

        with self.db.get_connection() as conn:
            cur = conn.execute(f"""
                SELECT COUNT(*) FROM {tbl}
                WHERE (residence_id = ? OR residence_id IS NULL)
                  AND (date LIKE ? OR voucher_number LIKE ?)
            """, (r_id, f"{target_year}-%", f"{prefix}-{target_year}-%"))
            cnt = cur.fetchone()[0]
            next_num = cnt + 1
            return f"{prefix}-{target_year}-{next_num:04d}"

    # -------------------------------------------------------------
    # وصولات الإخراج والاستهلاك للمطبخ والإعارة (Exit Vouchers)
    # -------------------------------------------------------------
    def create_exit_voucher(self, voucher: Dict[str, Any], items: List[Dict[str, Any]]) -> int:
        """
        تسجيل وصل إخراج مع التحقق الصارم من توفر المخزون وخصم الكميات وحساب التكلفة
        """
        v_date = voucher["date"]
        voucher_type = voucher.get("voucher_type", "KITCHEN") # KITCHEN أو LOAN_OUT
        r_id = voucher.get("residence_id") or self.residence_id

        total_bf_cost = 0.0
        total_lu_cost = 0.0
        total_di_cost = 0.0
        total_voucher_cost = 0.0

        with self.db.get_connection() as conn:
            # 1. فحص كفاية المخزون أولاً لمنع الرصيد السالب بشكل قاطع
            check_stock_setting = self.db.get_setting("alert_on_negative_stock", "1") == "1"
            
            validated_items = []
            for it in items:
                art_id = it["article_id"]
                art_cur = conn.execute("""
                    SELECT a.name, a.price_ttc,
                           COALESCE(ra.current_stock, a.current_stock) as current_stock,
                           COALESCE(ra.current_pmp, a.current_pmp, a.price_ttc) as current_pmp
                    FROM articles a
                    LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                    WHERE a.id = ?
                """, (r_id, art_id))
                art_row = art_cur.fetchone()
                if not art_row:
                    continue

                q_bf = float(it.get("qty_breakfast", 0.0))
                q_lu = float(it.get("qty_lunch", 0.0))
                q_di = float(it.get("qty_dinner", 0.0))
                q_ot = float(it.get("qty_other", 0.0))
                tot_q = q_bf + q_lu + q_di + q_ot

                if tot_q <= 0:
                    continue

                avail = float(art_row["current_stock"] or 0.0)
                if check_stock_setting and tot_q > avail:
                    raise InsufficientStockError(art_row["name"], tot_q, avail)

                # تحديد السعر المعتمد (تعاقدي أو PMP)
                cost_mode = self.db.get_setting("cost_calculation_mode", "FIXED")
                unit_price = art_row["current_pmp"] if (cost_mode == "PMP" and art_row["current_pmp"] > 0) else art_row["price_ttc"]

                bf_cost = q_bf * unit_price
                lu_cost = q_lu * unit_price
                di_cost = q_di * unit_price
                tot_item_cost = tot_q * unit_price

                total_bf_cost += bf_cost
                total_lu_cost += lu_cost
                total_di_cost += di_cost
                total_voucher_cost += tot_item_cost

                validated_items.append({
                    "article_id": art_id,
                    "name": art_row["name"],
                    "current_stock": avail,
                    "qty_breakfast": q_bf,
                    "qty_lunch": q_lu,
                    "qty_dinner": q_di,
                    "qty_other": q_ot,
                    "total_qty": tot_q,
                    "unit_price_ttc": unit_price,
                    "total_cost": tot_item_cost
                })

            # 2. إنشاء رأس الوصل
            cur = conn.execute("""
                INSERT INTO exit_vouchers (
                    voucher_number, date, voucher_type, destination_residence,
                    total_breakfast_cost, total_lunch_cost, total_dinner_cost,
                    total_amount, notes, residence_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                voucher.get("voucher_number", f"BS-{v_date}"),
                v_date, voucher_type, voucher.get("destination_residence", ""),
                total_bf_cost, total_lu_cost, total_di_cost,
                total_voucher_cost, voucher.get("notes", ""),
                r_id
            ))
            voucher_id = cur.lastrowid

            # 3. تسجيل البنود وتحديث المخزون وسجل الحركات
            for it in validated_items:
                conn.execute("""
                    INSERT INTO exit_voucher_items (
                        voucher_id, article_id, qty_breakfast, qty_lunch,
                        qty_dinner, qty_other, total_qty, unit_price_ttc, total_cost
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    voucher_id, it["article_id"], it["qty_breakfast"], it["qty_lunch"],
                    it["qty_dinner"], it["qty_other"], it["total_qty"],
                    it["unit_price_ttc"], it["total_cost"]
                ))

                new_stock = it["current_stock"] - it["total_qty"]
                if r_id == 1:
                    conn.execute("UPDATE articles SET current_stock = ? WHERE id = ?", (new_stock, it["article_id"]))

                conn.execute("""
                    INSERT INTO residence_articles (residence_id, article_id, current_stock)
                    VALUES (?, ?, ?)
                    ON CONFLICT(residence_id, article_id) DO UPDATE SET
                        current_stock = excluded.current_stock
                """, (r_id, it["article_id"], new_stock))

                m_type = "KITCHEN_OUT" if voucher_type == "KITCHEN" else "LOAN_OUT"
                conn.execute("""
                    INSERT INTO stock_movements (
                        date, article_id, movement_type, voucher_id,
                        qty_in, qty_out, unit_price, total_value, balance_after, residence_id
                    ) VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
                """, (
                    v_date, it["article_id"], m_type, voucher_id,
                    it["total_qty"], it["unit_price_ttc"], it["total_cost"], new_stock, r_id
                ))

            # 4. تحديث المصاريف اليومية في جدول متابعة الوجبات لهذا اليوم آلياً
            if voucher_type == "KITCHEN":
                conn.execute("""
                    INSERT INTO daily_meals_tracking (date, residence_id, daily_food_expense)
                    VALUES (?, ?, ?)
                    ON CONFLICT(residence_id, date) DO UPDATE SET
                        daily_food_expense = daily_food_expense + excluded.daily_food_expense,
                        student_daily_cost = CASE 
                            WHEN average_daily_meals > 0 THEN (daily_food_expense + excluded.daily_food_expense) / (average_daily_meals * 2)
                            ELSE 0 
                        END
                """, (v_date, r_id, total_voucher_cost))

            conn.commit()
            from core.cache_service import CacheService
            CacheService.invalidate_articles(r_id)
            self._enqueue_sync("exit_voucher", "CREATE", voucher_id, {"voucher": voucher, "items": items})
            return voucher_id

    # -------------------------------------------------------------
    # تقارير وبطاقات المخزون (Inventory & Stock Cards)
    # -------------------------------------------------------------
    def get_stock_card(self, article_id: int, year: Optional[int] = None, month: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        توليد بطاقة المخزون الشهرية أو لفترة مخصصة لمادة معينة (مكافئ ورقة بطاقة مخزون)
        تعرض حركة الأيام مع تتبع الأرصدة التراكمية
        """
        if start_date and end_date:
            d_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            d_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            rep_year = year or d_start.year
            rep_month = month or d_start.month
        else:
            rep_year = year or datetime.date.today().year
            rep_month = month or datetime.date.today().month
            if rep_month in [1, 3, 5, 7, 8, 10, 12]:
                last_day = 31
            elif rep_month in [4, 6, 9, 11]:
                last_day = 30
            else:
                last_day = 29 if (rep_year % 4 == 0 and (rep_year % 100 != 0 or rep_year % 400 == 0)) else 28
            d_start = datetime.date(rep_year, rep_month, 1)
            d_end = datetime.date(rep_year, rep_month, last_day)

        start_date_str = d_start.isoformat()
        end_date_str = d_end.isoformat()

        with self.db.get_connection() as conn:
            art = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
            if not art:
                return {}

            # حساب رصيد بداية الفترة
            prior_in = conn.execute("""
                SELECT COALESCE(SUM(qty_in), 0) FROM stock_movements 
                WHERE article_id = ? AND date < ? AND residence_id = ?
            """, (article_id, start_date_str, self.residence_id)).fetchone()[0]
            prior_out = conn.execute("""
                SELECT COALESCE(SUM(qty_out), 0) FROM stock_movements 
                WHERE article_id = ? AND date < ? AND residence_id = ?
            """, (article_id, start_date_str, self.residence_id)).fetchone()[0]
            opening_stock = prior_in - prior_out

            # جلب تفاصيل حركات الفترة مقسمة بالأيام
            cur_sup = conn.execute("""
                SELECT ev.date, SUM(evi.quantity) as qty
                FROM entry_voucher_items evi
                JOIN entry_vouchers ev ON evi.voucher_id = ev.id
                WHERE evi.article_id = ? AND ev.voucher_type = 'SUPPLIER' AND ev.date BETWEEN ? AND ? AND ev.residence_id = ?
                GROUP BY ev.date
            """, (article_id, start_date_str, end_date_str, self.residence_id))
            sup_by_date = {r["date"]: r["qty"] for r in cur_sup.fetchall()}

            cur_li = conn.execute("""
                SELECT ev.date, SUM(evi.quantity) as qty
                FROM entry_voucher_items evi
                JOIN entry_vouchers ev ON evi.voucher_id = ev.id
                WHERE evi.article_id = ? AND ev.voucher_type = 'LOAN_IN' AND ev.date BETWEEN ? AND ? AND ev.residence_id = ?
                GROUP BY ev.date
            """, (article_id, start_date_str, end_date_str, self.residence_id))
            li_by_date = {r["date"]: r["qty"] for r in cur_li.fetchall()}

            cur_lo = conn.execute("""
                SELECT ev.date, SUM(evi.total_qty) as qty
                FROM exit_voucher_items evi
                JOIN exit_vouchers ev ON evi.voucher_id = ev.id
                WHERE evi.article_id = ? AND ev.voucher_type = 'LOAN_OUT' AND ev.date BETWEEN ? AND ? AND ev.residence_id = ?
                GROUP BY ev.date
            """, (article_id, start_date_str, end_date_str, self.residence_id))
            lo_by_date = {r["date"]: r["qty"] for r in cur_lo.fetchall()}

            cur_k = conn.execute("""
                SELECT ev.date, 
                       SUM(evi.qty_breakfast) as bf,
                       SUM(evi.qty_lunch) as lu,
                       SUM(evi.qty_dinner) as di
                FROM exit_voucher_items evi
                JOIN exit_vouchers ev ON evi.voucher_id = ev.id
                WHERE evi.article_id = ? AND ev.voucher_type = 'KITCHEN' AND ev.date BETWEEN ? AND ? AND ev.residence_id = ?
                GROUP BY ev.date
            """, (article_id, start_date_str, end_date_str, self.residence_id))
            k_by_date = {r["date"]: {"bf": r["bf"], "lu": r["lu"], "di": r["di"]} for r in cur_k.fetchall()}

            # بناء جدول الأيام مع تتبع الأرصدة
            running_stock = opening_stock
            daily_rows = []
            tot_sup = 0.0
            tot_li = 0.0
            tot_bf = 0.0
            tot_lu = 0.0
            tot_di = 0.0
            tot_lo = 0.0

            cur_d = d_start
            while cur_d <= d_end:
                d_str = cur_d.isoformat()
                d_day = cur_d.day
                sup = float(sup_by_date.get(d_str, 0.0))
                lin = float(li_by_date.get(d_str, 0.0))
                lout = float(lo_by_date.get(d_str, 0.0))
                k_data = k_by_date.get(d_str, {"bf": 0.0, "lu": 0.0, "di": 0.0})
                bf = float(k_data["bf"])
                lu = float(k_data["lu"])
                di = float(k_data["di"])

                init_stock = running_stock
                fin_stock = (init_stock + sup + lin) - (bf + lu + di + lout)
                running_stock = fin_stock

                tot_sup += sup
                tot_li += lin
                tot_bf += bf
                tot_lu += lu
                tot_di += di
                tot_lo += lout

                daily_rows.append({
                    "day": d_day,
                    "date": d_str,
                    "initial_stock": init_stock,
                    "supply_in": sup,
                    "loan_in": lin,
                    "bf_out": bf,
                    "lu_out": lu,
                    "di_out": di,
                    "loan_out": lout,
                    "kitchen_out": bf + lu + di,
                    "final_stock": fin_stock
                })
                cur_d += datetime.timedelta(days=1)

            return {
                "article": dict(art),
                "year": rep_year,
                "month": rep_month,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "opening_stock": opening_stock,
                "closing_stock": running_stock,
                "totals": {
                    "supply_in": tot_sup,
                    "loan_in": tot_li,
                    "bf_out": tot_bf,
                    "lu_out": tot_lu,
                    "di_out": tot_di,
                    "loan_out": tot_lo,
                    "total_out": tot_bf + tot_lu + tot_di + tot_lo
                },
                "days": daily_rows
            }

    def get_monthly_inventory(self, year: Optional[int] = None, month: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        توليد بطاقة الجرد لجميع المواد (مكافئ ورقة جرد)
        يدعم العرض الشهري الافتراضي أو فترة مخصصة من تاريخ إلى تاريخ
        """
        if start_date and end_date:
            d_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            d_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            rep_year = year or datetime.date.today().year
            rep_month = month or datetime.date.today().month
            if rep_month in [1, 3, 5, 7, 8, 10, 12]: last_day = 31
            elif rep_month in [4, 6, 9, 11]: last_day = 30
            else: last_day = 29 if (rep_year % 4 == 0 and (rep_year % 100 != 0 or rep_year % 400 == 0)) else 28
            d_start = datetime.date(rep_year, rep_month, 1)
            d_end = datetime.date(rep_year, rep_month, last_day)

        start_date_str = d_start.isoformat()
        end_date_str = d_end.isoformat()

        r_id = self.residence_id
        with self.db.get_connection() as conn:
            articles = conn.execute("SELECT * FROM articles WHERE is_active = 1 ORDER BY id ASC").fetchall()

            # 1. تجميع كل حركات ما قبل هذه الفترة لجميع المواد
            prior_moves = {
                r["article_id"]: (r["tot_in"] - r["tot_out"])
                for r in conn.execute("""
                    SELECT article_id,
                           COALESCE(SUM(qty_in), 0) as tot_in,
                           COALESCE(SUM(qty_out), 0) as tot_out
                    FROM stock_movements
                    WHERE date < ? AND residence_id = ?
                    GROUP BY article_id
                """, (start_date_str, r_id)).fetchall()
            }

            # 2. تجميع كل حركات الفترة لجميع المواد
            period_moves = {
                r["article_id"]: r
                for r in conn.execute("""
                    SELECT 
                        article_id,
                        COALESCE(SUM(CASE WHEN movement_type = 'SUPPLY_IN' THEN qty_in ELSE 0 END), 0) as sup_qty,
                        COALESCE(SUM(CASE WHEN movement_type = 'LOAN_IN' THEN qty_in ELSE 0 END), 0) as loan_in_qty,
                        COALESCE(SUM(CASE WHEN movement_type IN ('KITCHEN_OUT', 'BREAKFAST_OUT', 'LUNCH_OUT', 'DINNER_OUT') THEN qty_out ELSE 0 END), 0) as cons_qty,
                        COALESCE(SUM(CASE WHEN movement_type = 'LOAN_OUT' THEN qty_out ELSE 0 END), 0) as loan_out_qty
                    FROM stock_movements
                    WHERE date BETWEEN ? AND ? AND residence_id = ?
                    GROUP BY article_id
                """, (start_date_str, end_date_str, r_id)).fetchall()
            }

            inventory_rows = []
            for art in articles:
                art_id = art["id"]
                p_ttc = art["price_ttc"]

                init_qty = prior_moves.get(art_id, 0.0)
                m_row = period_moves.get(art_id)
                sup_qty = m_row["sup_qty"] if m_row else 0.0
                loan_in_qty = m_row["loan_in_qty"] if m_row else 0.0
                cons_qty = m_row["cons_qty"] if m_row else 0.0
                loan_out_qty = m_row["loan_out_qty"] if m_row else 0.0

                final_qty = (init_qty + sup_qty + loan_in_qty) - (cons_qty + loan_out_qty)

                inventory_rows.append({
                    "article_id": art_id,
                    "code": art["code"],
                    "name": art["name"],
                    "unit": art["unit"],
                    "price_ttc": p_ttc,
                    "initial_qty": init_qty,
                    "initial_val": init_qty * p_ttc,
                    "supply_qty": sup_qty,
                    "supply_val": sup_qty * p_ttc,
                    "loan_in_qty": loan_in_qty,
                    "loan_in_val": loan_in_qty * p_ttc,
                    "cons_qty": cons_qty,
                    "cons_val": cons_qty * p_ttc,
                    "loan_out_qty": loan_out_qty,
                    "loan_out_val": loan_out_qty * p_ttc,
                    "final_qty": final_qty,
                    "final_val": final_qty * p_ttc
                })

            return inventory_rows

    def get_low_stock_articles(self) -> List[Dict[str, Any]]:
        """المواد التي اقترب مخزونها من الحد الأدنى أو نفدت للتنبيه الفوري"""
        with self.db.get_connection() as conn:
            cur = conn.execute("""
                SELECT a.*, c.name as category_name
                FROM articles a
                LEFT JOIN categories c ON a.category_id = c.id
                WHERE a.is_active = 1 AND a.current_stock <= a.safety_stock
                ORDER BY a.current_stock ASC
            """)
            return [dict(r) for r in cur.fetchall()]

    def get_dashboard_kpis(self) -> Dict[str, Any]:
        """إحصائيات لوحة التحكم السريعة"""
        with self.db.get_connection() as conn:
            tot_articles = conn.execute("SELECT COUNT(*) FROM articles WHERE is_active = 1").fetchone()[0]
            tot_val = conn.execute("SELECT SUM(current_stock * price_ttc) FROM articles WHERE is_active = 1").fetchone()[0] or 0.0
            low_stock_count = conn.execute("SELECT COUNT(*) FROM articles WHERE is_active = 1 AND current_stock <= safety_stock").fetchone()[0]
            
            today_str = datetime.date.today().isoformat()
            today_expense = conn.execute("SELECT COALESCE(daily_food_expense, 0) FROM daily_meals_tracking WHERE date = ?", (today_str,)).fetchone()
            today_exp_val = today_expense[0] if today_expense else 0.0

            return {
                "total_articles": tot_articles,
                "total_stock_value": tot_val,
                "low_stock_alerts": low_stock_count,
                "today_expense": today_exp_val
            }

    # -------------------------------------------------------------
    # 7. ورقة اليوم الواحد المتكاملة (Sheets 01-31 في Excel)
    # -------------------------------------------------------------
    def get_daily_sheet_data(self, date_str: str, residence_id: Optional[int] = None) -> Dict[str, Any]:
        """جلب جميع بيانات ورقة اليوم: المواد، المخزون، الحركات، التذاكر، وقائمة الطعام"""
        r_id = residence_id or self.residence_id
        with self.db.get_connection() as conn:
            # 1. قائمة كل المواد الخاصة بهذه الإقامة
            articles = conn.execute("""
                SELECT a.id, a.code, a.name, a.unit, a.price_ttc,
                       COALESCE(ra.current_stock, a.current_stock) as current_stock,
                       COALESCE(ra.initial_stock, a.initial_stock) as initial_stock
                FROM articles a
                LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                WHERE a.is_active = 1 ORDER BY a.id ASC
            """, (r_id,)).fetchall()

            # 2. الحركات المسجلة في هذا اليوم
            # خروج المطبخ (فطور، غداء، عشاء)
            kitchen_items = {}
            k_cur = conn.execute("""
                SELECT evi.article_id, evi.qty_breakfast, evi.qty_lunch, evi.qty_dinner, evi.qty_other, evi.unit_price_ttc
                FROM exit_voucher_items evi
                JOIN exit_vouchers ev ON evi.voucher_id = ev.id
                WHERE ev.date = ? AND ev.voucher_type = 'KITCHEN' AND ev.residence_id = ?
            """, (date_str, r_id))
            for r in k_cur.fetchall():
                kitchen_items[r["article_id"]] = {
                    "bf": r["qty_breakfast"], "lu": r["qty_lunch"],
                    "di": r["qty_dinner"], "other": r["qty_other"]
                }

            # إعارة خارجية (LOAN_OUT)
            loan_out_items = {}
            lo_cur = conn.execute("""
                SELECT evi.article_id, SUM(evi.total_qty) as total_lo
                FROM exit_voucher_items evi
                JOIN exit_vouchers ev ON evi.voucher_id = ev.id
                WHERE ev.date = ? AND ev.voucher_type = 'LOAN_OUT' AND ev.residence_id = ?
                GROUP BY evi.article_id
            """, (date_str, r_id))
            for r in lo_cur.fetchall():
                loan_out_items[r["article_id"]] = r["total_lo"]

            # توريد اليوم (SUPPLY)
            supply_items = {}
            sup_cur = conn.execute("""
                SELECT evi.article_id, SUM(evi.quantity) as total_sup
                FROM entry_voucher_items evi
                JOIN entry_vouchers ev ON evi.voucher_id = ev.id
                WHERE ev.date = ? AND ev.voucher_type = 'SUPPLIER' AND ev.residence_id = ?
                GROUP BY evi.article_id
            """, (date_str, r_id))
            for r in sup_cur.fetchall():
                supply_items[r["article_id"]] = r["total_sup"]

            # استعارة اليوم (LOAN_IN)
            loan_in_items = {}
            li_cur = conn.execute("""
                SELECT evi.article_id, SUM(evi.quantity) as total_li
                FROM entry_voucher_items evi
                JOIN entry_vouchers ev ON evi.voucher_id = ev.id
                WHERE ev.date = ? AND ev.voucher_type = 'LOAN_IN' AND ev.residence_id = ?
                GROUP BY evi.article_id
            """, (date_str, r_id))
            for r in li_cur.fetchall():
                loan_in_items[r["article_id"]] = r["total_li"]

            # حساب مخزون بداية هذا اليوم دفعة واحدة لجميع المواد
            prior_moves = {
                r["article_id"]: (r["tot_in"] - r["tot_out"])
                for r in conn.execute("""
                    SELECT article_id,
                           COALESCE(SUM(qty_in), 0) as tot_in,
                           COALESCE(SUM(qty_out), 0) as tot_out
                    FROM stock_movements
                    WHERE date < ? AND residence_id = ?
                    GROUP BY article_id
                """, (date_str, r_id)).fetchall()
            }

            articles_rows = []
            tot_bf_expense = 0.0
            tot_lu_expense = 0.0
            tot_di_expense = 0.0

            for a in articles:
                art_id = a["id"]
                p_ttc = a["price_ttc"]

                init_base = a["initial_stock"] or 0.0
                initial_day_stock = init_base + prior_moves.get(art_id, 0.0)

                sup_qty = supply_items.get(art_id, 0.0)
                li_qty = loan_in_items.get(art_id, 0.0)

                k_info = kitchen_items.get(art_id, {"bf": 0.0, "lu": 0.0, "di": 0.0, "other": 0.0})
                bf_qty = k_info["bf"]
                lu_qty = k_info["lu"]
                di_qty = k_info["di"]
                lo_qty = loan_out_items.get(art_id, 0.0) + k_info["other"]

                final_day_stock = initial_day_stock + sup_qty + li_qty - (bf_qty + lu_qty + di_qty + lo_qty)

                cost_bf = bf_qty * p_ttc
                cost_lu = lu_qty * p_ttc
                cost_di = di_qty * p_ttc

                tot_bf_expense += cost_bf
                tot_lu_expense += cost_lu
                tot_di_expense += cost_di

                articles_rows.append({
                    "id": art_id,
                    "code": a["code"] or "",
                    "name": a["name"],
                    "unit": a["unit"],
                    "price_ttc": p_ttc,
                    "initial_stock": initial_day_stock,
                    "supply_qty": sup_qty,
                    "loan_in_qty": li_qty,
                    "bf_qty": bf_qty,
                    "lu_qty": lu_qty,
                    "di_qty": di_qty,
                    "loan_out_qty": lo_qty,
                    "final_stock": final_day_stock,
                    "cost_bf": cost_bf,
                    "cost_lu": cost_lu,
                    "cost_di": cost_di,
                    "total_expense": cost_bf + cost_lu + cost_di
                })

            grand_total_expense = tot_bf_expense + tot_lu_expense + tot_di_expense

            # 3. إحصائيات التذاكر وقائمة الطعام
            meal_cur = conn.execute("SELECT * FROM daily_meals_tracking WHERE date = ? AND residence_id = ?", (date_str, r_id))
            meal_row = meal_cur.fetchone()
            meal_data = dict(meal_row) if meal_row else {
                "date": date_str,
                "residence_id": r_id,
                "bf_students": 0, "bf_staff": 0, "bf_professors": 0, "bf_guests": 0, "bf_free": 0, "bf_total": 0,
                "lu_students": 0, "lu_staff": 0, "lu_professors": 0, "lu_guests": 0, "lu_free": 0, "lu_total": 0,
                "di_students": 0, "di_staff": 0, "di_professors": 0, "di_guests": 0, "di_free": 0, "di_total": 0,
                "average_daily_meals": 0.0,
                "daily_food_expense": grand_total_expense,
                "student_daily_cost": 0.0,
                "menu_breakfast": "", "menu_lunch": "", "menu_dinner": ""
            }

            if grand_total_expense == 0 and meal_data.get("daily_food_expense", 0) > 0:
                tot_bf_expense = float(meal_data.get("bf_expense") or 0.0)
                tot_lu_expense = float(meal_data.get("lu_expense") or 0.0)
                tot_di_expense = float(meal_data.get("di_expense") or 0.0)
                grand_total_expense = float(meal_data.get("daily_food_expense") or (tot_bf_expense + tot_lu_expense + tot_di_expense))

            return {
                "date": date_str,
                "residence_id": r_id,
                "articles": articles_rows,
                "tot_bf_expense": tot_bf_expense,
                "tot_lu_expense": tot_lu_expense,
                "tot_di_expense": tot_di_expense,
                "grand_total_expense": grand_total_expense,
                "meals": meal_data
            }

    def save_daily_sheet_full(self, date_str: str, articles_input: List[Dict[str, Any]], tickets_input: Optional[Dict[str, Any]] = None, menu_input: Optional[Dict[str, str]] = None, residence_id: Optional[int] = None) -> None:
        """حفظ ورقة اليوم بالكامل: الاستهلاك، التوريد، التذاكر، وتحديث الأرصدة دفعة واحدة"""
        r_id = residence_id or self.residence_id
        with self.db.get_connection() as conn:
            # 1. معالجة خروج المطبخ (KITCHEN)
            kitchen_items = [it for it in articles_input if (it.get("bf_qty", 0) > 0 or it.get("lu_qty", 0) > 0 or it.get("di_qty", 0) > 0)]
            
            # حذف وصولات الاستهلاك السابقة لهذا اليوم لإعادة بنائها بدقة
            old_ev = conn.execute("SELECT id FROM exit_vouchers WHERE date = ? AND voucher_type = 'KITCHEN' AND residence_id = ?", (date_str, r_id)).fetchall()
            for r in old_ev:
                conn.execute("DELETE FROM exit_voucher_items WHERE voucher_id = ?", (r["id"],))
                conn.execute("DELETE FROM exit_vouchers WHERE id = ?", (r["id"],))
                conn.execute("DELETE FROM stock_movements WHERE voucher_id = ? AND movement_type IN ('BREAKFAST_OUT', 'LUNCH_OUT', 'DINNER_OUT') AND residence_id = ?", (r["id"], r_id))

            if kitchen_items:
                tot_bf = sum(it.get("bf_qty", 0) * it["price_ttc"] for it in kitchen_items)
                tot_lu = sum(it.get("lu_qty", 0) * it["price_ttc"] for it in kitchen_items)
                tot_di = sum(it.get("di_qty", 0) * it["price_ttc"] for it in kitchen_items)
                tot_k = tot_bf + tot_lu + tot_di

                v_num = f"BS-{r_id}-{date_str}-KITCHEN"
                cur = conn.execute("""
                    INSERT INTO exit_vouchers (
                        voucher_number, date, voucher_type, residence_id,
                        total_breakfast_cost, total_lunch_cost, total_dinner_cost, total_amount, notes
                    ) VALUES (?, ?, 'KITCHEN', ?, ?, ?, ?, ?, 'استهلاك ورقة اليوم')
                """, (v_num, date_str, r_id, tot_bf, tot_lu, tot_di, tot_k))
                voucher_id = cur.lastrowid

                for it in kitchen_items:
                    bf = float(it.get("bf_qty", 0))
                    lu = float(it.get("lu_qty", 0))
                    di = float(it.get("di_qty", 0))
                    t_qty = bf + lu + di
                    p = float(it["price_ttc"])
                    t_cost = t_qty * p

                    conn.execute("""
                        INSERT INTO exit_voucher_items (
                            voucher_id, article_id, qty_breakfast, qty_lunch, qty_dinner, qty_other,
                            total_qty, unit_price_ttc, total_cost
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
                    """, (voucher_id, it["id"], bf, lu, di, t_qty, p, t_cost))

                    if bf > 0:
                        conn.execute("""
                            INSERT INTO stock_movements (date, article_id, movement_type, voucher_id, residence_id, qty_in, qty_out, unit_price, total_value, balance_after)
                            VALUES (?, ?, 'BREAKFAST_OUT', ?, ?, 0, ?, ?, ?, 0)
                        """, (date_str, it["id"], voucher_id, r_id, bf, p, bf * p))
                    if lu > 0:
                        conn.execute("""
                            INSERT INTO stock_movements (date, article_id, movement_type, voucher_id, residence_id, qty_in, qty_out, unit_price, total_value, balance_after)
                            VALUES (?, ?, 'LUNCH_OUT', ?, ?, 0, ?, ?, ?, 0)
                        """, (date_str, it["id"], voucher_id, r_id, lu, p, lu * p))
                    if di > 0:
                        conn.execute("""
                            INSERT INTO stock_movements (date, article_id, movement_type, voucher_id, residence_id, qty_in, qty_out, unit_price, total_value, balance_after)
                            VALUES (?, ?, 'DINNER_OUT', ?, ?, 0, ?, ?, ?, 0)
                        """, (date_str, it["id"], voucher_id, r_id, di, p, di * p))

            # 2. ملاحظة هامة: الإعارة (LOAN_OUT) والاستعارة (LOAN_IN) تدار حصرياً ومباشرة
            # عبر نظام "حركة الإعارة والاستعارة بين الإقامات" لضمان التحويل التبادلي الآلي للرصيد
            # ولا يتم مسحها أو استبدالها من ورقة الاستهلاك اليومي.

            # 3. معالجة التوريد (SUPPLY)
            supply_items = [it for it in articles_input if it.get("supply_qty", 0) > 0]
            old_sup = conn.execute("""
                SELECT id FROM entry_vouchers 
                WHERE date = ? AND voucher_type = 'SUPPLIER' AND residence_id = ?
                  AND (delivery_note_ref = 'AUTO-DAILY' 
                       OR voucher_number LIKE 'BE-%-SUP%' 
                       OR voucher_number LIKE 'BE-SUPP-%'
                       OR notes LIKE '%ورقة اليوم%'
                       OR notes LIKE '%إكسل%')
            """, (date_str, r_id)).fetchall()

            for r in old_sup:
                conn.execute("DELETE FROM entry_voucher_items WHERE voucher_id = ?", (r["id"],))
                conn.execute("DELETE FROM entry_vouchers WHERE id = ?", (r["id"],))
                conn.execute("DELETE FROM stock_movements WHERE voucher_id = ? AND movement_type = 'SUPPLY_IN' AND residence_id = ?", (r["id"], r_id))

            if supply_items:
                tot_sup = sum(it["supply_qty"] * it["price_ttc"] for it in supply_items)
                cur = conn.execute("""
                    INSERT INTO entry_vouchers (voucher_number, date, voucher_type, residence_id, delivery_note_ref, total_amount, notes)
                    VALUES (?, ?, 'SUPPLIER', ?, 'AUTO-DAILY', ?, 'توريد ورقة اليوم')
                """, (f"BE-{r_id}-{date_str}-SUP", date_str, r_id, tot_sup))
                sup_id = cur.lastrowid
                for it in supply_items:
                    q = float(it["supply_qty"])
                    p = float(it["price_ttc"])
                    conn.execute("""
                        INSERT INTO entry_voucher_items (voucher_id, article_id, quantity, unit_price_ttc, total_price)
                        VALUES (?, ?, ?, ?, ?)
                    """, (sup_id, it["id"], q, p, q * p))
                    conn.execute("""
                        INSERT INTO stock_movements (date, article_id, movement_type, voucher_id, residence_id, qty_in, qty_out, unit_price, total_value, balance_after)
                        VALUES (?, ?, 'SUPPLY_IN', ?, ?, ?, 0, ?, ?, 0)
                    """, (date_str, it["id"], sup_id, r_id, q, p, q * p))

            # 4. تحديث الأرصدة الحالية في جدول residence_articles وجدول articles دفعة واحدة (Batch High Performance)
            inits_map = {
                r["article_id"]: r["initial_stock"]
                for r in conn.execute("SELECT article_id, initial_stock FROM residence_articles WHERE residence_id = ?", (r_id,)).fetchall()
            }
            moves_map = {
                r["article_id"]: (r["tot_in"], r["tot_out"])
                for r in conn.execute("""
                    SELECT article_id, COALESCE(SUM(qty_in), 0) as tot_in, COALESCE(SUM(qty_out), 0) as tot_out
                    FROM stock_movements WHERE residence_id = ? GROUP BY article_id
                """, (r_id,)).fetchall()
            }
            batch_updates = []
            for it in articles_input:
                art_id = it["id"]
                init_stk = inits_map.get(art_id, 0.0)
                tot_in, tot_out = moves_map.get(art_id, (0.0, 0.0))
                new_current = init_stk + tot_in - tot_out
                batch_updates.append((r_id, art_id, init_stk, new_current, it.get("safety_stock", 0.0), it["price_ttc"]))

            conn.executemany("""
                INSERT INTO residence_articles (residence_id, article_id, initial_stock, current_stock, safety_stock, current_pmp)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(residence_id, article_id) DO UPDATE SET current_stock = excluded.current_stock
            """, batch_updates)

            if r_id == 1:
                conn.executemany("UPDATE articles SET current_stock = ? WHERE id = ?", [(b[3], b[1]) for b in batch_updates])

            # 5. حفظ بيانات التذاكر والمعدلات وقائمة الطعام
            exp_val = sum(it.get("bf_qty", 0) * it["price_ttc"] + it.get("lu_qty", 0) * it["price_ttc"] + it.get("di_qty", 0) * it["price_ttc"] for it in kitchen_items)
            existing_meal = conn.execute("SELECT id, average_daily_meals FROM daily_meals_tracking WHERE date = ? AND residence_id = ?", (date_str, r_id)).fetchone()

            if tickets_input is not None:
                bf_tot = tickets_input.get("bf_students", 0) + tickets_input.get("bf_staff", 0) + tickets_input.get("bf_professors", 0) + tickets_input.get("bf_guests", 0) + tickets_input.get("bf_free", 0)
                lu_tot = tickets_input.get("lu_students", 0) + tickets_input.get("lu_staff", 0) + tickets_input.get("lu_professors", 0) + tickets_input.get("lu_guests", 0) + tickets_input.get("lu_free", 0)
                di_tot = tickets_input.get("di_students", 0) + tickets_input.get("di_staff", 0) + tickets_input.get("di_professors", 0) + tickets_input.get("di_guests", 0) + tickets_input.get("di_free", 0)

                avg_m = (lu_tot + di_tot) / 2.0 if di_tot > 0 else float(lu_tot)
                cost_stud = (exp_val / avg_m / 2.0) if avg_m > 0 else 0.0
                menu_in = menu_input or {}

                if existing_meal:
                    conn.execute("""
                        UPDATE daily_meals_tracking SET
                            bf_students = ?, bf_staff = ?, bf_professors = ?, bf_guests = ?, bf_free = ?, bf_total = ?,
                            lu_students = ?, lu_staff = ?, lu_professors = ?, lu_guests = ?, lu_free = ?, lu_total = ?,
                            di_students = ?, di_staff = ?, di_professors = ?, di_guests = ?, di_free = ?, di_total = ?,
                            average_daily_meals = ?, daily_food_expense = ?, student_daily_cost = ?,
                            menu_breakfast = ?, menu_lunch = ?, menu_dinner = ?
                        WHERE id = ?
                    """, (
                        tickets_input.get("bf_students", 0), tickets_input.get("bf_staff", 0), tickets_input.get("bf_professors", 0), tickets_input.get("bf_guests", 0), tickets_input.get("bf_free", 0), bf_tot,
                        tickets_input.get("lu_students", 0), tickets_input.get("lu_staff", 0), tickets_input.get("lu_professors", 0), tickets_input.get("lu_guests", 0), tickets_input.get("lu_free", 0), lu_tot,
                        tickets_input.get("di_students", 0), tickets_input.get("di_staff", 0), tickets_input.get("di_professors", 0), tickets_input.get("di_guests", 0), tickets_input.get("di_free", 0), di_tot,
                        avg_m, exp_val, cost_stud,
                        menu_in.get("menu_breakfast", ""), menu_in.get("menu_lunch", ""), menu_in.get("menu_dinner", ""),
                        existing_meal["id"]
                    ))
                else:
                    conn.execute("""
                        INSERT INTO daily_meals_tracking (
                            date, residence_id,
                            bf_students, bf_staff, bf_professors, bf_guests, bf_free, bf_total,
                            lu_students, lu_staff, lu_professors, lu_guests, lu_free, lu_total,
                            di_students, di_staff, di_professors, di_guests, di_free, di_total,
                            average_daily_meals, daily_food_expense, student_daily_cost,
                            menu_breakfast, menu_lunch, menu_dinner
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date_str, r_id,
                        tickets_input.get("bf_students", 0), tickets_input.get("bf_staff", 0), tickets_input.get("bf_professors", 0), tickets_input.get("bf_guests", 0), tickets_input.get("bf_free", 0), bf_tot,
                        tickets_input.get("lu_students", 0), tickets_input.get("lu_staff", 0), tickets_input.get("lu_professors", 0), tickets_input.get("lu_guests", 0), tickets_input.get("lu_free", 0), lu_tot,
                        tickets_input.get("di_students", 0), tickets_input.get("di_staff", 0), tickets_input.get("di_professors", 0), tickets_input.get("di_guests", 0), tickets_input.get("di_free", 0), di_tot,
                        avg_m, exp_val, cost_stud,
                        menu_in.get("menu_breakfast", ""), menu_in.get("menu_lunch", ""), menu_in.get("menu_dinner", "")
                    ))
            else:
                # إذا كانت tickets_input فارغة أو None نحدث المصاريف فقط ونحافظ على التذاكر وقائمة الطعام السابقة
                if existing_meal:
                    avg_m = existing_meal["average_daily_meals"] or 0.0
                    cost_stud = (exp_val / avg_m / 2.0) if avg_m > 0 else 0.0
                    conn.execute("UPDATE daily_meals_tracking SET daily_food_expense = ?, student_daily_cost = ? WHERE id = ?", (exp_val, cost_stud, existing_meal["id"]))
                else:
                    conn.execute("""
                        INSERT INTO daily_meals_tracking (date, residence_id, daily_food_expense, student_daily_cost)
                        VALUES (?, ?, ?, 0.0)
                    """, (date_str, r_id, exp_val))

            conn.commit()

        self._enqueue_sync("daily_sheet_full", "UPSERT", f"{r_id}_{date_str}", {
            "date": date_str,
            "articles": articles_input,
            "tickets": tickets_input,
            "menus": menu_input
        }, residence_id=r_id)

    def save_daily_general_info(self, date_str: str, tickets_input: Dict[str, Any], menu_input: Dict[str, str], expenses_input: Optional[Dict[str, float]] = None, residence_id: Optional[int] = None) -> None:
        """حفظ بيانات واجهة معلومات عامة: التذاكر، قوائم الوجبات، وتحديث التكاليف بناءً على مصاريف استهلاك اليوم"""
        r_id = residence_id or self.residence_id
        with self.db.get_connection() as conn:
            bf_tot = sum(int(tickets_input.get(f"bf_{k}", 0)) for k in ["students", "staff", "professors", "guests", "free"])
            lu_tot = sum(int(tickets_input.get(f"lu_{k}", 0)) for k in ["students", "staff", "professors", "guests", "free"])
            di_tot = sum(int(tickets_input.get(f"di_{k}", 0)) for k in ["students", "staff", "professors", "guests", "free"])

            avg_m = (lu_tot + di_tot) / 2.0 if (lu_tot + di_tot) > 0 else 0.0

            if expenses_input:
                bf_exp = float(expenses_input.get("bf_expense", 0.0))
                lu_exp = float(expenses_input.get("lu_expense", 0.0))
                di_exp = float(expenses_input.get("di_expense", 0.0))
                exp_val = float(expenses_input.get("grand_total", bf_exp + lu_exp + di_exp))
            else:
                # جلب مصاريف اليوم المسجلة في وصولات المطبخ KITCHEN
                exp_row = conn.execute("""
                    SELECT COALESCE(SUM(total_amount), 0),
                           COALESCE(SUM(total_breakfast_cost), 0),
                           COALESCE(SUM(total_lunch_cost), 0),
                           COALESCE(SUM(total_dinner_cost), 0)
                    FROM exit_vouchers 
                    WHERE date = ? AND voucher_type = 'KITCHEN' AND residence_id = ?
                """, (date_str, r_id)).fetchone()
                exp_val = float(exp_row[0]) if exp_row else 0.0
                bf_exp = float(exp_row[1]) if exp_row else 0.0
                lu_exp = float(exp_row[2]) if exp_row else 0.0
                di_exp = float(exp_row[3]) if exp_row else 0.0

            cost_stud = (exp_val / avg_m / 2.0) if avg_m > 0 else 0.0

            existing = conn.execute("SELECT id FROM daily_meals_tracking WHERE date = ? AND residence_id = ?", (date_str, r_id)).fetchone()
            if existing:
                conn.execute("""
                    UPDATE daily_meals_tracking SET
                        bf_students = ?, bf_staff = ?, bf_professors = ?, bf_guests = ?, bf_free = ?, bf_total = ?,
                        lu_students = ?, lu_staff = ?, lu_professors = ?, lu_guests = ?, lu_free = ?, lu_total = ?,
                        di_students = ?, di_staff = ?, di_professors = ?, di_guests = ?, di_free = ?, di_total = ?,
                        average_daily_meals = ?, daily_food_expense = ?, student_daily_cost = ?,
                        menu_breakfast = ?, menu_lunch = ?, menu_dinner = ?,
                        bf_expense = ?, lu_expense = ?, di_expense = ?
                    WHERE id = ?
                """, (
                    int(tickets_input.get("bf_students", 0)), int(tickets_input.get("bf_staff", 0)), int(tickets_input.get("bf_professors", 0)), int(tickets_input.get("bf_guests", 0)), int(tickets_input.get("bf_free", 0)), bf_tot,
                    int(tickets_input.get("lu_students", 0)), int(tickets_input.get("lu_staff", 0)), int(tickets_input.get("lu_professors", 0)), int(tickets_input.get("lu_guests", 0)), int(tickets_input.get("lu_free", 0)), lu_tot,
                    int(tickets_input.get("di_students", 0)), int(tickets_input.get("di_staff", 0)), int(tickets_input.get("di_professors", 0)), int(tickets_input.get("di_guests", 0)), int(tickets_input.get("di_free", 0)), di_tot,
                    avg_m, exp_val, cost_stud,
                    menu_input.get("menu_breakfast", ""), menu_input.get("menu_lunch", ""), menu_input.get("menu_dinner", ""),
                    bf_exp, lu_exp, di_exp,
                    existing["id"]
                ))
            else:
                conn.execute("""
                    INSERT INTO daily_meals_tracking (
                        date, residence_id,
                        bf_students, bf_staff, bf_professors, bf_guests, bf_free, bf_total,
                        lu_students, lu_staff, lu_professors, lu_guests, lu_free, lu_total,
                        di_students, di_staff, di_professors, di_guests, di_free, di_total,
                        average_daily_meals, daily_food_expense, student_daily_cost,
                        menu_breakfast, menu_lunch, menu_dinner,
                        bf_expense, lu_expense, di_expense
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date_str, r_id,
                    int(tickets_input.get("bf_students", 0)), int(tickets_input.get("bf_staff", 0)), int(tickets_input.get("bf_professors", 0)), int(tickets_input.get("bf_guests", 0)), int(tickets_input.get("bf_free", 0)), bf_tot,
                    int(tickets_input.get("lu_students", 0)), int(tickets_input.get("lu_staff", 0)), int(tickets_input.get("lu_professors", 0)), int(tickets_input.get("lu_guests", 0)), int(tickets_input.get("lu_free", 0)), lu_tot,
                    int(tickets_input.get("di_students", 0)), int(tickets_input.get("di_staff", 0)), int(tickets_input.get("di_professors", 0)), int(tickets_input.get("di_guests", 0)), int(tickets_input.get("di_free", 0)), di_tot,
                    avg_m, exp_val, cost_stud,
                    menu_input.get("menu_breakfast", ""), menu_input.get("menu_lunch", ""), menu_input.get("menu_dinner", ""),
                    bf_exp, lu_exp, di_exp
                ))
            conn.commit()

    # -------------------------------------------------------------
    # 8. شبكات التتبع الشهرية (أوراق: نوريد، إستعارة، إستهلاك، عارة)
    # -------------------------------------------------------------
    def get_monthly_movement_matrix(self, year: int, month: int, matrix_type: str) -> Dict[str, Any]:
        """
        مصفوفة 31 يوماً مطابقة لأوراق الإكسل:
        matrix_type: 'SUPPLY' (نوريد), 'LOAN_IN' (إستعارة), 'CONSUMPTION' (إستهلاك), 'LOAN_OUT' (عارة)
        """
        import calendar
        num_days = calendar.monthrange(year, month)[1]

        articles = self.get_articles(only_active=True, residence_id=self.residence_id)

        start_date = f"{year:04d}-{month:02d}-01"
        end_date = f"{year:04d}-{month:02d}-{num_days:02d}"

        # تحديد أنواع الحركات
        if matrix_type == "SUPPLY":
            mv_types = ("'SUPPLY_IN'",)
            is_in = True
        elif matrix_type == "LOAN_IN":
            mv_types = ("'LOAN_IN'",)
            is_in = True
        elif matrix_type == "CONSUMPTION":
            mv_types = ("'BREAKFAST_OUT'", "'LUNCH_OUT'", "'DINNER_OUT'", "'KITCHEN_OUT'")
            is_in = False
        elif matrix_type == "LOAN_OUT":
            mv_types = ("'LOAN_OUT'",)
            is_in = False
        else:
            mv_types = ("'SUPPLY_IN'",)
            is_in = True

        qty_col = "qty_in" if is_in else "qty_out"
        r_id = self.residence_id
        sql = f"""
            SELECT article_id, strftime('%d', date) as day_num, SUM({qty_col}) as day_qty
            FROM stock_movements
            WHERE date >= ? AND date <= ? AND movement_type IN ({','.join(mv_types)})
              AND (residence_id = ? OR residence_id IS NULL)
            GROUP BY article_id, day_num
        """
        with self.db.get_connection() as conn:
            cur = conn.execute(sql, (start_date, end_date, r_id))
            moves = cur.fetchall()

            # خريطة: (art_id, day_int) -> qty
            move_map = {}
            for r in moves:
                art_id = r["article_id"]
                day_int = int(r["day_num"])
                move_map[(art_id, day_int)] = r["day_qty"]

            matrix_rows = []
            daily_totals = {d: 0.0 for d in range(1, num_days + 1)}
            grand_total_qty = 0.0
            grand_total_val = 0.0

            for a in articles:
                art_id = a["id"]
                p = a["price_ttc"]
                days_dict = {}
                row_qty = 0.0

                for d in range(1, num_days + 1):
                    q = move_map.get((art_id, d), 0.0)
                    days_dict[d] = q
                    row_qty += q
                    daily_totals[d] += q

                row_val = row_qty * p
                grand_total_qty += row_qty
                grand_total_val += row_val

                matrix_rows.append({
                    "id": art_id,
                    "code": a["code"] or "",
                    "name": a["name"],
                    "unit": a["unit"],
                    "price_ttc": p,
                    "days": days_dict,
                    "total_qty": row_qty,
                    "total_val": row_val
                })

            return {
                "year": year,
                "month": month,
                "num_days": num_days,
                "matrix_type": matrix_type,
                "articles": matrix_rows,
                "daily_totals": daily_totals,
                "grand_total_qty": grand_total_qty,
                "grand_total_val": grand_total_val
            }

    # -------------------------------------------------------------
    # 9. الجدول التفصيلي الشهري (ورقة جدول تفصيلي في Excel)
    # -------------------------------------------------------------
    def get_detailed_table(self, year: Optional[int] = None, month: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        الجدول التفصيلي الرقابي الشهري أو لفترة مخصصة:
        المواد | الوحدة | مخزون أول الشهر | المدخولات (توريد + إستعارة) | المخروجات (إستهلاك + إعارة) | باقي المخزون
        """
        jard = self.get_monthly_inventory(year, month, start_date=start_date, end_date=end_date)
        detailed_rows = []
        for it in jard:
            detailed_rows.append({
                "name": it["name"],
                "unit": it["unit"],
                "initial_stock": it["initial_qty"],
                "supply_in": it["supply_qty"],
                "loan_in": it["loan_in_qty"],
                "total_in": it["supply_qty"] + it["loan_in_qty"],
                "cons_out": it["cons_qty"],
                "loan_out": it["loan_out_qty"],
                "total_out": it["cons_qty"] + it["loan_out_qty"],
                "final_stock": it["final_qty"],
                "price_ttc": it["price_ttc"],
                "final_val": it["final_val"]
            })
        return detailed_rows

    # -------------------------------------------------------------
    # 10. وضعية الحصص الثلاثية والموردين (ملف عبد الحميد الوضعية.xlsx)
    # -------------------------------------------------------------
    def get_trimester_situation(self, year: Optional[int] = None, trimester: Optional[int] = None, supplier_id: Optional[int] = None, lot_name: Optional[str] = None, residence_id: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        وضعية المدخولات للثلاثي (1، 2، 3) أو لفترة مخصصة ومقارنتها مع حصص المديرية:
        الحصة الممنوحة vs المدخولات الفعلية + الفوارق بالكمية والمبلغ
        مطابقة 100% لملف عبد الحميد الوضعية.xlsx المعتمد في مديرية الخدمات الجامعية
        """
        r_id = residence_id or self.residence_id
        if start_date and end_date:
            d_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            d_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            rep_year = year or d_start.year
            t_name = f"الفترة الممتدة من {start_date} إلى {end_date}"
            start_date_str = start_date
            end_date_str = end_date
        else:
            rep_year = year or datetime.date.today().year
            tri = trimester or 1
            if tri == 1:
                months = (1, 2, 3)
                t_name = "الثلاثي الأول"
            elif tri == 2:
                months = (4, 5, 6)
                t_name = "الثلاثي الثاني"
            else:
                months = (7, 8, 9, 10, 11, 12)
                t_name = "الثلاثي الثالث"

            start_date_str = f"{rep_year:04d}-{months[0]:02d}-01"
            import calendar
            last_m = months[-1]
            last_d = calendar.monthrange(rep_year, last_m)[1]
            end_date_str = f"{rep_year:04d}-{last_m:02d}-{last_d:02d}"

        with self.db.get_connection() as conn:
            # 1. قائمة الحصص المتوفرة لملء قائمة التصفية
            if trimester:
                dist_lots = [
                    r[0] for r in conn.execute("""
                        SELECT DISTINCT lot_name FROM supplier_allocations 
                        WHERE year = ? AND trimester = ? AND lot_name IS NOT NULL
                        ORDER BY lot_name ASC
                    """, (rep_year, trimester)).fetchall()
                ]
            else:
                dist_lots = [
                    r[0] for r in conn.execute("""
                        SELECT DISTINCT lot_name FROM supplier_allocations 
                        WHERE year = ? AND lot_name IS NOT NULL
                        ORDER BY lot_name ASC
                    """, (rep_year,)).fetchall()
                ]

            # 2. بناء استعلام جلب الحصص
            if trimester:
                query = """
                    SELECT sa.*, a.name as article_name, a.unit, a.code, a.price_ttc, s.name as supplier_name
                    FROM supplier_allocations sa
                    JOIN articles a ON sa.article_id = a.id
                    LEFT JOIN suppliers s ON sa.supplier_id = s.id
                    WHERE sa.year = ? AND sa.trimester = ?
                """
                params = [rep_year, trimester]
            else:
                query = """
                    SELECT sa.*, a.name as article_name, a.unit, a.code, a.price_ttc, s.name as supplier_name
                    FROM supplier_allocations sa
                    JOIN articles a ON sa.article_id = a.id
                    LEFT JOIN suppliers s ON sa.supplier_id = s.id
                    WHERE sa.year = ?
                """
                params = [rep_year]

            if lot_name and lot_name != "ALL":
                query += " AND sa.lot_name = ?"
                params.append(lot_name)
            if supplier_id:
                query += " AND sa.supplier_id = ?"
                params.append(supplier_id)

            query += " ORDER BY sa.lot_name ASC, a.id ASC"
            alloc_rows = conn.execute(query, params).fetchall()

            # 3. جلب المدخولات الفعلية من وصولات الاستلام
            sup_cur = conn.execute("""
                SELECT evi.article_id, SUM(evi.quantity) as actual_qty, SUM(evi.total_price) as actual_amount
                FROM entry_voucher_items evi
                JOIN entry_vouchers ev ON evi.voucher_id = ev.id
                WHERE ev.date >= ? AND ev.date <= ? AND ev.voucher_type = 'SUPPLIER'
                GROUP BY evi.article_id
            """, (start_date_str, end_date_str))
            sup_map = {r["article_id"]: {"qty": r["actual_qty"], "amt": r["actual_amount"]} for r in sup_cur.fetchall()}

            items_list = []
            lots_dict = {}

            tot_allocated_qty = 0.0
            tot_allocated_amt = 0.0
            tot_actual_qty = 0.0
            tot_actual_amt = 0.0
            tot_diff_amt_excess = 0.0
            tot_diff_amt_deficit = 0.0

            for i, sa in enumerate(alloc_rows, 1):
                art_id = sa["article_id"]
                p = sa["contract_price"] if sa["contract_price"] > 0 else sa["price_ttc"]
                alloc_q = sa["allocated_qty"]
                alloc_a = alloc_q * p

                # المدخول الفعلي: الأولوية لوصولات التوريد إن وجدت، وإلا المدخول المسجل في ملف عبد الحميد
                actual = sup_map.get(art_id, {"qty": 0.0, "amt": 0.0})
                excel_act_q = sa["excel_actual_qty"] if "excel_actual_qty" in sa.keys() else 0.0
                act_q = actual["qty"] if actual["qty"] > 0 else excel_act_q
                act_a = act_q * p

                diff_q = act_q - alloc_q
                diff_a = act_a - alloc_a

                diff_q_excess = diff_q if diff_q > 0 else 0.0
                diff_q_deficit = abs(diff_q) if diff_q < 0 else 0.0

                diff_a_excess = diff_a if diff_a > 0 else 0.0
                diff_a_deficit = abs(diff_a) if diff_a < 0 else 0.0

                tot_allocated_qty += alloc_q
                tot_allocated_amt += alloc_a
                tot_actual_qty += act_q
                tot_actual_amt += act_a
                tot_diff_amt_excess += diff_a_excess
                tot_diff_amt_deficit += diff_a_deficit

                c_lot = sa["lot_name"] or "حصة عامة"
                c_supp = sa["supplier_name"] or "المورد العام"

                item_obj = {
                    "index": i,
                    "article_id": art_id,
                    "code": sa["code"] or f"{i:02d}",
                    "name": sa["article_name"],
                    "lot_name": c_lot,
                    "supplier_name": c_supp,
                    "unit": sa["unit"],
                    "price_ttc": p,
                    "allocated_qty": alloc_q,
                    "allocated_amt": alloc_a,
                    "actual_qty": act_q,
                    "actual_amt": act_a,
                    "diff_qty_excess": diff_q_excess,
                    "diff_qty_deficit": diff_q_deficit,
                    "diff_amt_excess": diff_a_excess,
                    "diff_amt_deficit": diff_a_deficit
                }
                items_list.append(item_obj)

                # تجميع حسب الحصص
                if c_lot not in lots_dict:
                    lots_dict[c_lot] = {
                        "lot_name": c_lot,
                        "supplier_name": c_supp,
                        "items": [],
                        "tot_allocated_qty": 0.0,
                        "tot_allocated_amt": 0.0,
                        "tot_actual_qty": 0.0,
                        "tot_actual_amt": 0.0,
                        "tot_diff_amt_excess": 0.0,
                        "tot_diff_amt_deficit": 0.0
                    }
                l_grp = lots_dict[c_lot]
                l_grp["items"].append(item_obj)
                l_grp["tot_allocated_qty"] += alloc_q
                l_grp["tot_allocated_amt"] += alloc_a
                l_grp["tot_actual_qty"] += act_q
                l_grp["tot_actual_amt"] += act_a
                l_grp["tot_diff_amt_excess"] += diff_a_excess
                l_grp["tot_diff_amt_deficit"] += diff_a_deficit

            return {
                "year": rep_year,
                "trimester": trimester,
                "trimester_name": t_name,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "distinct_lots": dist_lots,
                "lots": list(lots_dict.values()),
                "items": items_list,
                "tot_allocated_qty": tot_allocated_qty,
                "tot_allocated_amt": tot_allocated_amt,
                "tot_actual_qty": tot_actual_qty,
                "tot_actual_amt": tot_actual_amt,
                "tot_diff_amt_excess": tot_diff_amt_excess,
                "tot_diff_amt_deficit": tot_diff_amt_deficit
            }

    def import_wad3iya_excel(self, file_path: str = r"F:\2026\عبد الحميد الوضعية.xlsx", residence_id: Optional[int] = None) -> Dict[str, Any]:
        """
        استيراد وتحديث وضعية الحصص والموردين من ملف عبد الحميد الوضعية.xlsx
        يقوم باستخراج كافة الحصص والبنود والأسعار والكميات الممنوحة والفعلية لجميع الثلاثيات
        """
        import os
        import re
        import openpyxl

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ملف الوضعية غير موجود في المسار: {file_path}")

        r_id = residence_id or self.residence_id
        wb = openpyxl.load_workbook(file_path, data_only=True)

        alias_map = {
            "حليب غبرة 500 غ": "حليب بودرة جاف",
            "سكر مبلور": "سكر مبلور كلغ",
            "قهوة معلبة": "قهوة مطحونة",
            "الذرة معلبة": "ذرة معلبة كلغ",
            "زيتون اسود": "زيتون المائدة",
            "زيتون بدون نواة": "زيتون بدون علف",
            "الديول": "ديول 10 ورقات",
            "الفطر المعلب": "فطر معلب",
            "بطاطا مرحية": "مسحوق البطاطا",
            "ماء الزهر 75 سل": "ماء الزهر 1 ل",
            "مرغرين نباتية": "مرغرين نباتية 500 غ",
            "تونة بالزيت 65 غ": "تونة معلبة 65غ",
            "شمندر": "شمندر بدون اوراق",
            "الجزر": "جزر",
            "الكرنب الأخضر": "كرنب",
            "الكرنب الزهري": "كرنب زهري",
            "كوسة": "جريوات",
            "بصل جاف": "بصل",
            "فلفل اخضر": "فلفل حلو وفلفل حار",
            "خس اخضر": "خس أخضر",
            "الموز": "موز",
            "الليمون": "ليمون",
            "البرتقال": "برتقال موسمي",
            "العنب": "عنب",
            "خبز عادي": "خبز عادي 250غ",
            "خبز محسن": "خبز محسن 250غ",
            "حلويات جافة": "حلويات جافة ( كروكي )",
            "خبز محسن صغير بالشيكولاطة": "خبز صغير بالشيكولاطة",
            "قلب الوز": "قلب اللوز",
            "لحم الدجاج الطازج": "دجاج منزوع الاحشاء",
            "ماء المعدني 0.5 لتر": "ماء معدني 0,5 ل",
            "حليب الأكياس المدعم 1 لتر": "حليب مبستر 1ل",
            "حلوى قشدية 90 غ": "حلوى قشدية 100 غ",
            "جبن محلى 16 قطعة": "جبن علبة 16 قطعة",
            "لوبيا بيضاء الجافة": "لوبياء بيضاء",
            "طماطم مصبرة 28%": "طماطم 4/4 تركيز 28 %",
            "دجاج كامل": "دجاج منزوع الاحشاء",
            "طماطم طازجة": "طماطم طازجة",
        }

        lot_cat_map = {
            "حصة المواد الغذائية": 3,
            "حصة الخضر و الفواكه": 2,
            "حصة الحلويات و الخبز العادي": 5,
            "حصة اللحوم الحمراء الطازجة": 1,
            "حصة اللحوم البيضاء الطازجة": 1,
            "حصة الماء المعدني 0.5 ل": 6,
            "حصة السمك الطازج": 1,
            "حصة الحليب و مشتقاته": 4,
            "حصة الحبوب": 3,
            "حصة الكاشير والباتي": 1
        }

        def _clean_str(txt):
            if not txt: return ""
            txt = re.sub(r"[\u0640\ufe8e\ufe8f\ufe90\ufe91\ufe92]", "", str(txt))
            return re.sub(r"\s+", " ", txt).strip()

        stats = {"suppliers": 0, "articles_created": 0, "allocations": 0}

        with self.db.get_connection() as conn:
            # التأكد من وجود الأعمدة
            col_names = [r["name"] for r in conn.execute("PRAGMA table_info(supplier_allocations)").fetchall()]
            if "lot_name" not in col_names:
                conn.execute("ALTER TABLE supplier_allocations ADD COLUMN lot_name TEXT")
            if "excel_actual_qty" not in col_names:
                conn.execute("ALTER TABLE supplier_allocations ADD COLUMN excel_actual_qty REAL NOT NULL DEFAULT 0.0")

            db_arts = {_clean_str(r["name"]): r["id"] for r in conn.execute("SELECT id, name FROM articles").fetchall()}

            sheets = [("ثلاثي ول", 1), ("ثلاثي ثاني", 2), ("ثلاثي الثالث", 3)]
            for sheet_name, tri_idx in sheets:
                if sheet_name not in wb.sheetnames:
                    continue
                ws = wb[sheet_name]
                curr_lot = "حصة المواد الغذائية"
                curr_supp = "قريشي بلخير"
                curr_supp_id = 1

                for r in range(1, ws.max_row + 1):
                    c1 = _clean_str(ws.cell(r, 1).value)
                    c2 = _clean_str(ws.cell(r, 2).value)

                    header_text = None
                    if "حصة" in c1: header_text = c1
                    elif "حصة" in c2: header_text = c2

                    if header_text:
                        lot_name = header_text
                        supp_name = "غير محدد"
                        if "المورد" in header_text:
                            parts = re.split(r"للمورد\s*[/:\-]?|المورد\s*[/:\-]?", header_text)
                            lot_name = parts[0].strip()
                            if len(parts) > 1: supp_name = parts[1].replace("/", "").strip()
                        elif "/" in header_text:
                            parts = header_text.split("/")
                            lot_name = parts[0].strip()
                            supp_name = parts[1].strip()

                        lot_name = re.sub(r"\s*للمورد\s*$", "", lot_name).strip()
                        lot_name = re.sub(r"\s+", " ", lot_name)
                        supp_name = re.sub(r"\s+", " ", supp_name)

                        if "الماء المعدني" in lot_name:
                            lot_name = "حصة الماء المعدني 0.5 ل"
                        if "مرجي لخضر" in supp_name or "ش ذ م م برجي" in supp_name:
                            supp_name = "ش ذ م م برجي (مرجي لخضر)"

                        curr_lot = lot_name
                        curr_supp = supp_name

                        conn.execute("""
                            INSERT OR IGNORE INTO suppliers (name, phone, lot_number, notes)
                            VALUES (?, '0660000000', ?, 'مورد معتمد من مديرية الخدمات الجامعية')
                        """, (curr_supp, curr_lot))
                        supp_row = conn.execute("SELECT id FROM suppliers WHERE name = ?", (curr_supp,)).fetchone()
                        curr_supp_id = supp_row["id"]
                        stats["suppliers"] += 1
                        continue

                    if c1.isdigit() and c2 and c2 not in ["None", "المواد", "الرقم"]:
                        unit = _clean_str(ws.cell(r, 3).value) or "كلغ"
                        try: price_ttc = float(ws.cell(r, 4).value or 0.0)
                        except: price_ttc = 0.0
                        try: alloc_qty = float(ws.cell(r, 5).value or 0.0)
                        except: alloc_qty = 0.0
                        try: act_qty = float(ws.cell(r, 7).value or 0.0)
                        except: act_qty = 0.0

                        art_id = None
                        if c2 in db_arts:
                            art_id = db_arts[c2]
                        elif c2 in alias_map and alias_map[c2] in db_arts:
                            art_id = db_arts[alias_map[c2]]
                        else:
                            c2_no_al = c2[2:] if c2.startswith("ال") else c2
                            for k, vid in db_arts.items():
                                if c2_no_al and (c2_no_al == k or c2_no_al in k or k in c2_no_al):
                                    art_id = vid
                                    break

                        if not art_id:
                            cat_id = lot_cat_map.get(curr_lot, 3)
                            cur = conn.execute("""
                                INSERT INTO articles (
                                    code, name, category_id, unit, price_ht, discount_rate,
                                    discount_amount, price_after_discount, tva_rate, price_ttc,
                                    current_pmp, safety_stock, initial_stock, current_stock, is_active
                                ) VALUES (?, ?, ?, ?, ?, 0.0, 0.0, ?, 0.0, ?, ?, 10.0, 0.0, 0.0, 1)
                            """, (c1, c2, cat_id, unit, price_ttc, price_ttc, price_ttc, price_ttc))
                            art_id = cur.lastrowid
                            db_arts[c2] = art_id
                            stats["articles_created"] += 1

                        conn.execute("""
                            INSERT INTO supplier_allocations (
                                trimester, year, supplier_id, article_id, allocated_qty,
                                contract_price, lot_name, excel_actual_qty, residence_id
                            ) VALUES (?, 2026, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(residence_id, trimester, year, supplier_id, article_id) DO UPDATE SET
                                allocated_qty = excluded.allocated_qty,
                                contract_price = excluded.contract_price,
                                lot_name = excluded.lot_name,
                                excel_actual_qty = excluded.excel_actual_qty
                        """, (tri_idx, curr_supp_id, art_id, alloc_qty, price_ttc, curr_lot, act_qty, r_id))
                        stats["allocations"] += 1

        return stats

    # -------------------------------------------------------------
    # نظام حركة الإعارة والاستعارة التبادلية بين الإقامات الجامعية
    # (Inter-Residence Loans System)
    # -------------------------------------------------------------
    def get_next_loan_number(self, year: Optional[int] = None) -> str:
        """توليد رقم تسلسلي لإعارة المواد بين الإقامات (مثال: LOAN-2026-0001)"""
        target_year = year or datetime.date.today().year
        with self.db.get_connection() as conn:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM residence_loans WHERE date LIKE ?",
                (f"{target_year}-%",)
            ).fetchone()[0]
            return f"LOAN-{target_year}-{(cnt + 1):04d}"

    def create_residence_loan(
        self,
        from_residence_id: int,
        to_residence_id: int,
        date_str: str,
        items: List[Dict[str, Any]],
        notes: str = "",
        created_by: str = ""
    ) -> int:
        """
        تسجيل إعارة مواد من إقامة مانحة إلى إقامة مستفيدة (بحالة معلقة PENDING).
        يتم التحقق من توفر المخزون في الإقامة المانحة أولاً.
        """
        if from_residence_id == to_residence_id:
            raise ValueError("لا يمكن إعارة المواد لنفس الإقامة.")
        if not items:
            raise ValueError("يجب تحديد مادة واحدة على الأقل للإعارة.")

        loan_number = self.get_next_loan_number()

        with self.db.get_connection() as conn:
            # التحقق من كفاية المخزون في الإقامة المانحة
            for it in items:
                art_id = it["article_id"]
                req_qty = float(it["quantity"])
                if req_qty <= 0:
                    continue

                cur_art = conn.execute("""
                    SELECT a.name, COALESCE(ra.current_stock, a.current_stock, 0.0) as current_stock
                    FROM articles a
                    LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                    WHERE a.id = ?
                """, (from_residence_id, art_id)).fetchone()

                if not cur_art:
                    raise ValueError(f"المادة رقم {art_id} غير موجودة.")
                avail = float(cur_art["current_stock"])
                if req_qty > avail:
                    raise InsufficientStockError(cur_art["name"], req_qty, avail)

            # إدراج ترويسة الإعارة
            cur = conn.execute("""
                INSERT INTO residence_loans (
                    loan_number, from_residence_id, to_residence_id, date, status, notes, created_by
                ) VALUES (?, ?, ?, ?, 'PENDING', ?, ?)
            """, (loan_number, from_residence_id, to_residence_id, date_str, notes, created_by))
            loan_id = cur.lastrowid

            # إدراج بنود الإعارة
            for it in items:
                art_id = it["article_id"]
                qty = float(it["quantity"])
                if qty <= 0:
                    continue
                p_ttc = float(it.get("unit_price_ttc", 0.0))
                if p_ttc <= 0:
                    p_row = conn.execute("SELECT price_ttc FROM articles WHERE id = ?", (art_id,)).fetchone()
                    p_ttc = float(p_row[0]) if p_row else 0.0
                tot_p = qty * p_ttc

                conn.execute("""
                    INSERT INTO residence_loan_items (loan_id, article_id, quantity, unit_price_ttc, total_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (loan_id, art_id, qty, p_ttc, tot_p))

            conn.commit()
            return loan_id

    def get_outgoing_loans(
        self,
        residence_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """جلب قائمة الإعارات الصادرة من الإقامة المحددة"""
        r_id = residence_id or self.residence_id
        query = """
            SELECT rl.id, rl.loan_number, rl.from_residence_id, rl.to_residence_id,
                   rl.date, rl.status, rl.notes, rl.created_by, rl.created_at, rl.received_at,
                   r_to.name as to_residence_name,
                   COUNT(rli.id) as items_count,
                   COALESCE(SUM(rli.total_price), 0.0) as total_amount
            FROM residence_loans rl
            JOIN residences r_to ON rl.to_residence_id = r_to.id
            LEFT JOIN residence_loan_items rli ON rl.id = rli.loan_id
            WHERE rl.from_residence_id = ?
        """
        params = [r_id]
        if date_from:
            query += " AND rl.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND rl.date <= ?"
            params.append(date_to)
        if status:
            query += " AND rl.status = ?"
            params.append(status)

        query += " GROUP BY rl.id ORDER BY rl.date DESC, rl.id DESC"

        with self.db.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            loans = []
            for r in rows:
                loan_d = dict(r)
                cur_items = conn.execute("""
                    SELECT rli.id, rli.article_id, rli.quantity, rli.unit_price_ttc, rli.total_price,
                           a.name as article_name, a.unit
                    FROM residence_loan_items rli
                    JOIN articles a ON rli.article_id = a.id
                    WHERE rli.loan_id = ?
                """, (r["id"],)).fetchall()
                loan_d["items"] = [dict(it) for it in cur_items]
                summary_parts = [f"{it['article_name']} ({it['quantity']:g} {it['unit']})" for it in loan_d["items"]]
                loan_d["items_summary"] = "، ".join(summary_parts) if summary_parts else "لا توجد مواد"
                loans.append(loan_d)
            return loans

    def get_incoming_loans(
        self,
        residence_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: Optional[str] = None,
        from_residence_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """جلب قائمة الاستعارات الواردة إلى الإقامة المحددة (تظهر له المنتجات والكميات من كل إقامة على حدا)"""
        r_id = residence_id or self.residence_id
        query = """
            SELECT rl.id, rl.loan_number, rl.from_residence_id, rl.to_residence_id,
                   rl.date, rl.status, rl.notes, rl.created_by, rl.created_at, rl.received_at,
                   r_from.name as from_residence_name,
                   COUNT(rli.id) as items_count,
                   COALESCE(SUM(rli.total_price), 0.0) as total_amount
            FROM residence_loans rl
            JOIN residences r_from ON rl.from_residence_id = r_from.id
            LEFT JOIN residence_loan_items rli ON rl.id = rli.loan_id
            WHERE rl.to_residence_id = ?
        """
        params = [r_id]
        if from_residence_id:
            query += " AND rl.from_residence_id = ?"
            params.append(from_residence_id)
        if date_from:
            query += " AND rl.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND rl.date <= ?"
            params.append(date_to)
        if status:
            query += " AND rl.status = ?"
            params.append(status)

        query += " GROUP BY rl.id ORDER BY rl.date DESC, rl.id DESC"

        with self.db.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            loans = []
            for r in rows:
                loan_d = dict(r)
                cur_items = conn.execute("""
                    SELECT rli.id, rli.article_id, rli.quantity, rli.unit_price_ttc, rli.total_price,
                           a.name as article_name, a.unit
                    FROM residence_loan_items rli
                    JOIN articles a ON rli.article_id = a.id
                    WHERE rli.loan_id = ?
                """, (r["id"],)).fetchall()
                loan_d["items"] = [dict(it) for it in cur_items]
                summary_parts = [f"{it['article_name']} ({it['quantity']:g} {it['unit']})" for it in loan_d["items"]]
                loan_d["items_summary"] = "، ".join(summary_parts) if summary_parts else "لا توجد مواد"
                loans.append(loan_d)
            return loans

    def confirm_receive_loan(self, loan_id: int, received_by: str = "") -> bool:
        """
        تأكيد استلام الإعارة من قبل الإقامة المستفيدة:
        1. تضاف الكمية لمخزون الإقامة المستفيدة (LOAN_IN).
        2. تنقص الكمية من مخزون الإقامة المانحة (LOAN_OUT).
        3. تنشأ وصولات LOAN_IN و LOAN_OUT تلقائياً لتظهر فوراً في ورقة الاستهلاك وشبكات التتبع الشهرية.
        4. تحديث حالة الإعارة إلى RECEIVED وتخزين معرفات الوصولات.
        """
        with self.db.get_connection() as conn:
            loan = conn.execute("SELECT * FROM residence_loans WHERE id = ?", (loan_id,)).fetchone()
            if not loan:
                raise ValueError("عملية الإعارة غير موجودة.")
            if loan["status"] != "PENDING":
                raise ValueError(f"لا يمكن استلام إعارة بحالة: {loan['status']}")

            from_res_id = loan["from_residence_id"]
            to_res_id = loan["to_residence_id"]
            l_date = loan["date"]
            l_num = loan["loan_number"]

            # جلب أسماء الإقامات
            from_name = conn.execute("SELECT name FROM residences WHERE id = ?", (from_res_id,)).fetchone()["name"]
            to_name = conn.execute("SELECT name FROM residences WHERE id = ?", (to_res_id,)).fetchone()["name"]

            # جلب بنود الإعارة
            items = conn.execute("""
                SELECT rli.article_id, rli.quantity, rli.unit_price_ttc, rli.total_price,
                       a.name as article_name, a.unit
                FROM residence_loan_items rli
                JOIN articles a ON rli.article_id = a.id
                WHERE rli.loan_id = ?
            """, (loan_id,)).fetchall()

            if not items:
                raise ValueError("لا توجد بنود في هذه الإعارة.")

            # التحقق مرة أخرى من توفر المخزون في الإقامة المانحة
            for it in items:
                cur_art = conn.execute("""
                    SELECT a.name, COALESCE(ra.current_stock, a.current_stock, 0.0) as current_stock
                    FROM articles a
                    LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                    WHERE a.id = ?
                """, (from_res_id, it["article_id"])).fetchone()
                avail = float(cur_art["current_stock"])
                req_qty = float(it["quantity"])
                if req_qty > avail:
                    raise InsufficientStockError(cur_art["name"], req_qty, avail)

            tot_amount = sum(float(it["total_price"]) for it in items)

            # 1. إنشاء وصل إخراج LOAN_OUT للإقامة المانحة
            v_num_out = f"BS-{from_res_id}-{l_date}-LOAN-{loan_id}"
            cur_out = conn.execute("""
                INSERT INTO exit_vouchers (
                    voucher_number, date, voucher_type, residence_id, destination_residence,
                    total_breakfast_cost, total_lunch_cost, total_dinner_cost, total_amount, notes
                ) VALUES (?, ?, 'LOAN_OUT', ?, ?, 0, 0, 0, ?, ?)
            """, (v_num_out, l_date, from_res_id, to_name, tot_amount, f"إعارة رسمية برقم {l_num} لفائدة {to_name}"))
            exit_v_id = cur_out.lastrowid

            # 2. إنشاء وصل دخول LOAN_IN للإقامة المستفيدة
            v_num_in = f"BE-{to_res_id}-{l_date}-LOAN-{loan_id}"
            cur_in = conn.execute("""
                INSERT INTO entry_vouchers (
                    voucher_number, date, voucher_type, residence_id, source_residence,
                    delivery_note_ref, total_amount, notes
                ) VALUES (?, ?, 'LOAN_IN', ?, ?, ?, ?, ?)
            """, (v_num_in, l_date, to_res_id, from_name, l_num, tot_amount, f"استعارة رسمية برقم {l_num} من {from_name}"))
            entry_v_id = cur_in.lastrowid

            # 3. معالجة حركة كل مادة وتحديث الأرصدة
            for it in items:
                art_id = it["article_id"]
                qty = float(it["quantity"])
                p_ttc = float(it["unit_price_ttc"])
                tot_p = float(it["total_price"])

                # بند الإخراج
                conn.execute("""
                    INSERT INTO exit_voucher_items (
                        voucher_id, article_id, qty_breakfast, qty_lunch, qty_dinner, qty_other,
                        total_qty, unit_price_ttc, total_cost
                    ) VALUES (?, ?, 0, 0, 0, ?, ?, ?, ?)
                """, (exit_v_id, art_id, qty, qty, p_ttc, tot_p))

                # بند الدخول
                conn.execute("""
                    INSERT INTO entry_voucher_items (
                        voucher_id, article_id, quantity, unit_price_ttc, total_price
                    ) VALUES (?, ?, ?, ?, ?)
                """, (entry_v_id, art_id, qty, p_ttc, tot_p))

                # تحديث رصيد الإقامة المانحة (نقصان)
                from_stock_cur = conn.execute("""
                    SELECT COALESCE(ra.current_stock, a.current_stock, 0.0)
                    FROM articles a
                    LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                    WHERE a.id = ?
                """, (from_res_id, art_id)).fetchone()[0]
                new_from_stock = float(from_stock_cur) - qty

                conn.execute("""
                    INSERT INTO residence_articles (residence_id, article_id, current_stock)
                    VALUES (?, ?, ?)
                    ON CONFLICT(residence_id, article_id) DO UPDATE SET current_stock = excluded.current_stock
                """, (from_res_id, art_id, new_from_stock))
                if from_res_id == 1:
                    conn.execute("UPDATE articles SET current_stock = ? WHERE id = ?", (new_from_stock, art_id))

                # حركة مخزون الإخراج
                conn.execute("""
                    INSERT INTO stock_movements (
                        date, article_id, movement_type, voucher_id, residence_id,
                        qty_in, qty_out, unit_price, total_value, balance_after
                    ) VALUES (?, ?, 'LOAN_OUT', ?, ?, 0, ?, ?, ?, ?)
                """, (l_date, art_id, exit_v_id, from_res_id, qty, p_ttc, tot_p, new_from_stock))

                # تحديث رصيد الإقامة المستفيدة (زيادة)
                to_stock_cur = conn.execute("""
                    SELECT COALESCE(ra.current_stock, a.current_stock, 0.0)
                    FROM articles a
                    LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                    WHERE a.id = ?
                """, (to_res_id, art_id)).fetchone()[0]
                new_to_stock = float(to_stock_cur) + qty

                conn.execute("""
                    INSERT INTO residence_articles (residence_id, article_id, current_stock)
                    VALUES (?, ?, ?)
                    ON CONFLICT(residence_id, article_id) DO UPDATE SET current_stock = excluded.current_stock
                """, (to_res_id, art_id, new_to_stock))
                if to_res_id == 1:
                    conn.execute("UPDATE articles SET current_stock = ? WHERE id = ?", (new_to_stock, art_id))

                # حركة مخزون الدخول
                conn.execute("""
                    INSERT INTO stock_movements (
                        date, article_id, movement_type, voucher_id, residence_id,
                        qty_in, qty_out, unit_price, total_value, balance_after
                    ) VALUES (?, ?, 'LOAN_IN', ?, ?, ?, 0, ?, ?, ?)
                """, (l_date, art_id, entry_v_id, to_res_id, qty, p_ttc, tot_p, new_to_stock))

            # 4. تحديث حالة الإعارة إلى RECEIVED
            conn.execute("""
                UPDATE residence_loans SET
                    status = 'RECEIVED',
                    received_at = CURRENT_TIMESTAMP,
                    exit_voucher_id = ?,
                    entry_voucher_id = ?
                WHERE id = ?
            """, (exit_v_id, entry_v_id, loan_id))

            conn.commit()

        # إبطال الذاكرة المؤقتة للإقامتَين
        from core.cache_service import CacheService
        CacheService.invalidate_articles(from_res_id)
        CacheService.invalidate_articles(to_res_id)
        return True

    def cancel_residence_loan(self, loan_id: int, user_name: str = "") -> bool:
        """إلغاء طلب إعارة معلق لم يتم استلامه بعد"""
        with self.db.get_connection() as conn:
            loan = conn.execute("SELECT status FROM residence_loans WHERE id = ?", (loan_id,)).fetchone()
            if not loan:
                raise ValueError("عملية الإعارة غير موجودة.")
            if loan["status"] != "PENDING":
                raise ValueError("لا يمكن إلغاء إعارة تم استلامها بالفعل أو ملغاة.")

            conn.execute("UPDATE residence_loans SET status = 'CANCELLED' WHERE id = ?", (loan_id,))
            conn.commit()
            return True

    def revert_confirmed_loan(
        self,
        loan_id: int,
        target_status: str = "CANCELLED",
        reason: str = "",
        reverted_by: str = "المديرية"
    ) -> bool:
        """
        استرجاع وإلغاء إعارة مؤكدة ومستلمة مسبقاً (خاصية استثنائية محصورة بإدارة المديرية):
        1. التحقق من وجود الإعارة وأن حالتها RECEIVED.
        2. خصم الكميات من مخزون الإقامة المستفيدة (إلغاء أثر الاستلام).
        3. إعادة الكميات إلى مخزون الإقامة المعيرة (استرداد المواد إلى المخزن الأصلي).
        4. حذف وصولات LOAN_IN و LOAN_OUT وحركات المخزون المقابلة تلقائياً.
        5. تحديث حالة الإعارة في السجل إلى CANCELLED أو PENDING حسب خيار المديرية.
        6. إبطال الذاكرة المؤقتة للأرصدة في الإقامتَين.
        """
        with self.db.get_connection() as conn:
            loan = conn.execute("SELECT * FROM residence_loans WHERE id = ?", (loan_id,)).fetchone()
            if not loan:
                raise ValueError("عملية الإعارة غير موجودة.")
            if loan["status"] != "RECEIVED":
                raise ValueError(f"لا يمكن استرجاع هذه الإعارة لأن حالتها الحالية ليست (مستلمة) بل ({loan['status']}).")

            from_res_id = loan["from_residence_id"]
            to_res_id = loan["to_residence_id"]
            l_date = loan["date"]
            l_num = loan["loan_number"]

            # جلب بنود الإعارة
            items = conn.execute("""
                SELECT rli.article_id, rli.quantity, rli.unit_price_ttc, rli.total_price,
                       a.name as article_name, a.unit
                FROM residence_loan_items rli
                JOIN articles a ON rli.article_id = a.id
                WHERE rli.loan_id = ?
            """, (loan_id,)).fetchall()

            if not items:
                raise ValueError("لا توجد بنود مسجلة لهذه الإعارة.")

            # معالجة تصحيح أرصدة المواد في كلا الإقامتَين
            for it in items:
                art_id = it["article_id"]
                qty = float(it["quantity"])

                # 1. خصم الكمية من الإقامة المستفيدة (إلغاء الزيادة السابقة)
                to_stock_cur = conn.execute("""
                    SELECT COALESCE(ra.current_stock, a.current_stock, 0.0)
                    FROM articles a
                    LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                    WHERE a.id = ?
                """, (to_res_id, art_id)).fetchone()[0]
                new_to_stock = float(to_stock_cur) - qty

                conn.execute("""
                    INSERT INTO residence_articles (residence_id, article_id, current_stock)
                    VALUES (?, ?, ?)
                    ON CONFLICT(residence_id, article_id) DO UPDATE SET current_stock = excluded.current_stock
                """, (to_res_id, art_id, new_to_stock))
                if to_res_id == 1:
                    conn.execute("UPDATE articles SET current_stock = ? WHERE id = ?", (new_to_stock, art_id))

                # 2. إعادة الكمية إلى الإقامة المعيرة (استرجاع النقصان السابق)
                from_stock_cur = conn.execute("""
                    SELECT COALESCE(ra.current_stock, a.current_stock, 0.0)
                    FROM articles a
                    LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                    WHERE a.id = ?
                """, (from_res_id, art_id)).fetchone()[0]
                new_from_stock = float(from_stock_cur) + qty

                conn.execute("""
                    INSERT INTO residence_articles (residence_id, article_id, current_stock)
                    VALUES (?, ?, ?)
                    ON CONFLICT(residence_id, article_id) DO UPDATE SET current_stock = excluded.current_stock
                """, (from_res_id, art_id, new_from_stock))
                if from_res_id == 1:
                    conn.execute("UPDATE articles SET current_stock = ? WHERE id = ?", (new_from_stock, art_id))

            # حذف وصولات الخروج والدخول وحركات المخزون المرتبطة بها
            exit_v_id = loan["exit_voucher_id"]
            entry_v_id = loan["entry_voucher_id"]

            v_num_out = f"BS-{from_res_id}-{l_date}-LOAN-{loan_id}"
            v_num_in = f"BE-{to_res_id}-{l_date}-LOAN-{loan_id}"

            if not exit_v_id:
                row_ex = conn.execute("SELECT id FROM exit_vouchers WHERE voucher_number = ?", (v_num_out,)).fetchone()
                if row_ex:
                    exit_v_id = row_ex["id"]

            if not entry_v_id:
                row_en = conn.execute("SELECT id FROM entry_vouchers WHERE voucher_number = ?", (v_num_in,)).fetchone()
                if row_en:
                    entry_v_id = row_en["id"]

            if exit_v_id:
                conn.execute("DELETE FROM stock_movements WHERE voucher_id = ? AND movement_type = 'LOAN_OUT'", (exit_v_id,))
                conn.execute("DELETE FROM exit_voucher_items WHERE voucher_id = ?", (exit_v_id,))
                conn.execute("DELETE FROM exit_vouchers WHERE id = ?", (exit_v_id,))

            if entry_v_id:
                conn.execute("DELETE FROM stock_movements WHERE voucher_id = ? AND movement_type = 'LOAN_IN'", (entry_v_id,))
                conn.execute("DELETE FROM entry_voucher_items WHERE voucher_id = ?", (entry_v_id,))
                conn.execute("DELETE FROM entry_vouchers WHERE id = ?", (entry_v_id,))

            # تحديث حالة الإعارة وملاحظات التدقيق
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            audit_msg = f"تم إرجاع الإعارة وتصحيح المخزون بقرار من المديرية ({reverted_by}) بتاريخ {now_str}"
            if reason:
                audit_msg += f" [السبب: {reason}]"

            old_notes = loan["notes"] or ""
            updated_notes = f"{old_notes} | {audit_msg}" if old_notes else audit_msg

            final_status = 'CANCELLED' if target_status == 'CANCELLED' else 'PENDING'
            conn.execute("""
                UPDATE residence_loans SET
                    status = ?,
                    exit_voucher_id = NULL,
                    entry_voucher_id = NULL,
                    notes = ?
                WHERE id = ?
            """, (final_status, updated_notes, loan_id))

            conn.commit()

        # إبطال كاش الأرصدة للإقامتَين
        from core.cache_service import CacheService
        CacheService.invalidate_articles(from_res_id)
        CacheService.invalidate_articles(to_res_id)
        return True

    def get_loan_notes_for_daily_sheet(self, date_str: str, residence_id: Optional[int] = None) -> List[str]:
        """
        توليد الملاحظات الرسمية لحركة الإعارة والاستعارة ليوم محدد لطباعتها في ورقة الاستهلاك اليومي:
        - ملاحظة : تم إستعارة كذا وكذا من الإقامة الفلانية
        - ملاحظة : تم إعارة كذا وكذا لفائدة الإقامة الفلانية
        """
        r_id = residence_id or self.residence_id
        notes = []
        with self.db.get_connection() as conn:
            # 1. الاستعارات المستلمة (واردة)
            in_loans = conn.execute("""
                SELECT rl.loan_number, r_from.name as from_res_name,
                       a.name as article_name, a.unit, rli.quantity
                FROM residence_loans rl
                JOIN residences r_from ON rl.from_residence_id = r_from.id
                JOIN residence_loan_items rli ON rl.id = rli.loan_id
                JOIN articles a ON rli.article_id = a.id
                WHERE rl.to_residence_id = ? AND rl.date = ? AND rl.status = 'RECEIVED'
                ORDER BY rl.id ASC, a.name ASC
            """, (r_id, date_str)).fetchall()

            for row in in_loans:
                notes.append(f"تم إستعارة {row['quantity']:g} {row['unit']} من مادة {row['article_name']} من {row['from_res_name']}.")

            # 2. الإعارات الممنوحة (صادرة)
            out_loans = conn.execute("""
                SELECT rl.loan_number, r_to.name as to_res_name,
                       a.name as article_name, a.unit, rli.quantity
                FROM residence_loans rl
                JOIN residences r_to ON rl.to_residence_id = r_to.id
                JOIN residence_loan_items rli ON rl.id = rli.loan_id
                JOIN articles a ON rli.article_id = a.id
                WHERE rl.from_residence_id = ? AND rl.date = ? AND rl.status = 'RECEIVED'
                ORDER BY rl.id ASC, a.name ASC
            """, (r_id, date_str)).fetchall()

            for row in out_loans:
                notes.append(f"تم إعارة {row['quantity']:g} {row['unit']} من مادة {row['article_name']} لفائدة {row['to_res_name']}.")

        return notes


