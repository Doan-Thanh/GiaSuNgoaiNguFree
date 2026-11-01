import os
import json
import time
from datetime import datetime, timezone, timedelta
import threading
import logging

logger = logging.getLogger("ThanhBooksAnalytics")

# Múi giờ Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS_FILE = os.path.join(BASE_DIR, "stats.json")
_lock = threading.Lock()

DEFAULT_STATS = {
    "started_at": datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S"),
    "last_active": datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S"),
    "total_visits": 0,
    "total_chats": 0,
    "chats_by_lang": {
        "en": 0,
        "zh": 0
    },
    "chats_by_scenario": {},
    "daily_visits": {},
    "daily_chats": {},
    "devices": {
        "mobile": 0,
        "desktop": 0
    },
    "recent_activities": []
}

def _get_today_str():
    return datetime.now(VN_TZ).strftime("%Y-%m-%d")

def _get_now_str():
    return datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")

def _load_stats():
    if not os.path.exists(STATS_FILE):
        return DEFAULT_STATS.copy()
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all keys exist
            for k, v in DEFAULT_STATS.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        logger.warning(f"Lỗi đọc stats.json: {e}")
        return DEFAULT_STATS.copy()

def _save_stats(data):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Lỗi lưu stats.json: {e}")

def record_visit(user_agent: str = ""):
    with _lock:
        data = _load_stats()
        today = _get_today_str()
        now = _get_now_str()

        data["total_visits"] = data.get("total_visits", 0) + 1
        data["last_active"] = now

        # Daily visits
        daily = data.setdefault("daily_visits", {})
        daily[today] = daily.get(today, 0) + 1

        # Device detection
        ua_lower = (user_agent or "").lower()
        devices = data.setdefault("devices", {"mobile": 0, "desktop": 0})
        if any(kw in ua_lower for kw in ["iphone", "android", "mobile", "ipad"]):
            devices["mobile"] = devices.get("mobile", 0) + 1
            device_type = "📱 Điện thoại"
        else:
            devices["desktop"] = devices.get("desktop", 0) + 1
            device_type = "💻 Máy tính"

        # Log recent activity (keep max 30)
        recent = data.setdefault("recent_activities", [])
        recent.insert(0, {
            "time": datetime.now(VN_TZ).strftime("%H:%M:%S"),
            "date": today,
            "type": "visit",
            "desc": f"Mở ứng dụng ({device_type})"
        })
        data["recent_activities"] = recent[:30]

        _save_stats(data)

def record_chat(lang: str, scenario_id: str):
    with _lock:
        data = _load_stats()
        today = _get_today_str()
        now = _get_now_str()

        data["total_chats"] = data.get("total_chats", 0) + 1
        data["last_active"] = now

        # Language breakdown
        by_lang = data.setdefault("chats_by_lang", {"en": 0, "zh": 0})
        by_lang[lang] = by_lang.get(lang, 0) + 1

        # Scenario breakdown
        by_scen = data.setdefault("chats_by_scenario", {})
        by_scen[scenario_id] = by_scen.get(scenario_id, 0) + 1

        # Daily chats
        daily = data.setdefault("daily_chats", {})
        daily[today] = daily.get(today, 0) + 1

        # Friendly scenario title
        lang_label = "🇬🇧 Tiếng Anh" if lang == "en" else "🇨🇳 Tiếng Trung"
        recent = data.setdefault("recent_activities", [])
        recent.insert(0, {
            "time": datetime.now(VN_TZ).strftime("%H:%M:%S"),
            "date": today,
            "type": "chat",
            "desc": f"Luyện nói {lang_label} • Tình huống: {scenario_id}"
        })
        data["recent_activities"] = recent[:30]

        _save_stats(data)

def get_stats_summary():
    with _lock:
        data = _load_stats()
        today = _get_today_str()
        
        visits_today = data.get("daily_visits", {}).get(today, 0)
        chats_today = data.get("daily_chats", {}).get(today, 0)
        
        return {
            "started_at": data.get("started_at"),
            "last_active": data.get("last_active"),
            "total_visits": data.get("total_visits", 0),
            "visits_today": visits_today,
            "total_chats": data.get("total_chats", 0),
            "chats_today": chats_today,
            "chats_by_lang": data.get("chats_by_lang", {"en": 0, "zh": 0}),
            "chats_by_scenario": data.get("chats_by_scenario", {}),
            "devices": data.get("devices", {"mobile": 0, "desktop": 0}),
            "daily_visits": data.get("daily_visits", {}),
            "daily_chats": data.get("daily_chats", {}),
            "recent_activities": data.get("recent_activities", [])
        }
