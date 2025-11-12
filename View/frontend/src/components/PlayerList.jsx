import React from 'react';

export default function PlayerList({ players, isHost }) {
  if (!players || players.length === 0) {
    return (
      <ul className="text-sm text-slate-400 italic">
        <li>Waiting for players...</li>
      </ul>
    );
  }

  return (
    <ul className="space-y-1 text-sm">
      {players.map((name, index) => {
        const isFirst = index === 0;
        return (
          <li
            key={name + index}
            className={`flex items-center justify-between rounded-md px-2 py-1 ${
              isFirst ? 'bg-slate-800/80 border border-primary-500/60' : 'bg-slate-800/60'
            }`}
          >
            <span>{name}</span>
            {isFirst && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                Host
              </span>
            )}
          </li>
        );
      })}
    </ul>
  );
}
