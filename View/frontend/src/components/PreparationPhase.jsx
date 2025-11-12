import React, { useMemo, useState } from 'react';

export default function PreparationPhase({
  playerName,
  players,
  remaining,
  submissionSuccess,
  onSubmit
}) {
  const [text, setText] = useState('');
  const [type, setType] = useState('truth');
  const [selectedTargets, setSelectedTargets] = useState([]);

  const otherPlayers = useMemo(
    () => (players || []).filter((name) => name !== playerName),
    [players, playerName]
  );

  const toggleTarget = (name) => {
    setSelectedTargets((prev) =>
      prev.includes(name)
        ? prev.filter((n) => n !== name)
        : [...prev, name]
    );
  };

  const handleSelectAll = () => {
    setSelectedTargets(otherPlayers);
  };

  const handleDeselectAll = () => {
    setSelectedTargets([]);
  };

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed) {
      alert('Please enter a truth or dare!');
      return;
    }
    if (selectedTargets.length === 0) {
      alert('Please select at least one player!');
      return;
    }
    onSubmit({
      text: trimmed,
      type,
      targets: selectedTargets
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center text-xs text-slate-300">
        <div>Preparation Phase</div>
        <div>
          Time:{' '}
          <span className="font-mono text-primary-400">
            {Math.max(0, remaining || 0)}s
          </span>
        </div>
      </div>

      <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 grid md:grid-cols-[minmax(0,1.5fr),minmax(0,1fr)] gap-3">
        <div className="space-y-2">
          <textarea
            className="w-full h-24 bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-xs resize-none"
            placeholder="Enter a truth question or dare challenge..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <select
            className="w-32 bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-xs"
            value={type}
            onChange={(e) => setType(e.target.value)}
          >
            <option value="truth">Truth</option>
            <option value="dare">Dare</option>
          </select>

          {submissionSuccess && (
            <div className="mt-1 text-[11px] text-emerald-300">
              ✓ Added {submissionSuccess.type}: &quot;{submissionSuccess.text}&quot; to{' '}
              {submissionSuccess.targets.join(', ')}
            </div>
          )}
        </div>

        <div className="space-y-2 text-xs">
          <div className="font-semibold text-slate-200">Add to players:</div>
          <div className="max-h-28 overflow-auto bg-slate-900 border border-slate-700 rounded-md p-2 space-y-1">
            {otherPlayers.length === 0 ? (
              <div className="text-slate-500 text-center">
                No other players yet
              </div>
            ) : (
              otherPlayers.map((name) => {
                const checked = selectedTargets.includes(name);
                return (
                  <button
                    key={name}
                    type="button"
                    className={`w-full flex items-center gap-2 px-2 py-1 rounded-md text-left ${
                      checked ? 'bg-primary-500/20' : 'hover:bg-slate-800'
                    }`}
                    onClick={() => toggleTarget(name)}
                  >
                    <input
                      type="checkbox"
                      readOnly
                      checked={checked}
                    />
                    <span>{name}</span>
                  </button>
                );
              })
            )}
          </div>

          <div className="flex justify-between mt-1">
            <button
              className="text-[11px] text-slate-300 hover:text-primary-300"
              onClick={handleSelectAll}
            >
              Select All
            </button>
            <button
              className="text-[11px] text-slate-300 hover:text-primary-300"
              onClick={handleDeselectAll}
            >
              Deselect All
            </button>
          </div>

          <button
            className="mt-2 w-full bg-primary-500 hover:bg-primary-600 rounded-md py-1 text-xs font-semibold"
            onClick={handleSubmit}
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}
