import React, { useState } from 'react';

function Admin() {
  const [key, setKey] = useState(localStorage.getItem('fp_admin_key') || '');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  const saveKey = (e) => {
    const newKey = e.target.value;
    setKey(newKey);
    localStorage.setItem('fp_admin_key', newKey);
  };

  const runAction = async (endpoint) => {
    setLoading(true);
    setStatus(`Running ${endpoint}...`);
    try {
      const response = await fetch(`https://fantasy-parliament-web.onrender.com/admin/${endpoint}`, {
        method: 'POST',
        headers: { 'x-api-key': key }
      });
      const data = await response.json();
      setStatus(JSON.stringify(data, null, 2));
    } catch (e) {
      setStatus(`Error: ${e.message}`);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-2xl mx-auto bg-gray-800 rounded-xl shadow-2xl p-8 border border-red-900/50">
        <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-black uppercase tracking-tighter text-red-500">System Admin</h1>
            <a href="/" className="text-sm bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition">Back to App</a>
        </div>

        <div className="mb-8">
          <label className="block text-xs font-bold uppercase text-gray-400 mb-2">Sync API Key</label>
          <input
            type="password"
            value={key}
            onChange={saveKey}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:border-red-500 transition"
            placeholder="Enter SYNC_API_KEY"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <button
            onClick={() => runAction('migrate')}
            disabled={loading || !key}
            className="bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-bold py-4 rounded-xl shadow-lg shadow-red-900/20 transition-all active:scale-95"
          >
            Trigger Migrations
          </button>
          <button
            onClick={() => runAction('sync')}
            disabled={loading || !key}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-bold py-4 rounded-xl shadow-lg shadow-blue-900/20 transition-all active:scale-95"
          >
            Trigger Data Sync
          </button>
        </div>

        {status && (
          <div className="bg-black/50 rounded-xl p-6 border border-gray-700">
            <h3 className="text-xs font-bold text-gray-500 uppercase mb-4">Console Output</h3>
            <pre className="font-mono text-sm text-green-400 whitespace-pre-wrap leading-relaxed">
              {status}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default Admin;
