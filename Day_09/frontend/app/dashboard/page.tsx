import React from 'react';
import fs from 'fs';
import path from 'path';

export const revalidate = 0; // Disable static caching

export default function Dashboard() {
  let data = { total_calls: 0, successful_calls: 0, failed_calls: 0, calls: [] };
  
  try {
    const filePath = path.join(process.cwd(), '..', 'backend', 'analytics.json');
    if (fs.existsSync(filePath)) {
      const fileContents = fs.readFileSync(filePath, 'utf8');
      data = JSON.parse(fileContents);
    }
  } catch (error) {
    console.error("Error reading analytics file:", error);
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-white p-10 font-sans">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
          Call Analytics Dashboard
        </h1>
        <p className="text-neutral-400 mb-8">Real-time performance tracking for Dukaan Sathi.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 shadow-lg">
            <h3 className="text-neutral-400 text-sm font-medium mb-1">Total Calls</h3>
            <p className="text-5xl font-bold">{data.total_calls}</p>
          </div>
          
          <div className="bg-neutral-900 border border-emerald-900/50 rounded-xl p-6 shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            </div>
            <h3 className="text-emerald-400 text-sm font-medium mb-1">Successful Calls</h3>
            <p className="text-5xl font-bold text-emerald-400">{data.successful_calls}</p>
          </div>
          
          <div className="bg-neutral-900 border border-red-900/50 rounded-xl p-6 shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
            </div>
            <h3 className="text-red-400 text-sm font-medium mb-1">Failed Calls</h3>
            <p className="text-5xl font-bold text-red-400">{data.failed_calls}</p>
          </div>
        </div>

        <h2 className="text-2xl font-semibold mb-4 border-b border-neutral-800 pb-2">Recent Call Logs</h2>
        
        {data.calls.length === 0 ? (
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-8 text-center text-neutral-500">
            No calls logged yet. Start a conversation with the agent!
          </div>
        ) : (
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden shadow-lg">
            <table className="w-full text-left">
              <thead className="bg-neutral-950 border-b border-neutral-800">
                <tr>
                  <th className="p-4 font-medium text-neutral-400">Time</th>
                  <th className="p-4 font-medium text-neutral-400">Status</th>
                  <th className="p-4 font-medium text-neutral-400">Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800">
                {data.calls.reverse().map((call: any, idx: number) => {
                  const date = new Date(call.timestamp);
                  return (
                    <tr key={idx} className="hover:bg-neutral-800/50 transition-colors">
                      <td className="p-4 text-sm text-neutral-300 whitespace-nowrap">
                        {date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      </td>
                      <td className="p-4">
                        {call.is_successful ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-900/50 text-emerald-400 border border-emerald-800">
                            Success
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-900/50 text-red-400 border border-red-800">
                            Failed
                          </span>
                        )}
                      </td>
                      <td className="p-4 text-sm text-neutral-300">
                        {call.summary}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
