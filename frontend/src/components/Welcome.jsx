import React, { useState } from 'react';

const Welcome = ({ onComplete }) => {
  const [step, setStep] = useState(1);
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMp, setSelectedMp] = useState(null);
  const [samePartyHandicap, setSamePartyHandicap] = useState(false);

  const handleNameSubmit = (e) => {
    e.preventDefault();
    if (displayName.trim() && email.trim()) setStep(2);
  };

  const searchRidings = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
        const response = await fetch(`https://fantasy-parliament-web.onrender.com/mps/search?q=${encodeURIComponent(searchQuery)}`);
        if (!response.ok) throw new Error("Search failed");
        const data = await response.json();
        setResults(data);
    } catch (err) {
        console.error("Failed to fetch MPs", err);
    } finally {
        setLoading(false);
    }
  };

  const confirmCaptain = () => {
    if (displayName && email && selectedMp) {
        onComplete(displayName, email, selectedMp, samePartyHandicap);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4 font-sans">
      <div className="max-w-md w-full bg-white rounded-xl shadow-2xl overflow-hidden border border-gray-100">
        <div className="bg-red-700 p-6 text-center">
            <h1 className="text-2xl font-black text-white uppercase tracking-tighter">Fantasy <span className="text-red-200">Parliament</span></h1>
            <p className="text-red-100 text-sm mt-1 font-medium">Official League Onboarding</p>
        </div>

        <div className="p-8">
            <div className="flex justify-center gap-2 mb-6">
                <div className={`h-2 w-12 rounded-full ${step >= 1 ? 'bg-red-600' : 'bg-gray-200'}`}></div>
                <div className={`h-2 w-12 rounded-full ${step >= 2 ? 'bg-red-600' : 'bg-gray-200'}`}></div>
            </div>

            {step === 1 && (
                <div className="animate-fade-in-up">
                    <h2 className="text-xl font-bold text-gray-900 mb-2">Welcome!</h2>
                    <p className="text-gray-500 text-sm mb-6">Let's get you set up. We need your name and email to track your score.</p>
                    <form onSubmit={handleNameSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-1">Display Name</label>
                            <input
                                type="text"
                                required
                                className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition bg-gray-50"
                                placeholder="e.g. PoliticalJunkie99"
                                value={displayName}
                                onChange={(e) => setDisplayName(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-1">Email Address</label>
                            <input
                                type="email"
                                required
                                className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition bg-gray-50"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>
                        <button
                            type="submit"
                            className="w-full bg-red-600 text-white font-bold py-3 rounded-lg hover:bg-red-700 transition shadow-md"
                        >
                            Continue
                        </button>
                    </form>
                </div>
            )}

            {step === 2 && (
                <div className="animate-fade-in-up space-y-6">
                    {!selectedMp ? (
                        <>
                            <div>
                                <h2 className="text-xl font-bold text-gray-900 mb-2">Local Representation</h2>
                                <p className="text-gray-500 text-sm mb-4">Find your local riding to draft your <strong>Team Captain</strong> automatically.</p>
                                
                                <label className="block text-xs font-bold text-gray-700 uppercase mb-2">Search Riding or MP Name</label>
                                <form onSubmit={searchRidings} className="flex gap-2">
                                    <input
                                        type="text"
                                        className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none bg-gray-50 transition"
                                        placeholder="e.g. Halifax, Pierre..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                    />
                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="bg-gray-800 text-white px-4 py-2 rounded-lg hover:bg-black transition font-bold text-sm"
                                    >
                                        {loading ? '...' : 'Search'}
                                    </button>
                                </form>
                            </div>

                            <div className="max-h-60 overflow-y-auto space-y-2 border-t border-gray-100 pt-2 custom-scrollbar">
                                {results.map(mp => (
                                    <button
                                        key={mp.id}
                                        onClick={() => setSelectedMp(mp)}
                                        className="w-full text-left p-3 rounded-lg border border-transparent hover:border-red-200 hover:bg-red-50 transition group flex justify-between items-center"
                                    >
                                        <div className="flex items-center gap-3">
                                            {mp.image_url && (
                                                <img 
                                                    src={mp.image_url} 
                                                    alt={mp.name} 
                                                    className="w-10 h-10 rounded-full object-cover bg-gray-100"
                                                    onError={(e) => {e.target.style.display = 'none'}}
                                                />
                                            )}
                                            <div>
                                                <div className="font-bold text-gray-800 group-hover:text-red-700">{mp.name}</div>
                                                <div className="text-xs text-gray-500">{mp.constituency}</div>
                                            </div>
                                        </div>
                                        <div className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded group-hover:bg-red-200 group-hover:text-red-800 flex-shrink-0 ml-2">
                                            {mp.party}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </>
                    ) : (
                        <div className="text-center space-y-5 animate-fade-in-up">
                            <h2 className="text-xl font-bold text-gray-900">Confirm Captain</h2>
                            <p className="text-gray-500 text-sm">Is this your local Member of Parliament?</p>

                            <div className="bg-gradient-to-br from-yellow-50 to-white border-2 border-yellow-400 rounded-xl p-6 shadow-sm relative overflow-hidden">
                                <div className="absolute top-0 right-0 bg-yellow-400 text-yellow-900 text-[10px] font-black px-2 py-1 rounded-bl">TEAM CAPTAIN</div>
                                {selectedMp.image_url && (
                                    <img 
                                        src={selectedMp.image_url} 
                                        alt={selectedMp.name} 
                                        className="w-24 h-24 rounded-full mx-auto mb-4 object-cover border-4 border-white shadow-sm bg-gray-100"
                                        onError={(e) => {e.target.style.display = 'none'}}
                                    />
                                )}
                                <h3 className="text-2xl font-bold text-gray-900 mb-1">{selectedMp.name}</h3>
                                <p className="text-sm font-medium text-gray-600 uppercase tracking-wide mb-3">{selectedMp.constituency}</p>
                                <span className="inline-block bg-gray-900 text-white text-xs font-bold px-3 py-1 rounded-full">
                                    {selectedMp.party}
                                </span>
                            </div>

                            <div className="flex items-center justify-center gap-2 py-3">
                                <input
                                    type="checkbox"
                                    id="handicap"
                                    checked={samePartyHandicap}
                                    onChange={(e) => setSamePartyHandicap(e.target.checked)}
                                    className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                                />
                                <label htmlFor="handicap" className="text-sm text-gray-700">
                                    Same party as captain <span className="text-gray-500">(handicap mode - harder to score, +50 bonus if enabled)</span>
                                </label>
                            </div>
                            
                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={() => setSelectedMp(null)}
                                    className="flex-1 px-4 py-3 rounded-lg border border-gray-300 text-gray-600 font-bold hover:bg-gray-50 transition text-sm"
                                >
                                    Back
                                </button>
                                <button
                                    onClick={confirmCaptain}
                                    className="flex-1 bg-red-600 text-white font-bold py-3 rounded-lg hover:bg-red-700 transition shadow-md hover:shadow-lg text-sm"
                                >
                                    Yes, Confirm
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
      </div>
    </div>
  );
};

export default Welcome;
