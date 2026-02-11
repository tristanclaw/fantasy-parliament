import React from 'react';

const MyTeam = ({ team, onRemove, onSubmit }) => {
    const { captain, members } = team;
    const allMembers = captain ? [captain, ...members] : members;
    
    // Calculate total score safely
    const totalScore = allMembers.reduce((sum, mp) => sum + (mp.score || 0), 0);

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 mb-8">
            <h2 className="text-2xl font-bold mb-4 text-red-700 border-b pb-2 flex justify-between items-center">
                <span>My Team</span>
                <span className="text-gray-900 bg-red-100 px-3 py-1 rounded-full text-sm">Total Score: {totalScore}</span>
            </h2>

            {/* Captain Section */}
            <div className="mb-6">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wide mb-2">Team Captain</h3>
                {captain ? (
                    <div className="border-2 border-yellow-400 p-4 rounded-lg bg-yellow-50 relative">
                        <div className="flex justify-between items-start">
                            <div>
                                <h3 className="font-bold text-gray-800 text-lg">{captain.name}</h3>
                                <p className="text-sm text-gray-600">{captain.party} • {captain.constituency}</p>
                            </div>
                            <div className="text-xl font-black text-yellow-600">{captain.score} pts</div>
                        </div>
                        <span className="absolute -top-2 -right-2 bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-1 rounded shadow-sm">CAPTAIN</span>
                    </div>
                ) : (
                    <div className="border-2 border-dashed border-gray-300 p-4 rounded-lg bg-gray-50 text-center text-gray-400">
                        No Captain Selected
                    </div>
                )}
            </div>

            {/* Members Section */}
            <div className="mb-6">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wide mb-2">Team Members ({members.length}/4)</h3>
                <div className="grid grid-cols-1 gap-3">
                    {members.map((mp, index) => (
                        <div key={mp.id || index} className="border border-gray-200 p-3 rounded-lg flex justify-between items-center">
                            <div>
                                <h4 className="font-semibold text-gray-800">{mp.name}</h4>
                                <p className="text-xs text-gray-500">{mp.party}</p>
                            </div>
                            <div className="flex items-center space-x-3">
                                <span className="font-bold text-gray-700">{mp.score} pts</span>
                                <button 
                                    onClick={() => onRemove(mp.id)}
                                    className="text-red-400 hover:text-red-600 text-sm font-medium"
                                >
                                    Remove
                                </button>
                            </div>
                        </div>
                    ))}
                    {members.length === 0 && (
                        <p className="text-sm text-gray-500 italic">Draft MPs to fill your roster.</p>
                    )}
                </div>
            </div>

            <button 
                onClick={() => onSubmit(totalScore)}
                className="w-full bg-red-600 text-white font-bold py-3 rounded-lg hover:bg-red-700 transition shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!captain}
            >
                Submit Score to Leaderboard
            </button>
        </div>
    );
};

export default MyTeam;
