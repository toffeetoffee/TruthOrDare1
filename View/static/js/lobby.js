// View/static/js/lobby.js
import { socket, gameState } from './main.js';
import { qs } from './ui_helpers.js';

const playerList = qs('#player-list');
const startBtn = qs('#start-game-btn');

socket.on('player_list', (players) => {
  playerList.innerHTML = '';
  players.forEach((p) => {
    const li = document.createElement('li');
    li.className = 'player-item';
    li.textContent = p.name + (p.is_host ? ' (Host)' : '');
    playerList.appendChild(li);
  });
});

socket.on('joined_room', (data) => {
  console.log(`${data.name} joined ${data.room}`);
});

socket.on('left_room', (data) => {
  console.log(`${data.name} left`);
});

startBtn?.addEventListener('click', () => {
  socket.emit('start_game', { room: gameState.roomCode });
});
