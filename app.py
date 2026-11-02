import os
import json
import logging
import webbrowser
import threading
import time
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from engine.port_finder import find_safe_port
from engine.tts_engine import generate_speech_base64, VOICE_OPTIONS, DEFAULT_VOICES
from engine.ai_tutor import SCENARIOS, process_tutor_chat, get_dynamic_offline_response, generate_fresh_suggestions, start_topic_conversation
import engine.analytics as analytics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ThanhBooksAI")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_config():
    default_cfg = {
        "geminiApiKey": os.environ.get("GEMINI_API_KEY", ""),
        "geminiModel": os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        "currentLang": "zh",
        "voiceEn": DEFAULT_VOICES["en"],
        "voiceZh": DEFAULT_VOICES["zh"],
        "showPinyin": True,
        "showTranslation": True,
        "donateBank": "ACB (Ngân hàng Á Châu)",
        "donateAcc": "8335897",
        "donateName": "DOAN DUC THANH"
    }
    if not os.path.exists(CONFIG_FILE):
        return default_cfg
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = {**default_cfg, **json.load(f)}
            if not cfg.get("geminiApiKey") and os.environ.get("GEMINI_API_KEY"):
                cfg["geminiApiKey"] = os.environ.get("GEMINI_API_KEY")
            return cfg
    except Exception:
        return default_cfg

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

app = FastAPI(title="Gia Sư Ngoại Ngữ Free - Học Nói Tiếng Anh & Tiếng Trung")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/api/ping")
async def ping_keep_alive():
    """Endpoint siêu nhẹ phục vụ Keep-Alive, không ghi nhận visit ảo vào analytics"""
    return {"status": "awake", "service": "GiaSuNgoaiNguFree", "timestamp": time.time()}

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    ua = request.headers.get("user-agent", "")
    analytics.record_visit(ua)
    index_path = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h3>Chưa tìm thấy templates/index.html</h3>")

ADMIN_KEYS = {"thanhbooks", "8335897"}

@app.get("/stats", response_class=HTMLResponse)
async def serve_stats():
    stats_path = os.path.join(BASE_DIR, "templates", "stats.html")
    if os.path.exists(stats_path):
        with open(stats_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h3>Chưa tìm thấy templates/stats.html</h3>")

@app.get("/api/stats")
async def get_stats_data(key: str = ""):
    if key not in ADMIN_KEYS:
        raise HTTPException(status_code=403, detail="Mật mã quản trị không chính xác.")
    return analytics.get_stats_summary()

@app.get("/api/config")
async def get_config():
    cfg = load_config()
    return {
        "config": cfg,
        "voiceOptions": VOICE_OPTIONS,
        "hasKey": bool(cfg.get("geminiApiKey", "").strip())
    }

@app.post("/api/config")
async def update_config(data: dict = Body(...)):
    cfg = load_config()
    for k, v in data.items():
        cfg[k] = v
    save_config(cfg)
    return {"success": True, "config": cfg}

@app.get("/api/scenarios")
async def get_scenarios(lang: str = "en"):
    scenarios = SCENARIOS.get(lang, SCENARIOS["en"])
    return {"success": True, "lang": lang, "scenarios": scenarios}

@app.post("/api/chat")
async def handle_chat(payload: dict = Body(...)):
    user_text = payload.get("userText", "").strip()
    lang = payload.get("lang", "en")
    scenario_id = payload.get("scenarioId", "free_chat" if lang == "en" else "free_zh")
    voice = payload.get("voice")
    history = payload.get("history", [])
    turn_count = payload.get("turnCount", 1)

    if not user_text:
        raise HTTPException(status_code=400, detail="Nội dung nói không được để trống.")

    # Ghi nhận thống kê lượt luyện nói
    try:
        analytics.record_chat(lang=lang, scenario_id=scenario_id)
    except Exception as e:
        logger.warning(f"Lỗi ghi nhận analytics chat: {e}")

    cfg = load_config()
    api_key = cfg.get("geminiApiKey", "").strip()
    preferred_model = cfg.get("geminiModel", "gemini-3.5-flash-lite")

    # Phân tích ngữ cảnh và tạo câu trả lời + 3 gợi ý linh động
    ai_result = process_tutor_chat(
        api_key=api_key,
        user_text=user_text,
        lang=lang,
        scenario_id=scenario_id,
        history=history,
        turn_count=turn_count,
        preferred_model=preferred_model
    )

    speak_text = ""
    if lang == "zh":
        speak_text = ai_result.get("reply_hanzi", "")
        chosen_voice = voice or cfg.get("voiceZh", DEFAULT_VOICES["zh"])
    else:
        speak_text = ai_result.get("reply", "")
        chosen_voice = voice or cfg.get("voiceEn", DEFAULT_VOICES["en"])

    audio_b64 = await generate_speech_base64(speak_text, chosen_voice, lang)

    return {
        "success": True,
        "lang": lang,
        "aiResult": ai_result,
        "audio": audio_b64
    }

@app.post("/api/topic/start")
async def start_topic(payload: dict = Body(...)):
    topic = payload.get("topic", "Trò chuyện tự do").strip()
    lang = payload.get("lang", "en")
    voice = payload.get("voice")

    cfg = load_config()
    api_key = cfg.get("geminiApiKey", "").strip()
    preferred_model = cfg.get("geminiModel", "gemini-3.5-flash-lite")

    ai_result = start_topic_conversation(
        api_key=api_key,
        topic=topic,
        lang=lang,
        preferred_model=preferred_model
    )

    speak_text = ai_result.get("reply_hanzi", "") if lang == "zh" else ai_result.get("reply", "")
    chosen_voice = voice or (cfg.get("voiceZh", DEFAULT_VOICES["zh"]) if lang == "zh" else cfg.get("voiceEn", DEFAULT_VOICES["en"]))
    audio_b64 = await generate_speech_base64(speak_text, chosen_voice, lang)

    return {
        "success": True,
        "lang": lang,
        "topic": topic,
        "aiResult": ai_result,
        "audio": audio_b64
    }

@app.post("/api/suggestions/refresh")
async def refresh_suggestions(payload: dict = Body(...)):
    lang = payload.get("lang", "en")
    scenario_id = payload.get("scenarioId", "free_chat" if lang == "en" else "free_zh")
    history = payload.get("history", [])

    cfg = load_config()
    api_key = cfg.get("geminiApiKey", "").strip()
    preferred_model = cfg.get("geminiModel", "gemini-3.5-flash-lite")

    suggestions = generate_fresh_suggestions(
        api_key=api_key,
        lang=lang,
        scenario_id=scenario_id,
        history=history,
        preferred_model=preferred_model
    )
    return {"success": True, "suggestions": suggestions}

@app.post("/api/tts")
async def text_to_speech(payload: dict = Body(...)):
    text = payload.get("text", "").strip()
    lang = payload.get("lang", "en")
    voice = payload.get("voice")

    if not text:
        raise HTTPException(status_code=400, detail="Thiếu văn bản cần phát âm.")

    audio_b64 = await generate_speech_base64(text, voice, lang)
    return {"success": True, "audio": audio_b64}

def launch_server():
    env_port = os.environ.get("PORT")
    if env_port:
        port = int(env_port)
        host = "0.0.0.0"
        is_cloud = True
    else:
        port = find_safe_port(start_port=53210, end_port=53280)
        host = "127.0.0.1"
        is_cloud = False

    url = f"http://127.0.0.1:{port}" if not is_cloud else f"http://0.0.0.0:{port}"

    try:
        with open(os.path.join(BASE_DIR, "runtime_port.json"), "w") as f:
            json.dump({"port": port, "url": url, "timestamp": time.time()}, f)
    except Exception:
        pass

    logger.info("=" * 60)
    logger.info("  🎉 GIA SƯ NGOẠI NGỮ FREE (TIẾNG ANH & TIẾNG TRUNG) ĐÃ KHỞI CHẠY!")
    logger.info(f"  🌐 Truy cập Web App: {url}")
    logger.info("  👤 Phát triển bởi: ThanhBooks (Đoàn Đức Thanh)")
    logger.info("=" * 60)

    if not is_cloud:
        def _open_browser():
            time.sleep(1.2)
            webbrowser.open(url)
        threading.Thread(target=_open_browser, daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="warning")

if __name__ == "__main__":
    launch_server()
