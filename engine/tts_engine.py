import base64
import edge_tts
import logging

logger = logging.getLogger("ThanhBooksAI.TTS")

DEFAULT_VOICES = {
    "en": "en-US-JennyNeural",
    "zh": "zh-CN-XiaoxiaoNeural"
}

VOICE_OPTIONS = {
    "en": [
        {"id": "en-US-JennyNeural", "name": "Jenny (Nữ - Mỹ, tự nhiên, truyền cảm)"},
        {"id": "en-US-GuyNeural", "name": "Guy (Nam - Mỹ, trầm ấm)"},
        {"id": "en-GB-SoniaNeural", "name": "Sonia (Nữ - Anh, chuẩn quý tộc)"}
    ],
    "zh": [
        {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 Xiaoxiao (Nữ - Phổ thông Bắc Kinh, ngọt ngào)"},
        {"id": "zh-CN-YunxiNeural", "name": "云希 Yunxi (Nam - Trẻ trung, tự nhiên)"},
        {"id": "zh-CN-YunjianNeural", "name": "云健 Yunjian (Nam - Trưởng thành, chuyên nghiệp)"}
    ]
}

async def generate_speech_base64(text: str, voice: str = None, lang: str = "en") -> str:
    """
    Sinh file âm thanh giọng bản xứ và chuyển đổi thành base64 data URL để trình duyệt phát tức thì.
    """
    if not voice:
        voice = DEFAULT_VOICES.get(lang, "en-US-JennyNeural")

    # Loại bỏ ký tự Pinyin hoặc Markdown để tránh đọc nhầm vào voice
    clean_text = text.replace("**", "").replace("*", "").replace("`", "")

    try:
        comm = edge_tts.Communicate(clean_text, voice)
        audio_data = b""
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        if not audio_data:
            return ""

        b64 = base64.b64encode(audio_data).decode("utf-8")
        return f"data:audio/mp3;base64,{b64}"
    except Exception as e:
        logger.error(f"Lỗi tạo giọng đọc TTS: {e}")
        return ""
