import json
import logging
import random
import requests

logger = logging.getLogger("ThanhBooksAI.Tutor")

SCENARIOS = {
    "en": [
        {
            "id": "cafe",
            "title": "☕ Gọi Đồ Uống Tại Quán Cà Phê (Ordering at a Café)",
            "description": "Thực hành gọi cà phê, hỏi giá, tùy chỉnh lượng đường/đá tại quán cà phê Mỹ.",
            "botRole": "Barista thân thiện tại quán Starbucks New York",
            "initialMessage": "Hi there! Welcome to Central Perk Café. What can I get started for you today?",
            "initialTranslation": "Xin chào! Chào mừng bạn đến quán Central Perk Café. Tôi có thể chuẩn bị đồ uống gì cho bạn hôm nay?"
        },
        {
            "id": "hotel",
            "title": "🏨 Nhận Phòng Khách Sạn (Hotel Check-in)",
            "description": "Luyện tập thủ tục nhận phòng, hỏi pass wifi, yêu cầu phòng view đẹp.",
            "botRole": "Lễ tân khách sạn Marriott London",
            "initialMessage": "Good afternoon, welcome to the Grand Hotel. Do you have a reservation with us?",
            "initialTranslation": "Chào buổi chiều, chào mừng quý khách đến khách sạn Grand Hotel. Quý khách đã đặt phòng trước chưa ạ?"
        },
        {
            "id": "interview",
            "title": "💼 Phỏng Vấn Xin Việc (Job Interview)",
            "description": "Luyện trả lời câu hỏi giới thiệu bản thân, điểm mạnh, kinh nghiệm làm việc.",
            "botRole": "Giám đốc nhân sự công ty công nghệ đa quốc gia",
            "initialMessage": "Thank you for taking the time to speak with me today. Could you briefly introduce yourself?",
            "initialTranslation": "Cảm ơn bạn đã dành thời gian trao đổi với tôi hôm nay. Bạn có thể giới thiệu ngắn gọn về bản thân được không?"
        },
        {
            "id": "airport",
            "title": "✈️ Phỏng Vấn Hải Quan Sân Bay (Airport Immigration)",
            "description": "Trả lời nhân viên hải quan Mỹ/Anh về mục đích chuyến đi, nơi lưu trú, vé khứ hồi.",
            "botRole": "Sĩ quan hải quan sân bay quốc tế JFK New York",
            "initialMessage": "Good morning. Passport and declaration form, please. What is the primary purpose of your visit to the United States?",
            "initialTranslation": "Chào buổi sáng. Xin vui lòng xuất trình hộ chiếu và tờ khai. Mục đích chính chuyến đi đến Mỹ của bạn là gì?"
        },
        {
            "id": "standup",
            "title": "📊 Họp Standup & Báo Cáo Với Sếp (Daily Standup Meeting)",
            "description": "Báo cáo tiến độ công việc hôm qua, dự định hôm nay và nêu khó khăn cần hỗ trợ.",
            "botRole": "Trưởng dự án kỹ thuật (Project Lead) người Mỹ vui vẻ, thực tế",
            "initialMessage": "Morning everyone! Let's do a quick round for today's standup. What did you finish yesterday and what are you tackling today?",
            "initialTranslation": "Chào buổi sáng cả đội! Chúng ta cùng điểm nhanh cuộc họp hôm nay nhé. Hôm qua bạn đã xong việc gì và hôm nay sẽ giải quyết việc gì?"
        },
        {
            "id": "refund",
            "title": "🛒 Đổi Trả Hàng & Hoàn Tiền (Store Return & Refund)",
            "description": "Phàn nàn lịch sự về sản phẩm lỗi/sai size tại cửa hàng, yêu cầu hoàn tiền vào thẻ.",
            "botRole": "Nhân viên quầy chăm sóc khách hàng tại trung tâm thương mại",
            "initialMessage": "Hi there! Welcome to Customer Service. Are you returning or exchanging an item today?",
            "initialTranslation": "Xin chào! Chào mừng bạn đến quầy Chăm sóc khách hàng. Hôm nay bạn muốn trả hàng hay đổi sang món khác ạ?"
        },
        {
            "id": "clinic",
            "title": "🩺 Đi Khám Bệnh & Nhà Thuốc (Doctor's Clinic & Pharmacy)",
            "description": "Miêu tả triệu chứng sức khỏe, cảm cúm, đau đầu cho bác sĩ và hỏi cách dùng thuốc.",
            "botRole": "Bác sĩ gia đình tận tâm tại phòng khám",
            "initialMessage": "Good afternoon. Please take a seat. What seems to be bothering you today?",
            "initialTranslation": "Chào buổi chiều. Mời bạn ngồi. Hôm nay bạn cảm thấy khó chịu ở đâu trong người?"
        },
        {
            "id": "cinema",
            "title": "🎬 Mua Vé Xem Phim & Bắp Nước (At the Cinema)",
            "description": "Chọn phim, chọn suất chiếu, chọn ghế giữa rạp và gọi combo bắp phô mai nước ngọt.",
            "botRole": "Nhân viên bán vé rạp chiếu phim AMC",
            "initialMessage": "Hey! Welcome to AMC Cinema. Which movie are you looking to watch today, and how many tickets?",
            "initialTranslation": "Xin chào! Chào mừng bạn đến rạp phim AMC. Hôm nay bạn muốn xem phim nào và cần mua mấy vé?"
        },
        {
            "id": "complaint",
            "title": "🍽️ Phàn Nàn Lịch Sự Tại Nhà Hàng (Dining & Polite Feedback)",
            "description": "Báo bồi bàn món ăn bị nguội hoặc đem nhầm món, yêu cầu làm lại và xin hóa đơn.",
            "botRole": "Quản lý nhà hàng Âu chu đáo",
            "initialMessage": "Good evening. How is everything tasting tonight? Is your steak cooked to your liking?",
            "initialTranslation": "Chào buổi tối. Các món ăn tối nay có vừa miệng quý khách không ạ? Miếng bít tết đã đúng độ chín như ý quý khách chưa?"
        },
        {
            "id": "free_chat",
            "title": "💬 Trò Chuyện Tự Do (Casual Daily Talk)",
            "description": "Tán gẫu thoải mái về sở thích, âm nhạc, phim ảnh, văn hóa cùng bạn bản xứ.",
            "botRole": "Người bạn bản xứ vui tính đến từ California",
            "initialMessage": "Hey! How's your day going so far? Doing anything fun today?",
            "initialTranslation": "Chào bạn! Ngày hôm nay của bạn thế nào rồi? Có làm gì vui không?"
        }
    ],
    "zh": [
        {
            "id": "taobao",
            "title": "🛍️ Mua Sắm & Mặc Cả Taobao / 1688 (逛街砍价)",
            "description": "Hỏi giá, kiểm tra chất lượng hàng, mặc cả giá và phí ship khi mua đồ Trung Quốc.",
            "botRole": "Chủ shop quần áo nhiệt tình tại chợ Bạch Mã, Quảng Châu",
            "initialHanzi": "帅哥/美女，来看衣服啊！这款是今年最流行的，质量非常好，想看看哪件？",
            "initialPinyin": "Shuàigē/Měinǚ, lái kàn yīfu a! Zhè kuǎn shì jīnnián zuì liúxíng de, zhìliàng fēicháng hǎo, xiǎng kànkan nǎ jiàn?",
            "initialTranslation": "Soái ca / Người đẹp ơi, vào xem đồ đi! Mẫu này đang hot nhất năm nay, chất lượng cực tốt, bạn muốn xem cái nào?"
        },
        {
            "id": "restaurant",
            "title": "🥟 Đi Ăn Tại Nhà Hàng Trung Quốc (在餐厅点餐)",
            "description": "Gọi món ăn, hỏi độ cay, gọi thêm trà và tính tiền tại nhà hàng Bắc Kinh.",
            "botRole": "Bồi bàn nhanh nhẹn tại nhà hàng Vịt quay Bắc Kinh",
            "initialHanzi": "您好！欢迎光临全聚德。请问您几位？今天想吃点什么特色菜？",
            "initialPinyin": "Nín hǎo! Huānyíng guānglín Quánjùdé. Qǐngwèn nín jǐ wèi? Jīntiān xiǎng chī diǎn shénme tèsè cài?",
            "initialTranslation": "Xin chào quý khách! Chào mừng đến Toàn Tụ Đức. Xin hỏi quý khách đi mấy người? Hôm nay muốn dùng món đặc sản gì ạ?"
        },
        {
            "id": "factory",
            "title": "🏭 Đàm Phán Xưởng & Nhà Máy Trung Quốc (工厂询盘谈判)",
            "description": "Hỏi giá sỉ số lượng lớn, yêu cầu gửi mẫu (sample), tiến độ sản xuất và thanh toán.",
            "botRole": "Giám đốc kinh doanh xưởng gia công tại Thâm Quyến",
            "initialHanzi": "老板你好！很高兴认识您。请问您看中哪款产品？大概需要多少起订量（MOQ）？",
            "initialPinyin": "Lǎobǎn nǐ hǎo! Hěn gāoxìng rènshi nín. Qǐngwèn nín kànzhòng nǎ kuǎn chǎnpǐn? Dàgài xūyào duōshao qǐdìngliàng (MOQ)?",
            "initialTranslation": "Chào ông chủ! Rất vui được biết bạn. Xin hỏi bạn đang ưng mẫu sản phẩm nào? Số lượng đặt hàng tối thiểu dự kiến khoảng bao nhiêu?"
        },
        {
            "id": "didi",
            "title": "🚕 Đi Taxi / Bắt Xe Didi & Chỉ Đường (打车与指路)",
            "description": "Xác nhận điểm đón xe, bảo tài xế đi đường cao tốc, rẽ trái/phải, dừng xe tính tiền.",
            "botRole": "Tài xế Didi nhiệt tình tại Thượng Hải",
            "initialHanzi": "师傅到了！尾号8897对吧？看定位是去虹桥高铁站，走高架桥比较快，可以吗？",
            "initialPinyin": "Shīfu dào le! Wěihào bābājiǔqī duì ba? Kàn dìngwèi shì qù Hóngqiáo Gāotiězhàn, zǒu gāojiàqiáo bǐjiào kuài, kěyǐ ma?",
            "initialTranslation": "Tài xế tới rồi! 4 số cuối điện thoại là 8897 đúng không? Điểm đến là ga tàu Hồng Kiều, đi cầu vượt trên cao sẽ nhanh hơn, được không bạn?"
        },
        {
            "id": "haidilao",
            "title": "🍲 Ăn Lẩu Haidilao & Gọi Trà Sữa (吃火锅喝奶茶)",
            "description": "Chọn nước lẩu cà chua/cay tê, pha nước chấm, chọn độ ngọt và đá trà sữa.",
            "botRole": "Phục vụ viên Haidilao chu đáo",
            "initialHanzi": "欢迎光临海底捞！请问今天锅底想要番茄牛尾的还是麻辣清油的？先给您倒杯酸梅汤吧！",
            "initialPinyin": "Huānyíng guānglín Hǎidǐlāo! Qǐngwèn jīntiān guōdǐ xiǎng yào fānqié niúwěi de háishì málà qīngyóu de? Xiān gěi nín dào bēi suānméitāng ba!",
            "initialTranslation": "Chào mừng đến Haidilao! Hôm nay bạn muốn dùng nước lẩu đuôi bò cà chua hay lẩu cay thanh dầu? Để em rót cho bạn cốc nước mơ chua giải nhiệt trước nhé!"
        },
        {
            "id": "pharmacy",
            "title": "🏥 Đi Hiệu Thuốc & Mua Thuốc (药店问药)",
            "description": "Miêu tả triệu chứng cảm sốt, đau họng, đau dạ dày và hỏi liều lượng uống thuốc.",
            "botRole": "Dược sĩ tư vấn tại nhà thuốc Bắc Kinh",
            "initialHanzi": "你好！看你脸色不太好，是哪里不舒服？发烧还是嗓子疼？",
            "initialPinyin": "Nǐ hǎo! Kàn nǐ liǎnsè bú tài hǎo, shì nǎlǐ bù shūfu? Fāshāo háishì sǎngzi téng?",
            "initialTranslation": "Chào bạn! Thấy sắc mặt bạn hơi nhợt nhạt, bạn đang khó chịu ở đâu? Có bị sốt hay đau họng không?"
        },
        {
            "id": "rent",
            "title": "🏢 Thuê Căn Hộ & Phòng Trọ (租房看房)",
            "description": "Hỏi giá thuê phòng theo tháng, tiền đặt cọc, tiền điện nước, kiểm tra nội thất.",
            "botRole": "Môi giới nhà đất nhiệt tình tại Quảng Châu",
            "initialHanzi": "你好！这套一室一厅采光非常好，家具家电全配齐，押一付一，想今天实地看看房吗？",
            "initialPinyin": "Nǐ hǎo! Zhè tào yíshìyìtīng cǎiguāng fēicháng hǎo, jiājù jiādiàn quán pèiqí, yā yī fù yī, xiǎng jīntiān shídì kànkan fáng ma?",
            "initialTranslation": "Chào bạn! Căn 1 phòng ngủ 1 phòng khách này đón ánh sáng cực tốt, đầy đủ nội thất đồ điện, cọc 1 đóng 1 tháng, bạn có muốn qua xem nhà trực tiếp hôm nay không?"
        },
        {
            "id": "salon",
            "title": "💇 Cắt Tóc & Tạo Kiểu Salon (理发做造型)",
            "description": "Yêu cầu thợ cắt tóc chỉ tỉa bớt ngọn tóc, không cắt quá ngắn, nhuộm màu tự nhiên.",
            "botRole": "Nhà tạo mẫu tóc chuyên nghiệp tại Salon",
            "initialHanzi": "帅哥/美女请坐！今天想怎么剪？是要换个新发型还是只稍微修剪一下？",
            "initialPinyin": "Shuàigē/Měinǚ qǐng zuò! Jīntiān xiǎng zěnme jiǎn? Shì yào huàn ge xīn fàxíng háishì zhǐ shāowēi xiūjiǎn yíxià?",
            "initialTranslation": "Mời bạn ngồi! Hôm nay bạn muốn cắt thế nào? Muốn đổi kiểu tóc mới hay chỉ tỉa gọn lại một chút thôi?"
        },
        {
            "id": "travel",
            "title": "🚄 Du Lịch & Hỏi Đường Ga Tàu (旅行问路)",
            "description": "Hỏi đường đến ga tàu cao tốc, mua vé tàu, hỏi cửa kiểm soát vé.",
            "botRole": "Người dân bản địa nhiệt tình tại Thượng Hải",
            "initialHanzi": "你好！看你在看地图，是去高铁站吗？需要我帮忙指路吗？",
            "initialPinyin": "Nǐ hǎo! Kàn nǐ zài kàn dìtú, shì qù gāotiě zhàn ma? Xūyào wǒ bāngmáng zhǐlù ma?",
            "initialTranslation": "Chào bạn! Thấy bạn đang xem bản đồ, bạn định đi ga tàu cao tốc à? Cần tôi chỉ đường giúp không?"
        },
        {
            "id": "free_zh",
            "title": "💬 Tán Gẫu Đời Thường Tiếng Trung (日常闲聊)",
            "description": "Luyện phản xạ giao tiếp tự nhiên, luyện thanh điệu và ngữ pháp tiếng Trung cơ bản.",
            "botRole": "Bạn học người Trung Quốc vui vẻ, kiên nhẫn",
            "initialHanzi": "你好啊！很高兴和你练习中文。你学中文多久了？平时最喜欢做什么？",
            "initialPinyin": "Nǐ hǎo a! Hěn gāoxìng hé nǐ liànxí Zhōngwén. Nǐ xué Zhōngwén duōjiǔ le? Píngshí zuì xǐhuan zuò shénme?",
            "initialTranslation": "Chào bạn nhé! Rất vui được cùng bạn luyện tập tiếng Trung. Bạn học tiếng Trung được bao lâu rồi? Bình thường bạn thích làm gì nhất?"
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

    if lang == "zh":
        system_inst = """Bạn là một gia sư AI dạy tiếng Trung Quốc bản ngữ (Bắc Kinh) cực kỳ tự nhiên, thông minh và nhạy bén.
Nhiệm vụ của bạn:
1. Trả lời người học tự nhiên theo đúng bối cảnh hội thoại, đặt câu hỏi gợi mở tiếp theo.
2. CỰC KỲ QUAN TRỌNG VỀ GỢI Ý (suggested_replies):
   - Phải tạo ra 3 câu gợi ý hoàn toàn mới, phản hồi TRỰC TIẾP cho câu vừa rồi của bạn.
   - 3 câu phải đại diện cho 3 hướng trả lời KHÁC NHAU:
     + Hướng 1: Đồng ý / Chọn một lựa chọn cụ thể
     + Hướng 2: Hỏi thêm chi tiết / Thắc mắc / Mặc cả thêm
     + Hướng 3: Đổi ý / Từ chối nhẹ nhàng / Đề xuất phương án khác
   - TUYỆT ĐỐI KHÔNG lặp lại các câu gợi ý thông thường sáo rỗng.
3. Xuất JSON hợp lệ:
   - "reply_hanzi": Câu tiếng Trung (chữ Hán Giản thể).
   - "reply_pinyin": Phiên âm Pinyin kèm thanh điệu.
   - "translation_vi": Dịch nghĩa tiếng Việt tự nhiên.
   - "feedback": Nhận xét ngắn gọn về ngữ pháp/từ vựng/lượng từ của người dùng bằng tiếng Việt.
   - "suggested_replies": Mảng 3 chuỗi, mỗi chuỗi có dạng: "Chữ Hán (Pinyin - Nghĩa tiếng Việt)".
"""
    else:
        system_inst = """You are an engaging, highly adaptive native English language coach.
Your tasks:
1. Respond naturally to keep the roleplay flow going, asking a follow-up question.
2. CRITICAL FOR SUGGESTED REPLIES (suggested_replies):
   - You MUST provide 3 completely fresh, dynamic options directly responding to your latest question.
   - The 3 options must cover 3 DISTINCT conversational intents:
     + Option 1: Direct confirmation / Making a specific choice
     + Option 2: Asking for details / Inquiring for options or customization
     + Option 3: Politeness / Hesitation / Suggesting an alternative
   - NEVER repeat generic suggestions. Keep them sharp, idiomatic, and lively.
3. Output strictly valid JSON:
   - "reply": Natural English response.
   - "translation_vi": Natural Vietnamese translation.
   - "feedback": Brief helpful tip in Vietnamese on natural phrasing or grammar.
   - "suggested_replies": Array of 3 natural, specific conversational phrases the user can say next.
"""

    try:
        raw_res = call_gemini_api(api_key, current_history, system_inst, preferred_model=preferred_model)
        parsed = json.loads(raw_res)
        return parsed
    except Exception as e:
        logger.warning(f"Gemini API không phản hồi ({e}), chuyển sang động cơ mô phỏng ngữ cảnh linh động.")
        return get_dynamic_offline_response(user_text, lang, scenario_id, turn_count, error_note=str(e))

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
                 "Mẫu này phom hơi rộng một chút. Xin hỏi bạn cao bao nhiêu và nặng bao nhiêu kg? Mình lấy size vừa vặn nhất cho bạn! Còn màu đen và be nữa nhé.")
            ]
            chosen = replies[0]
            suggestions = [
                "我身高1米75，体重65公斤 (Wǒ shēngāo 1 mǐ 75, tǐzhòng 65 gōngjīn - Em cao 1m75, nặng 65 cân)",
                "我想试一下黑色L号的 (Wǒ xiǎng shì yíxià hēisè L hào de - Em muốn thử chiếc màu đen size L)",
                "如果尺码不合身可以退换吗？ (Rúguǒ chǐmǎ bù héshēn kěyǐ tuìhuàn ma? - Nếu size không vừa có được đổi trả không?)"
            ]
            feedback = "Khi nói về chiều cao cân nặng trong tiếng Trung: dùng '米' (mét) và '公斤' (kilogram)."

        elif any(k in text for k in ["买", "要", "单", "付", "微信", "支付宝", "lấy", "mua"]):
            replies = [
                ("太棒了！这就帮您包起来。支持微信或者支付宝扫码付款，您扫墙上的收款码就可以！",
                 "Tài bàng le! Zhè jiù bāng nín bāo qǐlai. Zhīchí Wēixìn huòzhě Zhīfùbǎo sǎomǎ fùkuǎn, nín sǎo qiáng shàng de shōukuǎnmǎ jiù kěyǐ!",
                 "Tuyệt vời quá! Mình gói lại cho bạn ngay đây. Hỗ trợ quét mã Wechat hoặc Alipay nhé, bạn quét mã thu tiền trên tường là được!")
            ]
            chosen = replies[0]
            suggestions = [
                "已经扫码付款了，你查收一下 (Yǐjīng sǎomǎ fùkuǎn le, nǐ cháshōu yíxià - Em đã quét mã thanh toán rồi, bạn kiểm tra nhé)",
                "请问可以开一张发票吗？ (Qǐngwèn kěyǐ kāi yì zhāng fāpiào ma? - Cho hỏi có thể xuất hóa đơn cho em được không?)",
                "帮我装个结实点的袋子 (Bāng wǒ zhuāng ge jiēshi diǎn de dàizi - Cho em vào cái túi chắc chắn một chút)"
            ]
            feedback = "Ở Trung Quốc hiện nay 99% thanh toán bằng '微信' (Wechat) hoặc '支付宝' (Alipay) qua hình thức '扫码' (quét mã)."

        else:
            replies = [
                ("你看中哪一件了？这一排都是今年秋季爆款，手感特别舒适，你可以摸摸面料！",
                 "Nǐ kànzhòng nǎ yí jiàn le? Zhè yì pái dōushì jīnnián qiūjì bàokuǎn, shǒugǎn tèbié shūshì, nǐ kěyǐ mōmo miànliào!",
                 "Bạn ưng chiếc nào rồi? Cả dãy này đều là hàng hot hit mùa thu năm nay, sờ vải cực êm, bạn chạm thử chất vải xem!")
            ]
            chosen = replies[0]
            suggestions = [
                "这件外套多少钱？能试穿吗？ (Zhè jiàn wàitào duōshao qián? Néng shìchuān ma? - Cái áo khoác này bao nhiêu tiền? Thử được không?)",
                "这款有没有白色的现货？ (Zhè kuǎn yǒu méiyǒu báisè de xiànhuò? - Mẫu này có sẵn màu trắng không?)",
                "这个面料容易起球吗？ (Zhège miànliào róngyì qǐqiú ma? - Chất vải này có dễ bị xù lông không?)"
            ]
            feedback = "Từ '爆款' (bàokuǎn) là tiếng lóng thương mại điện tử Trung Quốc cực kỳ phổ biến, nghĩa là 'mặt hàng bán siêu chạy/hot trend'."

    # 2. NHÀ HÀNG ĂN UỐNG (在餐厅点餐)
    elif scenario == "restaurant":
        if any(k in text for k in ["辣", "cay", "chili", "hot"]):
            replies = [
                ("没问题！后厨可以做微辣或者免辣。除了烤鸭，要不要尝尝我们的水煮牛肉和清炒芥兰？",
                 "Méi wèntí! Hòuchú kěyǐ zuò wēilà huòzhě miǎnlà. Chúle kǎoyā, yào bu yào chángchang wǒmen de shuǐzhǔ niúròu hé qīngchǎo jièlán?",
                 "Không thành vấn đề! Nhà bếp có thể làm cay nhẹ hoặc không cay. Ngoài vịt quay, bạn có muốn thử thêm món bò cay Tứ Xuyên và cải xào không?")
            ]
            chosen = replies[0]
            suggestions = [
                "就要微辣的，少放一点油 (Jiù yào wēilà de, shǎo fàng yìdiǎn yóu - Cho em cay nhẹ thôi, bớt dầu mỡ nhé)",
                "清炒芥兰来一份，再要两碗米饭 (Qīngchǎo jièlán lái yí fèn, zài yào liǎng wǎn mǐfàn - Cho 1 phần cải xào, thêm 2 bát cơm trắng)",
                "你们有清淡一点的汤推荐吗？ (Nǐmen yǒu qīngdàn yìdiǎn de tāng tuījiàn ma? - Quán có món canh nào thanh đạm gợi ý không?)"
            ]
            feedback = "Trong ẩm thực Trung Hoa: '免辣' (miǎnlà) = không cay, '微辣' (wēilà) = cay nhẹ, '中辣' (zhōnglà) = cay vừa, '特辣' (tèlà) = siêu cay."

        elif any(k in text for k in ["买单", "结账", "多少钱", "tiền", "bill", "pay"]):
            replies = [
                ("您好，总共是268元。您扫桌子角上的二维码就可以直接结账，也可以到前台刷卡！",
                 "Nín hǎo, zǒnggòng shì 268 yuán. Nín sǎo zhuōzi jiǎo shàng de èrwéimǎ jiù kěyǐ zhíjiē jiézhàng, yě kěyǐ dào qiántái shuākǎ!",
                 "Dạ của quý khách tổng cộng là 268 tệ. Bạn quét mã QR ở góc bàn là thanh toán được ngay, hoặc ra quầy lễ tân quẹt thẻ ạ!")
            ]
            chosen = replies[0]
            suggestions = [
                "好的，我已经扫码付好了 (Hǎo de, wǒ yǐjīng sǎomǎ fù hǎo le - Dạ vâng, em quét mã trả xong rồi ạ)",
                "吃不完的菜可以帮我打包吗？ (Chī bù wán de cài kěyǐ bāng wǒ dǎbāo ma? - Thức ăn chưa hết gói mang về giúp em được không?)",
                "请问停车可以免费领停车券吗？ (Qǐngwèn tíngchē kěyǐ miǎnfèi lǐng tíngchēquàn ma? - Cho hỏi gửi xe có được phát phiếu đỗ xe miễn phí không?)"
            ]
            feedback = "Từ '打包' (dǎbāo) rất hữu ích khi đi ăn ở Trung Quốc, có nghĩa là gói đồ ăn thừa mang về."

        else:
            replies = [
                ("您好！我们店的招牌全聚德挂炉烤鸭是必点的，皮脆肉嫩，配荷叶饼和大葱。请问您要半只还是一整只？",
                 "Nín hǎo! Wǒmen diàn de zhāopái Quánjùdé guàlú kǎoyā shì bì diǎn de, pí cuì ròu nèn, pèi héyèbǐng hé dàcōng. Qǐngwèn nín yào bàn zhī háishì yì zhěng zhī?",
                 "Chào bạn! Vịt quay lò treo đặc sản Toàn Tụ Đức của tiệm em là món nhất định phải thử, da giòn thịt mềm ăn kèm bánh tráng và hành hoa. Quý khách muốn dùng nửa con hay cả con ạ?")
            ]
            chosen = replies[0]
            suggestions = [
                "先来半只烤鸭尝尝 (Xiān lái bàn zhī kǎoyā chángchang - Cho em nửa con vịt quay ăn thử trước nhé)",
                "烤鸭大概需要等多久？ (Kǎoyā dàgài xūyào děng duōjiǔ? - Vịt quay làm có lâu không, đợi khoảng bao lâu?)",
                "除了烤鸭，还有什么特色凉菜？ (Chúle kǎoyā, hái yǒu shénme tèsè liángcài? - Ngoài vịt quay còn món nguội khai vị đặc sắc nào không?)"
            ]
            feedback = "Lượng từ cho vịt/gà là '只' (zhī). Nửa con là '半只' (bàn zhī), cả con là '整只' (zhěng zhī)."

    # 3. DU LỊCH & TÀU CAO TỐC (旅行问路)
    elif scenario == "travel":
        if any(k in text for k in ["票", "买", "vé", "ticket"]):
            replies = [
                ("如果你去人工窗口买票，出示护照就可以。现在大部分人都在手机上用12306软件买，直接刷护照就能进站！",
                 "Rúguǒ nǐ qù réngōng chuāngkǒu mǎi piào, chūshì hùzhào jiù kěyǐ. Xiànzài dàbùfen rén dōu zài shǒujī shàng yòng 12306 ruǎnjiàn mǎi, zhíjiē shuā hùzhào jiù néng jìnzhàn!",
                 "Nếu bạn ra quầy nhân viên mua vé, chỉ cần xuất trình hộ chiếu là được. Giờ đa phần người ta mua trên app 12306 điện thoại, quét trực tiếp hộ chiếu là vào ga!")
            ]
            chosen = replies[0]
            suggestions = [
                "去北京的高铁最早是几点？ (Qù Běijīng de gāotiě zuìzǎo shì jǐ diǎn? - Chuyến tàu cao tốc sớm nhất đi Bắc Kinh là mấy giờ?)",
                "二等座和一等座有什么区别？ (Èrděngzuò hé yīděngzuò yǒu shénme qūbié? - Vé hạng nhì và hạng nhất khác nhau thế nào?)",
                "进站需要提前多长时间安检？ (Jìnzhàn xūyào tíqián duō cháng shíjiān ānjiǎn? - Vào ga cần đến trước bao lâu để soi chiếu an ninh?)"
            ]
            feedback = "Tàu cao tốc Trung Quốc chia làm các hạng vé: '二等座' (hạng nhì phổ thông), '一等座' (hạng nhất), và '商务座' (hạng thương gia)."
        else:
            replies = [
                ("去高铁站很方便！你出门往右走两百米坐地铁2号线，直达火车站南广场，大概只要20分钟。",
                 "Qù gāotiě zhàn hěn fāngbiàn! Nǐ chūmén wǎng yòu zǒu liǎngbǎi mǐ zuò dìtiě 2 hào xiàn, zhídá huǒchēzhàn nán guǎngchǎng, dàgài zhǐ yào 20 fēnzhōng.",
                 "Đi ra ga tàu cao tốc tiện lắm! Bạn ra cửa rẽ phải 200m đi tàu điện ngầm tuyến số 2, đến thẳng quảng trường phía Nam ga tàu, chỉ mất khoảng 20 phút thôi.")
            ]
            chosen = replies[0]
            suggestions = [
                "地铁票要在哪里买？可以用手机扫码吗？ (Dìtiě piào yào zài nǎlǐ mǎi? Kěyǐ yòng shǒujī sǎomǎ ma? - Mua vé tàu điện ở đâu ạ? Dùng điện thoại quét mã được không?)",
                "如果打出租车大概要多少钱？ (Rúguǒ dǎ chūzūchē dàgài yào duōshao qián? - Nếu bắt taxi đi thì hết khoảng bao nhiêu tiền?)",
                "附近有能寄存行李的地方吗？ (Fùjìn yǒu néng jìcún xíngli de dìfang ma? - Gần đây có chỗ nào gửi hành lý không ạ?)"
            ]
            feedback = "Chỉ phương hướng: '往右走' (rẽ phải), '往左走' (rẽ trái), '往前走' (đi thẳng)."

    # 4. TÁN GẪU ĐỜI THƯỜNG (日常闲聊)
    else:
        replies = [
            ("哇，你的中文发音很有感觉啊！平时你是通过看电视剧还是听歌自学的？中国人常说'熟能生巧'，多说很快就能流利了！",
             "Wa, nǐ de Zhōngwén fāyīn hěn yǒu gǎnjué a! Píngshí nǐ shì tōngguò kàn diànshìjù háishì tīng gē zìxué de? Zhōngguórén cháng shuō 'shú néng shēng qiǎo', duō shuō hěn kuài jiù néng liúlì le!",
             "Oa, phát âm tiếng Trung của bạn có chất giọng đấy chứ! Bình thường bạn tự học qua xem phim hay nghe nhạc thế? Người Trung Quốc hay nói 'Trăm hay không bằng tay quen', cứ nói nhiều là trôi chảy ngay thôi!"),
            ("哈哈，很有意思！中国很大，各个地方的美食和口音都很不一样。如果让你选，你最想去中国的哪个城市旅行？",
             "Hāhā, hěn yǒu yìsi! Zhōngguó hěn dà, gège dìfang de měishí hé kǒuyīn dōu hěn bù yíyàng. Rúguǒ ràng nǐ xuǎn, nǐ zuì xiǎng qù Zhōngguó de nǎge chéngshì lǚxíng?",
             "Haha, thú vị ghê! Trung Quốc rất rộng lớn, ẩm thực và giọng điệu mỗi nơi đều rất khác nhau. Nếu được chọn, bạn muốn đi du lịch thành phố nào nhất?")
        ]
        chosen = random.choice(replies)
        suggestions = [
            "我非常想去北京看故宫和长城 (Wǒ fēicháng xiǎng qù Běijīng kàn Gùgōng hé Chángchéng - Mình rất muốn đi Bắc Kinh thăm Cố Cung và Vạn Lý Trường Thành)",
            "我平时很喜欢看中国电影和短视频 (Wǒ píngshí hěn xǐhuan kàn Zhōngguó diànyǐng hé duǎnshìpín - Bình thường mình rất thích xem phim và video ngắn Trung Quốc)",
            "能推荐几个适合新手学的汉语成语吗？ (Néng tuījiàn jǐ ge shìhé xīnshǒu xué de Hànyǔ chéngyǔ ma? - Bạn gợi ý cho mình vài thành ngữ tiếng Hán dễ học được không?)"
        ]
        feedback = "Thành ngữ '熟能生巧' (shú néng shēng qiǎo) tương đương câu tục ngữ tiếng Việt 'Trăm hay không bằng tay quen' - luyện tập nhiều ắt sẽ giỏi."

    return {
        "reply_hanzi": chosen[0],
        "reply_pinyin": chosen[1],
        "translation_vi": chosen[2],
        "feedback": feedback,
        "suggested_replies": suggestions
    }

def _resolve_english_dynamic(text: str, scenario: str, turn: int):
    if scenario == "cafe":
        if any(k in text for k in ["latte", "cappuccino", "coffee", "tea", "americano", "mocha"]):
            replies = [
                ("Great choice! What size would you prefer: Tall, Grande, or Venti? And would you like whole milk, skim, or an alternative like oat milk?",
                 "Lựa chọn tuyệt vời! Bạn muốn cỡ nào: Nhỏ (Tall), Vừa (Grande) hay Lớn (Venti)? Và bạn muốn dùng sữa tươi béo, sữa tách béo hay sữa hạt như sữa yến mạch ạ?")
            ]
            suggestions = [
                "I'll have a medium (Grande) with oat milk, please.",
                "Could I get that iced with sugar-free vanilla syrup?",
                "Do you have any decaf options available today?"
            ]
            feedback = "In American coffee shops, sizes are often called: Tall (Small), Grande (Medium), and Venti (Large)."
        elif any(k in text for k in ["size", "milk", "oat", "ice", "sugar", "sweet"]):
            replies = [
                ("Got it! One iced latte with oat milk. Would you like any extra espresso shots, or perhaps a fresh blueberry muffin to go with that?",
                 "Đã ghi nhận! Một latte đá sữa yến mạch. Bạn có muốn thêm một shot cà phê đậm đặc, hoặc bánh nướng việt quất dùng kèm không ạ?")
            ]
            suggestions = [
                "Just the coffee for me, thank you!",
                "A warm blueberry muffin sounds delicious, add one please.",
                "How much does that come to in total?"
            ]
            feedback = "When declining an add-on politely, native speakers often say: 'Just the coffee for me, thank you!' rather than a flat 'No'."
        elif any(k in text for k in ["how much", "cost", "total", "pay", "card", "cash"]):
            replies = [
                ("That'll be $5.85 in total. You can tap your card or phone right on the reader whenever you're ready!",
                 "Tổng của bạn là $5.85. Bạn có thể quẹt thẻ hoặc chạm điện thoại vào máy thanh toán bất cứ khi nào sẵn sàng nhé!")
            ]
            suggestions = [
                "Here you go, paying with Apple Pay.",
                "Could I please get a receipt for this?",
                "Keep the change, have a wonderful day!"
            ]
            feedback = "Contactless payment is usually referred to as 'tapping' (e.g., 'You can tap your card here')."
        else:
            replies = [
                ("Welcome! We have our seasonal pumpkin spice latte on special today, or our classic cold brew. What catches your eye?",
                 "Chào bạn! Hôm nay chúng tôi có món đặc biệt là latte bí ngô quế, hoặc cà phê ủ lạnh truyền thống. Bạn thích món nào hơn?")
            ]
            suggestions = [
                "Could you tell me what the pumpkin spice latte tastes like?",
                "I'd love a classic iced Americano, black please.",
                "What's your most popular drink here?"
            ]
            feedback = "Asking 'What catches your eye?' is a friendly idiom meaning 'What looks appealing to you?'"

    elif scenario == "hotel":
        if any(k in text for k in ["reservation", "booked", "name", "passport", "id"]):
            replies = [
                ("I found your booking right here! You're booked for 3 nights in an Executive King room. May I please see your passport and a credit card for the room deposit?",
                 "Tôi đã tìm thấy đơn đặt phòng của quý khách! Phòng Executive giường King cho 3 đêm. Quý khách vui lòng cho tôi mượn hộ chiếu và thẻ tín dụng để đặt cọc phòng nhé ạ?")
            ]
            suggestions = [
                "Here is my passport and credit card.",
                "Could I request a quiet room on a higher floor?",
                "Is buffet breakfast included in my booking?"
            ]
            feedback = "Hotels will almost always ask for a 'deposit' (tiền đặt cọc) or 'pre-authorization' for incidentals."
        elif any(k in text for k in ["wifi", "breakfast", "key", "elevator", "floor"]):
            replies = [
                ("Here are your room keycards for Room 1204 on the 12th floor. Elevators are just to your left. Breakfast is served from 6:30 to 10:00 AM on the 2nd floor, and Wi-Fi is complimentary with your room number!",
                 "Đây là thẻ từ phòng 1204 tại tầng 12 của quý khách. Thang máy ở ngay bên tay trái. Bữa sáng phục vụ từ 6:30 đến 10:00 sáng tại tầng 2, và Wi-Fi miễn phí theo số phòng ạ!")
            ]
            suggestions = [
                "What is the checkout time on our last day?",
                "Where is the swimming pool and fitness center?",
                "Thank you so much for your warm hospitality!"
            ]
            feedback = "The word 'complimentary' is the elegant hotel term for 'free of charge' (miễn phí)."
        else:
            replies = [
                ("Good afternoon! Welcome to the Grand Hotel. Are you checking in today, or can I assist you with concierge services?",
                 "Chào buổi chiều! Chào mừng quý khách đến khách sạn Grand Hotel. Quý khách muốn làm thủ tục nhận phòng hay cần hỗ trợ dịch vụ gì ạ?")
            ]
            suggestions = [
                "Yes, I'm checking in today under the name of Thanh.",
                "I have a reservation booked through Agoda.",
                "Do you have early check-in available right now?"
            ]
            feedback = "When giving your name at a hotel check-in, say: 'I have a reservation under the name of [Your Name]'."

    elif scenario == "interview":
        replies = [
            ("That's very insightful! In this role, we value adaptability and strong communication. Can you tell me about a time you faced a difficult challenge at work and how you overcame it?",
             "Thật sâu sắc! Ở vị trí này, chúng tôi rất coi trọng sự thích nghi và kỹ năng giao tiếp tốt. Bạn có thể chia sẻ về một thử thách khó khăn trong công việc mà bạn đã vượt qua được không?")
        ]
        suggestions = [
            "In my previous project, we faced a tight deadline and resolved it by prioritizing core deliverables.",
            "I believe clear communication and active listening helped our team navigate conflicts smoothly.",
            "Could you share more about the typical day-to-day responsibilities in this position?"
        ]
        feedback = "The STAR method (Situation, Task, Action, Result) is the standard framework for answering behavioral interview questions."

    else:
        replies = [
            ("That's super cool! I love hearing about different perspectives. Speaking of which, have you been following any good TV shows, movies, or podcasts lately?",
             "Tuyệt vời quá! Tôi rất thích lắng nghe những góc nhìn mới. Nhân tiện, dạo này bạn có đang theo dõi bộ phim, chương trình hay podcast thú vị nào không?")
        ]
        suggestions = [
            "I've been binge-watching a great sci-fi documentary series recently.",
            "I mostly enjoy listening to history and technology podcasts while walking.",
            "Not really, I've been quite busy with work lately. How about you?"
        ]
        feedback = "The phrasal verb 'binge-watching' means watching multiple episodes of a series in rapid succession (cày phim)."

    chosen = replies[0]
    return {
        "reply": chosen[0],
        "translation_vi": chosen[1],
        "feedback": feedback,
        "suggested_replies": suggestions
    }
