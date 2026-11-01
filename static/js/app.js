document.addEventListener('DOMContentLoaded', () => {
  // STATE
  let currentLang = 'en'; // 'en' hoặc 'zh'
  let currentScenario = null;
  let scenariosList = [];
  let showPinyin = true;
  let showTranslation = true;
  let appConfig = null;
  let recognition = null;
  let isRecording = false;

  let chatHistory = [];
  let turnCount = 0;

  // DOM ELEMENTS
  const chatMessages = document.getElementById('chat-messages');
  const inputCustomText = document.getElementById('input-custom-text');
  const btnSendText = document.getElementById('btn-send-text');
  const btnMic = document.getElementById('btn-mic');
  const recordingStatus = document.getElementById('recording-status');
  const recordingText = document.getElementById('recording-text');
  const suggestionsContainer = document.getElementById('suggestions-container');
  const suggestionsList = document.getElementById('suggestions-list');
  const btnRefreshSuggestions = document.getElementById('btn-refresh-suggestions');

  const currentScenarioTitle = document.getElementById('current-scenario-title');
  const btnShowScenarios = document.getElementById('btn-show-scenarios');
  const modalScenarios = document.getElementById('modal-scenarios');
  const btnCloseScenarios = document.getElementById('btn-close-scenarios');
  const scenariosListContainer = document.getElementById('scenarios-list-container');

  const modalSettings = document.getElementById('modal-settings');
  const btnOpenSettings = document.getElementById('btn-open-settings');
  const btnCloseSettings = document.getElementById('btn-close-settings');
  const btnSaveSettings = document.getElementById('btn-save-settings');

  const modalDonate = document.getElementById('modal-donate');
  const btnOpenDonate = document.getElementById('btn-open-donate');
  const btnOpenShare = document.getElementById('btn-open-share');
  const btnCloseDonate = document.getElementById('btn-close-donate');
  const btnDoneDonate = document.getElementById('btn-done-donate');
  const btnShareFb = document.getElementById('btn-share-fb');
  const btnShareZalo = document.getElementById('btn-share-zalo');
  const btnShareTelegram = document.getElementById('btn-share-telegram');
  const btnShareCopy = document.getElementById('btn-share-copy');
  const btnShareNative = document.getElementById('btn-share-native');
  const btnCopyAcc = document.getElementById('btn-copy-acc');
  const btnCopyContent = document.getElementById('btn-copy-content');
  const inputApiKey = document.getElementById('input-api-key');
  const selectModel = document.getElementById('select-model');
  const selectVoiceEn = document.getElementById('select-voice-en');
  const selectVoiceZh = document.getElementById('select-voice-zh');

  const togglePinyinBtn = document.getElementById('toggle-pinyin');
  const toggleTransBtn = document.getElementById('toggle-translation');
  const langBtns = document.querySelectorAll('.lang-btn');

  // 1. SETUP SPEECH RECOGNITION (Web Speech API - Nhận diện thông minh & chống nhảy chữ)
  let accumulatedTranscript = '';
  let currentInterimText = '';
  let silenceTimer = null;
  const SILENCE_TIMEOUT_MS = 2200; // 2.2 giây đệm khoảng lặng để người học nghỉ lấy hơi, không bị nhảy chữ ngắt ngang

  function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Trình duyệt không hỗ trợ Web Speech API nhận diện giọng nói.');
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      isRecording = true;
      accumulatedTranscript = '';
      currentInterimText = '';
      btnMic.classList.add('recording');
      btnMic.title = "Nhấn để hoàn tất và gửi câu nói ngay";
      recordingStatus.style.display = 'flex';
      recordingText.innerHTML = currentLang === 'zh'
        ? '🎙️ <b>Đang lắng nghe tiếng Trung...</b> Hãy nói tự nhiên, không sợ ngập ngừng!'
        : '🎙️ <b>Listening...</b> Speak at your natural pace, no rush!';
    };

    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          accumulatedTranscript += event.results[i][0].transcript + ' ';
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      currentInterimText = interim;

      const fullSpokenText = (accumulatedTranscript + currentInterimText).trim();
      if (fullSpokenText) {
        // Cập nhật chữ tức thì lên ô nhập để người học nhìn thấy chính xác nội dung đang nói
        inputCustomText.value = fullSpokenText;
        recordingText.innerHTML = `🎙️ Đang nghe: <b>"${escapeHtml(fullSpokenText)}"</b> <span style="opacity:0.8; font-size:0.75rem;">(Nói tiếp hoặc bấm Mic để gửi)</span>`;

        // Đệm khoảng lặng 2.2s: Chờ người học nói tiếp câu gợi ý mà không bị ngắt ngang giữa chừng
        if (silenceTimer) clearTimeout(silenceTimer);
        silenceTimer = setTimeout(() => {
          if (isRecording && (accumulatedTranscript || currentInterimText).trim()) {
            finishAndSendSpeech();
          }
        }, SILENCE_TIMEOUT_MS);
      }
    };

    recognition.onerror = (event) => {
      if (event.error === 'no-speech' || event.error === 'aborted') {
        return;
      }
      console.warn('Cảnh báo nhận diện giọng nói:', event.error);
    };

    recognition.onend = () => {
      if (isRecording) {
        const candidate = (accumulatedTranscript + currentInterimText).trim();
        if (candidate) {
          finishAndSendSpeech();
        } else {
          stopRecording();
        }
      }
    };
  }

  function startRecording() {
    if (!recognition) {
      alert('Trình duyệt này chưa kích hoạt micro nhận diện giọng nói. Bạn có thể gõ chữ vào ô nhập!');
      return;
    }
    if (isRecording) return;

    if (silenceTimer) clearTimeout(silenceTimer);
    accumulatedTranscript = '';
    currentInterimText = '';
    recognition.lang = (currentLang === 'zh') ? 'zh-CN' : 'en-US';
    try {
      recognition.start();
    } catch (e) {
      console.warn('Mic start err:', e);
    }
  }

  function finishAndSendSpeech() {
    if (silenceTimer) clearTimeout(silenceTimer);
    const spoken = (accumulatedTranscript + currentInterimText).trim() || inputCustomText.value.trim();
    stopRecording();
    try {
      recognition.stop();
    } catch (e) {}

    if (spoken) {
      sendUserMessage(spoken);
    }
  }

  function stopRecording() {
    isRecording = false;
    btnMic.classList.remove('recording');
    btnMic.title = "Nhấn để bắt đầu nói";
    recordingStatus.style.display = 'none';
    if (silenceTimer) clearTimeout(silenceTimer);
  }

  btnMic.addEventListener('click', () => {
    if (isRecording) {
      // Bấm nút Mic lần 2 -> gửi ngay lập tức nội dung đã nói mà không cần chờ 2.2 giây
      finishAndSendSpeech();
    } else {
      startRecording();
    }
  });

  // 2. TOGGLE PINYIN & TRANSLATION
  togglePinyinBtn.addEventListener('click', () => {
    showPinyin = !showPinyin;
    togglePinyinBtn.classList.toggle('active', showPinyin);
    document.querySelectorAll('.pinyin-text').forEach(el => {
      el.style.display = showPinyin ? 'block' : 'none';
    });
  });

  toggleTransBtn.addEventListener('click', () => {
    showTranslation = !showTranslation;
    toggleTransBtn.classList.toggle('active', showTranslation);
    document.querySelectorAll('.translation-text').forEach(el => {
      el.style.display = showTranslation ? 'block' : 'none';
    });
  });

  // 2.1 TOGGLE SPEECH PLAYBACK RATE (1.0x ➔ 0.8x ➔ 1.2x)
  const toggleSpeedBtn = document.getElementById('toggle-speed');
  const selectSpeechRate = document.getElementById('select-speech-rate');
  let currentSpeechRate = parseFloat(localStorage.getItem('speechRate')) || 1.0;

  function updateSpeedUI() {
    if (currentSpeechRate === 0.8) {
      if (toggleSpeedBtn) {
        toggleSpeedBtn.innerHTML = '<span class="toggle-icon">🐢</span> 0.8x';
        toggleSpeedBtn.title = 'Tốc độ: 0.8x (Chậm, nghe rõ phát âm). Bấm để đổi.';
      }
      if (selectSpeechRate) selectSpeechRate.value = '0.8';
    } else if (currentSpeechRate === 1.2) {
      if (toggleSpeedBtn) {
        toggleSpeedBtn.innerHTML = '<span class="toggle-icon">🐇</span> 1.2x';
        toggleSpeedBtn.title = 'Tốc độ: 1.2x (Nhanh, luyện phản xạ). Bấm để đổi.';
      }
      if (selectSpeechRate) selectSpeechRate.value = '1.2';
    } else {
      currentSpeechRate = 1.0;
      if (toggleSpeedBtn) {
        toggleSpeedBtn.innerHTML = '<span class="toggle-icon">⚡</span> 1.0x';
        toggleSpeedBtn.title = 'Tốc độ: 1.0x (Chuẩn bản ngữ). Bấm để đổi.';
      }
      if (selectSpeechRate) selectSpeechRate.value = '1.0';
    }
  }

  if (toggleSpeedBtn) {
    updateSpeedUI();
    toggleSpeedBtn.addEventListener('click', () => {
      if (currentSpeechRate === 1.0) {
        currentSpeechRate = 0.8;
        showToast('🐢 Đã chuyển tốc độ đọc: 0.8x (Chậm, nghe rõ phát âm)');
      } else if (currentSpeechRate === 0.8) {
        currentSpeechRate = 1.2;
        showToast('🐇 Đã chuyển tốc độ đọc: 1.2x (Nhanh, luyện phản xạ)');
      } else {
        currentSpeechRate = 1.0;
        showToast('⚡ Đã chuyển tốc độ đọc: 1.0x (Chuẩn bản ngữ)');
      }
      localStorage.setItem('speechRate', currentSpeechRate);
      updateSpeedUI();

      if (sharedAudio && !sharedAudio.paused) {
        sharedAudio.playbackRate = currentSpeechRate;
      }
    });
  }

  if (selectSpeechRate) {
    selectSpeechRate.addEventListener('change', () => {
      currentSpeechRate = parseFloat(selectSpeechRate.value) || 1.0;
      localStorage.setItem('speechRate', currentSpeechRate);
      updateSpeedUI();
    });
  }

  // 3. LOAD CONFIG & SCENARIOS
  async function loadConfig() {
    try {
      const res = await fetch('/api/config');
      const data = await res.json();
      appConfig = data.config;

      selectVoiceEn.innerHTML = '';
      data.voiceOptions.en.forEach(v => {
        selectVoiceEn.innerHTML += `<option value="${v.id}" ${v.id === appConfig.voiceEn ? 'selected' : ''}>${v.name}</option>`;
      });

      selectVoiceZh.innerHTML = '';
      data.voiceOptions.zh.forEach(v => {
        selectVoiceZh.innerHTML += `<option value="${v.id}" ${v.id === appConfig.voiceZh ? 'selected' : ''}>${v.name}</option>`;
      });

      if (appConfig.geminiApiKey) {
        inputApiKey.value = appConfig.geminiApiKey;
      }
      if (selectModel && appConfig.geminiModel) {
        selectModel.value = appConfig.geminiModel;
      }

      if (appConfig.donateBank) {
        const el = document.getElementById('donate-bank');
        if (el) el.textContent = appConfig.donateBank;
      }
      if (appConfig.donateAcc) {
        const el = document.getElementById('donate-acc');
        if (el) el.textContent = appConfig.donateAcc;
      }
      if (appConfig.donateName) {
        const el = document.getElementById('donate-name');
        if (el) el.textContent = appConfig.donateName;
      }

      currentLang = appConfig.currentLang || 'en';
      updateLangUI();
      startTopicConversation('free', false);
    } catch (err) {
      console.error('Lỗi tải cấu hình:', err);
    }
  }

  function updateLangUI() {
    langBtns.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === currentLang);
    });

    togglePinyinBtn.style.display = 'flex';
    if (currentLang === 'zh') {
      togglePinyinBtn.innerHTML = '<span class="toggle-icon">Aa</span> Pinyin';
      togglePinyinBtn.title = 'Bật/Tắt Pinyin';
      inputCustomText.placeholder = 'Nhập tiếng Trung hoặc bấm Mic để nói...';
    } else {
      togglePinyinBtn.innerHTML = '<span class="toggle-icon">Aa</span> Phiên âm';
      togglePinyinBtn.title = 'Bật/Tắt Phiên âm IPA';
      inputCustomText.placeholder = 'Nhập tiếng Anh hoặc bấm Mic để nói...';
    }
  }

  // Chuyển đổi ngôn ngữ Anh ⇄ Trung
  langBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
      const targetLang = btn.getAttribute('data-lang');
      if (targetLang === currentLang) return;

      currentLang = targetLang;
      updateLangUI();
      startTopicConversation('free', false);
      fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ currentLang })
      });
    });
  });


  // ==========================================================================
  // HỆ THỐNG CHỌN TỪ KHÓA CHỦ ĐỀ ĐÀM THOẠI (TOPIC LAUNCHER HUB)
  // ==========================================================================
  const TOPIC_PRESETS = {
    en: [
      { id: "free", icon: "💬", title: "Casual Daily Talk", sub: "Trò chuyện tự do mọi điều (Mặc định)", isDefault: true },
      { id: "cafe", icon: "☕", title: "Café & Hanging Out", sub: "Quán cà phê, đồ uống, tán gẫu" },
      { id: "food", icon: "🍕", title: "Food & Cooking", sub: "Món ăn ngon, ẩm thực, nấu nướng" },
      { id: "travel", icon: "✈️", title: "Travel & Vacations", sub: "Du lịch, khám phá, đi biển" },
      { id: "work", icon: "💼", title: "Work & Career", sub: "Công việc, đồng nghiệp, văn phòng" },
      { id: "movies", icon: "🎬", title: "Movies & Netflix", sub: "Phim ảnh, rạp chiếu, diễn viên" },
      { id: "music", icon: "🎵", title: "Music & Songs", sub: "Âm nhạc, ca sĩ, ban nhạc yêu thích" },
      { id: "weather", icon: "🌧️", title: "Weather & Daily Life", sub: "Thời tiết, tâm trạng, nhịp sống" },
      { id: "shopping", icon: "🛍️", title: "Shopping & Fashion", sub: "Mua sắm, quần áo, thời trang" },
      { id: "fitness", icon: "🏋️", title: "Fitness & Health", sub: "Tập gym, thể thao, sức khỏe" },
      { id: "pets", icon: "🐾", title: "Pets & Animals", sub: "Chó mèo, thú cưng, chăm sóc" },
      { id: "money", icon: "💰", title: "Money & Spending", sub: "Tiền bạc, chi tiêu, tiết kiệm" },
      { id: "books", icon: "📚", title: "Books & Self-Growth", sub: "Đọc sách, học tập, phát triển" },
      { id: "commute", icon: "🚗", title: "Traffic & Commute", sub: "Xe cộ, đường phố, đi lại" },
      { id: "weekend", icon: "🏖️", title: "Weekend Plans", sub: "Kế hoạch cuối tuần, xả stress" }
    ],
    zh: [
      { id: "free", icon: "💬", title: "随心日常闲聊", sub: "Trò chuyện tự do mọi điều (Mặc định)", isDefault: true },
      { id: "cafe", icon: "☕", title: "喝咖啡与探店", sub: "Quán cà phê, hẹn hò, đồ uống" },
      { id: "food", icon: "🍕", title: "美食与烹饪", sub: "Ẩm thực Trung - Việt, nấu nướng" },
      { id: "travel", icon: "✈️", title: "旅游与度假", sub: "Du lịch ngắm cảnh, đi chơi xa" },
      { id: "work", icon: "💼", title: "职场与工作", sub: "Đi làm, đồng nghiệp, văn phòng" },
      { id: "movies", icon: "🎬", title: "电影与追剧", sub: "Phim ảnh, xem rạp, thần tượng" },
      { id: "music", icon: "🎵", title: "音乐与爱好", sub: "Âm nhạc, sở thích nghe nhạc" },
      { id: "weather", icon: "🌧️", title: "天气与生活", sub: "Thời tiết, tâm trạng, khí hậu" },
      { id: "shopping", icon: "🛍️", title: "逛街与网购", sub: "Mua sắm, săn sale Taobao, thời trang" },
      { id: "fitness", icon: "🏋️", title: "健身与运动", sub: "Tập gym, chạy bộ, giữ dáng" },
      { id: "pets", icon: "🐾", title: "萌宠与动物", sub: "Nuôi mèo chó, thú cưng đáng yêu" },
      { id: "money", icon: "💰", title: "消费与理财", sub: "Chi tiêu, tiền bạc, tiết kiệm" },
      { id: "books", icon: "📚", title: "学习与阅读", sub: "Đọc sách, học tiếng Trung, tiến bộ" },
      { id: "commute", icon: "🚗", title: "交通与出行", sub: "Tàu điện ngầm, xe cộ, đi lại" },
      { id: "weekend", icon: "🏖️", title: "周末去哪儿", sub: "Kế hoạch cuối tuần, xả hơi" }
    ]
  };

  let currentTopic = "free";

  function renderTopicHub() {
    stopAllSpeech();
    chatHistory = [];
    turnCount = 0;
    currentTopic = "";
    suggestionsContainer.style.display = 'none';
    currentScenarioTitle.textContent = "🎯 Chọn Chủ Đề";

    const isZh = currentLang === 'zh';
    const topics = TOPIC_PRESETS[currentLang] || TOPIC_PRESETS.en;

    chatMessages.innerHTML = `
      <div class="topic-hub-container" id="topic-hub">
        <div class="topic-hub-header">
          <div class="topic-hub-badge">🎯 ${isZh ? '选择口语交流主题' : 'TỪ KHÓA CHỦ ĐỀ ĐÀM THOẠI'}</div>
          <h2 class="topic-hub-title">${isZh ? '今天你想聊什么话题？' : 'Hôm nay bạn muốn luyện nói về chủ đề gì?'}</h2>
          <p class="topic-hub-subtitle">${isZh ? '选择下方生活主题关键词，或直接输入你想聊的任意话题：' : 'Chọn một từ khóa gợi ý bên dưới hoặc tự nhập chủ đề bạn thích để bắt đầu nhé:'}</p>
        </div>

        <div class="topic-custom-box">
          <input type="text" id="input-custom-topic" placeholder="${isZh ? '💡 输入任意话题 (例如: 去三亚旅游、吃火锅、宠物狗...)' : '💡 Tự nhập chủ đề bạn thích (vd: Đi phượt Đà Lạt, Mua xe mới, Thú cưng...)'}" />
          <button id="btn-start-custom-topic">${isZh ? '开始 ➔' : 'Bắt Đầu ➔'}</button>
        </div>

        <div class="topic-chips-grid">
          ${topics.map(t => `
            <div class="topic-chip-item ${t.isDefault ? 'topic-chip-default' : ''}" data-topic="${t.id === 'free' ? 'free' : escapeHtml(t.title)}">
              <span class="topic-chip-icon">${t.icon}</span>
              <div class="topic-chip-info">
                <span class="topic-chip-title">${escapeHtml(t.title)} ${t.isDefault ? '<span class="default-badge">⭐ Mặc định</span>' : ''}</span>
                <span class="topic-chip-sub">${escapeHtml(t.sub)}</span>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    const chips = chatMessages.querySelectorAll('.topic-chip-item');
    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        const selectedTopic = chip.getAttribute('data-topic');
        startTopicConversation(selectedTopic, true);
      });
    });

    const btnCustom = chatMessages.querySelector('#btn-start-custom-topic');
    const inputCustom = chatMessages.querySelector('#input-custom-topic');
    if (btnCustom && inputCustom) {
      const handleCustom = () => {
        const val = inputCustom.value.trim();
        if (val) {
          startTopicConversation(val, true);
        } else {
          startTopicConversation('free', true);
        }
      };
      btnCustom.addEventListener('click', handleCustom);
      inputCustom.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleCustom();
      });
    }
  }

  async function startTopicConversation(topicName, autoPlay = true) {
    const isFree = !topicName || topicName === 'free' || topicName.toLowerCase().includes('free') || topicName.toLowerCase().includes('tự do') || topicName.toLowerCase().includes('casual') || topicName.toLowerCase().includes('闲聊');

    currentTopic = isFree ? 'free' : topicName;
    if (isFree) {
      currentScenarioTitle.textContent = currentLang === 'zh'
        ? "🎯 Trò Chuyện Tự Do (日常闲聊)"
        : "🎯 Trò Chuyện Tự Do (Casual Talk)";
    } else {
      currentScenarioTitle.textContent = `🎯 ${topicName.split('(')[0].trim()}`;
    }

    chatHistory = [];
    turnCount = 1;

    chatMessages.innerHTML = `
      <div class="msg-row bot" id="temp-topic-loading">
        <div class="msg-bubble" style="opacity: 0.9; font-size: 0.88rem; color: #94a3b8;">
          ✨ Gia sư AI đang kết nối cuộc trò chuyện về <b>"${escapeHtml(isFree ? (currentLang === 'zh' ? 'Trò chuyện tự do' : 'Casual Daily Talk') : topicName)}"</b>...
        </div>
      </div>
    `;

    try {
      const res = await fetch('/api/topic/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: isFree ? 'free' : topicName,
          lang: currentLang
        })
      });
      const data = await res.json();
      const loadingEl = document.getElementById('temp-topic-loading');
      if (loadingEl) loadingEl.remove();

      if (data.success && data.aiResult) {
        const botReply = currentLang === 'zh'
          ? (data.aiResult.reply_hanzi || '')
          : (data.aiResult.reply || '');
        chatHistory.push({ role: 'assistant', content: botReply });
        appendBotMessage(data.aiResult, data.audio, autoPlay);
      } else {
        alert(data.detail || 'Lỗi khởi tạo chủ đề');
      }
    } catch (err) {
      const loadingEl = document.getElementById('temp-topic-loading');
      if (loadingEl) loadingEl.remove();
      alert('Lỗi kết nối: ' + err.message);
    }
  }

  async function loadScenarios() {
    try {
      const res = await fetch(`/api/scenarios?lang=${currentLang}`);
      const data = await res.json();
      scenariosList = data.scenarios;

      if (scenariosList.length > 0) {
        selectScenario(scenariosList[0]);
      }
      renderScenariosModal();
    } catch (err) {
      console.error('Lỗi nạp tình huống:', err);
    }
  }

  function renderScenariosModal() {
    scenariosListContainer.innerHTML = '';
    scenariosList.forEach(s => {
      const isCurrent = currentScenario && (s.id === currentScenario.id);
      const card = document.createElement('div');
      card.className = `scenario-card-item ${isCurrent ? 'active' : ''}`;
      card.innerHTML = `
        <div class="scenario-card-title">${escapeHtml(s.title)}</div>
        <div class="scenario-card-desc">${escapeHtml(s.description)}</div>
      `;
      card.addEventListener('click', () => {
        selectScenario(s);
        modalScenarios.style.display = 'none';
      });
      scenariosListContainer.appendChild(card);
    });

    if (scenariosList.length <= 1) {
      const upcomingCard = document.createElement('div');
      upcomingCard.className = 'scenario-card-item';
      upcomingCard.style.cssText = 'border: 1px dashed rgba(56, 189, 248, 0.4); background: rgba(56, 189, 248, 0.05); cursor: default; opacity: 0.9; margin-top: 10px;';
      upcomingCard.innerHTML = `
        <div class="scenario-card-title" style="color: #38bdf8; font-size: 0.95rem;">🚀 Tình huống theo chủ đề (Đang hoàn thiện)</div>
        <div class="scenario-card-desc" style="font-size: 0.8rem; line-height: 1.45; color: #94a3b8; margin-top: 4px;">
          Các chủ đề giao tiếp thực tế (Gọi đồ uống, Mua sắm mặc cả, Đặt phòng khách sạn, Phỏng vấn xin việc, Sân bay...) đang được tác giả hệ thống hóa bài bản và sẽ sớm cập nhật trong các phiên bản tiếp theo.
        </div>
      `;
      scenariosListContainer.appendChild(upcomingCard);
    }
  }

  function selectScenario(scenario) {
    currentScenario = scenario;
    currentScenarioTitle.textContent = scenario.title.split('(')[0].trim();
    chatMessages.innerHTML = '';
    chatHistory = [];
    turnCount = 0;

    const initialSuggestions = (scenario.initialSuggestions && scenario.initialSuggestions.length > 0)
      ? scenario.initialSuggestions
      : [];

    // Lời mở đầu của AI
    if (currentLang === 'zh') {
      const initialText = scenario.initialHanzi;
      chatHistory.push({ role: 'assistant', content: initialText });
      appendBotMessage({
        reply_hanzi: scenario.initialHanzi,
        reply_pinyin: scenario.initialPinyin,
        translation_vi: scenario.initialTranslation,
        feedback: "Bấm vào biểu tượng loa 🔊 để nghe phát âm mẫu, hoặc bấm vào các câu gợi ý phía dưới để bắt đầu nói!",
        suggested_replies: initialSuggestions
      });
      playSpeechWithFallback(scenario.initialHanzi, 'zh', null, null);
    } else {
      const initialText = scenario.initialMessage;
      chatHistory.push({ role: 'assistant', content: initialText });
      appendBotMessage({
        reply: scenario.initialMessage,
        reply_ipa: scenario.initialIpa || '',
        translation_vi: scenario.initialTranslation,
        feedback: "Welcome! Tap the speaker 🔊 to hear native pronunciation, or tap any suggestion chip below to reply!",
        suggested_replies: initialSuggestions
      });
      playSpeechWithFallback(scenario.initialMessage, 'en', null, null);
    }
  }

  // 4. CHAT RENDERING
  function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'msg-row user';
    row.innerHTML = `<div class="msg-bubble">${escapeHtml(text)}</div>`;
    chatMessages.appendChild(row);
    scrollToBottom();
  }

  function appendBotMessage(data, audioUrl = null, autoPlay = true) {
    const row = document.createElement('div');
    row.className = 'msg-row bot';

    let contentHtml = '';
    const speakText = currentLang === 'zh' ? (data.reply_hanzi || '') : (data.reply || '');

    if (currentLang === 'zh') {
      contentHtml = `
        <div style="display:flex; align-items:flex-start;">
          <button class="speaker-btn" data-speak="${escapeHtml(speakText)}">🔊</button>
          <div style="flex:1;">
            <span class="hanzi-text">${escapeHtml(data.reply_hanzi)}</span>
            ${data.reply_pinyin ? `<span class="pinyin-text" style="display:${showPinyin ? 'block' : 'none'};">${escapeHtml(data.reply_pinyin)}</span>` : ''}
            ${data.translation_vi ? `<span class="translation-text" style="display:${showTranslation ? 'block' : 'none'};">${escapeHtml(data.translation_vi)}</span>` : ''}
          </div>
        </div>
      `;
    } else {
      contentHtml = `
        <div style="display:flex; align-items:flex-start;">
          <button class="speaker-btn" data-speak="${escapeHtml(speakText)}">🔊</button>
          <div style="flex:1;">
            <span class="hanzi-text" style="font-size:1.05rem; font-weight:600; color:#f8fafc;">${escapeHtml(data.reply)}</span>
            ${data.reply_ipa ? `<span class="pinyin-text" style="display:${showPinyin ? 'block' : 'none'};">${escapeHtml(data.reply_ipa)}</span>` : ''}
            ${data.translation_vi ? `<span class="translation-text" style="display:${showTranslation ? 'block' : 'none'};">${escapeHtml(data.translation_vi)}</span>` : ''}
          </div>
        </div>
      `;
    }

    if (data.feedback) {
      contentHtml += `
        <div class="feedback-box">
          <span class="feedback-title">💡 Góp ý của Gia sư:</span>
          <span class="feedback-desc">${escapeHtml(data.feedback)}</span>
        </div>
      `;
    }

    row.innerHTML = `<div class="msg-bubble">${contentHtml}</div>`;
    chatMessages.appendChild(row);

    const speakerBtn = row.querySelector('.speaker-btn');
    if (speakerBtn) {
      speakerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const textToPlay = e.currentTarget.getAttribute('data-speak') || speakText;
        playSpeechWithFallback(textToPlay, currentLang, audioUrl, speakerBtn);
      });
    }

    renderSuggestions(data.suggested_replies || []);
    scrollToBottom();

    if (audioUrl && autoPlay) {
      playSpeechWithFallback(speakText, currentLang, audioUrl, speakerBtn);
    }
  }

  function parseSuggestionItem(item, lang) {
    if (!item) return { main: '', pinyin: '', trans: '', cleanMsg: '' };

    let main = item;
    let pinyin = '';
    let trans = '';

    const match = item.match(/^(.*?)\s*[\(（](.*?)[\)）]\s*$/);
    if (match) {
      main = match[1].trim();
      const inside = match[2].trim();
      if (inside.includes(' - ')) {
        const parts = inside.split(' - ');
        pinyin = parts[0].trim();
        trans = parts.slice(1).join(' - ').trim();
      } else if (inside.includes(' – ')) {
        const parts = inside.split(' – ');
        pinyin = parts[0].trim();
        trans = parts.slice(1).join(' – ').trim();
      } else if (inside.includes('-') && (lang === 'zh' || inside.includes('/'))) {
        const parts = inside.split('-');
        pinyin = parts[0].trim();
        trans = parts.slice(1).join('-').trim();
      } else {
        if (lang === 'zh') {
          pinyin = inside;
        } else {
          if (inside.startsWith('/') && inside.endsWith('/')) {
            pinyin = inside;
          } else {
            trans = inside;
          }
        }
      }
    } else {
      if (item.includes(' - ')) {
        const parts = item.split(' - ');
        main = parts[0].trim();
        trans = parts.slice(1).join(' - ').trim();
      }
    }

    return { main, pinyin, trans, cleanMsg: main };
  }

  let currentSuggestionsList = [];
  let currentSuggestionIndex = 0;

  function renderSuggestions(suggestions) {
    if (!suggestions || suggestions.length === 0) {
      suggestionsContainer.style.display = 'none';
      currentSuggestionsList = [];
      currentSuggestionIndex = 0;
      return;
    }

    currentSuggestionsList = suggestions;
    currentSuggestionIndex = 0;
    displayCurrentSuggestion();
    suggestionsContainer.style.display = 'block';
  }

  function displayCurrentSuggestion() {
    suggestionsList.innerHTML = '';
    if (!currentSuggestionsList || currentSuggestionsList.length === 0) {
      suggestionsContainer.style.display = 'none';
      return;
    }

    const item = currentSuggestionsList[currentSuggestionIndex];
    const parsed = parseSuggestionItem(item, currentLang);

    const chip = document.createElement('div');
    chip.className = 'suggestion-chip';

    let innerHtml = `
      <div class="chip-header-row">
        <span class="chip-speaker-btn" title="Nghe phát âm mẫu">🔊</span>
        <span class="chip-main-text">${escapeHtml(parsed.main)}</span>
      </div>
    `;

    if (parsed.pinyin) {
      innerHtml += `<div class="chip-pinyin-row pinyin-text" style="display:${showPinyin ? 'block' : 'none'};">${escapeHtml(parsed.pinyin)}</div>`;
    }

    if (parsed.trans) {
      innerHtml += `<div class="chip-trans-row translation-text" style="display:${showTranslation ? 'block' : 'none'};">${escapeHtml(parsed.trans)}</div>`;
    }

    chip.innerHTML = innerHtml;

    // Bấm vào biểu tượng loa 🔊 -> nghe phát âm mẫu
    const speakerBtn = chip.querySelector('.chip-speaker-btn');
    if (speakerBtn) {
      speakerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        playSpeechWithFallback(parsed.cleanMsg, currentLang, null, speakerBtn);
      });
    }

    // Bấm vào thân thẻ -> gửi tin nhắn
    chip.addEventListener('click', () => {
      sendUserMessage(parsed.cleanMsg);
    });

    suggestionsList.appendChild(chip);

    if (btnRefreshSuggestions) {
      btnRefreshSuggestions.textContent = '🔄 Gợi ý khác';
    }
  }

  // Đổi gợi ý khác: Chuyển ngay sang gợi ý tiếp theo, hết vòng thì gọi AI
  if (btnRefreshSuggestions) {
    btnRefreshSuggestions.addEventListener('click', async () => {
      // 1. Nếu còn gợi ý trong danh sách hiện tại -> chuyển ngay tức thì (0ms trễ)
      if (currentSuggestionsList && currentSuggestionsList.length > 1 && currentSuggestionIndex < currentSuggestionsList.length - 1) {
        currentSuggestionIndex++;
        displayCurrentSuggestion();
        return;
      }

      // 2. Nếu đã xem hết danh sách hiện tại -> gọi AI lấy 3 gợi ý mới
      try {
        btnRefreshSuggestions.textContent = '⏳ Đang tìm...';
        btnRefreshSuggestions.style.opacity = '0.6';
        btnRefreshSuggestions.disabled = true;

        const res = await fetch('/api/suggestions/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lang: currentLang,
            scenarioId: currentTopic || (currentLang === 'zh' ? '日常闲聊' : 'Casual Daily Talk'),
            turnCount: turnCount,
            history: chatHistory.slice(-4)
          })
        });
        const data = await res.json();
        if (data.success && data.suggestions && data.suggestions.length > 0) {
          currentSuggestionsList = data.suggestions;
          currentSuggestionIndex = 0;
          displayCurrentSuggestion();
        } else {
          // Quay lại câu đầu nếu không lấy được thêm
          currentSuggestionIndex = 0;
          displayCurrentSuggestion();
        }
      } catch (err) {
        console.warn('Lỗi đổi gợi ý:', err);
        currentSuggestionIndex = 0;
        displayCurrentSuggestion();
      } finally {
        btnRefreshSuggestions.textContent = '🔄 Gợi ý khác';
        btnRefreshSuggestions.style.opacity = '1';
        btnRefreshSuggestions.disabled = false;
      }
    });
  }

  // --- ROBUST AUDIO PLAYBACK ENGINE (CHỐNG ĐƠ, PHÒNG NGỪA AUTOPLAY SAFARI & DỰ PHÒNG NATIVE) ---
  let sharedAudio = null;
  let isAudioUnlocked = false;

  function unlockAudio() {
    if (isAudioUnlocked) return;
    try {
      if (!sharedAudio) sharedAudio = new Audio();
      sharedAudio.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
      sharedAudio.play().then(() => {
        isAudioUnlocked = true;
      }).catch(() => {});
    } catch (e) {}
  }
  document.addEventListener('touchstart', unlockAudio, { once: true });
  document.addEventListener('click', unlockAudio, { once: true });

  // Khởi động trước voices Web Speech
  if ('speechSynthesis' in window) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
  }

  function stopAllSpeech() {
    if (sharedAudio) {
      try {
        sharedAudio.pause();
        sharedAudio.currentTime = 0;
      } catch (e) {}
    }
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {}
    }
    document.querySelectorAll('.speaker-btn, .chip-speaker-btn').forEach(btn => {
      btn.textContent = '🔊';
      btn.classList.remove('playing');
    });
  }

  async function playSpeechWithFallback(text, lang, audioDataUrl = null, btnElement = null) {
    if (!text || !text.trim()) return;

    stopAllSpeech();

    if (btnElement) {
      btnElement.textContent = '🔊🎶';
      btnElement.classList.add('playing');
    }

    const resetButton = () => {
      if (btnElement) {
        btnElement.textContent = '🔊';
        btnElement.classList.remove('playing');
      }
    };

    // 1. Thử phát từ audioDataUrl có sẵn từ Edge-TTS
    if (audioDataUrl && audioDataUrl.startsWith('data:audio')) {
      try {
        if (!sharedAudio) sharedAudio = new Audio();
        sharedAudio.src = audioDataUrl;
        sharedAudio.playbackRate = currentSpeechRate;
        sharedAudio.onended = resetButton;
        sharedAudio.onerror = () => {
          fallbackWebSpeech(text, lang, resetButton);
        };
        await sharedAudio.play();
        return;
      } catch (err) {
        console.warn('Audio play error, chuyển sang Web Speech:', err);
      }
    }

    // 2. Nếu chưa có audioDataUrl, thử lấy từ /api/tts (timeout 3.5s chống đơ)
    let fetchedAudioUrl = null;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3500);

      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, lang }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      const data = await res.json();
      if (data.audio && data.audio.startsWith('data:audio')) {
        fetchedAudioUrl = data.audio;
      }
    } catch (err) {
      console.warn('Fetch /api/tts timeout hoặc lỗi:', err);
    }

    if (fetchedAudioUrl) {
      try {
        if (!sharedAudio) sharedAudio = new Audio();
        sharedAudio.src = fetchedAudioUrl;
        sharedAudio.playbackRate = currentSpeechRate;
        sharedAudio.onended = resetButton;
        sharedAudio.onerror = () => {
          fallbackWebSpeech(text, lang, resetButton);
        };
        await sharedAudio.play();
        return;
      } catch (err) {
        console.warn('Play fetched audio bị chặn, chuyển sang Web Speech:', err);
      }
    }

    // 3. Dự phòng cấp cao nhất: Trình phát giọng nói Web Speech API tích hợp của thiết bị
    fallbackWebSpeech(text, lang, resetButton);
  }

  function fallbackWebSpeech(text, lang, onEndCallback) {
    if (!('speechSynthesis' in window)) {
      if (onEndCallback) onEndCallback();
      return;
    }

    try {
      window.speechSynthesis.cancel();
      const cleanText = text.replace(/[\(\)\[\]（）\*]/g, ' ').trim();
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = lang === 'zh' ? 'zh-CN' : 'en-US';
      utterance.rate = currentSpeechRate;

      const voices = window.speechSynthesis.getVoices();
      if (voices && voices.length > 0) {
        const targetPrefix = lang === 'zh' ? 'zh' : 'en';
        const bestVoice = voices.find(v => v.lang.toLowerCase().startsWith(targetPrefix));
        if (bestVoice) utterance.voice = bestVoice;
      }

      utterance.onend = () => {
        if (onEndCallback) onEndCallback();
      };
      utterance.onerror = () => {
        if (onEndCallback) onEndCallback();
      };

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.error('Web Speech error:', e);
      if (onEndCallback) onEndCallback();
    }
  }

  async function sendUserMessage(text) {
    if (!text || !text.trim()) return;
    appendUserMessage(text);
    inputCustomText.value = '';
    suggestionsContainer.style.display = 'none';

    turnCount++;
    chatHistory.push({ role: 'user', content: text });

    const loadingRow = document.createElement('div');
    loadingRow.className = 'msg-row bot';
    loadingRow.id = 'temp-loading-msg';
    loadingRow.innerHTML = `<div class="msg-bubble" style="color:#94a3b8; font-style:italic;">Gia sư đang nghe và chuẩn bị lời khuyên...</div>`;
    chatMessages.appendChild(loadingRow);
    scrollToBottom();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userText: text,
          lang: currentLang,
          scenarioId: currentTopic || (currentLang === 'zh' ? '日常闲聊' : 'Casual Daily Talk'),
          history: chatHistory.slice(-6),
          turnCount: turnCount
        })
      });

      const data = await res.json();
      const loadingEl = document.getElementById('temp-loading-msg');
      if (loadingEl) loadingEl.remove();

      if (data.success && data.aiResult) {
        const botReply = currentLang === 'zh' ? (data.aiResult.reply_hanzi || '') : (data.aiResult.reply || '');
        chatHistory.push({ role: 'assistant', content: botReply });
        appendBotMessage(data.aiResult, data.audio);
      } else {
        alert(data.detail || 'Lỗi xử lý phản hồi từ AI');
      }
    } catch (err) {
      const loadingEl = document.getElementById('temp-loading-msg');
      if (loadingEl) loadingEl.remove();
      alert('Lỗi kết nối: ' + err.message);
    }
  }

  btnSendText.addEventListener('click', () => {
    if (isRecording) {
      finishAndSendSpeech();
    } else {
      sendUserMessage(inputCustomText.value);
    }
  });

  inputCustomText.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      if (isRecording) {
        finishAndSendSpeech();
      } else {
        sendUserMessage(inputCustomText.value);
      }
    }
  });

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // 5. MODAL EVENT HANDLERS
  if (currentScenarioTitle) {
    currentScenarioTitle.style.cursor = 'pointer';
    currentScenarioTitle.title = 'Bấm vào đây để chọn chủ đề khác';
    currentScenarioTitle.addEventListener('click', () => {
      renderTopicHub();
    });
  }
  btnShowScenarios.addEventListener('click', () => {
    renderTopicHub();
  });
  btnCloseScenarios.addEventListener('click', () => {
    modalScenarios.style.display = 'none';
  });

  btnOpenSettings.addEventListener('click', () => {
    modalSettings.style.display = 'flex';
  });
  btnCloseSettings.addEventListener('click', () => {
    modalSettings.style.display = 'none';
  });

  if (btnOpenDonate) {
    btnOpenDonate.addEventListener('click', () => {
      modalDonate.style.display = 'flex';
    });
  }
  if (btnOpenShare) {
    btnOpenShare.addEventListener('click', () => {
      modalDonate.style.display = 'flex';
    });
  }
  if (btnCloseDonate) {
    btnCloseDonate.addEventListener('click', () => {
      modalDonate.style.display = 'none';
    });
  }
  if (btnDoneDonate) {
    btnDoneDonate.addEventListener('click', () => {
      modalDonate.style.display = 'none';
    });
  }

  // --- SOCIAL SHARE & DONATE LOGIC ---
  function getAppShareUrl() {
    return (window.location.origin && window.location.origin !== 'null' && window.location.protocol.startsWith('http'))
      ? window.location.origin + '/'
      : 'https://giasungoaingufree.onrender.com/';
  }

  function showToast(message) {
    let toast = document.getElementById('app-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'app-toast';
      toast.className = 'app-toast';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
      toast.classList.remove('show');
    }, 2500);
  }

  function copyToClipboard(text, successMsg) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showToast(successMsg);
      }).catch(() => {
        fallbackCopy(text, successMsg);
      });
    } else {
      fallbackCopy(text, successMsg);
    }
  }

  function fallbackCopy(text, successMsg) {
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      showToast(successMsg);
    } catch (e) {
      showToast('⚠️ Không thể sao chép tự động!');
    }
  }

  if (btnShareFb) {
    btnShareFb.addEventListener('click', () => {
      const url = encodeURIComponent(getAppShareUrl());
      window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank', 'noopener,noreferrer');
    });
  }

  if (btnShareZalo) {
    btnShareZalo.addEventListener('click', () => {
      const url = encodeURIComponent(getAppShareUrl());
      window.open(`https://sp.zalo.me/plugins/share?url=${url}`, '_blank', 'noopener,noreferrer');
    });
  }

  if (btnShareTelegram) {
    btnShareTelegram.addEventListener('click', () => {
      const url = encodeURIComponent(getAppShareUrl());
      const text = encodeURIComponent('Gia Sư Ngoại Ngữ Free — Luyện nói Tiếng Anh & Tiếng Trung cùng AI miễn phí!');
      window.open(`https://t.me/share/url?url=${url}&text=${text}`, '_blank', 'noopener,noreferrer');
    });
  }

  if (btnShareCopy) {
    btnShareCopy.addEventListener('click', () => {
      copyToClipboard(getAppShareUrl(), '📋 Đã sao chép liên kết web!');
    });
  }

  if (btnShareNative && navigator.share) {
    btnShareNative.style.display = 'inline-flex';
    btnShareNative.addEventListener('click', async () => {
      try {
        await navigator.share({
          title: 'Gia Sư Ngoại Ngữ Free',
          text: 'Luyện nói Tiếng Anh & Tiếng Trung cùng AI miễn phí, không cần cài đặt!',
          url: getAppShareUrl()
        });
      } catch (e) {
        // User cancelled share
      }
    });
  }

  if (btnCopyAcc) {
    btnCopyAcc.addEventListener('click', () => {
      const acc = document.getElementById('donate-acc')?.textContent?.trim() || '8335897';
      copyToClipboard(acc, '💳 Đã sao chép STK: ' + acc);
    });
  }

  if (btnCopyContent) {
    btnCopyContent.addEventListener('click', () => {
      const content = document.getElementById('donate-content')?.textContent?.trim() || 'Thanhbooks - Cafe ung ho';
      copyToClipboard(content, '💬 Đã sao chép nội dung CK!');
    });
  }

  // --- HƯỚNG DẪN GHIM APP RA MÀN HÌNH CHÍNH (PWA INSTALL GUIDE) ---
  const modalInstallGuide = document.getElementById('modal-install-guide');
  const btnOpenInstallGuide = document.getElementById('btn-open-install-guide');
  const btnOpenInstallGuideSettings = document.getElementById('btn-open-install-guide-settings');
  const btnCloseInstallGuide = document.getElementById('btn-close-install-guide');
  const btnCloseGuideDone = document.getElementById('btn-close-guide-done');
  const tabBtnIos = document.getElementById('tab-btn-ios');
  const tabBtnAndroid = document.getElementById('tab-btn-android');
  const guideContentIos = document.getElementById('guide-content-ios');
  const guideContentAndroid = document.getElementById('guide-content-android');
  const androidPwaBanner = document.getElementById('android-pwa-banner');
  const btnTriggerPwa = document.getElementById('btn-trigger-pwa');

  function switchInstallTab(tab) {
    if (tab === 'ios') {
      if (tabBtnIos) tabBtnIos.classList.add('active');
      if (tabBtnAndroid) tabBtnAndroid.classList.remove('active');
      if (guideContentIos) guideContentIos.style.display = 'block';
      if (guideContentAndroid) guideContentAndroid.style.display = 'none';
    } else {
      if (tabBtnAndroid) tabBtnAndroid.classList.add('active');
      if (tabBtnIos) tabBtnIos.classList.remove('active');
      if (guideContentAndroid) guideContentAndroid.style.display = 'block';
      if (guideContentIos) guideContentIos.style.display = 'none';
    }
  }

  function openInstallGuideModal() {
    const isAndroid = /Android/i.test(navigator.userAgent);
    switchInstallTab(isAndroid ? 'android' : 'ios');
    if (modalInstallGuide) modalInstallGuide.style.display = 'flex';
  }

  if (btnOpenInstallGuide) {
    btnOpenInstallGuide.addEventListener('click', () => {
      if (modalDonate) modalDonate.style.display = 'none';
      openInstallGuideModal();
    });
  }

  if (btnOpenInstallGuideSettings) {
    btnOpenInstallGuideSettings.addEventListener('click', () => {
      if (modalSettings) modalSettings.style.display = 'none';
      openInstallGuideModal();
    });
  }

  if (btnCloseInstallGuide) {
    btnCloseInstallGuide.addEventListener('click', () => {
      if (modalInstallGuide) modalInstallGuide.style.display = 'none';
    });
  }

  if (btnCloseGuideDone) {
    btnCloseGuideDone.addEventListener('click', () => {
      if (modalInstallGuide) modalInstallGuide.style.display = 'none';
    });
  }

  if (tabBtnIos) {
    tabBtnIos.addEventListener('click', () => switchInstallTab('ios'));
  }

  if (tabBtnAndroid) {
    tabBtnAndroid.addEventListener('click', () => switchInstallTab('android'));
  }

  // Bắt sự kiện beforeinstallprompt (Android Chrome tự động)
  let deferredInstallPrompt = null;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    if (androidPwaBanner) {
      androidPwaBanner.style.display = 'block';
    }
  });

  if (btnTriggerPwa) {
    btnTriggerPwa.addEventListener('click', async () => {
      if (deferredInstallPrompt) {
        deferredInstallPrompt.prompt();
        const { outcome } = await deferredInstallPrompt.userChoice;
        if (outcome === 'accepted') {
          showToast('🎉 Đang tiến hành cài đặt ra Màn hình chính...');
          if (modalInstallGuide) modalInstallGuide.style.display = 'none';
        }
        deferredInstallPrompt = null;
      }
    });
  }

  btnSaveSettings.addEventListener('click', async () => {
    const geminiApiKey = inputApiKey.value.trim();
    const geminiModel = selectModel ? selectModel.value : 'gemini-3.5-flash-lite';
    const voiceEn = selectVoiceEn.value;
    const voiceZh = selectVoiceZh.value;

    if (selectSpeechRate) {
      currentSpeechRate = parseFloat(selectSpeechRate.value) || 1.0;
      localStorage.setItem('speechRate', currentSpeechRate);
      updateSpeedUI();
    }

    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ geminiApiKey, geminiModel, voiceEn, voiceZh })
      });
      const data = await res.json();
      if (data.success) {
        alert('Đã lưu cấu hình cài đặt thành công!');
        modalSettings.style.display = 'none';
        await loadConfig();
      }
    } catch (err) {
      alert('Lỗi lưu cài đặt: ' + err.message);
    }
  });

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // STARTUP
  initSpeechRecognition();
  loadConfig();
});
