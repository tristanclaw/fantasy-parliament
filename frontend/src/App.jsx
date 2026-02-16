import React, { useState, useEffect } from 'react';
import { HashRouter, Routes, Route, Link } from 'react-router-dom';
import Scoreboard from './components/Scoreboard';
import DraftPool from './components/DraftPool';
import MyTeam from './components/MyTeam';
import MPProfile from './components/MPProfile';
import Welcome from './components/Welcome';
import Rules from './components/Rules';
import Schedule from './components/Schedule';
import Admin from './components/Admin';

function MainApp() {
  const [username, setUsername] = useState(() => localStorage.getItem('fp_username') || '');
  const [team, setTeam] = useState(() => {
    const saved = localStorage.getItem('fp_team');
    return saved ? JSON.parse(saved) : { captain: null, members: [] };
  });
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem('fp_username', username);
  }, [username]);

  useEffect(() => {
    localStorage.setItem('fp_team', JSON.stringify(team));
  }, [team]);

  const handleOnboardingComplete = async (name, email, captain) => {
    try {
      const response = await fetch('https://fantasy-parliament-web.onrender.com/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          display_name: name,
          email: email,
          captain_mp_id: captain.id,
          team_mp_ids: [captain.id]
        })
      });
      if (response.ok) {
        setUsername(name);
        setTeam({ captain, members: [] });
      } else {
        const err = await response.json();
        alert("Registration failed: " + (err.detail || "Unknown error"));
      }
    } catch (e) {
      console.error(e);
      alert("Error registering. Try again.");
    }
  };

  const handleDraft = (mp) => {
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
      const response = await fetch('https://fantasy-parliament-web.onrender.com/leaderboard', {
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

  if (!username) {
    return <Welcome onComplete={handleOnboardingComplete} />;
  }

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900 flex flex-col">
      <nav className="bg-red-700 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-black tracking-tighter uppercase">Fantasy <span className="text-red-200">Parliament</span></Link>
            </div>
            
            {/* Desktop Menu */}
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link to="/" className="bg-red-800 px-3 py-2 rounded-md text-sm font-medium">Dashboard</Link>
                <Link to="/my-team" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">My Team</Link>
                <Link to="/rules" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Rules</Link>
                <Link to="/schedule" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Schedule</Link>
              </div>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="inline-flex items-center justify-center p-2 rounded-md text-red-100 hover:text-white hover:bg-red-800 focus:outline-none"
              >
                <svg className="h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
                  {isMobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>

            <div className="hidden md:flex items-center space-x-2">
                <span className="text-red-200 text-sm font-medium">Welcome, {username}</span>
                <div className="bg-red-800 p-2 rounded-full h-8 w-8 flex items-center justify-center font-bold text-xs">
                    {username ? username.substring(0,2).toUpperCase() : '??'}
                </div>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden bg-red-800">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              <Link to="/" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-red-700">Dashboard</Link>
              <Link to="/my-team" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-red-700">My Team</Link>
              <Link to="/rules" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-red-700">Rules</Link>
                <Link to="/schedule" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-red-700">Schedule</Link>
            </div>
            <div className="pt-4 pb-2 border-t border-red-700">
                <div className="flex items-center px-4">
                    <div className="flex-shrink-0">
                        <div className="h-8 w-8 rounded-full bg-red-600 flex items-center justify-center font-bold text-xs">
                            {username ? username.substring(0,2).toUpperCase() : '??'}
                        </div>
                    </div>
                    <div className="ml-3">
                        <div className="text-base font-medium text-white">{username}</div>
                    </div>
                </div>
            </div>
          </div>
        )}
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 flex-grow">
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
          <div className="lg:col-span-2">
            <MyTeam team={team} username={username} onRemove={handleRemove} />
            <DraftPool onDraft={handleDraft} />
          </div>
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

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/my-team" element={<MyTeamViewWrapper />} />
        <Route path="/mp/:id" element={<MPProfile />} />
        <Route path="/rules" element={<Rules />} />
        <Route path="/schedule" element={<Schedule />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </HashRouter>
  );
}

// Wrapper to reuse MyTeam component without props or with default props if needed
// For now, MyTeam expects 'team', 'username', 'onRemove'.
// The MainApp renders it with those props.
// We need to lift state or just duplicate the logic.
// Actually, let's just pass empty team or fetch from local storage in the wrapper.
import { useNavigate } from 'react-router-dom';

function MyTeamViewWrapper() {
    const [username, setUsername] = useState(() => localStorage.getItem('fp_username') || '');
    const [team, setTeam] = useState(() => {
        const saved = localStorage.getItem('fp_team');
        return saved ? JSON.parse(saved) : { captain: null, members: [] };
    });
    const navigate = useNavigate();

    const handleRemove = (id) => {
        if (team.captain?.id === id) {
            if (confirm("Removing the captain will reset your team leader. Continue?")) {
                setTeam(prev => ({ ...prev, captain: null }));
            }
        } else {
            setTeam(prev => ({ ...prev, members: prev.members.filter(m => m.id !== id) }));
        }
    };
    
    useEffect(() => {
        localStorage.setItem('fp_team', JSON.stringify(team));
    }, [team]);

    if (!username) {
        // Redirect to home to set username
        useEffect(() => {
            navigate('/');
        }, [navigate]);
        return null;
    }

    return (
        <div className="min-h-screen bg-gray-50 font-sans text-gray-900 flex flex-col">
            <nav className="bg-red-700 text-white shadow-md">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center">
                            <Link to="/" className="text-xl font-black tracking-tighter uppercase">Fantasy <span className="text-red-200">Parliament</span></Link>
                        </div>
                        <div className="hidden md:block">
                            <div className="ml-10 flex items-baseline space-x-4">
                                <Link to="/" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Dashboard</Link>
                                <Link to="/my-team" className="bg-red-800 px-3 py-2 rounded-md text-sm font-medium">My Team</Link>
                                <Link to="/rules" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Rules</Link>
                                <Link to="/schedule" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Schedule</Link>
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
            <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 flex-grow w-full">
                <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
                    <MyTeam team={team} username={username} onRemove={handleRemove} />
                </div>
            </main>
            <footer className="mt-auto py-8 text-center text-gray-400 text-sm">
                &copy; 2026 Fantasy Parliament League. Data powered by OpenParliament.
            </footer>
        </div>
    );
}

export default App;
