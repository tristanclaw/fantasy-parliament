import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const Scoreboard = () => {
    const [topMPs, setTopMPs] = useState([]);
    const [leaderboard, setLeaderboard] = useState([]);
    const [specialTeams, setSpecialTeams] = useState([]);
    const [view, setView] = useState('mps'); // 'mps', 'users', or 'special'
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            if (view === 'mps') {
                const response = await fetch('https://fantasy-parliament-api.onrender.com/scoreboard');
                const data = await response.json();
                setTopMPs(data);
            } else if (view === 'users') {
                const response = await fetch('https://fantasy-parliament-api.onrender.com/leaderboard');
                const data = await response.json();
                setLeaderboard(data);
            } else if (view === 'special') {
                const response = await fetch('https://fantasy-parliament-api.onrender.com/special');
                if (!response.ok) {
                    throw new Error('Failed to load special leaderboard');
                }
                const data = await response.json();
                setSpecialTeams(data);
            }
            setLoading(false);
        } catch (err) {
            setError(err.message);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [view]);

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 h-full">
            <div className="flex justify-between items-center mb-6 border-b pb-2">
                <h2 className="text-2xl font-bold text-red-700">Rankings</h2>
                <div className="flex space-x-2 bg-gray-100 p-1 rounded-lg">
                    <button 
                        onClick={() => setView('mps')}
                        className={`px-3 py-1 text-xs font-bold rounded-md transition ${view === 'mps' ? 'bg-white text-red-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        MPs
                    </button>
                    <button 
                        onClick={() => setView('users')}
                        className={`px-3 py-1 text-xs font-bold rounded-md transition ${view === 'users' ? 'bg-white text-red-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Users
                    </button>
                    <button 
                        onClick={() => setView('special')}
                        className={`px-3 py-1 text-xs font-bold rounded-md transition ${view === 'special' ? 'bg-white text-red-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Special
                    </button>
                </div>
            </div>

            {loading ? <div className="p-4 text-center text-gray-400">Loading...</div> : 
             error ? <div className="p-4 text-red-500">Error: {error}</div> : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                    {view === 'mps' && topMPs.map((mp, index) => (
                        <Link to={`/mp/${mp.id}`} key={mp.id || index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg transition hover:bg-red-100">
                            <div className="flex items-center space-x-4">
                                <span className="font-bold text-red-600 w-6">#{index + 1}</span>
                                <div>
                                    <p className="font-semibold text-gray-800">{mp.name}</p>
                                    <p className="text-sm text-gray-500">{mp.party} - {mp.constituency}</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <span className="text-xl font-bold text-red-700">{mp.score}</span>
                                <p className="text-xs text-red-400 uppercase tracking-wider font-semibold">Points</p>
                            </div>
                        </Link>
                    ))}
                    
                    {view === 'users' && leaderboard.map((entry, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg transition hover:bg-blue-100">
                            <div className="flex items-center space-x-4">
                                <span className="font-bold text-blue-600 w-6">#{index + 1}</span>
                                <div>
                                    <p className="font-semibold text-gray-800">{entry.username}</p>
                                    <p className="text-xs text-gray-400">{new Date(entry.updated_at).toLocaleDateString()}</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <span className="text-xl font-bold text-blue-700">{entry.score}</span>
                                <p className="text-xs text-blue-400 uppercase tracking-wider font-semibold">Total</p>
                            </div>
                        </div>
                    ))}

                    {view === 'special' && specialTeams.map((team, index) => (
                        <div key={team.id} className="border border-gray-200 rounded-lg p-4 bg-purple-50 hover:bg-purple-100 transition">
                            <div className="flex justify-between items-center mb-2">
                                <h3 className="font-bold text-purple-900">{team.name}</h3>
                                <div className="text-right">
                                    <span className="text-xl font-bold text-purple-700">{team.score}</span>
                                    <span className="text-xs text-purple-500 ml-1 uppercase">Points</span>
                                </div>
                            </div>
                            <div className="flex -space-x-2 overflow-hidden">
                                {team.mps.map((mp, i) => (
                                    <div key={mp.id || i} className="relative inline-block h-8 w-8 rounded-full ring-2 ring-white bg-gray-300 flex items-center justify-center text-xs overflow-hidden" title={mp.name}>
                                        {mp.image_url ? (
                                            <img src={mp.image_url} alt={mp.name} className="h-full w-full object-cover" />
                                        ) : (
                                            <span>{mp.name.substring(0, 2)}</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                {team.mps.length} Members
                            </p>
                        </div>
                    ))}

                    {((view === 'mps' && topMPs.length === 0) || 
                      (view === 'users' && leaderboard.length === 0) ||
                      (view === 'special' && specialTeams.length === 0)) && (
                        <p className="text-center text-gray-400 py-4">No rankings available.</p>
                    )}
                </div>
            )}
        </div>
    );
};

export default Scoreboard;
