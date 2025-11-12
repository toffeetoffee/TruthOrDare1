/* global bootstrap, io, TODToast */
(function(){
  const app = document.getElementById('roomApp');
  if (!app) return;

  const ROOM = (app.dataset.roomCode || '').toUpperCase();
  const NAME = app.dataset.playerName || app.dataset.playerName || '';
  const IS_HOST = app.dataset.isHost === '1';

  const els = {
    codeBadge: document.getElementById('roomCodeBadge'),
    playerList: document.getElementById('playerList'),
    playerCount: document.getElementById('playerCount'),
    selectedPlayer: document.getElementById('selectedPlayer'),
    timerBar: document.getElementById('timerBar'),
    timerLabel: document.getElementById('timerLabel'),
    roundBadge: document.getElementById('roundBadge'),
    phaseBadge: document.getElementById('phaseBadge'),
    copyBtn: document.getElementById('copyCodeBtn'),
    leaveBtn: document.getElementById('leaveRoomBtn'),
    hostControls: document.getElementById('hostControls'),
    // Panels
    pCountdown: document.getElementById('panel-countdown'),
    pPreparation: document.getElementById('panel-preparation'),
    pSelection: document.getElementById('panel-selection'),
    pMinigame: document.getElementById('panel-minigame'),
    pTruthDare: document.getElementById('panel-truthdare'),
    // Preparation
    contributeForm: document.getElementById('contributeForm'),
    targetPlayers: document.getElementById('targetPlayers'),
    phaseSubs: document.getElementById('phaseSubmissions'),
    // Truth/Dare
    voteSkipBtn: document.getElementById('voteSkipBtn'),
    tdType: document.getElementById('tdType'),
    tdPlayer: document.getElementById('tdPlayer'),
    tdContent: document.getElementById('tdContent'),
    tdSubmittedBy: document.getElementById('tdSubmittedBy'),
    // History
    historyBody: document.getElementById('historyBody'),
    historyList: document.getElementById('historyList'),
    expandHistoryBtn: document.getElementById('expandHistoryBtn'),
    // Host
    startBtn: document.getElementById('startGameBtn'),
    endBtn: document.getElementById('endGameBtn'),
    destroyBtn: document.getElementById('destroyRoomBtn'),
    // Settings
    settingsModal: document.getElementById('settingsModal'),
    settingsForm: document.getElementById('settingsForm'),
    applySettingsBtn: document.getElementById('applySettingsBtn'),
    // Defaults
    defaultsModal: document.getElementById('defaultsModal'),
    defaultsTruths: document.getElementById('defaultsTruths'),
    defaultsDares: document.getElementById('defaultsDares'),
    presetFile: document.getElementById('presetFile'),
    savePresetBtn: document.getElementById('savePresetBtn'),
    applyDefaultsBtn: document.getElementById('applyDefaultsBtn'),
  };

  // Show host controls if host
  if (IS_HOST) els.hostControls.classList.remove('d-none');
  if (ROOM) els.codeBadge.textContent = ROOM;

  // Socket.IO
  const socket = io({ transports: ['websocket', 'polling'] });

  // Helpers
  let timerInterval = null;
  function setPhase(name){
    const panels = [els.pCountdown, els.pPreparation, els.pSelection, els.pMinigame, els.pTruthDare];
    panels.forEach(p => p.classList.add('d-none'));
    switch(name){
      case 'countdown': els.pCountdown.classList.remove('d-none'); break;
      case 'preparation': els.pPreparation.classList.remove('d-none'); break;
      case 'selection': els.pSelection.classList.remove('d-none'); break;
      case 'minigame': els.pMinigame.classList.remove('d-none'); break;
      case 'truthdare': els.pTruthDare.classList.remove('d-none'); break;
      default: break;
    }
    els.phaseBadge.textContent = name.charAt(0).toUpperCase() + name.slice(1);
  }

  function startTimer(totalSeconds){
    clearInterval(timerInterval);
    let left = totalSeconds;
    function render(){
      const pct = Math.max(0, Math.min(100, 100 * (left / totalSeconds)));
      els.timerBar.style.width = pct.toFixed(1) + '%';
      els.timerLabel.textContent = `${Math.max(0, Math.ceil(left))}s`;
    }
    render();
    timerInterval = setInterval(() => {
      left -= 0.1;
      render();
      if (left <= 0) clearInterval(timerInterval);
    }, 100);
  }

  function renderPlayers(players, selectedId){
    els.playerList.innerHTML = '';
    players.forEach(p => {
      const li = document.createElement('li');
      li.className = 'list-group-item d-flex align-items-center justify-content-between';
      if (selectedId && p.id === selectedId) li.classList.add('selected');
      const you = p.name === NAME ? ' <span class="badge text-bg-info ms-1">you</span>' : '';
      li.innerHTML = `<span>${p.name}${you}</span><span class="badge text-bg-secondary">${p.score ?? 0}</span>`;
      els.playerList.appendChild(li);
    });
    els.playerCount.textContent = players.length;
    // update target checkboxes for preparation phase
    els.targetPlayers.innerHTML = '';
    players.forEach(p => {
      if (p.name === NAME) return; // cannot target yourself
      const id = 'tgt-' + p.id;
      const w = document.createElement('div');
      w.className = 'form-check';
      w.innerHTML = `<input class="form-check-input" type="checkbox" value="${p.id}" id="${id}">
                     <label class="form-check-label" for="${id}">${p.name}</label>`;
      els.targetPlayers.appendChild(w);
    });
  }

  function addHistoryItem(item){
    const li = document.createElement('li');
    li.className = 'list-group-item';
    const sb = item.submitted_by ? ` · Submitted by ${item.submitted_by}` : '';
    li.innerHTML = `<div><b>Round ${item.round}</b> · <b>${item.type}</b> for <b>${item.player}</b></div>
                    <div>${item.content}</div>
                    <div class="small text-body-secondary">Duration ${item.duration || '-'}s${sb}</div>`;
    els.historyList.prepend(li);
  }

  // Initial join/create sequence
  socket.on('connect', () => {
    if (ROOM) {
      socket.emit('join', { room: ROOM, name: NAME });
    } else {
      // Creating a room via socket if route used /room/new
      // creation via /create route
    }
  });

  // Room created (server returns a new room code)
  socket.on('room_created', (data) => {
    const code = (data && data.room_code || '').toUpperCase();
    if (code && !ROOM) {
      els.codeBadge.textContent = code;
      history.replaceState({}, '', `/room/${code}?name=${encodeURIComponent(NAME)}&host=${IS_HOST ? '1':'0'}`);
      TODToast.show('Room Created', `Code: <b>${code}</b>`, 'success');
    }
  });

  // Room/Players state updates
  socket.on('game_state_update', (state) => {
    // expected: { room_code, players: [{id,name,score}], round, phase, phase_seconds_left, selected_player_id }
    if (!state) return;
    if (state.room_code) els.codeBadge.textContent = state.room_code;
    if (Array.isArray(state.players)) renderPlayers(state.players, state.selected_player_id);
    if (typeof state.round === 'number') els.roundBadge.textContent = `Round ${state.round}`;
    if (state.phase) setPhase(state.phase);
    if (typeof state.phase_seconds_left === 'number') startTimer(state.phase_seconds_left);
    const sel = (state.players || []).find(p => p.id === state.selected_player_id);
    els.selectedPlayer.textContent = sel ? sel.name : '—';
  });

  // Phase-specific events
  socket.on('phase_countdown', (data) => {
    setPhase('countdown');
    startTimer(data?.seconds || 10);
  });

  socket.on('phase_preparation', (data) => {
    setPhase('preparation');
    startTimer(data?.seconds || 30);
    // reset per-phase UI
    els.phaseSubs.innerHTML = '';
    submittedThisPhase = 0;
  });

  socket.on('phase_selection', (data) => {
    setPhase('selection');
    startTimer(data?.seconds || 10);
  });

  socket.on('phase_minigame', (data) => {
    setPhase('minigame');
    startTimer(data?.seconds || 10);
    document.getElementById('minigameInstruction').textContent = data?.instruction || 'Follow the on-screen instruction.';
  });

  socket.on('phase_truthdare', (data) => {
    setPhase('truthdare');
    startTimer(data?.seconds || 60);
    els.tdType.textContent = (data?.type || 'Truth').toString();
    els.tdPlayer.textContent = data?.player || '—';
    els.tdContent.textContent = data?.content || '—';
    els.tdSubmittedBy.textContent = data?.submitted_by ? `Submitted by: ${data.submitted_by}` : '';
    // enable vote skip for everyone except performing player
    const canVote = !!data?.can_vote_skip;
    els.voteSkipBtn.disabled = !canVote || votedSkip;
  });

  socket.on('round_history_item', addHistoryItem);

  socket.on('game_ended', (data) => {
    // navigate to end screen
    const code = data?.room_code || ROOM;
    window.location.href = `/end/${code}`;
  });

  socket.on('error_message', (msg) => {
    TODToast.show('Error', msg || 'Something went wrong', 'danger');
  });

  // User actions
  els.copyBtn?.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(els.codeBadge.textContent.trim());
      TODToast.show('Copied', 'Room code copied to clipboard.', 'primary');
    } catch(e){
      TODToast.show('Clipboard', 'Select and copy the code manually.', 'secondary');
    }
  });

  els.leaveBtn?.addEventListener('click', () => {
    socket.emit('leave', { room: ROOM });
    window.location.href = '/';
  });

  // Expand history
  els.expandHistoryBtn?.addEventListener('click', () => {
    els.historyBody.classList.toggle('d-none');
    els.expandHistoryBtn.textContent = els.historyBody.classList.contains('d-none') ? 'Expand' : 'Collapse';
  });

  // Host actions
  els.startBtn?.addEventListener('click', () => socket.emit('start_game', { room: ROOM }));
  els.endBtn?.addEventListener('click', () => socket.emit('restart_game', { room: ROOM }));
  els.destroyBtn?.addEventListener('click', () => {
    if (confirm('Destroy room for everyone?')) socket.emit('destroy_room', { room: ROOM });
  });

  // Preparation: per-phase submission handling (max 3)
  let submittedThisPhase = 0;
  els.contributeForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    if (submittedThisPhase >= 3) {
      TODToast.show('Limit reached', 'Max 3 submissions this phase.', 'warning');
      return;
    }
    const fd = new FormData(els.contributeForm);
    const type = fd.get('ctype') || 'truth';
    const item = (fd.get('item') || '').trim();
    const targets = Array.from(els.targetPlayers.querySelectorAll('input[type="checkbox"]:checked')).map(c => c.value);
    if (!item || targets.length === 0) {
      TODToast.show('Missing info', 'Write an item and pick at least one target.', 'warning');
      return;
    }
    socket.emit('submit_truth_dare', { room: ROOM, type, text: item, targets });
    submittedThisPhase += 1;
    // list locally
    const li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between';
    li.innerHTML = `<span>${type === 'truth' ? 'Truth' : 'Dare'}: ${item}</span><span class="text-body-secondary small">+10 pts</span>`;
    els.phaseSubs.prepend(li);
    els.contributeForm.reset();
    // keep last selected content type
    document.getElementById('typeTruth').checked = (type === 'truth');
    document.getElementById('typeDare').checked = (type === 'dare');
  });

  // Vote skip
  let votedSkip = false;
  els.voteSkipBtn?.addEventListener('click', () => {
    if (votedSkip) return;
    socket.emit('vote_skip', { room: ROOM });
    votedSkip = true;
    els.voteSkipBtn.disabled = true;
  });

  // Settings (host)
  function getSettingsPayload(){
    const ids = {
      countdown: 'set-countdown',
      preparation: 'set-preparation',
      selection: 'set-selection',
      truthdare: 'set-truthdare',
      skip: 'set-skip',
      maxRounds: 'set-maxRounds',
      minigameChance: 'set-minigameChance',
    };
    const obj = {};
    for (const [k, id] of Object.entries(ids)) {
      const el = document.getElementById(id);
      if (el) obj[k] = +el.value;
    }
    obj.aiEnabled = !!document.getElementById('set-ai')?.checked;
    return obj;
  }
  // live value bubbles
  els.settingsForm?.querySelectorAll('input[type="range"]').forEach(r => {
    const id = r.id.replace('set-','');
    const out = document.getElementById('val-' + id);
    r.addEventListener('input', () => { if (out) out.textContent = r.value; });
  });
  els.applySettingsBtn?.addEventListener('click', () => {
    socket.emit('update_settings', { room: ROOM, settings: getSettingsPayload() });
    TODToast.show('Settings', 'Applied successfully.', 'success');
  });

  // Defaults (host)
  els.presetFile?.addEventListener('change', async () => {
    const file = els.presetFile.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const json = JSON.parse(text);
      if (!Array.isArray(json.truths) || !Array.isArray(json.dares)) throw new Error('Invalid format');
      els.defaultsTruths.value = json.truths.join('\n');
      els.defaultsDares.value = json.dares.join('\n');
      TODToast.show('Preset Loaded', 'Review and Apply to Players.', 'primary');
    } catch(e){
      TODToast.show('Preset Error', 'Invalid JSON format.', 'danger');
    } finally {
      els.presetFile.value = '';
    }
  });

  els.savePresetBtn?.addEventListener('click', () => {
    const payload = {
      truths: els.defaultsTruths.value.split('\n').map(s => s.trim()).filter(Boolean),
      dares: els.defaultsDares.value.split('\n').map(s => s.trim()).filter(Boolean),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tod_preset_${(new Date()).toISOString().slice(0,10)}.json`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 0);
  });

  els.applyDefaultsBtn?.addEventListener('click', () => {
    const payload = {
      truths: els.defaultsTruths.value.split('\n').map(s => s.trim()).filter(Boolean),
      dares: els.defaultsDares.value.split('\n').map(s => s.trim()).filter(Boolean),
    };
    socket.emit('load_preset_file', { room: ROOM, file_data: JSON.stringify(payload) });
    TODToast.show('Defaults', 'Applied to all players.', 'success');
  });

  // Ask server for initial defaults (to prefill)
  socket.emit('get_settings', { room: ROOM }); socket.emit('get_default_lists', { room: ROOM });
  socket.on('defaults_data', (data) => {
    if (!data) return;
    els.defaultsTruths.value = (data.truths || []).join('\n');
    els.defaultsDares.value = (data.dares || []).join('\n');
  });

})();