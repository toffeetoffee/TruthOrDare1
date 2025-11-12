import React, { useEffect, useState } from 'react';
import useSocket from './hooks/useSocket';
import Lobby from './components/Lobby';
import SettingsModal from './components/SettingsModal';
import GameArea from './components/GameArea';

const defaultGameState = {
  phase: 'lobby',
  remaining_time: 0
};

const defaultSettings = {
  countdown_duration: 10,
  preparation_duration: 30,
  selection_duration: 10,
  truth_dare_duration: 60,
  skip_duration: 5,
  max_rounds: 10,
  minigame_chance: 20,
  ai_generation_enabled: true
};

export default function App() {
  const [playerName, setPlayerName] = useState('');
  const [roomCode, setRoomCode] = useState('');
  const [joined, setJoined] = useState(false);
  const [darkMode, setDarkMode] = useState(true);

  const { socket, isConnected, mySid } = useSocket(roomCode, playerName, joined);

  const [playerList, setPlayerList] = useState([]);
  const [hostSid, setHostSid] = useState(null);
  const [settings, setSettings] = useState(defaultSettings);
  const [defaultTruths, setDefaultTruths] = useState([]);
  const [defaultDares, setDefaultDares] = useState([]);
  const [gameState, setGameState] = useState(defaultGameState);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [submissionSuccess, setSubmissionSuccess] = useState(null);

  // Dark mode toggle
  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) root.classList.add('dark');
    else root.classList.remove('dark');
  }, [darkMode]);

  // Attach socket listeners
  useEffect(() => {
    if (!socket) return;

    // Ask for current settings & default lists
    socket.emit('get_settings', { room: roomCode });
    socket.emit('get_default_lists', { room: roomCode });

    const onSettingsUpdated = (data) => {
      if (data.settings) setSettings((prev) => ({ ...prev, ...data.settings }));
    };

    const onDefaultListsUpdated = (data) => {
      if (data.truths !== undefined) setDefaultTruths(data.truths);
      if (data.dares !== undefined) setDefaultDares(data.dares);
    };

    const onPlayerList = (data) => {
      setPlayerList(data.players || []);
      setHostSid(data.host_sid || null);
    };

    const onGameStateUpdate = (data) => {
      setGameState(data);
      setTimerSeconds(data.remaining_time || 0);
    };

    const onSubmissionSuccess = (data) => {
      setSubmissionSuccess(data);
      setTimeout(() => setSubmissionSuccess(null), 3000);
    };

    const onSubmissionError = (data) => {
      alert(data.message || 'Submission error');
    };

    const onRoomDestroyed = () => {
      alert('The host has closed the room.');
      window.location.href = '/';
    };

    const onLeftRoom = () => {
      window.location.href = '/';
    };

    const onPresetLoaded = (data) => alert(data.message);
    const onPresetError = (data) => alert('Error: ' + data.message);

    socket.on('settings_updated', onSettingsUpdated);
    socket.on('default_lists_updated', onDefaultListsUpdated);
    socket.on('player_list', onPlayerList);
    socket.on('game_state_update', onGameStateUpdate);
    socket.on('submission_success', onSubmissionSuccess);
    socket.on('submission_error', onSubmissionError);
    socket.on('room_destroyed', onRoomDestroyed);
    socket.on('left_room', onLeftRoom);
    socket.on('preset_loaded', onPresetLoaded);
    socket.on('preset_error', onPresetError);

    return () => {
      socket.off('settings_updated', onSettingsUpdated);
      socket.off('default_lists_updated', onDefaultListsUpdated);
      socket.off('player_list', onPlayerList);
      socket.off('game_state_update', onGameStateUpdate);
      socket.off('submission_success', onSubmissionSuccess);
      socket.off('submission_error', onSubmissionError);
      socket.off('room_destroyed', onRoomDestroyed);
      socket.off('left_room', onLeftRoom);
      socket.off('preset_loaded', onPresetLoaded);
      socket.off('preset_error', onPresetError);
    };
  }, [socket, roomCode]);

  // Timer countdown locally
  useEffect(() => {
    if (!gameState || !gameState.phase) return;
    const activePhases = ['countdown', 'preparation', 'selection', 'truth_dare'];
    if (!activePhases.includes(gameState.phase)) return;

    if (timerSeconds <= 0) return;

    const id = setInterval(() => {
      setTimerSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(id);
  }, [gameState.phase, timerSeconds]);

  const isHost = mySid && hostSid && mySid === hostSid;

  // Join form submit
  const handleJoinSubmit = (e) => {
    e.preventDefault();
    if (!playerName.trim() || !roomCode.trim()) return;
    setJoined(true);
  };

  // Socket emit helpers
  const emitSafe = (event, payload) => {
    if (!socket) return;
    socket.emit(event, payload);
  };

  const handleLeaveRoom = () => {
    if (!socket) return;
    if (confirm('Are you sure you want to leave the room?')) {
      emitSafe('leave', { room: roomCode });
    }
  };

  const handleDestroyRoom = () => {
    if (!socket) return;
    if (confirm('Are you sure you want to destroy the room? All players will be kicked.')) {
      emitSafe('destroy_room', { room: roomCode });
    }
  };

  const handleStartGame = () => {
    emitSafe('start_game', { room: roomCode });
  };

  const handleRestartGame = () => {
    if (confirm('Are you sure you want to restart the game? All scores will be reset.')) {
      emitSafe('restart_game', { room: roomCode });
    }
  };

  const handleSaveSettings = (newSettings) => {
    emitSafe('update_settings', { room: roomCode, settings: newSettings });
    setSettingsOpen(false);
  };

  const handleMinigameVote = (playerNameToVote) => {
    emitSafe('minigame_vote', { room: roomCode, voted_player: playerNameToVote });
  };

  const handleSelectTruthDare = (choice) => {
    emitSafe('select_truth_dare', { room: roomCode, choice });
  };

  const handleVoteSkip = () => {
    emitSafe('vote_skip', { room: roomCode });
  };

  const handleSubmitTruthDare = ({ text, type, targets }) => {
    emitSafe('submit_truth_dare', {
      room: roomCode,
      text,
      type,
      targets
    });
  };

  // Default list management (truths/dares)
  const handleAddDefaultItem = (type, text) => {
    if (type === 'truth') {
      emitSafe('add_default_truth', { room: roomCode, text });
    } else {
      emitSafe('add_default_dare', { room: roomCode, text });
    }
  };

  const handleEditDefaultItem = (type, oldText, newText) => {
    if (type === 'truth') {
      emitSafe('edit_default_truth', { room: roomCode, old_text: oldText, new_text: newText });
    } else {
      emitSafe('edit_default_dare', { room: roomCode, old_text: oldText, new_text: newText });
    }
  };

  const handleRemoveDefaultItems = (type, texts) => {
    if (type === 'truth') {
      emitSafe('remove_default_truths', { room: roomCode, texts });
    } else {
      emitSafe('remove_default_dares', { room: roomCode, texts });
    }
  };

  const handleLoadPresetFile = (fileContent) => {
    emitSafe('load_preset_file', { room: roomCode, file_data: fileContent });
  };

  // Save preset locally as file (no socket)
  const handleSavePresetFile = () => {
    if (defaultTruths.length === 0 && defaultDares.length === 0) {
      alert('No truths or dares to save!');
      return;
    }
    const preset = {
      truths: defaultTruths,
      dares: defaultDares
    };
    const jsonString = JSON.stringify(preset, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const today = new Date().toISOString().split('T')[0];
    a.href = url;
    a.download = `truth_dare_preset_${today}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    alert(`Preset saved!\n${defaultTruths.length} truths and ${defaultDares.length} dares exported.`);
  };

  // If user hasn't joined yet, show join screen
  if (!joined) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="w-full max-w-md bg-slate-900/90 border border-slate-700 rounded-2xl p-6 shadow-2xl space-y-6">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-primary-500">Dare or Dare</h1>
            <button
              onClick={() => setDarkMode((d) => !d)}
              className="text-xs px-2 py-1 rounded-full bg-slate-800 border border-slate-600 hover:border-primary-500 transition"
            >
              {darkMode ? '🌙 Dark' : '☀️ Light'}
            </button>
          </div>
          <p className="text-sm text-slate-300">
            Enter your name and a room code. If the room doesn&apos;t exist yet, it will be created and you&apos;ll be the host.
          </p>
          <form className="space-y-4" onSubmit={handleJoinSubmit}>
            <div>
              <label className="block text-sm mb-1">Your Name</label>
              <input
                className="w-full rounded-lg bg-slate-800 border border-slate-600 px-3 py-2 text-sm focus:border-primary-500"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm mb-1">Room Code</label>
              <input
                className="w-full rounded-lg bg-slate-800 border border-slate-600 px-3 py-2 text-sm uppercase tracking-widest focus:border-primary-500"
                value={roomCode}
                onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-primary-500 hover:bg-primary-600 text-white font-semibold py-2 rounded-lg mt-2 transition"
            >
              Join Room
            </button>
          </form>
          <div className="text-xs text-slate-400 text-right">
            Backend: Socket.IO {isConnected ? '🔌 ready after join' : '⏳ waiting'}
          </div>
        </div>
      </div>
    );
  }

  // In-room UI
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-4 py-2">
          <div>
            <div className="text-lg font-bold text-primary-500">Dare or Dare</div>
            <div className="text-xs text-slate-300">
              Room <span className="font-mono tracking-widest text-primary-400">{roomCode}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-xs text-slate-300">
              You are <span className="font-semibold">{playerName}</span>{' '}
              {isHost && <span className="ml-1 text-emerald-400">(Host)</span>}
            </div>
            <button
              onClick={() => setDarkMode((d) => !d)}
              className="text-xs px-2 py-1 rounded-full bg-slate-800 border border-slate-600 hover:border-primary-500 transition"
            >
              {darkMode ? '🌙' : '☀️'}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-4 grid gap-4 md:grid-cols-[minmax(0,260px),minmax(0,1fr)]">
        <Lobby
          roomCode={roomCode}
          players={playerList}
          isHost={isHost}
          onOpenSettings={() => setSettingsOpen(true)}
          onStartGame={handleStartGame}
          onDestroyRoom={handleDestroyRoom}
          onLeaveRoom={handleLeaveRoom}
        />

        <GameArea
          playerName={playerName}
          players={playerList}
          isHost={isHost}
          gameState={gameState}
          timerSeconds={timerSeconds}
          submissionSuccess={submissionSuccess}
          onRestartGame={handleRestartGame}
          onLeaveRoom={handleLeaveRoom}
          onSubmitTruthDare={handleSubmitTruthDare}
          onSelectTruthDare={handleSelectTruthDare}
          onVoteSkip={handleVoteSkip}
          onMinigameVote={handleMinigameVote}
        />
      </main>

      {settingsOpen && (
        <SettingsModal
          isHost={isHost}
          settings={settings}
          defaultTruths={defaultTruths}
          defaultDares={defaultDares}
          onClose={() => setSettingsOpen(false)}
          onSaveSettings={handleSaveSettings}
          onAddItem={handleAddDefaultItem}
          onEditItem={handleEditDefaultItem}
          onRemoveItems={handleRemoveDefaultItems}
          onSavePreset={handleSavePresetFile}
          onLoadPresetFile={handleLoadPresetFile}
        />
      )}
    </div>
  );
}
