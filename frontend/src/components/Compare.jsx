import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Compare = () => {
  const [mp1, setMp1] = useState(null);
  const [mp2, setMp2] = useState(null);
  const [search1, setSearch1] = useState('');
  const [search2, setSearch2] = useState('');
  const [results1, setResults1] = useState([]);
  const [results2, setResults2] = useState([]);
  const [loading1, setLoading1] = useState(false);
  const [loading2, setLoading2] = useState(false);
  const navigate = useNavigate();

  const searchMPs = async (query, setResults, setLoading) => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`https://fantasy-parliament-web.onrender.com/mps/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setResults(data.slice(0, 8));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchMpDetails = async (id, setMp) => {
    try {
      const response = await fetch(`https://fantasy-parliament-web.onrender.com/mps/${id}`);
      const data = await response.json();
      setMp(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelect1 = (mp) => {
    setMp1(mp);
    setResults1([]);
    setSearch1(mp.name);
    fetchMpDetails(mp.id, setMp1);
  };

  const handleSelect2 = (mp) => {
    setMp2(mp);
    setResults2([]);
    setSearch2(mp.name);
    fetchMpDetails(mp.id, setMp2);
  };

  useEffect(() => {
    const debounce = setTimeout(() => searchMPs(search1, setResults1, setLoading1), 300);
    return () => clearTimeout(debounce);
  }, [search1]);

  useEffect(() => {
    const debounce = setTimeout(() => searchMPs(search2, setResults2, setLoading2), 300);
    return () => clearTimeout(debounce);
  }, [search2]);

  const StatBar = ({ label, val1, val2, color1 = "bg-red-500", color2 = "bg-blue-500" }) => {
    const max = Math.max(val1, val2, 1);
    return (
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden flex">
            <div className={`${color1} h-4`} style={{ width: `${(val1 / max) * 100}%` }}></div>
          </div>
          <span className="text-xs font-bold w-8 text-right">{val1}</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden flex">
            <div className={`${color2} h-4`} style={{ width: `${(val2 / max) * 100}%` }}></div>
          </div>
          <span className="text-xs font-bold w-8 text-right">{val2}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
      <nav className="bg-red-700 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="text-xl font-black tracking-tighter uppercase">Fantasy <span className="text-red-200">Parliament</span></Link>
          <div className="flex items-center space-x-4">
            <Link to="/" className="text-red-100 hover:text-white text-sm">Dashboard</Link>
            <Link to="/my-team" className="text-red-100 hover:text-white text-sm">My Team</Link>
            <Link to="/rules" className="text-red-100 hover:text-white text-sm">Rules</Link>
            <Link to="/schedule" className="text-red-100 hover:text-white text-sm">Schedule</Link>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-6">MP Comparison</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {/* MP 1 Search */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-2">Select MP 1</label>
            <input
              type="text"
              value={search1}
              onChange={(e) => setSearch1(e.target.value)}
              placeholder="Search MPs..."
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
            />
            {results1.length > 0 && (
              <div className="absolute z-10 w-full bg-white border rounded-lg shadow-lg mt-1 max-h-60 overflow-y-auto">
                {results1.map(mp => (
                  <button
                    key={mp.id}
                    onClick={() => handleSelect1(mp)}
                    className="w-full text-left px-4 py-2 hover:bg-red-50 flex items-center gap-2"
                  >
                    {mp.image_url && <img src={mp.image_url} className="w-8 h-8 rounded-full" alt="" />}
                    <div>
                      <div className="font-medium">{mp.name}</div>
                      <div className="text-xs text-gray-500">{mp.party} • {mp.constituency}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* MP 2 Search */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-2">Select MP 2</label>
            <input
              type="text"
              value={search2}
              onChange={(e) => setSearch2(e.target.value)}
              placeholder="Search MPs..."
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
            {results2.length > 0 && (
              <div className="absolute z-10 w-full bg-white border rounded-lg shadow-lg mt-1 max-h-60 overflow-y-auto">
                {results2.map(mp => (
                  <button
                    key={mp.id}
                    onClick={() => handleSelect2(mp)}
                    className="w-full text-left px-4 py-2 hover:bg-blue-50 flex items-center gap-2"
                  >
                    {mp.image_url && <img src={mp.image_url} className="w-8 h-8 rounded-full" alt="" />}
                    <div>
                      <div className="font-medium">{mp.name}</div>
                      <div className="text-xs text-gray-500">{mp.party} • {mp.constituency}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {mp1 && mp2 && (
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
            <div className="grid grid-cols-3 bg-gray-50 border-b">
              <div className="p-4 text-center">
                <img src={mp1.image_url} alt={mp1.name} className="w-20 h-20 rounded-full mx-auto mb-2 object-cover" />
                <h3 className="font-bold text-lg">{mp1.name}</h3>
                <p className="text-sm text-gray-600">{mp1.party}</p>
              </div>
              <div className="p-4 flex items-center justify-center">
                <span className="text-2xl font-black text-gray-300">VS</span>
              </div>
              <div className="p-4 text-center">
                <img src={mp2.image_url} alt={mp2.name} className="w-20 h-20 rounded-full mx-auto mb-2 object-cover" />
                <h3 className="font-bold text-lg">{mp2.name}</h3>
                <p className="text-sm text-gray-600">{mp2.party}</p>
              </div>
            </div>

            <div className="p-6">
              <h4 className="font-bold text-xl mb-4 text-center">Score Comparison</h4>
              
              <StatBar label="Total Score" val1={mp1.score} val2={mp2.score} />
              
              {mp1.score_breakdown && mp2.score_breakdown && (
                <>
                  <StatBar label="Speeches" val1={mp1.score_breakdown.speeches || 0} val2={mp2.score_breakdown.speeches || 0} color1="bg-red-400" color2="bg-blue-400" />
                  <StatBar label="Votes" val1={mp1.score_breakdown.votes || 0} val2={mp2.score_breakdown.votes || 0} color1="bg-red-300" color2="bg-blue-300" />
                  <StatBar label="Bills" val1={mp1.score_breakdown.bills || 0} val2={mp2.score_breakdown.bills || 0} color1="bg-red-200" color2="bg-blue-200" />
                </>
              )}
            </div>
          </div>
        )}

        {(!mp1 || !mp2) && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">Select two MPs to compare their stats</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default Compare;
