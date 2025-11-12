import React, { useRef, useState } from 'react';
import SharedButton from './SharedButton';

function DefaultListEditor({
  type,
  items,
  onAdd,
  onEdit,
  onRemove
}) {
  const [selected, setSelected] = useState([]);

  const toggleSelected = (text) => {
    setSelected((prev) =>
      prev.includes(text)
        ? prev.filter((t) => t !== text)
        : [...prev, text]
    );
  };

  const handleAdd = () => {
    const text = window.prompt(`Enter a new default ${type}:`);
    if (!text || !text.trim()) return;
    onAdd(type, text.trim());
  };

  const handleEdit = () => {
    if (selected.length === 0) {
      alert('Please select one item to edit');
      return;
    }
    if (selected.length > 1) {
      alert('Please select only one item to edit');
      return;
    }
    const oldText = selected[0];
    const newText = window.prompt(`Edit ${type}:`, oldText);
    if (!newText || !newText.trim() || newText.trim() === oldText) return;
    onEdit(type, oldText, newText.trim());
  };

  const handleRemove = () => {
    if (selected.length === 0) {
      alert('Please select at least one item to remove');
      return;
    }
    const count = selected.length;
    if (!window.confirm(`Remove ${count} ${type}${count > 1 ? 's' : ''}?`)) {
      return;
    }
    onRemove(type, selected);
  };

  const handleSelectAll = () => {
    setSelected(items);
  };

  const handleDeselectAll = () => {
    setSelected([]);
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2 text-xs">
        <SharedButton variant="outline" onClick={handleAdd}>
          + Add {type === 'truth' ? 'Truth' : 'Dare'}
        </SharedButton>
        <SharedButton variant="outline" onClick={handleEdit}>
          Edit Selected
        </SharedButton>
        <SharedButton variant="danger" onClick={handleRemove}>
          Remove Selected
        </SharedButton>
      </div>

      <div className="max-h-48 overflow-auto bg-slate-900/60 border border-slate-700 rounded-lg p-2 text-xs space-y-1">
        {items.length === 0 ? (
          <div className="text-slate-500 text-center py-4">
            No default {type}s yet.
          </div>
        ) : (
          items.map((text) => {
            const isSel = selected.includes(text);
            return (
              <button
                key={text}
                type="button"
                className={`w-full text-left px-2 py-1 rounded-md flex gap-2 items-start ${
                  isSel ? 'bg-primary-500/20 border border-primary-500/60' : 'hover:bg-slate-800'
                }`}
                onClick={() => toggleSelected(text)}
              >
                <input
                  type="checkbox"
                  className="mt-0.5"
                  readOnly
                  checked={isSel}
                />
                <span>{text}</span>
              </button>
            );
          })
        )}
      </div>

      <div className="flex justify-between text-[11px] text-slate-400">
        <button onClick={handleSelectAll}>Select All</button>
        <button onClick={handleDeselectAll}>Deselect All</button>
      </div>
    </div>
  );
}

export default function SettingsModal({
  isHost,
  settings,
  defaultTruths,
  defaultDares,
  onClose,
  onSaveSettings,
  onAddItem,
  onEditItem,
  onRemoveItems,
  onSavePreset,
  onLoadPresetFile
}) {
  const [tab, setTab] = useState('game');
  const [localSettings, setLocalSettings] = useState(settings);
  const fileInputRef = useRef(null);

  const updateSetting = (key, value) => {
    setLocalSettings((prev) => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSaveSettings = () => {
    const s = localSettings;
    const num = (k) => parseInt(s[k], 10);

    if (num('countdown_duration') < 3 || num('countdown_duration') > 30) {
      alert('Countdown duration must be between 3 and 30 seconds');
      return;
    }
    if (num('preparation_duration') < 10 || num('preparation_duration') > 120) {
      alert('Preparation duration must be between 10 and 120 seconds');
      return;
    }
    if (num('selection_duration') < 5 || num('selection_duration') > 30) {
      alert('Selection duration must be between 5 and 30 seconds');
      return;
    }
    if (num('truth_dare_duration') < 30 || num('truth_dare_duration') > 180) {
      alert('Truth/Dare duration must be between 30 and 180 seconds');
      return;
    }
    if (num('skip_duration') < 3 || num('skip_duration') > 30) {
      alert('Skip duration must be between 3 and 30 seconds');
      return;
    }
    if (num('max_rounds') < 1 || num('max_rounds') > 50) {
      alert('Maximum rounds must be between 1 and 50');
      return;
    }
    if (num('minigame_chance') < 0 || num('minigame_chance') > 100) {
      alert('Minigame chance must be between 0 and 100%');
      return;
    }

    onSaveSettings({
      countdown_duration: num('countdown_duration'),
      preparation_duration: num('preparation_duration'),
      selection_duration: num('selection_duration'),
      truth_dare_duration: num('truth_dare_duration'),
      skip_duration: num('skip_duration'),
      max_rounds: num('max_rounds'),
      minigame_chance: num('minigame_chance'),
      ai_generation_enabled: !!localSettings.ai_generation_enabled
    });
  };

  const handleTriggerLoadPreset = () => {
    if (!fileInputRef.current) return;
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.json')) {
      alert('Please select a JSON file');
      e.target.value = '';
      return;
    }
    if (!window.confirm('Loading a preset will replace your current truths and dares lists. Continue?')) {
      e.target.value = '';
      return;
    }
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const content = ev.target.result;
        JSON.parse(content); // validation
        onLoadPresetFile(content);
      } catch (err) {
        alert('Invalid JSON file: ' + err.message);
      }
      e.target.value = '';
    };
    reader.onerror = () => {
      alert('Error reading file');
      e.target.value = '';
    };
    reader.readAsText(file);
  };

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-3xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-4 py-3 border-b border-slate-700 flex justify-between items-center">
          <div className="font-semibold text-slate-100">Game Settings</div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-sm"
          >
            ✕
          </button>
        </div>

        {!isHost && (
          <div className="px-4 py-2 text-xs text-amber-300 bg-amber-900/40 border-b border-amber-700/60">
            Only the host can change settings. You can still view them here.
          </div>
        )}

        <div className="px-4 py-2 border-b border-slate-800 flex items-center justify-between">
          <div className="text-xs text-slate-300">
            Save or load a preset file containing both truths and dares.
          </div>
          <div className="flex gap-2">
            <SharedButton
              variant="outline"
              onClick={onSavePreset}
            >
              💾 Save Preset
            </SharedButton>
            <SharedButton
              variant="outline"
              onClick={handleTriggerLoadPreset}
            >
              📁 Load Preset
            </SharedButton>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="px-4 pt-3 flex gap-2 border-b border-slate-800 text-sm">
          <button
            className={`px-3 py-1 rounded-t-md ${
              tab === 'game'
                ? 'bg-slate-800 text-primary-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            onClick={() => setTab('game')}
          >
            Game Settings
          </button>
          <button
            className={`px-3 py-1 rounded-t-md ${
              tab === 'truths'
                ? 'bg-slate-800 text-primary-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            onClick={() => setTab('truths')}
          >
            Default Truths
          </button>
          <button
            className={`px-3 py-1 rounded-t-md ${
              tab === 'dares'
                ? 'bg-slate-800 text-primary-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            onClick={() => setTab('dares')}
          >
            Default Dares
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 text-sm space-y-4">
          {tab === 'game' && (
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Countdown Duration (seconds)
                </label>
                <input
                  type="number"
                  min="3"
                  max="30"
                  className="w-full bg-slate-800 border border-slate-700 rounded-md px-2 py-1 text-xs"
                  value={localSettings.countdown_duration}
                  onChange={(e) =>
                    updateSetting('countdown_duration', e.target.value)
                  }
                  disabled={!isHost}
                />
                <div className="text-[11px] text-slate-500 mt-1">
                  Time before game starts (3-30 seconds)
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Preparation Duration (seconds)
                </label>
                <input
                  type="number"
                  min="10"
                  max="120"
                  className="w-full bg-slate-800 border border-slate-700 rounded-md px-2 py-1 text-xs"
                  value={localSettings.preparation_duration}
                  onChange={(e) =>
                    updateSetting('preparation_duration', e.target.value)
                  }
                  disabled={!isHost}
                />
                <div className="text-[11px] text-slate-500 mt-1">
                  Time to submit truths/dares (10-120 seconds)
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Selection Duration (seconds)
                </label>
                <input
                  type="number"
                  min="5"
                  max="30"
                  className="w-full bg-slate-800 border border-slate-700 rounded-md px-2 py-1 text-xs"
                  value={localSettings.selection_duration}
                  onChange={(e) =>
                    updateSetting('selection_duration', e.target.value)
                  }
                  disabled={!isHost}
                />
                <div className="text-[11px] text-slate-500 mt-1">
                  Time for player to choose truth/dare (5-30 seconds)
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Truth/Dare Duration (seconds)
                </label>
                <input
                  type="number"
                  min="30"
                  max="180"
                  className="w-full bg-slate-800 border border-slate-700 rounded-md px-2 py-1 text-xs"
                  value={localSettings.truth_dare_duration}
                  onChange={(e) =>
                    updateSetting('truth_dare_duration', e.target.value)
                  }
                  disabled={!isHost}
                />
                <div className="text-[11px] text-slate-500 mt-1">
                  Time to perform challenge (30-180 seconds)
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Skip Duration (seconds)
                </label>
                <input
                  type="number"
                  min="3"
                  max="30"
                  className="w-full bg-slate-800 border border-slate-700 rounded-md px-2 py-1 text-xs"
                  value={localSettings.skip_duration}
                  onChange={(e) =>
                    updateSetting('skip_duration', e.target.value)
                  }
                  disabled={!isHost}
                />
                <div className="text-[11px] text-slate-500 mt-1">
                  Time remaining after vote skip (3-30 seconds)
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Maximum Rounds
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  className="w-full bg-slate-800 border border-slate-700 rounded-md px-2 py-1 text-xs"
                  value={localSettings.max_rounds}
                  onChange={(e) =>
                    updateSetting('max_rounds', e.target.value)
                  }
                  disabled={!isHost}
                />
                <div className="text-[11px] text-slate-500 mt-1">
                  Number of rounds before game ends (1-50)
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Minigame Chance (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  className="w-full bg-slate-800 border border-slate-700 rounded-md px-2 py-1 text-xs"
                  value={localSettings.minigame_chance}
                  onChange={(e) =>
                    updateSetting('minigame_chance', e.target.value)
                  }
                  disabled={!isHost}
                />
                <div className="text-[11px] text-slate-500 mt-1">
                  Chance of triggering a minigame (0-100%)
                </div>
              </div>

              <div className="col-span-2 flex items-center gap-2 mt-2">
                <input
                  id="setting-ai-generation"
                  type="checkbox"
                  className="w-4 h-4"
                  checked={!!localSettings.ai_generation_enabled}
                  onChange={(e) =>
                    updateSetting('ai_generation_enabled', e.target.checked)
                  }
                  disabled={!isHost}
                />
                <label
                  htmlFor="setting-ai-generation"
                  className="text-xs text-slate-200"
                >
                  AI-Powered Generation
                </label>
                <div className="text-[11px] text-slate-500 ml-2">
                  Automatically generate new truths/dares when a player runs out (requires Gemini API key).
                </div>
              </div>
            </div>
          )}

          {tab === 'truths' && (
            <DefaultListEditor
              type="truth"
              items={defaultTruths}
              onAdd={onAddItem}
              onEdit={onEditItem}
              onRemove={onRemoveItems}
            />
          )}

          {tab === 'dares' && (
            <DefaultListEditor
              type="dare"
              items={defaultDares}
              onAdd={onAddItem}
              onEdit={onEditItem}
              onRemove={onRemoveItems}
            />
          )}
        </div>

        <div className="px-4 py-3 border-t border-slate-800 flex justify-end gap-2">
          <SharedButton variant="outline" onClick={onClose}>
            Close
          </SharedButton>
          {isHost && (
            <SharedButton variant="primary" onClick={handleSaveSettings}>
              Save &amp; Close
            </SharedButton>
          )}
        </div>
      </div>
    </div>
  );
}
