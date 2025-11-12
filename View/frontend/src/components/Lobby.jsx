import React from 'react';
import PlayerList from './PlayerList';
import SharedButton from './SharedButton';

export default function Lobby({
  roomCode,
  players,
  isHost,
  onOpenSettings,
  onStartGame,
  onDestroyRoom,
  onLeaveRoom
}) {
  return (
    <section className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col gap-4">
      <div>
        <h2 className="text-sm font-semibold text-slate-200 mb-1">
          Players in Room
        </h2>
        <PlayerList players={players} />
        <div className="mt-1 text-[11px] text-slate-400">
          {players?.length || 0} player(s) in room
        </div>
      </div>

      <div className="mt-auto flex flex-col gap-2">
        <SharedButton variant="ghost" className="w-full" onClick={onLeaveRoom}>
          Leave Room
        </SharedButton>

        {isHost && (
          <div className="space-y-2">
            <div className="flex gap-2">
              <SharedButton
                variant="outline"
                className="flex-1"
                onClick={onOpenSettings}
              >
                Settings
              </SharedButton>
              <SharedButton
                variant="primary"
                className="flex-1"
                onClick={onStartGame}
              >
                Start Game
              </SharedButton>
            </div>
            <SharedButton
              variant="danger"
              className="w-full"
              onClick={onDestroyRoom}
            >
              Destroy Room
            </SharedButton>
          </div>
        )}

        <div className="text-[11px] text-slate-500 mt-1">
          Room code:{' '}
          <span className="font-mono tracking-widest text-primary-400">
            {roomCode}
          </span>
        </div>
      </div>
    </section>
  );
}
