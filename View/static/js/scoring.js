// View/static/js/scoring.js
import { socket, gameState } from './main.js';
import { qs } from './ui_helpers.js';

const scoreboardSection = qs('#scoreboard-section');

socket.on('scores', (data) => {
  scoreboardSection.innerHTML = '<h3>Scores</h3>';
  const ul = document.createElement('ul');
  data.players.forEach((p) => {
    const li = document.createElement('li');
    li.textContent = `${p.name}: ${p.score}`;
    ul.appendChild(li);
  });
  scoreboardSection.appendChild(ul);
});

socket.on('round_history', (data) => {
  console.log('Round history:', data.records);
});
