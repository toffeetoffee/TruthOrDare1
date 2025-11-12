import React from 'react';

export default function Countdown({ remaining }) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center">
        <div className="text-sm text-slate-300 mb-1">Game Starting In</div>
        <div className="text-5xl font-extrabold text-primary-500">
          {Math.max(0, remaining || 0)}
        </div>
      </div>
    </div>
  );
}
