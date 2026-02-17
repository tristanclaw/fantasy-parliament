import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const Rules = () => {
  const username = localStorage.getItem('fp_username');
  const [committeeData, setCommitteeData] = useState(null);

  useEffect(() => {
    // Fetch committee tier data
    fetch('https://fantasy-parliament-web.onrender.com/committees')
      .then(res => res.json())
      .then(data => setCommitteeData(data))
      .catch(err => console.error('Failed to load committee data:', err));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900 flex flex-col">
      <nav className="bg-red-700 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-black tracking-tighter uppercase">Fantasy <span className="text-red-200">Parliament</span></Link>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link to="/" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Dashboard</Link>
                <a href="#" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">My Team</a>
                <Link to="/rules" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Rules</Link>
                <Link to="/schedule" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Schedule</Link>
              </div>
            </div>
            <div className="flex items-center space-x-2">
                <span className="text-red-200 text-sm font-medium">{username ? `Welcome, ${username}` : 'Guest'}</span>
                <div className="bg-red-800 p-2 rounded-full h-8 w-8 flex items-center justify-center font-bold text-xs">
                    {username ? username.substring(0,2).toUpperCase() : '??'}
                </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 flex-grow">
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h1 className="text-3xl font-extrabold text-gray-900">Official Rules</h1>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">Everything you need to know to play Fantasy Parliament.</p>
          </div>
          <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
            
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. How to Play</h2>
              <ul className="list-disc pl-5 space-y-2 text-gray-700">
                <li><strong>The Core Five:</strong> You draft a team of <strong>5 MPs</strong> total (1 Captain + 4 Members).</li>
                <li><strong>Locked Rosters:</strong> Once you join the season, your team is locked for the duration of the current session.</li>
                <li><strong>Scoring:</strong> Your score is determined by the real-world performance of your MPs in the House of Commons.</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Scoring System</h2>
              <p className="text-gray-700 mb-4">MPs earn points for showing up and speaking out:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                  <p className="font-bold text-red-800">Speeches: +1 pt</p>
                  <p className="text-sm text-red-600">Every intervention in the House.</p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                  <p className="font-bold text-red-800">Votes: +2 pts</p>
                  <p className="text-sm text-red-600">Participation in official votes.</p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                  <p className="font-bold text-red-800">Bill Sponsored: +10 pts</p>
                  <p className="text-sm text-red-600">Introducing or sponsoring a bill.</p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                  <p className="font-bold text-red-800">The Grand Slam: +50 pts</p>
                  <p className="text-sm text-red-600">Bill receives Royal Assent.</p>
                </div>
              </div>
              <p className="text-gray-700 mt-6">
                <strong>The 7-Day Rolling Window:</strong> Your total score is a "snapshot" of your team's activity over the last 7 days. If an MP stops speaking or voting, their older points "expire" from your total. To stay at the top, you need a team that is consistently active in the House! Data syncs daily from OpenParliament.ca.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Committee Scoring (NEW!)</h2>
              <p className="text-gray-700 mb-4">
                Not all committees are created equal! MPs on prestigious committees earn bonus points based on committee tier:
              </p>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tier</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Weight</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Committees</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    <tr>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">A-Tier</span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">2.0x</td>
                      <td className="px-4 py-3 text-sm text-gray-500">Finance, Foreign Affairs, Defence, Treasury Board, Public Accounts</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">B-Tier</span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">1.5x</td>
                      <td className="px-4 py-3 text-sm text-gray-500">Health, Justice, Industry, Transport, Environment, Veterans, Immigration</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-orange-100 text-orange-800">C-Tier</span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">1.0x</td>
                      <td className="px-4 py-3 text-sm text-gray-500">Agriculture, Heritage, Employment, Fisheries, Natural Resources, etc.</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="mt-4 bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-700"><strong>Base Points:</strong> 10 points per committee</p>
                <p className="text-sm text-gray-700"><strong>Role Multipliers:</strong> Chair = 1.5x, Vice-Chair = 1.25x, Member = 1.0x</p>
                <p className="text-sm text-gray-500 mt-2">
                  <em>Example: An MP on Finance Committee (A-Tier) as Chair gets 10 × 2.0 × 1.5 = <strong>30 points</strong> per scoring period!</em>
                </p>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Leaderboards & Benchmarks</h2>
              <p className="text-gray-700">
                Compete on the global leaderboard against other users, or measure yourself against <strong>Special Teams</strong> like the "Party Leaders" squad. If your local MPs outscore the opposition leaders, you're winning the civic game.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. General Rules</h2>
              <ul className="list-disc pl-5 space-y-2 text-gray-700">
                <li><strong>Local-First:</strong> Your team is stored in your browser's local storage. No accounts required.</li>
                <li><strong>Data Retention:</strong> Older data is pruned to keep the league fresh and the database efficient.</li>
              </ul>
            </section>
            
          </div>
        </div>
      </main>

      <footer className="mt-auto py-8 text-center text-gray-400 text-sm">
        &copy; 2026 Fantasy Parliament League. Data powered by OpenParliament.
      </footer>
    </div>
  );
};

export default Rules;
