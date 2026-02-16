import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const PARTIES = ['All', 'Liberal', 'Conservative', 'NDP', 'Bloc', 'Green'];

const DraftPool = ({ onDraft }) => {
    const [mps, setMps] = useState([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeParty, setActiveParty] = useState('All');

    const fetchMPs = async (query = '', party = 'All') => {
        setLoading(true);
        try {
            let url = `https://fantasy-parliament-web.onrender.com/mps/search`;
            if (query) {
                url += `?q=${encodeURIComponent(query)}`;
            }
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to fetch MPs');
            }
            let data = await response.json();
            
            // Filter by party client-side (API doesn't support party filtering yet)
            if (party && party !== 'All') {
                data = data.filter(mp => mp.party === party);
            }
            
            setMps(data);
            setLoading(false);
        } catch (err) {
            setError(err.message);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMPs(search, activeParty);
    }, []);

    const handleSearchChange = (e) => {
        setSearch(e.target.value);
    };

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        fetchMPs(search, activeParty);
    };

    const handlePartyFilter = (party) => {
        setActiveParty(party);
        fetchMPs(search, party);
    };

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 h-full">
            <h2 className="text-2xl font-bold mb-6 text-red-700 border-b pb-2">Draft Pool</h2>
            
            {/* Party Filter */}
            <div className="mb-4">
                <p className="text-sm text-gray-500 mb-2">Filter by party:</p>
                <div className="flex flex-wrap gap-2">
                    {PARTIES.map(party => (
                        <button
                            key={party}
                            onClick={() => handlePartyFilter(party)}
                            className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                                activeParty === party 
                                    ? 'bg-red-600 text-white' 
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                        >
                            {party}
                        </button>
                    ))}
                </div>
            </div>
            
            <form onSubmit={handleSearchSubmit} className="mb-6">
                <div className="relative">
                    <input 
                        type="text" 
                        value={search}
                        onChange={handleSearchChange}
                        placeholder="Search MPs by name, party, or riding..."
                        className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition"
                    />
                    <button 
                        type="submit"
                        className="absolute right-2 top-2 bg-red-600 text-white px-4 py-1 rounded-md hover:bg-red-700 transition"
                    >
                        Search
                    </button>
                </div>
            </form>

            {loading ? (
                <div className="text-center py-10 text-gray-500">Loading MPs...</div>
            ) : error ? (
                <div className="text-center py-10 text-red-500 font-medium">{error}</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[600px] overflow-y-auto pr-2">
                    {mps.map((mp) => (
                        <div key={mp.id} className="border border-gray-100 p-4 rounded-lg hover:border-red-200 hover:shadow-sm transition group cursor-pointer flex gap-4 items-center">
                            {mp.image_url && (
                                <Link to={`/mp/${mp.id}`}>
                                    <img 
                                        src={mp.image_url} 
                                        alt={mp.name} 
                                        className="w-16 h-16 rounded-full object-cover border-2 border-gray-100 bg-gray-50 flex-shrink-0" 
                                        onError={(e) => {e.target.style.display = 'none'}}
                                    />
                                </Link>
                            )}
                            <div className="flex-1">
                                <Link to={`/mp/${mp.id}`} className="font-bold text-gray-800 group-hover:text-red-600 transition">
                                    {mp.name}
                                </Link>
                                <p className="text-sm text-gray-600">{mp.party}</p>
                                <p className="text-xs text-gray-400">{mp.constituency}</p>
                            </div>
                            <div className="flex-shrink-0 flex flex-col gap-2">
                                <Link 
                                    to={`/mp/${mp.id}`}
                                    className="text-xs text-gray-500 hover:text-gray-800 underline"
                                >
                                    View
                                </Link>
                                <button 
                                    onClick={() => onDraft(mp)}
                                    className="text-xs bg-red-50 text-red-600 px-2 py-1 rounded font-semibold hover:bg-red-600 hover:text-white transition"
                                >
                                    + Draft
                                </button>
                            </div>
                        </div>
                    ))}
                    {mps.length === 0 && <p className="text-gray-500 text-center col-span-2">No MPs found matching your search.</p>}
                </div>
            )}
        </div>
    );
};

export default DraftPool;
