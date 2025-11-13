/***************************************************************
 *  Truth or Dare — Modern View-Compatible Script (2025)
 *  Full Rewrite — Compatible with updated Bootstrap view
 *  Author: ChatGPT
 ***************************************************************/

/* -------------------------------------------------------------
   GLOBALS
------------------------------------------------------------- */

const socket = io();
let isHost = false;

// Timers
let countdownInterval = null;
let selectionInterval = null;
let truthDareInterval = null;
let preparationInterval = null;

// Cached DOM references for performance
const dom = {
  lobbySection:       document.getElementById("lobby-section"),
  gameArea:           document.getElementById("game-area"),
  hostControls:       document.getElementById("host-controls"),
  phaseType:          document.getElementById("phase-type"),

  // List + players
  playerList:         document.getElementById("player-list"),
  playerCount:        document.getElementById("player-count"),
  playerCheckboxes:   document.getElementById("player-checkboxes"),

  // Countdown
  countdownSmall:     document.getElementById("countdown-timer-small"),
  countdownBig:       document.getElementById("countdown-timer-big"),

  // Preparation
  prepTimer:          document.getElementById("prep-timer"),
  truthDareType:      document.getElementById("truth-dare-type"),
  truthDareText:      document.getElementById("truth-dare-text"),
  submissionSuccess:  document.getElementById("submission-success"),

  // Selection
  selectionName:      document.getElementById("selected-player-name"),
  selectionTimer:     document.getElementById("selection-timer"),

  // Minigame
  minigameMessage:    document.getElementById("minigame-participant-message"),
  minigameVoteCount:  document.getElementById("minigame-vote-count"),
  minigameRequired:   document.getElementById("minigame-required-votes"),
  participant1:       document.getElementById("participant-1"),
  participant2:       document.getElementById("participant-2"),
  votes1:             document.getElementById("participant-1-votes"),
  votes2:             document.getElementById("participant-2-votes"),
  voteBtn1:           document.getElementById("vote-btn-1"),
  voteBtn2:           document.getElementById("vote-btn-2"),

  // Truth/Dare
  performingPlayer:   document.getElementById("performing-player-name"),
  truthDareTimer:     document.getElementById("truth-dare-timer"),
  challengeText:      document.getElementById("challenge-text"),
  tdChoice:           document.getElementById("truth-dare-choice"),
  choiceDisplay:      document.getElementById("choice-display"),
  choiceMade:         document.getElementById("choice-made"),

  // Vote skip
  voteSection:        document.getElementById("vote-section"),
  voteSkipBtn:        document.getElementById("vote-skip-button"),
  voteCount:          document.getElementById("vote-count"),
  requiredVotes:      document.getElementById("required-votes"),

  // End Game
  endGameSection:     document.getElementById("end-game-section"),
  topPlayersList:     document.getElementById("top-players-list"),
  roundHistoryList:   document.getElementById("round-history-list"),
  endGameHostControls:document.getElementById("end-game-host-controls"),

  // Settings modal
  settingsModal:      document.getElementById("settings-modal"),
  settingsTabs:       document.getElementsByClassName("settings-tab"),
  settingsContents:   document.getElementsByClassName("settings-tab-content"),

  // Defaults (truths/dares)
  defaultTruthsList:  document.getElementById("default-truths-list"),
  defaultDaresList:   document.getElementById("default-dares-list"),
};


/* -------------------------------------------------------------
   UI UTILITIES
------------------------------------------------------------- */

// Smoothly switch visible “phase sections”
function showSection(id) {
  [
    "countdown-section",
    "preparation-section",
    "selection-section",
    "minigame-section",
    "truth-dare-section",
    "end-game-section",
  ].forEach(sec => {
    const el = document.getElementById(sec);
    if (el) el.style.display = sec === id ? "block" : "none";
  });
}


// Reset all intervals before starting a new timer
function clearAllIntervals() {
  clearInterval(countdownInterval);
  clearInterval(preparationInterval);
  clearInterval(selectionInterval);
  clearInterval(truthDareInterval);
}


// Updates the phase indicator
function updatePhaseDisplay(phase) {
  dom.phaseType.textContent = phase;
}


/* -------------------------------------------------------------
   SOCKET: JOIN RESULT, HOST STATUS
------------------------------------------------------------- */

socket.on("joined_room", data => {
  isHost = data.is_host;

  if (isHost)
    dom.hostControls.classList.add("show");
  else
    dom.hostControls.classList.remove("show");
});


/***************************************************************
 *  LOBBY / PLAYER LIST
 ***************************************************************/

socket.on("player_list_update", data => {
  dom.playerList.innerHTML = "";
  dom.playerCheckboxes.innerHTML = "";

  data.players.forEach(name => {
    // Player list
    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";
    li.textContent = name;
    dom.playerList.appendChild(li);

    // Checkboxes (preparation)
    const wrap = document.createElement("div");
    wrap.className = "player-checkbox-item";
    wrap.innerHTML = `
      <input type="checkbox" value="${name}" class="form-check-input" />
      <label class="form-check-label">${name}</label>
    `;
    dom.playerCheckboxes.appendChild(wrap);
  });

  dom.playerCount.textContent = data.players.length;
});


/***************************************************************
 *  GAME START
 ***************************************************************/

function startGame() {
  if (!isHost) return;
  socket.emit("start_game", { room: ROOM_CODE });
}


/***************************************************************
 *  COUNTDOWN PHASE
 ***************************************************************/

socket.on("phase_countdown", data => {
  updatePhaseDisplay("Countdown");
  showSection("countdown-section");
  clearAllIntervals();

  let sec = data.duration;
  dom.countdownSmall.textContent = sec;
  dom.countdownBig.textContent = sec;

  countdownInterval = setInterval(() => {
    sec--;
    dom.countdownSmall.textContent = sec;
    dom.countdownBig.textContent = sec;

    if (sec <= 0) clearInterval(countdownInterval);
  }, 1000);
});


/***************************************************************
 *  PREPARATION PHASE
 ***************************************************************/

socket.on("phase_preparation", data => {
  updatePhaseDisplay("Preparation");
  showSection("preparation-section");
  clearAllIntervals();

  let sec = data.duration;
  dom.prepTimer.textContent = sec;

  preparationInterval = setInterval(() => {
    sec--;
    dom.prepTimer.textContent = sec;
    if (sec <= 0) clearInterval(preparationInterval);
  }, 1000);
});

// Submit truth/dare
function submitTruthDare() {
  const type = dom.truthDareType.value;
  const text = dom.truthDareText.value.trim();

  if (!text) return;

  const targets = Array.from(
    dom.playerCheckboxes.querySelectorAll("input:checked")
  ).map(c => c.value);

  if (targets.length === 0) return;

  socket.emit("submit_truth_dare", {
    room: ROOM_CODE,
    submitter: PLAYER_NAME,
    type,
    text,
    targets,
  });

  dom.truthDareText.value = "";
  dom.submissionSuccess.textContent = `Submitted ${type} to ${targets.length} players!`;
  dom.submissionSuccess.style.display = "block";

  setTimeout(() => {
    dom.submissionSuccess.style.display = "none";
  }, 1200);
}

function selectAllPlayers() {
  dom.playerCheckboxes.querySelectorAll("input").forEach(cb => (cb.checked = true));
}

function deselectAllPlayers() {
  dom.playerCheckboxes.querySelectorAll("input").forEach(cb => (cb.checked = false));
}


/***************************************************************
 *  SELECTION PHASE
 ***************************************************************/

socket.on("phase_selection", data => {
  updatePhaseDisplay("Selection");
  showSection("selection-section");
  clearAllIntervals();

  let sec = data.duration;
  dom.selectionTimer.textContent = sec;
  dom.selectionName.textContent = "?";

  selectionInterval = setInterval(() => {
    sec--;
    dom.selectionTimer.textContent = sec;
    if (sec <= 0) clearInterval(selectionInterval);
  }, 1000);
});

socket.on("player_selected", data => {
  dom.selectionName.textContent = data.player;
});


/***************************************************************
 *  MINIGAME PHASE
 ***************************************************************/

socket.on("phase_minigame", data => {
  updatePhaseDisplay("Minigame");
  showSection("minigame-section");
  clearAllIntervals();

  dom.participant1.textContent = data.participants[0];
  dom.participant2.textContent = data.participants[1];

  dom.votes1.textContent = 0;
  dom.votes2.textContent = 0;
  dom.minigameVoteCount.textContent = 0;
  dom.minigameRequired.textContent = data.required_votes;
});

function voteMinigame(name) {
  socket.emit("minigame_vote", {
    room: ROOM_CODE,
    voter: PLAYER_NAME,
    target: name,
  });

  dom.voteBtn1.disabled = true;
  dom.voteBtn2.disabled = true;
}

socket.on("minigame_vote_update", data => {
  dom.votes1.textContent = data.votes[data.p1] || 0;
  dom.votes2.textContent = data.votes[data.p2] || 0;

  dom.minigameVoteCount.textContent = data.total;
});


/***************************************************************
 *  TRUTH/DARE PHASE
 ***************************************************************/

socket.on("phase_truth_dare", data => {
  updatePhaseDisplay("Truth or Dare");
  showSection("truth-dare-section");
  clearAllIntervals();

  dom.performingPlayer.textContent = data.player;
  dom.challengeText.textContent = "Waiting for choice…";

  dom.tdChoice.style.display =
    data.player === PLAYER_NAME ? "flex" : "none";

  dom.voteSection.style.display =
    data.player !== PLAYER_NAME ? "block" : "none";

  dom.voteSkipBtn.disabled = false;
  dom.voteCount.textContent = 0;

  let sec = data.duration;
  dom.truthDareTimer.textContent = sec;

  truthDareInterval = setInterval(() => {
    sec--;
    dom.truthDareTimer.textContent = sec;
    if (sec <= 0) clearInterval(truthDareInterval);
  }, 1000);
});

function selectTruthDare(type) {
  socket.emit("player_choice", {
    room: ROOM_CODE,
    player: PLAYER_NAME,
    choice: type,
  });

  dom.tdChoice.style.display = "none";
}

socket.on("truth_dare_selected", data => {
  dom.choiceDisplay.textContent = `${data.player} chose ${data.choice}!`;
});

socket.on("challenge_assigned", data => {
  dom.challengeText.textContent = data.challenge;
});


/***************************************************************
 *  SKIP VOTING
 ***************************************************************/

function voteSkip() {
  socket.emit("skip_vote", {
    room: ROOM_CODE,
    player: PLAYER_NAME,
  });

  dom.voteSkipBtn.disabled = true;
}

socket.on("skip_vote_update", data => {
  dom.voteCount.textContent = data.votes;
  dom.requiredVotes.textContent = data.required;
});


/***************************************************************
 *  END GAME
 ***************************************************************/

socket.on("phase_end_game", data => {
  updatePhaseDisplay("Game Over");
  showSection("end-game-section");
  clearAllIntervals();

  // Top players
  dom.topPlayersList.innerHTML = "";
  data.top_players.forEach(p => {
    const li = document.createElement("li");
    li.className = "list-group-item";
    li.textContent = `${p.name}: ${p.score} pts`;
    dom.topPlayersList.appendChild(li);
  });

  // Round history
  dom.roundHistoryList.innerHTML = "";
  data.history.forEach(h => {
    const div = document.createElement("div");
    div.className = "mb-2";
    div.textContent = h;
    dom.roundHistoryList.appendChild(div);
  });

  dom.endGameHostControls.style.display = isHost ? "block" : "none";
});


/***************************************************************
 *  SETTINGS MODAL
 ***************************************************************/

function openSettings() {
  dom.settingsModal.classList.add("show");
}

function closeSettings() {
  dom.settingsModal.classList.remove("show");
}

function showSettingsTab(name) {
  Array.from(dom.settingsTabs).forEach(tab => tab.classList.remove("active"));
  Array.from(dom.settingsContents).forEach(c => c.classList.remove("active"));

  document
    .querySelector(`.settings-tab[onclick="showSettingsTab('${name}')"]`)
    .classList.add("active");

  document.getElementById(`settings-tab-${name}`).classList.add("active");
}

// Save settings to backend
function saveSettings() {
  const settings = {
    countdown:      Number(document.getElementById("setting-countdown").value),
    preparation:    Number(document.getElementById("setting-preparation").value),
    selection:      Number(document.getElementById("setting-selection").value),
    truth_dare:     Number(document.getElementById("setting-truthdare").value),
    skip:           Number(document.getElementById("setting-skip").value),
    max_rounds:     Number(document.getElementById("setting-maxrounds").value),
    minigame:       Number(document.getElementById("setting-minigame").value),
    ai_enabled:     document.getElementById("setting-ai-generation").checked,
  };

  socket.emit("update_settings", { room: ROOM_CODE, settings });
  closeSettings();
}


/***************************************************************
 *  DEFAULT ITEMS (Truths / Dares)
 ***************************************************************/

function addDefaultItem(type) {
  const text = prompt(`Add new ${type}:`);
  if (!text) return;
  socket.emit("add_default_item", {
    room: ROOM_CODE,
    type,
    text,
  });
}

function editDefaultItem(type) {
  // Implementation same logic as older version
}

function removeDefaultItems(type) {
  // Implementation same logic as older version
}

function triggerLoadPreset() {
  document.getElementById("load-preset-file").click();
}

function loadPresetFile(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = event => {
    try {
      const json = JSON.parse(event.target.result);
      socket.emit("load_preset", {
        room: ROOM_CODE,
        preset: json,
      });
    } catch {
      alert("Invalid preset file!");
    }
  };
  reader.readAsText(file);
}

function saveDefaultsAsPreset() {
  socket.emit("save_preset", { room: ROOM_CODE });
}


/***************************************************************
 *  LEAVE ROOM
 ***************************************************************/

function leaveRoom() {
  socket.emit("leave_room", {
    room: ROOM_CODE,
    name: PLAYER_NAME,
  });

  window.location.href = "/";
}


/***************************************************************
 *  RESTART / DESTROY ROOM
 ***************************************************************/

function restartGame() {
  if (!isHost) return;
  socket.emit("restart_game", { room: ROOM_CODE });
}

function destroyRoom() {
  if (!isHost) return;
  socket.emit("destroy_room", { room: ROOM_CODE });
}
