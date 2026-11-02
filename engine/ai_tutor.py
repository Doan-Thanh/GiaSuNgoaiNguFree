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

def call_gemini_api(api_key: str, history: list, system_instruction: str = "", preferred_model: str = "gemini-3.5-flash-lite") -> str:
    """Gọi trực tiếp Google Gemini API qua REST v1beta với model tối ưu tốc độ phản hồi."""
    candidate_models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-lite-latest"]
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
            res = requests.post(url, headers=headers, json=payload, timeout=15)
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

def process_tutor_chat(api_key: str, user_text: str, lang: str, scenario_id: str, history: list = None, turn_count: int = 1, preferred_model: str = "gemini-3.5-flash-lite"):
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
        return get_dynamic_offline_response(user_text, lang, scenario_id, turn_count)

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
        parsed = json.loads(raw_res)
        return parsed
    except Exception as e:
        logger.warning(f"Gemini API không phản hồi ({e}), chuyển sang động cơ mô phỏng ngữ cảnh linh động.")
        return get_dynamic_offline_response(user_text, lang, scenario_id, turn_count, error_note=str(e))

def generate_fresh_suggestions(api_key: str, lang: str, scenario_id: str, history: list = None, preferred_model: str = "gemini-3.5-flash-lite") -> list:
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
            parsed = json.loads(raw_res)
            if "suggested_replies" in parsed and isinstance(parsed["suggested_replies"], list) and len(parsed["suggested_replies"]) > 0:
                return parsed["suggested_replies"]
        except Exception as e:
            logger.warning(f"Không thể tạo gợi ý mới qua Gemini: {e}")

    # Fallback ngoại tuyến thông minh theo chủ đề
    offline = get_dynamic_offline_response(last_bot_msg or "đổi gợi ý", lang, scenario_id, random.randint(1, 10))
    return offline.get("suggested_replies", [])

# ==============================================================================
# HỆ THỐNG ĐỘNG CƠ GỢI Ý & PHẢN HỒI NỘI HÀM CỰC KỲ LINH ĐỘNG (OFFLINE ENGINE)
# ==============================================================================

def get_dynamic_offline_response(user_text: str, lang: str, scenario_id: str, turn_count: int = 1, error_note: str = None):
    text_lower = user_text.lower().strip()
    scenario_lower = (scenario_id or "").lower().strip()
    search_context = f"{text_lower} {scenario_lower}"

    if lang == "zh":
        return _resolve_chinese_dynamic(search_context, scenario_id, turn_count)
    else:
        return _resolve_english_dynamic(search_context, scenario_id, turn_count)

def _resolve_chinese_dynamic(text: str, scenario: str, turn: int):
    # 1. Cà phê & Quán xá
    if any(k in text for k in ["咖啡", "kāfēi", "cafe", "coffee", "cà phê", "quán xá"]):
        return {
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

    # 2. Ẩm thực & Món ngon
    elif any(k in text for k in ["美食", "菜", "饭", "火锅", "food", "cooking", "ẩm thực", "món ngon", "ăn"]):
        return {
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

    # 3. Du lịch & Khám phá
    elif any(k in text for k in ["旅游", "度假", "旅行", "travel", "trip", "du lịch", "khám phá"]):
        return {
            "reply_hanzi": "旅行总能让人心情变好！你至今去过最难忘的地方是哪里？接下来最想去哪儿玩？",
            "reply_pinyin": "Lǚxíng zǒng néng ràng rén xīanqíng biàn hǎo! Nǐ zhìjīn qù guo zuì nánwàng de dìfang shì nǎlǐ? Jiēxiàlai zuì xiǎng qù nǎr wán?",
            "translation_vi": "Đi du lịch lúc nào cũng làm tâm trạng phấn chấn! Nơi đáng nhớ nhất bạn từng đi là đâu? Sắp tới muốn đi đâu nhất?",
            "feedback": "Hãy chia sẻ về cảnh đẹp hoặc kỷ niệm một chuyến đi của bạn.",
            "suggested_replies": [
                "我最难忘的是去北京看长城和故宫，非常震撼 (Wǒ zuì nánwàng de shì qù Běijīng kàn Chángchéng hé Gùgōng, fēicháng zhènhàn - Đáng nhớ nhất là lần đi Bắc Kinh ngắm Vạn Lý Trường Thành và Cố Cung)",
                "我更喜欢去海边度假，吹吹海风晒晒太阳 (Wǒ gèng xǐhuan qù hǎibiān dùjià, chuīchui hǎifēng shàishai tàiyáng - Tôi thích đi biển nghỉ dưỡng, hóng gió và tắm nắng hơn)",
                "我打算今年休年假的时候出国走走 (Wǒ dǎsuàn jīnnián xiū niánjià de shíhou chūguó zǒuzou - Tôi tính dịp nghỉ phép năm nay sẽ đi du lịch nước ngoài một chuyến)"
            ]
        }

    # 4. Công việc & Sự nghiệp
    elif any(k in text for k in ["职场", "工作", "上班", "work", "career", "công việc", "sự nghiệp"]):
        return {
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

    # 5. Phim ảnh & Giải trí
    elif any(k in text for k in ["电影", "追剧", "movie", "cinema", "netflix", "phim", "giải trí"]):
        return {
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

    # 6. Thời tiết & Đời sống
    elif any(k in text for k in ["天气", "四季", "weather", "thời tiết", "mưa", "nắng"]):
        return {
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

    # 7. Cuối tuần & Thư giãn
    elif any(k in text for k in ["周末", "weekend", "cuối tuần", "xả stress", "kế hoạch"]):
        return {
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

    # 8. Mua sắm & Thời trang (Taobao / Shopping)
    elif any(k in text for k in ["买", "逛街", "衣服", "淘宝", "shopping", "mua sắm", "thời trang", "giá"]):
        return {
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

    # Mặc định: Trò chuyện tự do đời sống
    return {
        "reply_hanzi": "哈哈，聊得太开心了！除了这个，你平时有什么特别感兴趣的爱好吗？",
        "reply_pinyin": "Hāhā, liáo de tài kāixīn le! Chúle zhège, nǐ píngshí yǒu shénme tèbié gǎnxìngqù de àihào ma?",
        "translation_vi": "Haha, trò chuyện cùng bạn vui quá! Ngoài điều này ra, bình thường bạn có sở thích nào đặc biệt đam mê không?",
        "feedback": "Bạn đang giao tiếp rất tự nhiên và trôi chảy!",
        "suggested_replies": [
            "我平时很喜欢听音乐和跑步，能让人心情舒畅 (Wǒ píngshí hěn xǐhuan tīng yīnyuè hé pǎobù, néng ràng rén xīanqíng shūchàng - Bình thường tôi rất thích nghe nhạc và chạy bộ, giúp tâm trạng thư thái)",
            "我挺喜欢摄影的，周末常去扫街拍照 (Wǒ tǐng xǐhuan shèyǐng de, zhōumò cháng qù sǎojiē pāizhào - Tôi khá thích nhiếp ảnh, cuối tuần hay đi dạo phố chụp ảnh)",
            "你有什么好玩的爱好可以推荐给我吗？ (Nǐ yǒu shénme hǎowán de àihào kěyǐ tuījiàn gěi wǒ ma? - Bạn có sở thích nào thú vị gợi ý cho tôi không?)"
        ]
    }

def _resolve_english_dynamic(text: str, scenario: str, turn: int):
    # 1. Coffee & Cafes
    if any(k in text for k in ["coffee", "cafe", "latte", "espresso", "cà phê", "quán xá", "drink"]):
        return {
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

    # 2. Food & Cooking
    elif any(k in text for k in ["food", "dish", "cook", "restaurant", "ẩm thực", "món ngon", "nấu", "ăn"]):
        return {
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

    # 3. Travel & Vacations
    elif any(k in text for k in ["travel", "trip", "vacation", "flight", "du lịch", "khám phá"]):
        return {
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

    # 4. Work & Career
    elif any(k in text for k in ["work", "job", "career", "office", "công việc", "sự nghiệp", "đi làm"]):
        return {
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

    # 5. Movies & Entertainment
    elif any(k in text for k in ["movie", "film", "cinema", "netflix", "phim", "giải trí"]):
        return {
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

    # 6. Weather & Life vibes
    elif any(k in text for k in ["weather", "rain", "sunny", "season", "thời tiết", "mưa", "nắng"]):
        return {
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

    # 7. Weekend & Relaxation
    elif any(k in text for k in ["weekend", "plans", "relax", "cuối tuần", "xả stress", "kế hoạch"]):
        return {
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

    # 8. Shopping & Fashion
    elif any(k in text for k in ["shopping", "clothes", "store", "buy", "mua sắm", "thời trang", "đồ"]):
        return {
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

    # Default: Casual Daily Talk
    return {
        "reply": "That's awesome! Aside from that, what kind of hobbies or activities do you enjoy most in your free time?",
        "reply_ipa": "/ðæts ˈɔːsəm! əˈsaɪd frʌm ðæt, wʌt kaɪnd əv ˈhɑːbiz ɔːr ækˈtɪvətiz duː juː ɪnˈdʒɔɪ moʊst ɪn jʊər friː taɪm?/",
        "translation_vi": "Tuyệt quá! Ngoài điều đó ra, bạn thích những sở thích hay hoạt động nào nhất vào thời gian rảnh rỗi?",
        "feedback": "Keep it up! Your conversational rhythm is getting smoother and more natural with every turn.",
        "suggested_replies": [
            "I really enjoy listening to music and taking long evening walks. (/aɪ ˈriːəli ɪnˈdʒɔɪ ˈlɪsnɪŋ tuː ˈmjuːzɪk ænd ˈteɪkɪŋ lɔːŋ ˈiːvnɪŋ wɔːks/ - Tôi rất thích nghe nhạc và đi dạo buổi tối.)",
            "I love reading inspirational books and learning new skills online. (/aɪ lʌv ˈriːdɪŋ ˌɪnspəˈreɪʃənl bʊks ænd ˈlɜːrnɪŋ nuː skɪlz ˌɑːnˈlaɪn/ - Tôi thích đọc sách truyền cảm hứng và học các kỹ năng mới trên mạng.)",
            "What about you? What are your favorite pastimes outside of work? (/wʌt əˈbaʊt juː? wʌt ɑːr jʊər ˈfeɪvərɪt ˈpæstaɪmz ˌaʊtˈsaɪd əv wɜːrk? - Còn bạn thì sao? Thú vui tiêu khiển bạn thích nhất ngoài giờ làm việc là gì?)"
        ]
    }

# ==============================================================================
# HỆ THỐNG KHỞI TẠO CHỦ ĐỀ ĐÀM THOẠI ĐA DẠNG (TOPIC CONVERSATION ENGINE)
# ==============================================================================

def start_topic_conversation(api_key: str, topic: str, lang: str = "en", preferred_model: str = "gemini-3.5-flash-lite") -> dict:
    """Khởi tạo cuộc trò chuyện mở đầu sinh động về bất kỳ chủ đề đàm thoại nào được chọn."""
    t_clean = (topic or "").strip().lower()
    if not t_clean or t_clean in ["free", "casual daily talk", "随心日常闲聊", "trò chuyện tự do", "tán gẫu", "tự do"]:
        topic_display = "日常随心闲聊 (Casual Daily Talk)" if lang == "zh" else "Casual Daily Talk (Trò chuyện tự do)"
    else:
        topic_display = topic.strip()

    if api_key:
        try:
            if lang == "zh":
                prompt_text = f"""你是一位热情、幽默的中国母语中文语伴（北京标准口音）。
用户刚选择了日常口语交流主题：“{topic_display}”。

任务：
请自然且简短地开场（1-2句话）。对主题“{topic_display}”做一个接地气、生动的开场白，并提出一个开放式的好问题引发交流。

严格输出JSON格式：
- "reply_hanzi": 中文开场白（简体中文，1-2句话，必须以一个好问题结尾）。
- "reply_pinyin": 拼音带完整声调。
- "translation_vi": 越南语自然流畅翻译。
- "feedback": 简短鼓励提示（越南语），鼓励用户大胆开口练习。
- "suggested_replies": 3个具体的回复建议，直接回答你刚才提出的问题，格式严格为："中文句子 (拼音 - 越南语翻译)"。"""
            else:
                prompt_text = f"""You are an enthusiastic, warm native English conversational tutor.
The user just selected this daily conversation topic: "{topic_display}".

TASK:
Open the conversation naturally and concisely (1-2 sentences). Share a quick relatable remark about "{topic_display}" and ask an engaging open-ended question to kick off the talk.

Provide strictly valid JSON format:
- "reply": Your English opening message (1-2 sentences, must conclude with an engaging question).
- "reply_ipa": International Phonetic Alphabet (IPA) transcription of your reply enclosed in slashes, e.g. "/.../".
- "translation_vi": Natural Vietnamese translation of your reply.
- "feedback": Welcoming tip in Vietnamese encouraging the learner to speak freely.
- "suggested_replies": Array of 3 natural, specific conversational phrases the user can say to directly reply to your question. Each formatted strictly as: "English sentence (/IPA/ - Dịch tiếng Việt)"."""

            single_turn_history = [{"role": "user", "content": prompt_text}]
            raw_res = call_gemini_api(api_key, single_turn_history, preferred_model=preferred_model)
            parsed = json.loads(raw_res)
            return parsed
        except Exception as e:
            logger.warning(f"Lỗi khởi tạo chủ đề qua Gemini: {e}")

    # Fallback ngoại tuyến sinh động theo chủ đề
    return get_topic_offline_opener(topic, lang)

def get_topic_offline_opener(topic: str, lang: str = "en") -> dict:
    t = topic.lower()
    return get_dynamic_offline_response("start_opener", lang, t)
