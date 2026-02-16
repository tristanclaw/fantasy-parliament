import React, { useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'https://fantasy-parliament-web.onrender.com';

const ConnectionStatus = () => {
  const [status, setStatus] = useState('connecting'); // 'connecting', 'online', 'offline'
  const [lastChecked, setLastChecked] = useState(null);

  useEffect(() => {
    const checkStatus = async () => {
      setStatus('connecting');
      try {
        const response = await fetch(`${API_URL}/mps`, { 
          method: 'HEAD',
          signal: AbortSignal.timeout(5000)
        });
        if (response.ok) {
          setStatus('online');
        } else {
          setStatus('offline');
        }
      } catch (e) {
        setStatus('offline');
      }
      setLastChecked(new Date());
    };

    // Check immediately on mount
    checkStatus();

    // Check every 30 seconds
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const statusConfig = {
    connecting: { 
      color: 'bg-yellow-500', 
      text: 'Connecting...', 
      icon: '⏳'
    },
    online: { 
      color: 'bg-green-500', 
      text: 'API Online', 
      icon: '✓' 
    },
    offline: { 
      color: 'bg-red-500', 
      text: 'API Offline', 
      icon: '✕' 
    }
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2 text-sm" title={lastChecked ? `Last checked: ${lastChecked.toLocaleTimeString()}` : ''}>
      <span className={`w-2 h-2 rounded-full ${config.color} ${status === 'connecting' ? 'animate-pulse' : ''}`}></span>
      <span className="text-red-100">{config.icon} {config.text}</span>
    </div>
  );
};

export default ConnectionStatus;
