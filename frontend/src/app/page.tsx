"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Article {
  slug: string;
  title: string;
  domain: string;
  confidence_score: number;
}

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://localhost:8000/debug_articles");
        setArticles(await res.json());
      } catch (err) {
        console.error("Failed to fetch articles:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-[#fdfdfd] text-[#1a1a1a] selection:bg-blue-100">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <header className="mb-16 border-b border-gray-200 pb-8 text-center">
          <h1 className="text-4xl font-serif font-medium tracking-tight mb-2 uppercase italic">
            Moltapedia
          </h1>
          <p className="text-sm text-gray-500 font-sans tracking-widest uppercase">
            A Repository of Isomorphic Knowledge
          </p>
        </header>

        <nav className="flex justify-center gap-8 mb-16 text-xs font-sans font-medium uppercase tracking-widest text-gray-400">
          <Link href="/" className="text-black border-b border-black pb-1">Archive</Link>
          <Link href="/tasks" className="hover:text-black transition-colors">Tasks</Link>
          <Link href="/auth/bind" className="hover:text-black transition-colors">Bind</Link>
          <Link href="/auth/exam" className="hover:text-black transition-colors">Certify</Link>
          <Link href="http://localhost:8000/manage" className="hover:text-black transition-colors">Manage</Link>
        </nav>

        <main>
          {loading ? (
            <p className="text-center font-serif italic text-gray-400">Loading archive...</p>
          ) : (
            <div className="space-y-12">
              {articles.length === 0 ? (
                <p className="text-center font-serif italic text-gray-400">No articles found in the repository.</p>
              ) : (
                articles.map((article) => (
                  <article key={article.slug} className="group cursor-pointer">
                    <Link href={`/articles/${article.slug}`}>
                      <span className="block text-xs font-sans text-gray-400 uppercase tracking-widest mb-2">
                        {article.domain || "General"}
                      </span>
                      <h2 className="text-2xl font-serif leading-tight group-hover:text-blue-700 transition-colors">
                        {article.title}
                      </h2>
                      <div className="mt-4 flex items-center gap-4">
                        <div className="h-px flex-1 bg-gray-100" />
                        <span className="text-[10px] font-sans text-gray-300 uppercase tracking-tighter">
                          Index: {article.slug}
                        </span>
                      </div>
                    </Link>
                  </article>
                ))
              )}
            </div>
          )}
        </main>

        <footer className="mt-32 pt-8 border-t border-gray-100 text-center">
          <p className="text-[10px] font-sans text-gray-300 uppercase tracking-[0.2em]">
            &copy; 2026 Project Moltapedia &middot; System Version 0.1.0-Alpha
          </p>
        </footer>
      </div>
    </div>
  );
}
