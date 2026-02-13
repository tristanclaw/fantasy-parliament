import React, { useState, useEffect } from 'react';

const MyTeam = ({ team, username, onRemove }) => {
    const { captain, members } = team;
    const allMembers = captain ? [captain, ...members] : (members || []);
    
    // Calculate total score safely
    const totalScore = allMembers.reduce((sum, mp) => sum + (mp.score || 0), 0);

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formData, setFormData] = useState({
        displayName: username || '',
        teamName: '',
        email: ''
    });
    const [status, setStatus] = useState('idle'); // idle, submitting, success, error
    const [message, setMessage] = useState('');

    useEffect(() => {
        if (username) {
            setFormData(prev => ({ ...prev, displayName: username }));
        }
    }, [username]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus('submitting');
        setMessage('');

        // Generate a random user ID for now (or use existing if available in context)
        const userId = localStorage.getItem('fantasy_parliament_user_id') || `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem('fantasy_parliament_user_id', userId);

        const payload = {
            user_id: userId,
            display_name: formData.displayName,
            team_name: formData.teamName || null,
            email: formData.email,
            captain_mp_id: captain.id,
            team_mp_ids: members.map(m => m.id)
        };
        
        const apiUrl = import.meta.env.VITE_API_URL || 'https://fantasy-parliament-api.onrender.com';

        try {
            const response = await fetch(`${apiUrl}/api/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (response.ok) {
                setStatus('success');
                setMessage('Successfully registered for the season!');
                setTimeout(() => {
                    setIsModalOpen(false);
                    setStatus('idle');
                    // We don't clear form data immediately so user sees their success
                }, 3000);
            } else {
                setStatus('error');
                setMessage(data.detail || 'Registration failed. Please try again.');
            }
        } catch (error) {
            setStatus('error');
            setMessage('Network error. Please try again.');
            console.error(error);
        }
    };

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
                onClick={() => setIsModalOpen(true)}
                className="w-full bg-red-600 text-white font-bold py-3 rounded-lg hover:bg-red-700 transition shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!captain || members.length < 4}
            >
                Join the Season
            </button>

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md w-full border border-gray-200">
                        <h2 className="text-2xl font-bold mb-4 text-gray-800 border-b pb-2">Join the Season</h2>
                        
                        {status === 'success' ? (
                            <div className="text-green-600 text-center py-8">
                                <p className="text-4xl mb-4">🎉</p>
                                <p className="text-xl font-bold">Registration Successful!</p>
                                <p className="text-gray-600 mt-2">{message}</p>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Display Name <span className="text-red-500">*</span></label>
                                    <input 
                                        type="text" 
                                        name="displayName"
                                        required
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm p-3 border"
                                        placeholder="Enter your display name"
                                        value={formData.displayName}
                                        onChange={handleInputChange}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Team Name <span className="text-gray-400">(Optional)</span></label>
                                    <input 
                                        type="text" 
                                        name="teamName"
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm p-3 border"
                                        placeholder="Enter a cool team name"
                                        value={formData.teamName}
                                        onChange={handleInputChange}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Email Address <span className="text-red-500">*</span></label>
                                    <input 
                                        type="email" 
                                        name="email"
                                        required
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm p-3 border"
                                        placeholder="you@example.com"
                                        value={formData.email}
                                        onChange={handleInputChange}
                                    />
                                    <p className="text-xs text-gray-500 mt-1">Required for season updates and prize notifications.</p>
                                </div>

                                {status === 'error' && (
                                    <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                                        {message}
                                    </div>
                                )}

                                <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
                                    <button 
                                        type="button"
                                        onClick={() => setIsModalOpen(false)}
                                        className="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium"
                                    >
                                        Cancel
                                    </button>
                                    <button 
                                        type="submit"
                                        disabled={status === 'submitting'}
                                        className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 font-bold shadow-md transition-all"
                                    >
                                        {status === 'submitting' ? 'Joining...' : 'Confirm & Join'}
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MyTeam;