// View/static/js/minigame.js
import { socket, gameState } from './main.js';
import { qs } from './ui_helpers.js';

const minigameSection = qs('#minigame-section');

socket.on('minigame_vote_update', (data) => {
  console.log('Vote update:', data);
});

socket.on('minigame_ended', (data) => {
  alert(`${data.loser} lost the minigame!`);
});
