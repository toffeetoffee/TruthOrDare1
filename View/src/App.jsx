
import React, { useEffect, useMemo, useState } from 'react'
import { io } from 'socket.io-client'

const socket = io({ path: '/socket.io' })
const q = new URLSearchParams(window.location.search)
const initialRoom = q.get('room_code') || ''
const initialName = q.get('name') || ''

const PHASES = { LOBBY:'lobby', COUNTDOWN:'countdown', PREPARATION:'preparation', SELECTION:'selection', MINIGAME:'minigame', TRUTH_DARE:'truth_dare', END_GAME:'end_game' }

export default function App() {
  const [connected, setConnected] = useState(false)
  const [roomCode, setRoomCode] = useState(initialRoom)
  const [name, setName] = useState(initialName)
  const [players, setPlayers] = useState([])
  const [hostSid, setHostSid] = useState(null)
  const [gameState, setGameState] = useState({ phase: PHASES.LOBBY, remaining_time: 0 })
  const [defaults, setDefaults] = useState({ truths: [], dares: [] })
  const [settings, setSettings] = useState({ countdown_duration:10, preparation_duration:30, selection_duration:10, truth_dare_duration:60, skip_duration:5, max_rounds:10, minigame_chance:20, ai_generation_enabled:true })
  const [showSettings, setShowSettings] = useState(false)
  const [textInput, setTextInput] = useState('')
  const [typeInput, setTypeInput] = useState('truth')
  const [targetPlayers, setTargetPlayers] = useState([])

  useEffect(() => {
    function onConnect() {
      setConnected(true)
      if (roomCode && name) {
        socket.emit('join', { room: roomCode, name })
        socket.emit('get_settings', { room: roomCode })
        socket.emit('get_default_lists', { room: roomCode })
      }
    }
    socket.on('connect', onConnect)
    socket.on('disconnect', () => setConnected(false))
    socket.on('player_list', (d)=>{ setPlayers(d.players||[]); setHostSid(d.host_sid||null) })
    socket.on('settings_updated', (d)=>{ if(d?.settings) setSettings(s=>({ ...s, ...d.settings })) })
    socket.on('default_lists_updated', (d)=>{ setDefaults(cur=>({ truths: d.truths ?? cur.truths, dares: d.dares ?? cur.dares })) })
    socket.on('preset_loaded', (d)=>alert(d.message))
    socket.on('preset_error', (d)=>alert('Error: '+d.message))
    socket.on('game_state_update', (d)=>setGameState(d))
    socket.on('room_destroyed', ()=>{ alert('The host closed the room.'); window.location.href='/' })
    socket.on('left_room', ()=>{ window.location.href='/' })
    return () => { socket.off() }
  }, [roomCode, name])

  const isHost = useMemo(()=> socket.id && hostSid && socket.id === hostSid, [hostSid])

  const createOrJoin = (isCreate) => {
    if (!name.trim()) return alert('Enter your name')
    if (!isCreate && !roomCode.trim()) return alert('Enter room code')
    if (isCreate) {
      fetch('/create', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: new URLSearchParams({name})})
        .then(res => { window.location.reload() })
    } else {
      fetch('/join', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: new URLSearchParams({name, code: roomCode})})
        .then(res => { window.location.reload() })
    }
  }

  const saveSettings = () => {
    const s = settings
    if (s.countdown_duration < 3 || s.countdown_duration > 30) return alert('Countdown must be 3-30')
    if (s.preparation_duration < 10 || s.preparation_duration > 120) return alert('Preparation 10-120')
    if (s.selection_duration < 5 || s.selection_duration > 30) return alert('Selection 5-30')
    if (s.truth_dare_duration < 30 || s.truth_dare_duration > 180) return alert('Truth/Dare 30-180')
    if (s.skip_duration < 3 || s.skip_duration > 30) return alert('Skip 3-30')
    if (s.max_rounds < 1 || s.max_rounds > 50) return alert('Rounds 1-50')
    if (s.minigame_chance < 0 || s.minigame_chance > 100) return alert('Minigame 0-100')
    socket.emit('update_settings', { room: roomCode, settings })
    setShowSettings(false)
  }

  const toggleTarget = (p) => setTargetPlayers(prev => prev.includes(p) ? prev.filter(x=>x!==p) : [...prev, p])
  const submitTruthDare = () => {
    const text = textInput.trim()
    if (!text) return alert('Enter a truth/dare')
    if (targetPlayers.length === 0) return alert('Select at least one player')
    socket.emit('submit_truth_dare', { room: roomCode, text, type: typeInput, targets: targetPlayers })
    setTextInput(''); setTargetPlayers([])
  }

  const leaveRoom = () => socket.emit('leave', { room: roomCode })
  const destroyRoom = () => { if (confirm('Destroy room?')) socket.emit('destroy_room', { room: roomCode }) }
  const startGame = () => socket.emit('start_game', { room: roomCode })
  const restartGame = () => { if (confirm('Restart game?')) socket.emit('restart_game', { room: roomCode }) }
  const selectTruthDare = (choice) => socket.emit('select_truth_dare', { room: roomCode, choice })
  const voteMinigame = (who) => socket.emit('minigame_vote', { room: roomCode, voted_player: who })
  const voteSkip = () => socket.emit('vote_skip', { room: roomCode })

  const PhaseView = () => {
    if (gameState.phase === PHASES.COUNTDOWN) {
      return (<div className="section text-center bg-amber-100"><div className="text-xl">Game Starting In</div><div className="text-5xl font-bold text-amber-700">{gameState.remaining_time ?? 0}</div></div>)
    }
    if (gameState.phase === PHASES.PREPARATION) {
      const others = players.filter(p => p !== name)
      return (
        <div className="section bg-sky-100">
          <div className="text-center text-2xl font-bold text-sky-800 mb-4">Preparation Phase: <span>{gameState.remaining_time ?? 0}s</span></div>
          <div className="card">
            <label className="label">Truth or Dare</label>
            <textarea className="input min-h-24" placeholder="Enter a truth or dare..." value={textInput} onChange={e=>setTextInput(e.target.value)} />
            <label className="label mt-3">Type</label>
            <select className="input" value={typeInput} onChange={e=>setTypeInput(e.target.value)}><option value="truth">Truth</option><option value="dare">Dare</option></select>
            <div className="mt-3 font-medium">Add to players:</div>
            <div className="mt-2 grid grid-cols-2 gap-2 max-h-48 overflow-auto">
              {others.length === 0 ? <div className="text-gray-500 col-span-2 text-center">No other players yet</div> :
                others.map(p => (<label key={p} className={`cursor-pointer flex items-center gap-2 p-2 rounded ${targetPlayers.includes(p) ? 'bg-blue-50' : ''}`}>
                    <input type="checkbox" checked={targetPlayers.includes(p)} onChange={()=>toggleTarget(p)} />
                    <span>{p}</span>
                  </label>))
              }
            </div>
            <div className="mt-3 flex gap-2">
              <button className="btn btn-secondary flex-1" onClick={()=>setTargetPlayers(others)}>Select All</button>
              <button className="btn btn-secondary flex-1" onClick={()=>setTargetPlayers([])}>Deselect All</button>
            </div>
            <button className="btn btn-primary w-full mt-3" onClick={submitTruthDare}>Submit</button>
          </div>
        </div>
      )
    }
    if (gameState.phase === PHASES.SELECTION) {
      const isSelected = gameState.selected_player === name
      return (
        <div className="section bg-blue-50 text-center">
          <div className="text-2xl text-blue-900 mb-2">Selected Player</div>
          <div className="text-5xl font-bold bg-white inline-block px-8 py-6 rounded-2xl shadow">{gameState.selected_player || '???'}</div>
          <div className="mt-3 text-gray-600">Time remaining: <span>{gameState.remaining_time ?? 0}s</span></div>
          {isSelected && !gameState.selected_choice && (<div className="flex gap-3 justify-center mt-6">
              <button className="btn btn-green text-lg px-6" onClick={()=>selectTruthDare('truth')}>Truth</button>
              <button className="btn btn-danger text-lg px-6" onClick={()=>selectTruthDare('dare')}>Dare</button>
            </div>)}
          {!isSelected && gameState.selected_choice && (<div className="mt-4 text-gray-700">Choice: <b>{String(gameState.selected_choice).toUpperCase()}</b></div>)}
        </div>
      )
    }
    if (gameState.phase === PHASES.MINIGAME && gameState.minigame) {
      const mg = gameState.minigame
      const participants = mg.participants || []
      const voteCounts = mg.vote_counts || {}
      const votes1 = voteCounts[participants[0]] || 0
      const votes2 = voteCounts[participants[1]] || 0
      const isParticipant = participants.includes(name)
      return (
        <div className="section bg-amber-50">
          <div className="text-3xl font-bold text-amber-700 mb-2">{mg.name || 'Minigame'}</div>
          <div className="text-gray-700 mb-4">{isParticipant ? (mg.description_participant || '') : (mg.description_voter || '')}</div>
          <div className="flex items-center justify-center gap-6">
            <div className="card min-w-[180px] text-center">
              <div className="text-xl font-bold">{participants[0] || 'Player 1'}</div>
              <div className="text-blue-600 font-semibold mt-1">{votes1} vote{votes1 !== 1 ? 's' : ''}</div>
            </div>
            <div className="text-2xl font-bold text-red-600">VS</div>
            <div className="card min-w-[180px] text-center">
              <div className="text-xl font-bold">{participants[1] || 'Player 2'}</div>
              <div className="text-blue-600 font-semibold mt-1">{votes2} vote{votes2 !== 1 ? 's' : ''}</div>
            </div>
          </div>
          {!isParticipant && (
            <div className="card mt-4 text-center">
              <div className="font-medium mb-3">{mg.vote_instruction || 'Vote for the loser!'}</div>
              <div className="flex gap-3 justify-center">
                <button className="btn btn-primary" onClick={()=>voteMinigame(participants[0])}>{participants[0] || 'Player 1'} loses!</button>
                <button className="btn btn-primary" onClick={()=>voteMinigame(participants[1])}>{participants[1] || 'Player 2'} loses!</button>
              </div>
              <div className="text-gray-600 mt-3">Votes: <b>{mg.vote_count || 0}</b> / <b>{mg.total_voters || 0}</b></div>
            </div>
          )}
        </div>
      )
    }
    if (gameState.phase === PHASES.TRUTH_DARE) {
      const isSelected = gameState.selected_player === name
      const listEmpty = !!gameState.list_empty
      const td = gameState.current_truth_dare
      return (
        <div className="section bg-amber-100">
          {listEmpty && (<div className="mb-4 p-3 rounded-lg border-2 border-amber-400 bg-yellow-50">
              <div className="font-bold text-amber-800">List Empty</div>
              <div className="text-amber-700 text-sm">Skip auto-activated.</div>
            </div>)}
          <div className="text-center mb-2">
            <div className="text-2xl font-bold text-amber-800">{String(gameState.selected_choice || '').toUpperCase()}</div>
            <div className="text-gray-700"> <b>{gameState.selected_player || ''}</b> is performing</div>
          </div>
          <div className={`card text-center text-xl ${listEmpty ? 'border-2 border-amber-400 bg-yellow-50' : ''}`}>
            {td?.text || '...'}
          </div>
          {!isSelected && (<div className="card mt-3 text-center">
              <button className="btn btn-secondary" disabled={listEmpty || gameState.skip_activated} onClick={voteSkip}>
                {listEmpty ? 'List Empty - Skip Auto' : (gameState.skip_activated ? 'Skip Activated' : 'Vote to Skip')}
              </button>
              <div className="text-gray-600 mt-2">
                Votes: <b>{gameState.skip_vote_count || 0}</b> / <b>{Math.ceil(Math.max(players.length - 1, 0) / 2)}</b>
              </div>
            </div>)}
          <div className="text-center text-lg mt-3">Time: <b>{gameState.remaining_time ?? 0}</b>s</div>
        </div>
      )
    }
    if (gameState.phase === PHASES.END_GAME) {
      return (
        <div className="section bg-green-100">
          <div className="text-3xl font-bold text-green-800 text-center mb-4">🎉 Game Over! 🎉</div>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="card">
              <div className="heading">Top Players</div>
              {(gameState.top_players || []).length === 0 ? (
                <div className="text-gray-500">No players</div>
              ) : (
                <div className="space-y-2">
                  {gameState.top_players.map((p,i)=>(
                    <div key={i} className="flex justify-between bg-gray-50 p-2 rounded">
                      <span className="font-medium">#{i+1} {p.name}</span>
                      <span className="font-bold text-blue-600">{p.score} pts</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="card max-h-96 overflow-auto">
              <div className="heading">Round History</div>
              {(gameState.round_history || []).slice().reverse().map((r,idx)=>(
                <div key={idx} className="bg-gray-50 p-2 rounded mb-2">
                  <div className="font-medium">Round {r.round_number}</div>
                  <div><b>{r.selected_player}</b> performed a <b>{r.truth_dare.type}</b></div>
                  <div className="italic text-gray-700">"{r.truth_dare.text}"</div>
                  <div className="text-xs text-gray-500">{r.submitted_by ? `Submitted by: ${r.submitted_by}` : 'Default challenge'}</div>
                </div>
              ))}
            </div>
          </div>
          {isHost && (<div className="card mt-3 flex gap-2">
              <button className="btn btn-secondary" onClick={()=>setShowSettings(true)}>Settings</button>
              <button className="btn btn-green" onClick={restartGame}>Restart Game</button>
            </div>)}
          <div className="card mt-3 text-center">
            <button className="btn btn-danger" onClick={leaveRoom}>Leave Room</button>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="max-w-3xl mx-auto p-5">
      <div className="text-center mb-5">
        <h1 className="text-3xl font-bold">Dare or Dare</h1>
        {roomCode && <div className="text-gray-600">Room Code: <span className="badge">{roomCode}</span></div>}
      </div>

      {!connected || !roomCode || !name ? (
        <div className="grid md:grid-cols-2 gap-4">
          <div className="section">
            <div className="heading">Create Room</div>
            <label className="label">Your Name</label>
            <input className="input" value={name} onChange={e=>setName(e.target.value)} placeholder="Enter your name" />
            <button className="btn btn-primary w-full mt-3" onClick={()=>createOrJoin(true)}>Create</button>
          </div>
          <div className="section">
            <div className="heading">Join Room</div>
            <label className="label">Your Name</label>
            <input className="input" value={name} onChange={e=>setName(e.target.value)} placeholder="Enter your name" />
            <label className="label mt-2">Room Code</label>
            <input className="input" value={roomCode} onChange={e=>setRoomCode(e.target.value.toUpperCase())} placeholder="ABC123" />
            <button className="btn btn-primary w-full mt-3" onClick={()=>createOrJoin(false)}>Join</button>
          </div>
        </div>
      ) : (
        <>
          {gameState.phase === PHASES.LOBBY && (
            <div className="grid md:grid-cols-2 gap-4">
              <div className="section">
                <div className="heading">Players in Room</div>
                <ul className="space-y-2">
                  {players.length === 0 ? <li className="text-gray-500">Waiting for players...</li> :
                    players.map((p,idx)=>(
                      <li key={p} className={`card py-3 ${idx===0?'ring-1 ring-blue-400 bg-blue-50':''}`}>
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{p}</span>
                          {idx===0 && <span className="text-xs text-blue-700">(Host)</span>}
                        </div>
                      </li>
                    ))
                  }
                </ul>
                <div className="text-sm text-gray-600 mt-2">{players.length} player(s) in room</div>
              </div>
              <div className="section space-y-2">
                <button className="btn btn-danger w-full" onClick={leaveRoom}>Leave Room</button>
                {isHost && (
                  <div className="space-y-2">
                    <button className="btn btn-secondary w-full" onClick={()=>setShowSettings(true)}>Settings</button>
                    <button className="btn btn-green w-full" onClick={startGame} id="start-button">Start Game</button>
                    <button className="btn btn-secondary w-full" onClick={destroyRoom}>Destroy Room</button>
                  </div>
                )}
              </div>
            </div>
          )}
          {gameState.phase !== PHASES.LOBBY && (
            <div className="space-y-4">
              <div className="card flex justify-end">
                <button className="btn btn-danger" onClick={leaveRoom}>Leave Room</button>
              </div>
              <PhaseView />
            </div>
          )}
        </>
      )}

      {showSettings && (
        <div className="modal-backdrop" onClick={(e)=>{ if(e.target===e.currentTarget) setShowSettings(false) }}>
          <div className="modal">
            <div className="p-5 border-b">
              <div className="text-xl font-bold">Game Settings</div>
            </div>
            <div className="p-5 space-y-3 max-h-[70vh] overflow-auto">
              <NumberInput label="Countdown Duration (3-30)" value={settings.countdown_duration} onChange={v=>setSettings(s=>({...s, countdown_duration:v}))} min={3} max={30} />
              <NumberInput label="Preparation Duration (10-120)" value={settings.preparation_duration} onChange={v=>setSettings(s=>({...s, preparation_duration:v}))} min={10} max={120} />
              <NumberInput label="Selection Duration (5-30)" value={settings.selection_duration} onChange={v=>setSettings(s=>({...s, selection_duration:v}))} min={5} max={30} />
              <NumberInput label="Truth/Dare Duration (30-180)" value={settings.truth_dare_duration} onChange={v=>setSettings(s=>({...s, truth_dare_duration:v}))} min={30} max={180} />
              <NumberInput label="Skip Duration (3-30)" value={settings.skip_duration} onChange={v=>setSettings(s=>({...s, skip_duration:v}))} min={3} max={30} />
              <NumberInput label="Maximum Rounds (1-50)" value={settings.max_rounds} onChange={v=>setSettings(s=>({...s, max_rounds:v}))} min={1} max={50} />
              <NumberInput label="Minigame Chance (0-100)" value={settings.minigame_chance} onChange={v=>setSettings(s=>({...s, minigame_chance:v}))} min={0} max={100} />
              <Toggle label="AI-Powered Generation" checked={!!settings.ai_generation_enabled} onChange={v=>setSettings(s=>({...s, ai_generation_enabled: v}))} />
              <hr className="my-2" />
              <div className="text-sm text-gray-600">Default Lists (read-only).</div>
              <div className="grid grid-cols-2 gap-3">
                <div><div className="font-medium mb-1">Default Truths</div><div className="card max-h-48 overflow-auto text-sm">{defaults.truths?.map((t,i)=>(<div key={i} className="py-1">{t}</div>))}</div></div>
                <div><div className="font-medium mb-1">Default Dares</div><div className="card max-h-48 overflow-auto text-sm">{defaults.dares?.map((d,i)=>(<div key={i} className="py-1">{d}</div>))}</div></div>
              </div>
            </div>
            <div className="p-5 border-t flex gap-2">
              <button className="btn btn-secondary flex-1" onClick={()=>setShowSettings(false)}>Close</button>
              <button className="btn btn-green flex-1" onClick={saveSettings}>Save & Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function NumberInput({label, value, onChange, min, max}) {
  return (<div><label className="label">{label}</label><input className="input" type="number" value={value} min={min} max={max} onChange={e=>onChange(parseInt(e.target.value || 0))} /></div>)
}
function Toggle({label, checked, onChange}) {
  return (<label className="flex items-center gap-2"><input type="checkbox" checked={checked} onChange={e=>onChange(e.target.checked)} /><span>{label}</span></label>)
}
