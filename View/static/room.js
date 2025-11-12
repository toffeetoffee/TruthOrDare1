// --- Globals & DOM ---
const ROOM_CODE = document.getElementById('roomCode')?.value;
const PLAYER_NAME = document.getElementById('playerName')?.value || 'Anonymous';

let mySocketId = null;
let hostSocketId = null;
let gameState = { phase: 'lobby', remaining_time: 0, round: 1 };

const lobbySection = document.getElementById('lobby-section');
const gameArea = document.getElementById('game-area');

// Buttons
const btnLeave = document.getElementById('btnLeave');
const btnDestroy = document.getElementById('btnDestroy');
const btnStart = document.getElementById('btnStart');
const btnRestart = document.getElementById('btnRestart');
const btnRestartAtEnd = document.getElementById('btnRestartAtEnd');
const btnSettings = document.getElementById('btnSettings');
const btnSaveSettings = document.getElementById('btnSaveSettings');
const btnDownloadPreset = document.getElementById('btnDownloadPreset');

// Submission
const submissionForm = document.getElementById('submission-form');
const textInput = document.getElementById('truth-dare-text');
const typeSelect = document.getElementById('truth-dare-type');
const successDiv = document.getElementById('submission-success');

// Sections
const sections = {
  countdown: document.getElementById('countdown-section'),
  preparation: document.getElementById('preparation-section'),
  selection: document.getElementById('selection-section'),
  minigame: document.getElementById('minigame-section'),
  truthdare: document.getElementById('truth-dare-section'),
  endgame: document.getElementById('end-game-section')
};

// Header bits
const phaseLabel = document.getElementById('phase-label');
const roundNumber = document.getElementById('round-number');
const timerEl = document.getElementById('timer');

// Selection buttons
const btnTruth = document.getElementById('btnTruth');
const btnDare = document.getElementById('btnDare');

// Minigame vote
document.querySelectorAll('.vote-btn').forEach(b => b.addEventListener('click', () => {
  const pick = b.dataset.target;
  socket.emit('minigame_vote', { room: ROOM_CODE, target: pick });
}));

// Skip button
const btnSkip = document.getElementById('btnVoteSkip');
if (btnSkip) btnSkip.addEventListener('click', () => socket.emit('vote_skip', { room: ROOM_CODE }));

// Settings modal
const settingsModal = new bootstrap.Modal(document.getElementById('settingsModal'));

// Socket
const socket = io();

socket.on('connect', () => {
  mySocketId = socket.id;
  socket.emit('join', { room: ROOM_CODE, name: PLAYER_NAME });
  socket.emit('get_settings', { room: ROOM_CODE });
  socket.emit('get_default_lists', { room: ROOM_CODE });
});

// --- Lobby / players ---
const playerList = document.getElementById('player-list');
const playerCount = document.getElementById('player-count');
const playerCheckboxes = document.getElementById('player-checkboxes');

socket.on('player_list', (data) => {
  const players = data.players || [];
  hostSocketId = data.host_sid;
  playerCount.textContent = players.length;

  // Fill visible list
  playerList.innerHTML = '';
  if (players.length === 0) {
    playerList.innerHTML = '<li class="list-group-item text-secondary">Waiting for players…</li>';
  } else {
    players.forEach(name => {
      const li = document.createElement('li');
      li.className = 'list-group-item d-flex align-items-center justify-content-between';
      li.innerHTML = `<span>${name}</span>${(data.host_name === name) ? '<span class="badge text-bg-warning">Host</span>' : ''}`;
      playerList.appendChild(li);
    });
  }

  // Update submission checkboxes (exclude self)
  playerCheckboxes.innerHTML = '';
  players.filter(n => n !== PLAYER_NAME).forEach(n => {
    const div = document.createElement('div');
    div.className = 'form-check';
    div.innerHTML = `<input class="form-check-input" type="checkbox" value="${n}" id="chk-${n}">
                     <label class="form-check-label" for="chk-${n}">${n}</label>`;
    playerCheckboxes.appendChild(div);
  });
});

// --- Game state ---
socket.on('game_state_update', (data) => {
  gameState = data || gameState;
  updateGameUI();
});

socket.on('room_destroyed', () => { window.location.href = '/'; });
socket.on('left_room', () => { window.location.href = '/'; });

// --- Submissions ---
if (submissionForm) {
  submissionForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = textInput.value.trim();
    if (!text) return;
    const type = typeSelect.value;
    const targets = Array.from(playerCheckboxes.querySelectorAll('input:checked')).map(i => i.value);
    socket.emit('submit_truth_dare', { room: ROOM_CODE, text, type, targets });
  });
}
socket.on('submission_success', (data) => {
  successDiv.classList.remove('d-none');
  successDiv.textContent = `✓ Added ${data.type}: "${data.text}" to ${data.targets.join(', ')}`;
  textInput.value = '';
  playerCheckboxes.querySelectorAll('input:checked').forEach(i => i.checked = false);
  setTimeout(() => successDiv.classList.add('d-none'), 2500);
});

// --- Settings ---
btnSettings?.addEventListener('click', () => settingsModal.show());
btnSaveSettings?.addEventListener('click', () => {
  const settings = {
    countdown_duration: +document.getElementById('setting-countdown').value || 10,
    preparation_duration: +document.getElementById('setting-preparation').value || 30,
    selection_duration: +document.getElementById('setting-selection').value || 10,
    truth_dare_duration: +document.getElementById('setting-truthdare').value || 60,
    skip_duration: +document.getElementById('setting-skip').value || 5,
    max_rounds: +document.getElementById('setting-maxrounds').value || 10,
    minigame_chance: +document.getElementById('setting-minigame').value || 20,
    ai_generation_enabled: document.getElementById('setting-ai-generation').checked
  };
  socket.emit('update_settings', { room: ROOM_CODE, settings });
  showToast('Settings', 'Saved successfully');
});

socket.on('settings_updated', (data) => {
  const s = data.settings || {};
  document.getElementById('setting-countdown').value = s.countdown_duration ?? 10;
  document.getElementById('setting-preparation').value = s.preparation_duration ?? 30;
  document.getElementById('setting-selection').value = s.selection_duration ?? 10;
  document.getElementById('setting-truthdare').value = s.truth_dare_duration ?? 60;
  document.getElementById('setting-skip').value = s.skip_duration ?? 5;
  document.getElementById('setting-maxrounds').value = s.max_rounds ?? 10;
  document.getElementById('setting-minigame').value = s.minigame_chance ?? 20;
  document.getElementById('setting-ai-generation').checked = !!s.ai_generation_enabled;
});

// --- Defaults list (truths/dares) ---
const truthList = document.getElementById('truth-list');
const dareList = document.getElementById('dare-list');

const presetFile = document.getElementById('presetFile');
const btnAddTruth = document.getElementById('btnAddTruth');
const btnAddDare = document.getElementById('btnAddDare');
const btnClearTruths = document.getElementById('btnClearTruths');
const btnClearDares = document.getElementById('btnClearDares');

btnAddTruth?.addEventListener('click', () => {
  const text = document.getElementById('new-truth').value.trim();
  if (!text) return;
  socket.emit('add_default_truth', { room: ROOM_CODE, text });
  document.getElementById('new-truth').value = '';
});
btnAddDare?.addEventListener('click', () => {
  const text = document.getElementById('new-dare').value.trim();
  if (!text) return;
  socket.emit('add_default_dare', { room: ROOM_CODE, text });
  document.getElementById('new-dare').value = '';
});
btnClearTruths?.addEventListener('click', () => socket.emit('remove_default_truths', { room: ROOM_CODE }));
btnClearDares?.addEventListener('click', () => socket.emit('remove_default_dares', { room: ROOM_CODE }));

btnDownloadPreset?.addEventListener('click', () => {
  // Ask server for current defaults; when received, download
  socket.emit('get_default_lists', { room: ROOM_CODE });
  showToast('Preset', 'Downloading current defaults…');
});

presetFile?.addEventListener('change', (e) => {
  const file = e.target.files?.[0]; if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const json = JSON.parse(reader.result);
      socket.emit('load_preset_file', { room: ROOM_CODE, content: json });
    } catch (err) {
      showToast('Preset', 'Invalid JSON file');
    }
    e.target.value = '';
  };
  reader.readAsText(file);
});

socket.on('default_lists_updated', (data) => {
  const truths = data.truths || [];
  const dares  = data.dares || [];

  const renderList = (ul, items, type) => {
    ul.innerHTML = '';
    items.forEach((t, idx) => {
      const li = document.createElement('li');
      li.className = 'list-group-item d-flex align-items-center justify-content-between';
      li.innerHTML = `<span class="me-2 flex-grow-1">${t}</span>
                      <button class="btn btn-sm btn-outline-secondary" data-idx="${idx}" data-type="${type}"><i class="bi bi-pencil-square"></i></button>`;
      ul.appendChild(li);
    });
    // edit buttons
    ul.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        const which = btn.dataset.type;
        const idx = +btn.dataset.idx;
        const current = items[idx];
        const updated = prompt(`Edit ${which}`, current);
        if (updated && updated.trim()) {
          if (which === 'truth') socket.emit('edit_default_truth', { room: ROOM_CODE, index: idx, new_text: updated.trim() });
          if (which === 'dare')  socket.emit('edit_default_dare',  { room: ROOM_CODE, index: idx, new_text: updated.trim() });
        }
      });
    });
  };
  if (truthList) renderList(truthList, truths, 'truth');
  if (dareList)  renderList(dareList, dares, 'dare');

  // If this update came after requesting download, offer file
  if (btnDownloadPreset && btnDownloadPreset.dataset.download === '1') {
    const blob = new Blob([JSON.stringify({ truths, dares }, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `defaults_${ROOM_CODE}.json`;
    a.click();
    btnDownloadPreset.dataset.download = '0';
  }
});
btnDownloadPreset?.addEventListener('click', () => { btnDownloadPreset.dataset.download = '1'; });

socket.on('preset_loaded', () => showToast('Preset', 'Preset loaded'));
socket.on('preset_error', (d) => showToast('Preset error', d?.error||'Failed'));

// --- Controls ---
btnStart?.addEventListener('click', () => socket.emit('start_game', { room: ROOM_CODE }));
btnRestart?.addEventListener('click', () => socket.emit('restart_game', { room: ROOM_CODE }));
btnRestartAtEnd?.addEventListener('click', () => socket.emit('restart_game', { room: ROOM_CODE }));
btnLeave?.addEventListener('click', () => socket.emit('leave', { room: ROOM_CODE }));
btnDestroy?.addEventListener('click', () => socket.emit('destroy_room', { room: ROOM_CODE }));

// Select truth/dare choice
btnTruth?.addEventListener('click', () => socket.emit('select_truth_dare', { room: ROOM_CODE, choice: 'truth' }));
btnDare?.addEventListener('click', () => socket.emit('select_truth_dare', { room: ROOM_CODE, choice: 'dare' }));

// --- UI update ---
function showSection(name) {
  for (const [key, el] of Object.entries(sections)) {
    if (!el) continue;
    if (key === name) { el.classList.remove('d-none'); el.classList.add('showing'); }
    else { el.classList.add('d-none'); el.classList.remove('showing'); }
  }
  if (name) {
    lobbySection?.classList.add('d-none');
    gameArea?.classList.remove('d-none');
  }
}

function updateGameUI() {
  phaseLabel.textContent = gameState.phase || 'lobby';
  roundNumber.textContent = gameState.round || 1;
  timerEl.textContent = Math.max(0, Math.floor(gameState.remaining_time || 0));

  const phase = gameState.phase;
  if (phase === 'lobby') {
    lobbySection?.classList.remove('d-none');
    gameArea?.classList.add('d-none');
    showSection('');
    return;
  }
  if (phase === 'countdown') showSection('countdown');
  else if (phase === 'preparation') showSection('preparation');
  else if (phase === 'selection') showSection('selection');
  else if (phase === 'minigame')  showSection('minigame');
  else if (phase === 'truth_dare') showSection('truthdare');
  else if (phase === 'end_game')  showSection('endgame');

  // Truth/dare details
  if (phase === 'truth_dare' && gameState.current_player) {
    document.getElementById('selected-player').textContent = gameState.current_player || '—';
    document.getElementById('current-item-type').textContent = gameState.current_type || 'truth';
    document.getElementById('current-item-text').textContent = gameState.current_text || '';
  }

  // Minigame details
  if (phase === 'minigame' && gameState.minigame) {
    document.querySelector('.minigame-title').textContent = gameState.minigame.name || 'Mini Game';
    document.querySelector('.minigame-description').textContent = gameState.minigame.description_voter || '';
    const parts = gameState.minigame.participants || [];
    document.getElementById('participant-1').textContent = parts[0] || 'Player 1';
    document.getElementById('participant-2').textContent = parts[1] || 'Player 2';
    const votes = gameState.minigame.vote_counts || { A: 0, B: 0 };
    document.getElementById('vote-count-a').textContent = votes.A || 0;
    document.getElementById('vote-count-b').textContent = votes.B || 0;
  }

  // End game summary
  if (phase === 'end_game') {
    const top = gameState.top_players || [];
    const hist = gameState.round_history || [];
    const topEl = document.getElementById('top-players');
    const histEl = document.getElementById('round-history');
    if (topEl) {
      topEl.innerHTML = '';
      top.slice(0, 5).forEach(p => {
        const li = document.createElement('li');
        li.textContent = `${p.name} — ${p.score} pts`;
        topEl.appendChild(li);
      });
    }
    if (histEl) {
      histEl.innerHTML = '';
      hist.forEach((r, i) => {
        const div = document.createElement('div');
        div.className = 'mb-1';
        div.textContent = `${i+1}. ${r.player} did ${r.type}: "${r.text}" — submitted by ${r.submitted_by}`;
        histEl.appendChild(div);
      });
    }
  }
}

// Timer tick (client-side countdown visual only)
setInterval(() => {
  if (gameState.remaining_time > 0) {
    gameState.remaining_time -= 1;
    timerEl.textContent = Math.max(0, Math.floor(gameState.remaining_time));
  }
}, 1000);
