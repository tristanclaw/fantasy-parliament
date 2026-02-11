import React, { useState, useEffect } from 'react';
import Scoreboard from './components/Scoreboard';
import DraftPool from './components/DraftPool';
import MyTeam from './components/MyTeam';
import Welcome from './components/Welcome';

function App() {
  const [username, setUsername] = useState(() => localStorage.getItem('fp_username') || '');
  const [team, setTeam] = useState(() => {
    const saved = localStorage.getItem('fp_team');
    return saved ? JSON.parse(saved) : { captain: null, members: [] };
  });

  useEffect(() => {
    localStorage.setItem('fp_username', username);
  }, [username]);

  useEffect(() => {
    localStorage.setItem('fp_team', JSON.stringify(team));
  }, [team]);

  const handleOnboardingComplete = (name, captain) => {
    setUsername(name);
    setTeam({ captain, members: [] });
  };

  const handleDraft = (mp) => {
    // Check duplicates
    if (team.captain?.id === mp.id || team.members.some(m => m.id === mp.id)) {
      alert("This MP is already on your team!");
      return;
    }

    if (!team.captain) {
      if (confirm(`Draft ${mp.name} as your Team Captain?`)) {
        setTeam(prev => ({ ...prev, captain: mp }));
      }
    } else {
      if (team.members.length >= 4) {
        alert("Your team roster is full (1 Captain + 4 Members).");
        return;
      }
      setTeam(prev => ({ ...prev, members: [...prev.members, mp] }));
    }
  };

  const handleRemove = (id) => {
    if (team.captain?.id === id) {
        if (confirm("Removing the captain will reset your team leader. Continue?")) {
            setTeam(prev => ({ ...prev, captain: null }));
        }
    } else {
        setTeam(prev => ({ ...prev, members: prev.members.filter(m => m.id !== id) }));
    }
  };

  const handleSubmitScore = async (score) => {
    if (!username) {
      alert("Please set a username first.");
      return;
    }

    try {
      const response = await fetch('https://fantasy-parliament-api.onrender.com/leaderboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username, score })
      });
      if (response.ok) {
        alert("Score submitted to leaderboard!");
      } else {
        alert("Failed to submit score.");
      }
    } catch (e) {
      console.error(e);
      alert("Error submitting score.");
    }
  };

  // If no username, show onboarding
  if (!username) {
    return <Welcome onComplete={handleOnboardingComplete} />;
  }

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
      {/* Navigation */}
      <nav className="bg-red-700 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <span className="text-xl font-black tracking-tighter uppercase">Fantasy <span className="text-red-200">Parliament</span></span>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <a href="#" className="bg-red-800 px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>
                <a href="#" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">My Team</a>
                <a href="#" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Rules</a>
              </div>
            </div>
            <div className="flex items-center space-x-2">
                <span className="text-red-200 text-sm font-medium">Welcome, {username}</span>
                <div className="bg-red-800 p-2 rounded-full h-8 w-8 flex items-center justify-center font-bold text-xs">
                    {username ? username.substring(0,2).toUpperCase() : '??'}
                </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">MP Dashboard</h1>
          <p className="text-gray-500 mt-2">Manage your fantasy team and track the latest parliamentary performance stats.</p>
        </header>

        {!team.captain && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                <div className="flex">
                    <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div className="ml-3">
                        <p className="text-sm text-yellow-700">
                            <strong>Action Required:</strong> Please select a <strong>Team Captain</strong> from the Draft Pool below to start building your team.
                        </p>
                    </div>
                </div>
            </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content Area - Draft Pool */}
          <div className="lg:col-span-2">
            <MyTeam team={team} onRemove={handleRemove} onSubmit={handleSubmitScore} />
            <DraftPool onDraft={handleDraft} />
          </div>

          {/* Sidebar Area - Scoreboard */}
          <div className="lg:col-span-1">
            <Scoreboard />
          </div>
        </div>
      </main>

      <footer className="mt-auto py-8 text-center text-gray-400 text-sm">
        &copy; 2026 Fantasy Parliament League. Data powered by OpenParliament.
      </footer>
    </div>
  );
}

export default App;
