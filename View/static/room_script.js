// Global variables
let mySocketId = null;
let hostSocketId = null;
let gameState = { phase: 'lobby', remaining_time: 0 };
let timerInterval = null;

// Store default lists
let defaultTruths = [];
let defaultDares = [];

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

  // Request default lists
  socket.emit('get_default_lists', { room: ROOM_CODE });
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
    document.getElementById('setting-minigame').value = data.settings.minigame_chance || 20;
    document.getElementById('setting-ai-generation').checked =
      data.settings.ai_generation_enabled !== undefined
        ? data.settings.ai_generation_enabled
        : true;
  }
});

// Default lists updated event
socket.on('default_lists_updated', (data) => {
  if (data.truths !== undefined) {
    defaultTruths = data.truths;
    renderDefaultList('truth');
  }
  if (data.dares !== undefined) {
    defaultDares = data.dares;
    renderDefaultList('dare');
  }
});

// Preset loaded event
socket.on('preset_loaded', (data) => {
  alert(data.message);
});

// Preset error event
socket.on('preset_error', (data) => {
  alert('Error: ' + data.message);
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
  const otherPlayers = data.players.filter((name) => name !== PLAYER_NAME);

  if (otherPlayers.length === 0) {
    playerCheckboxes.innerHTML =
      '<div style="color: #999; text-align: center;">No other players yet</div>';
  } else {
    playerCheckboxes.innerHTML = otherPlayers
      .map(
        (name) => `
        <div class="player-checkbox-item">
          <label>
            <input type="checkbox" name="target-player" value="${escapeHtml(name)}">
            ${escapeHtml(name)}
          </label>
        </div>
      `,
      )
      .join('');
  }

  // Display all players
  playerList.innerHTML = data.players
    .map((name, index) => {
      const isHost = index === 0;
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

// Helper: set phase label
function setPhaseLabel(label) {
  const phaseType = document.getElementById('phase-type');
  if (phaseType) {
    phaseType.textContent = label;
  }
}

// Update game UI based on phase
function updateGameUI() {
  // Hide all sections first
  document.getElementById('countdown-section').style.display = 'none';
  document.getElementById('preparation-section').style.display = 'none';
  document.getElementById('selection-section').style.display = 'none';
  document.getElementById('minigame-section').style.display = 'none';
  document.getElementById('truth-dare-section').style.display = 'none';
  document.getElementById('end-game-section').style.display = 'none';

  // Default: hide empty banner
  const emptyListBanner = document.getElementById('empty-list-banner');
  if (emptyListBanner) {
    emptyListBanner.style.display = 'none';
  }

  if (gameState.phase === 'end_game') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('end-game-section').style.display = 'block';
    setPhaseLabel('End Game');

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
  } else if (gameState.phase === 'minigame') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('minigame-section').style.display = 'block';
    setPhaseLabel('Minigame');

    if (gameState.minigame) {
      const m = gameState.minigame;
      const participants = m.participants || [];

      // Universal text fields
      const titleEl = document.querySelector('.minigame-title');
      if (titleEl) {
        titleEl.textContent = m.name || 'Mini Game';
      }
      const descEl = document.querySelector('.minigame-description');
      if (descEl) {
        descEl.textContent = m.description_voter || '';
      }

      // Update voting instruction
      const voteInstructionEl = document.querySelector('.voting-instruction');
      if (voteInstructionEl) {
        voteInstructionEl.textContent = m.vote_instruction || 'Vote for the loser!';
      }

      // Participants display
      const p1 = participants[0] || 'Player 1';
      const p2 = participants[1] || 'Player 2';

      const part1El = document.getElementById('participant-1');
      const part2El = document.getElementById('participant-2');
      if (part1El) part1El.textContent = p1;
      if (part2El) part2El.textContent = p2;

      // Vote counts
      const voteCounts = m.vote_counts || {};
      const votes1 = voteCounts[participants[0]] || 0;
      const votes2 = voteCounts[participants[1]] || 0;
      const p1VotesEl = document.getElementById('participant-1-votes');
      const p2VotesEl = document.getElementById('participant-2-votes');
      if (p1VotesEl) {
        p1VotesEl.textContent = `${votes1} vote${votes1 !== 1 ? 's' : ''}`;
      }
      if (p2VotesEl) {
        p2VotesEl.textContent = `${votes2} vote${votes2 !== 1 ? 's' : ''}`;
      }

      // Participant or voter
      const isParticipant = participants.includes(PLAYER_NAME);
      const votingContainer = document.getElementById('minigame-voting');
      const participantMsgBox = document.getElementById('minigame-participant-message');

      if (isParticipant) {
        if (votingContainer) votingContainer.style.display = 'none';
        if (participantMsgBox) {
          participantMsgBox.style.display = 'block';
          const p = participantMsgBox.querySelector('p:first-child');
          if (p) {
            p.textContent = m.description_participant || 'You are participating!';
          }
        }
      } else {
        if (votingContainer) votingContainer.style.display = 'block';
        if (participantMsgBox) participantMsgBox.style.display = 'none';

        const btn1 = document.getElementById('vote-btn-1');
        const btn2 = document.getElementById('vote-btn-2');
        const voteName1 = document.getElementById('vote-name-1');
        const voteName2 = document.getElementById('vote-name-2');

        if (btn1 && btn2) {
          btn1.disabled = false;
          btn2.disabled = false;
        }
        if (voteName1) voteName1.textContent = p1;
        if (voteName2) voteName2.textContent = p2;

        if (btn1) btn1.onclick = () => voteMinigame(p1);
        if (btn2) btn2.onclick = () => voteMinigame(p2);

        // Vote count progress
        const voteCountEl = document.getElementById('minigame-vote-count');
        const requiredVotesEl = document.getElementById('minigame-required-votes');
        if (voteCountEl) voteCountEl.textContent = m.vote_count || 0;
        if (requiredVotesEl) requiredVotesEl.textContent = m.total_voters || 0;
      }
    }
  } else if (gameState.phase === 'countdown') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('countdown-section').style.display = 'block';
    setPhaseLabel('Countdown');

    // Update countdown timer
    startCountdownTimer();
  } else if (gameState.phase === 'preparation') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('preparation-section').style.display = 'block';
    setPhaseLabel('Preparation');

    // Update preparation timer
    startPreparationTimer();
  } else if (gameState.phase === 'selection') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('selection-section').style.display = 'block';
    setPhaseLabel('Selection');

    // Update selected player display
    const playerNameElement = document.getElementById('selected-player-name');
    if (gameState.selected_player && playerNameElement) {
      playerNameElement.textContent = gameState.selected_player;

      // Show truth/dare buttons only for selected player
      const isSelectedPlayer = gameState.selected_player === PLAYER_NAME;
      const choiceButtons = document.getElementById('truth-dare-choice');
      const choiceMade = document.getElementById('choice-made');

      if (isSelectedPlayer && !gameState.selected_choice) {
        if (choiceButtons) choiceButtons.style.display = 'flex';
        if (choiceMade) choiceMade.style.display = 'none';
      } else {
        if (choiceButtons) choiceButtons.style.display = 'none';
        if (choiceMade && gameState.selected_choice) {
          choiceMade.style.display = 'block';
          const choiceDisplay = document.getElementById('choice-display');
          if (choiceDisplay) {
            choiceDisplay.textContent = gameState.selected_choice.toUpperCase();
          }
        }
      }
    }

    // Update selection timer
    startSelectionTimer();
  } else if (gameState.phase === 'truth_dare') {
    lobbySection.classList.add('hide');
    gameArea.classList.add('show');
    document.getElementById('truth-dare-section').style.display = 'block';

    // Phase label based on selected_choice
    if (gameState.selected_choice) {
      setPhaseLabel(gameState.selected_choice.toUpperCase());
    } else {
      setPhaseLabel('Truth/Dare');
    }

    // Show/hide empty list banner
    if (emptyListBanner) {
      if (gameState.list_empty) {
        emptyListBanner.style.display = 'flex';
      } else {
        emptyListBanner.style.display = 'none';
      }
    }

    const performingPlayer = document.getElementById('performing-player-name');
    const challengeText = document.getElementById('challenge-text');

    if (gameState.selected_player && performingPlayer) {
      performingPlayer.textContent = gameState.selected_player;
    }

    if (challengeText && gameState.current_truth_dare) {
      challengeText.textContent = gameState.current_truth_dare.text;

      // Add warning styling if list was empty
      if (gameState.list_empty) {
        challengeText.style.background = '#fff3cd';
        challengeText.style.color = '#856404';
        challengeText.style.border = '2px solid #ffc107';
        challengeText.style.fontWeight = 'bold';
      } else {
        // Reset to normal styling
        challengeText.style.background = '';
        challengeText.style.color = '';
        challengeText.style.border = '';
        challengeText.style.fontWeight = '';
      }
    }

    // Show vote section only for non-selected players
    const isSelectedPlayer = gameState.selected_player === PLAYER_NAME;
    const voteSection = document.getElementById('vote-section');
    if (voteSection) {
      if (!isSelectedPlayer) {
        voteSection.style.display = 'block';

        const voteSkipButton = document.getElementById('vote-skip-button');

        if (voteSkipButton) {
          // Check if list was empty or skip has been activated
          if (gameState.list_empty) {
            // List empty - skip auto-activated
            voteSkipButton.disabled = true;
            voteSkipButton.textContent = '⚠️ List Empty - Skip Auto-Activated!';
            voteSkipButton.style.background = '#ffc107';
            voteSkipButton.style.color = '#000';
          } else if (gameState.skip_activated) {
            // Skip activated normally
            voteSkipButton.disabled = true;
            voteSkipButton.textContent = 'Skip Activated!';
            voteSkipButton.style.background = '#6c757d';
            voteSkipButton.style.color = 'white';
          } else {
            // Re-enable skip vote button (reset from previous rounds)
            voteSkipButton.disabled = false;
            voteSkipButton.textContent = 'Vote to Skip';
            voteSkipButton.style.background = '#6c757d';
            voteSkipButton.style.color = 'white';
          }
        }

        // Update vote count
        const totalPlayers = playerList.children.length;
        const otherPlayersCount = totalPlayers - 1;
        const requiredVotes = Math.ceil(otherPlayersCount / 2);

        const voteCountEl = document.getElementById('vote-count');
        const requiredVotesEl = document.getElementById('required-votes');
        if (voteCountEl) voteCountEl.textContent = gameState.skip_vote_count || 0;
        if (requiredVotesEl) requiredVotesEl.textContent = requiredVotes;
      } else {
        voteSection.style.display = 'none';
      }
    }

    // Update truth/dare timer
    startTruthDareTimer();
  } else if (gameState.phase === 'lobby') {
    // Back to lobby
    lobbySection.classList.remove('hide');
    gameArea.classList.remove('show');
    setPhaseLabel('Lobby');
  }
}

function displayTopPlayers() {
  const topPlayersList = document.getElementById('top-players-list');

  if (!gameState.top_players || gameState.top_players.length === 0) {
    topPlayersList.innerHTML =
      '<div style="color: #999; text-align: center;">No players</div>';
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
    roundHistoryList.innerHTML =
      '<div style="color: #999; text-align: center;">No rounds played</div>';
    return;
  }

  // Reverse to show most recent first
  const reversedHistory = [...gameState.round_history].reverse();

  roundHistoryList.innerHTML = reversedHistory
    .map((round) => {
      const submitterText = round.submitted_by
        ? `<div class="round-submitter">Submitted by: ${escapeHtml(
            round.submitted_by,
          )}</div>`
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
    const headerTimer = document.getElementById('countdown-timer');
    const bigTimer = document.getElementById('big-countdown-timer');

    const value = Math.max(0, gameState.remaining_time);

    if (headerTimer) {
      headerTimer.textContent = value;
    }
    if (bigTimer) {
      bigTimer.textContent = value;
    }

    gameState.remaining_time--;
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
  if (
    confirm(
      'Are you sure you want to destroy the room? All players will be kicked.',
    )
  ) {
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
    countdown_duration: parseInt(
      document.getElementById('setting-countdown').value,
      10,
    ),
    preparation_duration: parseInt(
      document.getElementById('setting-preparation').value,
      10,
    ),
    selection_duration: parseInt(
      document.getElementById('setting-selection').value,
      10,
    ),
    truth_dare_duration: parseInt(
      document.getElementById('setting-truthdare').value,
      10,
    ),
    skip_duration: parseInt(
      document.getElementById('setting-skip').value,
      10,
    ),
    max_rounds: parseInt(
      document.getElementById('setting-maxrounds').value,
      10,
    ),
    minigame_chance: parseInt(
      document.getElementById('setting-minigame').value,
      10,
    ),
    ai_generation_enabled:
      document.getElementById('setting-ai-generation').checked,
  };

  // Validate settings
  if (settings.countdown_duration < 3 || settings.countdown_duration > 30) {
    alert('Countdown duration must be between 3 and 30 seconds');
    return;
  }
  if (
    settings.preparation_duration < 10 ||
    settings.preparation_duration > 120
  ) {
    alert('Preparation duration must be between 10 and 120 seconds');
    return;
  }
  if (settings.selection_duration < 5 || settings.selection_duration > 30) {
    alert('Selection duration must be between 5 and 30 seconds');
    return;
  }
  if (
    settings.truth_dare_duration < 30 ||
    settings.truth_dare_duration > 180
  ) {
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
  if (settings.minigame_chance < 0 || settings.minigame_chance > 100) {
    alert('Minigame chance must be between 0 and 100%');
    return;
  }

  socket.emit('update_settings', {
    room: ROOM_CODE,
    settings: settings,
  });

  closeSettings();
}

function startGame() {
  enterGameMode();
  if (startButton) startButton.disabled = true;
  socket.emit('start_game', { room: ROOM_CODE });
}

function restartGame() {
  if (
    confirm(
      'Are you sure you want to restart the game? All scores will be reset.',
    )
  ) {
    socket.emit('restart_game', { room: ROOM_CODE });
  }
}

function voteMinigame(playerName) {
  if (!playerName) return;

  // Disable both buttons after voting
  const btn1 = document.getElementById('vote-btn-1');
  const btn2 = document.getElementById('vote-btn-2');
  if (btn1) btn1.disabled = true;
  if (btn2) btn2.disabled = true;

  socket.emit('minigame_vote', {
    room: ROOM_CODE,
    voted_player: playerName,
  });
}

function selectAllPlayers() {
  const checkboxes = document.querySelectorAll('input[name="target-player"]');
  checkboxes.forEach((cb) => (cb.checked = true));
}

function deselectAllPlayers() {
  const checkboxes = document.querySelectorAll('input[name="target-player"]');
  checkboxes.forEach((cb) => (cb.checked = false));
}

function submitTruthDare() {
  const text = document.getElementById('truth-dare-text').value.trim();
  const type = document.getElementById('truth-dare-type').value;
  const checkboxes = document.querySelectorAll(
    'input[name="target-player"]:checked',
  );
  const targets = Array.from(checkboxes).map((cb) => cb.value);

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
    targets: targets,
  });
}

function selectTruthDare(choice) {
  socket.emit('select_truth_dare', {
    room: ROOM_CODE,
    choice: choice,
  });
}

function voteSkip() {
  const button = document.getElementById('vote-skip-button');
  if (button) {
    button.disabled = true;
    button.textContent = 'Vote Submitted';
  }

  socket.emit('vote_skip', {
    room: ROOM_CODE,
  });
}

// Simple HTML escape function
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Settings Tab Management
function showSettingsTab(tabName) {
  // Remove active class from all tabs and contents
  document.querySelectorAll('.settings-tab').forEach((tab) => {
    tab.classList.remove('active');
  });
  document.querySelectorAll('.settings-tab-content').forEach((content) => {
    content.classList.remove('active');
  });

  // Add active class to selected tab and content
  if (event && event.target) {
    event.target.classList.add('active');
  }
  const contentEl = document.getElementById(`settings-tab-${tabName}`);
  if (contentEl) contentEl.classList.add('active');
}

// Render default list
function renderDefaultList(type) {
  const listContainer = document.getElementById(`default-${type}s-list`);
  const items = type === 'truth' ? defaultTruths : defaultDares;

  if (!listContainer) return;

  if (items.length === 0) {
    listContainer.innerHTML = `<div class="default-list-empty">No default ${type}s yet. Click "Add" to add one.</div>`;
    return;
  }

  listContainer.innerHTML = items
    .map(
      (text, index) => `
    <div class="default-list-item" onclick="toggleItemSelection(event, '${type}', ${index})">
      <input type="checkbox" 
             id="default-${type}-${index}" 
             data-type="${type}" 
             data-text="${escapeHtml(text)}"
             onclick="event.stopPropagation()">
      <div class="default-list-item-text">${escapeHtml(text)}</div>
    </div>
  `,
    )
    .join('');
}

// Toggle item selection
function toggleItemSelection(event, type, index) {
  const checkbox = document.getElementById(`default-${type}-${index}`);
  if (!checkbox) return;

  checkbox.checked = !checkbox.checked;

  // Update item styling
  const item = event.currentTarget;
  if (checkbox.checked) {
    item.classList.add('selected');
  } else {
    item.classList.remove('selected');
  }
}

// Select all items
function selectAllItems(type) {
  const checkboxes = document.querySelectorAll(`input[data-type="${type}"]`);
  checkboxes.forEach((cb) => {
    cb.checked = true;
    const item = cb.closest('.default-list-item');
    if (item) item.classList.add('selected');
  });
}

// Deselect all items
function deselectAllItems(type) {
  const checkboxes = document.querySelectorAll(`input[data-type="${type}"]`);
  checkboxes.forEach((cb) => {
    cb.checked = false;
    const item = cb.closest('.default-list-item');
    if (item) item.classList.remove('selected');
  });
}

// Add new default item
function addDefaultItem(type) {
  const text = prompt(`Enter a new default ${type}:`);
  if (!text || !text.trim()) {
    return;
  }

  if (type === 'truth') {
    socket.emit('add_default_truth', {
      room: ROOM_CODE,
      text: text.trim(),
    });
  } else {
    socket.emit('add_default_dare', {
      room: ROOM_CODE,
      text: text.trim(),
    });
  }
}

// Edit selected default item
function editDefaultItem(type) {
  const checkboxes = document.querySelectorAll(
    `input[data-type="${type}"]:checked`,
  );

  if (checkboxes.length === 0) {
    alert('Please select one item to edit');
    return;
  }

  if (checkboxes.length > 1) {
    alert('Please select only one item to edit');
    return;
  }

  const oldText = checkboxes[0].dataset.text;
  const newText = prompt(`Edit ${type}:`, oldText);

  if (!newText || !newText.trim() || newText.trim() === oldText) {
    return;
  }

  if (type === 'truth') {
    socket.emit('edit_default_truth', {
      room: ROOM_CODE,
      old_text: oldText,
      new_text: newText.trim(),
    });
  } else {
    socket.emit('edit_default_dare', {
      room: ROOM_CODE,
      old_text: oldText,
      new_text: newText.trim(),
    });
  }
}

// Remove selected default items
function removeDefaultItems(type) {
  const checkboxes = document.querySelectorAll(
    `input[data-type="${type}"]:checked`,
  );

  if (checkboxes.length === 0) {
    alert('Please select at least one item to remove');
    return;
  }

  const count = checkboxes.length;
  if (
    !confirm(
      `Are you sure you want to remove ${count} ${type}${count > 1 ? 's' : ''}?`,
    )
  ) {
    return;
  }

  const textsToRemove = Array.from(checkboxes).map((cb) => cb.dataset.text);

  if (type === 'truth') {
    socket.emit('remove_default_truths', {
      room: ROOM_CODE,
      texts: textsToRemove,
    });
  } else {
    socket.emit('remove_default_dares', {
      room: ROOM_CODE,
      texts: textsToRemove,
    });
  }
}

// Save preset to file
function savePreset() {
  // Check if we have any data to save
  if (defaultTruths.length === 0 && defaultDares.length === 0) {
    alert('No truths or dares to save!');
    return;
  }

  // Create preset object with BOTH lists
  const preset = {
    truths: defaultTruths,
    dares: defaultDares,
  };

  // Convert to JSON
  const jsonString = JSON.stringify(preset, null, 2);

  // Create blob and download
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `truth_dare_preset_${new Date()
    .toISOString()
    .split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  alert(
    `Preset saved!\n${defaultTruths.length} truths and ${defaultDares.length} dares exported.`,
  );
}

// Trigger file input for loading preset
function triggerLoadPreset() {
  const fileInput = document.getElementById('load-preset-file');
  if (fileInput) fileInput.click();
}

// Load preset from file
function loadPresetFile(event) {
  const file = event.target.files[0];
  if (!file) {
    return;
  }

  // Check file type
  if (!file.name.endsWith('.json')) {
    alert('Please select a JSON file');
    event.target.value = ''; // Reset file input
    return;
  }

  // Confirm before loading (since it will replace current lists)
  if (
    !confirm(
      'Loading a preset will replace your current truths and dares lists. Continue?',
    )
  ) {
    event.target.value = '';
    return;
  }

  // Read file
  const reader = new FileReader();
  reader.onload = function (e) {
    try {
      const fileContent = e.target.result;

      // Basic validation
      JSON.parse(fileContent); // Will throw if invalid JSON

      // Send to server
      socket.emit('load_preset_file', {
        room: ROOM_CODE,
        file_data: fileContent,
      });
    } catch (error) {
      alert('Invalid JSON file: ' + error.message);
    }

    // Reset file input
    event.target.value = '';
  };

  reader.onerror = function () {
    alert('Error reading file');
    event.target.value = '';
  };

  reader.readAsText(file);
}

// Center game UI once game starts
function enterGameMode() {
  const left = document.getElementById('left-column');
  const gameAreaEl = document.getElementById('game-area');

  if (left) left.classList.add('hidden');
  if (gameAreaEl) gameAreaEl.classList.add('centered');
}
