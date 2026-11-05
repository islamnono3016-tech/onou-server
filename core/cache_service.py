import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class CacheService:
    """
    نظام التخزين المؤقت في الذاكرة الرامية (High-Speed In-Memory Cache)
    يقضي تماماً على تكرار قراءة دليل المواد والفئات والإقامات من القرص
    مما يجعل التنقل بين الواجهات وتصفية المواد فورياً وبزمن استجابة 0 ميلي ثانية.
    """
    _instance = None

    _articles_cache: Dict[int, List[Dict[str, Any]]] = {}     # residence_id -> list of articles
    _article_by_id_cache: Dict[int, Dict[int, Dict[str, Any]]] = {} # residence_id -> (art_id -> article)
    _categories_cache: Optional[List[Dict[str, Any]]] = None
    _residences_cache: Optional[List[Dict[str, Any]]] = None
    _cache_timestamps: Dict[str, float] = {}

    CACHE_TTL_SECONDS = 300  # 5 minutes default TTL

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheService, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_articles(cls, db: DatabaseManager, residence_id: int = 1, only_active: bool = True) -> List[Dict[str, Any]]:
        """جلب دليل المواد من الذاكرة الرامية بسرعة فائقة مع التحديث التلقائي عند الحاجة"""
        cache_key = f"articles_{residence_id}_{only_active}"
        now = time.time()
        last_time = cls._cache_timestamps.get(cache_key, 0)

        if cache_key in cls._articles_cache and (now - last_time < cls.CACHE_TTL_SECONDS):
            return cls._articles_cache[cache_key]

        # إعادة القراءة من قاعدة البيانات وتخزينها في الذاكرة مع أسعار كل إقامة المعزولة
        query = """
            SELECT a.id, a.code, a.name, a.category_id, a.unit,
                   COALESCE(ra.price_ht, a.price_ht) as price_ht,
                   COALESCE(ra.discount_rate, a.discount_rate) as discount_rate,
                   COALESCE(ra.discount_amount, a.discount_amount) as discount_amount,
                   COALESCE(ra.price_after_discount, a.price_after_discount) as price_after_discount,
                   COALESCE(ra.tva_rate, a.tva_rate) as tva_rate,
                   COALESCE(ra.price_ttc, a.price_ttc) as price_ttc,
                   COALESCE(ra.current_pmp, a.current_pmp, a.price_ttc) as current_pmp,
                   COALESCE(ra.safety_stock, a.safety_stock) as safety_stock,
                   COALESCE(ra.initial_stock, a.initial_stock) as initial_stock,
                   COALESCE(ra.current_stock, a.current_stock) as current_stock,
                   a.is_active, c.name as category_name 
            FROM articles a
            LEFT JOIN categories c ON a.category_id = c.id
            LEFT JOIN residence_articles ra ON a.id = ra.article_id AND ra.residence_id = ?
        """
        if only_active:
            query += " WHERE a.is_active = 1"
        query += " ORDER BY a.id ASC"

        with db.get_connection() as conn:
            cur = conn.execute(query, (residence_id,))
            articles = [dict(r) for r in cur.fetchall()]

        cls._articles_cache[cache_key] = articles
        cls._cache_timestamps[cache_key] = now

        # تحديث فهرس البحث السريع بالمعرف
        if residence_id not in cls._article_by_id_cache:
            cls._article_by_id_cache[residence_id] = {}
        for art in articles:
            cls._article_by_id_cache[residence_id][art["id"]] = art

        return articles

    @classmethod
    def get_article_by_id(cls, db: DatabaseManager, article_id: int, residence_id: int = 1) -> Optional[Dict[str, Any]]:
        """البحث عن مادة بمعرفها مباشرة من الذاكرة بـ O(1)"""
        if residence_id in cls._article_by_id_cache and article_id in cls._article_by_id_cache[residence_id]:
            return cls._article_by_id_cache[residence_id][article_id]
        
        # إذا لم تكن موجودة، يتم تحميل الكتالوج كاملاً
        cls.get_articles(db, residence_id)
        return cls._article_by_id_cache.get(residence_id, {}).get(article_id)

    @classmethod
    def get_categories(cls, db: DatabaseManager) -> List[Dict[str, Any]]:
        """جلب قائمة الفئات من الذاكرة"""
        now = time.time()
        last_time = cls._cache_timestamps.get("categories", 0)
        if cls._categories_cache is not None and (now - last_time < cls.CACHE_TTL_SECONDS):
            return cls._categories_cache

        with db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM categories ORDER BY id ASC")
            cls._categories_cache = [dict(r) for r in cur.fetchall()]
        cls._cache_timestamps["categories"] = now
        return cls._categories_cache

    @classmethod
    def get_residences(cls, db: DatabaseManager, only_active: bool = True) -> List[Dict[str, Any]]:
        """جلب قائمة الإقامات من الذاكرة"""
        now = time.time()
        cache_key = f"residences_{only_active}"
        last_time = cls._cache_timestamps.get(cache_key, 0)
        if cls._residences_cache is not None and (now - last_time < cls.CACHE_TTL_SECONDS):
            return cls._residences_cache

        with db.get_connection() as conn:
            sql = "SELECT * FROM residences"
            if only_active:
                sql += " WHERE is_active = 1"
            sql += " ORDER BY id ASC"
            cur = conn.execute(sql)
            residences = [dict(r) for r in cur.fetchall()]

        cls._residences_cache = residences
        cls._cache_timestamps[cache_key] = now
        return residences

    @classmethod
    def invalidate_articles(cls, residence_id: Optional[int] = None):
        """إبطال الكاش الخاص بالمواد لإجبار التطبيق على القراءة المحدثة فوراً"""
        if residence_id is not None:
            keys_to_remove = [k for k in cls._articles_cache if k.startswith(f"articles_{residence_id}_")]
            for k in keys_to_remove:
                cls._articles_cache.pop(k, None)
                cls._cache_timestamps.pop(k, None)
            cls._article_by_id_cache.pop(residence_id, None)
        else:
            cls._articles_cache.clear()
            cls._article_by_id_cache.clear()
            cls._cache_timestamps.clear()

    @classmethod
    def invalidate_all(cls):
        """مسح كامل التخزين المؤقت"""
        cls._articles_cache.clear()
        cls._article_by_id_cache.clear()
        cls._categories_cache = None
        cls._residences_cache = None
        cls._cache_timestamps.clear()
