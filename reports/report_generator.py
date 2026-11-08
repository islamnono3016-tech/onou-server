try:
    from core.time_service import TimeService
except Exception:
    TimeService = None
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import datetime
import math
from typing import Dict, Any, List, Optional
from database.db_manager import DatabaseManager
from core.stock_service import StockService
from core.meals_service import MealsService
from core.residence_service import get_french_residence_name

class ReportGenerator:
    """محرك توليد وطباعة وتصدير التقارير الرسمية للإطعام الجامعي"""

    def __init__(self, db_manager: Any = None, residence_id: Optional[int] = None):
        if hasattr(db_manager, "db"):
            self.db = db_manager.db
        elif isinstance(db_manager, DatabaseManager):
            self.db = db_manager
        elif db_manager is None:
            self.db = DatabaseManager()
        else:
            self.db = db_manager
        self.residence_id = residence_id or 1
        self.residence_name = ""
        self.residence_name_fr = ""
        self.city = "ورقلة"
        self.stock_svc = StockService(self.db, residence_id=self.residence_id)
        self.meals_svc = MealsService(self.db, residence_id=self.residence_id)
        self._init_residence_info()

    def _init_residence_info(self):
        try:
            with self.db.get_connection() as conn:
                row = conn.execute("SELECT id, name, name_fr, city FROM residences WHERE id = ?", (self.residence_id,)).fetchone()
                if row:
                    self.residence_name = row["name"]
                    self.residence_name_fr = row["name_fr"] if "name_fr" in row.keys() and row["name_fr"] else ""
                    self.city = row["city"] if "city" in row.keys() and row["city"] else "ورقلة"
                else:
                    self.residence_name = self.db.get_setting("residence_name", "الإقامة الجامعية محمد الطاهر العبيدي بورقلة")
                    self.residence_name_fr = ""
                    self.city = "ورقلة"
        except Exception:
            self.residence_name = "الإقامة الجامعية محمد الطاهر العبيدي بورقلة"
            self.residence_name_fr = ""
            self.city = "ورقلة"

        if not self.residence_name_fr:
            self.residence_name_fr = get_french_residence_name(self.residence_name, city=self.city)

    def set_residence(self, residence_id: int, residence_name: Optional[str] = None):
        self.residence_id = residence_id
        try:
            with self.db.get_connection() as conn:
                row = conn.execute("SELECT id, name, name_fr, city FROM residences WHERE id = ?", (residence_id,)).fetchone()
                if row:
                    self.residence_name = row["name"]
                    self.residence_name_fr = row["name_fr"] if "name_fr" in row.keys() and row["name_fr"] else ""
                    self.city = row["city"] if "city" in row.keys() and row["city"] else "ورقلة"
                else:
                    self.residence_name = residence_name or ""
                    self.residence_name_fr = ""
                    self.city = "ورقلة"
        except Exception:
            self.residence_name = residence_name or ""
            self.residence_name_fr = ""
            self.city = "ورقلة"

        if residence_name:
            self.residence_name = residence_name

        if not getattr(self, "residence_name_fr", None):
            self.residence_name_fr = get_french_residence_name(self.residence_name, city=getattr(self, "city", "ورقلة"))

        self.stock_svc.set_residence(residence_id)
        self.meals_svc.set_residence(residence_id)

    def get_residence_name_ar(self) -> str:
        return self.residence_name or self.db.get_setting("residence_name", "الإقامة الجامعية محمد الطاهر العبيدي بورقلة")

    def get_residence_name_fr(self) -> str:
        if not getattr(self, "residence_name_fr", None):
            self.residence_name_fr = get_french_residence_name(self.get_residence_name_ar(), city=getattr(self, "city", "ورقلة"))
        return self.residence_name_fr

    def get_directorate_name_ar(self) -> str:
        name = self.db.get_setting("directorate_name", "")
        if not name or "بورقلة" in name or name == "مديرية الخدمات الجامعية ورقلة" or "الجامعية ب" in name or "ورقلة" in name:
            return "مديرية الخدمات الجامعية ورقلة قطب"
        return name

    def get_directorate_name_fr(self) -> str:
        name_ar = self.get_directorate_name_ar()
        if "قطب" in name_ar or "ورقلة" in name_ar:
            return "DIRECTION DES ŒUVRES UNIVERSITAIRES OUARGLA POLE"
        city = getattr(self, "city", "ورقلة") or "ورقلة"
        city_fr = "OUARGLA POLE" if "ورقلة" in city else city.upper()
        return f"DIRECTION DES ŒUVRES UNIVERSITAIRES {city_fr}"

    def get_logo_base64(self) -> str:
        """قراءة شعار الديوان الوطني للخدمات الجامعية بصيغة base64 لطباعة التقارير الرسمية"""
        if hasattr(self, "_cached_logo_b64") and self._cached_logo_b64:
            return self._cached_logo_b64
        try:
            candidates = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "onou_logo_b64.txt"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "onou_logo_b64.txt"),
                os.path.join(os.getcwd(), "assets", "onou_logo_b64.txt"),
            ]
            for p in candidates:
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as f:
                        self._cached_logo_b64 = f.read().strip()
                        return self._cached_logo_b64

            import base64
            png_candidates = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "onou_logo_report.png"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "onou_logo.png"),
                os.path.join(os.getcwd(), "assets", "onou_logo_report.png"),
            ]
            for p in png_candidates:
                if os.path.exists(p):
                    with open(p, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                        self._cached_logo_b64 = f"data:image/png;base64,{b64}"
                        return self._cached_logo_b64
        except Exception:
            pass
        self._cached_logo_b64 = ""
        return ""

    def get_logo_img_html(self, size: int = 56) -> str:
        """توليد وسم HTML لشعار الديوان الوطني للخدمات الجامعية بحجم متناسق ومضبوط لجميع المطبوعات الرسمية"""
        logo_b64 = self.get_logo_base64()
        if logo_b64:
            return f'<img src="{logo_b64}" width="{size}" height="{size}" style="width:{size}px; height:{size}px; object-fit:contain; border-radius:50%; vertical-align:middle;" alt="ONOU">'
        return '<div style="font-size:11pt; font-weight:bold; color:#0F2D25;">ONOU</div>'


    def get_clean_residence_name(self) -> str:
        name = self.get_residence_name_ar().strip()
        prefix = "الإقامة الجامعية "
        if name.startswith(prefix):
            return name[len(prefix):].strip()
        prefix2 = "الاقامة الجامعية "
        if name.startswith(prefix2):
            return name[len(prefix2):].strip()
        return name

    # -------------------------------------------------------------
    # 1. ورقة الاستهلاك اليومي (قسيمة المطبوعة) - HTML للطباعة و Excel
    # -------------------------------------------------------------
    def generate_daily_voucher_html(self, date_str: str) -> str:
        """توليد ورقة الاستهلاك اليومي بصيغة HTML أنيقة للطباعة المباشرة وحفظ PDF"""
        res_name = self.get_residence_name_ar()
        dir_name = self.get_directorate_name_ar()
        onou_name = self.db.get_setting("onou_name", "الديوان الوطني للخدمات الجامعية")

        with self.db.get_connection() as conn:
            # جلب المواد المصروفة لهذا اليوم
            cur = conn.execute("""
                SELECT 
                    a.code, a.name, a.unit, evi.unit_price_ttc,
                    evi.qty_breakfast, (evi.qty_breakfast * evi.unit_price_ttc) as cost_bf,
                    evi.qty_lunch, (evi.qty_lunch * evi.unit_price_ttc) as cost_lu,
                    evi.qty_dinner, (evi.qty_dinner * evi.unit_price_ttc) as cost_di,
                    evi.total_qty, evi.total_cost
                FROM exit_voucher_items evi
                JOIN exit_vouchers ev ON evi.voucher_id = ev.id
                JOIN articles a ON evi.article_id = a.id
                WHERE ev.date = ? AND ev.voucher_type = 'KITCHEN' AND ev.residence_id = ?
                ORDER BY a.id ASC
            """, (date_str, self.residence_id))
            raw_items = [dict(r) for r in cur.fetchall()]
            items = []
            for r in raw_items:
                it = dict(r)
                p_ttc = round(float(it.get("unit_price_ttc", 0.0) or 0.0), 2)
                c_bf = round(float(it.get("qty_breakfast", 0.0) or 0.0) * p_ttc, 2)
                c_lu = round(float(it.get("qty_lunch", 0.0) or 0.0) * p_ttc, 2)
                c_di = round(float(it.get("qty_dinner", 0.0) or 0.0) * p_ttc, 2)
                it["unit_price_ttc"] = p_ttc
                it["cost_bf"] = c_bf
                it["cost_lu"] = c_lu
                it["cost_di"] = c_di
                it["total_cost"] = round(c_bf + c_lu + c_di, 2)
                items.append(it)

            # جلب إحصائيات التذاكر للإقامة المحددة حصراً
            meal_rec = self.meals_svc.get_daily_record(date_str, self.residence_id)

        # حساب المجاميع
        tot_bf_cost = sum(it["cost_bf"] for it in items)
        tot_lu_cost = sum(it["cost_lu"] for it in items)
        tot_di_cost = sum(it["cost_di"] for it in items)
        grand_total = sum(it["total_cost"] for it in items)

        rows_html = ""
        for i, it in enumerate(items, 1):
            rows_html += f"""
            <tr>
                <td style="text-align:right; font-weight:bold;">{it['total_cost']:,.2f}</td>
                <td style="text-align:center; font-weight:bold;">{it['total_qty']}</td>
                <td style="text-align:right;">{it['cost_di']:,.2f}</td>
                <td style="text-align:center;">{it['qty_dinner'] if it['qty_dinner'] > 0 else '-'}</td>
                <td style="text-align:right;">{it['cost_lu']:,.2f}</td>
                <td style="text-align:center;">{it['qty_lunch'] if it['qty_lunch'] > 0 else '-'}</td>
                <td style="text-align:right;">{it['cost_bf']:,.2f}</td>
                <td style="text-align:center;">{it['qty_breakfast'] if it['qty_breakfast'] > 0 else '-'}</td>
                <td style="text-align:right;">{it['unit_price_ttc']:,.2f}</td>
                <td style="text-align:center;">{it['unit']}</td>
                <td style="text-align:right; font-weight:bold;">{it['name']}</td>
                <td style="text-align:center;">{i:02d}</td>
            </tr>
            """

        logo_img_html = self.get_logo_img_html(56)
        d_note = (meal_rec.get("notes") or "").strip()
        daily_note_html = f'<div style="margin-top:10px; border:1px solid #000; padding:6px; font-size:11px; text-align:right;"><strong>ملاحظـــة : </strong> {d_note}</div>' if d_note else '<div style="margin-top:10px; border:1px solid #000; padding:6px; font-size:11px; text-align:right;"><strong>ملاحظـــة : </strong> ................................................................................................................................................................................................................</div>'

        html = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="utf-8">
            <title>ورقة الاستهلاك اليومي - {date_str}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; margin: 20px; font-size: 11px; }}
                .header-table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; }}
                .header-table td {{ padding: 3px; }}
                .title-box {{ text-align: center; font-size: 16px; font-weight: bold; border: 2px solid #0F2D25; padding: 6px; margin: 8px 0; background-color: #F8FAFC; }}
                table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
                table.data-table th, table.data-table td {{ border: 1px solid #334155; padding: 4px 6px; }}
                table.data-table th {{ background-color: #E2E8F0; text-align: center; font-size: 11px; }}
                .totals-row td {{ background-color: #F1F5F9; font-weight: bold; }}
                .stats-box {{ display: flex; justify-content: space-between; margin-top: 15px; border: 1px solid #94A3B8; padding: 10px; background-color: #F8FAFC; }}
                .sign-box {{ width: 100%; margin-top: 25px; }}
                .sign-box td {{ text-align: center; font-weight: bold; width: 33%; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <table class="header-table" width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                    <td colspan="3" align="center" style="text-align:center; font-size:13px; font-weight:bold; padding-bottom:6px;">
                        الجمهورية الجزائرية الديمقراطية الشعبية
                    </td>
                </tr>
                <tr>
                    <td width="38%" align="right" style="width:38%; text-align:right; font-size:10px; font-weight:bold; vertical-align:middle; line-height:1.4;">
                        وزارة التعليم العالي والبحث العلمي<br>
                        {onou_name}<br>
                        {dir_name}<br>
                        {res_name}
                    </td>
                    <td width="24%" align="center" style="width:24%; text-align:center; vertical-align:middle;">
                        {logo_img_html}
                    </td>
                    <td width="38%" align="left" style="width:38%; text-align:left; font-size:9.5px; font-weight:bold; vertical-align:middle; line-height:1.4; direction:ltr;">
                        RÉPUBLIQUE ALGÉRIENNE DÉMOCRATIQUE ET POPULAIRE<br>
                        MINISTÈRE DE L'ENSEIGNEMENT SUPÉRIEUR<br>
                        OFFICE NATIONAL DES ŒUVRES UNIVERSITAIRES<br>
                        DIRECTION DES ŒUVRES UNIVERSITAIRES OUARGLA POLE
                    </td>
                </tr>
            </table>

            <div class="title-box" style="text-align:center; font-size:18px; font-weight:bold; margin:6px 0 2px 0;">ورقـــة الإسـتـهـلاك اليومـــي</div>
            <div style="text-align:center; font-size:12px; font-weight:bold; margin-bottom:10px;">ليــــوم : {date_str}</div>

            <table class="data-table" width="100%" border="1" cellspacing="0" cellpadding="4">
                <thead>
                    <tr>
                        <th colspan="2">المجمــــوع</th>
                        <th colspan="2">وجبـة العشـاء</th>
                        <th colspan="2">وجبـة الغــذاء</th>
                        <th colspan="2">فطور الصباح</th>
                        <th rowspan="2">السعر TTC</th>
                        <th rowspan="2">الوحدة</th>
                        <th rowspan="2">إسـم المــــادة</th>
                        <th rowspan="2">الرقم</th>
                    </tr>
                    <tr>
                        <th>المبلغ</th><th>الكمية</th>
                        <th>المبلغ</th><th>الكمية</th>
                        <th>المبلغ</th><th>الكمية</th>
                        <th>المبلغ</th><th>الكمية</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html if rows_html else '<tr><td colspan="12" style="text-align:center; padding:15px;">لا توجد مواد مستهلكة مسجلة في هذا اليوم</td></tr>'}
                </tbody>
                <tfoot>
                    <tr class="totals-row">
                        <td style="text-align:right; font-size:12px; color:#0F2D25;">{grand_total:,.2f} دج</td><td>-</td>
                        <td style="text-align:right;">{tot_di_cost:,.2f}</td><td>-</td>
                        <td style="text-align:right;">{tot_lu_cost:,.2f}</td><td>-</td>
                        <td style="text-align:right;">{tot_bf_cost:,.2f}</td><td>-</td>
                        <td colspan="4" style="text-align:center;">المجـــــــــاميع الإجماليـــــة</td>
                    </tr>
                </tfoot>
            </table>

            <div style="margin-top: 15px; border: 1px solid #64748B; padding: 8px;">
                <strong>إحصائيات اليوم الغذائي والتذاكر:</strong><br>
                • عدد وجبات الفطور: <strong>{meal_rec['bf_total']}</strong> | 
                • عدد وجبات الغداء: <strong>{meal_rec['lu_total']}</strong> | 
                • عدد وجبات العشاء: <strong>{meal_rec['di_total']}</strong> | 
                • معدل المستفيدين )غداء+عشاء(/2: <strong>{self._fmt_excel_qty(meal_rec.get('average_daily_meals', 0))}</strong> | 
                • تكلفة اليوم الغذائي للطالب: <strong>{meal_rec['student_daily_cost']:,.2f} دج</strong>
            </div>

            {daily_note_html}

            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="width:100%; margin-top:20px; border-collapse:collapse;">
                <tr>
                    <td width="33%" align="center" style="width:33%; text-align:center; font-weight:bold; font-size:12px; border:none;">مدير الإقامة الجامعية</td>
                    <td width="34%" align="center" style="width:34%; text-align:center; font-weight:bold; font-size:12px; border:none;">رئيس مصلحة الإطعام</td>
                    <td width="33%" align="center" style="width:33%; text-align:center; font-weight:bold; font-size:12px; border:none;">مسير المطعم / المخزني</td>
                </tr>
                <tr>
                    <td align="center" style="padding-top:35px; text-align:center; border:none; color:#94A3B8;">...................................</td>
                    <td align="center" style="padding-top:35px; text-align:center; border:none; color:#94A3B8;">...................................</td>
                    <td align="center" style="padding-top:35px; text-align:center; border:none; color:#94A3B8;">...................................</td>
                </tr>
            </table>
        </body>
        </html>
        """
        return html

    # -------------------------------------------------------------
    # 2. تصدير بطاقة الجرد الشهري العام إلى Excel (مثل ورقة جرد)
    # -------------------------------------------------------------
    def export_monthly_inventory_excel(self, year: Optional[int] = None, month: Optional[int] = None, save_path: str = "", start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """تصدير بطاقة الجرد الشهري أو لفترة مخصصة إلى ملف Excel مطابق 100% لورقة جرد في Excel بـ 14 عموداً"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "جرد"
        ws.sheet_view.rightToLeft = True

        res_name = self.get_residence_name_ar()
        dir_name = self.get_directorate_name_ar()
        if start_date and end_date:
            period_title = f"جدول الجرد للفترة من {start_date} إلى {end_date}"
            inventory_data = self.stock_svc.get_monthly_inventory(start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        else:
            m_name = self._get_arabic_month_name(month or 1)
            period_title = f"جدول الجرد الشهري لشهر {m_name} {year or ''}"
            inventory_data = self.stock_svc.get_monthly_inventory(year, month, residence_id=self.residence_id)

        # ترويسة الصفحة
        ws.merge_cells("A1:N1")
        ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية - وزارة التعليم العالي والبحث العلمي"
        ws["A1"].font = Font(name="Segoe UI", size=11, bold=True)
        ws["A1"].alignment = Alignment(horizontal="center")

        ws.merge_cells("A2:N2")
        ws["A2"] = f"{dir_name} - {res_name} - {period_title}"
        ws["A2"].font = Font(name="Segoe UI", size=13, bold=True, color="0F2D25")
        ws["A2"].alignment = Alignment(horizontal="center")

        header_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        header_font = Font(name="Segoe UI", size=10, bold=True)
        thin_border = Border(
            left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000")
        )

        # 3 صفوف عناوين رئيسية
        ws.merge_cells("A4:A6"); ws["A4"] = "إسم المادة"
        ws.merge_cells("B4:B6"); ws["B4"] = "سعر الوحدة"
        ws.merge_cells("C4:D5"); ws["C4"] = "مخزون أول مدة"
        ws.merge_cells("E4:H4"); ws["E4"] = "المدخولات"
        ws.merge_cells("E5:F5"); ws["E5"] = "توريد"
        ws.merge_cells("G5:H5"); ws["G5"] = "إستعارة"
        ws.merge_cells("I4:L4"); ws["I4"] = "مخروجات"
        ws.merge_cells("I5:J5"); ws["I5"] = "إستهلاك"
        ws.merge_cells("K5:L5"); ws["K5"] = "إعارة"
        ws.merge_cells("M4:N5"); ws["M4"] = "مخزون نهاية مدة"

        for c, text in enumerate(["كمية", "المبلغ", "كمية", "المبلغ", "كمية", "المبلغ", "كمية", "المبلغ", "كمية", "المبلغ", "كمية", "المبلغ"], start=3):
            ws.cell(6, c, text)

        for r in range(4, 7):
            for c in range(1, 15):
                cell = ws.cell(r, c)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

        # تعبئة البيانات
        row_idx = 7
        for item in inventory_data:
            ws.cell(row_idx, 1, item["name"]).alignment = Alignment(horizontal="right")
            ws.cell(row_idx, 2, item["price_ttc"]).number_format = "#,##0.00"

            ws.cell(row_idx, 3, item["initial_qty"])
            ws.cell(row_idx, 4, item["initial_val"]).number_format = "#,##0.00"
            ws.cell(row_idx, 5, item["supply_qty"])
            ws.cell(row_idx, 6, item["supply_val"]).number_format = "#,##0.00"
            ws.cell(row_idx, 7, item["loan_in_qty"])
            ws.cell(row_idx, 8, item["loan_in_val"]).number_format = "#,##0.00"
            ws.cell(row_idx, 9, item["cons_qty"])
            ws.cell(row_idx, 10, item["cons_val"]).number_format = "#,##0.00"
            ws.cell(row_idx, 11, item["loan_out_qty"])
            ws.cell(row_idx, 12, item["loan_out_val"]).number_format = "#,##0.00"
            ws.cell(row_idx, 13, item["final_qty"])
            ws.cell(row_idx, 14, item["final_val"]).number_format = "#,##0.00"

            for c in range(1, 15):
                ws.cell(row_idx, c).border = thin_border
            row_idx += 1

        # صف المجاميع
        ws.cell(row_idx, 1, "المجــــــــاميع الإجماليـــــة").font = Font(name="Segoe UI", bold=True)
        for col_val in [4, 6, 8, 10, 12, 14]:
            col_letter = openpyxl.utils.get_column_letter(col_val)
            ws.cell(row_idx, col_val, f"=SUM({col_letter}7:{col_letter}{row_idx-1})").font = Font(name="Segoe UI", bold=True)
            ws.cell(row_idx, col_val).number_format = "#,##0.00"

        for c in range(1, 15):
            ws.cell(row_idx, c).border = thin_border
            ws.cell(row_idx, c).fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

        # ضبط عرض الأعمدة
        ws.column_dimensions["A"].width = 28
        ws.column_dimensions["B"].width = 13
        for c_ltr in ["C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N"]:
            ws.column_dimensions[c_ltr].width = 12

        wb.save(save_path)
        return save_path

    # -------------------------------------------------------------
    # 3. توابع مساعدة للغة العربية
    # -------------------------------------------------------------
    def _get_arabic_month_name(self, month: Any) -> str:
        try:
            m = int(month)
            names = ["جانفي", "فيفري", "مارس", "أفريل", "ماي", "جوان", "جويلية", "أوت", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
            return names[m - 1] if 1 <= m <= 12 else str(month)
        except Exception:
            return str(month)

    def _get_arabic_weekday(self, date_str: str) -> str:
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            days = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
            return days[dt.weekday()]
        except Exception:
            return ""

    def _split_into_4_lines(self, text: str) -> List[str]:
        if not text:
            return ["..", "..", "..", ".."]
        if "\n" in text:
            parts = [p.strip() for p in text.split("\n") if p.strip()]
        elif "،" in text:
            parts = [p.strip() for p in text.split("،") if p.strip()]
        elif "," in text:
            parts = [p.strip() for p in text.split(",") if p.strip()]
        else:
            parts = [text.strip()]
        res = parts[:4]
        while len(res) < 4:
            res.append("..")
        return res

    def _fmt_excel_amount(self, val: float) -> str:
        if abs(val) < 0.001:
            return ".00"
        return f"{val:,.2f}"

    def _fmt_excel_qty(self, val: float) -> str:
        if abs(val) < 0.001:
            return "0"
        if abs(val - int(val)) < 0.001:
            return str(int(val))
        return f"{val:g}"

    # -------------------------------------------------------------
    # 4. ورقة الاستهلاك اليومي الرسمية (مطابقة لورقة مطبوعة في Excel)
    # -------------------------------------------------------------
    def _generate_single_daily_voucher_content(self, date_str: str, is_last: bool = False) -> str:
        """توليد محتوى ورقة يوم واحد مع كامل الجداول والخطوط الواضحة"""
        res_name = self.get_residence_name_ar()
        res_clean = self.get_clean_residence_name()
        dir_name = self.get_directorate_name_ar()
        onou_name = self.db.get_setting("onou_name", "الديوان الوطني للخدمات الجامعية")

        sheet_data = self.stock_svc.get_daily_sheet_data(date_str, self.residence_id)
        articles = [a for a in sheet_data["articles"] if (a["bf_qty"] > 0 or a["lu_qty"] > 0 or a["di_qty"] > 0 or a["loan_out_qty"] > 0)]
        meals = sheet_data["meals"]

        weekday = self._get_arabic_weekday(date_str)
        dt_parts = date_str.split("-")
        y, m, d = dt_parts[0], int(dt_parts[1]), dt_parts[2]

        loan_notes = self.stock_svc.get_loan_notes_for_daily_sheet(date_str, self.residence_id)
        loan_notes_html = ""
        if loan_notes:
            notes_items = "".join(f"<li style='margin: 2px 0;'><strong>ملاحظة :</strong> {n}</li>" for n in loan_notes)
            loan_notes_html = f"""
            <div style="margin-top:6px; margin-bottom:4px; border:1px solid #000000; padding:4px 8px; background:#F8FAFC; font-size:9pt; text-align:right;">
                <span style="font-weight:bold; color:#0F2D25; text-decoration:underline;">ملاحظات حركة الإعارة والاستعارة الرسمية:</span>
                <ul style="margin:3px 0 2px 0; padding-right:20px; list-style-type:square;">
                    {notes_items}
                </ul>
            </div>
            """

        daily_note = (meals.get("notes") or "").strip()
        if daily_note:
            daily_note_html = f"""
            <div style="margin-top:3px; margin-bottom:3px; border:1px solid #000000; padding:2px 6px; background:#FFF; font-size:9pt; text-align:right;">
                <span style="font-weight:bold; color:#0F2D25;">ملاحظـــــة : </span>
                <span style="font-weight:bold; color:#000000;">{daily_note}</span>
            </div>
            """
        else:
            daily_note_html = """
            <div style="margin-top:3px; margin-bottom:3px; border:1px solid #000000; padding:2px 6px; background:#FFF; font-size:9pt; text-align:right;">
                <span style="font-weight:bold; color:#0F2D25;">ملاحظـــــة : </span>
                <span style="color:#64748B;">................................................................................................................................................................................................................</span>
            </div>
            """

        logo_img_html = self.get_logo_img_html(36)

        calc_tot_bf = 0.0
        calc_tot_lu = 0.0
        calc_tot_di = 0.0
        rows_html = ""
        for i, a in enumerate(articles, 1):
            p_ttc = round(float(a.get("price_ttc", 0.0) or 0.0), 2)
            c_bf = round(float(a.get("bf_qty", 0.0) or 0.0) * p_ttc, 2)
            c_lu = round(float(a.get("lu_qty", 0.0) or 0.0) * p_ttc, 2)
            c_di = round(float(a.get("di_qty", 0.0) or 0.0) * p_ttc, 2)
            tot_exp = round(c_bf + c_lu + c_di, 2)
            tot_q = a["bf_qty"] + a["lu_qty"] + a["di_qty"]

            calc_tot_bf = round(calc_tot_bf + c_bf, 2)
            calc_tot_lu = round(calc_tot_lu + c_lu, 2)
            calc_tot_di = round(calc_tot_di + c_di, 2)

            rows_html += f"""
            <tr>
                <td style="border:1px solid #000000; text-align:right; font-weight:bold; padding:0px 2px;">{tot_exp:,.2f}</td>
                <td style="border:1px solid #000000; text-align:center; font-weight:bold; padding:0px 2px;">{tot_q if tot_q > 0 else '-'}</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{c_di:,.2f}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{a['di_qty'] if a['di_qty'] > 0 else '-'}</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{c_lu:,.2f}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{a['lu_qty'] if a['lu_qty'] > 0 else '-'}</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{c_bf:,.2f}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{a['bf_qty'] if a['bf_qty'] > 0 else '-'}</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{p_ttc:,.2f}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{a['unit']}</td>
                <td style="border:1px solid #000000; font-weight:bold; text-align:right; padding:0px 3px;">{a['name']}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{i:02d}</td>
            </tr>
            """

        tot_bf = calc_tot_bf
        tot_lu = calc_tot_lu
        tot_di = calc_tot_di
        grand_tot = round(tot_bf + tot_lu + tot_di, 2)

        bf_cnt = meals.get("bf_total", 0)
        lu_cnt = meals.get("lu_total", 0)
        di_cnt = meals.get("di_total", 0)

        # معدل الوجبات بدقة تامة
        if di_cnt == 0:
            avg_m = float(lu_cnt)
        else:
            avg_m = float((lu_cnt + di_cnt) / 2.0)

        cost_bf_stud = (tot_bf / bf_cnt) if bf_cnt > 0 else 0.0
        cost_lu_stud = (tot_lu / lu_cnt) if lu_cnt > 0 else 0.0
        cost_di_stud = (tot_di / di_cnt) if di_cnt > 0 else 0.0

        if di_cnt > 0 and (lu_cnt + di_cnt) > 0:
            student_cost = grand_tot / float(lu_cnt + di_cnt)
        elif lu_cnt > 0:
            student_cost = grand_tot / float(lu_cnt)
        else:
            student_cost = 0.0

        return f"""
        <div class="voucher-sheet" style="padding: 1px 4px; margin: 0; box-sizing: border-box; page-break-inside: avoid;">
            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="width:100%; margin-bottom:4px; border-collapse:collapse;">
                <tr>
                    <td colspan="3" align="center" style="text-align:center; font-size:10.5pt; font-weight:bold; padding-bottom:1px; border:none;">
                        الجمهورية الجزائرية الديمقراطية الشعبية
                    </td>
                </tr>
                <tr>
                    <td width="38%" align="right" style="width:38%; text-align:right; font-size:8.5pt; font-weight:bold; vertical-align:middle; border:none; line-height:1.25;">
                        وزارة التعليم العالي والبحث العلمي<br>
                        {onou_name}<br>
                        {dir_name}<br>
                        {res_name}
                    </td>
                    <td width="24%" align="center" style="width:24%; text-align:center; vertical-align:middle; border:none;">
                        {logo_img_html}
                    </td>
                    <td width="38%" align="left" style="width:38%; text-align:left; font-size:8pt; font-weight:bold; vertical-align:middle; border:none; line-height:1.25; direction:ltr;">
                        RÉPUBLIQUE ALGÉRIENNE DÉMOCRATIQUE ET POPULAIRE<br>
                        MINISTÈRE DE L'ENSEIGNEMENT SUPÉRIEUR<br>
                        OFFICE NATIONAL DES ŒUVRES UNIVERSITAIRES<br>
                        DIRECTION DES ŒUVRES UNIVERSITAIRES OUARGLA POLE
                    </td>
                </tr>
                <tr>
                    <td colspan="3" align="center" style="text-align:center; font-size:12.5pt; font-weight:bold; padding: 1px 0; border:none;">
                        ورقــة الإسـتـهـلاك اليومـــي &nbsp;&nbsp;&nbsp;&nbsp; ليـــــوم : {weekday} {d} / {m:02d} / {y}
                    </td>
                </tr>
            </table>

            <table class="main-layout" width="100%" style="width:100%; border-collapse:collapse;">
            <tr>
                <!-- اللوحة الجانبية -->
                <td class="side-panel" style="width:205px; padding-left:6px; vertical-align:top; border:none;">
                    <div class="box" style="border:1px solid #000; padding:2px 4px; margin-bottom:3px; background:#FFF;">
                        <div class="box-title" style="font-weight:bold; border-bottom:1px solid #000; padding-bottom:1px; margin-bottom:2px; font-size:8.5pt;">معلومات عامة عن المصاريف</div>
                        <table style="width:100%; font-size:10px; border-collapse:collapse;">
                            <tr><td style="border:none;">فطور الصباح:</td><td style="text-align:left; font-weight:bold; border:none;">{tot_bf:,.2f} دج</td></tr>
                            <tr><td style="border:none;">وجبـة الغذاء:</td><td style="text-align:left; font-weight:bold; border:none;">{tot_lu:,.2f} دج</td></tr>
                            <tr><td style="border:none;">وجبة العشاء:</td><td style="text-align:left; font-weight:bold; border:none;">{tot_di:,.2f} دج</td></tr>
                            <tr style="border-top:1px solid #000;"><td style="font-weight:bold; border:none;">المجموع الكلي:</td><td style="text-align:left; font-weight:bold; color:#0D9488; border:none;">{grand_tot:,.2f} دج</td></tr>
                        </table>
                    </div>

                    <div class="box" style="border:1px solid #000; padding:2px 4px; margin-bottom:3px; background:#FFF;">
                        <div class="box-title" style="font-weight:bold; border-bottom:1px solid #000; padding-bottom:1px; margin-bottom:2px; font-size:8.5pt;">تعداد التذاكر</div>
                        <table class="mini-table" width="100%" border="1" cellspacing="0" cellpadding="2" style="width:100%; border-collapse:collapse; font-size:8pt; border:1px solid #000;">
                            <tr>
                                <th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:1px 2px;">عشاء</th>
                                <th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:1px 2px;">غداء</th>
                                <th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:1px 2px;">فطور</th>
                                <th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:1px 2px;">الفئة</th>
                            </tr>
                            <tr>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('di_students',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('lu_students',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('bf_students',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">طلبة</td>
                            </tr>
                            <tr>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('di_staff',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('lu_staff',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('bf_staff',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">عمال</td>
                            </tr>
                            <tr>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('di_professors',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('lu_professors',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('bf_professors',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">أساتذة</td>
                            </tr>
                            <tr>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('di_guests',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('lu_guests',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('bf_guests',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">ضيوف</td>
                            </tr>
                            <tr>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('di_free',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('lu_free',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('bf_free',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">مجان</td>
                            </tr>
                            <tr style="font-weight:bold; background:#E2E8F0;">
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('di_total',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('lu_total',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">{meals.get('bf_total',0)}</td>
                                <td style="border:1px solid #000; text-align:center; padding:1px 2px;">المجموع</td>
                            </tr>
                        </table>
                        <div style="margin-top:4px; font-weight:bold; font-size:10px; color:#0284C7;">
                            معدل الوجبات (غداء+عشاء)/2 : {self._fmt_excel_qty(avg_m)}
                        </div>
                    </div>

                    <div class="box" style="border:1px solid #000; padding:2px 4px; margin-bottom:3px; background:#FFF;">
                        <div class="box-title" style="font-weight:bold; border-bottom:1px solid #000; padding-bottom:1px; margin-bottom:2px; font-size:8.5pt;">التكلفة اليومية للطالب</div>
                        <table style="width:100%; font-size:10px; border-collapse:collapse;">
                            <tr><td style="border:none;">تكلفة فطور:</td><td style="text-align:left; border:none;">{cost_bf_stud:,.2f} دج</td></tr>
                            <tr><td style="border:none;">تكلفة الغداء:</td><td style="text-align:left; border:none;">{cost_lu_stud:,.2f} دج</td></tr>
                            <tr><td style="border:none;">تكلفة العشاء:</td><td style="text-align:left; border:none;">{cost_di_stud:,.2f} دج</td></tr>
                            <tr style="border-top:1px solid #000; font-weight:bold;">
                                <td style="border:none;">الوجبة اليومية:</td><td style="text-align:left; color:#DC2626; border:none;">{student_cost:,.2f} دج</td>
                            </tr>
                        </table>
                    </div>

                    <div class="box" style="border:1px solid #000; padding:2px 4px; margin-bottom:3px; background:#FFF;">
                        <div class="box-title" style="font-weight:bold; border-bottom:1px solid #000; padding-bottom:1px; margin-bottom:2px; font-size:8.5pt;">قائمة الأكل المقدم</div>
                        <div style="font-size:10px;">
                            <strong>فطور:</strong> {meals.get('menu_breakfast') or '-'}<br>
                            <strong>غداء:</strong> {meals.get('menu_lunch') or '-'}<br>
                            <strong>عشاء:</strong> {meals.get('menu_dinner') or '-'}
                        </div>
                    </div>
                </td>

                <!-- جدول المواد المستهلكة -->
                <td style="vertical-align:top; border:none;">
                    <table class="data-table" width="100%" border="1" cellspacing="0" cellpadding="3" style="width:100%; border-collapse:collapse; font-size:8.5pt; border:1px solid #000000;">
                        <thead>
                            <tr>
                                <th colspan="2" style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">المجموع</th>
                                <th colspan="2" style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">وجبة العشاء</th>
                                <th colspan="2" style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">وجبة الغداء</th>
                                <th colspan="2" style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">فطور الصباح</th>
                                <th rowspan="2" style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">السعر TTC</th>
                                <th rowspan="2" style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">الوحدة</th>
                                <th rowspan="2" style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">إسم المادة</th>
                                <th rowspan="2" style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">رقم</th>
                            </tr>
                            <tr>
                                <th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">المبلغ</th><th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">كمية</th>
                                <th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">المبلغ</th><th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">كمية</th>
                                <th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">المبلغ</th><th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">كمية</th>
                                <th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">المبلغ</th><th style="border:1px solid #000; background:#F1F5F9; text-align:center; padding:2px 3px;">كمية</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html if rows_html else '<tr><td colspan="12" style="text-align:center; padding:15px; color:#64748B; border:1px solid #000;">لا توجد مواد مستهلكة مسجلة في هذا اليوم</td></tr>'}
                        </tbody>
                        <tfoot>
                            <tr style="background:#F1F5F9; font-weight:bold;">
                                <td style="border:1px solid #000; text-align:right; color:#0F2D25; font-size:11px; padding:2px 3px;">{grand_tot:,.2f} دج</td>
                                <td style="border:1px solid #000; text-align:center; padding:2px 3px;">-</td>
                                <td style="border:1px solid #000; text-align:right; padding:2px 3px;">{tot_di:,.2f}</td>
                                <td style="border:1px solid #000; text-align:center; padding:2px 3px;">-</td>
                                <td style="border:1px solid #000; text-align:right; padding:2px 3px;">{tot_lu:,.2f}</td>
                                <td style="border:1px solid #000; text-align:center; padding:2px 3px;">-</td>
                                <td style="border:1px solid #000; text-align:right; padding:2px 3px;">{tot_bf:,.2f}</td>
                                <td style="border:1px solid #000; text-align:center; padding:2px 3px;">-</td>
                                <td colspan="4" style="border:1px solid #000; text-align:center; padding:2px 3px;">المجـــــــــاميع الإجماليـــــة</td>
                            </tr>
                        </tfoot>
                    </table>
                </td>
            </tr>
            </table>

            {loan_notes_html}

            {daily_note_html}

            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="width:100%; margin-top:2px; border-collapse:collapse;">
                <tr>
                    <td width="33%" align="center" style="width:33%; text-align:center; font-weight:bold; font-size:9.5pt; border:none;">إمضاء مدير الإقامة الجامعية</td>
                    <td width="34%" align="center" style="width:34%; text-align:center; font-weight:bold; font-size:9.5pt; border:none;">إمضاء رئيس مصلحة الإطعام</td>
                    <td width="33%" align="center" style="width:33%; text-align:center; font-weight:bold; font-size:9.5pt; border:none;">إمضاء مخزني الإطعام</td>
                </tr>
                <tr>
                    <td align="center" style="padding-top:2px; text-align:center; border:none; color:#94A3B8;">...................................</td>
                    <td align="center" style="padding-top:2px; text-align:center; border:none; color:#94A3B8;">...................................</td>
                    <td align="center" style="padding-top:2px; text-align:center; border:none; color:#94A3B8;">...................................</td>
                </tr>
            </table>
        </div>
        """

    def generate_daily_voucher_html_v2(self, date_str: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """توليد ورقة أو أوراق الاستهلاك اليومي مطابقة 100% لورقة مطبوعة الرسمية في Excel"""
        if start_date and end_date:
            d_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            d_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            cur_d = d_start
            date_list = []
            while cur_d <= d_end:
                date_list.append(cur_d.isoformat())
                cur_d += datetime.timedelta(days=1)
            total_days = len(date_list)
            pages = []
            for idx, d_iso in enumerate(date_list):
                pb_div = '<div style="page-break-before: always; height:0; line-height:0; margin:0; padding:0; clear:both;"></div>\n' if idx > 0 else ''
                pages.append(f"{pb_div}{self._generate_single_daily_voucher_content(d_iso, is_last=(idx == total_days - 1))}")
            content = "\n".join(pages)
            title = f"أوراق الاستهلاك للفترة من {start_date} إلى {end_date}"
        else:
            d_str = date_str or (TimeService.today_str() if TimeService else datetime.date.today().isoformat())
            content = self._generate_single_daily_voucher_content(d_str, is_last=True)
            title = f"ورقة الاستهلاك اليومي - {d_str}"

        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; margin: 0; font-size: 8.5pt; color: #000; }}
    table.data-table {{ width: 100%; border-collapse: collapse; font-size: 8.5pt; border: 1px solid #000; }}
    table.data-table th, table.data-table td {{ border: 1px solid #000; padding: 2px 3px; white-space: nowrap; }}
    table.data-table th {{ background-color: #F1F5F9; text-align: center; font-weight: bold; font-size: 8.5pt; }}
    table.mini-table {{ width: 100%; border-collapse: collapse; font-size: 8pt; border: 1px solid #000; }}
    table.mini-table th, table.mini-table td {{ border: 1px solid #000; padding: 1px 2px; text-align: center; white-space: nowrap; }}
    table.mini-table th {{ background-color: #F1F5F9; }}
    .voucher-sheet {{ margin: 0; padding: 4px 6px; }}
</style>
</head>
<body>
{content}
</body>
</html>"""

    def export_daily_voucher_excel(self, date_str: Optional[str] = None, save_path: str = "", start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """تصدير ورقة أو أوراق الاستهلاك اليومي إلى Excel مطابقة 100% للورقة الرسمية"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        res_name = self.get_residence_name_ar()
        dir_name = self.get_directorate_name_ar()
        onou_name = self.db.get_setting("onou_name", "الديوان الوطني للخدمات الجامعية")

        if start_date and end_date:
            d_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            d_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            cur_d = d_start
            dates = []
            while cur_d <= d_end:
                dates.append(cur_d.isoformat())
                cur_d += datetime.timedelta(days=1)
        else:
            d_str = date_str or (TimeService.today_str() if TimeService else datetime.date.today().isoformat())
            dates = [d_str]

        header_font = Font(name="Segoe UI", size=10, bold=True)
        title_font = Font(name="Segoe UI", size=14, bold=True)
        sub_font = Font(name="Segoe UI", size=11, bold=True)
        bold_font = Font(name="Segoe UI", size=10, bold=True)
        regular_font = Font(name="Segoe UI", size=10)

        header_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        highlight_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        green_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
        white_bold_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")

        thin_border = Border(
            left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000")
        )

        for d_iso in dates:
            sheet_data = self.stock_svc.get_daily_sheet_data(d_iso, self.residence_id)
            articles = [a for a in sheet_data["articles"] if (a["bf_qty"] > 0 or a["lu_qty"] > 0 or a["di_qty"] > 0 or a["loan_out_qty"] > 0)]
            meals = sheet_data["meals"]

            weekday = self._get_arabic_weekday(d_iso)
            dt_parts = d_iso.split("-")
            y, m, d = dt_parts[0], int(dt_parts[1]), dt_parts[2]

            sheet_title = f"{d}-{m:02d}" if len(dates) > 1 else "ورقة الاستهلاك"
            ws = wb.create_sheet(title=sheet_title)
            ws.sheet_view.rightToLeft = True

            # 1. Government Header
            ws.merge_cells("A1:L1")
            ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية"
            ws["A1"].font = sub_font; ws["A1"].alignment = Alignment(horizontal="center")

            ws.merge_cells("A2:F2")
            ws["A2"] = f"وزارة التعليم العالي والبحث العلمي - {onou_name}"
            ws["A2"].font = bold_font; ws["A2"].alignment = Alignment(horizontal="right")

            ws.merge_cells("G2:L2")
            ws["G2"] = f"{dir_name} - {res_name}"
            ws["G2"].font = bold_font; ws["G2"].alignment = Alignment(horizontal="left")

            ws.merge_cells("A3:L3")
            ws["A3"] = "ورقــة الإسـتـهـلاك اليومـــي"
            ws["A3"].font = title_font; ws["A3"].alignment = Alignment(horizontal="center")

            ws.merge_cells("A4:L4")
            ws["A4"] = f"ليـــــوم : {weekday} {d} / {m:02d} / {y}"
            ws["A4"].font = sub_font; ws["A4"].alignment = Alignment(horizontal="center")

            # 2. Side Panel / Summary Block
            ws.merge_cells("A6:D6"); ws["A6"] = "معلومات عامة عن المصاريف"
            ws["A6"].fill = green_fill; ws["A6"].font = white_bold_font; ws["A6"].alignment = Alignment(horizontal="center")

            tot_bf = sheet_data["tot_bf_expense"]
            tot_lu = sheet_data["tot_lu_expense"]
            tot_di = sheet_data["tot_di_expense"]
            grand_tot = sheet_data["grand_total_expense"]

            expenses = [
                ("فطور الصباح:", tot_bf),
                ("وجبـة الغداء:", tot_lu),
                ("وجبة العشاء:", tot_di),
                ("المجموع الكلي:", grand_tot),
            ]
            for idx_e, (lbl, val) in enumerate(expenses, 7):
                ws.merge_cells(f"A{idx_e}:B{idx_e}"); ws[f"A{idx_e}"] = lbl
                ws[f"A{idx_e}"].font = bold_font; ws[f"A{idx_e}"].alignment = Alignment(horizontal="right")
                ws.merge_cells(f"C{idx_e}:D{idx_e}"); ws[f"C{idx_e}"] = f"{val:,.2f} دج"
                ws[f"C{idx_e}"].font = bold_font; ws[f"C{idx_e}"].alignment = Alignment(horizontal="left")
                for c in range(1, 5): ws.cell(idx_e, c).border = thin_border

            # Box 2: تعداد التذاكر
            ws.merge_cells("A12:D12"); ws["A12"] = "تعداد التذاكر"
            ws["A12"].fill = green_fill; ws["A12"].font = white_bold_font; ws["A12"].alignment = Alignment(horizontal="center")
            ws["A13"] = "الفئة"; ws["B13"] = "فطور"; ws["C13"] = "غداء"; ws["D13"] = "عشاء"
            for c in range(1, 5):
                ws.cell(13, c).fill = header_fill; ws.cell(13, c).font = bold_font
                ws.cell(13, c).alignment = Alignment(horizontal="center"); ws.cell(13, c).border = thin_border

            ticket_rows = [
                ("طلبة", meals.get('bf_students', 0), meals.get('lu_students', 0), meals.get('di_students', 0)),
                ("عمال", meals.get('bf_staff', 0), meals.get('lu_staff', 0), meals.get('di_staff', 0)),
                ("أساتذة", meals.get('bf_professors', 0), meals.get('lu_professors', 0), meals.get('di_professors', 0)),
                ("ضيوف", meals.get('bf_guests', 0), meals.get('lu_guests', 0), meals.get('di_guests', 0)),
                ("مجان", meals.get('bf_free', 0), meals.get('lu_free', 0), meals.get('di_free', 0)),
                ("المجموع", meals.get('bf_total', 0), meals.get('lu_total', 0), meals.get('di_total', 0)),
            ]
            for idx_t, (cat, bf, lu, di) in enumerate(ticket_rows, 14):
                ws.cell(idx_t, 1, cat).alignment = Alignment(horizontal="center")
                ws.cell(idx_t, 2, bf).alignment = Alignment(horizontal="center")
                ws.cell(idx_t, 3, lu).alignment = Alignment(horizontal="center")
                ws.cell(idx_t, 4, di).alignment = Alignment(horizontal="center")
                for c in range(1, 5):
                    ws.cell(idx_t, c).border = thin_border
                    if cat == "المجموع":
                        ws.cell(idx_t, c).font = bold_font
                        ws.cell(idx_t, c).fill = highlight_fill

            # Box 3: معدل الوجبات والتكلفة اليومية
            bf_cnt = meals.get("bf_total", 0)
            lu_cnt = meals.get("lu_total", 0)
            di_cnt = meals.get("di_total", 0)
            if di_cnt == 0:
                avg_m = float(lu_cnt)
            else:
                avg_m = float((lu_cnt + di_cnt) / 2.0)

            cost_bf_stud = (tot_bf / bf_cnt) if bf_cnt > 0 else 0.0
            cost_lu_stud = (tot_lu / lu_cnt) if lu_cnt > 0 else 0.0
            cost_di_stud = (tot_di / di_cnt) if di_cnt > 0 else 0.0

            if di_cnt > 0 and (lu_cnt + di_cnt) > 0:
                student_cost = grand_tot / float(lu_cnt + di_cnt)
            elif lu_cnt > 0:
                student_cost = grand_tot / float(lu_cnt)
            else:
                student_cost = 0.0

            ws.merge_cells("A21:D21"); ws["A21"] = f"معدل الوجبات: {self._fmt_excel_qty(avg_m)} | تكلفة الوجبة اليومية: {student_cost:,.2f} دج"
            ws["A21"].font = bold_font; ws["A21"].alignment = Alignment(horizontal="center")
            ws["A21"].fill = highlight_fill
            for c in range(1, 5): ws.cell(21, c).border = thin_border

            # Box 4: قائمة الأكل المقدم
            ws.merge_cells("A23:D23"); ws["A23"] = "قائمة الأكل المقدم"
            ws["A23"].fill = green_fill; ws["A23"].font = white_bold_font; ws["A23"].alignment = Alignment(horizontal="center")
            ws.merge_cells("A24:D24"); ws["A24"] = f"فطور: {meals.get('menu_breakfast') or '-'}"
            ws.merge_cells("A25:D25"); ws["A25"] = f"غداء: {meals.get('menu_lunch') or '-'}"
            ws.merge_cells("A26:D26"); ws["A26"] = f"عشاء: {meals.get('menu_dinner') or '-'}"
            for r in range(24, 27):
                ws[f"A{r}"].font = regular_font; ws[f"A{r}"].alignment = Alignment(horizontal="right")
                for c in range(1, 5): ws.cell(r, c).border = thin_border

            # 3. Data Table (Cols E-P)
            headers_r6 = [
                ("E6", "F6", "المجموع"),
                ("G6", "H6", "وجبة العشاء"),
                ("I6", "J6", "وجبة الغداء"),
                ("K6", "L6", "فطور الصباح"),
            ]
            for start_c, end_c, title in headers_r6:
                ws.merge_cells(f"{start_c}:{end_c}")
                ws[start_c] = title
                ws[start_c].font = bold_font; ws[start_c].fill = header_fill
                ws[start_c].alignment = Alignment(horizontal="center", vertical="center")

            ws.merge_cells("M6:M7"); ws["M6"] = "السعر TTC"
            ws.merge_cells("N6:N7"); ws["N6"] = "الوحدة"
            ws.merge_cells("O6:O7"); ws["O6"] = "إسم المادة"
            ws.merge_cells("P6:P7"); ws["P6"] = "رقم"

            for col_letter in ["M", "N", "O", "P"]:
                ws[f"{col_letter}6"].font = bold_font; ws[f"{col_letter}6"].fill = header_fill
                ws[f"{col_letter}6"].alignment = Alignment(horizontal="center", vertical="center")

            ws["E7"] = "المبلغ"; ws["F7"] = "كمية"
            ws["G7"] = "المبلغ"; ws["H7"] = "كمية"
            ws["I7"] = "المبلغ"; ws["J7"] = "كمية"
            ws["K7"] = "المبلغ"; ws["L7"] = "كمية"
            for c in range(5, 17):
                ws.cell(7, c).font = bold_font; ws.cell(7, c).fill = header_fill
                ws.cell(7, c).alignment = Alignment(horizontal="center", vertical="center")
                ws.cell(6, c).border = thin_border; ws.cell(7, c).border = thin_border

            # Data Rows
            cur_r = 8
            for i, a in enumerate(articles, 1):
                tot_q = a["bf_qty"] + a["lu_qty"] + a["di_qty"]
                ws.cell(cur_r, 5, a["total_expense"]).number_format = "#,##0.00"
                ws.cell(cur_r, 5).font = bold_font
                ws.cell(cur_r, 6, tot_q if tot_q > 0 else "-")
                ws.cell(cur_r, 7, a["cost_di"]).number_format = "#,##0.00"
                ws.cell(cur_r, 8, a["di_qty"] if a["di_qty"] > 0 else "-")
                ws.cell(cur_r, 9, a["cost_lu"]).number_format = "#,##0.00"
                ws.cell(cur_r, 10, a["lu_qty"] if a["lu_qty"] > 0 else "-")
                ws.cell(cur_r, 11, a["cost_bf"]).number_format = "#,##0.00"
                ws.cell(cur_r, 12, a["bf_qty"] if a["bf_qty"] > 0 else "-")
                ws.cell(cur_r, 13, a["price_ttc"]).number_format = "#,##0.00"
                ws.cell(cur_r, 14, a["unit"])
                ws.cell(cur_r, 15, a["name"]).font = bold_font
                ws.cell(cur_r, 16, i)

                ws.cell(cur_r, 5).alignment = Alignment(horizontal="right")
                ws.cell(cur_r, 6).alignment = Alignment(horizontal="center")
                ws.cell(cur_r, 7).alignment = Alignment(horizontal="right")
                ws.cell(cur_r, 8).alignment = Alignment(horizontal="center")
                ws.cell(cur_r, 9).alignment = Alignment(horizontal="right")
                ws.cell(cur_r, 10).alignment = Alignment(horizontal="center")
                ws.cell(cur_r, 11).alignment = Alignment(horizontal="right")
                ws.cell(cur_r, 12).alignment = Alignment(horizontal="center")
                ws.cell(cur_r, 13).alignment = Alignment(horizontal="right")
                ws.cell(cur_r, 14).alignment = Alignment(horizontal="center")
                ws.cell(cur_r, 15).alignment = Alignment(horizontal="right")
                ws.cell(cur_r, 16).alignment = Alignment(horizontal="center")

                for c in range(5, 17):
                    ws.cell(cur_r, c).border = thin_border
                cur_r += 1

            # Totals Row
            ws.cell(cur_r, 5, grand_tot).number_format = "#,##0.00"
            ws.cell(cur_r, 5).font = bold_font
            ws.cell(cur_r, 6, "-").alignment = Alignment(horizontal="center")
            ws.cell(cur_r, 7, tot_di).number_format = "#,##0.00"
            ws.cell(cur_r, 8, "-").alignment = Alignment(horizontal="center")
            ws.cell(cur_r, 9, tot_lu).number_format = "#,##0.00"
            ws.cell(cur_r, 10, "-").alignment = Alignment(horizontal="center")
            ws.cell(cur_r, 11, tot_bf).number_format = "#,##0.00"
            ws.cell(cur_r, 12, "-").alignment = Alignment(horizontal="center")
            ws.merge_cells(f"M{cur_r}:P{cur_r}")
            ws[f"M{cur_r}"] = "المجـــــــــاميع الإجماليـــــة"
            ws[f"M{cur_r}"].font = bold_font; ws[f"M{cur_r}"].alignment = Alignment(horizontal="center")
            for c in range(5, 17):
                ws.cell(cur_r, c).fill = highlight_fill
                ws.cell(cur_r, c).border = thin_border
            cur_r += 1
            # ملاحظات الإعارة والاستعارة في الإكسل
            loan_notes = self.stock_svc.get_loan_notes_for_daily_sheet(d_iso, self.residence_id)
            if loan_notes:
                ws.merge_cells(f"A{cur_r}:P{cur_r}")
                ws[f"A{cur_r}"] = "ملاحظات الإعارة والاستعارة: " + " | ".join(loan_notes)
                ws[f"A{cur_r}"].font = bold_font
                ws[f"A{cur_r}"].alignment = Alignment(horizontal="right")
                cur_r += 2
            else:
                cur_r += 2

            # Daily Note
            note_text = (sheet_data.get("meals") or {}).get("notes") or ""
            ws.merge_cells(f"A{cur_r}:L{cur_r}")
            ws[f"A{cur_r}"] = f"ملاحظـــة : {note_text}" if note_text else "ملاحظـــة : .........................................................................................................................................................."
            ws[f"A{cur_r}"].font = bold_font
            ws[f"A{cur_r}"].alignment = Alignment(horizontal="right")
            cur_r += 2

            # Signatures
            sig_r = max(cur_r, 29)
            ws.merge_cells(f"A{sig_r}:D{sig_r}"); ws[f"A{sig_r}"] = "إمضاء مدير الإقامة الجامعية"
            ws.merge_cells(f"E{sig_r}:H{sig_r}"); ws[f"E{sig_r}"] = "إمضاء رئيس مصلحة الإطعام"
            ws.merge_cells(f"I{sig_r}:L{sig_r}"); ws[f"I{sig_r}"] = "إمضاء مخزني الإطعام"
            for sc in [f"A{sig_r}", f"E{sig_r}", f"I{sig_r}"]:
                ws[sc].font = bold_font; ws[sc].alignment = Alignment(horizontal="center")

            # Column widths
            ws.column_dimensions["A"].width = 16
            ws.column_dimensions["B"].width = 12
            ws.column_dimensions["C"].width = 12
            ws.column_dimensions["D"].width = 12
            ws.column_dimensions["E"].width = 15
            ws.column_dimensions["F"].width = 10
            ws.column_dimensions["G"].width = 13
            ws.column_dimensions["H"].width = 10
            ws.column_dimensions["I"].width = 13
            ws.column_dimensions["J"].width = 10
            ws.column_dimensions["K"].width = 13
            ws.column_dimensions["L"].width = 10
            ws.column_dimensions["M"].width = 14
            ws.column_dimensions["N"].width = 10
            ws.column_dimensions["O"].width = 24
            ws.column_dimensions["P"].width = 8

        save_target = save_path or os.path.join(os.path.expanduser("~"), "Desktop", "ورقة_الاستهلاك_اليومي.xlsx")
        wb.save(save_target)
        return save_target

    # -------------------------------------------------------------
    # 5. الجدول التفصيلي الشهري الرقابي (مطابق لورقة جدول تفصيلي)
    # -------------------------------------------------------------
    def generate_detailed_table_html(self, year: Optional[int] = None, month: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """توليد الجدول التفصيلي الشهري أو لفترة مخصصة مطابق لورقة جدول تفصيلي في Excel بـ 8 أعمدة مع تقسيم صفحات نظيف ومضغوط لاستيعاب أكبر قدر من البيانات بأقل عدد ممكن من الصفحات"""
        if isinstance(year, str) and "-" in year:
            start_date, end_date = year, month
            year, month = None, None
        res_name = self.get_residence_name_ar()
        res_clean = self.get_clean_residence_name()
        dir_name = self.get_directorate_name_ar()
        onou_name = self.db.get_setting("onou_name", "الديوان الوطني للخدمات الجامعية")
        m_name = self._get_arabic_month_name(month or 1)

        items = self.stock_svc.get_detailed_table(year, month, start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        active_items = [it for it in items if (it["initial_stock"] > 0 or it["total_in"] > 0 or it["total_out"] > 0 or it["final_stock"] > 0)]

        if start_date and end_date:
            period_title = f"جدول تفصيلي رقابي للفترة من {start_date} إلى {end_date}"
        else:
            period_title = f"جدول تفصيلي لشهر {m_name} {year}"

        logo_img_html = self.get_logo_img_html(30)
        gov_header_html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom:1px; border-collapse:collapse;">
            <tr>
                <td align="right" style="text-align:right; font-size:7.5pt; font-weight:bold; vertical-align:middle; border:none; width:40%; padding:0;">
                    الجمهورية الجزائرية الديمقراطية الشعبية<br>
                    {dir_name}<br>{res_name}
                </td>
                <td align="center" style="border:none; width:20%; text-align:center; vertical-align:middle; padding:0;">
                    {logo_img_html}
                </td>
                <td align="left" style="text-align:left; font-size:7.5pt; font-weight:bold; vertical-align:middle; border:none; width:40%; padding:0;">
                    وزارة التعليم العالي والبحث العلمي<br>{onou_name}
                </td>
            </tr>
        </table>
        <div style="text-align:center; color:#1E7E34; font-size:11pt; font-weight:bold; margin-top:1px; margin-bottom:3px; white-space:nowrap;">
            {period_title}
        </div>
        """

        thead_html = """
        <thead>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th rowspan="2" style="border:1px solid #000; text-align:center; width:13%; padding:1px 2px;">باقي المخزون</th>
                <th colspan="2" style="border:1px solid #000; text-align:center; width:20%; padding:1px 2px;">المخروجات</th>
                <th colspan="2" style="border:1px solid #000; text-align:center; width:20%; padding:1px 2px;">المدخولات</th>
                <th rowspan="2" style="border:1px solid #000; text-align:center; width:13%; padding:1px 2px;">مخزون أول الشهر</th>
                <th rowspan="2" style="border:1px solid #000; text-align:center; width:9%; padding:1px 2px;">الوحدة</th>
                <th rowspan="2" style="border:1px solid #000; text-align:center; width:25%; padding:1px 2px;">المواد</th>
            </tr>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th style="border:1px solid #000; text-align:center; width:10%; padding:1px 2px;">الإعارة</th>
                <th style="border:1px solid #000; text-align:center; width:10%; padding:1px 2px;">الإستهلاك</th>
                <th style="border:1px solid #000; text-align:center; width:10%; padding:1px 2px;">الإستعارة</th>
                <th style="border:1px solid #000; text-align:center; width:10%; padding:1px 2px;">التوريد</th>
            </tr>
        </thead>
        """

        signatures_html = """
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top:2px; border-collapse:collapse;">
            <tr>
                <td style="width:50%; text-align:center; font-weight:bold; font-size:7.5pt; border:none; padding:0;">
                    إمضاء رئيس مصلحة الإطعام: ..............................
                </td>
                <td style="width:50%; text-align:center; font-weight:bold; font-size:7.5pt; border:none; padding:0;">
                    إمضاء مخزني الإطعام: ..............................
                </td>
            </tr>
        </table>
        """

        # التقسيم الهندسي الذكي للصفحات: حتى 36 مادة في صفحة واحدة، وللجداول الكبيرة 35 مادة للصفحة لتقليص الأوراق
        chunks = []
        if active_items:
            if len(active_items) <= 36:
                chunks = [active_items]
            else:
                c0_size = 35
                chunks.append(active_items[:c0_size])
                rem = active_items[c0_size:]
                while rem:
                    if len(rem) <= 38:
                        chunks.append(rem)
                        break
                    else:
                        chunks.append(rem[:38])
                        rem = rem[38:]
        else:
            chunks = [[]]

        pages_html = []
        for idx, chunk in enumerate(chunks):
            is_last = (idx == len(chunks) - 1)

            if idx == 0:
                header_block = gov_header_html
            else:
                header_block = f"""
                <table width="100%" border="0" style="margin-bottom:2px; border-collapse:collapse;">
                    <tr>
                        <td align="center" style="color:#1E7E34; font-size:10pt; font-weight:bold; border:none;">
                            {period_title} - )تابع - صفحة {idx + 1}(
                        </td>
                    </tr>
                </table>
                """

            rows_html = ""
            for it in chunk:
                sup_str = f"{it['supply_in']:g}" if it['supply_in'] > 0 else '-'
                li_str = f"{it['loan_in']:g}" if it['loan_in'] > 0 else '-'
                cons_str = f"{it['cons_out']:g}" if it['cons_out'] > 0 else '-'
                lo_str = f"{it['loan_out']:g}" if it['loan_out'] > 0 else '-'
                rows_html += f"""
                <tr>
                    <td style="text-align:center; border:1px solid #000; font-weight:bold; color:#0D9488; padding:0px 2px;">{it['final_stock']:g}</td>
                    <td style="text-align:center; border:1px solid #000; padding:0px 2px;">{lo_str}</td>
                    <td style="text-align:center; border:1px solid #000; padding:0px 2px;">{cons_str}</td>
                    <td style="text-align:center; border:1px solid #000; padding:0px 2px;">{li_str}</td>
                    <td style="text-align:center; border:1px solid #000; padding:0px 2px;">{sup_str}</td>
                    <td style="text-align:center; border:1px solid #000; padding:0px 2px;">{it['initial_stock']:g}</td>
                    <td style="text-align:center; border:1px solid #000; padding:0px 2px;">{it['unit']}</td>
                    <td style="font-weight:bold; border:1px solid #000; text-align:right; padding:0px 4px;">{it['name']}</td>
                </tr>
                """

            if not chunk and idx == 0:
                rows_html = '<tr><td colspan="8" style="text-align:center; padding:15px; border:1px solid #000;">لا توجد بيانات مسجلة في هذه الفترة</td></tr>'

            pb_sep = '<div style="page-break-before: always; height:0; line-height:0; margin:0; padding:0; clear:both;"></div>\n' if idx > 0 else ''
            page_div = f"""
            {pb_sep}
            <div class="page-container" style="margin: 0; padding: 0; box-sizing: border-box; page-break-inside: avoid;">
                {header_block}
                <table class="data-table" width="100%" border="1" cellspacing="0" cellpadding="0" style="width:100%; border-collapse:collapse; border:1px solid #000000; font-size:7pt;">
                    {thead_html}
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
                {signatures_html if is_last else ''}
            </div>
            """
            pages_html.append(page_div)

        content = "\n".join(pages_html)
        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<title>{period_title}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; margin: 0; padding: 0; font-size: 7pt; font-weight: bold; color: #000; }}
    table.data-table {{ width: 100%; border-collapse: collapse; border: 1px solid #000000; }}
    table.data-table th, table.data-table td {{ border: 1px solid #000000; padding: 0px 2px; font-size: 7pt; }}
    .page-container {{ margin: 0; padding: 0; }}
</style>
</head>
<body>
{content}
</body>
</html>"""
        return html

    # -------------------------------------------------------------
    # 6. بطاقة متابعة الوجبات الغذائية (مطابقة لورقة بطاقة متابعة الوجبات)
    # -------------------------------------------------------------
    def generate_meal_tracking_html(self, year: Optional[int] = None, month: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """توليد بطاقة متابعة الوجبات مطابقة 100% لورقة بطاقة متابعة الوجبات في Excel ومضغوطة هندسياً لتستوعب الشهر كاملاً (31 يوماً) في صفحة واحدة"""
        if isinstance(year, str) and "-" in year:
            start_date, end_date = year, month
            year, month = None, None
        res_name = self.get_residence_name_ar()
        res_clean = self.get_clean_residence_name()
        dir_name = self.get_directorate_name_ar()
        onou_name = self.db.get_setting("onou_name", "الديوان الوطني للخدمات الجامعية")
        m_name = self._get_arabic_month_name(month or 1)

        rep = self.meals_svc.get_monthly_activity_report(year, month, start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        days = rep["days"]

        if start_date and end_date:
            period_title = f"بطاقة متابعة الوجبات الغذائية للفترة من {start_date} إلى {end_date}"
        else:
            period_title = f"بطاقة متابعة الوجبات الغذائية لشهر {m_name} {year}"

        tot_bf_stud = 0; tot_bf_staff = 0
        tot_lu_stud = 0; tot_lu_staff = 0
        tot_di_stud = 0; tot_di_staff = 0
        tot_expense = 0.0
        tot_avg_4 = 0

        computed_days = []
        with self.db.get_connection() as conn:
            for d in days:
                d_str = d["date"]
                m_row = conn.execute("SELECT * FROM daily_meals_tracking WHERE date = ? AND residence_id = ?", (d_str, self.residence_id)).fetchone()

                bf_st = m_row["bf_students"] if m_row else 0
                bf_sf = (m_row["bf_staff"] + m_row["bf_professors"] + m_row["bf_guests"] + m_row["bf_free"]) if m_row else 0

                lu_st = m_row["lu_students"] if m_row else 0
                lu_sf = (m_row["lu_staff"] + m_row["lu_professors"] + m_row["lu_guests"] + m_row["lu_free"]) if m_row else 0

                di_st = m_row["di_students"] if m_row else 0
                di_sf = (m_row["di_staff"] + m_row["di_professors"] + m_row["di_guests"] + m_row["di_free"]) if m_row else 0

                tot_bf_stud += bf_st; tot_bf_staff += bf_sf
                tot_lu_stud += lu_st; tot_lu_staff += lu_sf
                tot_di_stud += di_st; tot_di_staff += di_sf

                exp_5 = d["total_expense"]
                tot_expense += exp_5

                lu_tot = lu_st + lu_sf
                di_tot = di_st + di_sf
                if di_tot == 0:
                    avg_4 = float(lu_tot)
                else:
                    avg_4 = float((lu_tot + di_tot) / 2.0)

                cost_day_7 = (exp_5 / avg_4) if avg_4 > 0 else 0.0
                cost_meal_6 = (cost_day_7 / 2.0) if di_tot > 0 else cost_day_7

                d_parts = d_str.split("-")
                date_display = f"{d_parts[2]}-{d_parts[1]}-{d_parts[0]}"

                computed_days.append({
                    "date_display": date_display,
                    "cost_meal_6": cost_meal_6,
                    "cost_day_7": cost_day_7,
                    "exp_5": exp_5,
                    "avg_4": avg_4,
                    "di_sf": di_sf, "di_st": di_st,
                    "lu_sf": lu_sf, "lu_st": lu_st,
                    "bf_sf": bf_sf, "bf_st": bf_st,
                })

        tot_lu_all = tot_lu_stud + tot_lu_staff
        tot_di_all = tot_di_stud + tot_di_staff
        if tot_di_all == 0:
            tot_avg_4 = float(tot_lu_all)
        else:
            tot_avg_4 = float((tot_lu_all + tot_di_all) / 2.0)

        grand_avg_day_cost = (tot_expense / tot_avg_4) if tot_avg_4 > 0 else 0.0
        grand_avg_meal_cost = (grand_avg_day_cost / 2.0) if tot_di_all > 0 else grand_avg_day_cost

        logo_img_html = self.get_logo_img_html(30)
        gov_header_html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom:1px; border-collapse:collapse;">
            <tr>
                <td align="right" style="text-align:right; font-size:7.5pt; font-weight:bold; vertical-align:middle; border:none; width:40%; padding:0;">
                    الجمهورية الجزائرية الديمقراطية الشعبية<br>
                    {dir_name}<br>{res_name}
                </td>
                <td align="center" style="border:none; width:20%; text-align:center; vertical-align:middle; padding:0;">
                    {logo_img_html}
                </td>
                <td align="left" style="text-align:left; font-size:7.5pt; font-weight:bold; vertical-align:middle; border:none; width:40%; padding:0;">
                    وزارة التعليم العالي والبحث العلمي<br>{onou_name}
                </td>
            </tr>
        </table>
        <div style="text-align:center; color:#1E7E34; font-size:11pt; font-weight:bold; margin-top:1px; margin-bottom:3px; white-space:nowrap;">
            {period_title}
        </div>
        """

        thead_html = """
        <thead>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th rowspan="2" style="border:1px solid #000; text-align:center; width:9%; padding:1px;">الكلفة )6(</th>
                <th rowspan="2" style="border:1px solid #000; text-align:center; width:9%; padding:1px;">كلفة اليوم )7(</th>
                <th rowspan="2" style="border:1px solid #000; text-align:center; width:9%; padding:1px;">النفقة )5(</th>
                <th rowspan="2" style="border:1px solid #000; text-align:center; width:8%; padding:1px;">المعدل )4(</th>
                <th colspan="2" style="border:1px solid #000; text-align:center; padding:1px;">وجبة العشاء )3(</th>
                <th colspan="2" style="border:1px solid #000; text-align:center; padding:1px;">وجبة الغداء )2(</th>
                <th colspan="2" style="border:1px solid #000; text-align:center; padding:1px;">فطور الصباح )1(</th>
                <th rowspan="2" style="border:1px solid #000; text-align:center; width:9%; padding:1px;">التاريخ</th>
            </tr>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th style="border:1px solid #000; text-align:center; padding:1px;">عمال</th><th style="border:1px solid #000; text-align:center; padding:1px;">طلبة</th>
                <th style="border:1px solid #000; text-align:center; padding:1px;">عمال</th><th style="border:1px solid #000; text-align:center; padding:1px;">طلبة</th>
                <th style="border:1px solid #000; text-align:center; padding:1px;">عمال</th><th style="border:1px solid #000; text-align:center; padding:1px;">طلبة</th>
            </tr>
        </thead>
        """

        tfoot_html = f"""
        <tfoot>
            <tr style="background:#F1F5F9; font-weight:bold;">
                <td style="border:1px solid #000; text-align:right; padding:0px 2px;">{grand_avg_meal_cost:,.2f}</td>
                <td style="border:1px solid #000; text-align:right; padding:0px 2px;">{grand_avg_day_cost:,.2f}</td>
                <td style="border:1px solid #000; text-align:right; padding:0px 2px;">{tot_expense:,.2f}</td>
                <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{self._fmt_excel_qty(tot_avg_4)}</td>
                <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{tot_di_staff}</td>
                <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{tot_di_stud}</td>
                <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{tot_lu_staff}</td>
                <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{tot_lu_stud}</td>
                <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{tot_bf_staff}</td>
                <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{tot_bf_stud}</td>
                <td style="border:1px solid #000; text-align:center; padding:0px 2px;">المجـموع</td>
            </tr>
        </tfoot>
        """

        signatures_html = """
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top:12px; margin-bottom:4px; border-collapse:collapse;">
            <tr>
                <td style="width:33.3%; text-align:center; font-weight:bold; font-size:8pt; border:none; padding:0;">
                    إمضاء مدير الإقامة<br><br>..............................
                </td>
                <td style="width:33.4%; text-align:center; font-weight:bold; font-size:8pt; border:none; padding:0;">
                    تأشيرة مدير الخدمات<br><br>..............................
                </td>
                <td style="width:33.3%; text-align:center; font-weight:bold; font-size:8pt; border:none; padding:0;">
                    إمضاء رئيس المصلحة<br><br>..............................
                </td>
            </tr>
        </table>
        """

        # التقسيم الهندسي الذكي: الشهر كاملاً (حتى 31 يوماً) في صفحة واحدة بدقة عالية
        chunks = []
        if computed_days:
            if len(computed_days) <= 31:
                chunks = [computed_days]
            else:
                c0_size = 31
                chunks.append(computed_days[:c0_size])
                rem = computed_days[c0_size:]
                while rem:
                    if len(rem) <= 34:
                        chunks.append(rem)
                        break
                    else:
                        chunks.append(rem[:34])
                        rem = rem[34:]
        else:
            chunks = [[]]

        pages_html = []
        for idx, chunk in enumerate(chunks):
            is_last = (idx == len(chunks) - 1)

            if idx == 0:
                header_block = gov_header_html
            else:
                header_block = f"""
                <table width="100%" border="0" style="margin-bottom:2px; border-collapse:collapse;">
                    <tr>
                        <td align="center" style="color:#1E7E34; font-size:10pt; font-weight:bold; border:none;">
                            {period_title} - )تابع - صفحة {idx + 1}(
                        </td>
                    </tr>
                </table>
                """

            rows_html = ""
            for cd in chunk:
                rows_html += f"""
                <tr>
                    <td style="border:1px solid #000; text-align:right; padding:0px 2px;">{cd['cost_meal_6']:,.2f}</td>
                    <td style="border:1px solid #000; text-align:right; padding:0px 2px;">{cd['cost_day_7']:,.2f}</td>
                    <td style="border:1px solid #000; text-align:right; padding:0px 2px;">{cd['exp_5']:,.2f}</td>
                    <td style="border:1px solid #000; text-align:center; font-weight:bold; padding:0px 2px;">{self._fmt_excel_qty(cd['avg_4'])}</td>
                    <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{cd['di_sf']}</td>
                    <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{cd['di_st']}</td>
                    <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{cd['lu_sf']}</td>
                    <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{cd['lu_st']}</td>
                    <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{cd['bf_sf']}</td>
                    <td style="border:1px solid #000; text-align:center; padding:0px 2px;">{cd['bf_st']}</td>
                    <td style="border:1px solid #000; text-align:center; font-weight:bold; padding:0px 2px;">{cd['date_display']}</td>
                </tr>
                """

            pb_sep = '<div style="page-break-before: always; height:0; line-height:0; margin:0; padding:0; clear:both;"></div>\n' if idx > 0 else ''
            page_div = f"""
            {pb_sep}
            <div class="page-container" style="margin: 0; padding: 0; box-sizing: border-box; page-break-inside: avoid;">
                {header_block}
                <table class="data-table" width="100%" border="1" cellspacing="0" cellpadding="0" style="width:100%; border-collapse:collapse; border:1px solid #000000; font-size:7pt;">
                    {thead_html}
                    <tbody>
                        {rows_html}
                    </tbody>
                    {tfoot_html if is_last else ''}
                </table>
                {signatures_html if is_last else ''}
            </div>
            """
            pages_html.append(page_div)

        content = "\n".join(pages_html)
        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<title>{period_title}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; margin: 0; padding: 0; font-size: 7pt; font-weight: bold; color: #000; }}
    table.data-table {{ width: 100%; border-collapse: collapse; border: 1px solid #000000; }}
    table.data-table th, table.data-table td {{ border: 1px solid #000000; padding: 0px 2px; font-size: 7pt; }}
    .page-container {{ margin: 0; padding: 0; }}
</style>
</head>
<body>
{content}
</body>
</html>"""
        return html

    # -------------------------------------------------------------
    # 7. وضعية الحصص الثلاثية والموردين (مطابقة لـ عبد الحميد الوضعية.xlsx)
    # -------------------------------------------------------------
    # 7. وضعية الحصص الثلاثية والموردين (مطابقة 100% لـ عبد الحميد الوضعية.xlsx)
    # -------------------------------------------------------------
    def _get_trimester_period_title(self, trimester: int, year: int) -> str:
        if trimester == 1:
            return f"وضعية المدخولات من جانفي الى غاية مارس من سنة {year}"
        elif trimester == 2:
            return f"وضعية المدخولات من أفريل الى غاية جوان من سنة {year}"
        else:
            return f"وضعية المدخولات من سبتمبر الى غاية ديسمبر من سنة {year}"

    def generate_trimester_situation_html(self, year: Optional[int] = None, trimester: Optional[int] = None, lot_name: Optional[str] = "ALL", start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """توليد وضعية المدخولات الثلاثية أو لفترة مخصصة مطابقة بنسبة 100% للشكل والعناوين والإمضاءات والخطوط الواضحة (صفحة واحدة أو صفحتين كأقصى تقدير لكل حصة)"""
        if isinstance(year, str) and "-" in year:
            start_date, end_date = year, trimester
            year, trimester = None, None
        sit = self.stock_svc.get_trimester_situation(year=year, trimester=trimester, lot_name=lot_name, start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        lots = sit.get("lots", [])
        
        if start_date and end_date:
            period_title = f"وضعية المدخولات للفترة الممتدة من {start_date} إلى {end_date}"
        else:
            period_title = self._get_trimester_period_title(trimester or 1, year or sit.get("year", 2026))

        res_name_ar = self.get_residence_name_ar()
        res_name_fr = self.get_residence_name_fr()
        dir_name_ar = self.get_directorate_name_ar()
        dir_name_fr = self.get_directorate_name_fr()

        logo_img_html = self.get_logo_img_html(46)
        gov_header_html = f"""
        <table class="gov-header" width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom: 2px;">
            <tr>
                <td colspan="3" class="country-ar" align="center" style="text-align:center; font-size:11pt; font-weight:bold; padding-bottom:1px; font-family:'Times New Roman', Tahoma, Arial; border:none;">
                    الجمهوريــــــة الجزائريــــــة الديمقراطيــــــة الشعبيــــــة
                </td>
            </tr>
            <tr>
                <td colspan="3" class="country-fr" align="center" style="text-align:center; font-size:9pt; font-weight:bold; padding-bottom:3px; font-family:'Times New Roman', Tahoma, Arial; border:none;">
                    REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE
                </td>
            </tr>
            <tr>
                <td class="title-left" style="width:42%; vertical-align:middle; text-align:left; direction:ltr; font-size:8pt; line-height:1.3; font-family:'Times New Roman', Tahoma, Arial; border:none;" align="left">
                    <span><u>MINISTERE DE L'ENSEIGNEMENT SUPERIEUR ET DE LA RECHERCHE SCIENTIFIQUE</u></span><br>
                    <span><u>OFFICE NATIONAL DES ŒUVRES UNIVERSITAIRES</u></span><br>
                    <span><u>{dir_name_fr}</u></span><br>
                    <span><u>{res_name_fr}</u></span>
                </td>
                <td class="title-center" style="width:16%; vertical-align:middle; text-align:center; border:none;" align="center">
                    {logo_img_html}
                </td>
                <td class="title-right" style="width:42%; vertical-align:middle; text-align:right; direction:rtl; font-size:8.5pt; line-height:1.3; font-family:'Times New Roman', Tahoma, Arial; border:none;" align="right">
                    <span><u>وزارة التعلــــيم العالــــي والبحـــــث العلمـــــي</u></span><br>
                    <span><u>الديـــــوان الوطنـــــي للخدمـــــات الجامعيـــــة</u></span><br>
                    <span><u>{dir_name_ar}</u></span><br>
                    <span><u>{res_name_ar}</u></span>
                </td>
            </tr>
        </table>
        <div class="main-period-title" align="center" style="text-align:center; color:#C00000; font-size:12pt; font-weight:bold; margin:3px 0 4px 0; font-family:'Segoe UI', Tahoma, Arial;">
            {period_title}
        </div>
        """

        tables_html = ""
        total_lots = len(lots)
        has_summary = (total_lots > 1)
        global_page_idx = 0

        for lot_idx, lot in enumerate(lots):
            l_name = lot["lot_name"]
            s_name = lot["supplier_name"]
            items = lot["items"]

            thead_html = """
            <thead>
                <tr>
                    <th colspan="2" style="border:1px solid #000000; width:14%; background:#F8FAFC; text-align:center; padding:3px 2px; font-weight:bold;">الفارق بالمبلغ</th>
                    <th colspan="2" style="border:1px solid #000000; width:13%; background:#F8FAFC; text-align:center; padding:3px 2px; font-weight:bold;">الفارق بالكمية</th>
                    <th colspan="2" style="border:1px solid #000000; width:16%; background:#F8FAFC; text-align:center; padding:3px 2px; font-weight:bold;">المدخولات</th>
                    <th colspan="2" style="border:1px solid #000000; width:16%; background:#F8FAFC; text-align:center; padding:3px 2px; font-weight:bold;">الكميات الممنوحة من المديرية</th>
                    <th style="border:1px solid #000000; width:8%; background:#F8FAFC; text-align:center; padding:3px 2px; font-weight:bold;">السعر</th>
                    <th style="border:1px solid #000000; width:6%; background:#F8FAFC; text-align:center; padding:3px 2px; font-weight:bold;">الوحدة</th>
                    <th style="border:1px solid #000000; width:23%; background:#F8FAFC; text-align:center; padding:3px 2px; font-weight:bold;">المواد</th>
                    <th style="border:1px solid #000000; width:4%; background:#F8FAFC; text-align:center; padding:3px 2px; font-weight:bold;">الرقم</th>
                </tr>
                <tr>
                    <th style="border:1px solid #000000; background:#F8FAFC; text-align:center; padding:2px; font-weight:bold;">بالنقصان</th>
                    <th style="border:1px solid #000000; background:#F8FAFC; text-align:center; padding:2px; font-weight:bold;">بالزيادة</th>
                    <th style="border:1px solid #000000; background:#F8FAFC; text-align:center; padding:2px; font-weight:bold;">بالنقصان</th>
                    <th style="border:1px solid #000000; background:#F8FAFC; text-align:center; padding:2px; font-weight:bold;">بالزيادة</th>
                    <th style="border:1px solid #000000; background:#F8FAFC; text-align:center; padding:2px; font-weight:bold;">المبلغ</th>
                    <th style="border:1px solid #000000; background:#F8FAFC; text-align:center; padding:2px; font-weight:bold;">الكمية</th>
                    <th style="border:1px solid #000000; background:#F8FAFC; text-align:center; padding:2px; font-weight:bold;">المبلغ</th>
                    <th style="border:1px solid #000000; background:#F8FAFC; text-align:center; padding:2px; font-weight:bold;">الكمية</th>
                    <th style="border:1px solid #000000; background:#F8FAFC; text-align:center; padding:2px; font-weight:bold;">بكل الرسوم</th>
                    <th style="border:1px solid #000000; background:#F8FAFC;"></th>
                    <th style="border:1px solid #000000; background:#F8FAFC;"></th>
                    <th style="border:1px solid #000000; background:#F8FAFC;"></th>
                </tr>
            </thead>
            """

            tfoot_html = f"""
            <tfoot>
                <tr style="font-weight:bold; background:#FFFFFF;">
                    <td align="right" style="border:1px solid #000000; text-align:right; color:#DC2626; white-space:nowrap; padding:3px 4px; font-weight:bold;">{lot['tot_diff_amt_deficit']:,.2f}</td>
                    <td align="right" style="border:1px solid #000000; text-align:right; color:#16A34A; white-space:nowrap; padding:3px 4px; font-weight:bold;">{lot['tot_diff_amt_excess']:,.2f}</td>
                    <td align="center" style="border:1px solid #000000; text-align:center; white-space:nowrap; padding:3px 4px; font-weight:bold; color:#DC2626;">{lot.get('tot_diff_qty_deficit', 0):g}</td>
                    <td align="center" style="border:1px solid #000000; text-align:center; white-space:nowrap; padding:3px 4px; font-weight:bold; color:#16A34A;">{lot.get('tot_diff_qty_excess', 0):g}</td>
                    <td align="right" style="border:1px solid #000000; text-align:right; font-weight:bold; white-space:nowrap; padding:3px 4px;">{lot['tot_actual_amt']:,.2f}</td>
                    <td align="center" style="border:1px solid #000000; text-align:center; white-space:nowrap; padding:3px 4px; font-weight:bold;">{lot['tot_actual_qty']:g}</td>
                    <td align="right" style="border:1px solid #000000; text-align:right; white-space:nowrap; padding:3px 4px; font-weight:bold;">{lot['tot_allocated_amt']:,.2f}</td>
                    <td align="center" style="border:1px solid #000000; text-align:center; white-space:nowrap; padding:3px 4px; font-weight:bold;">{lot['tot_allocated_qty']:g}</td>
                    <td colspan="4" align="center" style="border:1px solid #000000; text-align:center; font-weight:bold; padding:3px 4px;">المجمـــــــــــوع</td>
                </tr>
            </tfoot>
            """

            signatures_html = """
            <table class="signatures-table" width="100%" style="margin-top:8px; margin-bottom:2px; border-collapse:collapse;">
                <tr>
                    <td style="width:33.3%; text-align:center; font-weight:bold; font-size:10pt; border:none;">المــــــــــــــــــدير</td>
                    <td style="width:33.4%; text-align:center; font-weight:bold; font-size:10pt; border:none;">رئيس المصلحة</td>
                    <td style="width:33.3%; text-align:center; font-weight:bold; font-size:10pt; border:none;">مخزني الاطعام</td>
                </tr>
                <tr>
                    <td style="padding-top:12px; text-align:center; border:none; color:#94A3B8; font-weight:bold;">..............................</td>
                    <td style="padding-top:12px; text-align:center; border:none; color:#94A3B8; font-weight:bold;">..............................</td>
                    <td style="padding-top:12px; text-align:center; border:none; color:#94A3B8; font-weight:bold;">..............................</td>
                </tr>
            </table>
            """

            # تقسيم هندسي متوازن لضمان استيعاب كل حصة في صفحة واحدة أو صفحتين كأكبر تقدير
            num_items = len(items)
            if num_items <= 14:
                item_chunks = [items]
            elif num_items <= 38:
                mid = min(20, math.ceil(num_items / 2))
                if (num_items - mid) > 19 and mid < 20:
                    mid = min(20, num_items - 19)
                item_chunks = [items[:mid], items[mid:]]
            else:
                mid = math.ceil(num_items / 2)
                if mid <= 22:
                    item_chunks = [items[:mid], items[mid:]]
                else:
                    chunk_size = 20
                    item_chunks = [items[i:i + chunk_size] for i in range(0, num_items, chunk_size)]

            for c_idx, c_items in enumerate(item_chunks):
                is_last_chunk = (c_idx == len(item_chunks) - 1)

                if c_idx == 0:
                    lot_header_block = f"""
                    {gov_header_html}
                    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom:4px; margin-top:1px;">
                        <tr>
                            <td align="right" style="border:none; text-align:right; color:#C00000; font-size:11pt; font-weight:bold; font-family:'Segoe UI', Tahoma, Arial;">
                                <u>حصة {l_name} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; للمورد / {s_name}</u>
                            </td>
                        </tr>
                    </table>
                    """
                else:
                    lot_header_block = f"""
                    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom:4px; margin-top:2px;">
                        <tr>
                            <td align="right" style="border:none; text-align:right; color:#C00000; font-size:11pt; font-weight:bold; font-family:'Segoe UI', Tahoma, Arial;">
                                <u>تابع حصة {l_name} للمورد / {s_name} )صفحة {c_idx + 1}(</u>
                            </td>
                        </tr>
                    </table>
                    """

                rows_html = ""
                for it in c_items:
                    q_ex_str = f"{it['diff_qty_excess']:g}" if it['diff_qty_excess'] > 0 else '0'
                    q_def_str = f"{it['diff_qty_deficit']:g}" if it['diff_qty_deficit'] > 0 else '0'
                    a_ex_str = f"{it['diff_amt_excess']:,.2f}" if it['diff_amt_excess'] > 0 else '0.00'
                    a_def_str = f"{it['diff_amt_deficit']:,.2f}" if it['diff_amt_deficit'] > 0 else '0.00'

                    rows_html += f"""
                    <tr>
                        <td align="right" style="border:1px solid #000000; text-align:right; white-space:nowrap; padding:2px 4px; font-weight:bold;">{a_def_str}</td>
                        <td align="right" style="border:1px solid #000000; text-align:right; white-space:nowrap; padding:2px 4px; font-weight:bold;">{a_ex_str}</td>
                        <td align="center" style="border:1px solid #000000; text-align:center; white-space:nowrap; padding:2px 4px; font-weight:bold;">{q_def_str}</td>
                        <td align="center" style="border:1px solid #000000; text-align:center; white-space:nowrap; padding:2px 4px; font-weight:bold;">{q_ex_str}</td>
                        <td align="right" style="border:1px solid #000000; text-align:right; font-weight:bold; white-space:nowrap; padding:2px 4px;">{it['actual_amt']:,.2f}</td>
                        <td align="center" style="border:1px solid #000000; text-align:center; white-space:nowrap; padding:2px 4px; font-weight:bold;">{it['actual_qty']:g}</td>
                        <td align="right" style="border:1px solid #000000; text-align:right; white-space:nowrap; padding:2px 4px; font-weight:bold;">{it['allocated_amt']:,.2f}</td>
                        <td align="center" style="border:1px solid #000000; text-align:center; white-space:nowrap; padding:2px 4px; font-weight:bold;">{it['allocated_qty']:g}</td>
                        <td align="right" style="border:1px solid #000000; text-align:right; white-space:nowrap; padding:2px 4px; font-weight:bold;">{it['price_ttc']:,.2f}</td>
                        <td align="center" style="border:1px solid #000000; text-align:center; white-space:nowrap; padding:2px 4px; font-weight:bold;">{it['unit']}</td>
                        <td align="right" style="border:1px solid #000000; text-align:right; font-weight:bold; padding:2px 4px;">{it['name']}</td>
                        <td align="center" style="border:1px solid #000000; text-align:center; font-weight:bold; padding:2px 4px;">{it['code']}</td>
                    </tr>
                    """

                pb_sep = '<div style="page-break-before: always; height:0; line-height:0; margin:0; padding:0; clear:both;"></div>\n' if global_page_idx > 0 else ''
                tables_html += f"""
                {pb_sep}
                <div class="lot-page" style="margin: 0; padding: 0; box-sizing: border-box;">
                    {lot_header_block}
                    <table class="data-table" width="100%" border="1" cellspacing="0" cellpadding="2" style="width:100%; border-collapse:collapse; border:1px solid #000000;">
                        {thead_html}
                        <tbody>
                            {rows_html}
                        </tbody>
                        {tfoot_html if is_last_chunk else ''}
                    </table>
                    {signatures_html if is_last_chunk else ''}
                </div>
                """
                global_page_idx += 1

        grand_total_html = ""
        if total_lots > 1:
            pb_sep = '<div style="page-break-before: always; height:0; line-height:0; margin:0; padding:0; clear:both;"></div>\n' if global_page_idx > 0 else ''
            grand_total_html = f"""
            {pb_sep}
            <div class="summary-page" style="margin: 0; padding: 0; box-sizing: border-box;">
                {gov_header_html}
                <div class="grand-total-box" style="margin-top:15px; background:#0F2D25; color:white; padding:12px; border-radius:6px;">
                    <div style="font-size:12pt; font-weight:bold; margin-bottom:10px; text-align:center;">📊 الحصيلة الإجمالية الشاملة لجميع الحصص والموردين ){sit['trimester_name']} {sit.get('year', '')}(:</div>
                    <table width="100%" style="font-size:10pt; color:white; border-collapse:collapse;" border="0">
                        <tr>
                            <td style="padding:5px; border:none; font-weight:bold;">إجمالي حصص المديرية الممنوحة: <strong>{sit['tot_allocated_amt']:,.2f} دج</strong></td>
                            <td style="padding:5px; border:none; font-weight:bold;">إجمالي المدخولات الفعلية المستلمة: <strong>{sit['tot_actual_amt']:,.2f} دج</strong></td>
                        </tr>
                        <tr>
                            <td style="padding:5px; border:none; font-weight:bold;">الفارق بالنقصان: <strong style="color:#FCA5A5;">{sit['tot_diff_amt_deficit']:,.2f} دج</strong></td>
                            <td style="padding:5px; border:none; font-weight:bold;">الفارق بالزيادة: <strong style="color:#86EFAC;">{sit['tot_diff_amt_excess']:,.2f} دج</strong></td>
                        </tr>
                    </table>
                </div>

                <table class="signatures-table" width="100%" style="margin-top:30px; margin-bottom:10px; border-collapse:collapse;">
                    <tr>
                        <td style="width:33.3%; text-align:center; font-weight:bold; font-size:10.5pt; border:none;">المــــــــــــــــــدير</td>
                        <td style="width:33.4%; text-align:center; font-weight:bold; font-size:10.5pt; border:none;">رئيس المصلحة</td>
                        <td style="width:33.3%; text-align:center; font-weight:bold; font-size:10.5pt; border:none;">مخزني الاطعام</td>
                    </tr>
                    <tr>
                        <td style="padding-top:20px; text-align:center; border:none; color:#94A3B8; font-weight:bold;">..............................</td>
                        <td style="padding-top:20px; text-align:center; border:none; color:#94A3B8; font-weight:bold;">..............................</td>
                        <td style="padding-top:20px; text-align:center; border:none; color:#94A3B8; font-weight:bold;">..............................</td>
                    </tr>
                </table>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{period_title}</title>
<style>
    body {{
        font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
        margin: 2mm 3mm;
        color: #000000;
        font-size: 8.5pt;
        font-weight: bold;
    }}
    .gov-header {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 2px;
    }}
    .gov-header td {{
        border: none;
        padding: 0;
        font-family: 'Times New Roman', Tahoma, Arial, sans-serif;
    }}
    .country-ar {{
        text-align: center;
        font-size: 11pt;
        font-weight: bold;
        text-decoration: underline;
        padding-bottom: 1px;
    }}
    .country-fr {{
        text-align: center;
        font-size: 9pt;
        font-weight: bold;
        text-decoration: underline;
        padding-bottom: 3px;
    }}
    .title-right {{
        text-align: right;
        line-height: 1.3;
        font-size: 8.5pt;
    }}
    .title-right span {{
        text-decoration: underline;
        font-weight: bold;
    }}
    .title-left {{
        text-align: left;
        direction: ltr;
        line-height: 1.3;
        font-size: 8pt;
    }}
    .title-left span {{
        text-decoration: underline;
        font-weight: bold;
    }}
    .main-period-title {{
        text-align: center;
        color: #C00000;
        font-size: 12pt;
        font-weight: bold;
        margin: 3px 0 4px 0;
        font-family: 'Segoe UI', Tahoma, Arial;
    }}
    table.data-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 8.5pt;
        font-weight: bold;
        margin-top: 0;
        border: 1px solid #000000;
    }}
    table.data-table th, table.data-table td {{
        border: 1px solid #000000;
        padding: 2px 3px;
        font-weight: bold;
    }}
    table.data-table th {{
        background-color: #F8FAFC;
        text-align: center;
        font-weight: bold;
        font-size: 8pt;
    }}
    .lot-page {{
        margin: 0;
        padding: 0;
    }}
</style>
</head>
<body>

{tables_html if tables_html else '<div style="text-align:center; padding:25px;">لا توجد حصص مسجلة في هذا الثلاثي</div>'}
{grand_total_html}

</body>
</html>"""
        return html

    # -------------------------------------------------------------
    # 8. تصدير وضعية الثلاثي إلى Excel (مطابق 100% لملف عبد الحميد الوضعية.xlsx)
    # -------------------------------------------------------------
    def export_trimester_situation_excel(self, year: Optional[int] = None, trimester: Optional[int] = None, save_path: str = "", lot_name: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """تصدير وضعية الثلاثي أو الفترة المخصصة إلى Excel بتنسيق وتصميم وعناوين وإمضاءات مطابقة تماماً لملف عبد الحميد الوضعية.xlsx"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.sheet_view.rightToLeft = True

        sit = self.stock_svc.get_trimester_situation(year=year, trimester=trimester, lot_name=lot_name, start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        if start_date and end_date:
            period_title = f"وضعية المدخولات للفترة الممتدة من {start_date} إلى {end_date}"
        else:
            period_title = self._get_trimester_period_title(trimester or 1, year or sit.get("year", 2026))
        ws.title = f"وضعية_{sit['trimester_name']}_{year}"
        res_name_ar = self.get_residence_name_ar()
        res_name_fr = self.get_residence_name_fr()
        dir_name_ar = self.get_directorate_name_ar()
        dir_name_fr = self.get_directorate_name_fr()

        font_header_ar = Font(name="Times New Roman", size=9, bold=True, underline="single")
        font_header_fr = Font(name="Times New Roman", size=8, bold=True, underline="single")
        font_period_title = Font(name="Simplified Arabic", size=11, bold=True, color="FFFF0000")
        font_lot_title = Font(name="Simplified Arabic", size=9, bold=True, color="FFFF0000")
        font_tbl_header = Font(name="Arial", size=9, bold=True)
        font_tbl_data = Font(name="Arial", size=9)
        font_sig = Font(name="Arial", size=9, bold=True)

        thin_border = Border(
            left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000")
        )
        double_bottom_border = Border(
            left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"), bottom=Side(style="double", color="000000")
        )

        row_idx = 1
        # Row 1: الجمهورية الجزائرية الديمقراطية الشعبية
        ws.merge_cells(f"A{row_idx}:L{row_idx}")
        ws[f"A{row_idx}"] = "الجمهوريــــــة الجزائريــــــة الديمقراطيــــــة الشعبيــــــة"
        ws[f"A{row_idx}"].font = font_header_ar
        ws[f"A{row_idx}"].alignment = Alignment(horizontal="center")
        row_idx += 1

        # Row 2: REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE
        ws.merge_cells(f"A{row_idx}:L{row_idx}")
        ws[f"A{row_idx}"] = "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE"
        ws[f"A{row_idx}"].font = font_header_fr
        ws[f"A{row_idx}"].alignment = Alignment(horizontal="center")
        row_idx += 1

        # Rows 3-6: Official Institutions (Arabic Right / French Left)
        headers_pairs = [
            ("وزارة التعلــــيم العالــــي والبحـــــث العلمـــــي", "MINISTERE DE L'ENSEIGNEMENT SUPERIEUR ET DE LA RECHERCHE SCIENTIFIQUE"),
            ("الديـــــوان الوطنـــــي للخدمـــــات الجامعيـــــة", "OFFICE NATIONAL DES ŒUVRES UNIVERSITAIRES"),
            (dir_name_ar, dir_name_fr),
            (res_name_ar, res_name_fr)
        ]
        for ar_txt, fr_txt in headers_pairs:
            ws[f"A{row_idx}"] = ar_txt
            ws[f"A{row_idx}"].font = font_header_ar
            ws[f"A{row_idx}"].alignment = Alignment(horizontal="right")

            ws[f"L{row_idx}"] = fr_txt
            ws[f"L{row_idx}"].font = font_header_fr
            ws[f"L{row_idx}"].alignment = Alignment(horizontal="left")
            row_idx += 1

        # Row 7: فارغ
        row_idx += 1

        # Row 8: وضعية المدخولات
        ws.merge_cells(f"A{row_idx}:L{row_idx}")
        ws[f"A{row_idx}"] = period_title
        ws[f"A{row_idx}"].font = font_period_title
        ws[f"A{row_idx}"].alignment = Alignment(horizontal="center")
        row_idx += 1

        lots = sit.get("lots", [])
        for lot in lots:
            # Row 9: اسم الحصة والمورد باللون الأحمر
            ws[f"A{row_idx}"] = f"{lot['lot_name']}       للمورد / {lot['supplier_name']}"
            ws[f"A{row_idx}"].font = font_lot_title
            ws[f"A{row_idx}"].alignment = Alignment(horizontal="right")
            row_idx += 1

            # Rows 10 & 11: ترويسة الجدول المطابقة للإكسل
            r10 = row_idx
            r11 = row_idx + 1

            ws.merge_cells(f"A{r10}:A{r11}"); ws.cell(r10, 1, "الرقم")
            ws.merge_cells(f"B{r10}:B{r11}"); ws.cell(r10, 2, "المواد")
            ws.merge_cells(f"C{r10}:C{r11}"); ws.cell(r10, 3, "الوحدة")
            ws.cell(r10, 4, "السعر")
            ws.cell(r11, 4, "بكل الرسوم")

            ws.merge_cells(f"E{r10}:F{r10}"); ws.cell(r10, 5, "الكميات الممنوحة من المديرية")
            ws.cell(r11, 5, "الكمية"); ws.cell(r11, 6, "المبلغ")

            ws.merge_cells(f"G{r10}:H{r10}"); ws.cell(r10, 7, "المدخولات")
            ws.cell(r11, 7, "الكمية"); ws.cell(r11, 8, "المبلغ")

            ws.merge_cells(f"I{r10}:J{r10}"); ws.cell(r10, 9, "الفارق بالكمية")
            ws.cell(r11, 9, "بالزيادة"); ws.cell(r11, 10, "بالنقصان")

            ws.merge_cells(f"K{r10}:L{r10}"); ws.cell(r10, 11, "الفارق بالمبلغ")
            ws.cell(r11, 11, "بالزيادة"); ws.cell(r11, 12, "بالنقصان")

            for r in (r10, r11):
                for c in range(1, 13):
                    cell = ws.cell(r, c)
                    cell.font = font_tbl_header
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    cell.border = thin_border

            row_idx += 2

            # أسطر بيانات المواد
            for it in lot["items"]:
                ws.cell(row_idx, 1, it["code"]).alignment = Alignment(horizontal="center")
                ws.cell(row_idx, 2, it["name"]).alignment = Alignment(horizontal="right")
                ws.cell(row_idx, 3, it["unit"]).alignment = Alignment(horizontal="center")
                
                c4 = ws.cell(row_idx, 4, it["price_ttc"]); c4.number_format = "#,##0.00"
                c5 = ws.cell(row_idx, 5, it["allocated_qty"]); c5.number_format = "0"
                c6 = ws.cell(row_idx, 6, it["allocated_amt"]); c6.number_format = "#,##0.00"
                c7 = ws.cell(row_idx, 7, it["actual_qty"]); c7.number_format = "0"
                c8 = ws.cell(row_idx, 8, it["actual_amt"]); c8.number_format = "#,##0.00"
                c9 = ws.cell(row_idx, 9, it["diff_qty_excess"] if it["diff_qty_excess"] > 0 else 0); c9.number_format = "0"
                c10 = ws.cell(row_idx, 10, it["diff_qty_deficit"] if it["diff_qty_deficit"] > 0 else 0); c10.number_format = "0"
                c11 = ws.cell(row_idx, 11, it["diff_amt_excess"] if it["diff_amt_excess"] > 0 else 0.0); c11.number_format = "#,##0.00"
                c12 = ws.cell(row_idx, 12, it["diff_amt_deficit"] if it["diff_amt_deficit"] > 0 else 0.0); c12.number_format = "#,##0.00"

                for c in range(1, 13):
                    cell = ws.cell(row_idx, c)
                    cell.font = font_tbl_data
                    cell.border = thin_border
                    if c in (1, 3): cell.alignment = Alignment(horizontal="center")
                row_idx += 1

            # سطر المجموع الفرعي للحصة (Row 48 المطابق للإكسل)
            ws.cell(row_idx, 2, "المجمــــــــــــــــــــــــوع").font = font_tbl_header
            ws.cell(row_idx, 5, lot["tot_allocated_qty"]).number_format = "0"
            ws.cell(row_idx, 6, lot["tot_allocated_amt"]).number_format = "#,##0.00"
            ws.cell(row_idx, 7, lot["tot_actual_qty"]).number_format = "0"
            ws.cell(row_idx, 8, lot["tot_actual_amt"]).number_format = "#,##0.00"
            c9 = ws.cell(row_idx, 9, lot.get("tot_diff_qty_excess", 0)); c9.number_format = "0"
            c10 = ws.cell(row_idx, 10, lot.get("tot_diff_qty_deficit", 0)); c10.number_format = "0"
            ws.cell(row_idx, 11, lot["tot_diff_amt_excess"]).number_format = "#,##0.00"
            ws.cell(row_idx, 12, lot["tot_diff_amt_deficit"]).number_format = "#,##0.00"

            for c in range(1, 13):
                cell = ws.cell(row_idx, c)
                cell.font = font_tbl_header
                cell.border = double_bottom_border
            row_idx += 2  # ترك سطر فارغ

            # سطر الإمضاءات الثلاثة (Row 50 المطابق لـ media_1792159205393.jpg)
            # Col C: مخزني الاطعام | Col G: رئيس المصلحة | Col J: المــــــــــــــــــدير
            ws.cell(row_idx, 3, "مخزني الاطعام ").font = font_sig
            ws.cell(row_idx, 3).alignment = Alignment(horizontal="center")

            ws.cell(row_idx, 7, "رئيس المصلحة ").font = font_sig
            ws.cell(row_idx, 7).alignment = Alignment(horizontal="center")

            ws.cell(row_idx, 10, "المــــــــــــــــــدير ").font = font_sig
            ws.cell(row_idx, 10).alignment = Alignment(horizontal="center")

            row_idx += 3  # مسافة للإمضاء

        # ضبط أبعاد الأعمدة لتطابق الإكسل
        ws.column_dimensions["A"].width = 8
        ws.column_dimensions["B"].width = 30
        ws.column_dimensions["C"].width = 10
        ws.column_dimensions["D"].width = 14
        ws.column_dimensions["E"].width = 12
        ws.column_dimensions["F"].width = 16
        ws.column_dimensions["G"].width = 12
        ws.column_dimensions["H"].width = 16
        ws.column_dimensions["I"].width = 12
        ws.column_dimensions["J"].width = 12
        ws.column_dimensions["K"].width = 16
        ws.column_dimensions["L"].width = 16

        wb.save(save_path)
        return save_path

    # -------------------------------------------------------------
    # 7. قائمة الأسعار الرسمية (مطابقة لورقة الأسعار في Excel)
    # -------------------------------------------------------------
    def generate_price_list_html(self, residence_id: Optional[int] = None) -> str:
        """توليد مطبوعة قائمة الأسعار الرسمية مطابقة تماماً لورقة الأسعار في Excel مع عزل أسعار كل إقامة"""
        r_id = residence_id or getattr(self, "residence_id", 1)
        res_name = self.get_residence_name_ar()
        if r_id:
            try:
                with self.db.get_connection() as conn:
                    r_row = conn.execute("SELECT name FROM residences WHERE id = ?", (r_id,)).fetchone()
                    if r_row:
                        res_name = r_row["name"]
            except Exception:
                pass
        dir_name = self.get_directorate_name_ar()
        onou_name = self.db.get_setting("onou_name", "الديوان الوطني للخدمات الجامعية")
        year = self.db.get_setting("academic_year", "2026")
        logo_img_html = self.get_logo_img_html(56)

        with self.db.get_connection() as conn:
            articles = conn.execute("""
                SELECT a.code, a.name, a.unit,
                       COALESCE(ra.price_ht, a.price_ht) as price_ht,
                       COALESCE(ra.discount_rate, a.discount_rate) as discount_rate,
                       COALESCE(ra.discount_amount, a.discount_amount) as discount_amount,
                       COALESCE(ra.price_after_discount, a.price_after_discount) as price_after_discount,
                       COALESCE(ra.tva_rate, a.tva_rate) as tva_rate,
                       COALESCE(ra.price_ttc, a.price_ttc) as price_ttc
                FROM articles a
                LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                WHERE a.is_active = 1
                ORDER BY a.id ASC
            """, (r_id,)).fetchall()

        rows_html = ""
        for it in articles:
            code_txt = str(it["code"] or "")
            disc_pct_txt = f"{int(it['discount_rate'] * 100)}%" if it["discount_rate"] > 0 else "0%"
            disc_amt = it["discount_amount"] or (it["price_ht"] * it["discount_rate"])
            p_after = it["price_after_discount"] or (it["price_ht"] - disc_amt)
            raw_tva = float(it.get("tva_rate") or 0.0)
            tva_pct = int(round(raw_tva * 100.0)) if (0.0 < raw_tva <= 1.0) else int(round(raw_tva))
            tva_txt = f"{tva_pct}%" if tva_pct > 0 else "0%"

            rows_html += f"""
            <tr>
                <td style="text-align:right; font-weight:bold; padding-right:6px;">{it['price_ttc']:,.2f}</td>
                <td style="text-align:center;">{tva_txt}</td>
                <td style="text-align:right; padding-right:6px;">{p_after:,.2f}</td>
                <td style="text-align:right; padding-right:6px;">{disc_amt:,.2f}</td>
                <td style="text-align:center;">{disc_pct_txt}</td>
                <td style="text-align:right; padding-right:6px;">{it['price_ht']:,.2f}</td>
                <td style="text-align:center;">{it['unit']}</td>
                <td style="text-align:right; font-weight:600; padding-right:8px;">{it['name']}</td>
                <td style="text-align:center;">{code_txt}</td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="utf-8">
            <title>قائمة الأسعار - {year}</title>
            <style>
                @page {{
                    size: A4 portrait;
                    margin: 10mm;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
                    direction: rtl;
                    margin: 0;
                    padding: 0;
                    color: #000;
                    background: #FFF;
                    font-size: 11px;
                }}
                .header-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 12px;
                }}
                .header-table td {{
                    vertical-align: top;
                    font-size: 11px;
                    line-height: 1.4;
                }}
                .main-title {{
                    text-align: center;
                    font-size: 20px;
                    font-weight: bold;
                    letter-spacing: 1px;
                    margin: 10px 0 14px 0;
                    text-decoration: underline;
                }}
                .data-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 5px;
                }}
                .data-table th {{
                    background-color: #E2E8F0;
                    border: 1px solid #475569;
                    padding: 6px 3px;
                    font-weight: bold;
                    text-align: center;
                    font-size: 11px;
                }}
                .data-table td {{
                    border: 1px solid #64748B;
                    padding: 4px 3px;
                    font-size: 11px;
                }}
                .data-table tr:nth-child(even) {{
                    background-color: #F8FAFC;
                }}
                .signatures {{
                    width: 100%;
                    margin-top: 25px;
                    border-collapse: collapse;
                }}
                .signatures td {{
                    width: 50%;
                    text-align: center;
                    font-weight: bold;
                    font-size: 12px;
                    vertical-align: top;
                    height: 70px;
                }}
            </style>
        </head>
        <body>
            <table class="header-table" width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                    <td colspan="3" align="center" style="text-align:center; font-size:13px; font-weight:bold; padding-bottom:6px;">
                        الجمهورية الجزائرية الديمقراطية الشعبية
                    </td>
                </tr>
                <tr>
                    <td width="38%" align="right" style="width:38%; text-align:right; font-size:10px; font-weight:bold; vertical-align:middle; line-height:1.4;">
                        وزارة التعليم العالي والبحث العلمي<br>
                        {onou_name}<br>
                        {dir_name}<br>
                        {res_name}
                    </td>
                    <td width="24%" align="center" style="width:24%; text-align:center; vertical-align:middle;">
                        {logo_img_html}
                    </td>
                    <td width="38%" align="left" style="width:38%; text-align:left; font-size:9.5px; font-weight:bold; vertical-align:middle; line-height:1.4; direction:ltr;">
                        RÉPUBLIQUE ALGÉRIENNE DÉMOCRATIQUE ET POPULAIRE<br>
                        MINISTÈRE DE L'ENSEIGNEMENT SUPÉRIEUR<br>
                        OFFICE NATIONAL DES ŒUVRES UNIVERSITAIRES<br>
                        DIRECTION DES ŒUVRES UNIVERSITAIRES OUARGLA POLE
                    </td>
                </tr>
            </table>

            <div class="main-title" style="text-align:center; font-size:18px; font-weight:bold; margin:6px 0 12px 0;">قائــــمة الأســـــعار</div>

            <table class="data-table" width="100%" border="1" cellspacing="0" cellpadding="4">
                <thead>
                    <tr>
                        <th style="width: 15%;">السعر بكامل الرسوم</th>
                        <th style="width: 8%;">ض ق م / TVA</th>
                        <th style="width: 11%;">السعر بعد التخفيض</th>
                        <th style="width: 9%;">قيمة التخفيض</th>
                        <th style="width: 8%;">نسبة التخفيض</th>
                        <th style="width: 11%;">سعر بدون رسوم</th>
                        <th style="width: 6%;">الوحدة</th>
                        <th style="width: 25%;">إسم المادة</th>
                        <th style="width: 7%;">رقم الحصة</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="width:100%; margin-top:30px; border-collapse:collapse;">
                <tr>
                    <td width="50%" align="center" style="width:50%; text-align:center; font-weight:bold; font-size:12px; border:none;">مـدير الإقـامــة</td>
                    <td width="50%" align="center" style="width:50%; text-align:center; font-weight:bold; font-size:12px; border:none;">رئيس مصلحة الإطعام</td>
                </tr>
                <tr>
                    <td align="center" style="padding-top:35px; text-align:center; border:none; color:#94A3B8;">..................................................</td>
                    <td align="center" style="padding-top:35px; text-align:center; border:none; color:#94A3B8;">..................................................</td>
                </tr>
            </table>
        </body>
        </html>
        """
        return html

    def export_price_list_to_excel(self, save_path: str, residence_id: Optional[int] = None) -> str:
        """تصدير قائمة الأسعار إلى مصنف Excel مطابق تماماً لورقة الأسعار في المنظومة مع عزل أسعار كل إقامة"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "الأسعار"
        ws.views.sheetView[0].rightToLeft = True

        r_id = residence_id or getattr(self, "residence_id", 1)
        res_name = self.get_residence_name_ar()
        if r_id:
            try:
                with self.db.get_connection() as conn:
                    r_row = conn.execute("SELECT name FROM residences WHERE id = ?", (r_id,)).fetchone()
                    if r_row:
                        res_name = r_row["name"]
            except Exception:
                pass

        # الترويسة الرئيسية
        ws.merge_cells("A1:I1")
        cell_title = ws["A1"]
        cell_title.value = f"قائمة الأسعار - {res_name}"
        cell_title.font = Font(name="Segoe UI", size=18, bold=True)
        cell_title.alignment = Alignment(horizontal="center", vertical="center")

        ws.cell(2, 10, res_name)

        headers = [
            ("رقم الحصة", "A"),
            ("إسم المادة", "B"),
            ("الوحدة", "C"),
            ("سعر بدون رسوم", "D"),
            ("نسبة التخفيض", "E"),
            ("قيمة التخفيض", "F"),
            ("السعر بعد التخفيض", "G"),
            ("ض ق م / TVA", "H"),
            ("السعر بكامل الرسوم", "I")
        ]

        header_font = Font(name="Segoe UI", size=10, bold=True, color="000000")
        header_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        thin_border = Border(
            left=Side(style="thin", color="64748B"), right=Side(style="thin", color="64748B"),
            top=Side(style="thin", color="64748B"), bottom=Side(style="thin", color="64748B")
        )

        for col_idx, (h_name, col_letter) in enumerate(headers, 1):
            cell = ws.cell(3, col_idx, h_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border

        with self.db.get_connection() as conn:
            articles = conn.execute("""
                SELECT a.code, a.name, a.unit,
                       COALESCE(ra.price_ht, a.price_ht) as price_ht,
                       COALESCE(ra.discount_rate, a.discount_rate) as discount_rate,
                       COALESCE(ra.discount_amount, a.discount_amount) as discount_amount,
                       COALESCE(ra.price_after_discount, a.price_after_discount) as price_after_discount,
                       COALESCE(ra.tva_rate, a.tva_rate) as tva_rate,
                       COALESCE(ra.price_ttc, a.price_ttc) as price_ttc
                FROM articles a
                LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
                WHERE a.is_active = 1
                ORDER BY a.id ASC
            """, (r_id,)).fetchall()

        row_idx = 4
        for it in articles:
            disc_amt = it["discount_amount"] or (it["price_ht"] * it["discount_rate"])
            p_after = it["price_after_discount"] or (it["price_ht"] - disc_amt)

            c_code = ws.cell(row_idx, 1, str(it["code"] or ""))
            c_code.alignment = Alignment(horizontal="center")

            c_name = ws.cell(row_idx, 2, it["name"])
            c_name.alignment = Alignment(horizontal="right")

            c_unit = ws.cell(row_idx, 3, it["unit"])
            c_unit.alignment = Alignment(horizontal="center")

            c_ht = ws.cell(row_idx, 4, it["price_ht"])
            c_ht.number_format = "#,##0.00"

            c_dr = ws.cell(row_idx, 5, it["discount_rate"])
            c_dr.number_format = "0%"
            c_dr.alignment = Alignment(horizontal="center")

            c_da = ws.cell(row_idx, 6, disc_amt)
            c_da.number_format = "#,##0.00"

            c_pa = ws.cell(row_idx, 7, p_after)
            c_pa.number_format = "#,##0.00"

            raw_tva = float(it.get("tva_rate") or 0.0)
            tva_factor = (raw_tva / 100.0) if raw_tva > 1.0 else raw_tva
            c_tva = ws.cell(row_idx, 8, tva_factor)
            c_tva.number_format = "0%"
            c_tva.alignment = Alignment(horizontal="center")

            c_ttc = ws.cell(row_idx, 9, it["price_ttc"])
            c_ttc.number_format = "#,##0.00"
            c_ttc.font = Font(name="Segoe UI", bold=True)

            for c in range(1, 10):
                ws.cell(row_idx, c).border = thin_border

            row_idx += 1

        ws.column_dimensions["A"].width = 12
        ws.column_dimensions["B"].width = 30
        ws.column_dimensions["C"].width = 10
        ws.column_dimensions["D"].width = 16
        ws.column_dimensions["E"].width = 14
        ws.column_dimensions["F"].width = 15
        ws.column_dimensions["G"].width = 18
        ws.column_dimensions["H"].width = 14
        ws.column_dimensions["I"].width = 20

        wb.save(save_path)
        return save_path

    # -------------------------------------------------------------
    # 8. سجل النشاط بالأرقام (مطابق 100% لورقة النشاط بالأرقام في Excel)
    # -------------------------------------------------------------
    def generate_activity_numbers_html(self, year: Optional[int] = None, month: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """توليد ورقة النشاط بالأرقام مطابقة 100% للنموذج المعتمد في Excel ومضغوطة هندسياً لتستوعب الشهر كاملاً (31 يوماً) في صفحة واحدة"""
        if isinstance(year, str) and "-" in year:
            start_date, end_date = year, month
            year, month = None, None
        res_name = self.get_residence_name_ar()
        res_clean = self.get_clean_residence_name()
        dir_name = self.get_directorate_name_ar()
        onou_name = self.db.get_setting("onou_name", "الديوان الوطني للخدمات الجامعية")
        m_name = self._get_arabic_month_name(month or 1)

        rep = self.meals_svc.get_monthly_activity_report(year, month, start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        days = rep["days"]

        if start_date and end_date:
            title_text = f"النشاط بالأرقام للفترة من {start_date} إلى {end_date}"
            subtitle_text = f"الفترة: {start_date} إلى {end_date}"
        else:
            title_text = f"النشاط بالأرقام لشهر {m_name} {year}"
            subtitle_text = f"شهـــــر : {m_name} {year}"

        tot_grand_exp = 0.0
        tot_bf_exp = 0.0; tot_bf_cnt = 0
        tot_lu_exp = 0.0; tot_lu_cnt = 0
        tot_di_exp = 0.0; tot_di_cnt = 0
        tot_avg_sum = 0
        active_days_count = 0

        computed_days = []
        with self.db.get_connection() as conn:
            for d in days:
                d_str = d["date"]
                m_row = conn.execute("SELECT * FROM daily_meals_tracking WHERE date = ? AND residence_id = ?", (d_str, self.residence_id)).fetchone()

                bf_tot = m_row["bf_total"] if m_row else 0
                lu_tot = m_row["lu_total"] if m_row else 0
                di_tot = m_row["di_total"] if m_row else 0

                tot_bf_cnt += bf_tot
                tot_lu_cnt += lu_tot
                tot_di_cnt += di_tot

                tot_e = d["total_expense"]
                bf_e = d["bf_expense"]
                lu_e = d["lu_expense"]
                di_e = d["di_expense"]

                # ضمان المعادلة الحسابية الصارمة: م المصاريف = مصاريف الفطور + مصاريف الغداء + مصاريف العشاء
                if (bf_e + lu_e + di_e) > 0:
                    tot_e = bf_e + lu_e + di_e

                tot_grand_exp += tot_e
                tot_bf_exp += bf_e
                tot_lu_exp += lu_e
                tot_di_exp += di_e

                if di_tot == 0:
                    avg_m = float(lu_tot)
                else:
                    avg_m = float((lu_tot + di_tot) / 2.0)

                tot_avg_sum += avg_m

                if tot_e > 0 or (bf_tot + lu_tot + di_tot) > 0:
                    active_days_count += 1

                tot_lu_di = lu_tot + di_tot
                if di_tot > 0 and tot_lu_di > 0:
                    cost_m = tot_e / float(tot_lu_di)
                elif lu_tot > 0:
                    cost_m = tot_e / float(lu_tot)
                else:
                    cost_m = 0.0

                d_parts = d_str.split("-")
                d_display = f"{d_parts[2]}/{d_parts[1]}/{d_parts[0]}"

                computed_days.append({
                    "d_display": d_display,
                    "bf_c": f"{bf_tot:,}" if bf_tot > 0 else '-',
                    "bf_e_str": self._fmt_excel_amount(bf_e),
                    "lu_c": f"{lu_tot:,}" if lu_tot > 0 else '-',
                    "lu_e_str": self._fmt_excel_amount(lu_e),
                    "di_c": f"{di_tot:,}" if di_tot > 0 else '-',
                    "di_e_str": self._fmt_excel_amount(di_e),
                    "avg_str": self._fmt_excel_qty(avg_m) if avg_m > 0 else '-',
                    "tot_e_str": self._fmt_excel_amount(tot_e),
                    "cost_str": f"{cost_m:,.2f}" if cost_m > 0 else '-',
                })

        tot_all_lu_di = tot_lu_cnt + tot_di_cnt
        if tot_di_cnt > 0 and tot_all_lu_di > 0:
            overall_food_avg = tot_grand_exp / float(tot_all_lu_di)
        elif tot_lu_cnt > 0:
            overall_food_avg = tot_grand_exp / float(tot_lu_cnt)
        else:
            overall_food_avg = 0.0

        daily_food_avg = (tot_grand_exp / active_days_count) if active_days_count > 0 else 0.0
        tot_avg_display = self._fmt_excel_qty(tot_avg_sum) if tot_avg_sum > 0 else '-'

        logo_img_html = self.get_logo_img_html(36)
        gov_header_html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom:2px; border-collapse:collapse;">
            <tr>
                <td align="right" style="text-align:right; font-size:7.5pt; font-weight:bold; vertical-align:middle; border:none; width:35%; padding:0;">
                    الجمهورية الجزائرية الديمقراطية الشعبية<br>
                    {dir_name}<br>{res_name}
                </td>
                <td align="center" style="border:none; width:30%; text-align:center; vertical-align:middle; padding:0;">
                    {logo_img_html}<br>
                    <span style="color:#1E7E34; font-size:11pt; font-weight:bold;">{title_text}</span>
                </td>
                <td align="left" style="text-align:left; font-size:7.5pt; font-weight:bold; vertical-align:middle; border:none; width:35%; padding:0;">
                    وزارة التعليم العالي والبحث العلمي<br>{onou_name}
                </td>
            </tr>
        </table>
        """

        thead_html = """
        <thead>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th colspan="3" style="border:1px solid #000; padding:1px;">الإحصائيات</th>
                <th colspan="2" style="border:1px solid #000; padding:1px;">وجبة العشاء</th>
                <th colspan="2" style="border:1px solid #000; padding:1px;">وجبة الغداء</th>
                <th colspan="2" style="border:1px solid #000; padding:1px;">وجبة الفطور</th>
                <th rowspan="2" style="border:1px solid #000; width:9%; padding:1px;">التاريخ</th>
            </tr>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th style="border:1px solid #000; padding:0;">التكلفة</th>
                <th style="border:1px solid #000; padding:0;">م المصاريف</th>
                <th style="border:1px solid #000; padding:0;">المعدل</th>
                <th style="border:1px solid #000; padding:0;">المصاريف</th>
                <th style="border:1px solid #000; padding:0;">ع الوجبات</th>
                <th style="border:1px solid #000; padding:0;">المصاريف</th>
                <th style="border:1px solid #000; padding:0;">ع الوجبات</th>
                <th style="border:1px solid #000; padding:0;">المصاريف</th>
                <th style="border:1px solid #000; padding:0;">ع الوجبات</th>
            </tr>
        </thead>
        """

        summary_box_html = f"""
        <table width="100%" border="1" cellpadding="0" cellspacing="0" style="margin-top:2px; margin-bottom:2px; border-collapse:collapse; border:1px solid #000; font-size:7.5pt;">
            <tr style="background:#F1F5F9; font-weight:bold; text-align:center;">
                <td style="border:1px solid #000; padding:1px 3px; width:16%;">عدد الأيام: <span style="color:#0284C7;">{active_days_count}</span></td>
                <td style="border:1px solid #000; padding:1px 3px; width:42%;">مجموع المصاريف: <span style="color:#DC2626;">{self._fmt_excel_amount(tot_grand_exp)} دج</span></td>
                <td style="border:1px solid #000; padding:1px 3px; width:42%;">معدل اليوم الغذائي: <span style="color:#0F2D25;">{self._fmt_excel_amount(daily_food_avg)} دج</span></td>
            </tr>
        </table>
        """

        tfoot_html = f"""
        <tfoot>
            <tr style="background:#F1F5F9; font-weight:bold;">
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{overall_food_avg:,.2f}</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{self._fmt_excel_amount(tot_grand_exp)}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{tot_avg_display}</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{self._fmt_excel_amount(tot_di_exp)}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{tot_di_cnt}</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{self._fmt_excel_amount(tot_lu_exp)}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{tot_lu_cnt}</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{self._fmt_excel_amount(tot_bf_exp)}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{tot_bf_cnt}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">المجاميع العامة</td>
            </tr>
        </tfoot>
        """

        signatures_html = """
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top:2px; border-collapse:collapse;">
            <tr>
                <td style="width:33.3%; text-align:center; font-weight:bold; font-size:7.5pt; border:none; padding:0;">
                    إمضاء مدير الإقامة: ..............................
                </td>
                <td style="width:33.4%; text-align:center; font-weight:bold; font-size:7.5pt; border:none; padding:0;">
                    تأشيرة مدير الخدمات: ..............................
                </td>
                <td style="width:33.3%; text-align:center; font-weight:bold; font-size:7.5pt; border:none; padding:0;">
                    إمضاء رئيس المصلحة: ..............................
                </td>
            </tr>
        </table>
        """

        # التقسيم الهندسي الذكي: حتى 31 يوماً في صفحة واحدة كاملة
        chunks = []
        if computed_days:
            if len(computed_days) <= 31:
                chunks = [computed_days]
            else:
                c0_size = 31
                chunks.append(computed_days[:c0_size])
                rem = computed_days[c0_size:]
                while rem:
                    if len(rem) <= 34:
                        chunks.append(rem)
                        break
                    else:
                        chunks.append(rem[:34])
                        rem = rem[34:]
        else:
            chunks = [[]]

        pages_html = []
        for idx, chunk in enumerate(chunks):
            is_last = (idx == len(chunks) - 1)

            if idx == 0:
                header_block = gov_header_html
            else:
                header_block = f"""
                <table width="100%" border="0" style="margin-bottom:2px; border-collapse:collapse;">
                    <tr>
                        <td align="center" style="font-size:10pt; font-weight:bold; border:none;">
                            {title_text} - )تابع - صفحة {idx + 1}(
                        </td>
                    </tr>
                </table>
                """

            rows_html = ""
            for cd in chunk:
                rows_html += f"""
                <tr>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px;">{cd['cost_str']}</td>
                    <td style="text-align:right; font-weight:bold; border:1px solid #000000; padding:0px 2px;">{cd['tot_e_str']}</td>
                    <td style="text-align:center; font-weight:bold; border:1px solid #000000; padding:0px 2px;">{cd['avg_str']}</td>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px;">{cd['di_e_str']}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{cd['di_c']}</td>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px;">{cd['lu_e_str']}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{cd['lu_c']}</td>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px;">{cd['bf_e_str']}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{cd['bf_c']}</td>
                    <td style="text-align:center; font-weight:bold; border:1px solid #000000; font-size:7pt; padding:0px 2px;">{cd['d_display']}</td>
                </tr>
                """

            pb_sep = '<div style="page-break-before: always; height:0; line-height:0; margin:0; padding:0; clear:both;"></div>\n' if idx > 0 else ''
            page_div = f"""
            {pb_sep}
            <div class="page-container" style="margin: 0; padding: 0; box-sizing: border-box; page-break-inside: avoid;">
                {header_block}
                <table class="data-table" width="100%" border="1" cellspacing="0" cellpadding="0" style="width:100%; border-collapse:collapse; border:1px solid #000000; font-size:7pt;">
                    {thead_html}
                    <tbody>
                        {rows_html}
                    </tbody>
                    {tfoot_html if is_last else ''}
                </table>
                {summary_box_html if is_last else ''}
                {signatures_html if is_last else ''}
            </div>
            """
            pages_html.append(page_div)

        content = "\n".join(pages_html)
        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<title>{title_text}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; margin: 0; padding: 0; font-size: 7pt; font-weight: bold; color: #000; }}
    table.data-table {{ width: 100%; border-collapse: collapse; border: 1px solid #000000; }}
    table.data-table th, table.data-table td {{ border: 1px solid #000000; padding: 0px 2px; font-size: 7pt; }}
    .page-container {{ margin: 0; padding: 0; }}
</style>
</head>
<body>
{content}
</body>
</html>"""
        return html

    # -------------------------------------------------------------
    # 9. سجل النشاط بالوجبة (مطابق 100% لورقة النشاط بالوجبة في Excel)
    # -------------------------------------------------------------
    def generate_activity_meals_html(self, year: Optional[int] = None, month: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """توليد سجل النشاط بالوجبة مطابق 100% لورقة النشاط بالوجبة في Excel بـ 4 أسطر لكل يوم وبتقسيم صفحات نظيف"""
        if isinstance(year, str) and "-" in year:
            start_date, end_date = year, month
            year, month = None, None
        res_name = self.get_residence_name_ar()
        res_clean = self.get_clean_residence_name()
        dir_name = self.get_directorate_name_ar()
        onou_name = self.db.get_setting("onou_name", "الديوان الوطني للخدمات الجامعية")

        menus = self.meals_svc.get_monthly_menus_report(year, month, start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        if start_date and end_date:
            m_name = ""
            title_text = "نشاط مصلحة الإطعام بالوجبة"
            subtitle_text = f"للفترة الممتدة من : {start_date} إلى : {end_date}"
        else:
            m_name = self._get_arabic_month_name(month or 1)
            title_text = f"نشاط مصلحة الإطعام لشهر {m_name} {year or ''} بالوجبة"
            if menus:
                first_w = self._get_arabic_weekday(menus[0]["date"])
                last_w = self._get_arabic_weekday(menus[-1]["date"])
                m_int = int(month) if month else 1
                first_day_str = f"{first_w} {int(menus[0]['day']):02d} / {m_int:02d}"
                last_day_str = f"{last_w} {int(menus[-1]['day']):02d} / {m_int:02d}"
                subtitle_text = f"للفترة الممتدة من : {first_day_str} إلى : {last_day_str}"
            else:
                subtitle_text = ""

        logo_img_html = self.get_logo_img_html(56)
        gov_header_html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom:6px; border-collapse:collapse;">
            <tr>
                <td colspan="3" align="center" style="text-align:center; font-size:14px; font-weight:bold; padding: 2px 0 6px 0; border:none;">
                    الجمهورية الجزائرية الديمقراطية الشعبية
                </td>
            </tr>
            <tr>
                <td align="right" style="text-align:right; font-size:11px; font-weight:bold; vertical-align:middle; border:none; width:42%;">
                    {dir_name}<br>{res_name}
                </td>
                <td align="center" style="border:none; width:16%; text-align:center; vertical-align:middle;">
                    {logo_img_html}
                </td>
                <td align="left" style="text-align:left; font-size:11px; font-weight:bold; vertical-align:middle; border:none; width:42%;">
                    وزارة التعليم العالي والبحث العلمي<br>{onou_name}
                </td>
            </tr>
            <tr>
                <td colspan="3" align="center" style="text-align:center; font-size:20px; font-weight:bold; padding: 4px 0 2px 0; border:none;">
                    {title_text}
                </td>
            </tr>
            <tr>
                <td colspan="3" align="center" style="text-align:center; font-size:11px; font-weight:bold; padding-bottom:8px; border:none;">
                    {subtitle_text}
                </td>
            </tr>
        </table>
        """

        thead_html = """
        <thead>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th style="border:1px solid #000000; text-align:center; width:29%; padding:4px;">وجبة العشاء</th>
                <th style="border:1px solid #000000; text-align:center; width:28%; padding:4px;">وجبة الغداء</th>
                <th style="border:1px solid #000000; text-align:center; width:28%; padding:4px;">وجبة الصباح</th>
                <th style="border:1px solid #000000; text-align:center; width:15%; padding:4px;">التاريخ</th>
            </tr>
        </thead>
        """

        signatures_html = """
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top:25px; border-collapse:collapse;">
            <tr>
                <td style="width:50%; text-align:center; font-weight:bold; font-size:12px; border:none;">
                    إمضاء مدير الإقامة<br><br>
                    <span style="color:#94A3B8;">..............................</span>
                </td>
                <td style="width:50%; text-align:center; font-weight:bold; font-size:12px; border:none;">
                    إمضاء رئيس مصلحة الإطعام<br><br>
                    <span style="color:#94A3B8;">..............................</span>
                </td>
            </tr>
        </table>
        """

        # التقسيم الهندسي الدقيق للصفحات: 4 أيام للصفحة الأولى (مع الترويسة الرسمية)، و5 أيام للصفحات الموالية
        chunks = []
        if menus:
            chunks.append(menus[:7])
            rem = menus[7:]
            while rem:
                if len(rem) <= 8:
                    chunks.append(rem)
                    break
                else:
                    chunks.append(rem[:8])
                    rem = rem[8:]
        else:
            chunks = [[]]

        pages_html = []
        for idx, chunk in enumerate(chunks):
            is_last = (idx == len(chunks) - 1)

            if idx == 0:
                header_block = gov_header_html
            else:
                header_block = f"""
                <table width="100%" border="0" style="margin-bottom:6px; border-collapse:collapse;">
                    <tr>
                        <td align="center" style="font-size:13px; font-weight:bold; border:none;">
                            {title_text} - )تابع - صفحة {idx + 1}(
                        </td>
                    </tr>
                </table>
                """

            rows_html = ""
            for m in chunk:
                bf_lines = self._split_into_4_lines(m["menu_breakfast"])
                lu_lines = self._split_into_4_lines(m["menu_lunch"])
                di_lines = self._split_into_4_lines(m["menu_dinner"])
                d_display = m['date'].replace("-", "/")

                rows_html += f"""
                <tr>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px; width:29%;">{di_lines[0]}</td>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px; width:28%;">{lu_lines[0]}</td>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px; width:28%;">{bf_lines[0]}</td>
                    <td rowspan="4" style="text-align:center; vertical-align:middle; font-weight:bold; border:1px solid #000000; font-size:10.5px; background:#FFF; width:15%;">{d_display}</td>
                </tr>
                <tr>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px;">{di_lines[1]}</td>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px;">{lu_lines[1]}</td>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px;">{bf_lines[1]}</td>
                </tr>
                <tr>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px;">{di_lines[2]}</td>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px;">{lu_lines[2]}</td>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px;">{bf_lines[2]}</td>
                </tr>
                <tr>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px;">{di_lines[3]}</td>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px;">{lu_lines[3]}</td>
                    <td style="text-align:center; border:1px solid #000000; height:16px; font-size:10.5px;">{bf_lines[3]}</td>
                </tr>
                """

            pb_sep = '<div style="page-break-before: always; height:0; line-height:0; margin:0; padding:0; clear:both;"></div>\n' if idx > 0 else ''
            page_div = f"""
            {pb_sep}
            <div class="page-container" style="margin: 0; padding: 2px 4px; box-sizing: border-box; page-break-inside: avoid;">
                {header_block}
                <table class="data-table" width="100%" border="1" cellspacing="0" cellpadding="2" style="width:100%; border-collapse:collapse; border:1px solid #000000;">
                    {thead_html}
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
                {signatures_html if is_last else ''}
            </div>
            """
            pages_html.append(page_div)

        content = "\n".join(pages_html)
        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<title>{title_text}</title>
<style>
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; margin: 0; font-size: 11px; color: #000; }}
    table.data-table {{ width: 100%; border-collapse: collapse; border: 1px solid #000000; }}
    table.data-table th, table.data-table td {{ border: 1px solid #000000; }}
    .page-container {{ margin: 0; padding: 4px; }}
</style>
</head>
<body>
{content}
</body>
</html>"""
        return html

    # -------------------------------------------------------------
    # 10. بطاقة الجرد الشهري العام لمخزن الإطعام (مطابقة 100% لورقة جرد)
    # -------------------------------------------------------------
    def generate_monthly_inventory_html(self, year: Optional[int] = None, month: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """توليد بطاقة الجرد الشهري العام مطابقة 100% لورقة جرد في Excel بـ 14 عموداً ومضغوطة هندسياً لاستيعاب البيانات بأقل عدد من الصفحات"""
        if isinstance(year, str) and "-" in year:
            start_date, end_date = year, month
            year, month = None, None
        res_name = self.get_residence_name_ar()
        res_clean = self.get_clean_residence_name()
        dir_name = self.get_directorate_name_ar()
        onou_name = self.db.get_setting("onou_name", "الديوان الوطني للخدمات الجامعية")

        items = self.stock_svc.get_monthly_inventory(year, month, start_date=start_date, end_date=end_date, residence_id=self.residence_id)

        if start_date and end_date:
            title_text = "بطاقة الجرد العام لمخزن الإطعام"
            subtitle_text = f"للفترة الممتدة من : {start_date} إلى : {end_date}"
        else:
            m_name = self._get_arabic_month_name(month or 1)
            title_text = f"بطاقة جرد لشهر {m_name} {year or ''}"
            subtitle_text = ""

        tot_init_val = sum(it["initial_val"] for it in items)
        tot_sup_val = sum(it["supply_val"] for it in items)
        tot_li_val = sum(it["loan_in_val"] for it in items)
        tot_cons_val = sum(it["cons_val"] for it in items)
        tot_lo_val = sum(it["loan_out_val"] for it in items)
        tot_fin_val = sum(it["final_val"] for it in items)

        logo_img_html = self.get_logo_img_html(36)
        gov_header_html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom:2px; border-collapse:collapse;">
            <tr>
                <td align="right" style="text-align:right; font-size:7.5pt; font-weight:bold; vertical-align:middle; border:none; width:35%; padding:0;">
                    الجمهورية الجزائرية الديمقراطية الشعبية<br>
                    {dir_name}<br>{res_name}
                </td>
                <td align="center" style="border:none; width:30%; text-align:center; vertical-align:middle; padding:0;">
                    {logo_img_html}<br>
                    <span style="color:#1E7E34; font-size:11pt; font-weight:bold;">{title_text}</span>
                    {f'<br><span style="font-size:7.5pt; font-weight:bold;">{subtitle_text}</span>' if subtitle_text else ''}
                </td>
                <td align="left" style="text-align:left; font-size:7.5pt; font-weight:bold; vertical-align:middle; border:none; width:35%; padding:0;">
                    وزارة التعليم العالي والبحث العلمي<br>{onou_name}
                </td>
            </tr>
        </table>
        """

        thead_html = """
        <thead>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th colspan="2" rowspan="2" style="border:1px solid #000000; text-align:center; padding:1px;">مخزون نهاية مدة</th>
                <th colspan="4" style="border:1px solid #000000; text-align:center; padding:1px;">مخروجات</th>
                <th colspan="4" style="border:1px solid #000000; text-align:center; padding:1px;">المدخولات</th>
                <th colspan="2" rowspan="2" style="border:1px solid #000000; text-align:center; padding:1px;">مخزون أول مدة</th>
                <th rowspan="3" style="border:1px solid #000000; text-align:center; width:8%; padding:1px;">سعر الوحدة</th>
                <th rowspan="3" style="border:1px solid #000000; text-align:center; width:20%; padding:1px;">إسم المادة</th>
            </tr>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th colspan="2" style="border:1px solid #000000; text-align:center; padding:1px;">إعارة</th>
                <th colspan="2" style="border:1px solid #000000; text-align:center; padding:1px;">إستهلاك</th>
                <th colspan="2" style="border:1px solid #000000; text-align:center; padding:1px;">إستعارة</th>
                <th colspan="2" style="border:1px solid #000000; text-align:center; padding:1px;">توريد</th>
            </tr>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th style="border:1px solid #000000; text-align:center; padding:1px;">المبلغ</th><th style="border:1px solid #000000; text-align:center; padding:1px;">كمية</th>
                <th style="border:1px solid #000000; text-align:center; padding:1px;">المبلغ</th><th style="border:1px solid #000000; text-align:center; padding:1px;">كمية</th>
                <th style="border:1px solid #000000; text-align:center; padding:1px;">المبلغ</th><th style="border:1px solid #000000; text-align:center; padding:1px;">كمية</th>
                <th style="border:1px solid #000000; text-align:center; padding:1px;">المبلغ</th><th style="border:1px solid #000000; text-align:center; padding:1px;">كمية</th>
                <th style="border:1px solid #000000; text-align:center; padding:1px;">المبلغ</th><th style="border:1px solid #000000; text-align:center; padding:1px;">كمية</th>
                <th style="border:1px solid #000000; text-align:center; padding:1px;">المبلغ</th><th style="border:1px solid #000000; text-align:center; padding:1px;">كمية</th>
            </tr>
        </thead>
        """

        tfoot_html = f"""
        <tfoot>
            <tr style="background:#F1F5F9; font-weight:bold;">
                <td style="border:1px solid #000000; text-align:right; font-weight:bold; padding:0px 2px;">{self._fmt_excel_amount(tot_fin_val)}</td><td style="border:1px solid #000000; text-align:center;">-</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{self._fmt_excel_amount(tot_lo_val)}</td><td style="border:1px solid #000000; text-align:center;">-</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{self._fmt_excel_amount(tot_cons_val)}</td><td style="border:1px solid #000000; text-align:center;">-</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{self._fmt_excel_amount(tot_li_val)}</td><td style="border:1px solid #000000; text-align:center;">-</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{self._fmt_excel_amount(tot_sup_val)}</td><td style="border:1px solid #000000; text-align:center;">-</td>
                <td style="border:1px solid #000000; text-align:right; padding:0px 2px;">{self._fmt_excel_amount(tot_init_val)}</td><td style="border:1px solid #000000; text-align:center;">-</td>
                <td colspan="2" style="border:1px solid #000000; text-align:center; padding:0px 2px;">المجــــــــموع العــــــــام :</td>
            </tr>
        </tfoot>
        """

        signatures_html = """
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top:2px; border-collapse:collapse;">
            <tr>
                <td style="width:33.3%; text-align:center; font-weight:bold; font-size:7.5pt; border:none; padding:0;">
                    إمضاء مدير الإقامة: ..............................
                </td>
                <td style="width:33.4%; text-align:center; font-weight:bold; font-size:7.5pt; border:none; padding:0;">
                    إمضاء رئيس مصلحة الإطعام: ..............................
                </td>
                <td style="width:33.3%; text-align:center; font-weight:bold; font-size:7.5pt; border:none; padding:0;">
                    إمضاء مخزني الإطعام: ..............................
                </td>
            </tr>
        </table>
        """

        # التقسيم الهندسي الذكي: حتى 34 مادة في صفحة واحدة، وللجداول الكبيرة 32 مادة في الصفحة
        chunks = []
        if items:
            if len(items) <= 34:
                chunks = [items]
            else:
                c0_size = 32
                chunks.append(items[:c0_size])
                rem = items[c0_size:]
                while rem:
                    if len(rem) <= 35:
                        chunks.append(rem)
                        break
                    else:
                        chunks.append(rem[:35])
                        rem = rem[35:]
        else:
            chunks = [[]]

        pages_html = []
        for idx, chunk in enumerate(chunks):
            is_last = (idx == len(chunks) - 1)

            if idx == 0:
                header_block = gov_header_html
            else:
                header_block = f"""
                <table width="100%" border="0" style="margin-bottom:2px; border-collapse:collapse;">
                    <tr>
                        <td align="center" style="font-size:10pt; font-weight:bold; border:none;">
                            {title_text} - )تابع - صفحة {idx + 1}(
                        </td>
                    </tr>
                </table>
                """

            rows_html = ""
            for it in chunk:
                p_ttc_str = f"{it['price_ttc']:,.2f}"
                iq_str = self._fmt_excel_qty(it['initial_qty'])
                iv_str = self._fmt_excel_amount(it['initial_val'])
                sq_str = self._fmt_excel_qty(it['supply_qty'])
                sv_str = self._fmt_excel_amount(it['supply_val'])
                liq_str = self._fmt_excel_qty(it['loan_in_qty'])
                liv_str = self._fmt_excel_amount(it['loan_in_val'])
                cq_str = self._fmt_excel_qty(it['cons_qty'])
                cv_str = self._fmt_excel_amount(it['cons_val'])
                loq_str = self._fmt_excel_qty(it['loan_out_qty'])
                lov_str = self._fmt_excel_amount(it['loan_out_val'])
                fq_str = self._fmt_excel_qty(it['final_qty'])
                fv_str = self._fmt_excel_amount(it['final_val'])

                rows_html += f"""
                <tr>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px; font-weight:bold;">{fv_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px; font-weight:bold;">{fq_str}</td>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px;">{lov_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{loq_str}</td>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px;">{cv_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{cq_str}</td>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px;">{liv_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{liq_str}</td>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px;">{sv_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{sq_str}</td>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px;">{iv_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{iq_str}</td>
                    <td style="text-align:right; border:1px solid #000000; padding:0px 2px;">{p_ttc_str}</td>
                    <td style="font-weight:bold; text-align:right; border:1px solid #000000; padding:0px 3px;">{it['name']}</td>
                </tr>
                """

            pb_sep = '<div style="page-break-before: always; height:0; line-height:0; margin:0; padding:0; clear:both;"></div>\n' if idx > 0 else ''
            page_div = f"""
            {pb_sep}
            <div class="page-container" style="margin: 0; padding: 0; box-sizing: border-box; page-break-inside: avoid;">
                {header_block}
                <table class="data-table" width="100%" border="1" cellspacing="0" cellpadding="0" style="width:100%; border-collapse:collapse; border:1px solid #000000; font-size:7pt;">
                    {thead_html}
                    <tbody>
                        {rows_html}
                    </tbody>
                    {tfoot_html if is_last else ''}
                </table>
                {signatures_html if is_last else ''}
            </div>
            """
            pages_html.append(page_div)

        content = "\n".join(pages_html)
        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<title>{title_text}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; margin: 0; padding: 0; font-size: 7pt; font-weight: bold; color: #000; }}
    table.data-table {{ width: 100%; border-collapse: collapse; border: 1px solid #000000; }}
    table.data-table th, table.data-table td {{ border: 1px solid #000000; padding: 0px 2px; font-size: 7pt; }}
    .page-container {{ margin: 0; padding: 0; }}
</style>
</head>
<body>
{content}
</body>
</html>"""
        return html

    # -------------------------------------------------------------
    # 8. بطاقة حركة المخزون لمادة (مطابقة لورقة بطاقة مخزون)
    # -------------------------------------------------------------
    def generate_stock_card_html(self, article_id: int, year: Optional[int] = None, month: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """توليد بطاقة حركة المخزون لمادة محددة مطابقة 100% لورقة بطاقة مخزون في Excel ومضغوطة هندسياً لتستوعب الشهر كاملاً (31 يوماً) في صفحة واحدة"""
        if isinstance(year, str) and "-" in year:
            start_date, end_date = year, month
            year, month = None, None
        res_name = self.get_residence_name_ar()
        res_clean = self.get_clean_residence_name()
        dir_name = self.get_directorate_name_ar()
        onou_name = self.db.get_setting("onou_name", "الديوان الوطني للخدمات الجامعية")
        m_name = self._get_arabic_month_name(month or 1)

        card = self.stock_svc.get_stock_card(article_id, year, month, start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        art = card["article"]
        days = card["days"]
        tots = card["totals"]

        if start_date and end_date:
            title_text = "بطاقة حركة المخزون لمادة"
            subtitle_text = f"الفترة من: {start_date} إلى {end_date}"
        else:
            title_text = f"بطاقة حركة المخزون لشهر {m_name} {year}"
            subtitle_text = ""

        logo_img_html = self.get_logo_img_html(36)
        gov_header_html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom:2px; border-collapse:collapse;">
            <tr>
                <td align="right" style="text-align:right; font-size:7.5pt; font-weight:bold; vertical-align:middle; border:none; width:35%; padding:0;">
                    الجمهورية الجزائرية الديمقراطية الشعبية<br>
                    {dir_name}<br>{res_name}
                </td>
                <td align="center" style="border:none; width:30%; text-align:center; vertical-align:middle; padding:0;">
                    {logo_img_html}<br>
                    <span style="color:#1E7E34; font-size:11pt; font-weight:bold;">{title_text}</span><br>
                    <span style="font-size:8pt; font-weight:bold; color:#000;">{art['name']} ){art['unit']}( - السعر: {art['price_ttc']:,.2f} دج</span>
                </td>
                <td align="left" style="text-align:left; font-size:7.5pt; font-weight:bold; vertical-align:middle; border:none; width:35%; padding:0;">
                    وزارة التعليم العالي والبحث العلمي<br>{onou_name}
                </td>
            </tr>
        </table>
        """

        thead_html = """
        <thead>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th rowspan="2" style="border:1px solid #000000; text-align:center; width:10%; padding:1px;">مخزون نهاية المدة</th>
                <th colspan="4" style="border:1px solid #000000; text-align:center; padding:1px;">مخروجات</th>
                <th colspan="2" style="border:1px solid #000000; text-align:center; padding:1px;">مدخولات</th>
                <th rowspan="2" style="border:1px solid #000000; text-align:center; width:12%; padding:1px;">مخزون بداية المدة</th>
                <th rowspan="2" style="border:1px solid #000000; text-align:center; width:12%; padding:1px;">التاريخ</th>
            </tr>
            <tr style="background:#F8FAFC; font-weight:bold; text-align:center;">
                <th style="border:1px solid #000000; text-align:center; width:8%; padding:1px;">إعارة</th>
                <th style="border:1px solid #000000; text-align:center; width:8%; padding:1px;">عشاء</th>
                <th style="border:1px solid #000000; text-align:center; width:8%; padding:1px;">غداء</th>
                <th style="border:1px solid #000000; text-align:center; width:8%; padding:1px;">صباح</th>
                <th style="border:1px solid #000000; text-align:center; width:8%; padding:1px;">إستعارة</th>
                <th style="border:1px solid #000000; text-align:center; width:8%; padding:1px;">توريد</th>
            </tr>
        </thead>
        """

        tfoot_html = f"""
        <tfoot>
            <tr style="background:#F1F5F9; font-weight:bold;">
                <td style="border:1px solid #000000; text-align:center; font-weight:bold; padding:0px 2px;">{self._fmt_excel_qty(card.get('closing_stock', 0))}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{self._fmt_excel_qty(tots.get('loan_out', 0))}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{self._fmt_excel_qty(tots.get('di_out', 0))}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{self._fmt_excel_qty(tots.get('lu_out', 0))}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{self._fmt_excel_qty(tots.get('bf_out', 0))}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{self._fmt_excel_qty(tots.get('loan_in', 0))}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">{self._fmt_excel_qty(tots.get('supply_in', 0))}</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">-</td>
                <td style="border:1px solid #000000; text-align:center; padding:0px 2px;">المجموع العام</td>
            </tr>
        </tfoot>
        """

        signatures_html = """
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top:2px; border-collapse:collapse;">
            <tr>
                <td style="width:50%; text-align:center; font-weight:bold; font-size:7.5pt; border:none; padding:0;">
                    إمضاء رئيس مصلحة الإطعام: ..............................
                </td>
                <td style="width:50%; text-align:center; font-weight:bold; font-size:7.5pt; border:none; padding:0;">
                    إمضاء مخزني الإطعام: ..............................
                </td>
            </tr>
        </table>
        """

        # التقسيم الهندسي الذكي: حركة الشهر كاملاً (31 يوماً) في صفحة واحدة
        chunks = []
        if days:
            if len(days) <= 31:
                chunks = [days]
            else:
                c0_size = 31
                chunks.append(days[:c0_size])
                rem = days[c0_size:]
                while rem:
                    if len(rem) <= 34:
                        chunks.append(rem)
                        break
                    else:
                        chunks.append(rem[:34])
                        rem = rem[34:]
        else:
            chunks = [[]]

        pages_html = []
        for idx, chunk in enumerate(chunks):
            is_last = (idx == len(chunks) - 1)

            if idx == 0:
                header_block = gov_header_html
            else:
                header_block = f"""
                <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom:2px; border-collapse:collapse;">
                    <tr>
                        <td align="right" style="font-size:8pt; font-weight:bold; border:none; width:50%; padding:0;">
                            {title_text} - {art['name']} )تابع - صفحة {idx + 1}(
                        </td>
                        <td align="left" style="font-size:8pt; font-weight:bold; border:none; width:50%; padding:0;">
                            سعر الوحدة : {art['price_ttc']:,.2f} دج
                        </td>
                    </tr>
                </table>
                """

            rows_html = ""
            for d in chunk:
                d_display = d['date'].replace("-", "/")
                init_str = self._fmt_excel_qty(d["initial_stock"])
                sup_str = self._fmt_excel_qty(d["supply_in"])
                li_str = self._fmt_excel_qty(d["loan_in"])
                bf_str = self._fmt_excel_qty(d["bf_out"])
                lu_str = self._fmt_excel_qty(d["lu_out"])
                di_str = self._fmt_excel_qty(d["di_out"])
                lo_str = self._fmt_excel_qty(d["loan_out"])
                fin_str = self._fmt_excel_qty(d["final_stock"])

                rows_html += f"""
                <tr>
                    <td style="text-align:center; font-weight:bold; border:1px solid #000000; padding:0px 2px;">{fin_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{lo_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{di_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{lu_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{bf_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{li_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{sup_str}</td>
                    <td style="text-align:center; border:1px solid #000000; padding:0px 2px;">{init_str}</td>
                    <td style="text-align:center; font-weight:bold; border:1px solid #000000; font-size:7pt; padding:0px 2px;">{d_display}</td>
                </tr>
                """

            pb_sep = '<div style="page-break-before: always; height:0; line-height:0; margin:0; padding:0; clear:both;"></div>\n' if idx > 0 else ''
            page_div = f"""
            {pb_sep}
            <div class="page-container" style="margin: 0; padding: 0; box-sizing: border-box; page-break-inside: avoid;">
                {header_block}
                <table class="data-table" width="100%" border="1" cellspacing="0" cellpadding="0" style="width:100%; border-collapse:collapse; border:1px solid #000000; font-size:7pt;">
                    {thead_html}
                    <tbody>
                        {rows_html}
                    </tbody>
                    {tfoot_html if is_last else ''}
                </table>
                {signatures_html if is_last else ''}
            </div>
            """
            pages_html.append(page_div)

        content = "\n".join(pages_html)
        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<title>{title_text} - {art['name']}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; margin: 0; padding: 0; font-size: 7pt; font-weight: bold; color: #000; }}
    table.data-table {{ width: 100%; border-collapse: collapse; border: 1px solid #000000; }}
    table.data-table th, table.data-table td {{ border: 1px solid #000000; padding: 0px 2px; font-size: 7pt; }}
    .page-container {{ margin: 0; padding: 0; }}
</style>
</head>
<body>
{content}
</body>
</html>"""
        return html


    # -------------------------------------------------------------
    # 12. تصدير سجل النشاط بالأرقام إلى Excel (مثل ورقة النشاط بالأرقام)
    # -------------------------------------------------------------
    def export_activity_numbers_excel(self, year: Optional[int] = None, month: Optional[int] = None, save_path: str = "", start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """تصدير سجل النشاط بالأرقام إلى ملف Excel مطابق للورقة الرسمية"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "النشاط بالأرقام"
        ws.sheet_view.rightToLeft = True

        res_name = self.get_residence_name_ar()
        dir_name = self.get_directorate_name_ar()

        if start_date and end_date:
            period_title = f"النشاط بالأرقام للفترة من {start_date} إلى {end_date}"
            rep = self.meals_svc.get_monthly_activity_report(start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        else:
            m_name = self._get_arabic_month_name(month or 1)
            period_title = f"النشاط بالأرقام لشهر {m_name} {year or ''}"
            rep = self.meals_svc.get_monthly_activity_report(year, month, residence_id=self.residence_id)

        ws.merge_cells("A1:J1"); ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية - وزارة التعليم العالي والبحث العلمي"
        ws["A1"].font = Font(name="Segoe UI", size=11, bold=True); ws["A1"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A2:J2"); ws["A2"] = f"{dir_name} - {res_name}"
        ws["A2"].font = Font(name="Segoe UI", size=11); ws["A2"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A3:J3"); ws["A3"] = period_title
        ws["A3"].font = Font(name="Segoe UI", size=13, bold=True, color="0F2D25"); ws["A3"].alignment = Alignment(horizontal="center")

        header_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        header_font = Font(name="Segoe UI", size=10, bold=True)
        thin_border = Border(
            left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000")
        )

        ws.merge_cells("A5:A6"); ws["A5"] = "التاريخ"
        ws.merge_cells("B5:C5"); ws["B5"] = "وجبة الفطور"
        ws.merge_cells("D5:E5"); ws["D5"] = "وجبة الغذاء"
        ws.merge_cells("F5:G5"); ws["F5"] = "وجبة العشاء"
        ws.merge_cells("H5:J5"); ws["H5"] = "الإحصائيات"

        sub_headers = ["ع الوجبات", "المصاريف", "ع الوجبات", "المصاريف", "ع الوجبات", "المصاريف", "المعدل", "م المصاريف", "التكلفة"]
        for c, txt in enumerate(sub_headers, start=2):
            ws.cell(6, c, txt)

        for r in range(5, 7):
            for c in range(1, 11):
                cell = ws.cell(r, c)
                cell.fill = header_fill; cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

        row_idx = 7
        for d in rep["days"]:
            d_display = d['date'].replace("-", "/")
            ws.cell(row_idx, 1, d_display).alignment = Alignment(horizontal="center")
            ws.cell(row_idx, 2, d["bf_count"]).alignment = Alignment(horizontal="center")
            ws.cell(row_idx, 3, d["bf_expense"]).number_format = "#,##0.00"
            ws.cell(row_idx, 4, d["lu_count"]).alignment = Alignment(horizontal="center")
            ws.cell(row_idx, 5, d["lu_expense"]).number_format = "#,##0.00"
            ws.cell(row_idx, 6, d["di_count"]).alignment = Alignment(horizontal="center")
            ws.cell(row_idx, 7, d["di_expense"]).number_format = "#,##0.00"
            ws.cell(row_idx, 8, d["average_meals"] if d["average_meals"] > 0 else 0).number_format = "#,##0.0"
            ws.cell(row_idx, 9, d["total_expense"]).number_format = "#,##0.00"
            ws.cell(row_idx, 10, d["student_cost"]).number_format = "#,##0.00"

            for c in range(1, 11):
                ws.cell(row_idx, c).border = thin_border
            row_idx += 1

        # صف المجاميع
        ws.cell(row_idx, 1, "المجاميع العامة").font = Font(name="Segoe UI", bold=True)
        ws.cell(row_idx, 1).alignment = Alignment(horizontal="center")
        for col_idx in [2, 3, 4, 5, 6, 7, 9]:
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            ws.cell(row_idx, col_idx, f"=SUM({col_letter}7:{col_letter}{row_idx-1})").font = Font(name="Segoe UI", bold=True)
            if col_idx in [3, 5, 7, 9]:
                ws.cell(row_idx, col_idx).number_format = "#,##0.00"
        # عمود المعدل في صف المجاميع مطابق لملف FC09: =(الغداء + العشاء)/2 بالتقريب العلوي
        ws.cell(row_idx, 8, f"=(D{row_idx}+F{row_idx})/2").font = Font(name="Segoe UI", bold=True)
        ws.cell(row_idx, 8).number_format = "#,##0"
        # التكلفة الإجمالية في صف المجاميع: =(م المصاريف / المعدل) / 2
        ws.cell(row_idx, 10, f"=IF((D{row_idx}+F{row_idx})>0,I{row_idx}/(D{row_idx}+F{row_idx}),0)").font = Font(name="Segoe UI", bold=True)
        ws.cell(row_idx, 10).number_format = "#,##0.00"

        for c in range(1, 11):
            ws.cell(row_idx, c).border = thin_border
            ws.cell(row_idx, c).fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

        # جدول إحصائي ملخص (معدل اليوم الغذائي وعدد الأيام) مطابق لـ FC09
        tot_row = row_idx
        act_cnt = sum(1 for d in rep["days"] if (d["bf_count"] > 0 or d["lu_count"] > 0 or d["di_count"] > 0 or d["total_expense"] > 0))
        s_row = tot_row + 2
        ws.cell(s_row, 1, "عدد الأيام").font = header_font; ws.cell(s_row, 1).alignment = Alignment(horizontal="center")
        ws.cell(s_row, 2, act_cnt).font = Font(name="Segoe UI", bold=True); ws.cell(s_row, 2).alignment = Alignment(horizontal="center")
        ws.cell(s_row, 3, "مجموع المصاريف").font = header_font; ws.cell(s_row, 3).alignment = Alignment(horizontal="center")
        ws.cell(s_row, 4, f"=I{tot_row}").font = Font(name="Segoe UI", bold=True); ws.cell(s_row, 4).number_format = "#,##0.00"
        ws.cell(s_row, 5, "معدل اليوم الغذائي").font = header_font; ws.cell(s_row, 5).alignment = Alignment(horizontal="center")
        ws.cell(s_row, 6, f"=IF(B{s_row}>0,D{s_row}/B{s_row},0)").font = Font(name="Segoe UI", bold=True); ws.cell(s_row, 6).number_format = "#,##0.00"
        for c in range(1, 7):
            ws.cell(s_row, c).border = thin_border
            ws.cell(s_row, c).fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

        # ضبط العرض
        ws.column_dimensions["A"].width = 14
        for col_l in ["B", "C", "D", "E", "F", "G", "H", "I", "J"]:
            ws.column_dimensions[col_l].width = 14

        wb.save(save_path)
        return save_path

    # -------------------------------------------------------------
    # 13. تصدير بطاقة متابعة الوجبات إلى Excel (مثل ورقة بطاقة متابعة الوجبات)
    # -------------------------------------------------------------
    def export_meal_tracking_excel(self, year: Optional[int] = None, month: Optional[int] = None, save_path: str = "", start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """تصدير بطاقة متابعة الوجبات إلى ملف Excel مطابق للورقة الرسمية بـ 11 عموداً"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "بطاقة متابعة الوجبات"
        ws.sheet_view.rightToLeft = True

        res_name = self.get_residence_name_ar()
        dir_name = self.get_directorate_name_ar()

        if start_date and end_date:
            period_title = f"بطاقة متابعة الوجبات الغذائية للفترة من {start_date} إلى {end_date}"
            rep = self.meals_svc.get_monthly_activity_report(start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        else:
            m_name = self._get_arabic_month_name(month or 1)
            period_title = f"بطاقة متابعة الوجبات الغذائية لشهر {m_name} {year or ''}"
            rep = self.meals_svc.get_monthly_activity_report(year, month, residence_id=self.residence_id)

        ws.merge_cells("A1:K1"); ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية - وزارة التعليم العالي والبحث العلمي"
        ws["A1"].font = Font(name="Segoe UI", size=11, bold=True); ws["A1"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A2:K2"); ws["A2"] = f"{dir_name} - {res_name}"
        ws["A2"].font = Font(name="Segoe UI", size=11); ws["A2"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A3:K3"); ws["A3"] = period_title
        ws["A3"].font = Font(name="Segoe UI", size=14, bold=True, color="15803D"); ws["A3"].alignment = Alignment(horizontal="center")

        header_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        header_font = Font(name="Segoe UI", size=10, bold=True)
        thin_border = Border(
            left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000")
        )

        ws.merge_cells("A5:A7"); ws["A5"] = "التاريخ"
        ws.merge_cells("B5:G5"); ws["B5"] = "عـــــــــــــــــدد الوجبـــــــــــــــات"
        ws.merge_cells("B6:C6"); ws["B6"] = "فطور الصباح ( 1 )"
        ws.merge_cells("D6:E6"); ws["D6"] = "وجبـــــة الغـــــداء ( 2 )"
        ws.merge_cells("F6:G6"); ws["F6"] = "وجبـــــة العشـــــاء ( 3 )"
        ws["B7"] = "طلبة"; ws["C7"] = "عمال"
        ws["D7"] = "طلبة"; ws["E7"] = "عمال"
        ws["F7"] = "طلبة"; ws["G7"] = "عمال"

        ws.merge_cells("H5:H6"); ws["H5"] = "المعدل ( 4 ) :"
        ws["H7"] = "2 / ( 3 + 2 )"
        ws.merge_cells("I5:I7"); ws["I5"] = "النفقـــــــة ( 5 )"
        ws.merge_cells("J5:J6"); ws["J5"] = "كلفة اليوم"
        ws["J7"] = "الغذائي ( 7 )"
        ws.merge_cells("K5:K7"); ws["K5"] = "الكلفـــــــــة ( 6 )"

        for r in range(5, 8):
            for c in range(1, 12):
                cell = ws.cell(r, c)
                cell.fill = header_fill; cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

        row_idx = 8
        with self.db.get_connection() as conn:
            for d in rep["days"]:
                d_str = d["date"]
                m_row = conn.execute("SELECT * FROM daily_meals_tracking WHERE date = ? AND residence_id = ?", (d_str, self.residence_id)).fetchone()
                bf_st = m_row["bf_students"] if m_row else 0
                bf_sf = (m_row["bf_staff"] + m_row["bf_professors"] + m_row["bf_guests"] + m_row["bf_free"]) if m_row else 0
                lu_st = m_row["lu_students"] if m_row else 0
                lu_sf = (m_row["lu_staff"] + m_row["lu_professors"] + m_row["lu_guests"] + m_row["lu_free"]) if m_row else 0
                di_st = m_row["di_students"] if m_row else 0
                di_sf = (m_row["di_staff"] + m_row["di_professors"] + m_row["di_guests"] + m_row["di_free"]) if m_row else 0

                date_display = d_str.replace("-", "/")
                ws.cell(row_idx, 1, date_display).alignment = Alignment(horizontal="center")
                ws.cell(row_idx, 2, bf_st).alignment = Alignment(horizontal="center")
                ws.cell(row_idx, 3, bf_sf).alignment = Alignment(horizontal="center")
                ws.cell(row_idx, 4, lu_st).alignment = Alignment(horizontal="center")
                ws.cell(row_idx, 5, lu_sf).alignment = Alignment(horizontal="center")
                ws.cell(row_idx, 6, di_st).alignment = Alignment(horizontal="center")
                ws.cell(row_idx, 7, di_sf).alignment = Alignment(horizontal="center")
                ws.cell(row_idx, 8, f"=ROUNDUP(((D{row_idx}+E{row_idx})+(F{row_idx}+G{row_idx}))/2, 0)").number_format = "#,##0"
                ws.cell(row_idx, 9, d["total_expense"]).number_format = "#,##0.00"
                ws.cell(row_idx, 10, f"=IF(H{row_idx}>0,I{row_idx}/H{row_idx},0)").number_format = "#,##0.00"
                ws.cell(row_idx, 11, f"=IF((F{row_idx}+G{row_idx})>0,J{row_idx}/2,J{row_idx})").number_format = "#,##0.00"

                for c in range(1, 12):
                    ws.cell(row_idx, c).border = thin_border
                row_idx += 1

        # صف المجموع مطابق تماماً لـ FC09
        ws.cell(row_idx, 1, "المجموع").font = Font(name="Segoe UI", bold=True)
        ws.cell(row_idx, 1).alignment = Alignment(horizontal="center")
        for col_idx in [2, 3, 4, 5, 6, 7, 9]:
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            ws.cell(row_idx, col_idx, f"=SUM({col_letter}8:{col_letter}{row_idx-1})").font = Font(name="Segoe UI", bold=True)
            if col_idx == 9:
                ws.cell(row_idx, col_idx).number_format = "#,##0.00"
        ws.cell(row_idx, 8, f"=ROUNDUP(((D{row_idx}+E{row_idx})+(F{row_idx}+G{row_idx}))/2, 0)").font = Font(name="Segoe UI", bold=True)
        ws.cell(row_idx, 8).number_format = "#,##0"
        ws.cell(row_idx, 10, f"=IF(H{row_idx}>0,I{row_idx}/H{row_idx},0)").font = Font(name="Segoe UI", bold=True)
        ws.cell(row_idx, 10).number_format = "#,##0.00"
        ws.cell(row_idx, 11, f"=IF((F{row_idx}+G{row_idx})>0,J{row_idx}/2,J{row_idx})").font = Font(name="Segoe UI", bold=True)
        ws.cell(row_idx, 11).number_format = "#,##0.00"

        for c in range(1, 12):
            ws.cell(row_idx, c).border = thin_border
            ws.cell(row_idx, c).fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

        # ضبط العرض
        ws.column_dimensions["A"].width = 12
        for col_l in ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]:
            ws.column_dimensions[col_l].width = 13

        wb.save(save_path)
        return save_path

    # -------------------------------------------------------------
    # 14. تصدير الجدول التفصيلي للكميات إلى Excel (مثل ورقة جدول تفصيلي)
    # -------------------------------------------------------------
    def export_detailed_table_excel(self, year: Optional[int] = None, month: Optional[int] = None, save_path: str = "", start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """تصدير الجدول التفصيلي للكميات إلى ملف Excel مطابق للورقة الرسمية بـ 8 أعمدة"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "جدول تفصيلي"
        ws.sheet_view.rightToLeft = True

        res_name = self.get_residence_name_ar()
        dir_name = self.get_directorate_name_ar()

        if start_date and end_date:
            period_title = f"جدول تفصيلي لحركة المواد الغذائية للفترة من {start_date} إلى {end_date}"
            items = self.stock_svc.get_detailed_table(start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        else:
            m_name = self._get_arabic_month_name(month or 1)
            period_title = f"جدول تفصيلي لحركة المواد الغذائية لشهر {m_name} {year or ''}"
            items = self.stock_svc.get_detailed_table(year, month, residence_id=self.residence_id)

        ws.merge_cells("A1:H1"); ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية - وزارة التعليم العالي والبحث العلمي"
        ws["A1"].font = Font(name="Segoe UI", size=11, bold=True); ws["A1"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A2:H2"); ws["A2"] = f"{dir_name} - {res_name}"
        ws["A2"].font = Font(name="Segoe UI", size=11); ws["A2"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A3:H3"); ws["A3"] = period_title
        ws["A3"].font = Font(name="Segoe UI", size=13, bold=True, color="0F2D25"); ws["A3"].alignment = Alignment(horizontal="center")

        header_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        header_font = Font(name="Segoe UI", size=10, bold=True)
        thin_border = Border(
            left=Side(style="thin", color="94A3B8"), right=Side(style="thin", color="94A3B8"),
            top=Side(style="thin", color="94A3B8"), bottom=Side(style="thin", color="94A3B8")
        )

        ws.merge_cells("A5:A6"); ws["A5"] = "المواد"
        ws.merge_cells("B5:B6"); ws["B5"] = "الوحدة"
        ws.merge_cells("C5:C6"); ws["C5"] = "مخزون اول الشهر"
        ws.merge_cells("D5:E5"); ws["D5"] = "المذخولات"
        ws["D6"] = "التوريد"; ws["E6"] = "الإستعارة"
        ws.merge_cells("F5:G5"); ws["F5"] = "المخروجات"
        ws["F6"] = "الإستهلاك"; ws["G6"] = "الإعارة"
        ws.merge_cells("H5:H6"); ws["H5"] = "باقي المخزون"

        for r in range(5, 7):
            for c in range(1, 9):
                cell = ws.cell(r, c)
                cell.fill = header_fill; cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

        row_idx = 7
        for it in items:
            ws.cell(row_idx, 1, it["name"]).alignment = Alignment(horizontal="right")
            ws.cell(row_idx, 2, it["unit"]).alignment = Alignment(horizontal="center")
            ws.cell(row_idx, 3, it["initial_stock"]).number_format = "#,##0.00"
            ws.cell(row_idx, 4, it["supply_in"]).number_format = "#,##0.00"
            ws.cell(row_idx, 5, it["loan_in"]).number_format = "#,##0.00"
            ws.cell(row_idx, 6, it["cons_out"]).number_format = "#,##0.00"
            ws.cell(row_idx, 7, it["loan_out"]).number_format = "#,##0.00"
            ws.cell(row_idx, 8, f"=C{row_idx}+D{row_idx}+E{row_idx}-(F{row_idx}+G{row_idx})").number_format = "#,##0.00"

            for c in range(1, 9):
                ws.cell(row_idx, c).border = thin_border
            row_idx += 1

        ws.column_dimensions["A"].width = 28
        ws.column_dimensions["B"].width = 10
        for col_l in ["C", "D", "E", "F", "G", "H"]:
            ws.column_dimensions[col_l].width = 16

        wb.save(save_path)
        return save_path

    # -------------------------------------------------------------
    # 15. تصدير بطاقة حركة المخزون للمادة إلى Excel (مثل ورقة بطاقة مخزون)
    # -------------------------------------------------------------
    def export_stock_card_excel(self, article_id: int, year: Optional[int] = None, month: Optional[int] = None, save_path: str = "", start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """تصدير بطاقة حركة المخزون لمادة محددة إلى ملف Excel مطابق للورقة الرسمية"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "بطاقة مخزون"
        ws.sheet_view.rightToLeft = True

        res_name = self.get_residence_name_ar()
        dir_name = self.get_directorate_name_ar()

        if start_date and end_date:
            period_title = f"بطاقـة مخـزون للفترة من {start_date} إلى {end_date}"
            card = self.stock_svc.get_stock_card(article_id, start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        else:
            m_name = self._get_arabic_month_name(month or 1)
            period_title = f"بطاقـة مخـزون لشهر {m_name} {year or ''}"
            card = self.stock_svc.get_stock_card(article_id, year, month, residence_id=self.residence_id)

        art = card.get("article", {})

        ws.merge_cells("A1:I1"); ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية - وزارة التعليم العالي والبحث العلمي"
        ws["A1"].font = Font(name="Segoe UI", size=11, bold=True); ws["A1"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A2:I2"); ws["A2"] = f"{dir_name} - {res_name}"
        ws["A2"].font = Font(name="Segoe UI", size=11); ws["A2"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A3:I3"); ws["A3"] = period_title
        ws["A3"].font = Font(name="Segoe UI", size=13, bold=True, color="0F2D25"); ws["A3"].alignment = Alignment(horizontal="center")

        ws.merge_cells("A4:D4"); ws["A4"] = art.get('name', '')
        ws["A4"].font = Font(name="Segoe UI", size=12, bold=True)
        ws.merge_cells("G4:I4"); ws["G4"] = f"سعر الوحدة : {art.get('price_ttc', 0.0):,.2f}"
        ws["G4"].font = Font(name="Segoe UI", size=11, bold=True); ws["G4"].alignment = Alignment(horizontal="left")

        header_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        header_font = Font(name="Segoe UI", size=10, bold=True)
        thin_border = Border(
            left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000")
        )

        ws.merge_cells("A6:A7"); ws["A6"] = "التاريخ"
        ws.merge_cells("B6:B7"); ws["B6"] = "مخزون بداية المدة"
        ws.merge_cells("C6:D6"); ws["C6"] = "مدخولات"
        ws["C7"] = "توريد"; ws["D7"] = "إستعارة"
        ws.merge_cells("E6:H6"); ws["E6"] = "مخروجات"
        ws["E7"] = "صباح"; ws["F7"] = "غداء"; ws["G7"] = "عشاء"; ws["H7"] = "إعارة"
        ws.merge_cells("I6:I7"); ws["I6"] = "مخزون نهاية المدة"

        for r in range(6, 8):
            for c in range(1, 10):
                cell = ws.cell(r, c)
                cell.fill = header_fill; cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

        row_idx = 8
        for d in card.get("days", []):
            d_display = d['date'].replace("-", "/")
            ws.cell(row_idx, 1, d_display).alignment = Alignment(horizontal="center")
            ws.cell(row_idx, 2, d["initial_stock"]).number_format = "#,##0"
            ws.cell(row_idx, 3, d["supply_in"]).number_format = "#,##0"
            ws.cell(row_idx, 4, d["loan_in"]).number_format = "#,##0"
            ws.cell(row_idx, 5, d["bf_out"]).number_format = "#,##0"
            ws.cell(row_idx, 6, d["lu_out"]).number_format = "#,##0"
            ws.cell(row_idx, 7, d["di_out"]).number_format = "#,##0"
            ws.cell(row_idx, 8, d["loan_out"]).number_format = "#,##0"
            ws.cell(row_idx, 9, f"=B{row_idx}+C{row_idx}+D{row_idx}-(E{row_idx}+F{row_idx}+G{row_idx}+H{row_idx})").number_format = "#,##0"

            for c in range(1, 10):
                ws.cell(row_idx, c).border = thin_border
            row_idx += 1

        # صف المجاميع
        ws.cell(row_idx, 1, "المجموع العام").font = Font(name="Segoe UI", bold=True)
        ws.cell(row_idx, 1).alignment = Alignment(horizontal="center")
        for col_idx in [3, 4, 5, 6, 7, 8]:
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            ws.cell(row_idx, col_idx, f"=SUM({col_letter}8:{col_letter}{row_idx-1})").font = Font(name="Segoe UI", bold=True)
            ws.cell(row_idx, col_idx).number_format = "#,##0"
        ws.cell(row_idx, 9, f"=I{row_idx-1}").font = Font(name="Segoe UI", bold=True)
        ws.cell(row_idx, 9).number_format = "#,##0"

        for c in range(1, 10):
            ws.cell(row_idx, c).border = thin_border
            ws.cell(row_idx, c).fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

        ws.column_dimensions["A"].width = 14
        for col_l in ["B", "C", "D", "E", "F", "G", "H", "I"]:
            ws.column_dimensions[col_l].width = 14

        wb.save(save_path)
        return save_path

    # -------------------------------------------------------------
    # 16. تصدير سجل النشاط بالوجبة إلى Excel (مثل ورقة النشاط بالوجبة)
    # -------------------------------------------------------------
    def export_activity_meals_excel(self, year: Optional[int] = None, month: Optional[int] = None, save_path: str = "", start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """تصدير سجل النشاط بالوجبة إلى ملف Excel مطابق للورقة الرسمية بـ 4 أسطر لكل يوم"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "النشاط بالوجبة"
        ws.sheet_view.rightToLeft = True

        res_name = self.get_residence_name_ar()
        dir_name = self.get_directorate_name_ar()

        if start_date and end_date:
            period_title = f"النشاط بالوجبة للفترة من {start_date} إلى {end_date}"
            menus = self.meals_svc.get_monthly_menus_report(start_date=start_date, end_date=end_date, residence_id=self.residence_id)
        else:
            m_name = self._get_arabic_month_name(month or 1)
            period_title = f"النشاط بالوجبة لشهر {m_name} {year or ''}"
            menus = self.meals_svc.get_monthly_menus_report(year, month, residence_id=self.residence_id)

        ws.merge_cells("A1:D1"); ws["A1"] = "الجمهورية الجزائرية الديمقراطية الشعبية - وزارة التعليم العالي والبحث العلمي"
        ws["A1"].font = Font(name="Segoe UI", size=11, bold=True); ws["A1"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A2:D2"); ws["A2"] = f"{dir_name} - {res_name}"
        ws["A2"].font = Font(name="Segoe UI", size=11); ws["A2"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A3:D3"); ws["A3"] = period_title
        ws["A3"].font = Font(name="Segoe UI", size=13, bold=True, color="0F2D25"); ws["A3"].alignment = Alignment(horizontal="center")

        header_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        header_font = Font(name="Segoe UI", size=10, bold=True)
        thin_border = Border(
            left=Side(style="thin", color="000000"), right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"), bottom=Side(style="thin", color="000000")
        )

        ws.cell(5, 1, "التاريخ"); ws.cell(5, 2, "وجبة الصباح"); ws.cell(5, 3, "وجبة الغداء"); ws.cell(5, 4, "وجبة العشاء")
        for c in range(1, 5):
            ws.cell(5, c).fill = header_fill; ws.cell(5, c).font = header_font
            ws.cell(5, c).alignment = Alignment(horizontal="center", vertical="center")
            ws.cell(5, c).border = thin_border

        row_idx = 6
        for m in menus:
            bf_lines = self._split_into_4_lines(m["menu_breakfast"])
            lu_lines = self._split_into_4_lines(m["menu_lunch"])
            di_lines = self._split_into_4_lines(m["menu_dinner"])
            d_display = m['date'].replace("-", "/")

            # دمج خلية التاريخ على مدى 4 أسطر
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx+3, end_column=1)
            ws.cell(row_idx, 1, d_display).alignment = Alignment(horizontal="center", vertical="center")

            for i in range(4):
                ws.cell(row_idx + i, 2, bf_lines[i]).alignment = Alignment(horizontal="center", vertical="center")
                ws.cell(row_idx + i, 3, lu_lines[i]).alignment = Alignment(horizontal="center", vertical="center")
                ws.cell(row_idx + i, 4, di_lines[i]).alignment = Alignment(horizontal="center", vertical="center")
                for c in range(1, 5):
                    ws.cell(row_idx + i, c).border = thin_border

            row_idx += 4

        ws.column_dimensions["A"].width = 16
        ws.column_dimensions["B"].width = 30
        ws.column_dimensions["C"].width = 30
        ws.column_dimensions["D"].width = 30

        wb.save(save_path)
        return save_path

