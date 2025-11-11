// View/static/js/ai.js
import { socket, gameState } from './main.js';

export function checkAIStatus() {
  socket.emit('check_ai_status', { room: gameState.roomCode });
}

socket.on('ai_status', (data) => {
  console.log('AI status:', data);
});

socket.on('ai_test_result', (data) => {
  console.log('AI test result:', data.result);
});
