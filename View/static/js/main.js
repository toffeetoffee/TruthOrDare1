// View/static/js/main.js
import { qs } from './ui_helpers.js';

export const socket = io();

// Global game data accessible by all modules
export const gameState = {
  roomCode: qs('#room-code')?.textContent,
  playerName: null,
  currentPhase: 'lobby',
};

// When connected, register player name from query params
socket.on('connect', () => {
  const params = new URLSearchParams(window.location.search);
  const name = params.get('name') || 'Anonymous';
  gameState.playerName = name;

  socket.emit('join', { room: gameState.roomCode, name });
});

// Basic error listener
socket.on('error', (data) => {
  alert(data.message || 'An unknown error occurred.');
});
