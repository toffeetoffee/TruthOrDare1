import React from 'react';

export default function Minigame({
  playerName,
  minigame
}) {
  if (!minigame) {
    return (
      <div className="flex-1 flex items-center justify-center text-sm text-slate-400">
        Minigame starting...
      </div>
    );
  }

  const participants = minigame.participants || [];
  const voteCounts = minigame.vote_counts || {};
  const votes1 = voteCounts[participants[0]] || 0;
  const votes2 = voteCounts[participants[1]] || 0;

  const isParticipant = participants.includes(playerName);
  const totalVoters = minigame.total_voters || 0;
  const currentVotes = minigame.vote_count || 0;

  return (
    <div className="space-y-3">
      <div className="text-center">
        <div className="text-lg font-bold">
          {minigame.name || 'Minigame'}
        </div>
        <div className="text-xs text-slate-300 mt-1">
          {minigame.description_voter || 'Vote for the loser!'}
        </div>
      </div>

      <div className="flex items-center justify-center gap-4 mt-2">
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 flex flex-col items-center w-32">
          <div className="text-sm font-semibold">
            {participants[0] || 'Player 1'}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {votes1} vote{votes1 !== 1 ? 's' : ''}
          </div>
        </div>

        <div className="text-xs text-slate-500">VS</div>

        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 flex flex-col items-center w-32">
          <div className="text-sm font-semibold">
            {participants[1] || 'Player 2'}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {votes2} vote{votes2 !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {isParticipant ? (
        <div className="mt-3 text-center text-xs text-amber-300">
          {minigame.description_participant ||
            "You are competing in this minigame!"}
        </div>
      ) : (
        <div className="mt-4 flex flex-col items-center gap-2 text-xs">
          <div className="text-slate-200">
            {minigame.vote_instruction || 'Vote for the loser!'}
          </div>

          <div className="flex gap-3">
            <button
              className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs"
              onClick={() =>
                minigame.participants[0] &&
                minigame.onVote &&
                minigame.onVote(minigame.participants[0])
              }
            >
              {participants[0] || 'Player 1'} lose!
            </button>
            <button
              className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs"
              onClick={() =>
                minigame.participants[1] &&
                minigame.onVote &&
                minigame.onVote(minigame.participants[1])
              }
            >
              {participants[1] || 'Player 2'} lose!
            </button>
          </div>

          <div className="text-slate-400">
            Votes:{' '}
            <span className="font-mono text-primary-300">
              {currentVotes}
            </span>{' '}
            /{' '}
            <span className="font-mono">
              {totalVoters}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
