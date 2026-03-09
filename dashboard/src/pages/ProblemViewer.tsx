import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface Problem {
  problem: string
  solution: string
  answer: string
  source: string
}

export default function ProblemViewer() {
  const [problems, setProblems] = useState<Problem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/numina_eval_balanced.json')
      .then(res => res.json())
      .then(json => {
        setProblems(json)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load problems:', err)
        setLoading(false)
      })
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="w-8 h-8 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
    </div>
  )

  if (problems.length === 0) return (
    <div className="glass p-8 rounded-3xl border-rose-500/20 text-rose-400 text-center">
      문제를 불러올 수 없습니다.
    </div>
  )

  return (
    <div className="space-y-12">
      <div className="space-y-4">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
          Problem <span className="text-gradient">Explorer</span>
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl leading-relaxed">
          NuminaMath-1.5 데이터셋에서 추출된 밸런스드 평가 세트입니다. 총 <span className="text-cyan-400 font-bold">{problems.length}</span>개의 문제가 포함되어 있습니다.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {problems.slice(0, 20).map((p, idx) => (
          <div key={idx} className="glass rounded-[32px] border-white/5 overflow-hidden card-hover group">
            <div className="px-8 py-6 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400 border border-white/5">
                  #{idx + 1}
                </span>
                <span className="px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-[10px] font-bold uppercase tracking-wider border border-cyan-500/20">
                  {p.source}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-medium whitespace-nowrap">Expected Answer</span>
                <div className="px-4 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-400 text-sm font-bold border border-emerald-500/20 shadow-lg shadow-emerald-500/5 overflow-x-auto max-w-sm custom-scrollbar">
                  <ReactMarkdown
                    remarkPlugins={[remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{ p: ({ node, ...props }) => <span {...props} /> }}
                  >
                    {`$${p.answer}$`}
                  </ReactMarkdown>
                </div>
              </div>
            </div>

            <div className="p-8 space-y-8">
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-widest">
                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                  Problem Statement
                </div>
                <div className="text-lg text-slate-100 leading-relaxed font-serif bg-slate-900/40 p-8 rounded-3xl border border-white/5 shadow-inner prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-slate-800">
                  <ReactMarkdown
                    remarkPlugins={[remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                  >
                    {p.problem}
                  </ReactMarkdown>
                </div>
              </div>

              <details className="group/details">
                <summary className="flex items-center gap-2 text-xs font-bold text-slate-500 cursor-pointer hover:text-slate-300 transition-colors uppercase tracking-widest list-none">
                  <span className="w-4 h-4 rounded-md bg-slate-800 flex items-center justify-center group-open/details:rotate-90 transition-transform">
                    <svg width="6" height="10" viewBox="0 0 6 10" fill="none"><path d="M1 1L5 5L1 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                  </span>
                  Show Chain of Thought
                </summary>
                <div className="mt-6 text-slate-400 text-sm leading-relaxed bg-indigo-500/[0.03] p-8 rounded-3xl border border-indigo-500/10 font-mono prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-slate-800">
                  <ReactMarkdown
                    remarkPlugins={[remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                  >
                    {p.solution}
                  </ReactMarkdown>
                </div>
              </details>
            </div>
          </div>
        ))}
      </div>

      {problems.length > 20 && (
        <div className="py-12 text-center">
          <button className="px-8 py-3 rounded-2xl glass border-white/10 text-slate-400 font-bold hover:text-white hover:border-cyan-500/50 transition-all">
            Load More Problems
          </button>
        </div>
      )}
    </div>
  )
}
