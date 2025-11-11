// View/static/js/game_flow.js
import { socket, gameState } from './main.js';
import { qs, updateText, show, hide } from './ui_helpers.js';

const phaseName = qs('#phase-name');
const phaseTimer = qs('#phase-timer');
let timerInterval = null;

socket.on('game_started', () => {
  show(qs('#game-section'));
  hide(qs('#lobby-section'));
  updateText('#phase-name', 'Game Starting...');
});

socket.on('phase_started', (data) => {
  gameState.currentPhase = data.phase;
  updateText('#phase-name', `Phase: ${data.phase}`);
});

socket.on('game_state_update', (state) => {
  const remaining = state.remaining_time || 0;
  if (remaining && phaseTimer) {
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      if (remaining > 0) {
        phaseTimer.textContent = `${remaining}s`;
      }
    }, 1000);
  }
});
