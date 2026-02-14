import React from 'react';
import { Link } from 'react-router-dom';

const Rules = () => {
  const username = localStorage.getItem('fp_username');

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
                <Link to="/rules" className="bg-red-800 px-3 py-2 rounded-md text-sm font-medium">Rules</Link>
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
                <li><strong>Draft Your Team:</strong> You must select 1 <strong>Captain</strong> and 4 <strong>Team Members</strong> (5 MPs total).</li>
                <li><strong>Locked Rosters:</strong> Once you join the season, your team is locked. You cannot trade or change MPs during the season.</li>
                <li><strong>Scoring:</strong> Your score is determined by the real-world performance of your MPs in Parliament (attendance, votes, etc.).</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Joining the Season</h2>
              <ol className="list-decimal pl-5 space-y-2 text-gray-700">
                <li>Click the <strong>"Join the Season"</strong> button on the home page.</li>
                <li>Enter your <strong>Display Name</strong>, optional Team Name, and Email.</li>
                <li>Browse the Draft Pool and select your MPs. Remember, your Captain earns bonus points!</li>
              </ol>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Scoring System</h2>
              <p className="text-gray-700 mb-2">MPs earn points based on their activity in the House of Commons:</p>
              <ul className="list-disc pl-5 space-y-2 text-gray-700">
                <li><strong>Speeches:</strong> Earn points for every speech or intervention in the House.</li>
                <li><strong>Votes:</strong> Earn points for participating in official votes.</li>
                <li><strong>Sponsorships:</strong> Earn points for sponsoring or supporting bills.</li>
              </ul>
              <p className="text-gray-700 mt-4">
                <strong>Weekly vs. Season Scoring:</strong> Data is synchronized daily from OpenParliament.ca. The league tracks performance on a rolling 7-day window.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Leaderboard</h2>
              <p className="text-gray-700">
                Submit your team's total score to the global anonymous leaderboard to compete against other "Political Junkies" across Canada. Rankings are updated in real-time as scores are submitted.
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
