import React from 'react';

export default function TruthDarePhase({
  gameState,
  playerName,
  players,
  remaining,
  onVoteSkip
}) {
  const isSelectedPlayer = gameState.selected_player === playerName;
  const skipActivated = gameState.skip_activated;
  const listEmpty = gameState.list_empty;
  const current = gameState.current_truth_dare;
  const selectedChoice = gameState.selected_choice || '';

  const totalPlayers = players?.length || 0;
  const otherPlayersCount = Math.max(totalPlayers - 1, 0);
  const requiredVotes = Math.ceil(otherPlayersCount / 2);
  const voteCount = gameState.skip_vote_count || 0;

  const getSkipButtonLabel = () => {
    if (listEmpty) {
      return '⚠️ List Empty - Skip Auto-Activated!';
    }
    if (skipActivated) {
      return 'Skip Activated!';
    }
    return 'Vote to Skip';
  };

  const disabled = listEmpty || skipActivated;

  return (
    <div className="space-y-3">
      {listEmpty && (
        <div className="flex gap-2 items-center bg-amber-900/40 border border-amber-700/60 rounded-lg px-3 py-2 text-xs text-amber-100">
          <span>⚠️</span>
          <div>
            <div className="font-semibold">List Empty!</div>
            <div className="text-[11px]">
              The selected player has run out of available challenges. Skip has been automatically activated.
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center">
        <div className="flex items-baseline gap-2">
          <div className="text-xs uppercase tracking-wide text-slate-400">
            {selectedChoice || 'Truth/Dare'}
          </div>
          <div className="text-sm text-slate-300">
            <span className="font-semibold text-primary-300">
              {gameState.selected_player || 'Someone'}
            </span>{' '}
            is performing
          </div>
        </div>

        <div className="text-xs text-slate-300">
          Time:{' '}
          <span className="font-mono text-primary-300">
            {Math.max(0, remaining || 0)}s
          </span>
        </div>
      </div>

      <div
        className={`rounded-xl px-3 py-2 text-sm ${
          listEmpty
            ? 'bg-amber-50 text-amber-900 border border-amber-400'
            : 'bg-slate-950/60 border border-slate-800 text-slate-100'
        }`}
      >
        {current?.text || 'Waiting for challenge...'}
      </div>

      {!isSelectedPlayer && (
        <div className="mt-3 flex items-center justify-between text-xs">
          <button
            className={`px-3 py-1 rounded-lg text-xs font-semibold ${
              disabled
                ? 'bg-slate-600 text-slate-200 cursor-not-allowed'
                : 'bg-slate-700 hover:bg-slate-600 text-white'
            }`}
            disabled={disabled}
            onClick={onVoteSkip}
          >
            {getSkipButtonLabel()}
          </button>
          <div className="text-slate-400">
            <span className="font-mono text-primary-300">{voteCount}</span> /{' '}
            <span className="font-mono">{requiredVotes}</span> votes to skip
          </div>
        </div>
      )}

      {isSelectedPlayer && (
        <div className="mt-2 text-xs text-slate-400">
          Other players can vote to skip your challenge.
        </div>
      )}
    </div>
  );
}
