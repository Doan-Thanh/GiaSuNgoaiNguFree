import json
import logging
import random
import requests

logger = logging.getLogger("ThanhBooksAI.Tutor")

SCENARIOS = {
    "en": [
        {
            "id": "free_chat",
            "title": "💬 Trò Chuyện Tự Do (Casual Daily Talk)",
            "description": "Tán gẫu thoải mái về sở thích, âm nhạc, phim ảnh, văn hóa cùng bạn bản xứ.",
            "botRole": "Người bạn bản xứ vui tính đến từ California",
            "initialMessage": "Hey! How's your day going so far? Doing anything fun today?",
            "initialIpa": "/heɪ! haʊz jʊər deɪ ˈɡoʊɪŋ soʊ fɑːr? ˈduːɪŋ ˈeniθɪŋ fʌn təˈdeɪ?/",
            "initialTranslation": "Chào bạn! Ngày hôm nay của bạn thế nào rồi? Có làm gì vui không?",
            "initialSuggestions": [
                "It's going great! Just relaxing with some music. (/ɪts ˈɡoʊɪŋ ɡreɪt! dʒʌst rɪˈlæksɪŋ wɪð səm ˈmjuːzɪk/ - Mọi thứ đang rất tuyệt! Mình đang thư giãn với chút âm nhạc.)",
                "A bit busy with work, but looking forward to the weekend! (/ə bɪt ˈbɪzi wɪð wɜːrk, bʌt ˈlʊkɪŋ ˈfɔːrwərd tuː ðə ˈwiːkend/ - Hơi bận với công việc, nhưng đang mong đến cuối tuần!)",
                "Not much, just practicing English with this app. (/nɑːt mʌtʃ, dʒʌst ˈpræktɪsɪŋ ˈɪŋɡlɪʃ wɪð ðɪs æp/ - Không có gì nhiều, mình chỉ đang luyện tiếng Anh với ứng dụng này.)"
            ]
        }
    ],
    "zh": [
        {
            "id": "free_zh",
            "title": "💬 Trò Chuyện Tự Do (日常闲聊)",
            "description": "Luyện phản xạ giao tiếp tự nhiên, luyện thanh điệu và ngữ pháp tiếng Trung cơ bản.",
            "botRole": "Bạn học người Trung Quốc vui vẻ, kiên nhẫn",
            "initialHanzi": "你好啊！很高兴和你练习中文。你学中文多久了？平时最喜欢做什么？",
            "initialPinyin": "Nǐ hǎo a! Hěn gāoxìng hé nǐ liànxí Zhōngwén. Nǐ xué Zhōngwén duōjiǔ le? Píngshí zuì xǐhuan zuò shénme?",
            "initialTranslation": "Chào bạn nhé! Rất vui được cùng bạn luyện tập tiếng Trung. Bạn học tiếng Trung được bao lâu rồi? Bình thường bạn thích làm gì nhất?",
            "initialSuggestions": [
                "你好！我学中文大概半年了，平时喜欢听中文歌和看电影 (Nǐ hǎo! Wǒ xué Zhōngwén dàgài bàn nián le, píngshí xǐhuan tīng Zhōngwén gē hé kàn diànyǐng - Chào bạn! Mình học tiếng Trung khoảng nửa năm rồi, hay nghe nhạc và xem phim)",
                "我主要是为了去中国旅游和工作，声调对我来说有点难 (Wǒ zhǔyào shì wèile qù Zhōngguó lǚyóu hé gōngzuò, shēngdiào duì wǒ láishuō yǒudiǎn nán - Mình học để đi du lịch và làm việc, thanh điệu hơi khó với mình)",
                "今天想跟你聊聊中国的美食，你家乡有什么好吃的？ (Jīntiān xiǎng gēn nǐ liáoliao Zhōngguó de měishí, nǐ jiāxiāng yǒu shénme hǎochī de? - Hôm nay muốn buôn chuyện ẩm thực với bạn, quê bạn có món gì ngon?)"
            ]
        }
    ]
}

VI_ACCENTS = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ"

def sanitize_ai_result(result: dict, lang: str, topic: str = "free") -> dict:
    """Bộ lọc kiểm toán ngôn ngữ tuyệt đối: Ngăn chặn triệt để hiện tượng AI nhầm lẫn hoặc rò rỉ ngôn ngữ chéo."""
    if not isinstance(result, dict):
        return result

    if lang == "en":
        # 1. Diệt trừ triệt để việc nhắc nhầm tiếng Trung trong bài học tiếng Anh
        fb = result.get("feedback", "")
        if fb:
            bad_words = ["tiếng Trung", "tiếng Hoa", "tiếng Hán", "bằng tiếng Trung", "bằng tiếng Hoa", "nói tiếng Trung", "nói tiếng Hoa"]
            for bw in bad_words:
                fb = fb.replace(bw, "tiếng Anh")
            result["feedback"] = fb

        # 2. Đảm bảo 'reply' là 100% tiếng Anh, không bị AI nhét tiếng Việt vào ô 'reply'
        reply = (result.get("reply") or "").strip()
        vi_count = sum(1 for c in reply if c in VI_ACCENTS)
        if not reply or vi_count >= 3:
            # AI trả lời nhầm bằng tiếng Việt vào ô reply tiếng Anh
            logger.warning(f"Phát hiện reply tiếng Anh bị lẫn tiếng Việt ('{reply[:30]}...'), tiến hành tự động hiệu chỉnh.")
            if vi_count >= 3 and not result.get("translation_vi"):
                result["translation_vi"] = reply
            offline = get_topic_offline_opener(topic, "en")
            result["reply"] = offline.get("reply", "Hey there! How is your day going so far? What have you been up to today?")
            result["reply_ipa"] = offline.get("reply_ipa", "/heɪ ðɛr! haʊ ɪz jʊər deɪ ˈɡoʊɪŋ soʊ fɑːr? wʌt hæv juː biːn ʌp tuː təˈdeɪ?/")
            if not result.get("translation_vi"):
                result["translation_vi"] = offline.get("translation_vi", "Chào bạn! Ngày hôm nay của bạn thế nào rồi? Hôm nay bạn đã làm những gì rồi?")

        # Đảm bảo có gợi ý đàm thoại tiếng Anh
        if not result.get("suggested_replies") or not isinstance(result["suggested_replies"], list) or len(result["suggested_replies"]) == 0:
            offline = get_topic_offline_opener(topic, "en")
            result["suggested_replies"] = offline.get("suggested_replies", [])

    elif lang == "zh":
        # 1. Diệt trừ triệt để việc nhắc nhầm tiếng Anh trong bài học tiếng Trung
        fb = result.get("feedback", "")
        if fb:
            bad_words = ["tiếng Anh", "bằng tiếng Anh", "nói tiếng Anh"]
            for bw in bad_words:
                fb = fb.replace(bw, "tiếng Trung")
            result["feedback"] = fb

        # 2. Đảm bảo 'reply_hanzi' phải có chữ Hán
        hanzi = (result.get("reply_hanzi") or "").strip()
        has_cjk = any('\u4e00' <= c <= '\u9fff' for c in hanzi)
        if not hanzi or not has_cjk:
            logger.warning("Phát hiện reply tiếng Trung thiếu chữ Hán, tiến hành tự động hiệu chỉnh.")
            offline = get_topic_offline_opener(topic, "zh")
            result["reply_hanzi"] = offline.get("reply_hanzi", "你好呀！今天过得怎么样？很高兴能和你一起轻松聊聊天！")
            result["reply_pinyin"] = offline.get("reply_pinyin", "Nǐ hǎo ya! Jīntiān guò de zěnmeyàng? Hěn gāoxìng néng hé nǐ yìqǐ qīngsōng liáoliáo tiān!")
            if not result.get("translation_vi"):
                result["translation_vi"] = offline.get("translation_vi", "Chào bạn! Ngày hôm nay của bạn thế nào rồi? Rất vui được thoải mái trò chuyện cùng bạn!")

        if not result.get("suggested_replies") or not isinstance(result["suggested_replies"], list) or len(result["suggested_replies"]) == 0:
            offline = get_topic_offline_opener(topic, "zh")
            result["suggested_replies"] = offline.get("suggested_replies", [])

    return result

def extract_json(raw_text: str) -> dict:
    """Trích xuất và giải mã JSON an toàn tuyệt đối từ chuỗi phản hồi LLM."""
    raw_text = (raw_text or "").strip()
    try:
        return json.loads(raw_text)
    except Exception:
        pass

    # Loại bỏ code block markdown ```json ... ```
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw_text, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Ghép ngoặc nhọn JSON (Bracket matching) bỏ qua rác/bình luận thừa ở sau
    start_idx = raw_text.find('{')
    if start_idx != -1:
        brace_count = 0
        in_string = False
        escape = False
        for i in range(start_idx, len(raw_text)):
            c = raw_text[i]
            if c == '"' and not escape:
                in_string = not in_string
            elif not in_string:
                if c == '{':
                    brace_count += 1
                elif c == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        try:
                            return json.loads(raw_text[start_idx:i+1])
                        except Exception:
                            pass
            if c == '\\' and not escape:
                escape = True
            else:
                escape = False

    raise ValueError(f"Không thể phân tích cú pháp JSON từ dữ liệu: {raw_text[:200]}")

def call_gemini_api(api_key: str, history: list, system_instruction: str = "", preferred_model: str = "gemini-3-flash-preview") -> str:
    """Gọi trực tiếp Google Gemini API qua REST v1beta với model tối ưu tốc độ phản hồi."""
    candidate_models = [
        "gemini-3-flash-preview",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-flash-latest",
        "gemini-3.5-flash",
        "gemini-flash-lite-latest"
    ]
    models_to_try = [preferred_model] + [m for m in candidate_models if m != preferred_model]
    headers = {"Content-Type": "application/json"}

    contents = []
    for item in history:
        role = "user" if item.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": item.get("content", "")}]})

    # Đảm bảo cấu trúc hợp lệ theo chuẩn Google Gemini API
    if not contents:
        contents.append({"role": "user", "parts": [{"text": "Hello, please assist me."}]})
    elif contents[0]["role"] == "model":
        contents.insert(0, {"role": "user", "parts": [{"text": "Hello, let's start the session."}]})
    if contents[-1]["role"] == "model":
        contents.append({"role": "user", "parts": [{"text": "Please provide your response in the requested JSON format."}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.75,
            "responseMimeType": "application/json"
        }
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    last_err = ""
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=8)
            data = res.json()
            if res.status_code == 200 and "candidates" in data:
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return raw_text
            else:
                last_err = data.get("error", {}).get("message", res.text)
        except Exception as e:
            last_err = str(e)
            continue

    raise RuntimeError(f"Gemini API không phản hồi: {last_err}")

def process_tutor_chat(api_key: str, user_text: str, lang: str, scenario_id: str, history: list = None, turn_count: int = 1, preferred_model: str = "gemini-3-flash-preview"):
    """
    Xử lý phản hồi gia sư AI cho cả Tiếng Anh và Tiếng Trung, kèm hệ thống gợi ý cực kỳ linh động và chuẩn xác.
    """
    # Khử trùng lặp và làm sạch lịch sử hội thoại
    clean_history = []
    for item in (history or []):
        r = "user" if item.get("role") == "user" else "model"
        c = item.get("content", "").strip()
        if c:
            clean_history.append({"role": r, "content": c})

    # Chỉ thêm user_text nếu câu cuối cùng trong clean_history chưa phải là chính user_text đó
    if not clean_history or clean_history[-1].get("role") != "user" or clean_history[-1].get("content") != user_text:
        clean_history.append({"role": "user", "content": user_text})

    if not api_key:
        return get_dynamic_offline_response(user_text, lang, scenario_id, turn_count, history=clean_history)

    scenario_info = next((s for s in SCENARIOS.get(lang, []) if s["id"] == scenario_id), None)
    scenario_title = scenario_info.get("title", "") if scenario_info else scenario_id
    if not scenario_title or scenario_title in ["free", "free_chat", "free_zh"]:
        scenario_title = "日常随心闲聊 (Casual Daily Talk)" if lang == "zh" else "Casual Daily Talk (Trò chuyện tự do)"
    bot_role = scenario_info.get("botRole", "Người bạn bản xứ vui vẻ, thông minh") if scenario_info else "Người bạn bản xứ"

    if lang == "zh":
        system_inst = f"""你是一位热情、地道、幽默的中国母语中文语伴（北京标准普通话口音）。
BỐI CẢNH ĐANG ĐÓNG VAI:
- Chủ đề: {scenario_title}
- Vai của bạn: {bot_role}

NHIỆM VỤ CỦA BẠN:
1. Trả lời người học thật tự nhiên, chuẩn mực, gần gũi (1-2 câu).
2. QUY TẮC BẮT BUỘC ĐỂ DUY TRÌ HỘI THOẠI:
   - Ở cuối câu trả lời ('reply_hanzi'), bạn BẮT BUỘC phải đặt ra 1 câu hỏi tiếp nối tự nhiên hoặc 1 lời gợi mở thân thiện để người học trả lời.
3. QUY TẮC TẠO GỢI Ý ĐÀM THOẠI (suggested_replies):
   - CỰC KỲ QUAN TRỌNG: 3 câu gợi ý này là những câu mà NGƯỜI HỌC sẽ dùng để trả lời lại CHÍNH XÁC câu hỏi/lời gợi mở bạn vừa đặt ra ở cuối 'reply_hanzi'.
   - TUYỆT ĐỐI KHÔNG đưa ra gợi ý lạc đề, máy móc hoặc của tình huống không liên quan.
   - 3 câu gợi ý phải phong phú, tự nhiên và đại diện cho 3 hướng trả lời thực tế khác nhau:
     + Gợi ý 1: Trả lời trực tiếp, hào hứng kèm chi tiết/lý do cụ thể.
     + Gợi ý 2: Trả lời theo hướng lựa chọn khác / trải nghiệm hoặc sở thích khác biệt.
     + Gợi ý 3: Hỏi ngược lại ý kiến của bạn hoặc xin bạn gợi ý/lời khuyên.
   - Định dạng mỗi câu: "Chữ Hán (Pinyin có thanh điệu - Dịch nghĩa tiếng Việt tự nhiên)"
4. Xuất JSON hợp lệ:
   - "reply_hanzi": Câu tiếng Trung kết thúc bằng câu hỏi tiếp nối (chữ Hán Giản thể).
   - "reply_pinyin": Phiên âm Pinyin kèm thanh điệu đầy đủ.
   - "translation_vi": Dịch nghĩa tiếng Việt tự nhiên.
   - "feedback": Lời nhận xét ngắn gọn, khích lệ hoặc lưu ý ngữ pháp/phát âm bằng tiếng Việt.
   - "suggested_replies": Mảng 3 chuỗi theo định dạng trên.
"""
    else:
        system_inst = f"""You are an engaging, warm, native English language conversation coach.
ROLEPLAY CONTEXT:
- Scenario: {scenario_title}
- Your Role: {bot_role}

YOUR TASKS:
1. Respond naturally staying in character as {bot_role} in the scenario: {scenario_title}. Keep responses conversational and concise (1-2 sentences).
2. MANDATORY CONVERSATION RULE:
   - You MUST ALWAYS conclude your reply ('reply') with a natural, engaging open-ended question or prompt so the learner has a clear cue to reply to.
3. CRITICAL FOR SUGGESTED REPLIES (suggested_replies):
   - CRITICAL: These 3 suggestions are what THE LEARNER will say to answer the exact question/prompt you just asked at the end of your 'reply'.
   - Suggestions MUST MATCH the conversation context 100%. Never output suggestions from another topic or unrelated phrases.
   - The 3 options must cover 3 realistic, distinct conversational directions:
     + Option 1: Direct personal answer sharing enthusiastic specific details.
     + Option 2: An alternative perspective, different preference, or different experience.
     + Option 3: A friendly counter-question or asking your recommendation/opinion back.
   - EACH suggestion MUST STRICTLY follow this 3-part format: "English sentence (/IPA phonetic transcription/ - Bản dịch tiếng Việt tự nhiên)"
4. Output strictly valid JSON:
   - "reply": Natural English response ending with an engaging question.
   - "reply_ipa": International Phonetic Alphabet (IPA) transcription of your reply enclosed in slashes, e.g. "/.../".
   - "translation_vi": Natural Vietnamese translation of your reply.
   - "feedback": Brief helpful tip or encouraging note in Vietnamese.
   - "suggested_replies": Array of 3 strings in the exact format "English sentence (/IPA/ - Bản dịch tiếng Việt)".
"""

    try:
        raw_res = call_gemini_api(api_key, clean_history, system_inst, preferred_model=preferred_model)
        parsed = extract_json(raw_res)
        return sanitize_ai_result(parsed, lang, scenario_id)
    except Exception as e:
        logger.warning(f"Gemini API không phản hồi ({e}), chuyển sang động cơ mô phỏng ngữ cảnh linh động.")
        return get_dynamic_offline_response(user_text, lang, scenario_id, turn_count, history=clean_history, error_note=str(e))

def generate_fresh_suggestions(api_key: str, lang: str, scenario_id: str, history: list = None, preferred_model: str = "gemini-3-flash-preview") -> list:
    """Tạo 3 câu gợi ý mới toanh khớp 100% với câu nói gần nhất của gia sư."""
    scenario_info = next((s for s in SCENARIOS.get(lang, []) if s["id"] == scenario_id), None)
    scenario_title = scenario_info.get("title", "") if scenario_info else scenario_id
    if not scenario_title or scenario_title in ["free", "free_chat", "free_zh"]:
        scenario_title = "日常随心闲聊 (Casual Daily Talk)" if lang == "zh" else "Casual Daily Talk (Trò chuyện tự do)"
    bot_role = scenario_info.get("botRole", "Người bạn bản xứ") if scenario_info else "Đối tác"

    last_bot_msg = ""
    for item in reversed(history or []):
        if item.get("role") in ["assistant", "model"]:
            last_bot_msg = item.get("content", "").strip()
            break
    if not last_bot_msg and scenario_info:
        last_bot_msg = scenario_info.get("initialHanzi" if lang == "zh" else "initialMessage", "")

    if api_key and last_bot_msg:
        try:
            if lang == "zh":
                prompt_text = f"""Bối cảnh giao tiếp: {scenario_title} (bạn là: {bot_role}).
Gia sư vừa nói với người học câu này:
"{last_bot_msg}"

YÊU CẦU:
Hãy tạo 3 câu gợi ý phản hồi HOÀN TOÀN MỚI, KHÁC BIỆT, tự nhiên để người học trả lời lại CHÍNH XÁC câu nói/câu hỏi trên của gia sư:
- Gợi ý 1: Trả lời trực tiếp, hào hứng kèm chi tiết cụ thể.
- Gợi ý 2: Câu trả lời mang tính lựa chọn khác / trải nghiệm hoặc góc nhìn khác.
- Gợi ý 3: Hỏi ngược lại ý kiến hoặc xin lời khuyên từ gia sư.
Mỗi câu có dạng: "Chữ Hán (Pinyin có thanh điệu - Nghĩa tiếng Việt)".
Xuất duy nhất JSON: {{"suggested_replies": ["...", "...", "..."]}}"""
            else:
                prompt_text = f"""Conversation scenario: {scenario_title} (your role: {bot_role}).
The tutor just said/asked the learner:
"{last_bot_msg}"

TASK:
Provide 3 completely FRESH, DIVERSE, and natural responses the learner can say to directly answer what the tutor just said/asked:
- Option 1: Direct personal answer sharing enthusiastic specific details.
- Option 2: An alternative perspective, different preference, or different experience.
- Option 3: A counter-question or asking the tutor's advice/opinion back.
Each suggestion MUST follow the 3-part format: "English sentence (/IPA phonetic transcription/ - Bản dịch tiếng Việt tự nhiên)"
Output strictly JSON: {{"suggested_replies": ["...", "...", "..."]}}"""

            single_turn_history = [{"role": "user", "content": prompt_text}]
            raw_res = call_gemini_api(api_key, single_turn_history, preferred_model=preferred_model)
            parsed = extract_json(raw_res)
            if "suggested_replies" in parsed and isinstance(parsed["suggested_replies"], list) and len(parsed["suggested_replies"]) > 0:
                return parsed["suggested_replies"]
        except Exception as e:
            logger.warning(f"Không thể tạo gợi ý mới qua Gemini: {e}")

    # Fallback ngoại tuyến thông minh theo chủ đề
    offline = get_dynamic_offline_response(last_bot_msg or "đổi gợi ý", lang, scenario_id, random.randint(1, 10), history=history)
    return offline.get("suggested_replies", [])

# ==============================================================================
# HỆ THỐNG ĐỘNG CƠ GỢI Ý & PHẢN HỒI NỘI HÀM CỰC KỲ LINH ĐỘNG (OFFLINE ENGINE)
# TÍCH HỢP XOAY VÒNG CHỦ ĐỀ & CƠ CHẾ CHỐNG LẶP HỘI THOẠI TUYỆT ĐỐI (ANTI-LOOP)
# ==============================================================================

DEFAULT_CHINESE_TURNS = [
    {
        "reply_hanzi": "哈哈，聊得太开心了！除了这个，你平时有什么特别感兴趣的爱好吗？",
        "reply_pinyin": "Hāhā, liáo de tài kāixīn le! Chúle zhège, nǐ píngshí yǒu shénme tèbié gǎnxìngqù de àihào ma?",
        "translation_vi": "Haha, trò chuyện cùng bạn vui quá! Ngoài điều này ra, bình thường bạn có sở thích nào đặc biệt đam mê không?",
        "feedback": "Bạn đang giao tiếp rất tự nhiên và trôi chảy!",
        "suggested_replies": [
            "我平时很喜欢听音乐和跑步，能让人心情舒畅 (Wǒ píngshí hěn xǐhuan tīng yīnyuè hé pǎobù, néng ràng rén xīnqíng shūchàng - Bình thường tôi rất thích nghe nhạc và chạy bộ, giúp tâm trạng thư thái)",
            "我挺喜欢摄影的，周末常去扫街拍照 (Wǒ tǐng xǐhuan shèyǐng de, zhōumò cháng qù sǎojiē pāizhào - Tôi khá thích nhiếp ảnh, cuối tuần hay đi dạo phố chụp ảnh)",
            "你有什么好玩的爱好可以推荐给我吗？ (Nǐ yǒu shénme hǎowán de àihào kěyǐ tuījiàn gěi wǒ ma? - Bạn có sở thích nào thú vị gợi ý cho tôi không?)"
        ]
    },
    {
        "reply_hanzi": "忙碌了一整天，下班或者学习之余，你一般最喜欢做什么来给自己彻底充充电、放松身心？",
        "reply_pinyin": "Mánglù le yì zhěng tiān, xiàbān huòzhě xuéxí zhīyú, nǐ yìbān zuì xǐhuan zuò shénme lái gěi zìjǐ chèdǐ chōngchōng diàn, fàngsōng shēnxīn?",
        "translation_vi": "Bận rộn cả ngày dài, sau giờ làm hay giờ học, bạn thường thích làm gì nhất để nạp lại năng lượng và thả lỏng đầu óc?",
        "feedback": "Chia sẻ về thói quen thư giãn buổi tối giúp câu chuyện thêm gần gũi và ấm áp.",
        "suggested_replies": [
            "我喜欢泡一杯热茶，静静地看会儿书 (Wǒ xǐhuan pào yì bēi rèchá, jìngjìng de kànhuǐr shū - Tôi thích pha một tách trà nóng, thong thả đọc chút sách)",
            "我一般会戴上耳机听听舒缓的歌，或者出门散步 (Wǒ yìbān huì dàishang ěrjī tīngting shūhuǎn de gē, huòzhě chūmén sànbù - Tôi thường đeo tai nghe nghe nhạc nhẹ, hoặc ra ngoài đi dạo)",
            "洗个热水澡然后美美地睡一觉，第二天就满血复活了 (Xǐ gè rèshuǐzǎo ránhòu měiměi de shuì yí jiào, dì-èr tiān jiù mǎnxuè fùhuó le - Tắm nước nóng rồi ngủ một giấc thật ngon, hôm sau là tràn đầy năng lượng)"
        ]
    },
    {
        "reply_hanzi": "生活总是需要一些新鲜期待！最近你有没有什么特别想去达成的小目标，或者想去尝试的新事物？",
        "reply_pinyin": "Shēnghuó zǒng shì xūyào yìxiē xīnxiān qīdài! Zuìjìn nǐ yǒu méiyǒu shénme tèbié xiǎng qù dáchéng de xiǎo mùbiāo, huòzhě xiǎng qù chángshì de xīn shìwù?",
        "translation_vi": "Cuộc sống lúc nào cũng cần những mong đợi mới mẻ! Dạo này bạn có mục tiêu nhỏ nào muốn đạt được, hay có điều gì mới muốn thử sức không?",
        "feedback": "Nói về những dự định tương lai thể hiện tinh thần sống tích cực và nhiều năng lượng.",
        "suggested_replies": [
            "我最近在坚持每天练习外语口语，希望能脱口而出 (Wǒ zuìjìn zài jiānchí měitiān liànxí wàiyǔ kǒuyǔ, xīwàng néng tuōkǒu ér chū - Dạo này tôi kiên trì luyện nói ngoại ngữ mỗi ngày, mong có thể nói tự nhiên lưu loát)",
            "我想学习一门新的技能，比如做烘焙或者剪辑视频 (Wǒ xiǎng xuéxí yì mén xīn de jìnéng, bǐrú zuò hōngbèi huòzhě jiǎnjí shìpín - Tôi muốn học thêm kỹ năng mới, như làm bánh hoặc dựng video)",
            "我正计划一次短途旅行，去看看不一样的风景 (Wǒ zhèng jìhuà yí cì duǎntú lǚxíng, qù kànkan bù yíyàng de fēngjǐng - Tôi đang lên lịch cho một chuyến du lịch ngắn ngày để ngắm phong cảnh mới)"
        ]
    },
    {
        "reply_hanzi": "有时候一首动听的歌能治愈一整天的心情。你最近有经常单曲循环的歌曲吗？能跟我聊聊它带给你的感觉吗？",
        "reply_pinyin": "Yǒushíhou yì shǒu dòngtīng de gē néng zhìyù yì zhěng tiān de xīnqíng. Nǐ zuìjìn yǒu chángcháng dānqǔ xúnhuán de gēqǔ ma? Néng gēn wǒ liáoliao tā dài gěi nǐ de gǎnjué ma?",
        "translation_vi": "Đôi khi một bài hát hay có thể xoa dịu tâm trạng cả ngày. Dạo này bạn có bài hát nào nghe đi nghe lại không? Có thể chia sẻ cảm xúc mà bài hát mang lại cho bạn không?",
        "feedback": "Âm nhạc là ngôn ngữ không biên giới, rất thích hợp để tâm sự cảm xúc.",
        "suggested_replies": [
            "我最近特别喜欢一首旋律温柔的民谣，听着心里很平静 (Wǒ zuìjìn tèbié xǐhuan yì shǒu xuánlǜ wēnróu de mínyáo, tīngzhe xīn lǐ hěn píngjìng - Dạo này tôi rất thích một bài dân ca giai điệu êm dịu, nghe thấy lòng rất bình yên)",
            "我喜欢节奏明快的流行歌，能让人瞬间充满干劲 (Wǒ xǐhuan jiézòu míngkuài de liúxínggē, néng ràng rén shùnjiān chōngmǎn gànjìn - Tôi thích nhạc pop sôi động, nghe là lập tức có thêm động lực)",
            "我平时各种风格都听一点，你有什么珍藏的好歌推荐吗？ (Wǒ píngshí gè zhǒng fēnggé dōu tīng yìdiǎn, nǐ yǒu shénme zhēncáng de hǎogē tuījiàn ma? - Tôi nhạc gì cũng nghe một chút, bạn có bài hát tủ nào hay giới thiệu cho tôi không?)"
        ]
    },
    {
        "reply_hanzi": "如果给你一整天完全自由的时间，不用考虑任何工作和琐事，你最想怎么度过这美好的一天？",
        "reply_pinyin": "Rúguǒ gěi nǐ yì zhěng tiān wánquán zìyóu de shíjiān, bú yòng kǎolǜ rènhé gōngzuò hé suǒshì, nǐ zuì xiǎng zěnme dùguò zhè měihǎo de yì tiān?",
        "translation_vi": "Nếu cho bạn trọn vẹn một ngày hoàn toàn tự do, không phải vướng bận công việc hay sự đời, bạn muốn trải qua ngày tuyệt vời đó như thế nào nhất?",
        "feedback": "Cấu trúc giả định 'Nếu... thì...' (如果...就...) là một mẫu câu rất hay để thực hành phản xạ nói.",
        "suggested_replies": [
            "我会在大自然里徒步一整天，呼吸新鲜空气 (Wǒ huì zài dàzìrán lǐ túbù yì zhěng tiān, hūxī xīnxiān kōngqì - Tôi sẽ đi bộ dã ngoại giữa thiên nhiên cả ngày, hít thở không khí trong lành)",
            "我会找一家安静舒适的咖啡馆，坐着发呆或者看书 (Wǒ huì zhǎo yì jiā ānjìng shūshì de kāfēiguǎn, zuòzhe fādāi huòzhě kànshū - Tôi sẽ tìm một quán cà phê yên tĩnh, ngồi ngắm phố hoặc đọc sách)",
            "睡到自然醒，吃一顿丰盛的早午餐，然后随心漫步 (Shuì dào zìrán xǐng, chī yí dùn fēngshèng de zǎowǔcān, ránhòu suíxīn mànbù - Ngủ đẫy giấc tự nhiên tỉnh, ăn một bữa brunch thịnh soạn rồi thong thả dạo phố)"
        ]
    },
    {
        "reply_hanzi": "俗话说‘民以食为天’，美食总能带给人满满的幸福感！你平时最怀念的一道家常滋味是什么？",
        "reply_pinyin": "Súhuà shuō ‘mín yǐ shí wéi tiān’, měishí zǒng néng dài gěi rén mǎnmǎn de xìngfúgǎn! Nǐ píngshí zuì huáiniàn de yí dào jiācháng zīwèi shì shénme?",
        "translation_vi": "Tục ngữ có câu 'Dân dĩ thực vi thiên' (Ăn uống là điều hệ trọng nhất), món ăn ngon lúc nào cũng mang lại cảm giác hạnh phúc ngập tràn! Vị cơm nhà mà bạn nhớ nhất là món gì?",
        "feedback": "Ẩm thực gia đình luôn gợi nhiều cảm xúc thân thương và vốn từ phong phú.",
        "suggested_replies": [
            "我最想念妈妈亲手做的拿手菜，永远吃不腻 (Wǒ zuì xiǎngniàn māma qīnshǒu zuò de náshǒucài, yǒngyuǎn chī bú nì - Tôi nhớ nhất món tủ do chính tay mẹ nấu, ăn hoài không bao giờ ngán)",
            "我最喜欢街头巷尾那些地道的小吃，烟火气十足 (Wǒ zuì xǐhuan jiētóu xiàngwěi nàxiē dìdao de xiǎochī, yānhuǒqì shízú - Tôi thích những món ăn vặt đường phố dân dã, đậm đà phong vị đời sống)",
            "我周末喜欢自己研究新菜谱，做给家人朋友尝 (Wǒ zhōumò xǐhuan zìjǐ yánjiū xīn càipǔ, zuò gěi jiārén péngyou cháng - Cuối tuần tôi thích tự mày mò công thức món mới nấu cho người thân bạn bè thưởng thức)"
        ]
    }
]

DEFAULT_ENGLISH_TURNS = [
    {
        "reply": "That's awesome! Aside from that, what kind of hobbies or activities do you enjoy most in your free time?",
        "reply_ipa": "/ðæts ˈɔːsəm! əˈsaɪd frʌm ðæt, wʌt kaɪnd əv ˈhɑːbiz ɔːr ækˈtɪvətiz duː juː ɪnˈdʒɔɪ moʊst ɪn jʊər friː taɪm?/",
        "translation_vi": "Tuyệt quá! Ngoài điều đó ra, bạn thích những sở thích hay hoạt động nào nhất vào thời gian rảnh rỗi?",
        "feedback": "Keep it up! Your conversational rhythm is getting smoother and more natural with every turn.",
        "suggested_replies": [
            "I really enjoy listening to music and taking long evening walks. (/aɪ ˈriːəli ɪnˈdʒɔɪ ˈlɪsnɪŋ tuː ˈmjuːzɪk ænd ˈteɪkɪŋ lɔːŋ ˈiːvnɪŋ wɔːks/ - Tôi rất thích nghe nhạc và đi dạo buổi tối.)",
            "I love reading inspirational books and learning new skills online. (/aɪ lʌv ˈriːdɪŋ ˌɪnspəˈreɪʃənl bʊks ænd ˈlɜːrnɪŋ nuː skɪlz ˌɑːnˈlaɪn/ - Tôi thích đọc sách truyền cảm hứng và học các kỹ năng mới trên mạng.)",
            "What about you? What are your favorite pastimes outside of work? (/wʌt əˈbaʊt juː? wʌt ɑːr jʊər ˈfeɪvərɪt ˈpæstaɪmz ˌaʊtˈsaɪd əv wɜːrk? - Còn bạn thì sao? Thú vui tiêu khiển bạn thích nhất ngoài giờ làm việc là gì?)"
        ]
    },
    {
        "reply": "After a productive or busy day, what is your absolute favorite way to unwind and recharge your energy?",
        "reply_ipa": "/ˈæftər ə prəˈdʌktɪv ɔːr ˈbɪzi deɪ, wʌt ɪz jʊər ˈæbsəluːt ˈfeɪvərɪt weɪ tuː ʌnˈwaɪnd ænd ˌriːˈtʃɑːrdʒ jʊər ˈenərdʒi?/",
        "translation_vi": "Sau một ngày làm việc hiệu quả hay bận rộn, cách bạn thích nhất để xả hơi và sạc lại năng lượng là gì?",
        "feedback": "Talking about evening decompression routines shows authentic, reflective language.",
        "suggested_replies": [
            "I love brewing a warm cup of herbal tea and reading quietly. (/aɪ lʌv ˈbruːɪŋ ə wɔːrm kʌp əv ˈɜːrbl tiː ænd ˈriːdɪŋ ˈkwaɪətli/ - Tôi thích pha một tách trà thảo mộc ấm và đọc sách trong yên tĩnh.)",
            "Putting on my headphones with chill music always recharges me. (/ˈpʊtɪŋ ɑːn maɪ ˈhedfoʊnz wɪð tʃɪl ˈmjuːzɪk ˈɔːlweɪz ˌriːˈtʃɑːrdʒɪz miː/ - Đeo tai nghe nghe nhạc êm dịu lúc nào cũng giúp tôi hồi phục năng lượng.)",
            "A hot shower followed by a deep restful sleep does wonders for me. (/ə hɑːt ˈʃaʊər ˈfɑːloʊd baɪ ə diːp ˈrestfl sliːp dʌz ˈwʌndərz fər miː/ - Tắm nước nóng rồi ngủ một giấc thật sâu giúp tôi sảng khoái hẳn.)"
        ]
    },
    {
        "reply": "Life is always more exciting with new goals! Is there any fresh skill or new activity you've been wanting to try lately?",
        "reply_ipa": "/laɪf ɪz ˈɔːlweɪz mɔːr ɪkˈsaɪtɪŋ wɪð nuː ɡoʊlz! ɪz ðɛr ˈɛni freʃ skɪl ɔːr nuː ækˈtɪvəti juːv biːn ˈwɑːntɪŋ tuː traɪ ˈleɪtli?/",
        "translation_vi": "Cuộc sống lúc nào cũng hào hứng hơn khi có những mục tiêu mới! Dạo này có kỹ năng mới hay hoạt động nào bạn đang ấp ủ muốn thử không?",
        "feedback": "Using 'have been wanting to...' is a great way to express ongoing aspirations.",
        "suggested_replies": [
            "I'm practicing daily English speaking to boost my natural fluency. (/aɪm ˈpræktɪsɪŋ ˈdeɪli ˈɪŋɡlɪʃ ˈspiːkɪŋ tuː buːst maɪ ˈnætʃrəl ˈfluːənsi/ - Tôi đang luyện nói tiếng Anh mỗi ngày để tăng độ trôi chảy tự nhiên.)",
            "I really want to pick up video editing and photography this year. (/aɪ ˈriːəli wɑːnt tuː pɪk ʌp ˈvɪdioʊ ˈedɪtɪŋ ænd fəˈtɑːɡrəfi ðɪs jɪr/ - Tôi rất muốn học thêm dựng video và nhiếp ảnh trong năm nay.)",
            "I'm hoping to plan an exciting road trip to explore new destinations. (/aɪm ˈhoʊpɪŋ tuː plæn ən ɪkˈsaɪtɪŋ roʊd trɪp tuː ɪkˈsplɔːr nuː ˌdestɪˈneɪʃnz/ - Tôi hy vọng sẽ lên kế hoạch cho một chuyến đi phượt để khám phá những điểm đến mới.)"
        ]
    },
    {
        "reply": "Music has such a magical way of lifting our spirits! Have you had any favorite song playing on repeat lately?",
        "reply_ipa": "/ˈmjuːzɪk hæz sʌtʃ ə ˈmædʒɪkl weɪ əv ˈlɪftɪŋ ˈaʊər ˈspɪrɪts! hæv juː hæd ˈɛni ˈfeɪvərɪt sɔːŋ ˈpleɪɪŋ ɑːn rɪˈpiːt ˈleɪtli?/",
        "translation_vi": "Âm nhạc có cách kỳ diệu để nâng cao tinh thần! Dạo này bạn có bài hát yêu thích nào đang bật nghe đi nghe lại không?",
        "feedback": "Music discussions bring out descriptive adjectives and personal storytelling.",
        "suggested_replies": [
            "I've been playing an acoustic indie folk song that feels so calming. (/aɪv biːn ˈpleɪɪŋ ən əˈkuːstɪk ˈɪndi foʊk sɔːŋ ðæt fiːlz soʊ ˈkɑːmɪŋ/ - Tôi đang nghe đi nghe lại một bài indie folk mộc mạc mang lại cảm giác rất thanh bình.)",
            "I love upbeat pop hits that instantly get me energized for the day. (/aɪ lʌv ˌʌpˈbiːt pɑːp hɪts ðæt ˈɪnstəntli ɡet miː ˈenərdʒaɪzd fər ðə deɪ/ - Tôi thích các bài pop sôi động giúp tôi lập tức tràn đầy năng lượng cho ngày mới.)",
            "My music taste is pretty eclectic, do you have any good recommendations? (/maɪ ˈmjuːzɪk teɪst ɪz ˈprɪti ɪˈklektɪk, duː juː hæv ˈɛni ɡʊd ˌrekəmenˈdeɪʃnz? - Gu âm nhạc của tôi khá đa dạng, bạn có bài nào hay gợi ý cho tôi không?)"
        ]
    },
    {
        "reply": "If you had an entire day completely free with zero work or obligations, how would you spend it from morning till night?",
        "reply_ipa": "/ɪf juː hæd ən ɪnˈtaɪər deɪ kəmˈpliːtli friː wɪð ˈzɪroʊ wɜːrk ɔːr ˌɑːblɪˈɡeɪʃnz, haʊ wʊd juː spend ɪt frʌm ˈmɔːrnɪŋ tɪl naɪt?/",
        "translation_vi": "Nếu bạn có một ngày trọn vẹn hoàn toàn tự do không công việc hay vướng bận gì, bạn sẽ tận hưởng ngày đó từ sáng tới tối như thế nào?",
        "feedback": "Hypothetical conditional sentences (If you had... would you...) are essential for expressive fluency.",
        "suggested_replies": [
            "I would spend the whole day outdoors hiking in lush nature. (/aɪ wʊd spend ðə hoʊl deɪ ˌaʊtˈdɔːrz ˈhaɪkɪŋ ɪn lʌʃ ˈneɪtʃər/ - Tôi sẽ dành trọn ngày ở ngoài trời đi bộ leo núi giữa thiên nhiên xanh ngát.)",
            "I'd sit in a cozy aesthetic cafe with a great book and delicious coffee. (/aɪd sɪt ɪn ə ˈkoʊzi esˈθetɪk kæˈfeɪ wɪð ə ɡreɪt bʊk ænd dɪˈlɪʃəs ˈkɔːfi/ - Tôi sẽ ngồi trong một quán cà phê xinh xắn với một cuốn sách hay và ly cà phê thơm ngon.)",
            "Sleep in with no alarm, enjoy a brunch feast, and wander freely. (/sliːp ɪn wɪð noʊ əˈlɑːrm, ɪnˈdʒɔɪ ə brʌntʃ fiːst, ænd ˈwɑːndər ˈfriːli/ - Ngủ nướng không cần chuông báo thức, thưởng thức bữa brunch thịnh soạn và thong thả dạo phố.)"
        ]
    },
    {
        "reply": "They say comfort food brings the purest happiness! What's your absolute favorite home-cooked dish that you never get tired of?",
        "reply_ipa": "/ðeɪ seɪ ˈkʌmfərt fuːd brɪŋz ðə ˈpjʊrɪst ˈhæpinəs! wʌts jʊər ˈæbsəluːt ˈfeɪvərɪt ˈhoʊmkʊkt dɪʃ ðæt juː ˈnevər ɡet ˈtaɪərd əv?/",
        "translation_vi": "Người ta nói những món ăn ấm cúng đem lại niềm hạnh phúc thuần khiết nhất! Món cơm nhà ruột mà bạn không bao giờ ăn ngán là món gì?",
        "feedback": "Talking about food comfort memories connects language directly to personal warmth.",
        "suggested_replies": [
            "Nothing can ever beat my mom's signature home cooking. (/ˈnʌθɪŋ kæn ˈevər biːt maɪ mɑːmz ˈsɪɡnətʃər hoʊm ˈkʊkɪŋ/ - Không gì có thể sánh được với những món cơm nhà do chính tay mẹ nấu.)",
            "I love exploring authentic street delicacies with rich cultural flavors. (/aɪ lʌv ɪkˈsplɔːrɪŋ ɔːˈθentɪk striːt ˈdelɪkəsiz wɪð rɪtʃ ˈkʌltʃərəl ˈfleɪvərz/ - Tôi mê khám phá những món ẩm thực đường phố dân dã đậm đà bản sắc.)",
            "I really enjoy experimenting with new home recipes on weekends. (/aɪ ˈriːəli ɪnˈdʒɔɪ ɪkˌsperɪˈmentɪŋ wɪð nuː hoʊm ˈresəpiz ɑːn ˈwiːkendz/ - Tôi rất thích tự tay mày mò các công thức nấu ăn mới vào dịp cuối tuần.)"
        ]
    }
]

def get_dynamic_offline_response(user_text: str, lang: str, scenario_id: str, turn_count: int = 1, history: list = None, error_note: str = None):
    text_lower = user_text.lower().strip()
    scenario_lower = (scenario_id or "").lower().strip()
    search_context = f"{text_lower} {scenario_lower}"

    if lang == "zh":
        return _resolve_chinese_dynamic(search_context, scenario_id, turn_count, history)
    else:
        return _resolve_english_dynamic(search_context, scenario_id, turn_count, history)

def _resolve_chinese_dynamic(text: str, scenario: str, turn: int, history: list = None):
    # Lấy tập hợp các câu phản hồi trước đó của trợ lý để chống lặp tuyệt đối
    past_replies = set()
    for item in (history or []):
        if item.get("role") in ["assistant", "model"]:
            c = item.get("content", "").strip()
            if c:
                past_replies.add(c)

    def is_new(item):
        return item and item.get("reply_hanzi") not in past_replies

    # 1. Cà phê & Quán xá
    if any(k in text for k in ["咖啡", "kāfēi", "cafe", "coffee", "拿铁", "美式", "手冲", "奶茶", "cà phê", "quán xá", "uống trà"]):
        cand = {
            "reply_hanzi": "聊到喝咖啡，我每天早上都得来一杯提提神！你平时更喜欢美式、拿铁还是手冲？有常去的咖啡馆吗？",
            "reply_pinyin": "Liáo dào hē kāfēi, wǒ měitiān zǎoshang dōu děi lái yì bēi títi shén! Nǐ píngshí gèng xǐhuan měishì, nátiě háishì shǒuchōng? Yǒu cháng qù de kāfēiguǎn ma?",
            "translation_vi": "Nhắc đến cà phê, sáng nào tôi cũng phải làm một ly cho tỉnh táo! Bạn hay uống Americano, Latte hay Pour-over? Có quán ruột nào hay ghé không?",
            "feedback": "Chủ đề cà phê rất gần gũi! Bạn có thể trả lời bằng việc kể loại cà phê yêu thích của mình.",
            "suggested_replies": [
                "我更喜欢喝冰美式，比较清爽无负担 (Wǒ gèng xǐhuan hē bīng měishì, bǐjiào qīngshuǎng wú fùdān - Tôi thích Americano đá hơn, thanh nhẹ không béo)",
                "我每天必喝热拿铁，奶香味特别浓 (Wǒ měitiān bì hē rè nátiě, nǎi xiāngwèi tèbié nóng - Ngày nào tôi cũng uống Latte nóng, thơm đậm vị sữa)",
                "我平时不太喝咖啡，更喜欢喝奶茶或水果茶 (Wǒ píngshí bú tài hē kāfēi, gèng xǐhuan hē nǎichá huò shuǐguǒchá - Bình thường tôi ít uống cà phê, thích trà sữa hoặc trà hoa quả hơn)"
            ]
        }
        if is_new(cand): return cand

    # 2. Ẩm thực & Món ngon
    elif any(k in text for k in ["美食", "菜", "饭", "火锅", "好吃", "美味", "food", "cooking", "ẩm thực", "món ngon", "ăn", "nấu"]):
        cand = {
            "reply_hanzi": "聊到好吃的我可就不困了！你最喜欢哪一种菜系？有没有什么百吃不厌的招牌家常菜？",
            "reply_pinyin": "Liáo dào hǎochī de wǒ kě jiù bú kùn le! Nǐ zuì xǐhuan nǎ yì zhǒng càixì? Yǒu méiyǒu shénme bǎi chī bú yàn de zhāopai jiāchángcài?",
            "translation_vi": "Nói đến đồ ăn ngon là tôi tỉnh cả ngủ! Bạn thích ẩm thực phong cách nào nhất? Có món cơm nhà nào ăn hoài không chán không?",
            "feedback": "Nói về đồ ăn rất dễ mở rộng câu chuyện. Hãy miêu tả vị ngon nhé!",
            "suggested_replies": [
                "我特别喜欢吃火锅，又麻又辣特别过瘾 (Wǒ tèbié xǐhuan chī huǒguō, yòu má yòu là tèbié guòyǐn - Tôi mê ăn lẩu cay tê, ăn cực kỳ đã)",
                "我最喜欢越南牛肉粉和春卷，汤头特别鲜 (Wǒ zuì xǐhuan Yuènán niúròufěn hé chūnjuǎn, tāngtóu tèbié xiān - Tôi thích nhất phở bò và nem rán Việt Nam, nước dùng thanh ngọt)",
                "我平时喜欢自己在家做饭，既健康又省钱 (Wǒ píngshí xǐhuan zìjǐ zài jiā zuòfàn, jì jiànkāng yòu shěngqián - Tôi hay tự nấu ăn ở nhà, vừa sạch lại tiết kiệm)"
            ]
        }
        if is_new(cand): return cand

    # 3. Du lịch & Khám phá
    elif any(k in text for k in ["旅游", "度假", "旅行", "去过", "travel", "trip", "du lịch", "khám phá", "phượt"]):
        cand = {
            "reply_hanzi": "旅行总能让人心情变好！你至今去过最难忘的地方是哪里？接下来最想去哪儿玩？",
            "reply_pinyin": "Lǚxíng zǒng néng ràng rén xīnqíng biàn hǎo! Nǐ zhìjīn qù guo zuì nánwàng de dìfang shì nǎlǐ? Jiēxiàlai zuì xiǎng qù nǎr wán?",
            "translation_vi": "Đi du lịch lúc nào cũng làm tâm trạng phấn chấn! Nơi đáng nhớ nhất bạn từng đi là đâu? Sắp tới muốn đi đâu nhất?",
            "feedback": "Hãy chia sẻ về cảnh đẹp hoặc kỷ niệm một chuyến đi của bạn.",
            "suggested_replies": [
                "我最难忘的是去北京看长城和故宫，非常震撼 (Wǒ zuì nánwàng de shì qù Běijīng kàn Chángchéng hé Gùgōng, fēicháng zhènhàn - Đáng nhớ nhất là lần đi Bắc Kinh ngắm Vạn Lý Trường Thành và Cố Cung)",
                "我更喜欢去海边度假，吹吹海风晒晒太阳 (Wǒ gèng xǐhuan qù hǎibiān dùjià, chuīchui hǎifēng shàishai tàiyáng - Tôi thích đi biển nghỉ dưỡng, hóng gió và tắm nắng hơn)",
                "我打算今年休年假的时候出国走走 (Wǒ dǎsuàn jīnnián xiū niánjià de shíhou chūguó zǒuzou - Tôi tính dịp nghỉ phép năm nay sẽ đi du lịch nước ngoài một chuyến)"
            ]
        }
        if is_new(cand): return cand

    # 4. Công việc & Sự nghiệp
    elif any(k in text for k in ["职场", "工作", "上班", "公司", "work", "career", "công việc", "sự nghiệp"]):
        cand = {
            "reply_hanzi": "工作忙碌之余也别忘了放松身心。你平时的工作节奏快吗？工作中最有成就感的事情是什么？",
            "reply_pinyin": "Gōngzuò mánglù zhī yú yě bié wàng le fàngsōng shēnxīn. Nǐ píngshí de gōngzuò jiézòu kuài ma? Gōngzuò zhōng zuì yǒu chéngjiùgǎn de shìqing shì shénme?",
            "translation_vi": "Bận rộn làm việc nhưng cũng đừng quên thư giãn nhé. Nhịp độ công việc của bạn có dồn dập không? Điều gì trong công việc làm bạn thấy có thành tựu nhất?",
            "feedback": "Chia sẻ về công việc giúp mở rộng nhiều từ vựng văn phòng hữu ích.",
            "suggested_replies": [
                "我平时工作挺忙的，不过同事们都特别好相处 (Wǒ píngshí gōngzuò tǐng máng de, búguò tóngshìmen dōu tèbié hǎo xiāngchǔ - Công việc khá bận rộn, nhưng đồng nghiệp rất dễ gần)",
                "我觉得完成一个大项目时的成就感最高 (Wǒ juéde wánchéng yí gè dà xiàngmù shí de chéngjiùgǎn zuì gāo - Tôi thấy lúc hoàn thành một dự án lớn là thỏa mãn nhất)",
                "我目前正在努力平衡工作与个人生活 (Wǒ mùqián zhèngzài nǔlì pínghéng gōngzuò yǔ gèrén shēnghuó - Hiện tôi đang cố gắng cân bằng giữa công việc và đời sống riêng)"
            ]
        }
        if is_new(cand): return cand

    # 5. Phim ảnh & Giải trí
    elif any(k in text for k in ["电影", "追剧", "电视剧", "movie", "cinema", "netflix", "phim", "giải trí"]):
        cand = {
            "reply_hanzi": "看电影追剧真是最棒的消遣了！你最近在追什么好看的电视剧或电影吗？",
            "reply_pinyin": "Kàn diànyǐng zhuījù zhēn shì zuì bàng de xiāoqiǎn le! Nǐ zuìjìn zài zhuī shénme hǎokàn de diànshìjù huò diànyǐng ma?",
            "translation_vi": "Xem phim đúng là cách giải trí tuyệt vời nhất! Dạo này bạn có đang cày bộ phim hay bộ truyền hình nào không?",
            "feedback": "Kể tên các thể loại phim bạn thích như hành động, hài hước hay tình cảm.",
            "suggested_replies": [
                "我特别喜欢科幻片和悬疑悬念电影 (Wǒ tèbié xǐhuan kēhuànpiàn hé xuányí diànyǐng - Tôi cực kỳ thích phim khoa học viễn tưởng và trinh thám ly kỳ)",
                "我最近在看一部轻松搞笑的情景喜剧 (Wǒ zuìjìn zài kàn yí bù qīngsōng gǎoxiào de qíngjǐng xǐjù - Dạo này tôi đang xem một bộ phim sitcom hài hước nhẹ nhàng)",
                "周末我打算约朋友一起去电影院看新上映的大片 (Zhōumò wǒ dǎsuàn yuē péngyou yìqǐ qù diànyǐngyuàn kàn xīn shàngyìng de dàpiàn - Cuối tuần tôi tính hẹn bạn ra rạp xem phim bom tấn mới chiếu)"
            ]
        }
        if is_new(cand): return cand

    # 6. Thời tiết & Đời sống
    elif any(k in text for k in ["天气", "四季", "weather", "thời tiết", "mưa", "nắng", "下雨", "晴天", "冬天", "夏天", "秋天", "春天"]):
        cand = {
            "reply_hanzi": "你那边的天气今天怎么样？是晴天还是下雨？你最喜欢哪一个季节？",
            "reply_pinyin": "Nǐ nàbiān de tiānqì jīntiān zěnmeyàng? Shì qíngtiān háishì xiàyǔ? Nǐ zuì xǐhuan nǎ yí gè jìjié?",
            "translation_vi": "Thời tiết bên bạn hôm nay thế nào? Trời nắng hay mưa? Bạn thích mùa nào nhất trong năm?",
            "feedback": "Thời tiết là câu mở đầu kinh điển trong mọi cuộc trò chuyện thường nhật.",
            "suggested_replies": [
                "今天天气很好，阳光明媚，温度很舒适 (Jīntiān tiānqì hěn hǎo, yángguāng míngmèi, wēndù hěn shūshì - Hôm nay thời tiết rất đẹp, nắng ấm và nhiệt độ dễ chịu)",
                "我最喜欢秋天，天气凉爽，不冷也不热 (Wǒ zuì xǐhuan qiūtiān, tiānqì liángshuǎng, bù lěng yě bú rè - Tôi thích nhất mùa thu, trời mát mẻ không quá lạnh cũng không quá nóng)",
                "这几天一直在下雨，出门有点不太方便 (Zhè jǐ tiān yìzhí zài xiàyǔ, chūmén yǒudiǎn bú tài fāngbiàn - Mấy hôm nay mưa suốt, ra đường hơi bất tiện một chút)"
            ]
        }
        if is_new(cand): return cand

    # 7. Cuối tuần & Thư giãn
    elif any(k in text for k in ["周末", "weekend", "cuối tuần", "xả stress", "kế hoạch"]):
        cand = {
            "reply_hanzi": "又快到周末啦！这个周末你有什么特别的计划吗？打算在家宅着还是出去逛逛？",
            "reply_pinyin": "Yòu kuài dào zhōumò la! Zhège zhōumò nǐ yǒu shénme tèbié de jìhuà ma? Dǎsuàn zài jiā zháizhe háishì chūqù guàngguang?",
            "translation_vi": "Lại sắp đến cuối tuần rồi! Cuối tuần này bạn có kế hoạch đặc biệt gì không? Định ở nhà nghỉ ngơi hay ra ngoài dạo chơi?",
            "feedback": "Chia sẻ về kế hoạch cuối tuần luôn tạo cảm giác háo hức và tích cực.",
            "suggested_replies": [
                "我打算好好睡个懒觉，然后在家里看书追剧 (Wǒ dǎsuàn hǎohǎo shuì gè lǎnjiào, ránhòu zài jiā lǐ kànshū zhuījù - Tôi tính ngủ nướng một giấc đã, rồi ở nhà đọc sách cày phim)",
                "我和朋友约好了一起去郊外野餐露营 (Wǒ hé péngyou yuē hǎo le yìqǐ qù jiāowài yěcān lùyíng - Tôi hẹn bạn bè đi dã ngoại cắm trại ở ngoại ô)",
                "目前还没什么安排，到时候随心而行吧 (Mùqián hái méi shénme ānpái, dào shíhou suíxīn ér xíng ba - Giờ chưa có lịch gì cụ thể, tới lúc đó thích gì làm nấy)"
            ]
        }
        if is_new(cand): return cand

    # 8. Mua sắm & Thời trang (Taobao / Shopping)
    elif any(k in text for k in ["买", "逛街", "衣服", "淘宝", "shopping", "mua sắm", "thời trang", "giá"]):
        cand = {
            "reply_hanzi": "逛街买到心仪的东西最开心了！你平时喜欢网上网购还是去商场实体店挑？最近有没有淘到什么好物？",
            "reply_pinyin": "Guàngjiē mǎi dào xīnyí de dōngxi zuì kāixīn le! Nǐ píngshí xǐhuan wǎngshàng wǎnggòu háishì qù shāngchǎng shítǐdiàn tiāo? Zuìjìn yǒu méiyǒu táo dào shénme hǎowù?",
            "translation_vi": "Đi mua sắm sắm được món đồ ưng ý là vui nhất! Bạn thích mua sắm online trên mạng hay ra trung tâm thương mại chọn trực tiếp? Gần đây có săn được món đồ xịn nào không?",
            "feedback": "Từ vựng mua sắm rất thiết thực cho giao tiếp đời sống hàng ngày.",
            "suggested_replies": [
                "我更喜欢在网上淘好物，款式多而且省事 (Wǒ gèng xǐhuan zài wǎngshang táo hǎowù, kuǎnshì duō érqiě shěngshì - Tôi thích săn đồ trên mạng hơn, nhiều mẫu mã lại tiện lợi)",
                "我喜欢去实体店试穿，看面料和版型最直观 (Wǒ xǐhuan qù shítǐdiàn shìchuān, kàn miànliào hé bǎnxíng zuì zhíguān - Tôi thích ra cửa hàng thử đồ trực tiếp, xem chất vải và phom dáng chuẩn nhất)",
                "最近刚买了一件特别舒服的外套，性价比很高 (Zuìjìn gāng mǎi le yí jiàn tèbié shūfu de wàitào, xìngjiàbǐ hěn gāo - Gần đây tôi vừa mua một chiếc áo khoác rất thoải mái, giá cả cực kỳ hời)"
            ]
        }
        if is_new(cand): return cand

    # 9. MỚI: Sở thích, Thể thao, Âm nhạc & Đọc sách (Gỡ triệt để vòng lặp sở thích)
    elif any(k in text for k in ["爱好", "音乐", "歌", "跑", "运动", "健身", "球", "摄影", "拍照", "书", "游戏", "sở thích", "đam mê", "âm nhạc", "chạy bộ", "thể thao", "đọc sách", "game", "chụp ảnh", "bơi"]):
        cand = {
            "reply_hanzi": "哇，听到你的爱好真让人觉得生活很有热情！坚持这些健康的兴趣能让人彻底放松。你平时一般是一个人享受这个爱好，还是喜欢和志同道合的朋友一起玩？",
            "reply_pinyin": "Wa, tīngdào nǐ de àihào zhēn ràng rén juéde shēnghuó hěn yǒu rèqíng! Jiānchí zhèxiē jiànkāng de xìngqù néng ràng rén chèdǐ fàngsōng. Nǐ píngshí yìbān shì yì gè rén xiǎngshòu zhège àihào, háishì xǐhuan hé zhìtóngdàohé de péngyou yìqǐ wán?",
            "translation_vi": "Oa, nghe về sở thích của bạn thật sự thấy cuộc sống tràn đầy nhiệt huyết! Duy trì những thú vui lành mạnh này giúp xua tan mệt mỏi rất tốt. Bạn thường thích tận hưởng sở thích này một mình hay thích tham gia cùng bạn bè chung chí hướng?",
            "feedback": "Từ vựng về sở thích và thói quen rất phổ biến trong giao tiếp hàng ngày.",
            "suggested_replies": [
                "我更喜欢一个人静静地享受，这样最解压 (Wǒ gèng xǐhuan yí gè rén jìngjìng de xiǎngshòu, zhèyàng zuì jiěyā - Tôi thích một mình tận hưởng trong yên tĩnh hơn, như vậy xả stress nhất)",
                "我经常和志趣相投的朋友一起切磋交流 (Wǒ chángcháng hé zhìqù xiāngtóu de péngyou yìqǐ qiēcuō jiāoliú - Tôi hay giao lưu trao đổi cùng những người bạn có chung sở thích)",
                "有时候一个人，有时候和朋友，看当时的心情 (Yǒushíhou yí gè rén, yǒushíhou hé péngyou, kàn dāngshí de xīnqíng - Có lúc một mình, có lúc cùng bạn bè, tùy vào tâm trạng lúc đó)"
            ]
        }
        if is_new(cand): return cand

    # 10. MỚI: Học ngoại ngữ & Trau dồi bản thân
    elif any(k in text for k in ["学", "汉语", "中文", "英语", "tiếng trung", "tiếng anh", "ngoại ngữ", "phát âm", "từ vựng", "ngữ pháp"]):
        cand = {
            "reply_hanzi": "学习一门外语就像打开了一扇看世界的新窗户！你在练习中文的过程中，觉得最有趣或者最有成就感的是哪一部分？",
            "reply_pinyin": "Xuéxí yì mén wàiyǔ jiù xiàng dǎkāi le yí shàn kàn shìjiè de xīn chuānghu! Nǐ zài liànxí Zhōngwén de guòchéng zhōng, juéde zuì yǒuyìsi huòzhě zuì yǒu chéngjiùgǎn de shì nǎ yí bùfen?",
            "translation_vi": "Học một ngoại ngữ mới giống như mở ra một cánh cửa sổ nhìn ra thế giới! Trong quá trình luyện tiếng Trung, bạn thấy phần nào thú vị hoặc đem lại cảm giác thành tựu nhất?",
            "feedback": "Nói về trải nghiệm học tập giúp bạn rèn luyện phản xạ trình bày quan điểm cá nhân.",
            "suggested_replies": [
                "我觉得能听懂原汁原味的影视剧和歌曲最有成就感 (Wǒ juéde néng tīngdǒng yuánzhīyuánwèi de yǐngshìjù hé gēqǔ zuì yǒu chéngjiùgǎn - Tôi thấy nghe hiểu được phim ảnh và bài hát nguyên bản là đã nhất)",
                "汉字的字形和声调虽然难，但非常有美感和内涵 (Hànzì de zìxíng hé shēngdiào suīrán nán, dàn fēicháng yǒu měigǎn hé nèihán - Chữ Hán và thanh điệu tuy khó nhưng rất giàu tính thẩm mỹ và chiều sâu)",
                "我喜欢能自信开口表达，和朋友无障碍沟通 (Wǒ xǐhuan néng zìxìn kāikǒu biǎodá, hé péngyou wú zhàng'ài gōutōng - Tôi thích cảm giác tự tin mở lời biểu đạt, giao tiếp thông suốt cùng bạn bè)"
            ]
        }
        if is_new(cand): return cand

    # 11. MỚI: Chào hỏi, Lịch sự & Bắt chuyện tự nhiên
    elif any(k in text for k in ["你好", "您好", "xin chào", "chào", "早安", "晚安", "好的", "哈哈", "嗨"]):
        cand = {
            "reply_hanzi": "嗨！很高兴能和你畅聊。今天过得怎么样？是刚下班还是正在休息？跟我分享一下你此刻的心情吧！",
            "reply_pinyin": "Hāi! Hěn gāoxìng néng hé nǐ chàngliáo. Jīntiān guò de zěnmeyàng? Shì gāng xiàbān háishì zhèngzài xiūxi? Gēn wǒ fēnxiǎng yíxià nǐ cǐkè de xīnqíng ba!",
            "translation_vi": "Chào bạn! Rất vui được trò chuyện thoải mái cùng bạn. Ngày hôm nay của bạn thế nào rồi? Vừa tan làm hay đang nghỉ ngơi? Chia sẻ với mình tâm trạng lúc này của bạn nhé!",
            "feedback": "Lời chào tự nhiên giúp bắt nhịp câu chuyện cực kỳ mượt mà.",
            "suggested_replies": [
                "我今天过得挺充实的，刚忙完手头的事情 (Wǒ jīntiān guò de tǐng chōngshí de, gāng máng wán shǒutóu de shìqing - Hôm nay tôi trải qua khá trọn vẹn, vừa làm xong việc trong tay)",
                "今天有点小累，正想找人轻松聊聊天解解压 (Jīntiān yǒudiǎn xiǎo lèi, zhèng xiǎng zhǎo rén qīngsōng liáoliáo tiān jiějiě yā - Hôm nay hơi mệt chút, đang muốn tìm người tán gẫu nhẹ nhàng để xả hơi)",
                "我心情很不错，正准备吃点好吃的犒劳自己 (Wǒ xīnqíng hěn búcuò, zhèng zhǔnbèi chī diǎn hǎochī de kàolao zìjǐ - Tâm trạng tôi rất tốt, đang chuẩn bị ăn món ngon để tự thưởng cho mình)"
            ]
        }
        if is_new(cand): return cand

    # Mặc định: Hệ thống xoay vòng chủ đề thông minh CHỐNG LẶP TUYỆT ĐỐI
    available_turns = [turn_item for turn_item in DEFAULT_CHINESE_TURNS if turn_item["reply_hanzi"] not in past_replies]
    if not available_turns:
        available_turns = DEFAULT_CHINESE_TURNS

    chosen_index = (max(turn, 1) - 1) % len(available_turns)
    return available_turns[chosen_index]

def _resolve_english_dynamic(text: str, scenario: str, turn: int, history: list = None):
    # Lấy tập hợp các câu phản hồi trước đó của trợ lý để chống lặp tuyệt đối
    past_replies = set()
    for item in (history or []):
        if item.get("role") in ["assistant", "model"]:
            c = item.get("content", "").strip()
            if c:
                past_replies.add(c)

    def is_new(item):
        return item and item.get("reply") not in past_replies

    import re
    words = set(re.findall(r'[a-zA-Z0-9_]+', text.lower()))

    def has_any(*kw_list):
        for k in kw_list:
            if " " in k:
                if k in text: return True
            else:
                if k in words or k in text: return True
        return False

    # 1. Coffee & Cafes
    if has_any("coffee", "cafe", "latte", "espresso", "cà phê", "quán xá", "brew", "cappuccino"):
        cand = {
            "reply": "I'm always down for good coffee! Do you prefer iced drinks or hot brew, and what's your absolute favorite spot?",
            "reply_ipa": "/aɪm ˈɔːlweɪz daʊn fər ɡʊd ˈkɔːfi! duː juː prɪˈfɜːr aɪst drɪŋks ɔːr hɑːt bruː, ænd wʌts jʊər ˈæbsəluːt ˈfeɪvərɪt spɑːt?/",
            "translation_vi": "Tôi luôn sẵn sàng cho một tách cà phê ngon! Bạn thích đồ uống đá hay đồ nóng, và quán ruột của bạn là ở đâu?",
            "feedback": "Talking about coffee is an effortless conversation starter with native speakers.",
            "suggested_replies": [
                "I love an iced Americano to start my busy morning. (/aɪ lʌv ən aɪst əˌmerɪˈkɑːnoʊ tuː stɑːrt maɪ ˈbɪzi ˈmɔːrnɪŋ/ - Tôi mê một ly Americano đá để khởi đầu buổi sáng bận rộn.)",
                "I usually get a hot vanilla latte with oat milk. (/aɪ ˈjuːʒuəli ɡet ə hɑːt vəˈnɪlə ˈlɑːteɪ wɪð oʊt mɪlk/ - Tôi thường gọi một ly latte vani nóng với sữa yến mạch.)",
                "I'm actually more of a tea person, especially matcha! (/aɪm ˈæktʃuəli mɔːr əv ə tiː ˈpɜːrsən, əˈspeʃəli ˈmætʃə/ - Thực ra tôi là người thích uống trà hơn, đặc biệt là matcha!)"
            ]
        }
        if is_new(cand): return cand

    # 2. Food & Cooking
    elif has_any("food", "dish", "cook", "restaurant", "ẩm thực", "món ngon", "nấu", "ăn", "dinner", "lunch", "breakfast", "meal", "delicious"):
        cand = {
            "reply": "Talking about delicious food always makes me hungry! What is your all-time favorite comfort dish to eat?",
            "reply_ipa": "/ˈtɔːkɪŋ əˈbaʊt dɪˈlɪʃəs fuːd ˈɔːlweɪz meɪks miː ˈhʌŋɡri! wʌt ɪz jʊər ˈɔːltaɪm ˈfeɪvərɪt ˈkʌmfərt dɪʃ tuː iːt?/",
            "translation_vi": "Nói về đồ ăn ngon lúc nào cũng làm tôi thấy thèm! Món ăn khoái khẩu nhất mang lại cảm giác dễ chịu cho bạn là gì?",
            "feedback": "Food vocabulary is rich and expressive. Don't hesitate to describe flavors and textures!",
            "suggested_replies": [
                "Nothing beats a hot bowl of traditional beef pho. (/ˈnʌθɪŋ biːts ə hɑːt boʊl əv trəˈdɪʃənl biːf fɜːr/ - Không gì sánh bằng một tô phở bò truyền thống bốc khói nghi ngút.)",
                "I'm a huge fan of Italian pasta and crispy pizza. (/aɪm ə hjuːdʒ fæn əv ɪˈtæljən ˈpɑːstə ænd ˈkrɪspi ˈpiːtsə/ - Tôi là fan cuồng của mì Ý và pizza giòn rụm.)",
                "I really enjoy cooking simple homemade meals every evening. (/aɪ ˈriːəli ɪnˈdʒɔɪ ˈkʊkɪŋ ˈsɪmpəl ˈhoʊmmeɪd miːlz ˈevri ˈiːvnɪŋ/ - Tôi rất thích tự nấu những bữa cơm nhà giản dị mỗi tối.)"
            ]
        }
        if is_new(cand): return cand

    # 3. Travel & Vacations
    elif has_any("travel", "trip", "vacation", "flight", "du lịch", "khám phá", "destination", "beach", "hotel"):
        cand = {
            "reply": "Traveling is such an incredible way to experience the world! What was the most unforgettable trip you've ever taken?",
            "reply_ipa": "/ˈtrævəlɪŋ ɪz sʌtʃ ən ɪnˈkredəbəl weɪ tuː ɪkˈspɪriəns ðə wɜːrld! wʌt wʌz ðə moʊst ˌʌnfərˈɡetəbəl trɪp juːv ˈevər ˈteɪkən?/",
            "translation_vi": "Đi du lịch là cách tuyệt vời nhất để trải nghiệm thế giới! Chuyến đi đáng nhớ nhất bạn từng trải qua là gì?",
            "feedback": "Use the past tense to describe highlights from past trips and adventures.",
            "suggested_replies": [
                "My trip to the coastal beaches was totally breathtaking. (/maɪ trɪp tuː ðə ˈkoʊstl ˈbiːtʃɪz wʌz ˈtoʊtəli ˈbreθteɪkɪŋ/ - Chuyến đi tới các bãi biển của tôi đẹp đến ngỡ ngàng.)",
                "I love exploring vibrant city nightlife and local street food. (/aɪ lʌv ɪkˈsplɔːrɪŋ ˈvaɪbrənt ˈsɪti ˈnaɪtlaɪf ænd ˈloʊkl striːt fuːd/ - Tôi thích khám phá cuộc sống về đêm sôi động và ẩm thực đường phố.)",
                "I'm planning an exciting road trip with friends this summer. (/aɪm ˈplænɪŋ ən ɪkˈsaɪtɪŋ roʊd trɪp wɪð frendz ðɪs ˈsʌmər/ - Tôi đang lên kế hoạch cho một chuyến phượt cùng bạn bè vào mùa hè này.)"
            ]
        }
        if is_new(cand): return cand

    # 4. Work & Career
    elif has_any("work", "job", "career", "office", "công việc", "sự nghiệp", "đi làm", "company", "boss", "deadline"):
        cand = {
            "reply": "Balancing work and personal life is always a journey! How has your workday been treating you lately?",
            "reply_ipa": "/ˈbælənsɪŋ wɜːrk ænd ˈpɜːrsənl laɪf ɪz ˈɔːlweɪz ə ˈdʒɜːrni! haʊ hæz jʊər ˈwɜːrkdeɪ biːn ˈtriːtɪŋ juː ˈleɪtli?/",
            "translation_vi": "Cân bằng công việc và cuộc sống luôn là một hành trình! Công việc dạo này của bạn diễn ra thế nào?",
            "feedback": "Work topics let you practice professional expressions and everyday banter.",
            "suggested_replies": [
                "Work has been quite productive, and my teammates are great. (/wɜːrk hæz biːn kwaɪt prəˈdʌktɪv, ænd maɪ ˈtiːmmeɪts ɑːr ɡreɪt/ - Công việc khá hiệu quả và đồng nghiệp của tôi rất tuyệt.)",
                "Things are a bit hectic right now with upcoming deadlines. (/θɪŋz ɑːr ə bɪt ˈhektɪk raɪt naʊ wɪð ˈʌpˌkʌmɪŋ ˈdedlaɪnz/ - Mọi thứ đang hơi bận rộn một chút vì hạn chót sắp đến.)",
                "I'm learning a lot of new skills at my current job. (/aɪm ˈlɜːrnɪŋ ə lɑːt əv nuː skɪlz æt maɪ ˈkɜːrənt dʒɑːb/ - Tôi đang học hỏi được rất nhiều kỹ năng mới ở công việc hiện tại.)"
            ]
        }
        if is_new(cand): return cand

    # 5. Movies & Entertainment
    elif has_any("movie", "movies", "film", "films", "cinema", "netflix", "phim", "giải trí", "series", "actor"):
        cand = {
            "reply": "Watching movies is such a fantastic way to unwind! Have you seen any great films or series recently?",
            "reply_ipa": "/ˈwɑːtʃɪŋ ˈmuːviz ɪz sʌtʃ ə fænˈtæstɪk weɪ tuː ʌnˈwaɪnd! hæv juː siːn ˈɛni ɡreɪt fɪlmz ɔːr ˈsɪriːz ˈriːsntli?/",
            "translation_vi": "Xem phim đúng là cách xả stress tuyệt vời nhất! Gần đây bạn có xem bộ phim hay series nào tâm đắc không?",
            "feedback": "Talk about movie genres you enjoy, like thrillers, sci-fi, comedy, or drama.",
            "suggested_replies": [
                "I recently watched an amazing sci-fi movie with stunning visuals. (/aɪ ˈriːsntli wɑːtʃt ən əˈmeɪzɪŋ ˈsaɪfaɪ ˈmuːvi wɪð ˈstʌnɪŋ ˈvɪʒuəlz/ - Gần đây tôi vừa xem một phim khoa học viễn tưởng kỹ xảo tuyệt đẹp.)",
                "I'm binge-watching a hilarious comedy series on Netflix. (/aɪm bɪndʒ ˈwɑːtʃɪŋ ə hɪˈlæriəs ˈkɑːmədi ˈsɪriːz ɑːn ˈnetflɪks/ - Tôi đang cày một bộ phim hài kịch cực vui trên Netflix.)",
                "I prefer psychological thrillers that keep me guessing until the end. (/aɪ prɪˈfɜːr ˌsaɪkəˈlɑːdʒɪkl ˈθrɪlərz ðæt kiːp miː ˈɡesɪŋ ʌnˈtɪl ðiː end/ - Tôi thích phim giật gân tâm lý khiến người xem phải đoán đến phút cuối.)"
            ]
        }
        if is_new(cand): return cand

    # 6. Weather & Life vibes
    elif has_any("weather", "rain", "rainy", "raining", "sunny", "season", "thời tiết", "mưa", "nắng", "cold", "warm", "hot"):
        cand = {
            "reply": "How's the weather over there today? Do you prefer sunny clear skies or cool rainy days?",
            "reply_ipa": "/haʊz ðə ˈweðər ˈoʊvər ðɛr təˈdeɪ? duː juː prɪˈfɜːr ˈsʌni klɪr skaɪz ɔːr kuːl ˈreɪni deɪz?/",
            "translation_vi": "Thời tiết bên bạn hôm nay thế nào? Bạn thích trời nắng quang đãng hay những ngày mưa mát mẻ hơn?",
            "feedback": "Talking about the weather is an easy, friendly ice-breaker everywhere.",
            "suggested_replies": [
                "It's sunny and pleasantly breezy today. (/ɪts ˈsʌni ænd ˈplezntli ˈbriːzi təˈdeɪ/ - Hôm nay trời nắng ráo và gió hiu hiu rất dễ chịu.)",
                "I love cool autumn days when the air feels crisp. (/aɪ lʌv kuːl ˈɔːtəm deɪz wen ðiː ɛr fiːlz krɪsp/ - Tôi mê những ngày thu mát mẻ không khí trong lành.)",
                "It's raining pretty heavily here, perfect for staying indoors. (/ɪts ˈreɪnɪŋ ˈprɪti ˈhevɪli hɪr, ˈpɜːrfɪkt fər ˈsteɪɪŋ ˌɪnˈdɔːrz/ - Chỗ tôi đang mưa khá to, rất hợp để ngồi trong nhà.)"
            ]
        }
        if is_new(cand): return cand

    # 7. Weekend & Relaxation
    elif has_any("weekend", "plans", "relax", "relaxing", "cuối tuần", "xả stress", "kế hoạch", "saturday", "sunday"):
        cand = {
            "reply": "The weekend is always something to look forward to! Do you have any fun plans coming up?",
            "reply_ipa": "/ðə ˈwiːkend ɪz ˈɔːlweɪz ˈsʌmθɪŋ tuː lʊk ˈfɔːrwərd tuː! duː juː hæv ˈɛni fʌn plænz ˈkʌmɪŋ ʌp?/",
            "translation_vi": "Cuối tuần lúc nào cũng là điều đáng mong đợi! Bạn có kế hoạch vui chơi gì sắp tới chưa?",
            "feedback": "Weekend plans are great for practicing future tenses and casual plans.",
            "suggested_replies": [
                "I'm planning to catch up on sleep and relax at home. (/aɪm ˈplænɪŋ tuː kætʃ ʌp ɑːn sliːp ænd rɪˈlæks æt hoʊm/ - Tôi định ngủ bù một bữa đã rồi thong thả nghỉ ngơi ở nhà.)",
                "I'm meeting up with some close friends for dinner and drinks. (/aɪm ˈmiːtɪŋ ʌp wɪð sʌm kloʊs frendz fər ˈdɪnər ænd drɪŋks/ - Tôi sẽ tụ tập bạn thân đi ăn tối và cà phê.)",
                "No set plans yet, just taking things as they come! (/noʊ set plænz jet, dʒʌst ˈteɪkɪŋ θɪŋz æz ðeɪ kʌm/ - Chưa có lịch gì cố định, cứ để mọi thứ tự nhiên thôi!)"
            ]
        }
        if is_new(cand): return cand

    # 8. Shopping & Fashion
    elif has_any("shopping", "clothes", "store", "buy", "bought", "mua sắm", "thời trang", "đồ", "jacket", "shoes"):
        cand = {
            "reply": "Retail therapy is always fun! Do you prefer browsing in physical stores or shopping online for convenience?",
            "reply_ipa": "/ˈriːteɪl ˈθerəpi ɪz ˈɔːlweɪz fʌn! duː juː prɪˈfɜːr ˈbraʊzɪŋ ɪn ˈfɪzɪkl stɔːrz ɔːr ˈʃɑːpɪŋ ˌɑːnˈlaɪn fər kənˈviːniəns?/",
            "translation_vi": "Đi mua sắm xả stress lúc nào cũng vui! Bạn thích đi dạo ở cửa hàng trực tiếp hay mua hàng online cho tiện?",
            "feedback": "Use shopping vocabulary to talk about styles, bargains, and choices.",
            "suggested_replies": [
                "I definitely prefer online shopping because of the great deals and variety. (/aɪ ˈdefɪnətli prɪˈfɜːr ˌɑːnˈlaɪn ˈʃɑːpɪŋ bɪˈkəz əv ðə ɡreɪt diːlz ænd vəˈraɪəti/ - Tôi chắc chắn thích mua online hơn vì nhiều ưu đãi và đa dạng mẫu mã.)",
                "I like going to actual malls so I can try things on before buying. (/aɪ laɪk ˈɡoʊɪŋ tuː ˈæktʃuəl mɔːlz soʊ aɪ kæn traɪ θɪŋz ɑːn bɪˈfɔːr ˈbaɪɪŋ/ - Tôi thích đi trung tâm thương mại để thử đồ trực tiếp trước khi mua.)",
                "I recently bought a really stylish jacket that I wear almost every day. (/aɪ ˈriːsntli bɔːt ə ˈriːəli ˈstaɪlɪʃ ˈdʒækɪt ðæt aɪ wer ˈɔːlmoʊst ˈevri deɪ/ - Gần đây tôi vừa mua được chiếc áo khoác rất phong cách mà hầu như ngày nào cũng mặc.)"
            ]
        }
        if is_new(cand): return cand

    # 9. MỚI: Hobbies, Sports, Music, Reading & Fitness (Giải quyết triệt để lặp câu hỏi sở thích)
    elif has_any("hobby", "hobbies", "music", "song", "songs", "run", "running", "sport", "sports", "gym", "workout", "fitness", "photo", "photography", "book", "books", "read", "reading", "game", "gaming", "sở thích", "âm nhạc", "chạy bộ", "thể thao", "đọc sách"):
        cand = {
            "reply": "It's wonderful to have passionate hobbies! Pursuing what you love is the best way to decompress. Do you usually enjoy this solo or with a group of friends?",
            "reply_ipa": "/ɪts ˈwʌndərfl tuː hæv ˈpæʃənət ˈhɑːbiz! pərˈsuːɪŋ wʌt juː lʌv ɪz ðə best weɪ tuː ˌdiːkəmˈpres. duː juː ˈjuːʒuəli ɪnˈdʒɔɪ ðɪs ˈsoʊloʊ ɔːr wɪð ə ɡruːp əv frendz?/",
            "translation_vi": "Thật tuyệt khi có những đam mê riêng! Theo đuổi điều mình yêu thích là cách tốt nhất để xả hơi. Bạn thường tận hưởng sở thích này một mình hay cùng một nhóm bạn?",
            "feedback": "Sharing about personal hobbies makes English conversations feel lively and authentic.",
            "suggested_replies": [
                "I definitely prefer enjoying it solo to fully clear my mind. (/aɪ ˈdefɪnətli prɪˈfɜːr ɪnˈdʒɔɪɪŋ ɪt ˈsoʊloʊ tuː ˈfʊli klɪr maɪ maɪnd/ - Tôi chắc chắn thích tận hưởng một mình để đầu óc hoàn toàn thư thái.)",
                "I often gather with like-minded friends to share our enthusiasm. (/aɪ ˈɔːfn ˈɡæðər wɪð laɪkˈmaɪndɪd frendz tuː ʃɛr ˈaʊər ɪnˈθuːziæzəm/ - Tôi hay tụ tập cùng những người bạn có chung đam mê để chia sẻ nhiệt huyết.)",
                "It depends on my mood, sometimes solo and sometimes with company. (/ɪt dɪˈpendz ɑːn maɪ muːd, ˈsʌmtaɪmz ˈsoʊloʊ ænd ˈsʌmtaɪmz wɪð ˈkʌmpəni/ - Tùy thuộc vào tâm trạng, lúc thì một mình lúc thì đi cùng bạn bè.)"
            ]
        }
        if is_new(cand): return cand

    # 10. MỚI: Learning Languages & Self-growth
    elif has_any("learn", "learning", "english", "chinese", "study", "language", "fluent", "speak", "practice", "tiếng anh", "tiếng trung", "phát âm"):
        cand = {
            "reply": "Learning a new language is truly like gaining a second soul! What part of practicing spoken English do you find most rewarding?",
            "reply_ipa": "/ˈlɜːrnɪŋ ə nuː ˈlæŋɡwɪdʒ ɪz ˈtruːli laɪk ˈɡeɪnɪŋ ə ˈsekənd soʊl! wʌt pɑːrt əv ˈpræktɪsɪŋ ˈspoʊkən ˈɪŋɡlɪʃ duː juː faɪnd moʊst rɪˈwɔːrdɪŋ?/",
            "translation_vi": "Học một ngoại ngữ mới thực sự giống như có thêm một tâm hồn thứ hai! Phần nào trong việc luyện nói tiếng Anh làm bạn cảm thấy hào hứng và đắc ý nhất?",
            "feedback": "Reflecting on your learning journey helps build higher-level expressive sentences.",
            "suggested_replies": [
                "Being able to express my thoughts spontaneously feels incredibly empowering. (/ˈbiːɪŋ ˈeɪbl tuː ɪkˈspres maɪ θɔːts spɑːnˈteɪniəsli fiːlz ɪnˈkredəbli ɪmˈpaʊərɪŋ/ - Có thể tự nhiên biểu đạt suy nghĩ của mình đem lại cảm giác tự tin tuyệt vời.)",
                "I love understanding original movies and podcasts without needing subtitles. (/aɪ lʌv ˌʌndərˈstændɪŋ əˈrɪdʒənl ˈmuːviz ænd ˈpɑːdkæsts wɪˈðaʊt ˈniːdɪŋ ˈsʌbtaɪtlz/ - Tôi rất thích việc hiểu trọn vẹn phim và podcast gốc mà không cần phụ đề.)",
                "Connecting with international friends with zero language barrier is amazing. (/kəˈnektɪŋ wɪð ˌɪntərˈnæʃnəl frendz wɪð ˈzɪroʊ ˈlæŋɡwɪdʒ ˈbæriər ɪz əˈmeɪzɪŋ/ - Kết nối với bạn bè quốc tế mà không có rào cản ngôn ngữ là điều rất tuyệt vời.)"
            ]
        }
        if is_new(cand): return cand

    # 11. MỚI: Greetings, Friendly Banter & Politeness (Dùng regex word boundaries chống dính chữ)
    elif has_any("hi", "hello", "hey", "how are you", "chào", "xin chào", "good morning", "good evening"):
        cand = {
            "reply": "Hey there! It's so nice to chat with you today. How has your day been treating you so far?",
            "reply_ipa": "/heɪ ðɛr! ɪts soʊ naɪs tuː tʃæt wɪð juː təˈdeɪ. haʊ hæz jʊər deɪ biːn ˈtriːtɪŋ juː soʊ fɑːr?/",
            "translation_vi": "Chào bạn! Thật vui được trò chuyện cùng bạn hôm nay. Ngày hôm nay của bạn diễn ra thế nào rồi?",
            "feedback": "A warm greeting is the best way to kick off an engaging English conversation.",
            "suggested_replies": [
                "My day has been smooth and productive, thanks for asking! (/maɪ deɪ hæz biːn smuːð ænd prəˈdʌktɪv, θæŋks fər ˈæskɪŋ/ - Ngày hôm nay của tôi rất suôn sẻ và hiệu quả, cảm ơn bạn đã hỏi!)",
                "A bit busy, but I'm excited to practice some conversational English now. (/ə bɪt ˈbɪzi, bʌt aɪm ɪkˈsaɪtɪd tuː ˈpræktɪs səm ˌkɑːnvərˈseɪʃənl ˈɪŋɡlɪʃ naʊ/ - Hơi bận một chút, nhưng tôi rất hào hứng được luyện nói tiếng Anh lúc này.)",
                "Pretty relaxing! I'm just taking some quiet downtime to recharge. (/ˈprɪti rɪˈlæksɪŋ! aɪm dʒʌst ˈteɪkɪŋ səm ˈkwaɪət ˈdaʊntaɪm tuː ˌriːˈtʃɑːrdʒ/ - Khá thư thả! Tôi chỉ đang dành chút thời gian yên tĩnh để nạp lại năng lượng.)"
            ]
        }
        if is_new(cand): return cand

    # Mặc định: Hệ thống xoay vòng chủ đề thông minh CHỐNG LẶP TUYỆT ĐỐI
    available_turns = [turn_item for turn_item in DEFAULT_ENGLISH_TURNS if turn_item["reply"] not in past_replies]
    if not available_turns:
        available_turns = DEFAULT_ENGLISH_TURNS

    chosen_index = (max(turn, 1) - 1) % len(available_turns)
    return available_turns[chosen_index]

# ==============================================================================
# HỆ THỐNG KHỞI TẠO CHỦ ĐỀ ĐÀM THOẠI ĐA DẠNG (TOPIC CONVERSATION ENGINE)
# ==============================================================================

def start_topic_conversation(api_key: str, topic: str, lang: str = "en", preferred_model: str = "gemini-3-flash-preview") -> dict:
    """Khởi tạo cuộc trò chuyện mở đầu sinh động về bất kỳ chủ đề đàm thoại nào được chọn."""
    t_clean = (topic or "").strip().lower()
    if not t_clean or t_clean in ["free", "casual daily talk", "随心日常闲聊", "trò chuyện tự do", "tán gẫu", "tự do"]:
        topic_display = "日常随心闲聊" if lang == "zh" else "Casual Daily Talk"
    else:
        topic_display = topic.strip()
        # Loại bỏ các ngoặc đơn đa ngữ để không làm LLM nhầm lẫn ngôn ngữ mục tiêu
        topic_display = re.sub(r'[\(（].*?[\)）]', '', topic_display).strip()

    if api_key:
        try:
            if lang == "zh":
                prompt_text = f"""你是一位热情、幽默的中国母语中文语伴（标准普通话口音）。
用户是一位正在练习中文口语交流的越南学习者。
交流主题：“{topic_display}”。

严格语言规范（VÔ CÙNG QUAN TRỌNG）：
1. 目标学习语言：标准中文普通话。
2. "reply_hanzi": 必须是100%地道简体中文（1-2句话），必须以一个好问题结尾。严禁在此输出越南语或英语！
3. "reply_pinyin": 拼音带完整声调。
4. "translation_vi": 越南语自然流畅翻译。
5. "feedback": 简短鼓励提示（越南语），鼓励用户大胆开口练习说中文（严禁提及英语 / tiếng Anh！）。
6. "suggested_replies": 3个具体的中文回复建议，直接回答你刚才提出的问题，格式严格为："中文句子 (拼音 - 越南语翻译)"。

严格JSON输出：
{{
  "reply_hanzi": "中文开场白",
  "reply_pinyin": "pīnyīn",
  "translation_vi": "bản dịch tiếng Việt",
  "feedback": "lời khuyên học tiếng Trung",
  "suggested_replies": ["句1 (拼音 - Dịch)", "句2 (拼音 - Dịch)", "句3 (拼音 - Dịch)"]
}}"""
            else:
                prompt_text = f"""You are an enthusiastic, warm native English conversational tutor.
The user is a Vietnamese student practicing SPOKEN ENGLISH.
Conversation topic: "{topic_display}".

CRITICAL LANGUAGE CONSTRAINTS (VÔ CÙNG QUAN TRỌNG):
1. TARGET PRACTICE LANGUAGE: ENGLISH ONLY.
2. "reply": MUST BE 100% IN NATURAL, VIBRANT ENGLISH (1-2 sentences), concluding with an engaging open-ended question. NEVER output Vietnamese or Chinese here!
3. "reply_ipa": International Phonetic Alphabet (IPA) transcription of your English reply in slashes, e.g. "/.../".
4. "translation_vi": Natural Vietnamese translation of your English reply.
5. "feedback": Welcoming tip in Vietnamese encouraging the learner to speak ENGLISH freely and confidently (STRICTLY FORBIDDEN to mention Chinese / tiếng Trung / tiếng Hoa!).
6. "suggested_replies": Exactly 3 conversational phrases in English the student can say to answer your question. Each formatted strictly as: "English sentence (/IPA/ - Dịch tiếng Việt)".

STRICT JSON OUTPUT:
{{
  "reply": "English opening statement ending with a question",
  "reply_ipa": "/IPA transcription/",
  "translation_vi": "Bản dịch tiếng Việt",
  "feedback": "Lời khuyên luyện nói tiếng Anh bằng tiếng Việt",
  "suggested_replies": ["English phrase 1 (/IPA/ - Dịch)", "English phrase 2 (/IPA/ - Dịch)", "English phrase 3 (/IPA/ - Dịch)"]
}}"""

            single_turn_history = [{"role": "user", "content": prompt_text}]
            raw_res = call_gemini_api(api_key, single_turn_history, preferred_model=preferred_model)
            parsed = extract_json(raw_res)
            return sanitize_ai_result(parsed, lang, topic)
        except Exception as e:
            logger.warning(f"Lỗi khởi tạo chủ đề qua Gemini: {e}")

    # Fallback ngoại tuyến sinh động theo chủ đề
    fallback = get_topic_offline_opener(topic, lang)
    return sanitize_ai_result(fallback, lang, topic)

def get_topic_offline_opener(topic: str, lang: str = "en") -> dict:
    t = (topic or "").strip().lower()
    is_free = not t or t in ["free", "start_opener", "casual daily talk", "随心日常闲聊", "trò chuyện tự do", "tán gẫu", "tự do"]

    if lang == "zh":
        if is_free:
            return {
                "reply_hanzi": "你好呀！今天过得怎么样？很高兴能和你一起轻松聊聊天，最近有什么新鲜好玩的事吗？",
                "reply_pinyin": "Nǐ hǎo ya! Jīntiān guò de zěnmeyàng? Hěn gāoxìng néng hé nǐ yìqǐ qīngsōng liáoliáo tiān, zuìjìn yǒu shénme xīnxiān hǎowán de shì ma?",
                "translation_vi": "Chào bạn! Hôm nay bạn thế nào rồi? Rất vui vì được thoải mái trò chuyện cùng bạn, dạo này có chuyện gì mới lạ hay ho không?",
                "feedback": "Cố gắng lên nhé! Đừng sợ sai, cứ thoải mái chia sẻ những câu chuyện thường ngày bằng tiếng Trung nha.",
                "suggested_replies": [
                    "我今天过得挺好的，刚吃完一顿美味的午饭 (Wǒ jīntiān guò de tǐng hǎo de, gāng chī wán yí dùn měiwèi de wǔfàn - Hôm nay tôi thấy rất ổn, vừa ăn xong một bữa trưa ngon miệng)",
                    "今天工作有点忙，不过下班后打算去散散步 (Jīntiān gōngzuò yǒudiǎn máng, búguò xiàbān hòu dǎsuàn qù sànsanbù - Hôm nay công việc hơi bận, nhưng tan làm tôi tính đi dạo)",
                    "最近看了部很有意思的电影，你今天过得好吗？ (Zuìjìn kàn le bù hěn yǒu yìsi de diànyǐng, nǐ jīntiān guò de hǎo ma? - Dạo này tôi xem được bộ phim rất hay, hôm nay bạn thế nào?)"
                ]
            }
        return get_dynamic_offline_response("start_opener", "zh", t)
    else:
        if is_free:
            return {
                "reply": "Hey there! How is your day going so far? I'm so glad we have some time to chat today, what have you been up to?",
                "reply_ipa": "/heɪ ðɛr! haʊ ɪz jʊər deɪ ˈɡoʊɪŋ soʊ fɑːr? aɪm soʊ ɡlæd wiː hæv səm taɪm tuː tʃæt təˈdeɪ, wʌt hæv juː biːn ʌp tuː?/",
                "translation_vi": "Chào bạn! Ngày hôm nay của bạn thế nào rồi? Rất vui vì chúng ta có thời gian trò chuyện hôm nay, hôm nay bạn đã làm những gì rồi?",
                "feedback": "Chào mừng bạn! Hãy tự tin nói tiếng Anh tự nhiên nhé, đừng ngại ngập ngừng hay sợ sai sót.",
                "suggested_replies": [
                    "My day has been pretty good and relaxing so far. (/maɪ deɪ hæz biːn ˈprɪti ɡʊd ænd rɪˈlæksɪŋ soʊ fɑːr/ - Ngày hôm nay của tôi khá tốt và thư thả.)",
                    "I've been quite busy with work, but really happy to chat now. (/aɪv biːn kwaɪt ˈbɪzi wɪð wɜːrk, bʌt ˈriːəli ˈhæpi tuː tʃæt naʊ/ - Tôi khá bận với công việc, nhưng rất vui vì được trò chuyện lúc này.)",
                    "Just finished learning something new today, how about you? (/dʒʌst ˈfɪnɪʃt ˈlɜːrnɪŋ ˈsʌmθɪŋ nuː təˈdeɪ, haʊ əˈbaʊt juː? - Tôi vừa học xong một điều mới mẻ hôm nay, còn bạn thì sao?)"
                ]
            }
        return get_dynamic_offline_response("start_opener", "en", t)
