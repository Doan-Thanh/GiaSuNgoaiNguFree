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
  const btnCloseDonate = document.getElementById('btn-close-donate');
  const btnDoneDonate = document.getElementById('btn-done-donate');
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
      await loadScenarios();
    } catch (err) {
      console.error('Lỗi tải cấu hình:', err);
    }
  }

  function updateLangUI() {
    langBtns.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === currentLang);
    });

    if (currentLang === 'zh') {
      togglePinyinBtn.style.display = 'flex';
      inputCustomText.placeholder = 'Nhập tiếng Trung hoặc bấm Mic để nói...';
    } else {
      togglePinyinBtn.style.display = 'none';
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
      await loadScenarios();
      fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ currentLang })
      });
    });
  });

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
      playTTSAudio(scenario.initialHanzi, 'zh');
    } else {
      const initialText = scenario.initialMessage;
      chatHistory.push({ role: 'assistant', content: initialText });
      appendBotMessage({
        reply: scenario.initialMessage,
        translation_vi: scenario.initialTranslation,
        feedback: "Welcome! Tap the speaker 🔊 to hear native pronunciation, or tap any suggestion chip below to reply!",
        suggested_replies: initialSuggestions
      });
      playTTSAudio(scenario.initialMessage, 'en');
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

  function appendBotMessage(data, audioUrl = null) {
    const row = document.createElement('div');
    row.className = 'msg-row bot';

    let contentHtml = '';
    const speakText = currentLang === 'zh' ? (data.reply_hanzi || '') : (data.reply || '');

    if (currentLang === 'zh') {
      contentHtml = `
        <div style="display:flex; align-items:flex-start;">
          <button class="speaker-btn" data-speak="${escapeHtml(speakText)}">🔊</button>
          <div style="flex:1;">
            ${data.reply_pinyin ? `<span class="pinyin-text" style="display:${showPinyin ? 'block' : 'none'};">${escapeHtml(data.reply_pinyin)}</span>` : ''}
            <span class="hanzi-text">${escapeHtml(data.reply_hanzi)}</span>
            ${data.translation_vi ? `<span class="translation-text" style="display:${showTranslation ? 'block' : 'none'};">${escapeHtml(data.translation_vi)}</span>` : ''}
          </div>
        </div>
      `;
    } else {
      contentHtml = `
        <div style="display:flex; align-items:flex-start;">
          <button class="speaker-btn" data-speak="${escapeHtml(speakText)}">🔊</button>
          <div style="flex:1;">
            <span>${escapeHtml(data.reply)}</span>
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

    row.querySelector('.speaker-btn').addEventListener('click', (e) => {
      const textToPlay = e.currentTarget.getAttribute('data-speak');
      if (audioUrl) {
        new Audio(audioUrl).play();
      } else {
        playTTSAudio(textToPlay, currentLang);
      }
    });

    renderSuggestions(data.suggested_replies || []);
    scrollToBottom();

    if (audioUrl) {
      const sound = new Audio(audioUrl);
      sound.play().catch(e => console.log('Autoplay blocked:', e));
    }
  }

  function renderSuggestions(suggestions) {
    if (!suggestions || suggestions.length === 0) {
      suggestionsContainer.style.display = 'none';
      return;
    }

    suggestionsList.innerHTML = '';
    suggestions.forEach(item => {
      let cleanMsg = item;
      // Xử lý cả dấu ngoặc đơn nửa góc '(' và dấu ngoặc đơn toàn góc '（' của tiếng Trung
      if (cleanMsg.includes('（')) {
        cleanMsg = cleanMsg.split('（')[0].trim();
      }
      if (cleanMsg.includes('(')) {
        cleanMsg = cleanMsg.split('(')[0].trim();
      }

      const chip = document.createElement('div');
      chip.className = 'suggestion-chip';
      chip.style.display = 'inline-flex';
      chip.style.alignItems = 'center';
      chip.style.gap = '6px';

      chip.innerHTML = `
        <span class="chip-speaker-btn" title="Nghe giọng đọc mẫu câu này" style="cursor:pointer; font-size:1.15rem; opacity:0.9; padding:2px 6px; border-radius:4px; transition:opacity 0.2s;">🔊</span>
        <span class="chip-text" title="Bấm để gửi ngay" style="cursor:pointer; font-size:1.02rem; font-weight:500; letter-spacing:0.2px;">${escapeHtml(item)}</span>
      `;

      // Bấm vào biểu tượng loa 🔊 -> nghe phát âm mẫu để luyện đọc theo
      const speakerBtn = chip.querySelector('.chip-speaker-btn');
      speakerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        speakerBtn.style.opacity = '1';
        speakerBtn.textContent = '⏳';
        playTTSAudio(cleanMsg, currentLang).finally(() => {
          speakerBtn.textContent = '🔊';
        });
      });

      // Bấm vào phần chữ -> gửi tin nhắn
      chip.querySelector('.chip-text').addEventListener('click', () => {
        sendUserMessage(cleanMsg);
      });

      suggestionsList.appendChild(chip);
    });
    suggestionsContainer.style.display = 'block';
  }

  // Đổi gợi ý khác
  if (btnRefreshSuggestions) {
    btnRefreshSuggestions.addEventListener('click', async () => {
      try {
        btnRefreshSuggestions.textContent = '⏳ Đang đổi...';
        btnRefreshSuggestions.style.opacity = '0.6';
        btnRefreshSuggestions.disabled = true;

        const res = await fetch('/api/suggestions/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lang: currentLang,
            scenarioId: currentScenario ? currentScenario.id : '',
            turnCount: turnCount,
            history: chatHistory.slice(-4)
          })
        });
        const data = await res.json();
        if (data.success && data.suggestions && data.suggestions.length > 0) {
          renderSuggestions(data.suggestions);
          suggestionsList.scrollLeft = 0;
        }
      } catch (err) {
        console.warn('Lỗi đổi gợi ý:', err);
      } finally {
        btnRefreshSuggestions.textContent = '🔄 Đổi gợi ý khác';
        btnRefreshSuggestions.style.opacity = '1';
        btnRefreshSuggestions.disabled = false;
      }
    });
  }

  async function playTTSAudio(text, lang) {
    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, lang })
      });
      const data = await res.json();
      if (data.audio) {
        new Audio(data.audio).play();
      }
    } catch (err) {
      console.warn('Lỗi phát âm TTS:', err);
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
          scenarioId: currentScenario ? currentScenario.id : '',
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
    currentScenarioTitle.title = 'Bấm vào đây để chọn tình huống khác';
    currentScenarioTitle.addEventListener('click', () => {
      modalScenarios.style.display = 'flex';
    });
  }
  btnShowScenarios.addEventListener('click', () => {
    modalScenarios.style.display = 'flex';
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

  btnSaveSettings.addEventListener('click', async () => {
    const geminiApiKey = inputApiKey.value.trim();
    const geminiModel = selectModel ? selectModel.value : 'gemini-3.5-flash-lite';
    const voiceEn = selectVoiceEn.value;
    const voiceZh = selectVoiceZh.value;

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
