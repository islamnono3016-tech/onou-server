import os
import sys
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "initial_setup_completed": False,
    "app_mode": "DIRECTORATE_SERVER",  # "DIRECTORATE_SERVER", "RESIDENCE_CLIENT", "STANDALONE"
    "residence_id": 1,
    "residence_name": "الإقامة الجامعية محمد الطاهر العبيدي",
    "server_host": "127.0.0.1",
    "server_port": 8050,
    "auto_sync": True,
    "sync_interval_seconds": 30,
    "timeout_seconds": 5.0,
    "theme": "DARK",
    "jwt_secret": "dou-ouargla-catering-secret-key-2026",
    "auto_backup_enabled": True,
    "auto_backup_time": "16:00",
    "auto_backup_dir": "",
    "last_auto_backup_date": ""
}

class AppConfig:
    _data: Dict[str, Any] = {}

    @classmethod
    def load(cls) -> Dict[str, Any]:
        cfg_path = os.path.abspath(CONFIG_FILE)
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cls._data = {**DEFAULT_CONFIG, **json.load(f)}
            except Exception as e:
                logger.error(f"Error loading config.json: {e}")
                cls._data = dict(DEFAULT_CONFIG)
        else:
            cls._data = dict(DEFAULT_CONFIG)
            cls.save()
        return cls._data

    @classmethod
    def save(cls, data: Dict[str, Any] = None) -> None:
        if data:
            cls._data.update(data)
        cfg_path = os.path.abspath(CONFIG_FILE)
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cls._data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error saving config.json: {e}")

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        if not cls._data:
            cls.load()
        return cls._data.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        if not cls._data:
            cls.load()
        cls._data[key] = value
        cls.save()

    @classmethod
    def is_server_mode(cls) -> bool:
        return cls.get("app_mode", "DIRECTORATE_SERVER") == "DIRECTORATE_SERVER"

    @classmethod
    def is_client_mode(cls) -> bool:
        return cls.get("app_mode") == "RESIDENCE_CLIENT"

    @classmethod
    def is_standalone(cls) -> bool:
        return cls.get("app_mode") == "STANDALONE"

    @classmethod
    def is_setup_completed(cls) -> bool:
        return bool(cls.get("initial_setup_completed", False))

    @classmethod
    def get_server_url(cls) -> str:
        """تنسيق وتوليد رابط الخادم بشكل ذكي يدعم النطاقات، السيرفرات السحابية (HTTPS/HTTP)، والـ IPs المحلية والعامة"""
        raw_host = str(cls.get("server_host", "127.0.0.1")).strip()
        port = cls.get("server_port", 8050)
        if not raw_host:
            raw_host = "127.0.0.1"

        if raw_host.startswith("http://") or raw_host.startswith("https://"):
            domain_part = raw_host.split("://", 1)[1]
            if ":" in domain_part or "/" in domain_part or port in (80, 443):
                return raw_host.rstrip("/")
            return f"{raw_host.rstrip('/')}:{port}"

        # عنوان بدون بروتوكول
        if ":" in raw_host:
            return f"http://{raw_host}"
        if port == 443:
            return f"https://{raw_host}"
        return f"http://{raw_host}:{port}"
