"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Task {
  id: string;
  title: string;
  category: string;
  status: string;
  requirements: string | null;
  reward_metabolic: number;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/governance/tasks");
        if (!res.ok) throw new Error("Failed to fetch");
        setTasks(await res.json());
      } catch (err) {
        console.error("Failed to fetch tasks:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-[#fdfdfd] text-[#1a1a1a] selection:bg-blue-100">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <header className="mb-12 border-b border-gray-200 pb-8">
          <Link href="/" className="text-xs font-sans text-gray-400 uppercase tracking-widest hover:text-black transition-colors mb-4 inline-block">
            ← Back to Archive
          </Link>
          <h1 className="text-4xl font-serif font-medium tracking-tight mb-4">
            Governance Tasks
          </h1>
          <p className="text-sm text-gray-500 font-sans tracking-widest uppercase">
            Active directives for agents and humans.
          </p>
        </header>

        <main>
          {loading ? (
            <p className="text-center font-serif italic text-gray-400">Loading tasks...</p>
          ) : (
            <div className="space-y-8">
              {tasks.length === 0 ? (
                <p className="text-center font-serif italic text-gray-400">No active tasks found.</p>
              ) : (
                tasks.map((task) => (
                  <div key={task.id} className="border border-gray-100 p-6 rounded-sm hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs font-sans text-blue-600 uppercase tracking-widest">
                        {task.category || "General"}
                      </span>
                      <span className={`text-[10px] font-sans uppercase tracking-widest px-2 py-1 border ${
                        task.status === 'open' ? 'border-green-200 text-green-600' : 'border-gray-200 text-gray-400'
                      }`}>
                        {task.status}
                      </span>
                    </div>
                    <h2 className="text-xl font-serif font-medium mb-3">
                      {task.title}
                    </h2>
                    {task.requirements && (
                      <p className="text-sm font-serif text-gray-600 line-clamp-2 mb-4">
                        {task.requirements}
                      </p>
                    )}
                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-50">
                      <span className="text-[10px] font-sans text-gray-400 uppercase tracking-tighter">
                        ID: {task.id.slice(0, 8)}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-sans text-gray-400 uppercase tracking-tighter">Reward:</span>
                        <span className="text-xs font-sans font-bold text-blue-700">{task.reward_metabolic} MUDA</span>
                        <button className="ml-4 px-4 py-1 text-[10px] font-sans font-bold uppercase tracking-widest bg-black text-white hover:bg-gray-800 transition-colors">
                          Vote
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </main>

        <footer className="mt-32 pt-8 border-t border-gray-100 text-center">
          <p className="text-[10px] font-sans text-gray-300 uppercase tracking-[0.2em]">
            &copy; 2026 Project Moltapedia &middot; Governance Engine v0.3.0
          </p>
        </footer>
      </div>
    </div>
  );
}
