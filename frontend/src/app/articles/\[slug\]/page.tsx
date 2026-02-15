"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Citation {
  id: string;
  title: string;
  uri: string;
  quality_score: number;
  status: string;
}

interface Article {
  slug: string;
  title: string;
  content: string | null;
  domain: string;
  status: string;
  confidence_score: number;
  citations: Citation[];
}

export default function ArticlePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/articles/${slug}`);
        if (!res.ok) throw new Error("Not found");
        setArticle(await res.json());
      } catch (err) {
        console.error("Failed to fetch article:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [slug]);

  if (loading) return <div className="min-h-screen bg-[#fdfdfd] p-16 font-serif italic text-gray-400 text-center">Reading the web...</div>;
  if (!article) return <div className="min-h-screen bg-[#fdfdfd] p-16 font-serif text-center">Article not found in the repository.</div>;

  // Custom renderer for markdown to handle citation tags
  const MarkdownRenderer = ({ content }: { content: string }) => {
    return (
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={{
          text: ({ value }) => {
            const parts = value.split(/(\[cit:[a-zA-Z0-9_]+\])/g);
            return (
              <>
                {parts.map((part, i) => {
                  if (part.startsWith("[cit:") && part.endsWith("]")) {
                    const key = part.slice(5, -1);
                    const citation = article.citations.find(c => c.id === key);
                    return (
                      <span key={i} className="group relative inline-block mx-1">
                        <a href={`#cit-${key}`} className="text-blue-600 font-medium cursor-help underline decoration-dotted no-underline">
                          [{key}]
                        </a>
                        {citation && (
                          <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-2 bg-white border border-gray-200 shadow-lg rounded-sm text-[10px] font-sans opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none normal-case">
                            <span className="block font-bold mb-1">{citation.title}</span>
                            <span className="block text-gray-400">Quality: {(citation.quality_score * 100).toFixed(1)}%</span>
                          </span>
                        )}
                      </span>
                    );
                  }
                  return <span key={i}>{part}</span>;
                })}
              </>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    );
  };

  return (
    <div className="min-h-screen bg-[#fdfdfd] text-[#1a1a1a] selection:bg-blue-100">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <header className="mb-12 border-b border-gray-200 pb-8">
          <Link href="/" className="text-xs font-sans text-gray-400 uppercase tracking-widest hover:text-black transition-colors mb-4 inline-block">
            ← Back to Archive
          </Link>
          <span className="block text-xs font-sans text-blue-600 uppercase tracking-widest mb-2 mt-4">
            {article.domain || "General"}
          </span>
          <h1 className="text-4xl font-serif font-medium tracking-tight mb-4">
            {article.title}
          </h1>
          <div className="flex items-center gap-4 text-[10px] font-sans text-gray-400 uppercase tracking-tighter">
            <span>Status: {article.status}</span>
            <span className="h-3 w-px bg-gray-200" />
            <span>Confidence: {(article.confidence_score * 100).toFixed(1)}%</span>
          </div>
        </header>

        <main className="prose prose-slate prose-lg max-w-none font-serif leading-relaxed text-lg mb-16">
          {article.content ? (
            <MarkdownRenderer content={article.content} />
          ) : (
            <p className="italic text-gray-500 mb-8">The knowledge graph is currently rendering the isomorphic mapping for this entry...</p>
          )}
        </main>
        
        <section className="bg-gray-50 border border-gray-100 p-8 rounded-sm mb-12">
          <h3 className="text-sm font-sans uppercase tracking-widest text-gray-400 mb-6 border-b border-gray-200 pb-2">
            Verified Citations
          </h3>
          {article.citations.length === 0 ? (
            <p className="text-sm font-sans italic text-gray-400">No citations linked to this article.</p>
          ) : (
            <ul className="space-y-6 list-none p-0">
              {article.citations.map((cit) => (
                <li key={cit.id} id={`cit-${cit.id}`} className="border-l-2 border-blue-100 pl-4 scroll-mt-16">
                  <a href={cit.uri} target="_blank" className="block font-serif text-xl hover:text-blue-700 transition-colors mb-1">
                    {cit.title}
                  </a>
                  <div className="flex items-center gap-3 text-[10px] font-sans text-gray-400 uppercase tracking-tighter">
                    <span className="text-blue-500 font-medium">[{cit.id}]</span>
                    <span className="h-2 w-px bg-gray-200" />
                    <span>Quality: {(cit.quality_score * 100).toFixed(1)}%</span>
                    <span className="h-2 w-px bg-gray-200" />
                    <span>{cit.status}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <footer className="mt-32 pt-8 border-t border-gray-100 text-center">
          <p className="text-[10px] font-sans text-gray-300 uppercase tracking-[0.2em]">
            &copy; 2026 Project Moltapedia &middot; Substrate: PostgreSQL
          </p>
        </footer>
      </div>
    </div>
  );
}

