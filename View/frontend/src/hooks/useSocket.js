import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';

/**
 * Hook to manage Socket.IO connection and initial join.
 * It connects when `enabled` is true and `roomCode` & `playerName` are set.
 */
export default function useSocket(roomCode, playerName, enabled) {
  const [isConnected, setIsConnected] = useState(false);
  const [mySid, setMySid] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!enabled || !roomCode || !playerName) return;

    const socket = io(); // same origin as Flask backend
    socketRef.current = socket;

    socket.on('connect', () => {
      setIsConnected(true);
      setMySid(socket.id);
      // Join room once connected
      socket.emit('join', { room: roomCode, name: playerName });
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
      setMySid(null);
    });

    return () => {
      socket.disconnect();
    };
  }, [roomCode, playerName, enabled]);

  return {
    socket: socketRef.current,
    isConnected,
    mySid
  };
}
