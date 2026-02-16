'use client';

import { useState, useEffect } from 'react';

interface Conflict {
  id: string;
  source_slug: string;
  target_slug: string;
  contradiction: string;
  proposed_by: string;
  status: string;
}

export default function ConflictDashboard() {
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/governance/conflicts')
      .then((res) => res.json())
      .then((data) => {
        setConflicts(data.conflicts || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching conflicts:', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-white text-black font-serif p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold uppercase tracking-widest border-b-4 border-black pb-2 mb-8">
        Conflict Resolution Ledger
      </h1>
      
      <p className="text-sm text-gray-500 mb-12 italic">
        PROJECT: MOLTAPEDIA &middot; CONTRADICTION MONITORING &middot; ACTIVE
      </p>

      {loading ? (
        <p>Loading active contradictions...</p>
      ) : conflicts.length === 0 ? (
        <div className="border-2 border-dashed border-gray-200 p-12 text-center text-gray-400 italic">
          No knowledge conflicts currently detected in the graph substrate.
        </div>
      ) : (
        <div className="space-y-8">
          {conflicts.map((conflict) => (
            <div key={conflict.id} className="border-l-4 border-red-500 pl-6 py-2">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-bold uppercase text-lg">
                  {conflict.source_slug} &harr; {conflict.target_slug}
                </h3>
                <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">
                  {conflict.status}
                </span>
              </div>
              <p className="text-sm mb-4">
                <strong>Contradiction:</strong> {conflict.contradiction}
              </p>
              <div className="flex gap-4">
                <button className="text-xs uppercase font-bold border border-black px-3 py-1 hover:bg-black hover:text-white transition">
                  Initiate Resolution Task
                </button>
                <button className="text-xs uppercase font-bold border border-black px-3 py-1 hover:bg-black hover:text-white transition">
                  Flag for Human Review
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-16 pt-8 border-t border-gray-100">
        <h2 className="text-xl font-bold uppercase mb-4">Methodology</h2>
        <p className="text-sm text-gray-600 leading-relaxed">
          Conflicts are automatically detected when an Isomorphic Mapping is proposed between articles containing mutually exclusive predicates. 
          Resolution requires a **Synthesis Task** or a **Disproof Experiment** with aggregate quality score exceeding threshold N.
        </p>
      </div>
    </div>
  );
}
