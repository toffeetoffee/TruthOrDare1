// --- Theme toggle ---
(function(){
  const toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-bs-theme') || 'dark';
      const next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-bs-theme', next);
      localStorage.setItem('tod-theme', next);
    });
  }
})();

// --- Helpers ---
function showToast(msg) {
  const toastEl = document.getElementById('mainToast');
  const body = document.getElementById('toast-body');
  body.textContent = msg;
  const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
  toast.show();
}
function escapeHtml(str){ return (str || '').replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[s])); }

// --- Socket.IO ---
const socket = io({ transports: ['websocket', 'polling'] });
let mySocketId = null;
let hostSocketId = null;

const playerListEl = document.getElementById('player-list');
const playerCountEl = document.getElementById('player-count');
const hostControls = document.getElementById('host-controls');

const timerEl = document.getElementById('timer');
const phaseLabel = document.getElementById('phase-label');
const phasePanels = {
  lobby: document.getElementById('panel-lobby'),
  preparation: document.getElementById('panel-preparation'),
  selection: document.getElementById('panel-selection'),
  truth_dare: document.getElementById('panel-truthdare'),
  end: document.getElementById('panel-end')
};
const selectedPlayerEl = document.getElementById('selected-player');
const currentPromptEl = document.getElementById('current-prompt');

// Connect -> join
socket.on('connect', () => {
  mySocketId = socket.id;
  socket.emit('join', { room: ROOM_CODE, name: PLAYER_NAME });
  socket.emit('get_settings', { room: ROOM_CODE });
  socket.emit('get_default_lists', { room: ROOM_CODE });
});

// Player list
socket.on('player_list', (data) => {
  const players = (data && data.players) || [];
  hostSocketId = data.host_sid;
  playerListEl.innerHTML = players.map((name, idx) => {
    const isHost = (idx === 0);
    const hostBadge = isHost ? '<span class="badge text-bg-info ms-2">Host</span>' : '';
    return `<li class="list-group-item d-flex justify-content-between align-items-center">
      <span>${escapeHtml(name)}</span>${hostBadge}
    </li>`;
  }).join('');
  playerCountEl.textContent = players.length;
  // Check host
  if (mySocketId && mySocketId === hostSocketId) {
    hostControls.hidden = false;
  } else {
    hostControls.hidden = true;
  }
});

// Game state
socket.on('game_state_update', (data) => {
  if (!data) return;
  const phase = data.phase || 'lobby';
  phaseLabel.textContent = (phase === 'truth_dare') ? 'Truth / Dare' : phase.replace('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
  timerEl.textContent = (data.remaining_time != null) ? String(data.remaining_time) : '--';

  // Panels
  Object.entries(phasePanels).forEach(([key, el]) => {
    el.classList.toggle('d-none', key !== phase);
  });

  if (phase === 'truth_dare') {
    if (data.selected_player) {
      selectedPlayerEl.textContent = `Selected: ${data.selected_player}`;
    } else {
      selectedPlayerEl.textContent = '';
    }
    if (data.current_prompt) currentPromptEl.textContent = data.current_prompt;
  }

  if (phase === 'end' && Array.isArray(data.scoreboard)) {
    const sb = document.getElementById('scoreboard');
    sb.innerHTML = '<div class="list-group">' + data.scoreboard.map((row, idx) =>
      `<div class="list-group-item d-flex justify-content-between">
        <div><span class="badge text-bg-secondary me-2">${idx+1}</span>${escapeHtml(row.name)}</div>
        <div class="fw-bold">${row.score}</div>
      </div>`).join('') + '</div>';
  }
});

// Settings sync
socket.on('settings_updated', (data) => {
  if (!data || !data.settings) return;
  const s = data.settings;
  document.getElementById('setting-countdown').value = s.countdown_duration ?? 10;
  document.getElementById('setting-preparation').value = s.preparation_duration ?? 30;
  document.getElementById('setting-selection').value = s.selection_duration ?? 10;
  document.getElementById('setting-truthdare').value = s.truth_dare_duration ?? 60;
  document.getElementById('setting-skip').value = s.skip_duration ?? 5;
  document.getElementById('setting-maxrounds').value = s.max_rounds ?? 10;
  document.getElementById('setting-minigame').value = s.minigame_chance ?? 20;
  document.getElementById('setting-ai-generation').checked = !!s.ai_generation_enabled;
});

// Default list updates (optional UI hints)
socket.on('default_lists_updated', () => {
  showToast('Default lists updated.');
});

socket.on('submission_success', (data) => {
  showToast(data && data.message ? data.message : 'Submission accepted!');
});

socket.on('room_destroyed', () => {
  showToast('Room destroyed by host.');
  setTimeout(() => location.href = '/', 1200);
});

socket.on('left_room', () => {
  showToast('You left the room.');
  setTimeout(() => location.href = '/', 800);
});

socket.on('preset_loaded', () => showToast('Preset loaded.'));
socket.on('preset_error', (data) => showToast(data && data.message ? data.message : 'Preset error.'));

// --- Host controls ---
document.getElementById('start-button').addEventListener('click', () => {
  socket.emit('start_game', { room: ROOM_CODE });
});
document.getElementById('restart-button').addEventListener('click', () => {
  if (confirm('Restart the current game?')) socket.emit('restart_game', { room: ROOM_CODE });
});
document.getElementById('destroy-button').addEventListener('click', () => {
  if (confirm('Destroy this room for everyone?')) socket.emit('destroy_room', { room: ROOM_CODE });
});

// Settings modal
document.getElementById('save-settings').addEventListener('click', (e) => {
  e.preventDefault();
  const settings = {
    countdown_duration: Number(document.getElementById('setting-countdown').value),
    preparation_duration: Number(document.getElementById('setting-preparation').value),
    selection_duration: Number(document.getElementById('setting-selection').value),
    truth_dare_duration: Number(document.getElementById('setting-truthdare').value),
    skip_duration: Number(document.getElementById('setting-skip').value),
    max_rounds: Number(document.getElementById('setting-maxrounds').value),
    minigame_chance: Number(document.getElementById('setting-minigame').value),
    ai_generation_enabled: document.getElementById('setting-ai-generation').checked
  };
  socket.emit('update_settings', { room: ROOM_CODE, settings });
  showToast('Settings saved.');
});

// Default content management
document.getElementById('add-default-truth').addEventListener('click', async () => {
  const text = prompt('New default truth:');
  if (!text) return;
  socket.emit('add_default_truth', { room: ROOM_CODE, text });
});
document.getElementById('add-default-dare').addEventListener('click', async () => {
  const text = prompt('New default dare:');
  if (!text) return;
  socket.emit('add_default_dare', { room: ROOM_CODE, text });
});
document.getElementById('remove-default-truths').addEventListener('click', () => {
  if (confirm('Clear ALL default truths?')) socket.emit('remove_default_truths', { room: ROOM_CODE });
});
document.getElementById('remove-default-dares').addEventListener('click', () => {
  if (confirm('Clear ALL default dares?')) socket.emit('remove_default_dares', { room: ROOM_CODE });
});

// Presets
document.getElementById('save-preset').addEventListener('click', () => {
  // Backend expects a file for loading; for saving we build from what we know: ask server? Here we create empty skeleton for user to edit.
  const preset = { truths: [], dares: [] };
  const blob = new Blob([JSON.stringify(preset, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `truth_dare_preset_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a); a.click(); a.remove();
});

document.getElementById('load-preset-file').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (!confirm('Loading a preset will replace current defaults for everyone. Continue?')) return;
  const text = await file.text();
  socket.emit('load_preset_file', { room: ROOM_CODE, file_data: text });
});

// --- Preparation submissions ---
function getTargets(){
  return Array.from(document.querySelectorAll('#player-checkboxes input[type=checkbox]:checked')).map(c => c.value);
}

document.getElementById('submit-truth').addEventListener('click', () => {
  const lines = (document.getElementById('submission-text').value || '').split(/\n/).map(s => s.trim()).filter(Boolean).slice(0,3);
  const targets = getTargets();
  if (!lines.length || !targets.length) return showToast('Add up to 3 lines and select targets.');
  socket.emit('submit_truth_dare', { room: ROOM_CODE, type: 'truth', items: lines, targets });
  document.getElementById('submission-text').value = '';
});

document.getElementById('submit-dare').addEventListener('click', () => {
  const lines = (document.getElementById('submission-text').value || '').split(/\n/).map(s => s.trim()).filter(Boolean).slice(0,3);
  const targets = getTargets();
  if (!lines.length || !targets.length) return showToast('Add up to 3 lines and select targets.');
  socket.emit('submit_truth_dare', { room: ROOM_CODE, type: 'dare', items: lines, targets });
  document.getElementById('submission-text').value = '';
});

// Selection/minigame
document.getElementById('minigame-vote').addEventListener('click', () => {
  socket.emit('minigame_vote', { room: ROOM_CODE });
});

// Truth/dare choice + skip
document.getElementById('choose-truth').addEventListener('click', () => {
  socket.emit('select_truth_dare', { room: ROOM_CODE, choice: 'truth' });
});
document.getElementById('choose-dare').addEventListener('click', () => {
  socket.emit('select_truth_dare', { room: ROOM_CODE, choice: 'dare' });
});
document.getElementById('vote-skip').addEventListener('click', () => {
  socket.emit('vote_skip', { room: ROOM_CODE });
});

// Leave
document.getElementById('leave-btn').addEventListener('click', () => {
  socket.emit('leave', { room: ROOM_CODE });
});

// Keep target checkboxes fresh whenever player_list arrives
socket.on('player_list', (data) => {
  const otherPlayers = (data.players || []).filter(n => n !== PLAYER_NAME);
  const box = document.getElementById('player-checkboxes');
  if (!box) return;
  if (!otherPlayers.length) {
    box.innerHTML = '<div class="text-secondary small">No other players yet.</div>';
    return;
  }
  box.innerHTML = otherPlayers.map(name => `
    <div class="col-6 col-md-4">
      <div class="form-check">
        <input class="form-check-input" type="checkbox" value="${escapeHtml(name)}" id="p_${escapeHtml(name)}">
        <label class="form-check-label" for="p_${escapeHtml(name)}">${escapeHtml(name)}</label>
      </div>
    </div>
  `).join('');
});
