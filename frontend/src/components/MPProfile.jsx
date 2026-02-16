import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

const MPProfile = () => {
  const { id } = useParams();
  const [mp, setMp] = useState(null);
  const [scoreHistory, setScoreHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch MP details
        const mpResponse = await fetch(`https://fantasy-parliament-web.onrender.com/mps/${id}`);
        if (!mpResponse.ok) {
          throw new Error('Failed to fetch MP data');
        }
        const mpData = await mpResponse.json();
        setMp(mpData);
        
        // Fetch score history
        const historyResponse = await fetch(`https://fantasy-parliament-web.onrender.com/mps/${id}/scores`);
        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          setScoreHistory(historyData.scores || []);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) return <div className="p-8 text-center">Loading profile...</div>;
  if (error) return <div className="p-8 text-center text-red-600">Error: {error}</div>;
  if (!mp) return null;

  const breakdown = mp.score_breakdown || {};
  
  // Calculate max points for chart scaling
  const maxPoints = Math.max(...scoreHistory.map(s => s.points), 1);
  
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

      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-100">
            {/* Header */}
            <div className="bg-red-700 p-6 text-white flex items-center space-x-6">
                {mp.image_url ? (
                    <img src={mp.image_url} alt={mp.name} className="w-24 h-24 rounded-full border-4 border-red-200 object-cover bg-white" />
                ) : (
                    <div className="w-24 h-24 rounded-full bg-gray-300 flex items-center justify-center text-3xl font-bold text-gray-600">
                        {mp.name.charAt(0)}
                    </div>
                )}
                <div>
                    <h1 className="text-3xl font-bold">{mp.name}</h1>
                    <p className="text-xl text-red-100">{mp.party} • {mp.constituency}</p>
                    <div className="mt-2 inline-block bg-red-800 px-3 py-1 rounded-md text-lg font-mono">
                        Score: {mp.score}
                    </div>
                </div>
            </div>

            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Stats Column */}
                <div>
                    <h2 className="text-xl font-bold mb-4 text-gray-800 border-b pb-2">Performance Stats</h2>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span className="text-gray-600">Speeches (7 days)</span>
                            <span className="font-bold text-gray-900">{breakdown.speeches || 0}</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span className="text-gray-600">Votes Attended</span>
                            <span className="font-bold text-gray-900">{Math.floor((breakdown.votes || 0) / 2)}</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span className="text-gray-600">Bill Activity</span>
                            <span className="font-bold text-gray-900">{breakdown.bills || 0} pts</span>
                        </div>
                    </div>
                </div>

                {/* Committee Column */}
                <div>
                    <h2 className="text-xl font-bold mb-4 text-gray-800 border-b pb-2">Committee Assignments</h2>
                    {mp.committees && mp.committees.length > 0 ? (
                        <ul className="space-y-2">
                            {mp.committees.map((c, idx) => (
                                <li key={idx} className="flex justify-between items-center p-3 border rounded-lg">
                                    <span className="font-medium text-gray-800">{c.name}</span>
                                    <span className={`text-xs px-2 py-1 rounded ${c.role === 'Chair' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                                        {c.role}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-gray-500 italic">No committee assignments found.</p>
                    )}
                    
                    {breakdown.committees > 0 && (
                        <div className="mt-4 p-3 bg-blue-50 border border-blue-100 rounded-lg text-blue-800">
                            <strong>Committee Bonus:</strong> +{breakdown.committees} points
                        </div>
                    )}
                </div>
            </div>
            
            {/* Score History Chart */}
            {scoreHistory.length > 0 && (
                <div className="p-6 bg-gray-50 border-t">
                    <h3 className="text-lg font-bold mb-4 text-gray-700">Score History</h3>
                    <div className="flex items-end justify-between gap-1 h-32">
                        {scoreHistory.slice(-14).map((score, idx) => (
                            <div key={idx} className="flex-1 flex flex-col items-center">
                                <div 
                                    className="w-full bg-red-500 rounded-t transition hover:bg-red-600"
                                    style={{ height: `${(score.points / maxPoints) * 100}%`, minHeight: score.points > 0 ? '4px' : '0' }}
                                    title={`${score.date}: ${score.points} pts`}
                                ></div>
                                <span className="text-[8px] text-gray-400 mt-1 transform -rotate-45 origin-left whitespace-nowrap">
                                    {score.date.slice(5)}
                                </span>
                            </div>
                        ))}
                    </div>
                    <p className="text-xs text-gray-400 mt-2 text-center">Last 14 scoring days</p>
                </div>
            )}
            
            {/* Score Breakdown Visual */}
            <div className="p-6 bg-gray-50 border-t">
                <h3 className="text-lg font-bold mb-2 text-gray-700">Score Breakdown</h3>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden flex">
                    <div className="bg-red-500 h-4" style={{ width: `${(breakdown.speeches || 0) / (mp.score || 1) * 100}%` }} title="Speeches"></div>
                    <div className="bg-blue-500 h-4" style={{ width: `${(breakdown.votes || 0) / (mp.score || 1) * 100}%` }} title="Votes"></div>
                    <div className="bg-green-500 h-4" style={{ width: `${(breakdown.bills || 0) / (mp.score || 1) * 100}%` }} title="Bills"></div>
                    <div className="bg-yellow-500 h-4" style={{ width: `${(breakdown.committees || 0) / (mp.score || 1) * 100}%` }} title="Committees"></div>
                </div>
                <div className="flex text-xs mt-2 space-x-4">
                    <span className="flex items-center"><div className="w-3 h-3 bg-red-500 mr-1"></div> Speeches</span>
                    <span className="flex items-center"><div className="w-3 h-3 bg-blue-500 mr-1"></div> Votes</span>
                    <span className="flex items-center"><div className="w-3 h-3 bg-green-500 mr-1"></div> Bills</span>
                    <span className="flex items-center"><div className="w-3 h-3 bg-yellow-500 mr-1"></div> Committees</span>
                </div>
            </div>
        </div>
      </main>
    </div>
  );
};

export default MPProfile;
