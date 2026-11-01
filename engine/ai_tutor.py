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
            "temperature": 0.8,
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
    Xử lý phản hồi gia sư AI cho cả Tiếng Anh và Tiếng Trung, kèm hệ thống gợi ý cực kỳ linh động.
    """
    if not history:
        history = []

    current_history = list(history)
    current_history.append({"role": "user", "content": user_text})

    if not api_key:
        return get_dynamic_offline_response(user_text, lang, scenario_id, turn_count)

    scenario_info = next((s for s in SCENARIOS.get(lang, []) if s["id"] == scenario_id), None)
    scenario_title = scenario_info.get("title", "") if scenario_info else scenario_id
    bot_role = scenario_info.get("botRole", "Người bản ngữ") if scenario_info else "Đối tác"

    if lang == "zh":
        system_inst = f"""Bạn là một gia sư AI dạy tiếng Trung Quốc bản ngữ (Bắc Kinh) cực kỳ tự nhiên, thông minh và nhạy bén.
BỐI CẢNH ĐANG ĐÓNG VAI:
- Tình huống: {scenario_title}
- Vai của bạn: {bot_role}

Nhiệm vụ của bạn:
1. Trả lời người học tự nhiên theo đúng vai {bot_role} và đúng bối cảnh {scenario_title}. Đặt câu hỏi tiếp nối hợp lý.
2. CỰC KỲ QUAN TRỌNG VỀ GỢI Ý (suggested_replies):
   - BẮT BUỘC phải tạo ra 3 câu gợi ý KHỚP CHÍNH XÁC 100% với câu bạn vừa nói và đúng bối cảnh {scenario_title}.
   - TUYỆT ĐỐI KHÔNG đưa ra gợi ý lạc đề hoặc của tình huống khác.
   - 3 câu gợi ý đại diện cho 3 hướng trả lời KHÁC NHAU:
     + Hướng 1: Đồng ý / Chọn một lựa chọn cụ thể
     + Hướng 2: Hỏi thêm chi tiết / Thắc mắc / Mặc cả thêm
     + Hướng 3: Đổi ý / Từ chối nhẹ nhàng / Đề xuất phương án khác
3. Xuất JSON hợp lệ:
   - "reply_hanzi": Câu tiếng Trung (chữ Hán Giản thể).
   - "reply_pinyin": Phiên âm Pinyin kèm thanh điệu.
   - "translation_vi": Dịch nghĩa tiếng Việt tự nhiên.
   - "feedback": Nhận xét ngắn gọn về ngữ pháp/từ vựng/lượng từ của người dùng bằng tiếng Việt.
   - "suggested_replies": Mảng 3 chuỗi, mỗi chuỗi có dạng: "Chữ Hán (Pinyin - Nghĩa tiếng Việt)".
"""
    else:
        system_inst = f"""You are an engaging, highly adaptive native English language coach.
ROLEPLAY CONTEXT:
- Scenario: {scenario_title}
- Your Role: {bot_role}

Your tasks:
1. Respond naturally staying strictly in character as {bot_role} in the scenario: {scenario_title}. Keep responses conversational and concise (1-2 sentences).
2. CRITICAL FOR SUGGESTED REPLIES (suggested_replies):
   - You MUST provide 3 completely fresh, dynamic options directly responding to your latest question in this scenario ({scenario_title}).
   - The suggestions MUST MATCH the conversation context 100%. Never output suggestions from another topic.
   - The 3 options must cover 3 DISTINCT conversational intents:
     + Option 1: Direct confirmation / Making a specific choice
     + Option 2: Asking for details / Inquiring for options or customization
     + Option 3: Politeness / Hesitation / Suggesting an alternative
   - EACH suggestion MUST STRICTLY follow this 3-part format: "English sentence (/IPA phonetic transcription/ - Bản dịch tiếng Việt tự nhiên)"
     Example: "I'd love a hot cappuccino, please. (/aɪd lʌv ə hɑːt ˌkæpəˈtʃiːnoʊ, pliːz/ - Cho tôi một ly cappuccino nóng nhé.)"
3. Output strictly valid JSON:
   - "reply": Natural English response.
   - "reply_ipa": International Phonetic Alphabet (IPA) transcription of your reply enclosed in slashes, e.g. "/.../".
   - "translation_vi": Natural Vietnamese translation of your reply.
   - "feedback": Brief helpful tip in Vietnamese on natural phrasing, pronunciation notes, or grammar.
   - "suggested_replies": Array of 3 strings in the exact format "English sentence (/IPA/ - Bản dịch tiếng Việt)".
"""

    try:
        raw_res = call_gemini_api(api_key, current_history, system_inst, preferred_model=preferred_model)
        parsed = json.loads(raw_res)
        return parsed
    except Exception as e:
        logger.warning(f"Gemini API không phản hồi ({e}), chuyển sang động cơ mô phỏng ngữ cảnh linh động.")
        return get_dynamic_offline_response(user_text, lang, scenario_id, turn_count, error_note=str(e))

def generate_fresh_suggestions(api_key: str, lang: str, scenario_id: str, history: list = None, preferred_model: str = "gemini-3.5-flash-lite") -> list:
    """Tạo 3 câu gợi ý mới toanh khớp 100% với ngữ cảnh hội thoại hiện tại."""
    scenario_info = next((s for s in SCENARIOS.get(lang, []) if s["id"] == scenario_id), None)
    scenario_title = scenario_info.get("title", "") if scenario_info else scenario_id
    bot_role = scenario_info.get("botRole", "Đối tác") if scenario_info else "Đối tác"

    last_bot_msg = ""
    for item in reversed(history or []):
        if item.get("role") in ["assistant", "model"]:
            last_bot_msg = item.get("content", "").strip()
            break
    if not last_bot_msg and scenario_info:
        last_bot_msg = scenario_info.get("initialHanzi" if lang == "zh" else "initialMessage", "")

    if api_key:
        try:
            if lang == "zh":
                prompt_text = f"""Tình huống giao tiếp: {scenario_title} (bạn đang đóng vai: {bot_role}).
Câu nói gần nhất của bạn: "{last_bot_msg}"

YÊU CẦU:
Hãy tạo 3 câu gợi ý phản hồi HOÀN TOÀN MỚI, KHÁC BIỆT, tự nhiên để người học trả lời lại câu trên (không trùng với các gợi ý trước).
Mỗi câu có dạng: "Chữ Hán (Pinyin - Nghĩa tiếng Việt)".
Xuất duy nhất định dạng JSON: {{"suggested_replies": ["...", "...", "..."]}}"""
            else:
                prompt_text = f"""Roleplay scenario: {scenario_title} (your role: {bot_role}).
Your latest statement to the user: "{last_bot_msg}"

TASK:
Provide 3 completely FRESH, DIVERSE, and natural alternative responses the learner can say next to your statement.
Each suggestion MUST follow the 3-part format: "English phrase (/IPA phonetic transcription/ - Bản dịch tiếng Việt tự nhiên)"
Example: "Sounds wonderful, let's do that! (/saʊndz ˈwʌndərfəl, lets duː ðæt/ - Nghe tuyệt đấy, làm vậy đi!)"
Output strictly JSON format: {{"suggested_replies": ["...", "...", "..."]}}"""

            single_turn_history = [{"role": "user", "content": prompt_text}]
            raw_res = call_gemini_api(api_key, single_turn_history, preferred_model=preferred_model)
            parsed = json.loads(raw_res)
            if "suggested_replies" in parsed and isinstance(parsed["suggested_replies"], list) and len(parsed["suggested_replies"]) > 0:
                return parsed["suggested_replies"]
        except Exception as e:
            logger.warning(f"Không thể tạo gợi ý mới qua Gemini: {e}")

    # Fallback ngoại tuyến ngẫu nhiên nếu offline hoặc lỗi mạng
    offline = get_dynamic_offline_response("đổi gợi ý", lang, scenario_id, random.randint(1, 10))
    return offline.get("suggested_replies", [])

# ==============================================================================
# HỆ THỐNG ĐỘNG CƠ GỢI Ý & PHẢN HỒI NỘI HÀM CỰC KỲ LINH ĐỘNG (OFFLINE ENGINE)
# ==============================================================================

def get_dynamic_offline_response(user_text: str, lang: str, scenario_id: str, turn_count: int = 1, error_note: str = None):
    text_lower = user_text.lower().strip()
    if lang == "zh":
        return _resolve_chinese_dynamic(text_lower, scenario_id, turn_count)
    else:
        return _resolve_english_dynamic(text_lower, scenario_id, turn_count)

def _resolve_chinese_dynamic(text: str, scenario: str, turn: int):
    # 1. MUA SẮM TAOBAO / MẶC CẢ (逛街砍价)
    if scenario == "taobao":
        if any(k in text for k in ["多少钱", "贵", "便宜", "优惠", "打折", "算", "giá", "tiền"]):
            replies = [
                ("哎呀，美女/帅哥，这已经是最低的实价了！不过如果你今天真心要，我给你抹个零头，再送你一件小礼物，怎么样？",
                 "Āiyā, měinǚ/shuàigē, zhè yǐjīng shì zuìdī de shíjià le! Bùguò rúguǒ nǐ jīntiān zhēnxīn yào, wǒ gěi nǐ mǒ ge língtóu, zài sòng nǐ yí jiàn xiǎo lǐwù, zěnmeyàng?",
                 "Ái chà, người đẹp ơi, đây đã là giá sát đáy rồi! Nhưng nếu hôm nay bạn thật lòng lấy, mình bớt số lẻ cho bạn, tặng thêm món quà nhỏ, thấy sao?"),
                ("我们家都是正品原单，一分钱一分货嘛！不过看你是爽快人，买两件我直接给你包邮，还能再减20块！",
                 "Wǒmen jiā dōushì zhèngpǐn yuándān, yì fēn qián yì fēn huò ma! Bùguò kàn nǐ shì shuǎngkuai rén, mǎi liǎng jiàn wǒ zhíjiē gěi nǐ bāoyóu, hái néng zài jiǎn 20 kuài!",
                 "Nhà mình toàn hàng chuẩn xuất xịn, tiền nào của nấy mà! Nhưng thấy bạn xởi lởi, mua 2 chiếc mình freeship luôn, giảm thêm 20 tệ nữa!")
            ]
            chosen = random.choice(replies)
            suggestions = [
                "能再少点吗？合适我马上转账 (Néng zài shǎo diǎn ma? Héshì wǒ mǎshàng zhuǎnzhàng - Bớt thêm chút được không? Được giá em chuyển khoản luôn)",
                "那给我两件，直接算总价吧 (Nà gěi wǒ liǎng jiàn, zhíjiē suàn zǒngjià ba - Vậy lấy em 2 chiếc, tính tổng tiền luôn đi)",
                "我再去别家对比一下看看 (Wǒ zài qù biéjiā duìbǐ yíxià kànkan - Để em sang tiệm khác so sánh giá chút đã)"
            ]
            feedback = "Người Trung Quốc đi mua sắm rất hay dùng '抹个零头' (bớt số lẻ) hoặc '一分钱一分货' (tiền nào của nấy)."

        elif any(k in text for k in ["尺码", "大", "小", "号", "颜色", "黑色", "白色", "穿", "size", "màu"]):
            replies = [
                ("这款版型稍微偏大一点点。请问您的身高和体重是多少？我帮你拿最合身的尺码！还有黑色和卡其色哦。",
                 "Zhè kuǎn bǎnxíng shāowēi piān dà yìdiǎndiǎn. Qǐngwèn nín de shēngāo hé tǐzhòng shì duōshao? Wǒ bāng nǐ ná zuì héshēn de chǐmǎ! Hái yǒu hēisè hé kǎqísè o.",
                 "Mẫu này phom hơi rộng một chút xíu. Xin hỏi chiều cao và cân nặng của bạn là bao nhiêu? Mình lấy size vừa vặn nhất cho! Còn có màu đen và màu kaki nữa đấy."),
                ("放心吧，这是纯棉微弹面料，洗了绝对不缩水。你平时穿M还是L？试衣间就在那面镜子后面。",
                 "Fàngxīn ba, zhè shì chúnmián wēidàn miànliào, xǐ le juéduì bù suōshuǐ. Nǐ píngshí chuān M háishì L? Shìyījiān jiù zài nà miàn jìngzi hòumiàn.",
                 "Yên tâm đi, đây là chất cotton co giãn nhẹ, giặt tuyệt đối không co rút. Bạn hay mặc M hay L? Phòng thử đồ ngay sau tấm gương kia.")
            ]
            chosen = random.choice(replies)
            suggestions = [
                "我身高一米七，体重六十公斤，拿什么尺码？ (Wǒ shēngāo yī mǐ qī, tǐzhòng liùshí gōngjīn, ná shénme chǐmǎ? - Em cao 1m70, nặng 60kg, lấy size gì?)",
                "帮我拿一件黑色的试一下吧 (Bāng wǒ ná yí jiàn hēisè de shì yíxià ba - Lấy giúp em một chiếc màu đen thử chút)",
                "如果洗了缩水或者掉色包退吗？ (Rúguǒ xǐ le suōshuǐ huòzhě diàosè bāotuì ma? - Nếu giặt bị co hoặc phai màu có bao đổi trả không?)"
            ]
            feedback = "Khi hỏi size số quần áo, người bản xứ hay hỏi '身高和体重' (chiều cao và cân nặng) để tư vấn chuẩn xác."

        else:
            replies = [
                ("今天店里刚到了一批春季新款，挂在墙上的这件爆款卖得最好！你要不要摸摸面料手感？特别舒服！",
                 "Jīntiān diànlǐ gāng dào le yì pī chūnjì xīnkuǎn, guà zài qiáng shàng de zhè jiàn bàokuǎn mài de zuì hǎo! Nǐ yào bu yào mōmo miànliào shǒugǎn? Tèbié shūfu!",
                 "Hôm nay tiệm vừa về một lô hàng mới mùa xuân, chiếc treo trên tường này là mẫu hot bán chạy nhất đấy! Bạn có muốn sờ thử chất vải không? Mịn lắm!"),
                ("你看中哪件跟我说一声就行，今天全场买满200减30，看合适的可以直接上身体验！",
                 "Nǐ kànzhòng nǎ jiàn gēn wǒ shuō yì shēng jiù xíng, jīntiān quánchǎng mǎi mǎn 200 jiǎn 30, kàn héshì de zhíjiē shàngshēn tǐyàn!",
                 "Bạn ưng mẫu nào cứ bảo mình một tiếng nhé, hôm nay cả cửa hàng mua đủ 200 giảm 30 tệ, thấy hợp có thể mặc thử trực tiếp luôn!")
            ]
            chosen = random.choice(replies)
            suggestions = [
                "墙上那件外套拿下来给我看看吧 (Qiáng shàng nà jiàn wàitào ná xiàlai gěi wǒ kànkan ba - Lấy chiếc áo khoác trên tường xuống cho em xem với)",
                "今天店里还有别的优惠活动吗？ (Jīntiān diànlǐ hái yǒu biéde yōuhuì huódòng ma? - Hôm nay cửa hàng còn khuyến mãi nào khác không?)",
                "我先随便挑挑，挑好了再叫你 (Wǒ xiān suíbiàn tiāotiao, tiāohǎo le zài jiào nǐ - Em cứ chọn qua đã, chọn được sẽ gọi anh)"
            ]
            feedback = "Người Trung Quốc dùng '爆款' (bàokuǎn) để chỉ những sản phẩm cực hot, bán chạy cháy hàng."

        return {
            "reply_hanzi": chosen[0],
            "reply_pinyin": chosen[1],
            "translation_vi": chosen[2],
            "feedback": feedback,
            "suggested_replies": suggestions
        }

    # CÁC TÌNH HUỐNG KHÁC (FALLBACK NỘI HÀM MẶC ĐỊNH)
    scenario_info = next((s for s in SCENARIOS.get("zh", []) if s["id"] == scenario), None)
    if scenario_info:
        suggestions = scenario_info.get("initialSuggestions", [
            "好的，麻烦帮我安排一下 (Hǎode, máfan bāng wǒ ānpái yíxià - Được, phiền bạn sắp xếp giúp tôi)",
            "请问还有别的选择吗？ (Qǐngwèn hái yǒu biéde xuǎnzé ma? - Cho hỏi còn lựa chọn nào khác không?)",
            "我再考虑一下，谢谢 (Wǒ zài kǎolǜ yíxià, xièxie - Tôi cân nhắc thêm chút, cảm ơn)"
        ])
    else:
        suggestions = [
            "好的，非常感谢你！ (Hǎode, fēicháng gǎnxiè nǐ! - Vâng, cảm ơn bạn rất nhiều!)",
            "请问接下来该怎么办？ (Qǐngwèn jiēxiàlai gāi zěnme bàn? - Xin hỏi tiếp theo nên làm thế nào?)",
            "我们换个话题聊聊吧 (Wǒmen huàn ge huàtí liáoliao ba - Chúng ta đổi chủ đề trò chuyện nhé)"
        ]

    return {
        "reply_hanzi": "好的，我已经明白您的意思了！请问还有什么我可以为您解答的吗？",
        "reply_pinyin": "Hǎode, wǒ yǐjīng míngbai nín de yìsi le! Qǐngwèn hái yǒu shénme wǒ kěyǐ wèi nín jiědá de ma?",
        "translation_vi": "Vâng, tôi đã hiểu ý của bạn rồi! Xin hỏi còn điều gì tôi có thể giải đáp thêm cho bạn không?",
        "feedback": "Bạn diễn đạt rất tự nhiên và trôi chảy!",
        "suggested_replies": suggestions
    }

def _resolve_english_dynamic(text: str, scenario: str, turn: int):
    scenario_info = next((s for s in SCENARIOS.get("en", []) if s["id"] == scenario), None)
    if scenario_info:
        suggestions = scenario_info.get("initialSuggestions", [
            "Sounds good, could you give me more details? (/saʊndz ɡʊd, kəd juː ɡɪv miː mɔːr dɪˈteɪlz/ - Nghe hay đấy, bạn có thể cho tôi thêm chi tiết không?)",
            "What other options or recommendations do you have? (/wʌt ˈʌðər ˈɑːpʃənz ɔːr ˌrekəmenˈdeɪʃənz duː juː hæv/ - Bạn có lựa chọn hoặc gợi ý nào khác không?)",
            "I'll think about it and let you know shortly. (/aɪl θɪŋk əˈbaʊt ɪt ænd let juː noʊ ˈʃɔːrtli/ - Tôi sẽ cân nhắc và báo lại sớm.)"
        ])
    else:
        suggestions = [
            "That sounds great, thank you for your help! (/ðæt saʊndz ɡreɪt, θæŋk juː fər jʊər help/ - Nghe tuyệt quá, cảm ơn bạn đã giúp đỡ!)",
            "Could you explain a bit more about that? (/kəd juː ɪkˈspleɪn ə bɪt mɔːr əˈbaʊt ðæt/ - Bạn có thể giải thích thêm một chút về điều đó không?)",
            "Let's move on to another topic! (/lets muːv ɑːn tuː əˈnʌðər ˈtɑːpɪk/ - Chúng ta chuyển sang chủ đề khác nhé!)"
        ]

    return {
        "reply": "Understood! I completely get what you mean. What would you like to explore next?",
        "reply_ipa": "/ˌʌndərˈstʊd! aɪ kəmˈpliːtli ɡet wʌt juː miːn. wʌt wʊd juː laɪk tuː ɪkˈsplɔːr nekst?/",
        "translation_vi": "Đã hiểu! Tôi hoàn toàn hiểu ý của bạn. Bạn muốn tiếp tục tìm hiểu điều gì tiếp theo?",
        "feedback": "Phát âm tiếng Anh rất tự nhiên! Hãy chú ý ngữ điệu lên xuống tự nhiên ở cuối câu.",
        "suggested_replies": suggestions
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
- "reply_hanzi": 中文开场白（简体中文，1-2句话）。
- "reply_pinyin": 拼音带完整声调。
- "translation_vi": 越南语自然流畅翻译。
- "feedback": 简短鼓励提示（越南语），鼓励用户大胆开口练习。
- "suggested_replies": 3个具体的回复建议，格式严格为："中文句子 (拼音 - 越南语翻译)"。"""
            else:
                prompt_text = f"""You are an enthusiastic, warm native English conversational tutor.
The user just selected this daily conversation topic: "{topic_display}".

TASK:
Open the conversation naturally and concisely (1-2 sentences). Share a quick relatable remark about "{topic_display}" and ask an engaging open-ended question to kick off the talk.

Provide strictly valid JSON format:
- "reply": Your English opening message (1-2 sentences).
- "reply_ipa": International Phonetic Alphabet (IPA) transcription of your reply enclosed in slashes, e.g. "/.../".
- "translation_vi": Natural Vietnamese translation of your reply.
- "feedback": Welcoming tip in Vietnamese encouraging the learner to speak freely.
- "suggested_replies": Array of 3 natural, specific conversational phrases the user can say to reply to your question. Each formatted strictly as: "English sentence (/IPA/ - Dịch tiếng Việt)"."""

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
    if lang == "zh":
        if any(k in t for k in ["free", "闲聊", "自由", "tự do", "tán gẫu", "casual"]):
            return {
                "reply_hanzi": "哈喽！很高兴今天能和你聊天。你今天过得怎么样呀？",
                "reply_pinyin": "Hālóu! Hěn gāoxìng jīntiān néng hé nǐ liáotiān. Nǐ jīntiān guò de zěnmeyàng ya?",
                "translation_vi": "Chào bạn! Rất vui hôm nay được trò chuyện cùng bạn. Hôm nay của bạn thế nào rồi?",
                "feedback": "Cứ trò chuyện tự nhiên như hai người bạn thân nhé!",
                "suggested_replies": [
                    "挺好的，今天过得挺充实 (Tǐng hǎo de, jīntiān guò de tǐng chōngshí - Khá tốt, hôm nay của tôi trôi qua rất trọn vẹn)",
                    "今天有点忙，不过心情还不错 (Jīntiān yǒudiǎn máng, búguò xīanqíng hái búcuò - Hôm nay hơi bận một chút, nhưng tâm trạng vẫn rất tốt)",
                    "一切正常，正想找个人聊聊天呢 (Yíqiè zhèngcháng, zhèng xiǎng zhǎo gèrén liáoliao tiān ne - Mọi thứ đều bình thường, tôi đang muốn tìm người tán gẫu đây)"
                ]
            }
        elif any(k in t for k in ["cà phê", "quán xá", "咖啡", "kāfēi", "cafe", "coffee"]):
            return {
                "reply_hanzi": "聊到喝咖啡，我每天早上都得来一杯提提神！你平时喜欢喝美式还是拿铁？有常去的咖啡馆吗？",
                "reply_pinyin": "Liáo dào hē kāfēi, wǒ měitiān zǎoshang dōu děi lái yì bēi títi shén! Nǐ píngshí xǐhuan hē měishì háishì nátiě? Yǒu cháng qù de kāfēiguǎn ma?",
                "translation_vi": "Nhắc đến cà phê, sáng nào tôi cũng phải làm một ly cho tỉnh táo! Bạn hay uống Americano hay Latte? Có quán ruột nào hay ghé không?",
                "feedback": "Chủ đề cà phê rất gần gũi! Bạn có thể trả lời bằng việc kể loại cà phê yêu thích của mình.",
                "suggested_replies": [
                    "我更喜欢喝冰美式，比较清爽无负担 (Wǒ gèng xǐhuan hē bīng měishì, bǐjiào qīngshuǎng wú fùdān - Tôi thích Americano đá hơn, thanh nhẹ không béo)",
                    "我每天必喝热拿铁，奶香味特别浓 (Wǒ měitiān bì hē rè nátiě, nǎi xiāngwèi tèbié nóng - Ngày nào tôi cũng uống Latte nóng, thơm đậm vị sữa)",
                    "我平时不太喝咖啡，更喜欢喝奶茶或水果茶 (Wǒ píngshí bú tài hē kāfēi, gèng xǐhuan hē nǎichá huò shuǐguǒchá - Bình thường tôi ít uống cà phê, thích trà sữa hoặc trà hoa quả hơn)"
                ]
            }
        elif any(k in t for k in ["ẩm thực", "món ngon", "nấu nướng", "ăn", "美食", "菜", "饭", "food", "cooking"]):
            return {
                "reply_hanzi": "聊到好吃的我可就不困了！你最喜欢哪一种菜系？有没有什么百吃不厌的家常菜？",
                "reply_pinyin": "Liáo dào hǎochī de wǒ kě jiù bú kùn le! Nǐ zuì xǐhuan nǎ yì zhǒng càixì? Yǒu méiyǒu shénme bǎi chī bú yàn de jiāchángcài?",
                "translation_vi": "Nói đến đồ ăn ngon là tôi tỉnh cả ngủ! Bạn thích ẩm thực món gì nhất? Có món cơm nhà nào ăn hoài không chán không?",
                "feedback": "Nói về đồ ăn rất dễ mở rộng câu chuyện. Hãy miêu tả vị ngon nhé!",
                "suggested_replies": [
                    "我特别喜欢吃火锅，又麻又辣特别过瘾 (Wǒ tèbié xǐhuan chī huǒguō, yòu má yòu là tèbié guòyǐn - Tôi mê ăn lẩu cay tê, ăn cực kỳ đã)",
                    "我最喜欢越南牛肉粉和春卷，汤头特别鲜 (Wǒ zuì xǐhuan Yuènán niúròufěn hé chūnjuǎn, tāngtóu tèbié xiān - Tôi thích nhất phở bò và nem rán Việt Nam, nước dùng thanh ngọt)",
                    "我平时喜欢自己在家做饭，既健康又省钱 (Wǒ píngshí xǐhuan zìjǐ zài jiā zuòfàn, jì jiànkāng yòu shěngqián - Tôi hay tự nấu ăn ở nhà, vừa sạch lại tiết kiệm)"
                ]
            }
        elif any(k in t for k in ["du lịch", "khám phá", "nghỉ dưỡng", "旅游", "度假", "travel", "trip"]):
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
        elif any(k in t for k in ["công việc", "sự nghiệp", "đi làm", "职场", "工作", "上班", "work", "career"]):
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
        elif any(k in t for k in ["phim", "giải trí", "rạp chiếu", "电影", "追剧", "movie", "cinema", "netflix"]):
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
        elif any(k in t for k in ["thời tiết", "đời sống", "mưa", "nắng", "天气", "四季", "weather"]):
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
        elif any(k in t for k in ["cuối tuần", "xả stress", "kế hoạch", "周末", "weekend"]):
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
        else:
            return {
                "reply_hanzi": f"太棒了！今天我们一起来聊聊“{topic}”吧。关于这个话题，你最想跟我分享什么？",
                "reply_pinyin": f"Tài bàng le! Jīntiān wǒmen yìqǐ lái liáoliao “{topic}” ba. Guānyú zhège huàtí, nǐ zuì xiǎng gēn wǒ fēnxiǎng shénme?",
                "translation_vi": f"Tuyệt vời! Hôm nay chúng ta cùng trò chuyện về chủ đề “{topic}” nhé. Về chủ đề này, bạn muốn chia sẻ điều gì nhất cùng tôi?",
                "feedback": "Bạn hãy trả lời tự nhiên theo suy nghĩ của mình, đừng ngại phát âm nhé!",
                "suggested_replies": [
                    "我对这个话题特别感兴趣，平时经常关注 (Wǒ duì zhège huàtí tèbié gǎnxìngqù, píngshí jīngcháng guānzhù - Tôi rất quan tâm chủ đề này, thường xuyên theo dõi)",
                    "其实我了解得不算多，正想听听你的看法 (Qíshí wǒ liǎojiě de bú suàn duō, zhèng xiǎng tīngting nǐ de kànfǎ - Thực ra tôi chưa biết nhiều lắm, muốn nghe góc nhìn từ bạn)",
                    "从我个人的经验来看，这确实挺有意思的 (Cóng wǒ gèrén de jīngyàn lái kàn, zhè quèshí tǐng yǒu yìsi de - Từ trải nghiệm cá nhân của tôi, chuyện này quả thật rất thú vị)"
                ]
            }
    else:
        # ENGLISH
        if any(k in t for k in ["free", "casual", "tự do", "tán gẫu", "daily talk"]):
            return {
                "reply": "Hey there! I'm so glad to chat with you today. How is your day going so far?",
                "reply_ipa": "/heɪ ðɛr! aɪm soʊ ɡlæd tuː tʃæt wɪð juː təˈdeɪ. haʊ ɪz jʊər deɪ ˈɡoʊɪŋ soʊ fɑːr?/",
                "translation_vi": "Chào bạn! Tôi rất vui được trò chuyện cùng bạn hôm nay. Ngày hôm nay của bạn trôi qua thế nào rồi?",
                "feedback": "Cứ trò chuyện tự nhiên như hai người bạn nhé, không cần áp lực ngữ pháp!",
                "suggested_replies": [
                    "Pretty good, just having a relaxing evening. (/ˈprɪti ɡʊd, dʒʌst ˈhævɪŋ ə rɪˈlæksɪŋ ˈiːvnɪŋ/ - Khá tốt, tôi đang tận hưởng một buổi tối thư thái.)",
                    "It's been a bit busy, but I'm doing well. (/ɪts biːn ə bɪt ˈbɪzi, bʌt aɪm ˈduːɪŋ wel/ - Hôm nay hơi bận rộn một chút, nhưng tôi vẫn ổn.)",
                    "Not bad! I'm ready to practice speaking with you. (/nɑːt bæd! aɪm ˈredi tuː ˈpræktɪs ˈspiːkɪŋ wɪð juː/ - Không tệ! Tôi đã sẵn sàng luyện nói cùng bạn rồi.)"
                ]
            }
        elif any(k in t for k in ["cà phê", "quán xá", "cafe", "coffee"]):
            return {
                "reply": "I'm always down for good coffee! What's your go-to café drink or favorite spot to hang out?",
                "reply_ipa": "/aɪm ˈɔːlweɪz daʊn fər ɡʊd ˈkɔːfi! wʌts jʊər ˈɡoʊ tuː kæˈfeɪ drɪŋk ɔːr ˈfeɪvərɪt spɑːt tuː hæŋ aʊt?/",
                "translation_vi": "Tôi luôn sẵn sàng cho một tách cà phê ngon! Đồ uống 'ruột' của bạn ở quán hay nơi bạn thích ngồi tán gẫu là gì?",
                "feedback": "Talking about coffee and cafes is super natural! Share what you like to sip on.",
                "suggested_replies": [
                    "I love an iced Americano to start my busy morning. (/aɪ lʌv ən aɪst əˌmerɪˈkɑːnoʊ tuː stɑːrt maɪ ˈbɪzi ˈmɔːrnɪŋ/ - Tôi mê một ly Americano đá để khởi đầu buổi sáng bận rộn.)",
                    "I usually get a hot vanilla latte with oat milk. (/aɪ ˈjuːʒuəli ɡet ə hɑːt vəˈnɪlə ˈlɑːteɪ wɪð oʊt mɪlk/ - Tôi thường gọi một ly latte vani nóng với sữa yến mạch.)",
                    "I'm actually more of a tea person, especially matcha! (/aɪm ˈæktʃuəli mɔːr əv ə tiː ˈpɜːrsən, əˈspeʃəli ˈmætʃə/ - Thực ra tôi là người thích uống trà hơn, đặc biệt là matcha!)"
                ]
            }
        elif any(k in t for k in ["ẩm thực", "món ngon", "nấu nướng", "ăn", "food", "cooking"]):
            return {
                "reply": "Talking about delicious food always gets me excited! What is your absolute favorite comfort food?",
                "reply_ipa": "/ˈtɔːkɪŋ əˈbaʊt dɪˈlɪʃəs fuːd ˈɔːlweɪz ɡets miː ɪkˈsaɪtɪd! wʌt ɪz jʊər ˈæbsəluːt ˈfeɪvərɪt ˈkʌmfərt fuːd?/",
                "translation_vi": "Nói về đồ ăn ngon lúc nào cũng làm tôi hào hứng! Món ăn khoái khẩu nhất của bạn là gì?",
                "feedback": "Food vocabulary is great for practice. Don't hesitate to describe flavors!",
                "suggested_replies": [
                    "Nothing beats a hot bowl of traditional beef pho. (/ˈnʌθɪŋ biːts ə hɑːt boʊl əv trəˈdɪʃənl biːf fɜːr/ - Không gì sánh bằng một tô phở bò truyền thống bốc khói nghi ngút.)",
                    "I'm a huge fan of Italian pasta and crispy pizza. (/aɪm ə hjuːdʒ fæn əv ɪˈtæljən ˈpɑːstə ænd ˈkrɪspi ˈpiːtsə/ - Tôi là fan cuồng của mì Ý và pizza giòn rụm.)",
                    "I really enjoy cooking simple homemade meals every evening. (/aɪ ˈriːəli ɪnˈdʒɔɪ ˈkʊkɪŋ ˈsɪmpəl ˈhoʊmmeɪd miːlz ˈevri ˈiːvnɪŋ/ - Tôi rất thích tự nấu những bữa cơm nhà giản dị mỗi tối.)"
                ]
            }
        elif any(k in t for k in ["du lịch", "khám phá", "nghỉ dưỡng", "travel", "vacation", "trip"]):
            return {
                "reply": "Traveling is such an incredible way to explore the world! What was the most unforgettable trip you've ever had?",
                "reply_ipa": "/ˈtrævəlɪŋ ɪz sʌtʃ ən ɪnˈkredəbəl weɪ tuː ɪkˈsplɔːr ðə wɜːrld! wʌt wʌz ðə moʊst ˌʌnfərˈɡetəbəl trɪp juːv ˈevər hæd?/",
                "translation_vi": "Đi du lịch là cách tuyệt vời nhất để khám phá thế giới! Chuyến đi đáng nhớ nhất bạn từng trải nghiệm là gì?",
                "feedback": "Use past tense to share memories of your best trips!",
                "suggested_replies": [
                    "My trip to the coastal beaches was totally breathtaking. (/maɪ trɪp tuː ðə ˈkoʊstl ˈbiːtʃɪz wʌz ˈtoʊtəli ˈbreθteɪkɪŋ/ - Chuyến đi tới các bãi biển của tôi đẹp đến ngỡ ngàng.)",
                    "I love exploring vibrant city nightlife and local street food. (/aɪ lʌv ɪkˈsplɔːrɪŋ ˈvaɪbrənt ˈsɪti ˈnaɪtlaɪf ænd ˈloʊkl striːt fuːd/ - Tôi thích khám phá cuộc sống về đêm sôi động và ẩm thực đường phố.)",
                    "I'm planning an exciting road trip with friends this summer. (/aɪm ˈplænɪŋ ən ɪkˈsaɪtɪŋ roʊd trɪp wɪð frendz ðɪs ˈsʌmər/ - Tôi đang lên kế hoạch cho một chuyến phượt cùng bạn bè vào mùa hè này.)"
                ]
            }
        elif any(k in t for k in ["công việc", "sự nghiệp", "đi làm", "work", "career"]):
            return {
                "reply": "Balancing work and personal life is always a journey! How has your workday been treating you lately?",
                "reply_ipa": "/ˈbælənsɪŋ wɜːrk ænd ˈpɜːrsənl laɪf ɪz ˈɔːlweɪz ə ˈdʒɜːrni! haʊ hæz jʊər ˈwɜːrkdeɪ biːn ˈtriːtɪŋ juː ˈleɪtli?/",
                "translation_vi": "Cân bằng công việc và cuộc sống luôn là một hành trình! Công việc dạo này của bạn diễn ra thế nào?",
                "feedback": "Work topics let you practice professional and daily conversational phrases.",
                "suggested_replies": [
                    "Work has been quite productive, and my teammates are great. (/wɜːrk hæz biːn kwaɪt prəˈdʌktɪv, ænd maɪ ˈtiːmmeɪts ɑːr ɡreɪt/ - Công việc khá hiệu quả và đồng nghiệp của tôi rất tuyệt.)",
                    "Things are a bit hectic right now with upcoming deadlines. (/θɪŋz ɑːr ə bɪt ˈhektɪk raɪt naʊ wɪð ˈʌpˌkʌmɪŋ ˈdedlaɪnz/ - Mọi thứ đang hơi bận rộn một chút vì hạn chót sắp đến.)",
                    "I'm learning a lot of new skills at my current job. (/aɪm ˈlɜːrnɪŋ ə lɑːt əv nuː skɪlz æt maɪ ˈkɜːrənt dʒɑːb/ - Tôi đang học hỏi được rất nhiều kỹ năng mới ở công việc hiện tại.)"
                ]
            }
        elif any(k in t for k in ["phim", "giải trí", "rạp chiếu", "movie", "cinema", "netflix"]):
            return {
                "reply": "Watching movies is such a fantastic way to unwind! Have you seen any great films or series recently?",
                "reply_ipa": "/ˈwɑːtʃɪŋ ˈmuːviz ɪz sʌtʃ ə fænˈtæstɪk weɪ tuː ʌnˈwaɪnd! hæv juː siːn ˈɛni ɡreɪt fɪlmz ɔːr ˈsɪriːz ˈriːsntli?/",
                "translation_vi": "Xem phim đúng là cách xả stress tuyệt vời nhất! Gần đây bạn có xem bộ phim hay series nào tâm đắc không?",
                "feedback": "Talk about genres you enjoy, like sci-fi, comedy, or thrillers.",
                "suggested_replies": [
                    "I recently watched an amazing sci-fi movie with stunning visuals. (/aɪ ˈriːsntli wɑːtʃt ən əˈmeɪzɪŋ ˈsaɪfaɪ ˈmuːvi wɪð ˈstʌnɪŋ ˈvɪʒuəlz/ - Gần đây tôi vừa xem một phim khoa học viễn tưởng kỹ xảo tuyệt đẹp.)",
                    "I'm binge-watching a hilarious comedy series on Netflix. (/aɪm bɪndʒ ˈwɑːtʃɪŋ ə hɪˈlæriəs ˈkɑːmədi ˈsɪriːz ɑːn ˈnetflɪks/ - Tôi đang cày một bộ phim hài kịch cực vui trên Netflix.)",
                    "I prefer psychological thrillers that keep me guessing until the end. (/aɪ prɪˈfɜːr ˌsaɪkəˈlɑːdʒɪkl ˈθrɪlərz ðæt kiːp miː ˈɡesɪŋ ʌnˈtɪl ðiː end/ - Tôi thích phim giật gân tâm lý khiến người xem phải đoán đến phút cuối.)"
                ]
            }
        elif any(k in t for k in ["thời tiết", "đời sống", "mưa", "nắng", "weather"]):
            return {
                "reply": "How's the weather over there today? Do you prefer sunny clear skies or cool rainy days?",
                "reply_ipa": "/haʊz ðə ˈweðər ˈoʊvər ðɛr təˈdeɪ? duː juː prɪˈfɜːr ˈsʌni klɪr skaɪz ɔːr kuːl ˈreɪni deɪz?/",
                "translation_vi": "Thời tiết bên bạn hôm nay thế nào? Bạn thích trời nắng quang đãng hay những ngày mưa mát mẻ hơn?",
                "feedback": "Talking about the weather is an easy, friendly ice-breaker.",
                "suggested_replies": [
                    "It's sunny and pleasantly breezy today. (/ɪts ˈsʌni ænd ˈplezntli ˈbriːzi təˈdeɪ/ - Hôm nay trời nắng ráo và gió hiu hiu rất dễ chịu.)",
                    "I love cool autumn days when the air feels crisp. (/aɪ lʌv kuːl ˈɔːtəm deɪz wen ðiː ɛr fiːlz krɪsp/ - Tôi mê những ngày thu mát mẻ không khí trong lành.)",
                    "It's raining pretty heavily here, perfect for staying indoors. (/ɪts ˈreɪnɪŋ ˈprɪti ˈhevɪli hɪr, ˈpɜːrfɪkt fər ˈsteɪɪŋ ˌɪnˈdɔːrz/ - Chỗ tôi đang mưa khá to, rất hợp để ngồi trong nhà.)"
                ]
            }
        elif any(k in t for k in ["cuối tuần", "kế hoạch", "xả stress", "weekend"]):
            return {
                "reply": "The weekend is always something to look forward to! Do you have any fun plans coming up?",
                "reply_ipa": "/ðə ˈwiːkend ɪz ˈɔːlweɪz ˈsʌmθɪŋ tuː lʊk ˈfɔːrwərd tuː! duː juː hæv ˈɛni fʌn plænz ˈkʌmɪŋ ʌp?/",
                "translation_vi": "Cuối tuần lúc nào cũng là điều đáng mong đợi! Bạn có kế hoạch vui chơi gì sắp tới chưa?",
                "feedback": "Weekend plans are great for practicing future tenses and leisure activities.",
                "suggested_replies": [
                    "I'm planning to catch up on sleep and relax at home. (/aɪm ˈplænɪŋ tuː kætʃ ʌp ɑːn sliːp ænd rɪˈlæks æt hoʊm/ - Tôi định ngủ bù một bữa đã rồi thong thả nghỉ ngơi ở nhà.)",
                    "I'm meeting up with some close friends for dinner and drinks. (/aɪm ˈmiːtɪŋ ʌp wɪð sʌm kloʊs frendz fər ˈdɪnər ænd drɪŋks/ - Tôi sẽ tụ tập bạn thân đi ăn tối và cà phê.)",
                    "No set plans yet, just taking things as they come! (/noʊ set plænz jet, dʒʌst ˈteɪkɪŋ θɪŋz æz ðeɪ kʌm/ - Chưa có lịch gì cố định, cứ để mọi thứ tự nhiên thôi!)"
                ]
            }
        else:
            return {
                "reply": f"Awesome choice! Let's talk about '{topic}'. What comes to your mind first when you think about this?",
                "reply_ipa": f"/ˈɔːsəm tʃɔɪs! lets tɔːk əˈbaʊt ðɪs. wʌt kʌmz tuː jʊər maɪnd fɜːrst wen juː θɪŋk əˈbaʊt ɪt?/",
                "translation_vi": f"Lựa chọn tuyệt vời! Chúng ta cùng trò chuyện về '{topic}' nhé. Điều đầu tiên bạn nghĩ đến khi nhắc tới chủ đề này là gì?",
                "feedback": "Feel free to share your personal thoughts and opinions naturally!",
                "suggested_replies": [
                    "I find this topic really interesting and relevant to my daily life. (/aɪ faɪnd ðɪs ˈtɑːpɪk ˈriːəli ˈɪntrəstɪŋ ænd ˈreləvənt tuː maɪ ˈdeɪli laɪf/ - Tôi thấy chủ đề này thực sự thú vị và gắn liền với cuộc sống hàng ngày.)",
                    "I haven't thought much about it, but I'm eager to hear your take. (/aɪ hævnt θɔːt mʌtʃ əˈbaʊt ɪt, bʌt aɪm ˈiːɡər tuː hɪr jʊər teɪk/ - Tôi chưa nghĩ nhiều về nó, nhưng rất háo hức muốn nghe ý kiến của bạn.)",
                    "In my personal experience, it has both advantages and challenges. (/ɪn maɪ ˈpɜːrsənl ɪkˈspɪriəns, ɪt hæz boʊθ ədˈvæntɪdʒɪz ænd ˈtʃælɪndʒɪz/ - Theo kinh nghiệm cá nhân của tôi, nó vừa có lợi thế vừa có thách thức.)"
                ]
            }
