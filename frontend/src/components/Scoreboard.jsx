import React, { useState, useEffect } from 'react';

const Scoreboard = () => {
    const [topMPs, setTopMPs] = useState([]);
    const [leaderboard, setLeaderboard] = useState([]);
    const [view, setView] = useState('mps'); // 'mps' or 'users'
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            if (view === 'mps') {
                const response = await fetch('https://fantasy-parliament-api.onrender.com/scoreboard');
                const data = await response.json();
                setTopMPs(data);
            } else {
                const response = await fetch('https://fantasy-parliament-api.onrender.com/leaderboard');
                const data = await response.json();
                setLeaderboard(data);
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
                </div>
            </div>

            {loading ? <div className="p-4 text-center text-gray-400">Loading...</div> : 
             error ? <div className="p-4 text-red-500">Error: {error}</div> : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                    {view === 'mps' ? topMPs.map((mp, index) => (
                        <div key={mp.id || index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg transition hover:bg-red-100">
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
                        </div>
                    )) : leaderboard.map((entry, index) => (
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
                    {((view === 'mps' && topMPs.length === 0) || (view === 'users' && leaderboard.length === 0)) && (
                        <p className="text-center text-gray-400 py-4">No rankings available.</p>
                    )}
                </div>
            )}
        </div>
    );
};

export default Scoreboard;
