// === Bootstrap helpers ===
let settingsModalInstance = null;
document.addEventListener('DOMContentLoaded', () => {
  const modalEl = document.getElementById('settings-modal');
  if (modalEl) {
    settingsModalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);
  }

  // Theme toggle
  const themeBtn = document.getElementById('themeToggle');
  const root = document.documentElement;
  const applyTheme = (t) => root.setAttribute('data-bs-theme', t);
  try {
    const saved = localStorage.getItem('theme') || 'light';
    applyTheme(saved);
  } catch(e) {}
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = root.getAttribute('data-bs-theme') || 'light';
      const next = current === 'light' ? 'dark' : 'light';
      applyTheme(next);
      try { localStorage.setItem('theme', next); } catch(e){}
      showToast(`Switched to ${next} mode`);
    });
  }
});

// === Global state ===
let mySocketId = null;
let hostSocketId = null;
let gameState = { phase: 'lobby', remaining_time: 0 };
let timerInterval = null;

// Defaults cache
let defaultTruths = [];
let defaultDares = [];

// DOM refs
const playerList = document.getElementById('player-list');
const playerCount = document.getElementById('player-count');
const hostControls = document.getElementById('host-controls');
const lobbySection = document.getElementById('lobby-section');
const gameArea = document.getElementById('game-area');
const startButton = document.getElementById('start-button');
const submissionSection = document.getElementById('submission-section');

// Socket
const socket = io();

socket.on('connect', () => {
  mySocketId = socket.id;
  socket.emit('join', { room: ROOM_CODE, name: PLAYER_NAME });
  socket.emit('get_settings', { room: ROOM_CODE });
  socket.emit('get_default_lists', { room: ROOM_CODE });
});

// --- Settings ---
socket.on('settings_updated', (data) => {
  if (!data || !data.settings) return;
  const s = data.settings;
  const $ = (id) => document.getElementById(id);
  $('setting-countdown').value = s.countdown_duration ?? 10;
  $('setting-preparation').value = s.preparation_duration ?? 30;
  $('setting-selection').value = s.selection_duration ?? 10;
  $('setting-truthdare').value = s.truth_dare_duration ?? 60;
  $('setting-skip').value = s.skip_duration ?? 5;
  $('setting-maxrounds').value = s.max_rounds ?? 10;
  $('setting-minigame').value = s.minigame_chance ?? 20;
  $('setting-ai-generation').checked = (s.ai_generation_enabled ?? true);
});

// --- Default lists ---
socket.on('default_lists_updated', (data) => {
  if (data.truths !== undefined) { defaultTruths = data.truths; renderDefaultList('truth'); }
  if (data.dares !== undefined) { defaultDares = data.dares; renderDefaultList('dare'); }
});

socket.on('preset_loaded', (data) => showToast(data.message || 'Preset loaded'));
socket.on('preset_error', (data) => showToast('Preset error: ' + (data.message || 'Unknown'), 'danger'));

// --- Player list ---
socket.on('player_list', (data) => {
  try {
    if (!data.players || data.players.length === 0) {
      playerList.innerHTML = '<li class="list-group-item text-secondary">Waiting for players...</li>';
      playerCount.textContent = '';
      hostControls.classList.add('d-none');
      return;
    }

    hostSocketId = data.host_sid;
    const hostName = data.host_name;

    // Targets (exclude self)
    const playerCheckboxes = document.getElementById('player-checkboxes');
    const otherPlayers = data.players.filter(n => n !== PLAYER_NAME);
    if (playerCheckboxes) {
      playerCheckboxes.innerHTML = otherPlayers.length === 0
        ? '<div class="text-secondary text-center">No other players yet</div>'
        : otherPlayers.map(name => `
            <div class="form-check">
              <input class="form-check-input" type="checkbox" name="target-player" value="${escapeHtml(name)}" id="cb-${escapeHtml(name)}">
              <label class="form-check-label" for="cb-${escapeHtml(name)}">${escapeHtml(name)}</label>
            </div>`).join('');
    }

    // Visible player list
    playerList.innerHTML = data.players.map(name => {
      const isHost = (hostName && hostName === name);
      const badge = isHost ? '<span class="badge text-bg-warning ms-2">Host</span>' : '';
      return `<li class="list-group-item d-flex justify-content-between align-items-center">
                <span>${escapeHtml(name)}</span>${badge}
              </li>`;
    }).join('');

    playerCount.textContent = `${data.players.length} player(s) in room`;

    // Host controls visible only to host
    if (mySocketId && hostSocketId && mySocketId === hostSocketId) {
      hostControls.classList.remove('d-none');
    } else {
      hostControls.classList.add('d-none');
    }
  } catch(e) {
    console.error(e);
  }
});

// --- Game state ---
socket.on('game_state_update', (data) => {
  gameState = data || gameState;
  updateGameUI();
});

// --- Submissions ---
socket.on('submission_success', (data) => {
  const successDiv = document.getElementById('submission-success');
  const targetList = (data.targets || []).join(', ');
  successDiv.textContent = `✔ Added ${data.type}: "${data.text}" to ${targetList}`;
  successDiv.classList.remove('d-none');
  document.getElementById('truth-dare-text').value = '';
  deselectAllPlayers();
  setTimeout(() => successDiv.classList.add('d-none'), 2000);
});

// --- Room lifecycle ---
socket.on('room_destroyed', () => {
  showToast('The host has closed the room', 'warning');
  setTimeout(() => window.location.href = '/', 500);
});

socket.on('left_room', () => {
  setTimeout(() => window.location.href = '/', 200);
});

// === UI Update ===
function updateGameUI() {
  const show = (id, on) => document.getElementById(id).classList.toggle('d-none', !on);

  // Sections reset
  ['countdown-section','preparation-section','selection-section','minigame-section','truth-dare-section','end-game-section']
    .forEach(id => show(id, false));

  // Hide submission section by default
  if (submissionSection) submissionSection.classList.add('d-none');

  if (gameState.phase === 'end_game') {
    lobbySection.classList.add('d-none');
    gameArea.classList.remove('d-none');
    show('end-game-section', true);

    const endHost = document.getElementById('end-game-host-controls');
    if (mySocketId === hostSocketId) endHost.classList.remove('d-none'); else endHost.classList.add('d-none');
    displayTopPlayers();
    displayRoundHistory();
    return;
  }

  if (gameState.phase === 'countdown') {
    lobbySection.classList.add('d-none');
    gameArea.classList.remove('d-none');
    show('countdown-section', true);
    startCountdownTimer();
    return;
  }

  if (gameState.phase === 'preparation') {
    lobbySection.classList.add('d-none');
    gameArea.classList.remove('d-none');
    show('preparation-section', true);
    if (submissionSection) submissionSection.classList.remove('d-none'); // Show here
    startPreparationTimer();
    return;
  }

  if (gameState.phase === 'selection') {
    lobbySection.classList.add('d-none');
    gameArea.classList.remove('d-none');
    show('selection-section', true);

    if (gameState.selected_player) {
      document.getElementById('selected-player-name').textContent = gameState.selected_player;
      const isSelected = (gameState.selected_player === PLAYER_NAME);
      const choiceButtons = document.getElementById('truth-dare-choice');
      const choiceMade = document.getElementById('choice-made');
      if (isSelected && !gameState.selected_choice) {
        choiceButtons.classList.remove('d-none');
        choiceMade.classList.add('d-none');
      } else {
        choiceButtons.classList.add('d-none');
        if (gameState.selected_choice) {
          choiceMade.classList.remove('d-none');
          document.getElementById('choice-display').textContent = gameState.selected_choice.toUpperCase();
        }
      }
    }
    startSelectionTimer();
    return;
  }

  if (gameState.phase === 'truth_dare') {
    lobbySection.classList.add('d-none');
    gameArea.classList.remove('d-none');
    show('truth-dare-section', true);
    startTruthDareTimer();
    return;
  }

  // Lobby fallback
  lobbySection.classList.remove('d-none');
  gameArea.classList.add('d-none');
}

// === Timers ===
function startCountdownTimer(){ clearInterval(timerInterval); timerInterval = setInterval(() => {
  const el = document.getElementById('countdown-timer'); if (el){ el.textContent = Math.max(0, gameState.remaining_time); gameState.remaining_time--; } }, 1000); }
function startPreparationTimer(){ clearInterval(timerInterval); timerInterval = setInterval(() => {
  const el = document.getElementById('prep-timer'); if (el){ el.textContent = Math.max(0, gameState.remaining_time); gameState.remaining_time--; } }, 1000); }
function startSelectionTimer(){ clearInterval(timerInterval); timerInterval = setInterval(() => {
  const el = document.getElementById('selection-timer'); if (el){ el.textContent = Math.max(0, gameState.remaining_time); gameState.remaining_time--; } }, 1000); }
function startTruthDareTimer(){ clearInterval(timerInterval); timerInterval = setInterval(() => {
  const el = document.getElementById('truth-dare-timer'); if (el){ el.textContent = Math.max(0, gameState.remaining_time); gameState.remaining_time--; } }, 1000); }

// === Actions ===
function leaveRoom(){
  if (!confirm('Leave this room?')) return;
  socket.emit('leave', { room: ROOM_CODE });
  try { socket.disconnect(); } catch(e) {}
}

function destroyRoom(){
  if (!confirm('Destroy this room for everyone?')) return;
  socket.emit('destroy_room', { room: ROOM_CODE });
}

function openSettings(){ settingsModalInstance?.show(); }
function closeSettings(){ settingsModalInstance?.hide(); }

function saveSettings(){
  const s = {
    countdown_duration: parseInt(document.getElementById('setting-countdown').value),
    preparation_duration: parseInt(document.getElementById('setting-preparation').value),
    selection_duration: parseInt(document.getElementById('setting-selection').value),
    truth_dare_duration: parseInt(document.getElementById('setting-truthdare').value),
    skip_duration: parseInt(document.getElementById('setting-skip').value),
    max_rounds: parseInt(document.getElementById('setting-maxrounds').value),
    minigame_chance: parseInt(document.getElementById('setting-minigame').value),
    ai_generation_enabled: document.getElementById('setting-ai-generation').checked
  };
  socket.emit('update_settings', { room: ROOM_CODE, settings: s });
  showToast('Settings saved', 'success');
  closeSettings();
}

function startGame(){
  startButton.disabled = true;
  socket.emit('start_game', { room: ROOM_CODE });
  setTimeout(()=> startButton.disabled = false, 1500);
}

function restartGame(){
  if (!confirm('Restart game and reset scores?')) return;
  socket.emit('restart_game', { room: ROOM_CODE });
}

// === Utilities ===
function escapeHtml(text){ const div = document.createElement('div'); div.textContent = text; return div.innerHTML; }

function renderDefaultList(type){
  const listContainer = document.getElementById(`default-${type}s-list`);
  const items = type === 'truth' ? defaultTruths : defaultDares;
  if (!listContainer) return;
  if ((items || []).length === 0){
    listContainer.innerHTML = `<div class="text-secondary">No default ${type}s yet.</div>`;
    return;
  }
  listContainer.innerHTML = items.map((text, i)=> `
    <label class="list-group-item d-flex align-items-center gap-2">
      <input class="form-check-input me-1" type="checkbox" data-type="${type}" data-text="${escapeHtml(text)}">
      <span class="small">${escapeHtml(text)}</span>
    </label>
  `).join('');
}
