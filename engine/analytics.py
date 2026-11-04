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

_active_sessions = {}

def _touch_active(identifier: str):
    if not identifier:
        return
    now = time.time()
    _active_sessions[identifier] = now
    expired = [k for k, v in list(_active_sessions.items()) if now - v > 300]
    for k in expired:
        _active_sessions.pop(k, None)

def _remove_active(identifier: str):
    if identifier:
        _active_sessions.pop(identifier, None)

def get_online_users_count():
    now = time.time()
    active = [k for k, v in list(_active_sessions.items()) if now - v < 65]
    return len(active)


DEFAULT_STATS = {
    "started_at": datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S"),
    "last_active": datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S"),
    "total_visits": 0,
    "total_chats": 0,
    "total_listens": 0,
    "unique_users_count": 0,
    "unique_users": [],
    "sessions_today": {},
    "chats_by_lang": {
        "en": 0,
        "zh": 0
    },
    "listens_by_lang": {
        "en": 0,
        "zh": 0
    },
    "chats_by_scenario": {},
    "daily_visits": {},
    "daily_chats": {},
    "daily_listens": {},
    "devices": {
        "mobile": 0,
        "desktop": 0
    },
    "recent_activities": []
}

BOT_KEYWORDS = (
    "googlebot", "bingbot", "yandexbot", "baiduspider", "duckduckbot",
    "facebookexternalhit", "slackbot", "twitterbot", "telegrambot",
    "uptime", "monitor", "keepalive", "curl/", "wget/", "headlesschrome"
)

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
    """Ghi nhận trực tiếp từ Server đảm bảo 100% thời gian thực không bị adblock nuốt mất"""
    ua_lower = (user_agent or "").lower()
    if any(b in ua_lower for b in BOT_KEYWORDS):
        return

    with _lock:
        data = _load_stats()
        today = _get_today_str()
        now_time = datetime.now(VN_TZ).strftime("%H:%M:%S")
        data["last_active"] = f"{today} {now_time}"

        if any(kw in ua_lower for kw in ["iphone", "android", "mobile", "ipad"]):
            device_type = "📱 Điện thoại"
            device_key = "mobile"
        else:
            device_type = "💻 Máy tính"
            device_key = "desktop"

        recent = data.setdefault("recent_activities", [])
        # Tránh ghi trùng liên tiếp trong cùng 1 giây
        if not recent or recent[0].get("time") != now_time or recent[0].get("desc") != f"Mở ứng dụng ({device_type})":
            recent.insert(0, {
                "time": now_time,
                "date": today,
                "type": "visit",
                "desc": f"Mở ứng dụng ({device_type})"
            })
            data["recent_activities"] = recent[:35]

        # Tăng tổng lượt vào
        data["total_visits"] = data.get("total_visits", 0) + 1
        daily = data.setdefault("daily_visits", {})
        daily[today] = daily.get(today, 0) + 1

        devs = data.setdefault("devices", {"mobile": 0, "desktop": 0})
        devs[device_key] = devs.get(device_key, 0) + 1

        _save_stats(data)

def record_client_event(event_type: str = "visit", details: str = "", user_id: str = "", session_id: str = "", platform: str = "", user_agent: str = "", lang: str = "en"):
    """Ghi nhận sự kiện chủ động từ JavaScript của trình duyệt (chống nuốt do cache)"""
    client_key = user_id or session_id or "cli_user"

    # Người dùng đóng tab hoặc chuyển trang: giảm ngay số online tức thì
    if event_type == "leave":
        _remove_active(client_key)
        return

    # Duy trì trạng thái online
    _touch_active(client_key)

    # Heartbeat định kỳ chỉ dùng để duy trì đếm người online thời gian thực,
    # tuyệt đối KHÔNG tăng total_visits và KHÔNG ghi vào recent_activities để tránh rác log
    if event_type == "heartbeat":
        return

    with _lock:
        data = _load_stats()
        today = _get_today_str()
        now = _get_now_str()

        data["last_active"] = now

        # Theo dõi người dùng độc nhất (Unique User) toàn thời gian & theo ngày
        if user_id:
            users_list = data.setdefault("unique_users", [])
            if user_id not in users_list:
                users_list.append(user_id)
                if len(users_list) > 2000:
                    users_list.pop(0)
            data["unique_users_count"] = max(data.get("unique_users_count", 0), len(users_list))

            daily_users = data.setdefault("daily_unique_users", {})
            today_users = daily_users.setdefault(today, [])
            if user_id not in today_users:
                today_users.append(user_id)

        # Theo dõi phiên (Session): Mỗi phiên mới tính 1 visit chính xác
        is_new_session = False
        if session_id:
            sessions_dict = data.setdefault("sessions_today", {})
            today_sessions = sessions_dict.setdefault(today, [])
            if session_id not in today_sessions:
                today_sessions.append(session_id)
                if len(today_sessions) > 500:
                    today_sessions.pop(0)
                is_new_session = True
                data["total_visits"] = data.get("total_visits", 0) + 1
                daily = data.setdefault("daily_visits", {})
                daily[today] = daily.get(today, 0) + 1

        # Phân loại thiết bị
        ua_str = f"{user_agent} {platform}".lower()
        devices = data.setdefault("devices", {"mobile": 0, "desktop": 0})
        if any(kw in ua_str for kw in ["iphone", "android", "mobile", "ipad"]):
            if is_new_session:
                devices["mobile"] = devices.get("mobile", 0) + 1
            device_label = "📱 Điện thoại"
        else:
            if is_new_session:
                devices["desktop"] = devices.get("desktop", 0) + 1
            device_label = "💻 Máy tính"

        # Ghi nhật ký chi tiết
        action_desc = details or f"Truy cập ứng dụng ({device_label})"
        recent = data.setdefault("recent_activities", [])
        recent.insert(0, {
            "time": datetime.now(VN_TZ).strftime("%H:%M:%S"),
            "date": today,
            "type": event_type,
            "desc": action_desc
        })
        data["recent_activities"] = recent[:35]

        _save_stats(data)

def record_listen(lang: str, text: str, user_id: str = ""):
    """Ghi nhận lượt nghe phát âm mẫu (tách riêng, KHÔNG cộng vào total_chats)"""
    if user_id:
        _touch_active(user_id)
    with _lock:
        data = _load_stats()
        today = _get_today_str()
        now = _get_now_str()

        data["last_active"] = now
        data["total_listens"] = data.get("total_listens", 0) + 1

        by_lang = data.setdefault("listens_by_lang", {"en": 0, "zh": 0})
        by_lang[lang] = by_lang.get(lang, 0) + 1

        daily = data.setdefault("daily_listens", {})
        daily[today] = daily.get(today, 0) + 1

        short_text = text[:32] + ("..." if len(text) > 32 else "")
        lang_label = "🇬🇧 Tiếng Anh" if lang == "en" else "🇨🇳 Tiếng Trung"
        recent = data.setdefault("recent_activities", [])
        recent.insert(0, {
            "time": datetime.now(VN_TZ).strftime("%H:%M:%S"),
            "date": today,
            "type": "listen",
            "desc": f"Nghe phát âm {lang_label}: \"{short_text}\""
        })
        data["recent_activities"] = recent[:35]
        _save_stats(data)

def record_chat(lang: str, scenario_id: str, user_id: str = ""):
    """Ghi nhận lượt hội thoại (chat tự do hoặc bấm chủ đề)"""
    if user_id:
        _touch_active(user_id)
    with _lock:
        data = _load_stats()
        today = _get_today_str()
        now = _get_now_str()

        data["total_chats"] = data.get("total_chats", 0) + 1
        data["last_active"] = now

        by_lang = data.setdefault("chats_by_lang", {"en": 0, "zh": 0})
        by_lang[lang] = by_lang.get(lang, 0) + 1

        by_scen = data.setdefault("chats_by_scenario", {})
        by_scen[scenario_id] = by_scen.get(scenario_id, 0) + 1

        daily = data.setdefault("daily_chats", {})
        daily[today] = daily.get(today, 0) + 1

        lang_label = "🇬🇧 Tiếng Anh" if lang == "en" else "🇨🇳 Tiếng Trung"
        recent = data.setdefault("recent_activities", [])
        recent.insert(0, {
            "time": datetime.now(VN_TZ).strftime("%H:%M:%S"),
            "date": today,
            "type": "chat",
            "desc": f"Luyện nói {lang_label} • Tình huống: {scenario_id}"
        })
        data["recent_activities"] = recent[:35]

        _save_stats(data)

def get_stats_summary():
    """Lấy dữ liệu tổng hợp phục vụ dashboard"""
    with _lock:
        data = _load_stats()
        today = _get_today_str()
        
        visits_today = data.get("daily_visits", {}).get(today, 0)
        chats_today = data.get("daily_chats", {}).get(today, 0)
        listens_today = data.get("daily_listens", {}).get(today, 0)
        unique_users_count = data.get("unique_users_count", len(data.get("unique_users", [])))
        
        today_u_list = data.get("daily_unique_users", {}).get(today, [])
        users_today_count = len(today_u_list)

        return {
            "started_at": data.get("started_at"),
            "last_active": data.get("last_active"),
            "total_visits": data.get("total_visits", 0),
            "visits_today": visits_today,
            "users_today": users_today_count,
            "unique_users_count": unique_users_count,
            "total_chats": data.get("total_chats", 0),
            "chats_today": chats_today,
            "total_listens": data.get("total_listens", 0),
            "listens_today": listens_today,
            "listens_by_lang": data.get("listens_by_lang", {"en": 0, "zh": 0}),
            "chats_by_lang": data.get("chats_by_lang", {"en": 0, "zh": 0}),
            "chats_by_scenario": data.get("chats_by_scenario", {}),
            "devices": data.get("devices", {"mobile": 0, "desktop": 0}),
            "daily_visits": data.get("daily_visits", {}),
            "daily_chats": data.get("daily_chats", {}),
            "daily_listens": data.get("daily_listens", {}),
            "recent_activities": data.get("recent_activities", []),
            "online_now": get_online_users_count()
        }
