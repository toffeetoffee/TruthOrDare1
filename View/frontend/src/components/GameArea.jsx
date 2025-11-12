import React from 'react';
import Countdown from './Countdown';
import PreparationPhase from './PreparationPhase';
import SelectionPhase from './SelectionPhase';
import Minigame from './Minigame';
import TruthDarePhase from './TruthDarePhase';
import EndGame from './EndGame';
import SharedButton from './SharedButton';

export default function GameArea({
  playerName,
  players,
  isHost,
  gameState,
  timerSeconds,
  submissionSuccess,
  onRestartGame,
  onLeaveRoom,
  onSubmitTruthDare,
  onSelectTruthDare,
  onVoteSkip,
  onMinigameVote
}) {
  const phase = gameState?.phase || 'lobby';

  return (
    <section className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col gap-4">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-sm font-semibold text-slate-200">Game</h2>
        <div className="flex gap-2">
          <SharedButton variant="ghost" onClick={onLeaveRoom}>
            Leave Room
          </SharedButton>
        </div>
      </div>

      {phase === 'lobby' && (
        <div className="flex-1 flex items-center justify-center text-sm text-slate-400">
          Waiting for host to start the game...
        </div>
      )}

      {phase === 'countdown' && (
        <Countdown remaining={timerSeconds} />
      )}

      {phase === 'preparation' && (
        <PreparationPhase
          playerName={playerName}
          players={players}
          remaining={timerSeconds}
          submissionSuccess={submissionSuccess}
          onSubmit={onSubmitTruthDare}
        />
      )}

      {phase === 'selection' && (
        <SelectionPhase
          gameState={gameState}
          playerName={playerName}
          remaining={timerSeconds}
          onSelectTruthDare={onSelectTruthDare}
        />
      )}

      {phase === 'minigame' && (
        <Minigame
          playerName={playerName}
          minigame={gameState.minigame}
          onVote={onMinigameVote}
        />
      )}

      {phase === 'truth_dare' && (
        <TruthDarePhase
          gameState={gameState}
          playerName={playerName}
          players={players}
          remaining={timerSeconds}
          onVoteSkip={onVoteSkip}
        />
      )}

      {phase === 'end_game' && (
        <EndGame
          gameState={gameState}
          isHost={isHost}
          onRestartGame={onRestartGame}
          onLeaveRoom={onLeaveRoom}
        />
      )}
    </section>
  );
}
