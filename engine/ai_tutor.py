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
            "initialTranslation": "Xin chào! Chào mừng bạn đến quán Central Perk Café. Tôi có thể chuẩn bị đồ uống gì cho bạn hôm nay?",
            "initialSuggestions": [
                "Could I get a hot cappuccino with oat milk, please?",
                "What kind of signature drinks or pastries do you recommend here?",
                "Just looking at the menu for a moment, thank you!"
            ]
        },
        {
            "id": "hotel",
            "title": "🏨 Nhận Phòng Khách Sạn (Hotel Check-in)",
            "description": "Luyện tập thủ tục nhận phòng, hỏi pass wifi, yêu cầu phòng view đẹp.",
            "botRole": "Lễ tân khách sạn Marriott London",
            "initialMessage": "Good afternoon, welcome to the Grand Hotel. Do you have a reservation with us?",
            "initialTranslation": "Chào buổi chiều, chào mừng quý khách đến khách sạn Grand Hotel. Quý khách đã đặt phòng trước chưa ạ?",
            "initialSuggestions": [
                "Yes, I have a reservation under the name Thanh.",
                "No, do you have any single rooms available for two nights?",
                "Could I check in a bit early, please?"
            ]
        },
        {
            "id": "interview",
            "title": "💼 Phỏng Vấn Xin Việc (Job Interview)",
            "description": "Luyện trả lời câu hỏi giới thiệu bản thân, điểm mạnh, kinh nghiệm làm việc.",
            "botRole": "Giám đốc nhân sự công ty công nghệ đa quốc gia",
            "initialMessage": "Thank you for taking the time to speak with me today. Could you briefly introduce yourself?",
            "initialTranslation": "Cảm ơn bạn đã dành thời gian trao đổi với tôi hôm nay. Bạn có thể giới thiệu ngắn gọn về bản thân được không?",
            "initialSuggestions": [
                "Certainly! I have over five years of experience in project management.",
                "Thank you for having me. My background is in digital marketing and sales.",
                "Sure! I'm passionate about technology and solving customer problems."
            ]
        },
        {
            "id": "airport",
            "title": "✈️ Phỏng Vấn Hải Quan Sân Bay (Airport Immigration)",
            "description": "Trả lời nhân viên hải quan Mỹ/Anh về mục đích chuyến đi, nơi lưu trú, vé khứ hồi.",
            "botRole": "Sĩ quan hải quan sân bay quốc tế JFK New York",
            "initialMessage": "Good morning. Passport and declaration form, please. What is the primary purpose of your visit to the United States?",
            "initialTranslation": "Chào buổi sáng. Xin vui lòng xuất trình hộ chiếu và tờ khai. Mục đích chính chuyến đi đến Mỹ của bạn là gì?",
            "initialSuggestions": [
                "Here you go. I'm here for sightseeing and traveling for two weeks.",
                "I'm visiting on business to attend a tech conference in San Francisco.",
                "I'm visiting some friends and relatives in California for ten days."
            ]
        },
        {
            "id": "standup",
            "title": "📊 Họp Standup & Báo Cáo Với Sếp (Daily Standup Meeting)",
            "description": "Báo cáo tiến độ công việc hôm qua, dự định hôm nay và nêu khó khăn cần hỗ trợ.",
            "botRole": "Trưởng dự án kỹ thuật (Project Lead) người Mỹ vui vẻ, thực tế",
            "initialMessage": "Morning everyone! Let's do a quick round for today's standup. What did you finish yesterday and what are you tackling today?",
            "initialTranslation": "Chào buổi sáng cả đội! Chúng ta cùng điểm nhanh cuộc họp hôm nay nhé. Hôm qua bạn đã xong việc gì và hôm nay sẽ giải quyết việc gì?",
            "initialSuggestions": [
                "Yesterday I finished the API integration. Today I'm testing the user interface.",
                "I wrapped up the bug fixes yesterday. Today I'll work on database optimization.",
                "I'm a bit blocked on the third-party payment service and need a quick review."
            ]
        },
        {
            "id": "refund",
            "title": "🛒 Đổi Trả Hàng & Hoàn Tiền (Store Return & Refund)",
            "description": "Phàn nàn lịch sự về sản phẩm lỗi/sai size tại cửa hàng, yêu cầu hoàn tiền vào thẻ.",
            "botRole": "Nhân viên quầy chăm sóc khách hàng tại trung tâm thương mại",
            "initialMessage": "Hi there! Welcome to Customer Service. Are you returning or exchanging an item today?",
            "initialTranslation": "Xin chào! Chào mừng bạn đến quầy Chăm sóc khách hàng. Hôm nay bạn muốn trả hàng hay đổi sang món khác ạ?",
            "initialSuggestions": [
                "I'd like to return this jacket. It's the wrong size and has never been worn.",
                "I'd like to exchange this shirt for a size medium, please.",
                "There's a defective zipper on this bag. Could I get a full refund?"
            ]
        },
        {
            "id": "clinic",
            "title": "🩺 Đi Khám Bệnh & Nhà Thuốc (Doctor's Clinic & Pharmacy)",
            "description": "Miêu tả triệu chứng sức khỏe, cảm cúm, đau đầu cho bác sĩ và hỏi cách dùng thuốc.",
            "botRole": "Bác sĩ gia đình tận tâm tại phòng khám",
            "initialMessage": "Good afternoon. Please take a seat. What seems to be bothering you today?",
            "initialTranslation": "Chào buổi chiều. Mời bạn ngồi. Hôm nay bạn cảm thấy khó chịu ở đâu trong người?",
            "initialSuggestions": [
                "I've had a severe headache and a mild fever since yesterday morning.",
                "My stomach has been hurting badly after dinner last night.",
                "I have a sore throat and a persistent cough. Could you check my throat?"
            ]
        },
        {
            "id": "cinema",
            "title": "🎬 Mua Vé Xem Phim & Bắp Nước (At the Cinema)",
            "description": "Chọn phim, chọn suất chiếu, chọn ghế giữa rạp và gọi combo bắp phô mai nước ngọt.",
            "botRole": "Nhân viên bán vé rạp chiếu phim AMC",
            "initialMessage": "Hey! Welcome to AMC Cinema. Which movie are you looking to watch today, and how many tickets?",
            "initialTranslation": "Xin chào! Chào mừng bạn đến rạp phim AMC. Hôm nay bạn muốn xem phim nào và cần mua mấy vé?",
            "initialSuggestions": [
                "Two tickets for the 7:30 PM action movie in 2D, please.",
                "What are the best available seats for the sci-fi screening tonight?",
                "Could we get a large popcorn combo with two Diet Cokes as well?"
            ]
        },
        {
            "id": "complaint",
            "title": "🍽️ Phàn Nàn Lịch Sự Tại Nhà Hàng (Dining & Polite Feedback)",
            "description": "Báo bồi bàn món ăn bị nguội hoặc đem nhầm món, yêu cầu làm lại và xin hóa đơn.",
            "botRole": "Quản lý nhà hàng Âu chu đáo",
            "initialMessage": "Good evening. How is everything tasting tonight? Is your steak cooked to your liking?",
            "initialTranslation": "Chào buổi tối. Các món ăn tối nay có vừa miệng quý khách không ạ? Miếng bít tết đã đúng độ chín như ý quý khách chưa?",
            "initialSuggestions": [
                "Actually, I asked for medium-rare, but this steak is completely well-done.",
                "Excuse me, the soup was served lukewarm. Could you please heat it up?",
                "Everything is wonderful, thank you! Could we also get the dessert menu?"
            ]
        },
        {
            "id": "free_chat",
            "title": "💬 Trò Chuyện Tự Do (Casual Daily Talk)",
            "description": "Tán gẫu thoải mái về sở thích, âm nhạc, phim ảnh, văn hóa cùng bạn bản xứ.",
            "botRole": "Người bạn bản xứ vui tính đến từ California",
            "initialMessage": "Hey! How's your day going so far? Doing anything fun today?",
            "initialTranslation": "Chào bạn! Ngày hôm nay của bạn thế nào rồi? Có làm gì vui không?",
            "initialSuggestions": [
                "It's going great! Just relaxing with some music and practicing English.",
                "A bit busy with work today, but looking forward to the weekend!",
                "Not much, just trying out this new AI app to improve my speaking skills."
            ]
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
            "initialTranslation": "Soái ca / Người đẹp ơi, vào xem đồ đi! Mẫu này đang hot nhất năm nay, chất lượng cực tốt, bạn muốn xem cái nào?",
            "initialSuggestions": [
                "老板，这件黑色外套多少钱？能便宜点吗？ (Lǎobǎn, zhè jiàn hēisè wàitào duōshao qián? Néng piányi diǎn ma? - Ông chủ, áo khoác đen này bao nhiêu tiền? Bớt được không?)",
                "这款有没有我穿的L码？我想试穿一下 (Zhè kuǎn yǒu méiyǒu wǒ chuān de L mǎ? Wǒ xiǎng shìchuān yíxià - Mẫu này có size L em mặc không? Em muốn thử)",
                "我先随便看看，挑中了再叫你 (Wǒ xiān suíbiàn kànkan, tiāozhòng le zài jiào nǐ - Em xem qua chút đã, chọn được sẽ gọi anh)"
            ]
        },
        {
            "id": "restaurant",
            "title": "🥟 Đi Ăn Tại Nhà Hàng Trung Quốc (在餐厅点餐)",
            "description": "Gọi món ăn, hỏi độ cay, gọi thêm trà và tính tiền tại nhà hàng Bắc Kinh.",
            "botRole": "Bồi bàn nhanh nhẹn tại nhà hàng Vịt quay Bắc Kinh",
            "initialHanzi": "您好！欢迎光临全聚德。请问您几位？今天想吃点什么特色菜？",
            "initialPinyin": "Nín hǎo! Huānyíng guānglín Quánjùdé. Qǐngwèn nín jǐ wèi? Jīntiān xiǎng chī diǎn shénme tèsè cài?",
            "initialTranslation": "Xin chào quý khách! Chào mừng đến Toàn Tụ Đức. Xin hỏi quý khách đi mấy người? Hôm nay muốn dùng món đặc sản gì ạ?",
            "initialSuggestions": [
                "我们两位，请问招牌烤鸭现在有现做的吗？ (Wǒmen liǎng wèi, qǐngwèn zhāopai kǎoyā xiànzài yǒu xiànzuò de ma? - Chúng tôi 2 người, vịt quay đặc sản có sẵn không?)",
                "给我们找个靠窗安静点的位子，先上一壶龙井茶 (Gěi wǒmen zhǎo ge kàochuāng ānjìng diǎn de wèizi, xiān shàng yì hú Lóngjǐngchá - Cho bàn cạnh cửa sổ yên tĩnh, cho bình trà Long Tỉnh trước)",
                "有哪些不辣的特色菜推荐吗？ (Yǒu nǎxiē bù là de tèsè cài tuījiàn ma? - Có món đặc sản nào không cay gợi ý không?)"
            ]
        },
        {
            "id": "factory",
            "title": "🏭 Đàm Phán Xưởng & Nhà Máy Trung Quốc (工厂询盘谈判)",
            "description": "Hỏi giá sỉ số lượng lớn, yêu cầu gửi mẫu (sample), tiến độ sản xuất và thanh toán.",
            "botRole": "Giám đốc kinh doanh xưởng gia công tại Thâm Quyến",
            "initialHanzi": "老板你好！很高兴认识您。请问您看中哪款产品？大概需要多少起订量（MOQ）？",
            "initialPinyin": "Lǎobǎn nǐ hǎo! Hěn gāoxìng rènshi nín. Qǐngwèn nín kànzhòng nǎ kuǎn chǎnpǐn? Dàgài xūyào duōshao qǐdìngliàng (MOQ)?",
            "initialTranslation": "Chào ông chủ! Rất vui được biết bạn. Xin hỏi bạn đang ưng mẫu sản phẩm nào? Số lượng đặt hàng tối thiểu dự kiến khoảng bao nhiêu?",
            "initialSuggestions": [
                "我们对A款智能手表很感兴趣，如果订500台单价多少？ (Wǒmen duì A kuǎn zhìnéng shǒubiǎo hěn gǎnxìngqù, rúguǒ dìng 500 tái dānjià duōshao? - Chúng tôi quan tâm mẫu A, nếu đặt 500 chiếc thì đơn giá bao nhiêu?)",
                "能不能先给我们寄两件样品看一下质量？ (Néng bu néng xiān gěi wǒmen jì liǎng jiàn yàngpǐn kàn yíxià zhìliàng? - Có thể gửi 2 mẫu sample trước để xem chất lượng không?)",
                "如果今天下单，交货周期大概需要多少天？ (Rúguǒ jīntiān xiàdān, jiāohuò zhōuqī dàgài xūyào duōshao tiān? - Nếu hôm nay chốt đơn thì thời gian giao hàng bao nhiêu ngày?)"
            ]
        },
        {
            "id": "didi",
            "title": "🚕 Đi Taxi / Bắt Xe Didi & Chỉ Đường (打车与指路)",
            "description": "Xác nhận điểm đón xe, bảo tài xế đi đường cao tốc, rẽ trái/phải, dừng xe tính tiền.",
            "botRole": "Tài xế Didi nhiệt tình tại Thượng Hải",
            "initialHanzi": "师傅到了！尾号8897对吧？看定位是去虹桥高铁站，走高架桥比较快，可以吗？",
            "initialPinyin": "Shīfu dào le! Wěihào bābājiǔqī duì ba? Kàn dìngwèi shì qù Hóngqiáo Gāotiězhàn, zǒu gāojiàqiáo bǐjiào kuài, kěyǐ ma?",
            "initialTranslation": "Tài xế tới rồi! 4 số cuối điện thoại là 8897 đúng không? Điểm đến là ga tàu Hồng Kiều, đi cầu vượt trên cao sẽ nhanh hơn, được không bạn?",
            "initialSuggestions": [
                "对的师傅！没问题，走高架桥吧，我不赶时间 (Duì de shīfu! Méi wèntí, zǒu gāojiàqiáo ba, wǒ bù gǎn shíjiān - Đúng rồi bác tài! Cứ đi cầu vượt, em không vội)",
                "师傅，大概多久能到？我还要赶半小时后的火车 (Shīfu, dàgài duōjiǔ néng dào? Wǒ hái yào gǎn bàn xiǎoshí hòu de huǒchē - Đi tầm bao lâu tới? Em phải kịp chuyến tàu 30 phút nữa)",
                "好的，麻烦车里空调稍微开大一点点，有点热 (Hǎode, máfan chēlǐ kōngtiáo shāowēi kāi dà yìdiǎndiǎn, yǒudiǎn rè - Vâng, phiền bác mở điều hòa mát hơn chút, hơi nóng)"
            ]
        },
        {
            "id": "haidilao",
            "title": "🍲 Ăn Lẩu Haidilao & Gọi Trà Sữa (吃火锅喝奶茶)",
            "description": "Chọn nước lẩu cà chua/cay tê, pha nước chấm, chọn độ ngọt và đá trà sữa.",
            "botRole": "Phục vụ viên Haidilao chu đáo",
            "initialHanzi": "欢迎光临海底捞！请问今天锅底想要番茄牛尾的还是麻辣清油的？先给您倒杯酸梅汤吧！",
            "initialPinyin": "Huānyíng guānglín Hǎidǐlāo! Qǐngwèn jīntiān guōdǐ xiǎng yào fānqié niúwěi de háishì málà qīngyóu de? Xiān gěi nín dào bēi suānméitāng ba!",
            "initialTranslation": "Chào mừng đến Haidilao! Hôm nay bạn muốn dùng nước lẩu đuôi bò cà chua hay lẩu cay thanh dầu? Để em rót cho bạn cốc nước mơ chua giải nhiệt trước nhé!",
            "initialSuggestions": [
                "我们要番茄和微辣四宫格锅底，谢谢！ (Wǒmen yào fānqié hé wēilà sìgōnggé guōdǐ, xièxie! - Cho nồi 4 ngăn vị cà chua và cay nhẹ nhé, cảm ơn!)",
                "招牌捞派毛肚和虾滑先各来一份！ (Zhāopai lǎopài máodù hé xiāhuá xiān gè lái yí fèn! - Cho trước 1 phần sách bò và chả tôm đặc sản!)",
                "能不能麻烦帮我们调两碗招牌牛肉粒蘸料？ (Néng bu néng máfan bāng wǒmen tiáo liǎng wǎn zhāopai niúròulì zhànliào? - Phiền bạn pha giúp 2 bát nước chấm thịt bò băm nhé?)"
            ]
        },
        {
            "id": "pharmacy",
            "title": "🏥 Đi Hiệu Thuốc & Mua Thuốc (药店问药)",
            "description": "Miêu tả triệu chứng cảm sốt, đau họng, đau dạ dày và hỏi liều lượng uống thuốc.",
            "botRole": "Dược sĩ tư vấn tại nhà thuốc Bắc Kinh",
            "initialHanzi": "你好！看你脸色不太好，是哪里不舒服？发烧还是嗓子疼？",
            "initialPinyin": "Nǐ hǎo! Kàn nǐ liǎnsè bú tài hǎo, shì nǎlǐ bù shūfu? Fāshāo háishì sǎngzi téng?",
            "initialTranslation": "Chào bạn! Thấy sắc mặt bạn hơi nhợt nhạt, bạn đang khó chịu ở đâu? Có bị sốt hay đau họng không?",
            "initialSuggestions": [
                "我从昨晚开始有点发低烧，嗓子也特别哑 (Wǒ cóng zuówǎn kāishǐ yǒudiǎn fā dīshāo, sǎngzi yě tèbié yǎ - Từ tối qua em hơi sốt nhẹ, họng cũng khản đặc)",
                "我胃疼得厉害，一阵一阵地疼，有止疼药吗？ (Wǒ wèiténg de lìhai, yízhèn yízhèn de téng, yǒu zhǐténgyào ma? - Em bị đau dạ dày dữ dội, từng cơn một, có thuốc giảm đau không?)",
                "请问这个感冒冲剂一天喝几次？饭前还是饭后喝？ (Qǐngwèn zhège gǎnmào chōngjì yì tiān hē jǐ cì? Fànqián háishì fànhòu hē? - Thuốc cốm cảm cúm này ngày uống mấy lần? Uống trước hay sau ăn?)"
            ]
        },
        {
            "id": "rent",
            "title": "🏢 Thuê Căn Hộ & Phòng Trọ (租房看房)",
            "description": "Hỏi giá thuê phòng theo tháng, tiền đặt cọc, tiền điện nước, kiểm tra nội thất.",
            "botRole": "Môi giới nhà đất nhiệt tình tại Quảng Châu",
            "initialHanzi": "你好！这套一室一厅采光非常好，家具家电全配齐，押一付一，想今天实地看看房吗？",
            "initialPinyin": "Nǐ hǎo! Zhè tào yíshìyìtīng cǎiguāng fēicháng hǎo, jiājù jiādiàn quán pèiqí, yā yī fù yī, xiǎng jīntiān shídì kànkan fáng ma?",
            "initialTranslation": "Chào bạn! Căn 1 phòng ngủ 1 phòng khách này đón ánh sáng cực tốt, đầy đủ nội thất đồ điện, cọc 1 đóng 1 tháng, bạn có muốn qua xem nhà trực tiếp hôm nay không?",
            "initialSuggestions": [
                "请问月租金能再商量吗？包不包物业和宽带费？ (Qǐngwèn yuè zūjīn néng zài shāngliang ma? Bāo bù bāo wùyè hé kuāndàifèi? - Giá thuê tháng bớt được không? Có bao phí quản lý và wifi không?)",
                "今天下午三点方便看房吗？我想看下洗衣机和热水器 (Jīntiān xiàwǔ sān diǎn fāngbiàn kàn fáng ma? Wǒ xiǎng kàn xià xǐyījī hé rèshuǐqì - Chiều nay 3h xem phòng tiện không? Em muốn kiểm tra máy giặt và bình nóng lạnh)",
                "周围离地铁站有多远？走路大概几分钟？ (Zhōuwéi lí dìtiězhàn yǒu duō yuǎn? Zǒulù dàgài jǐ fēnzhōng? - Xung quanh cách ga tàu điện ngầm bao xa? Đi bộ mấy phút?)"
            ]
        },
        {
            "id": "salon",
            "title": "💇 Cắt Tóc & Tạo Kiểu Salon (理发做造型)",
            "description": "Yêu cầu thợ cắt tóc chỉ tỉa bớt ngọn tóc, không cắt quá ngắn, nhuộm màu tự nhiên.",
            "botRole": "Nhà tạo mẫu tóc chuyên nghiệp tại Salon",
            "initialHanzi": "帅哥/美女请坐！今天想怎么剪？是要换个新发型还是只稍微修剪一下？",
            "initialPinyin": "Shuàigē/Měinǚ qǐng zuò! Jīntiān xiǎng zěnme jiǎn? Shì yào huàn ge xīn fàxíng háishì zhǐ shāowēi xiūjiǎn yíxià?",
            "initialTranslation": "Mời bạn ngồi! Hôm nay bạn muốn cắt thế nào? Muốn đổi kiểu tóc mới hay chỉ tỉa gọn lại một chút thôi?",
            "initialSuggestions": [
                "只把发尾分叉的地方剪掉一点，长度尽量保留 (Zhǐ bǎ fàwěi fēnchà de dìfang jiǎndiào yìdiǎn, chángdù jìnliàng bǎoliú - Chỉ tỉa bớt phần đuôi chẻ ngọn, giữ nguyên chiều dài cho em)",
                "两边推短一点，头顶打薄，显得精神一点 (Liǎngbiān tuī duǎn yìdiǎn, tóudǐng dǎbáo, xiǎnde jīngshen yìdiǎn - Hai bên cạo ngắn bớt, đỉnh đầu tỉa mỏng cho sáng sủa)",
                "我想染个低调自然的冷棕色，需要先漂头发吗？ (Wǒ xiǎng rǎn ge dīdiào zìrán de lěngzōngsè, xūyào xiān piāo tóufa ma? - Em muốn nhuộm màu nâu lạnh tự nhiên, có cần tẩy tóc trước không?)"
            ]
        },
        {
            "id": "travel",
            "title": "🚄 Du Lịch & Hỏi Đường Ga Tàu (旅行问路)",
            "description": "Hỏi đường đến ga tàu cao tốc, mua vé tàu, hỏi cửa kiểm soát vé.",
            "botRole": "Người dân bản địa nhiệt tình tại Thượng Hải",
            "initialHanzi": "你好！看你在看地图，是去高铁站吗？需要我帮忙指路吗？",
            "initialPinyin": "Nǐ hǎo! Kàn nǐ zài kàn dìtú, shì qù gāotiě zhàn ma? Xūyào wǒ bāngmáng zhǐlù ma?",
            "initialTranslation": "Chào bạn! Thấy bạn đang xem bản đồ, bạn định đi ga tàu cao tốc à? Cần tôi chỉ đường giúp không?",
            "initialSuggestions": [
                "你好！请问去高铁站坐地铁几号线最快？ (Nǐ hǎo! Qǐngwèn qù gāotiězhàn zuò dìtiě jǐ hào xiàn zuì kuài? - Chào bạn! Đi ga tàu cao tốc bắt tàu điện ngầm tuyến số mấy nhanh nhất?)",
                "请问自动取票机在哪里？需要刷身份证吗？ (Qǐngwèn zìdòng qǔpiàojī zài nǎlǐ? Xūyào shuā shēnfènzhèng ma? - Máy lấy vé tự động ở đâu ạ? Có cần quẹt căn cước không?)",
                "太感谢了！进站安检大概需要排队多久？ (Tài gǎnxiè le! Jìnzhàn ānjiǎn dàgài xūyào páiduì duōjiǔ? - Cảm ơn bạn nhiều! Xếp hàng qua cửa kiểm tra an ninh mất tầm bao lâu?)"
            ]
        },
        {
            "id": "free_zh",
            "title": "💬 Tán Gẫu Đời Thường Tiếng Trung (日常闲聊)",
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
1. Respond naturally staying strictly in character as {bot_role} in the scenario: {scenario_title}.
2. CRITICAL FOR SUGGESTED REPLIES (suggested_replies):
   - You MUST provide 3 completely fresh, dynamic options directly responding to your latest question in this scenario ({scenario_title}).
   - The suggestions MUST MATCH the conversation context 100%. Never output suggestions from another topic.
   - The 3 options must cover 3 DISTINCT conversational intents:
     + Option 1: Direct confirmation / Making a specific choice
     + Option 2: Asking for details / Inquiring for options or customization
     + Option 3: Politeness / Hesitation / Suggesting an alternative
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

def generate_fresh_suggestions(api_key: str, lang: str, scenario_id: str, history: list = None, preferred_model: str = "gemini-3.5-flash-lite") -> list:
    """Tạo 3 câu gợi ý mới toanh khớp 100% với ngữ cảnh hội thoại hiện tại."""
    scenario_info = next((s for s in SCENARIOS.get(lang, []) if s["id"] == scenario_id), None)
    scenario_title = scenario_info.get("title", "") if scenario_info else scenario_id
    bot_role = scenario_info.get("botRole", "Đối tác") if scenario_info else "Đối tác"

    if api_key and history:
        try:
            if lang == "zh":
                prompt = f"""Bạn là gia sư AI dạy tiếng Trung trong tình huống: {scenario_title} (bạn đóng vai {bot_role}).
Dựa vào tin nhắn gần nhất trong đoạn hội thoại, hãy tạo 3 câu gợi ý trả lời HOÀN TOÀN MỚI, KHÁC BIỆT và KHỚP 100% VỚI NGỮ CẢNH để người học nói tiếp.
Mỗi câu gợi ý có dạng: "Chữ Hán (Pinyin - Nghĩa tiếng Việt)".
Xuất JSON dạng: {{"suggested_replies": ["...", "...", "..."]}}"""
            else:
                prompt = f"""You are an English language coach in the scenario: {scenario_title} (playing as {bot_role}).
Based on the latest message in this conversation, provide 3 completely fresh, natural alternative responses the learner can say next.
Keep suggestions strictly aligned to the current dialogue context.
Output JSON: {{"suggested_replies": ["...", "...", "..."]}}"""

            raw = call_gemini_api(api_key, history, prompt, preferred_model=preferred_model)
            parsed = json.loads(raw)
            if "suggested_replies" in parsed and isinstance(parsed["suggested_replies"], list) and len(parsed["suggested_replies"]) > 0:
                return parsed["suggested_replies"]
        except Exception as e:
            logger.warning(f"Không thể tạo gợi ý mới qua Gemini: {e}")

    # Fallback to scenario initialSuggestions or dynamic response
    if scenario_info and scenario_info.get("initialSuggestions"):
        return scenario_info["initialSuggestions"]
    offline = get_dynamic_offline_response("gợi ý", lang, scenario_id, 1)
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
            "Sounds good, could you give me a bit more detail on that?",
            "What other options or recommendations do you have?",
            "I'll think about it and let you know shortly, thanks!"
        ])
    else:
        suggestions = [
            "That sounds great, thank you for your help!",
            "Could you explain a bit more about that?",
            "Let's move on to another topic!"
        ]

    return {
        "reply": "Understood! I completely get what you mean. What would you like to explore next?",
        "translation_vi": "Đã hiểu! Tôi hoàn toàn hiểu ý của bạn. Bạn muốn tiếp tục tìm hiểu điều gì tiếp theo?",
        "feedback": "Great pronunciation and natural phrasing! Keep up the good work.",
        "suggested_replies": suggestions
    }
