import React from 'react';
import Scoreboard from './components/Scoreboard';
import DraftPool from './components/DraftPool';

function App() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      {/* Navigation */}
      <nav className="bg-indigo-900 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <span className="text-xl font-black tracking-tighter uppercase">Fantasy <span className="text-indigo-400">Parliament</span></span>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <a href="#" className="bg-indigo-800 px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>
                <a href="#" className="text-indigo-300 hover:bg-indigo-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">My Team</a>
                <a href="#" className="text-indigo-300 hover:bg-indigo-800 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition">Rules</a>
              </div>
            </div>
            <div className="flex items-center">
                <div className="bg-indigo-800 p-2 rounded-full h-8 w-8 flex items-center justify-center font-bold text-xs">JD</div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">MP Dashboard</h1>
          <p className="text-slate-500 mt-2">Manage your fantasy team and track the latest parliamentary performance stats.</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content Area - Draft Pool */}
          <div className="lg:col-span-2">
            <DraftPool />
          </div>

          {/* Sidebar Area - Scoreboard */}
          <div className="lg:col-span-1">
            <Scoreboard />
          </div>
        </div>
      </main>

      <footer className="mt-auto py-8 text-center text-slate-400 text-sm">
        &copy; 2026 Fantasy Parliament League. Data powered by OpenParliament.
      </footer>
    </div>
  );
}

export default App;
