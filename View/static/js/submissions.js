// View/static/js/submissions.js
import { socket, gameState } from './main.js';
import { qs } from './ui_helpers.js';

const submitBtn = qs('#submit-btn');
const textInput = qs('#submission-text');
const typeSelect = qs('#submission-type');

submitBtn?.addEventListener('click', () => {
  const text = textInput.value.trim();
  const type = typeSelect.value;
  if (!text) return alert('Please enter a truth or dare.');

  socket.emit('submit_truth_dare', {
    room: gameState.roomCode,
    text,
    type,
    targets: [], // can add UI for selecting targets later
  });

  textInput.value = '';
});

socket.on('submission_result', (data) => {
  if (data.success) alert('Submission accepted!');
  else alert('Submission failed.');
});
