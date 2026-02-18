import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

// Mock Parliament events - in production, fetch from OpenParliament.ca API
// Hardcoded Parliament schedule - should be fetched from API in production
// Last actual score: 2026-02-14 (recess since then)
const PARLIAMENT_EVENTS = [
  { date: '2026-02-16', type: 'recess', title: 'Parliament Recess', description: 'No scheduled sittings' },
  { date: '2026-02-17', type: 'recess', title: 'Parliament Recess', description: 'No scheduled sittings' },
  { date: '2026-02-18', type: 'recess', title: 'Parliament Recess', description: 'No scheduled sittings' },
  { date: '2026-02-19', type: 'recess', title: 'Parliament Recess', description: 'No scheduled sittings' },
  { date: '2026-02-20', type: 'recess', title: 'Parliament Recess', description: 'No scheduled sittings' },
  { date: '2026-02-21', type: 'break', title: 'No Sitting', description: 'Weekend' },
  { date: '2026-02-22', type: 'break', title: 'No Sitting', description: 'Weekend' },
  { date: '2026-02-23', type: 'recess', title: 'Parliament Recess', description: 'Winter break continues' },
];

function getParliamentSchedule() {
  const schedule = [];
  const today = new Date();
  
  for (let i = 0; i < 56; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    
    const dayOfWeek = date.getDay();
    const dateStr = date.toISOString().split('T')[0];
    
    // Parliament sits Monday-Friday (1-5)
    if (dayOfWeek >= 1 && dayOfWeek <= 5) {
      const saturday = new Date(date);
      saturday.setDate(date.getDate() + (6 - dayOfWeek));
      
      if (saturday > today) {
        schedule.push({
          sittingDate: dateStr,
          processingDate: saturday.toISOString().split('T')[0],
          dayName: date.toLocaleDateString('en-CA', { weekday: 'long' }),
          sittingDateFormatted: date.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' }),
          processingDateFormatted: saturday.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' }),
        });
      }
    }
  }
  
  const uniqueSaturdays = [];
  const seen = new Set();
  for (const item of schedule) {
    if (!seen.has(item.processingDate)) {
      uniqueSaturdays.push(item);
      seen.add(item.processingDate);
    }
  }
  
  return uniqueSaturdays;
}

function Schedule() {
  const [schedule, setSchedule] = useState([]);
  const username = localStorage.getItem('fp_username');
  
  useEffect(() => {
    setSchedule(getParliamentSchedule());
  }, []);
  
  const nextProcessingDate = schedule.length > 0 ? schedule[0].processingDate : null;
  
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
                <Link to="/my-team" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">My Team</Link>
                <Link to="/rules" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Rules</Link>
                <Link to="/schedule" className="bg-red-800 px-3 py-2 rounded-md text-sm font-medium">Schedule</Link>
                <Link to="/compare" className="text-red-100 hover:bg-red-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Compare</Link>
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Parliament Schedule</h1>
          <p className="mt-2 text-gray-600">
            Scores are processed Saturday mornings based on the previous week's parliamentary activity.
          </p>
        </div>
        
        {nextProcessingDate && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-8">
            <p className="text-red-700 font-medium">
              Next score processing: Saturday, {new Date(nextProcessingDate + 'T00:00:00').toLocaleDateString('en-CA', { month: 'long', day: 'numeric' })}
            </p>
          </div>
        )}
        
        {/* Parliament Activity Section */}
        <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-100 mb-8">
          <div className="px-4 py-5 sm:px-6 bg-blue-50 border-b">
            <h2 className="text-lg font-medium text-gray-900">📅 This Week in Parliament</h2>
            <p className="text-sm text-gray-500 mt-1">Expected activity (based on standard sitting schedule)</p>
          </div>
          <ul className="divide-y divide-gray-200">
            {PARLIAMENT_EVENTS.map((event, idx) => (
              <li key={idx} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                <div className="flex items-start">
                  <div className={`flex-shrink-0 w-3 h-3 rounded-full mt-2 mr-3 ${event.type === 'sitting' ? 'bg-green-500' : event.type === 'recess' ? 'bg-yellow-500' : 'bg-gray-300'}`}></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{event.title}</p>
                    <p className="text-sm text-gray-500">{event.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-700">{new Date(event.date + 'T00:00:00').toLocaleDateString('en-CA', { month: 'short', day: 'numeric' })}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          <div className="bg-gray-50 px-4 py-3 text-xs text-gray-500 text-center">
            * Actual schedule may vary. Check <a href="https://www.ourcommons.ca" target="_blank" rel="noopener" className="text-blue-600 hover:underline">ourcommons.ca</a> for real-time schedule.
          </div>
        </div>
        
        {/* Processing Dates */}
        <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-100">
          <div className="px-4 py-5 sm:px-6 bg-gray-50 border-b">
            <h2 className="text-lg font-medium text-gray-900">📊 Score Processing Dates</h2>
            <p className="text-sm text-gray-500 mt-1">Saturdays when Fantasy Parliament scores update</p>
          </div>
          <ul className="divide-y divide-gray-200">
            {schedule.slice(0, 12).map((item, idx) => (
              <li key={idx} className="px-4 py-4 sm:px-6 hover:bg-gray-50 transition">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Week of {item.sittingDateFormatted}
                    </p>
                    <p className="text-sm text-gray-500">
                      Sitting days: Mon-Fri
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-red-600">
                      → {item.processingDateFormatted}
                    </p>
                    <p className="text-xs text-gray-400">Saturday AM</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
        
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Schedule is calculated based on standard Parliament sitting days (Monday-Friday).</p>
          <p className="mt-1">Actual processing may vary during parliamentary breaks.</p>
        </div>
      </main>

      <footer className="mt-auto py-8 text-center text-gray-400 text-sm">
        &copy; 2026 Fantasy Parliament League. Data powered by OpenParliament.
      </footer>
    </div>
  );
}

export default Schedule;
