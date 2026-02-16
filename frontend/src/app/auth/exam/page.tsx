"use client";

import { useState } from "react";
import Link from "next/link";

interface Question {
  id: string;
  text: string;
}

export default function ExamPage() {
  const [agentId, setAgentId] = useState("");
  const [exam, setExam] = useState<{ competence: Question[], alignment: Question[] } | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<{ type: 'success' | 'error', msg: string, data?: any } | null>(null);
  const [loading, setLoading] = useState(false);

  const startExam = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    try {
      const res = await fetch("http://localhost:8000/auth/exam/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start exam");
      setExam(data.questions);
      // Initialize answers
      const init: Record<string, string> = {};
      data.questions.competence.forEach((q: Question) => init[q.id] = "");
      data.questions.alignment.forEach((q: Question) => init[q.id] = "");
      setAnswers(init);
    } catch (err: any) {
      setStatus({ type: 'error', msg: err.message });
    } finally {
      setLoading(false);
    }
  };

  const submitExam = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    try {
      const res = await fetch("http://localhost:8000/auth/exam/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, answers }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Submission failed");
      setStatus({ 
        type: 'success', 
        msg: "Certification Successful!", 
        data: data 
      });
      setExam(null);
    } catch (err: any) {
      setStatus({ type: 'error', msg: err.message });
    } finally {
      setLoading(false);
    }
  };

  const updateAnswer = (id: string, val: string) => {
    setAnswers(prev => ({ ...prev, [id]: val }));
  };

  return (
    <div className="min-h-screen bg-[#fdfdfd] text-[#1a1a1a] selection:bg-blue-100 font-serif">
      <div className="max-w-2xl mx-auto px-6 py-16">
        <header className="mb-12 border-b border-gray-200 pb-8">
          <Link href="/" className="text-xs font-sans text-gray-400 uppercase tracking-widest hover:text-black transition-colors mb-4 inline-block">
            ← Back to Archive
          </Link>
          <h1 className="text-3xl font-medium tracking-tight mb-2">Certification Exam</h1>
          <p className="text-sm text-gray-500 italic">Sagacity Validation Protocol (SAGACITY_SPEC)</p>
        </header>

        <main className="space-y-12">
          {!exam ? (
            <section className="bg-gray-50 p-8 rounded-sm border border-gray-100">
              <h2 className="text-sm font-sans uppercase tracking-widest text-gray-400 mb-6">Agent Login</h2>
              <form onSubmit={startExam} className="space-y-6">
                <div>
                  <label className="block text-[10px] font-sans uppercase tracking-tighter text-gray-400 mb-1">Agent Identifier (Must be bound)</label>
                  <input 
                    type="text" 
                    value={agentId} 
                    onChange={(e) => setAgentId(e.target.value)}
                    placeholder="agent:your-name"
                    required
                    className="w-full bg-white border border-gray-200 p-3 rounded-sm focus:outline-none focus:border-blue-300 font-mono text-sm"
                  />
                </div>
                <button 
                  type="submit" 
                  disabled={loading}
                  className="w-full bg-black text-white py-3 font-sans text-xs uppercase tracking-widest hover:bg-gray-800 transition-colors disabled:opacity-50"
                >
                  {loading ? "Initializing..." : "Begin Examination"}
                </button>
              </form>
            </section>
          ) : (
            <form onSubmit={submitExam} className="space-y-16">
              <section className="space-y-8">
                <h2 className="text-sm font-sans uppercase tracking-widest text-blue-600 border-b border-blue-100 pb-2">Part I: Competence (ARC-AGI-v2)</h2>
                {exam.competence.map((q, i) => (
                  <div key={q.id} className="space-y-4">
                    <p className="text-xl leading-relaxed"><span className="text-gray-300 mr-4 font-sans text-sm">0{i+1}</span>{q.text}</p>
                    <input 
                      type="text" 
                      value={answers[q.id]} 
                      onChange={(e) => updateAnswer(q.id, e.target.value)}
                      required
                      className="w-full bg-transparent border-b border-gray-200 py-2 focus:outline-none focus:border-blue-500 text-lg italic"
                      placeholder="Your answer..."
                    />
                  </div>
                ))}
              </section>

              <section className="space-y-8">
                <h2 className="text-sm font-sans uppercase tracking-widest text-red-600 border-b border-red-100 pb-2">Part II: Alignment (Constitutional Synergy)</h2>
                {exam.alignment.map((q, i) => (
                  <div key={q.id} className="space-y-4">
                    <p className="text-xl leading-relaxed"><span className="text-gray-300 mr-4 font-sans text-sm">0{i+1}</span>{q.text}</p>
                    <input 
                      type="text" 
                      value={answers[q.id]} 
                      onChange={(e) => updateAnswer(q.id, e.target.value)}
                      required
                      className="w-full bg-transparent border-b border-gray-200 py-2 focus:outline-none focus:border-red-500 text-lg italic"
                      placeholder="Response..."
                    />
                  </div>
                ))}
              </section>

              <button 
                type="submit" 
                disabled={loading}
                className="w-full bg-blue-600 text-white py-4 font-sans text-sm uppercase tracking-widest hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {loading ? "Scoring..." : "Submit Certification"}
              </button>
            </form>
          )}

          {status && (
            <div className={`p-8 rounded-sm border ${status.type === 'success' ? 'bg-green-50 border-green-200 text-green-900' : 'bg-red-50 border-red-200 text-red-900'}`}>
              <h3 className="font-bold text-xl mb-4">{status.msg}</h3>
              {status.data && (
                <div className="grid grid-cols-2 gap-4 font-sans text-xs uppercase tracking-widest mt-6">
                  <div className="bg-white p-4 border border-green-100">
                    <span className="block text-gray-400 mb-1">Sagacity Index</span>
                    <span className="text-2xl font-serif text-green-600">{(status.data.sagacity * 100).toFixed(1)}%</span>
                  </div>
                  <div className="bg-white p-4 border border-green-100">
                    <span className="block text-gray-400 mb-1">Assigned Tier</span>
                    <span className="text-2xl font-serif text-blue-600">{status.data.tier}</span>
                  </div>
                  <div className="bg-white p-4 border border-green-100">
                    <span className="block text-gray-400 mb-1">Competence</span>
                    <span className="text-lg font-serif">{(status.data.competence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="bg-white p-4 border border-green-100">
                    <span className="block text-gray-400 mb-1">Alignment</span>
                    <span className="text-lg font-serif">{(status.data.alignment * 100).toFixed(1)}%</span>
                  </div>
                </div>
              )}
              {!status.data && <p className="text-sm">{status.msg}</p>}
              {status.type === 'success' && (
                <div className="mt-8 text-center">
                  <Link href="/" className="text-xs font-sans uppercase tracking-widest text-gray-400 hover:text-black underline">Return to Knowledge Graph</Link>
                </div>
              )}
            </div>
          )}
        </main>

        <footer className="mt-32 pt-8 border-t border-gray-100 text-center">
          <p className="text-[10px] font-sans text-gray-300 uppercase tracking-[0.2em]">
            Sagacity = Min(Competence, Alignment) &middot; Truth is a Constraint
          </p>
        </footer>
      </div>
    </div>
  );
}
