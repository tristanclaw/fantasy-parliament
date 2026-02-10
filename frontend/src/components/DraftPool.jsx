import React, { useState, useEffect } from 'react';

const DraftPool = () => {
    const [mps, setMps] = useState([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchMPs = async (query = '') => {
        setLoading(true);
        try {
            const url = query 
                ? `https://fantasy-parliament-api.onrender.com/mps/search?q=${encodeURIComponent(query)}`
                : `https://fantasy-parliament-api.onrender.com/mps/search`; // Assuming default empty search works or adjustment needed
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to fetch MPs');
            }
            const data = await response.json();
            setMps(data);
            setLoading(false);
        } catch (err) {
            setError(err.message);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMPs();
    }, []);

    const handleSearchChange = (e) => {
        setSearch(e.target.value);
    };

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        fetchMPs(search);
    };

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 h-full">
            <h2 className="text-2xl font-bold mb-6 text-indigo-900 border-b pb-2">Draft Pool</h2>
            
            <form onSubmit={handleSearchSubmit} className="mb-6">
                <div className="relative">
                    <input 
                        type="text" 
                        value={search}
                        onChange={handleSearchChange}
                        placeholder="Search MPs by name, party, or riding..."
                        className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                    />
                    <button 
                        type="submit"
                        className="absolute right-2 top-2 bg-indigo-600 text-white px-4 py-1 rounded-md hover:bg-indigo-700 transition"
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
                        <div key={mp.id} className="border border-gray-100 p-4 rounded-lg hover:border-indigo-200 hover:shadow-sm transition group cursor-pointer">
                            <h3 className="font-bold text-gray-800 group-hover:text-indigo-600 transition">{mp.name}</h3>
                            <p className="text-sm text-gray-600">{mp.party}</p>
                            <p className="text-xs text-gray-400">{mp.constituency}</p>
                            <div className="mt-2 flex justify-end">
                                <button className="text-xs bg-indigo-50 text-indigo-600 px-2 py-1 rounded font-semibold hover:bg-indigo-600 hover:text-white transition">
                                    + Draft to Team
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
