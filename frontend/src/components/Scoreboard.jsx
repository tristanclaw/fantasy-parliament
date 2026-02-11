import React, { useState, useEffect } from 'react';

const Scoreboard = () => {
    const [topMPs, setTopMPs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchScoreboard = async () => {
            try {
                const response = await fetch('https://fantasy-parliament-api.onrender.com/scoreboard');
                if (!response.ok) {
                    throw new Error('Failed to fetch scoreboard');
                }
                const data = await response.json();
                setTopMPs(data);
                setLoading(false);
            } catch (err) {
                setError(err.message);
                setLoading(false);
            }
        };

        fetchScoreboard();
    }, []);

    if (loading) return <div className="p-4">Loading Scoreboard...</div>;
    if (error) return <div className="p-4 text-red-500">Error: {error}</div>;

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
            <h2 className="text-2xl font-bold mb-6 text-indigo-900 border-b pb-2">Live Scoreboard</h2>
            <div className="space-y-4">
                {topMPs.map((mp, index) => (
                    <div key={mp.id || index} className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg transition hover:bg-indigo-100">
                        <div className="flex items-center space-x-4">
                            <span className="font-bold text-indigo-600 w-6">#{index + 1}</span>
                            <div>
                                <p className="font-semibold text-gray-800">{mp.name}</p>
                                <p className="text-sm text-gray-500">{mp.party} - {mp.constituency}</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <span className="text-xl font-bold text-indigo-700">{mp.score}</span>
                            <p className="text-xs text-indigo-400 uppercase tracking-wider font-semibold">Points</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Scoreboard;
