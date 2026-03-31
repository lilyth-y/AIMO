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
  is_correct?: boolean // Added mapped field
}

interface ResultData {
  problem_id: number
  is_correct: boolean
}

export default function ProblemViewer() {
  const [problems, setProblems] = useState<Problem[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'correct' | 'incorrect'>('all')

  useEffect(() => {
    Promise.all([
      fetch('/numina_eval_balanced.json').then(res => res.json()),
      fetch('/results/numina_balanced_results.json').then(res => res.json()).catch(() => ({ results: [] }))
    ]).then(([problemsData, resultsData]) => {
      // Map results to problems
      const mappedProblems = problemsData.map((p: any, idx: number) => {
        const resultMatch = resultsData.results?.find((r: any) => r.problem_id === idx)
        return {
          ...p,
          is_correct: resultMatch ? resultMatch.is_correct : undefined
        }
      })
      setProblems(mappedProblems)
      setLoading(false)
    }).catch(err => {
      console.error('Failed to load problems or results:', err)
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

      {/* Filters */}
      <div className="flex gap-2 p-1.5 glass w-fit rounded-2xl border-white/5">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${filter === 'all' ? 'bg-slate-700 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'}`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('correct')}
          className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${filter === 'correct' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-slate-400 hover:text-emerald-400/70 hover:bg-emerald-500/10'}`}
        >
          Correct
        </button>
        <button
          onClick={() => setFilter('incorrect')}
          className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${filter === 'incorrect' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'text-slate-400 hover:text-rose-400/70 hover:bg-rose-500/10'}`}
        >
          Incorrect
        </button>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {problems
          .filter(p => {
            if (filter === 'correct') return p.is_correct === true
            if (filter === 'incorrect') return p.is_correct === false || p.is_correct === undefined // Treat unmapped as incorrect for now or just false
            return true
          })
          .map((p, idx) => (
            <div key={idx} className="glass rounded-[32px] border-white/5 overflow-hidden card-hover group relative">

              {/* Success/Fail Badge */}
              {p.is_correct !== undefined && (
                <div className={`absolute top-6 right-8 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-white/10 shadow-lg ${p.is_correct
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30 shadow-emerald-500/20'
                    : 'bg-rose-500/20 text-rose-400 border-rose-500/30 shadow-rose-500/20'
                  }`}>
                  {p.is_correct ? '✅ Correct' : '❌ Incorrect'}
                </div>
              )}

              <div className={`px-8 py-6 border-b border-white/5 flex justify-between items-center ${p.is_correct === true ? 'bg-emerald-500/[0.02]' : p.is_correct === false ? 'bg-rose-500/[0.02]' : 'bg-white/[0.02]'
                }`}>
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400 border border-white/5">
                    #{idx + 1}
                  </span>
                  <span className="px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-[10px] font-bold uppercase tracking-wider border border-cyan-500/20">
                    {p.source}
                  </span>
                </div>
                <div className="flex items-center gap-2 pr-32"> {/* Added padding to avoid overlapping with badge */}
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

    </div>
  )
}
