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
    playerList.innerHTML = data.players.map((name, idx) => {
      const isHost = (data.host_name ? data.host_name === name : idx === 0);
      const badge = isHost ? '<span class="badge text-bg-warning ms-2">Host</span>' : '';
      return `<li class="list-group-item d-flex justify-content-between align-items-center">
                <span>${escapeHtml(name)}</span>${badge}
              </li>`;
    }).join('');

    playerCount.textContent = `${data.players.length} player(s) in room`;

    // Host controls visible only to host
    if (mySocketId === hostSocketId) {
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

  if (gameState.phase === 'minigame') {
    lobbySection.classList.add('d-none');
    gameArea.classList.remove('d-none');
    show('minigame-section', true);

    if (gameState.minigame) {
      const m = gameState.minigame;
      const participants = m.participants || [];

      document.querySelector('.minigame-title').textContent = m.name || 'Mini Game';
      document.querySelector('.minigame-description').textContent = m.description_voter || '';
      document.querySelector('.voting-instruction').textContent = m.vote_instruction || 'Vote for the loser!';

      document.getElementById('participant-1').textContent = participants[0] || 'Player 1';
      document.getElementById('participant-2').textContent = participants[1] || 'Player 2';

      const voteCounts = m.vote_counts || {};
      const votes1 = voteCounts[participants[0]] || 0;
      const votes2 = voteCounts[participants[1]] || 0;
      document.getElementById('participant-1-votes').textContent = `${votes1} vote${votes1 !== 1 ? 's' : ''}`;
      document.getElementById('participant-2-votes').textContent = `${votes2} vote${votes2 !== 1 ? 's' : ''}`;

      const isParticipant = participants.includes(PLAYER_NAME);
      if (isParticipant) {
        document.getElementById('minigame-voting').classList.add('d-none');
        const msg = document.getElementById('minigame-participant-message');
        msg.classList.remove('d-none');
        msg.querySelector('p:first-child').textContent = m.description_participant || 'You are participating!';
      } else {
        document.getElementById('minigame-voting').classList.remove('d-none');
        document.getElementById('minigame-participant-message').classList.add('d-none');
        const btn1 = document.getElementById('vote-btn-1');
        const btn2 = document.getElementById('vote-btn-2');
        btn1.disabled = false; btn2.disabled = false;
        document.getElementById('vote-name-1').textContent = participants[0] || 'Player 1';
        document.getElementById('vote-name-2').textContent = participants[1] || 'Player 2';
        btn1.onclick = () => voteMinigame(participants[0]);
        btn2.onclick = () => voteMinigame(participants[1]);
        document.getElementById('minigame-vote-count').textContent = m.vote_count || 0;
        document.getElementById('minigame-required-votes').textContent = m.total_voters || 0;
      }
    }
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

    const emptyBanner = document.getElementById('empty-list-banner');
    emptyBanner.classList.toggle('d-none', !gameState.list_empty);

    const phaseType = document.getElementById('phase-type');
    const performingPlayer = document.getElementById('performing-player-name');
    const challengeText = document.getElementById('challenge-text');
    if (gameState.selected_choice) { phaseType.textContent = gameState.selected_choice.toUpperCase(); }
    if (gameState.selected_player) { performingPlayer.textContent = gameState.selected_player; }
    if (gameState.current_truth_dare) {
      challengeText.textContent = gameState.current_truth_dare.text;
      if (gameState.list_empty) {
        challengeText.classList.add('border-warning','bg-warning-subtle');
      } else {
        challengeText.classList.remove('border-warning','bg-warning-subtle');
      }
    }

    const isSelectedPlayer = (gameState.selected_player === PLAYER_NAME);
    const voteSection = document.getElementById('vote-section');
    voteSection.classList.toggle('d-none', isSelectedPlayer);

    if (!isSelectedPlayer) {
      const voteSkipButton = document.getElementById('vote-skip-button');
      if (gameState.list_empty) {
        voteSkipButton.disabled = true;
        voteSkipButton.textContent = '⚠️ List Empty - Skip Auto-Activated!';
        voteSkipButton.className = 'btn btn-warning';
      } else if (gameState.skip_activated) {
        voteSkipButton.disabled = true;
        voteSkipButton.textContent = 'Skip Activated!';
        voteSkipButton.className = 'btn btn-secondary';
      } else {
        voteSkipButton.disabled = false;
        voteSkipButton.textContent = 'Vote to Skip';
        voteSkipButton.className = 'btn btn-secondary';
      }
      const totalPlayers = playerList.children.length;
      const otherPlayersCount = totalPlayers - 1;
      const requiredVotes = Math.ceil(otherPlayersCount / 2);
      document.getElementById('vote-count').textContent = gameState.skip_vote_count || 0;
      document.getElementById('required-votes').textContent = requiredVotes;
    }
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
  if (s.countdown_duration < 3 || s.countdown_duration > 30) return alert('Countdown must be 3-30s');
  if (s.preparation_duration < 10 || s.preparation_duration > 120) return alert('Preparation must be 10-120s');
  if (s.selection_duration < 5 || s.selection_duration > 30) return alert('Selection must be 5-30s');
  if (s.truth_dare_duration < 30 || s.truth_dare_duration > 180) return alert('Truth/Dare must be 30-180s');
  if (s.skip_duration < 3 || s.skip_duration > 30) return alert('Skip must be 3-30s');
  if (s.max_rounds < 1 || s.max_rounds > 50) return alert('Max rounds must be 1-50');
  if (s.minigame_chance < 0 || s.minigame_chance > 100) return alert('Minigame chance must be 0-100%');
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

function voteMinigame(playerName){
  if (!playerName) return;
  document.getElementById('vote-btn-1').disabled = true;
  document.getElementById('vote-btn-2').disabled = true;
  socket.emit('minigame_vote', { room: ROOM_CODE, voted_player: playerName });
}

function selectAllPlayers(){
  document.querySelectorAll('input[name="target-player"]').forEach(cb => cb.checked = true);
}

function deselectAllPlayers(){
  document.querySelectorAll('input[name="target-player"]').forEach(cb => cb.checked = false);
}

function submitTruthDare(){
  const text = document.getElementById('truth-dare-text').value.trim();
  const type = document.getElementById('truth-dare-type').value;
  const targets = Array.from(document.querySelectorAll('input[name="target-player"]:checked')).map(cb => cb.value);
  if (!text) return alert('Please enter a truth or dare');
  if (!targets.length) return alert('Please select at least one player');
  socket.emit('submit_truth_dare', { room: ROOM_CODE, text, type, targets });
}

function selectTruthDare(choice){
  socket.emit('select_truth_dare', { room: ROOM_CODE, choice });
}

function voteSkip(){
  const btn = document.getElementById('vote-skip-button');
  btn.disabled = true; btn.textContent = 'Vote Submitted';
  socket.emit('vote_skip', { room: ROOM_CODE });
}

// === Utilities ===
function escapeHtml(text){ const div = document.createElement('div'); div.textContent = text; return div.innerHTML; }

function renderDefaultList(type){
  const listContainer = document.getElementById(`default-${type}s-list`);
  const items = type === 'truth' ? defaultTruths : defaultDares;
  if (!listContainer) return;
  if ((items || []).length === 0){
    listContainer.innerHTML = `<div class="text-secondary">No default ${type}s yet. Click "Add ${type==='truth'?'Truth':'Dare'}".</div>`;
    return;
  }
  listContainer.innerHTML = items.map((text, i)=> `
    <label class="list-group-item d-flex align-items-center gap-2">
      <input class="form-check-input me-1" type="checkbox" data-type="${type}" data-text="${escapeHtml(text)}">
      <span class="small">${escapeHtml(text)}</span>
    </label>
  `).join('');
}

function selectAllItems(type){
  document.querySelectorAll(`input[data-type="${type}"]`).forEach(cb => cb.checked = true);
}
function deselectAllItems(type){
  document.querySelectorAll(`input[data-type="${type}"]`).forEach(cb => cb.checked = false);
}
function addDefaultItem(type){
  const text = prompt(`Enter a new default ${type}:`);
  if (!text || !text.trim()) return;
  if (type === 'truth'){ socket.emit('add_default_truth', { room: ROOM_CODE, text: text.trim() }); }
  else { socket.emit('add_default_dare', { room: ROOM_CODE, text: text.trim() }); }
}
function editDefaultItem(type){
  const selected = Array.from(document.querySelectorAll(`input[data-type="${type}"]:checked`));
  if (selected.length === 0) return alert('Please select one item to edit');
  if (selected.length > 1) return alert('Please select only one item');
  const oldText = selected[0].dataset.text;
  const nv = prompt(`Edit ${type}:`, oldText);
  if (!nv || !nv.trim() || nv.trim() === oldText) return;
  if (type === 'truth'){ socket.emit('edit_default_truth', { room: ROOM_CODE, old_text: oldText, new_text: nv.trim() }); }
  else { socket.emit('edit_default_dare', { room: ROOM_CODE, old_text: oldText, new_text: nv.trim() }); }
}
function removeDefaultItems(type){
  const selected = Array.from(document.querySelectorAll(`input[data-type="${type}"]:checked`));
  if (selected.length === 0) return alert('Please select items to remove');
  if (!confirm(`Remove ${selected.length} ${type}${selected.length>1?'s':''}?`)) return;
  const textsToRemove = selected.map(cb => cb.dataset.text);
  if (type === 'truth'){ socket.emit('remove_default_truths', { room: ROOM_CODE, texts: textsToRemove }); }
  else { socket.emit('remove_default_dares', { room: ROOM_CODE, texts: textsToRemove }); }
}
