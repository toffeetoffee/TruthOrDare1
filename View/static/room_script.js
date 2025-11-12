// Global variables
let mySocketId = null;
let hostSocketId = null;
let gameState = { phase: 'lobby', remaining_time: 0 };
let timerInterval = null;

// Store default lists
let defaultTruths = [];
let defaultDares = [];

// DOM elements
const playerList = document.getElementById('player-list');
const playerCount = document.getElementById('player-count');
const hostControls = document.getElementById('host-controls');
const lobbySection = document.getElementById('lobby-section');
const gameArea = document.getElementById('game-area');
const startButton = document.getElementById('start-button');

// ---- Theme persistence (shared with index.html) ----
(function themeBoot() {
  const saved = localStorage.getItem('dod-theme') || 'light';
  document.documentElement.setAttribute('data-bs-theme', saved);
  const btn = document.getElementById('themeToggle');
  const apply = (mode) => {
    document.documentElement.setAttribute('data-bs-theme', mode);
    localStorage.setItem('dod-theme', mode);
    if (btn) btn.textContent = (mode === 'dark') ? '🌙 Dark' : '🌞 Light';
  };
  if (btn) {
    btn.addEventListener('click', () => {
      const next = (document.documentElement.getAttribute('data-bs-theme') === 'dark') ? 'light' : 'dark';
      apply(next);
    });
  }
  apply(saved);
})();

// ---- Toast helper (Bootstrap 5) ----
function showToast(title, body, variant = 'primary') {
  const container = document.getElementById('toast-container');
  const id = `t${Date.now()}${Math.floor(Math.random()*999)}`;
  const el = document.createElement('div');
  el.className = `toast align-items-center text-bg-${variant} border-0`;
  el.id = id;
  el.role = 'alert';
  el.ariaLive = 'assertive';
  el.ariaAtomic = 'true';
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <strong class="me-2">${title}</strong>${body || ''}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;
  container.appendChild(el);
  const t = new bootstrap.Toast(el, { delay: 3000 });
  t.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

// Socket connection
const socket = io();

// Join the room when connected
socket.on('connect', () => {
  mySocketId = socket.id;
  socket.emit('join', { room: ROOM_CODE, name: PLAYER_NAME });
  socket.emit('get_settings', { room: ROOM_CODE });
  socket.emit('get_default_lists', { room: ROOM_CODE });
});

// Settings updated
socket.on('settings_updated', (data) => {
  if (data.settings) {
    document.getElementById('setting-countdown').value = data.settings.countdown_duration ?? 10;
    document.getElementById('setting-preparation').value = data.settings.preparation_duration ?? 30;
    document.getElementById('setting-selection').value = data.settings.selection_duration ?? 10;
    document.getElementById('setting-truthdare').value = data.settings.truth_dare_duration ?? 60;
    document.getElementById('setting-skip').value = data.settings.skip_duration ?? 5;
    document.getElementById('setting-maxrounds').value = data.settings.max_rounds ?? 10;
    document.getElementById('setting-minigame').value = data.settings.minigame_chance ?? 20;
    document.getElementById('setting-ai-generation').checked = (data.settings.ai_generation_enabled ?? true);
  }
});

// Default lists updated
socket.on('default_lists_updated', (data) => {
  if (data.truths !== undefined) {
    defaultTruths = data.truths;
    renderDefaultList('truth');
  }
  if (data.dares !== undefined) {
    defaultDares = data.dares;
    renderDefaultList('dare');
  }
});

// Preset signals
socket.on('preset_loaded', (data) => showToast('Preset', data.message || 'Loaded.', 'success'));
socket.on('preset_error', (data) => showToast('Error', data.message || 'Something went wrong.', 'danger'));

// Player list update
socket.on('player_list', (data) => {
  if (!data.players || data.players.length === 0) {
    playerList.innerHTML = '<li class="list-group-item text-body-secondary">Waiting for players...</li>';
    playerCount.textContent = '';
    return;
  }

  hostSocketId = data.host_sid;

  // Update player checkboxes (exclude current player)
  const playerCheckboxes = document.getElementById('player-checkboxes');
  const otherPlayers = data.players.filter(name => name !== PLAYER_NAME);
  if (playerCheckboxes) {
    if (otherPlayers.length === 0) {
      playerCheckboxes.innerHTML = '<div class="text-center text-body-secondary">No other players yet</div>';
    } else {
      playerCheckboxes.innerHTML = otherPlayers.map(name => `
        <div class="player-checkbox-item form-check">
          <input class="form-check-input" type="checkbox" name="target-player" value="${escapeHtml(name)}" id="cb-${escapeHtml(name)}">
          <label class="form-check-label" for="cb-${escapeHtml(name)}">${escapeHtml(name)}</label>
        </div>
      `).join('');
    }
  }

  // Display all players
  playerList.innerHTML = data.players.map((name, index) => {
    const isHost = (index === 0);
    const badge = isHost ? ' <span class="badge text-bg-warning ms-2">Host</span>' : '';
    return `<li class="list-group-item d-flex align-items-center">${escapeHtml(name)}${badge}</li>`;
  }).join('');

  playerCount.textContent = `${data.players.length} player(s) in room`;

  // Toggle host controls (using presence of host id)
  const isHost = (mySocketId && hostSocketId && mySocketId === hostSocketId);
  document.getElementById('openSettingsBtn').disabled = !isHost;
  startButton.disabled = !isHost;
});

// Game state update
socket.on('game_state_update', (data) => {
  gameState = data;
  updateGameUI();
});

// Submission success
socket.on('submission_success', (data) => {
  const successDiv = document.getElementById('submission-success');
  const targetList = (data.targets || []).join(', ');
  successDiv.textContent = `✓ Added ${data.type}: "${data.text}" to ${targetList}`;
  successDiv.classList.remove('d-none');
  document.getElementById('truth-dare-text').value = '';
  deselectAllPlayers();
  setTimeout(() => successDiv.classList.add('d-none'), 2200);
  showToast('Submitted', `${escapeHtml(data.type)} added for ${escapeHtml(targetList)}`, 'success');
});

// Room destroyed
socket.on('room_destroyed', () => {
  showToast('Room', 'The host has closed the room.', 'warning');
  setTimeout(() => (window.location.href = '/'), 800);
});

// Left room
socket.on('left_room', () => {
  window.location.href = '/';
});

// ----- UI helpers for phases -----
function show(el) { el.classList.remove('d-none'); }
function hide(el) { el.classList.add('d-none'); }

function updateGameUI() {
  const sections = [
    'countdown-section','preparation-section','selection-section',
    'minigame-section','truth-dare-section','end-game-section'
  ];
  sections.forEach(id => hide(document.getElementById(id)));

  if (gameState.phase === 'end_game') {
    lobbySection.classList.add('d-none');
    show(gameArea);
    show(document.getElementById('end-game-section'));
    const endGameHostControls = document.getElementById('end-game-host-controls');
    if (mySocketId === hostSocketId) show(endGameHostControls); else hide(endGameHostControls);
    displayTopPlayers();
    displayRoundHistory();
  } else if (gameState.phase === 'minigame') {
    lobbySection.classList.add('d-none');
    show(gameArea);
    show(document.getElementById('minigame-section'));
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
        hide(document.getElementById('minigame-voting'));
        const msgBox = document.getElementById('minigame-participant-message');
        show(msgBox);
        msgBox.querySelector('p:first-child').textContent = m.description_participant || 'You are participating!';
      } else {
        show(document.getElementById('minigame-voting'));
        hide(document.getElementById('minigame-participant-message'));
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
  } else if (gameState.phase === 'countdown') {
    lobbySection.classList.add('d-none');
    show(gameArea);
    show(document.getElementById('countdown-section'));
    startCountdownTimer();
  } else if (gameState.phase === 'preparation') {
    lobbySection.classList.add('d-none');
    show(gameArea);
    show(document.getElementById('preparation-section'));
    startPreparationTimer();
  } else if (gameState.phase === 'selection') {
    lobbySection.classList.add('d-none');
    show(gameArea);
    show(document.getElementById('selection-section'));
    const playerNameElement = document.getElementById('selected-player-name');
    if (gameState.selected_player) {
      playerNameElement.textContent = gameState.selected_player;
      const isSelectedPlayer = (gameState.selected_player === PLAYER_NAME);
      const choiceButtons = document.getElementById('truth-dare-choice');
      const choiceMade = document.getElementById('choice-made');
      if (isSelectedPlayer && !gameState.selected_choice) {
        show(choiceButtons); hide(choiceMade);
      } else {
        hide(choiceButtons);
        if (gameState.selected_choice) {
          show(choiceMade);
          document.getElementById('choice-display').textContent = gameState.selected_choice.toUpperCase();
        }
      }
    }
    startSelectionTimer();
  } else if (gameState.phase === 'truth_dare') {
    lobbySection.classList.add('d-none');
    show(gameArea);
    show(document.getElementById('truth-dare-section'));
    const emptyListBanner = document.getElementById('empty-list-banner');
    if (gameState.list_empty) emptyListBanner.classList.remove('d-none'); else emptyListBanner.classList.add('d-none');
    const phaseType = document.getElementById('phase-type');
    const performingPlayer = document.getElementById('performing-player-name');
    const challengeText = document.getElementById('challenge-text');
    if (gameState.selected_choice) phaseType.textContent = gameState.selected_choice.toUpperCase();
    if (gameState.selected_player) performingPlayer.textContent = gameState.selected_player;
    if (gameState.current_truth_dare) {
      challengeText.textContent = gameState.current_truth_dare.text;
      if (gameState.list_empty) {
        challengeText.classList.add('border-warning', 'bg-warning-subtle');
      } else {
        challengeText.classList.remove('border-warning', 'bg-warning-subtle');
      }
    }
    const isSelectedPlayer = (gameState.selected_player === PLAYER_NAME);
    const voteSection = document.getElementById('vote-section');
    if (!isSelectedPlayer) {
      show(voteSection);
      const voteSkipButton = document.getElementById('vote-skip-button');
      if (gameState.list_empty) {
        voteSkipButton.disabled = true;
        voteSkipButton.textContent = '⚠️ List Empty - Skip Auto-Activated!';
        voteSkipButton.classList.remove('btn-outline-secondary');
        voteSkipButton.classList.add('btn-warning', 'text-dark');
      } else if (gameState.skip_activated) {
        voteSkipButton.disabled = true;
        voteSkipButton.textContent = 'Skip Activated!';
      } else {
        voteSkipButton.disabled = false;
        voteSkipButton.textContent = 'Vote to Skip';
        voteSkipButton.classList.add('btn-outline-secondary');
        voteSkipButton.classList.remove('btn-warning', 'text-dark');
      }
      const totalPlayers = playerList.children.length;
      const otherPlayersCount = totalPlayers - 1;
      const requiredVotes = Math.ceil(otherPlayersCount / 2);
      document.getElementById('vote-count').textContent = gameState.skip_vote_count || 0;
      document.getElementById('required-votes').textContent = requiredVotes;
    } else {
      hide(voteSection);
    }
    startTruthDareTimer();
  } else if (gameState.phase === 'lobby') {
    lobbySection.classList.remove('d-none');
    hide(gameArea);
  }
}

function displayTopPlayers() {
  const topPlayersList = document.getElementById('top-players-list');
  if (!gameState.top_players || gameState.top_players.length === 0) {
    topPlayersList.innerHTML = '<div class="text-body-secondary text-center">No players</div>';
    return;
  }
  topPlayersList.innerHTML = gameState.top_players.map((player, index) => {
    const rank = index + 1;
    const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : '';
    return `
      <div class="d-flex justify-content-between border-bottom py-1">
        <span>${medal} #${rank} ${escapeHtml(player.name)}</span>
        <span class="text-body-secondary">${player.score} pts</span>
      </div>
    `;
  }).join('');
}

function displayRoundHistory() {
  const roundHistoryList = document.getElementById('round-history-list');
  if (!gameState.round_history || gameState.round_history.length === 0) {
    roundHistoryList.innerHTML = '<div class="text-body-secondary text-center">No rounds played</div>';
    return;
  }
  const reversedHistory = [...gameState.round_history].reverse();
  roundHistoryList.innerHTML = reversedHistory.map(round => {
    const submitterText = round.submitted_by 
      ? `<div class="small text-body-secondary">Submitted by: ${escapeHtml(round.submitted_by)}</div>`
      : '<div class="small text-body-secondary">Default challenge</div>';
    return `
      <div class="mb-3">
        <div class="fw-semibold">Round ${round.round_number}</div>
        <div><span class="fw-semibold">${escapeHtml(round.selected_player)}</span> performed a <strong>${round.truth_dare.type}</strong></div>
        <div class="fst-italic">"${escapeHtml(round.truth_dare.text)}"</div>
        ${submitterText}
      </div>
    `;
  }).join('');
}

function startCountdownTimer() {
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const timer = document.getElementById('countdown-timer');
    if (timer) {
      timer.textContent = Math.max(0, gameState.remaining_time);
      gameState.remaining_time--;
    }
  }, 1000);
}

function startPreparationTimer() {
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const timer = document.getElementById('prep-timer');
    if (timer) {
      timer.textContent = Math.max(0, gameState.remaining_time);
      gameState.remaining_time--;
    }
  }, 1000);
}

function startSelectionTimer() {
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const timer = document.getElementById('selection-timer');
    if (timer) {
      timer.textContent = Math.max(0, gameState.remaining_time);
      gameState.remaining_time--;
    }
  }, 1000);
}

function startTruthDareTimer() {
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const timer = document.getElementById('truth-dare-timer');
    if (timer) {
      timer.textContent = Math.max(0, gameState.remaining_time);
      gameState.remaining_time--;
    }
  }, 1000);
}

// Functions
function leaveRoom() {
  if (confirm('Are you sure you want to leave the room?')) {
    socket.emit('leave', { room: ROOM_CODE });
  }
}

function destroyRoom() {
  if (confirm('Are you sure you want to destroy the room? All players will be kicked.')) {
    socket.emit('destroy_room', { room: ROOM_CODE });
    window.location.href = '/';
  }
}

// Bootstrap modal control but keep existing IDs for compatibility
let settingsModalInstance = null;
function openSettings() {
  const modalEl = document.getElementById('settings-modal');
  settingsModalInstance = settingsModalInstance || new bootstrap.Modal(modalEl);
  settingsModalInstance.show();
}
function closeSettings() {
  if (settingsModalInstance) settingsModalInstance.hide();
}

function saveSettings() {
  const settings = {
    countdown_duration: parseInt(document.getElementById('setting-countdown').value),
    preparation_duration: parseInt(document.getElementById('setting-preparation').value),
    selection_duration: parseInt(document.getElementById('setting-selection').value),
    truth_dare_duration: parseInt(document.getElementById('setting-truthdare').value),
    skip_duration: parseInt(document.getElementById('setting-skip').value),
    max_rounds: parseInt(document.getElementById('setting-maxrounds').value),
    minigame_chance: parseInt(document.getElementById('setting-minigame').value),
    ai_generation_enabled: document.getElementById('setting-ai-generation').checked
  };
  if (settings.countdown_duration < 3 || settings.countdown_duration > 30) { alert('Countdown duration must be between 3 and 30 seconds'); return; }
  if (settings.preparation_duration < 10 || settings.preparation_duration > 120) { alert('Preparation duration must be between 10 and 120 seconds'); return; }
  if (settings.selection_duration < 5 || settings.selection_duration > 30) { alert('Selection duration must be between 5 and 30 seconds'); return; }
  if (settings.truth_dare_duration < 30 || settings.truth_dare_duration > 180) { alert('Truth/Dare duration must be between 30 and 180 seconds'); return; }
  if (settings.skip_duration < 3 || settings.skip_duration > 30) { alert('Skip duration must be between 3 and 30 seconds'); return; }
  if (settings.max_rounds < 1 || settings.max_rounds > 50) { alert('Maximum rounds must be between 1 and 50'); return; }
  if (settings.minigame_chance < 0 || settings.minigame_chance > 100) { alert('Minigame chance must be between 0 and 100%'); return; }
  socket.emit('update_settings', { room: ROOM_CODE, settings });
  closeSettings();
}

function startGame() {
  startButton.disabled = true;
  socket.emit('start_game', { room: ROOM_CODE });
}

function restartGame() {
  if (confirm('Are you sure you want to restart the game? All scores will be reset.')) {
    socket.emit('restart_game', { room: ROOM_CODE });
  }
}

function voteMinigame(playerName) {
  if (!playerName) return;
  document.getElementById('vote-btn-1').disabled = true;
  document.getElementById('vote-btn-2').disabled = true;
  socket.emit('minigame_vote', { room: ROOM_CODE, voted_player: playerName });
}

function selectAllPlayers() {
  const checkboxes = document.querySelectorAll('input[name="target-player"]');
  checkboxes.forEach(cb => cb.checked = true);
}

function deselectAllPlayers() {
  const checkboxes = document.querySelectorAll('input[name="target-player"]');
  checkboxes.forEach(cb => cb.checked = false);
}

function submitTruthDare() {
  const text = document.getElementById('truth-dare-text').value.trim();
  const type = document.getElementById('truth-dare-type').value;
  const checkboxes = document.querySelectorAll('input[name="target-player"]:checked');
  const targets = Array.from(checkboxes).map(cb => cb.value);
  if (!text) { alert('Please enter a truth or dare!'); return; }
  if (targets.length === 0) { alert('Please select at least one player!'); return; }
  socket.emit('submit_truth_dare', { room: ROOM_CODE, text, type, targets });
}

function selectTruthDare(choice) {
  socket.emit('select_truth_dare', { room: ROOM_CODE, choice });
}

function voteSkip() {
  const button = document.getElementById('vote-skip-button');
  button.disabled = true;
  button.textContent = 'Vote Submitted';
  socket.emit('vote_skip', { room: ROOM_CODE });
}

// Simple HTML escape
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Default lists renderers (tabs now use Bootstrap pills)
function renderDefaultList(type) {
  const listContainer = document.getElementById(`default-${type}s-list`);
  const items = type === 'truth' ? defaultTruths : defaultDares;
  if (items.length === 0) {
    listContainer.innerHTML = `<div class="text-body-secondary">No default ${type}s yet. Click "Add ${type === 'truth' ? 'Truth' : 'Dare'}" to add one.</div>`;
    return;
  }
  listContainer.innerHTML = items.map((text, index) => `
    <div class="default-list-item" onclick="toggleItemSelection(event, '${type}', ${index})">
      <input type="checkbox" class="form-check-input me-2" 
             id="default-${type}-${index}" 
             data-type="${type}" 
             data-text="${escapeHtml(text)}"
             onclick="event.stopPropagation()">
      <label class="form-check-label default-list-item-text" for="default-${type}-${index}">${escapeHtml(text)}</label>
    </div>
  `).join('');
}

function toggleItemSelection(event, type, index) {
  const checkbox = document.getElementById(`default-${type}-${index}`);
  checkbox.checked = !checkbox.checked;
  const item = event.currentTarget;
  if (checkbox.checked) item.classList.add('selected'); else item.classList.remove('selected');
}

function selectAllItems(type) {
  const checkboxes = document.querySelectorAll(`input[data-type="${type}"]`);
  checkboxes.forEach(cb => { cb.checked = true; cb.closest('.default-list-item').classList.add('selected'); });
}

function deselectAllItems(type) {
  const checkboxes = document.querySelectorAll(`input[data-type="${type}"]`);
  checkboxes.forEach(cb => { cb.checked = false; cb.closest('.default-list-item').classList.remove('selected'); });
}

// Add/edit/remove defaults
function addDefaultItem(type) {
  const text = prompt(`Enter a new default ${type}:`);
  if (!text || !text.trim()) return;
  if (type === 'truth') {
    socket.emit('add_default_truth', { room: ROOM_CODE, text: text.trim() });
  } else {
    socket.emit('add_default_dare', { room: ROOM_CODE, text: text.trim() });
  }
}
function editDefaultItem(type) {
  const checkboxes = document.querySelectorAll(`input[data-type="${type}"]:checked`);
  if (checkboxes.length === 0) { alert('Please select one item to edit'); return; }
  if (checkboxes.length > 1) { alert('Please select only one item to edit'); return; }
  const oldText = checkboxes[0].dataset.text;
  const newText = prompt(`Edit ${type}:`, oldText);
  if (!newText || !newText.trim() || newText.trim() === oldText) return;
  if (type === 'truth') {
    socket.emit('edit_default_truth', { room: ROOM_CODE, old_text: oldText, new_text: newText.trim() });
  } else {
    socket.emit('edit_default_dare', { room: ROOM_CODE, old_text: oldText, new_text: newText.trim() });
  }
}
function removeDefaultItems(type) {
  const checkboxes = document.querySelectorAll(`input[data-type="${type}"]:checked`);
  if (checkboxes.length === 0) { alert('Please select at least one item to remove'); return; }
  const count = checkboxes.length;
  if (!confirm(`Are you sure you want to remove ${count} ${type}${count > 1 ? 's' : ''}?`)) return;
  const textsToRemove = Array.from(checkboxes).map(cb => cb.dataset.text);
  if (type === 'truth') {
    socket.emit('remove_default_truths', { room: ROOM_CODE, texts: textsToRemove });
  } else {
    socket.emit('remove_default_dares', { room: ROOM_CODE, texts: textsToRemove });
  }
}

// Presets
function savePreset() {
  if (defaultTruths.length === 0 && defaultDares.length === 0) { alert('No truths or dares to save!'); return; }
  const preset = { truths: defaultTruths, dares: defaultDares };
  const jsonString = JSON.stringify(preset, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `truth_dare_preset_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('Preset saved', `${defaultTruths.length} truths / ${defaultDares.length} dares`, 'success');
}
function triggerLoadPreset() {
  document.getElementById('load-preset-file').click();
}
function loadPresetFile(event) {
  const file = event.target.files[0]; if (!file) return;
  if (!file.name.endsWith('.json')) { alert('Please select a JSON file'); event.target.value = ''; return; }
  if (!confirm('Loading a preset will replace your current truths and dares lists. Continue?')) { event.target.value=''; return; }
  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      const fileContent = e.target.result;
      JSON.parse(fileContent);
      socket.emit('load_preset_file', { room: ROOM_CODE, file_data: fileContent });
      showToast('Preset', 'Uploading…', 'primary');
    } catch (error) {
      alert('Invalid JSON file: ' + error.message);
    }
    event.target.value = '';
  };
  reader.onerror = function() { alert('Error reading file'); event.target.value = ''; };
  reader.readAsText(file);
}
