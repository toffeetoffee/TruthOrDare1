import React from 'react';

export default function SelectionPhase({
  gameState,
  playerName,
  remaining,
  onSelectTruthDare
}) {
  const selectedPlayer = gameState.selected_player;
  const selectedChoice = gameState.selected_choice;
  const isSelectedPlayer = selectedPlayer === playerName;

  return (
    <div className="space-y-3">
      <div className="text-center">
        <div className="text-xs text-slate-300 mb-1">Selected Player</div>
        <div className="text-2xl font-bold text-primary-400">
          {selectedPlayer || '???'}
        </div>
        <div className="mt-2 text-xs text-slate-400">
          Time remaining:{' '}
          <span className="font-mono text-primary-300">
            {Math.max(0, remaining || 0)}s
          </span>
        </div>
      </div>

      <div className="flex flex-col items-center gap-3 mt-2">
        {isSelectedPlayer && !selectedChoice && (
          <div className="flex gap-3">
            <button
              className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-semibold"
              onClick={() => onSelectTruthDare('truth')}
            >
              Truth
            </button>
            <button
              className="px-4 py-2 rounded-lg bg-rose-500 hover:bg-rose-600 text-white text-sm font-semibold"
              onClick={() => onSelectTruthDare('dare')}
            >
              Dare
            </button>
          </div>
        )}

        {!isSelectedPlayer && !selectedChoice && (
          <div className="text-xs text-slate-400">
            Waiting for{' '}
            <span className="font-semibold text-slate-200">
              {selectedPlayer || '...'}
            </span>{' '}
            to choose Truth or Dare...
          </div>
        )}

        {selectedChoice && (
          <div className="text-xs text-slate-300">
            Choice:{' '}
            <span className="font-semibold text-primary-300">
              {selectedChoice.toUpperCase()}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
