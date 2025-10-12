// Global variables
let mySocketId = null;
let hostSocketId = null;
let gameState = { phase: 'lobby', remaining_time: 0 };
let timerInterval = null;

// DOM elements
const playerList = document.getElementById('player-list');
const playerCount = document.getElementById('player-count');
const hostControls = document.getElementById('host-controls');
const lobbySection = document.getElementById('lobby-section');
const gameArea = document.getElementById('game-area');
const startButton = document.getElementById('start-button');

// Socket connection
const socket = io();

// Join the room when connected
socket.on('connect', () => {
  mySocketId = socket.id;
  socket.emit('join', { room: ROOM_CODE, name: PLAYER_NAME });
  
  // Request current settings
  socket.emit('get_settings', { room: ROOM_CODE });
});

// Settings updated event
socket.on('settings_updated', (data) => {
  if (data.settings) {
    // Update settings form with current values
    document.getElementById('setting-countdown').value = data.settings.countdown_duration || 10;
    document.getElementById('setting-preparation').value = data.settings.preparation_duration || 30;
    document.getElementById('setting-selection').value = data.settings.selection_duration || 10;
    document.getElementById('setting-truthdare').value = data.settings.truth_dare_duration || 60;
    document.getElementById('setting-skip').value = data.settings.skip_duration || 5;
    document.getElementById('setting-maxrounds').value = data.settings.max_rounds || 10;
  }
});

// Update player list
socket.on('player_list', (data) => {
  if (!data.players || data.players.length === 0) {
    playerList.innerHTML = '<li class="player-item">Waiting for players...</li>';
    playerCount.textContent = '';
    return;
  }

  hostSocketId = data.host_sid;

  // Update player checkboxes (exclude current player)
  const playerCheckboxes = document.getElementById('player-checkboxes');
  const otherPlayers = data.players.filter(name => name !== PLAYER_NAME);
  
  if (otherPlayers.length === 0) {
    playerCheckboxes.innerHTML = '<div style="color: #999; text-align: center;">No other players yet</div>';
  } else {
    playerCheckboxes.innerHTML = otherPlayers
      .map(name => `
        <div class="player-checkbox-item">
          <label>
            <input type="checkbox" name="target-player" value="${escapeHtml(name)}">
            ${escapeHtml(name)}
          </label>
        </div>
      `)
      .join('');
  }

  // Display all players
  playerList.innerHTML = data.players
    .map((name, index) => {
      const isHost = (index === 0);
      const hostBadge = isHost ? '<span class="host-badge">(Host)</span>' : '';
      const hostClass = isHost ? ' host' : '';
      return `<li class="player-item${hostClass}">${escapeHtml(name)}${hostBadge}</li>`;
    })
    .join('');
  
  playerCount.textContent = `${data.players.length} player(s) in room`;

  // Show host controls if this user is the host
  if (mySocketId === hostSocketId) {
    hostControls.classList.add('show');
  } else {
    hostControls.classList.remove('show');
  }
});

// Game state update
socket.on('game_state_update', (data) => {
  gameState = data;
  updateGameUI();
});

// Submission success
socket.on('submission_success', (data) => {
  const successDiv = document.getElementById('submission-success');
  const targetList = data.targets.join(', ');
  successDiv.textContent = `✓ Added ${data.type}: "${data.text}" to ${targetList}`;
  successDiv.style.display = 'block';
  
  // Clear form
  document.getElementById('truth-dare-text').value = '';
  deselectAllPlayers();
  
  // Hide success message after 3 seconds
  setTimeout(() => {
    successDiv.style.display = 'none';
  }, 3000);
});

// Room was destroyed
socket.on('room_destroyed', () => {
  alert('The host has closed the room.');
  window.location.href = '/';
});

// Successfully left room
socket.on('left_room', () => {
  window.location.href = '/';
});

// Update game UI based on phase
function updateGameUI() {
  // Hide all sections first
  document.getElementById('countdown-section').style.display = 'none';
  document.getElementById('preparation-section').style.display = 'none';
  document.getElementById('selection-section').style.display = 'none';
  document.getElementById('truth-dare-section').style.display = 'none';
  document.getElementById('end-game-section').style.display = 'none';
  
  if (gameState.phase === 'end_game') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('end-game-section').style.display = 'block';
    
    // Show host controls if this user is the host
    const endGameHostControls = document.getElementById('end-game-host-controls');
    if (mySocketId === hostSocketId) {
      endGameHostControls.style.display = 'block';
    } else {
      endGameHostControls.style.display = 'none';
    }
    
    // Display top players
    displayTopPlayers();
    
    // Display round history
    displayRoundHistory();
    
  } else if (gameState.phase === 'countdown') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('countdown-section').style.display = 'block';
    
    // Update countdown timer
    startCountdownTimer();
    
  } else if (gameState.phase === 'preparation') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('preparation-section').style.display = 'block';
    
    // Update preparation timer
    startPreparationTimer();
    
  } else if (gameState.phase === 'selection') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('selection-section').style.display = 'block';
    
    // Update selected player display
    const playerNameElement = document.getElementById('selected-player-name');
    if (gameState.selected_player) {
      playerNameElement.textContent = gameState.selected_player;
      
      // Show truth/dare buttons only for selected player
      const isSelectedPlayer = (gameState.selected_player === PLAYER_NAME);
      const choiceButtons = document.getElementById('truth-dare-choice');
      const choiceMade = document.getElementById('choice-made');
      
      if (isSelectedPlayer && !gameState.selected_choice) {
        choiceButtons.style.display = 'flex';
        choiceMade.style.display = 'none';
      } else {
        choiceButtons.style.display = 'none';
        if (gameState.selected_choice) {
          choiceMade.style.display = 'block';
          document.getElementById('choice-display').textContent = 
            gameState.selected_choice.toUpperCase();
        }
      }
    }
    
    // Update selection timer
    startSelectionTimer();
    
  } else if (gameState.phase === 'truth_dare') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('truth-dare-section').style.display = 'block';
    
    // Update phase type and challenge
    const phaseType = document.getElementById('phase-type');
    const performingPlayer = document.getElementById('performing-player-name');
    const challengeText = document.getElementById('challenge-text');
    
    if (gameState.selected_choice) {
      phaseType.textContent = gameState.selected_choice.toUpperCase();
    }
    
    if (gameState.selected_player) {
      performingPlayer.textContent = gameState.selected_player;
    }
    
    if (gameState.current_truth_dare) {
      challengeText.textContent = gameState.current_truth_dare.text;
    }
    
    // Show vote section only for non-selected players
    const isSelectedPlayer = (gameState.selected_player === PLAYER_NAME);
    const voteSection = document.getElementById('vote-section');
    if (!isSelectedPlayer) {
      voteSection.style.display = 'block';
      
      // Update vote count
      const totalPlayers = playerList.children.length;
      const otherPlayersCount = totalPlayers - 1;
      const requiredVotes = Math.ceil(otherPlayersCount / 2);
      
      document.getElementById('vote-count').textContent = gameState.skip_vote_count || 0;
      document.getElementById('required-votes').textContent = requiredVotes;
    } else {
      voteSection.style.display = 'none';
    }
    
    // Update truth/dare timer
    startTruthDareTimer();
    
  } else if (gameState.phase === 'lobby') {
    // Back to lobby
    lobbySection.classList.remove('hide');
    gameArea.classList.remove('show');
  }
}

function displayTopPlayers() {
  const topPlayersList = document.getElementById('top-players-list');
  
  if (!gameState.top_players || gameState.top_players.length === 0) {
    topPlayersList.innerHTML = '<div style="color: #999; text-align: center;">No players</div>';
    return;
  }
  
  topPlayersList.innerHTML = gameState.top_players
    .map((player, index) => {
      const rank = index + 1;
      const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : '';
      return `
        <div class="top-player">
          <span class="player-rank">${medal} #${rank}</span>
          <div class="player-name-score">
            <span>${escapeHtml(player.name)}</span>
            <span class="player-score">${player.score} pts</span>
          </div>
        </div>
      `;
    })
    .join('');
}

function displayRoundHistory() {
  const roundHistoryList = document.getElementById('round-history-list');
  
  if (!gameState.round_history || gameState.round_history.length === 0) {
    roundHistoryList.innerHTML = '<div style="color: #999; text-align: center;">No rounds played</div>';
    return;
  }
  
  // Reverse to show most recent first
  const reversedHistory = [...gameState.round_history].reverse();
  
  roundHistoryList.innerHTML = reversedHistory
    .map(round => {
      const submitterText = round.submitted_by 
        ? `<div class="round-submitter">Submitted by: ${escapeHtml(round.submitted_by)}</div>`
        : '<div class="round-submitter">Default challenge</div>';
      
      return `
        <div class="round-item">
          <div class="round-header">
            Round ${round.round_number}
          </div>
          <div>
            <span class="round-player">${escapeHtml(round.selected_player)}</span>
            performed a <strong>${round.truth_dare.type}</strong>
          </div>
          <div class="round-challenge">
            "${escapeHtml(round.truth_dare.text)}"
          </div>
          ${submitterText}
        </div>
      `;
    })
    .join('');
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

function openSettings() {
  document.getElementById('settings-modal').classList.add('show');
}

function closeSettings() {
  document.getElementById('settings-modal').classList.remove('show');
}

function saveSettings() {
  const settings = {
    countdown_duration: parseInt(document.getElementById('setting-countdown').value),
    preparation_duration: parseInt(document.getElementById('setting-preparation').value),
    selection_duration: parseInt(document.getElementById('setting-selection').value),
    truth_dare_duration: parseInt(document.getElementById('setting-truthdare').value),
    skip_duration: parseInt(document.getElementById('setting-skip').value),
    max_rounds: parseInt(document.getElementById('setting-maxrounds').value)
  };
  
  // Validate settings
  if (settings.countdown_duration < 3 || settings.countdown_duration > 30) {
    alert('Countdown duration must be between 3 and 30 seconds');
    return;
  }
  if (settings.preparation_duration < 10 || settings.preparation_duration > 120) {
    alert('Preparation duration must be between 10 and 120 seconds');
    return;
  }
  if (settings.selection_duration < 5 || settings.selection_duration > 30) {
    alert('Selection duration must be between 5 and 30 seconds');
    return;
  }
  if (settings.truth_dare_duration < 30 || settings.truth_dare_duration > 180) {
    alert('Truth/Dare duration must be between 30 and 180 seconds');
    return;
  }
  if (settings.skip_duration < 3 || settings.skip_duration > 30) {
    alert('Skip duration must be between 3 and 30 seconds');
    return;
  }
  if (settings.max_rounds < 1 || settings.max_rounds > 50) {
    alert('Maximum rounds must be between 1 and 50');
    return;
  }
  
  socket.emit('update_settings', {
    room: ROOM_CODE,
    settings: settings
  });
  
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

  if (!text) {
    alert('Please enter a truth or dare!');
    return;
  }

  if (targets.length === 0) {
    alert('Please select at least one player!');
    return;
  }

  socket.emit('submit_truth_dare', {
    room: ROOM_CODE,
    text: text,
    type: type,
    targets: targets
  });
}

function selectTruthDare(choice) {
  socket.emit('select_truth_dare', {
    room: ROOM_CODE,
    choice: choice
  });
}

function voteSkip() {
  const button = document.getElementById('vote-skip-button');
  button.disabled = true;
  button.textContent = 'Vote Submitted';
  
  socket.emit('vote_skip', {
    room: ROOM_CODE
  });
}

// Simple HTML escape function
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}