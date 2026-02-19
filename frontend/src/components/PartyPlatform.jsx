import React from 'react';
import { Link } from 'react-router-dom';

const PartyPlatform = () => {
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
                <Link to="/party" className="bg-red-800 text-white px-3 py-2 rounded-md text-sm font-medium transition">Party Platform</Link>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 flex-grow">
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h1 className="text-3xl font-extrabold text-gray-900">🏏 Fantasy Parliament Party</h1>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">Our platform. Our vision. Our Parliament.</p>
          </div>
          <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
            
            <section className="mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">About Our Party</h2>
              <p className="text-gray-600 mb-4">
                The Fantasy Parliament Party represents players who want real reform in Canadian politics. 
                We believe in common-sense solutions, transparency, and putting citizens first.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">🎯 Core Platform Issues</h2>
              
              <div className="space-y-6">
                <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-red-600">
                  <h3 className="font-bold text-lg mb-2">1. Recall Act</h3>
                  <p className="text-gray-600 mb-2">
                    <strong>The Problem:</strong> MPs can vote against their constituents' interests and face no consequences until the next election—years later.
                  </p>
                  <p className="text-gray-600 mb-2">
                    <strong>Our Solution:</strong> Implement a federal Recall Act allowing constituents to trigger a by-election if their MP betrays the trust of voters. 
                    If enough signatures are collected (25% of riding), the MP faces immediate recall vote.
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-red-600">
                  <h3 className="font-bold text-lg mb-2">2. Electoral Reform - One Person, One Vote</h3>
                  <p className="text-gray-600 mb-2">
                    <strong>The Problem:</strong> The current electoral system is rigged. A vote in a tiny rural riding is worth 3-4x more than a vote in a dense urban riding. 
                    This is undemocratic and undermines true representation.
                  </p>
                  <p className="text-gray-600 mb-2">
                    <strong>Our Solution:</strong> Implement proportional representation with equal-sized ridings. 
                    No Canadian's vote should be worth more than another's. We will fight for a system that truly represents all Canadians equally.
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-gray-400">
                  <h3 className="font-bold text-lg mb-2">3. Lower Taxes for Working Canadians</h3>
                  <p className="text-gray-600">
                    Reduce the tax burden on middle-class families. Close loopholes that let wealthy corporations and individuals escape their fair share.
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-gray-400">
                  <h3 className="font-bold text-lg mb-2">4. Common-Sense Justice</h3>
                  <p className="text-gray-600">
                    Balance the rights of victims with rehabilitation. Ensure our justice system actually serves and protects law-abiding Canadians.
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-gray-400">
                  <h3 className="font-bold text-lg mb-2">5. Protect Canadian Sovereignty</h3>
                  <p className="text-gray-600">
                    Put Canadian interests first in trade deals. Ensure our country controls its own destiny.
                  </p>
                </div>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">💪 Our Values</h2>
              <ul className="list-disc list-inside text-gray-600 space-y-2">
                <li><strong>Transparency:</strong> Open government, accessible records, honest politicians</li>
                <li><strong>Accountability:</strong> Politicians should answer to the people, not party bosses</li>
                <li><strong>Fairness:</strong> Every Canadian deserves equal representation and opportunity</li>
                <li><strong>Common Sense:</strong> Practical solutions over ideological purity</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-4">Join the Movement</h2>
              <p className="text-gray-600 mb-4">
                Help us bring real reform to Canadian politics. Together we can build a better Parliament that actually represents Canadians.
              </p>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800 font-medium">
                  🏏 Play Fantasy Parliament. Demand Real Reform!
                </p>
              </div>
            </section>

          </div>
        </div>
      </main>

      <footer className="bg-gray-800 text-white py-6">
        <div className="max-w-4xl mx-auto px-4 text-center text-sm text-gray-400">
          <p>© 2026 Fantasy Parliament Party. Not affiliated with any real political party.</p>
          <p className="mt-2">Built with ❤️ for Fantasy Parliament players.</p>
        </div>
      </footer>
    </div>
  );
};

export default PartyPlatform;
