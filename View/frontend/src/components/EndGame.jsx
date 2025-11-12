import React from 'react';
import SharedButton from './SharedButton';

export default function EndGame({
  gameState,
  isHost,
  onRestartGame,
  onLeaveRoom
}) {
  const topPlayers = gameState.top_players || [];
  const history = gameState.round_history || [];

  const reversedHistory = [...history].reverse();

  return (
    <div className="space-y-4">
      <div className="text-center">
        <div className="text-2xl font-bold text-primary-400">🎉 Game Over! 🎉</div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Scoreboard */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
          <div className="text-sm font-semibold mb-2">Top Players</div>
          {topPlayers.length === 0 ? (
            <div className="text-xs text-slate-500 text-center py-4">
              No players
            </div>
          ) : (
            <div className="space-y-1 text-xs">
              {topPlayers.map((p, index) => {
                const rank = index + 1;
                const medal =
                  rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : '';
                return (
                  <div
                    key={p.name + index}
                    className="flex justify-between items-center bg-slate-900/80 rounded-md px-2 py-1"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{medal}</span>
                      <span>{p.name}</span>
                    </div>
                    <div className="font-mono text-primary-300">
                      {p.score} pts
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Round history */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 max-h-64 overflow-auto">
          <div className="text-sm font-semibold mb-2">Round History</div>
          {reversedHistory.length === 0 ? (
            <div className="text-xs text-slate-500 text-center py-4">
              No rounds played
            </div>
          ) : (
            <div className="space-y-2 text-xs">
              {reversedHistory.map((round) => {
                const td = round.truth_dare || {};
                const submitterText = round.submitted_by
                  ? `Submitted by: ${round.submitted_by}`
                  : 'Default challenge';
                return (
                  <div
                    key={round.round_number + td.text}
                    className="border border-slate-800 rounded-md px-2 py-1.5 bg-slate-900/80"
                  >
                    <div className="text-[11px] text-slate-400 mb-1">
                      Round {round.round_number}
                    </div>
                    <div>
                      <span className="font-semibold">{round.selected_player}</span>{' '}
                      performed a <span className="font-semibold">{td.type}</span>
                    </div>
                    <div className="mt-1 text-slate-200">
                      &quot;{td.text}&quot;
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      {submitterText}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-between items-center mt-2">
        <div className="flex gap-2">
          {isHost && (
            <>
              <SharedButton variant="outline" onClick={onRestartGame}>
                Restart Game
              </SharedButton>
            </>
          )}
        </div>
        <SharedButton variant="ghost" onClick={onLeaveRoom}>
          Leave Room
        </SharedButton>
      </div>
    </div>
  );
}
