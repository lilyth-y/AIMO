import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface TraceItem {
  stage: string;
  status: 'completed' | 'rejected' | 'passed' | 'failed' | 'processing';
  details?: string;
  timestamp: string;
}

const EXAMPLES = [
  { label: 'hello', value: 'hello' },
  { label: 'quadratic', value: 'Solve x² - 5x + 6 = 0' },
  { label: 'integral', value: 'Find ∫(x² + 3x) dx from 0 to 2' },
  { label: 'number theory', value: 'Find all prime numbers p such that p² + 2 is also prime.' },
]

export default function LiveSolve() {
  const [problem, setProblem] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [trace, setTrace] = useState<TraceItem[]>([])
  const [inputDiagnosis, setInputDiagnosis] = useState<any>(null)
  const [copied, setCopied] = useState(false)

  const handleSolve = async () => {
    if (!problem.trim()) return
    setLoading(true)
    setResult(null)
    setError(null)
    setInputDiagnosis(null)
    setTrace([
      { stage: 'Initializing', status: 'processing', timestamp: new Date().toISOString() }
    ])

    try {
      const res = await fetch('/api/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem_text: problem, time_budget: 60.0 }),
      })
      
      if (!res.ok) throw new Error('API request failed')
      
      const data = await res.json()
      setResult(data)

      // Extract input_diagnosis if available
      const diag = data.result?.input_diagnosis || data.input_diagnosis || null
      setInputDiagnosis(diag)
      
      // Update trace from backend if available
      if (data.result?.pipeline_trace) {
        setTrace(data.result.pipeline_trace)
      } else if (data.pipeline_trace) {
        setTrace(data.pipeline_trace)
      } else {
        setTrace(prev => [...prev, { stage: 'Pipeline Complete', status: 'completed', timestamp: new Date().toISOString() }])
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong')
      setTrace(prev => [...prev, { stage: 'Error', status: 'failed', details: err.message, timestamp: new Date().toISOString() }])
    } finally {
      setLoading(false)
    }
  }

  const copyAnswer = () => {
    const answer = result?.result?.answer ?? result?.answer ?? ''
    navigator.clipboard.writeText(String(answer))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const r = result?.result ?? result ?? null
  const isRejected = r?.status === 'rejected'
  const latencyMs = r?.resource_usage?.wall_ms ?? result?.latency_ms ?? null
  const domain = r?.strategy_features?.dominant_domain ?? r?.domain ?? result?.domain ?? null
  const verified = r?.verified === true
  const mismatch = r?.mismatch === true

  const confidenceLabel = isRejected
    ? 'BLOCKED'
    : mismatch
    ? 'LOW — MISMATCH'
    : verified
    ? 'HIGH — VERIFIED'
    : r?.status === 'solved'
    ? 'MEDIUM — UNVERIFIED'
    : 'N/A'

  const confidenceStyle = isRejected
    ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
    : mismatch
    ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
    : verified
    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    : 'bg-slate-500/10 text-slate-400 border-slate-500/20'

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'passed':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
      case 'failed':
      case 'rejected':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20'
      case 'processing':
        return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20'
      default:
        return 'text-slate-400 bg-slate-500/10 border-slate-500/20'
    }
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto px-4 py-8">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl font-black tracking-tighter text-white uppercase italic">
            Live Mission <span className="text-cyan-400 not-italic">Control</span>
          </h1>
          <p className="text-slate-400 text-sm mt-2 max-w-xl font-medium">
            Execute the AIMO pipeline in real-time. Witness the AI's reasoning path from raw input to verified mathematical proof.
          </p>
        </div>
        <div className="flex gap-3">
          <div className="px-4 py-2 glass rounded-xl border border-white/5 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">Core v2.5 Online</span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Input & Trace */}
        <div className="lg:col-span-5 space-y-8">
          {/* Input Area */}
          <div className="glass rounded-3xl border border-white/10 p-8 space-y-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <svg className="w-24 h-24 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-black uppercase tracking-widest text-slate-400 flex items-center gap-2">
                <span className="w-1 h-3 bg-cyan-500 rounded-full" />
                Problem Input
              </h2>
            </div>
            
            {/* Quick-fill example buttons */}
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map(ex => (
                <button
                  key={ex.label}
                  onClick={() => setProblem(ex.value)}
                  className="px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest border border-white/10 text-slate-500 hover:text-cyan-400 hover:border-cyan-500/30 transition-all bg-slate-900/40"
                >
                  {ex.label}
                </button>
              ))}
            </div>

            <textarea
              value={problem}
              onChange={(e) => setProblem(e.target.value)}
              placeholder="Enter your math problem here (LaTeX supported)..."
              className="w-full h-80 bg-slate-950/50 border border-white/5 rounded-2xl p-6 text-slate-200 text-base focus:border-cyan-500/50 outline-none transition-all resize-none font-sans leading-relaxed placeholder:text-slate-700"
            />

            <button
              onClick={handleSolve}
              disabled={loading || !problem.trim()}
              className={`w-full py-5 rounded-2xl font-black uppercase tracking-widest transition-all shadow-2xl relative overflow-hidden group/btn ${
                loading 
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-cyan-500/20'
              }`}
            >
              <span className="relative z-10 flex items-center justify-center gap-3">
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Processing Mission...
                  </>
                ) : (
                  <>
                    Engage Solver
                    <svg className="w-5 h-5 group-hover/btn:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                  </>
                )}
              </span>
            </button>
          </div>

          {/* Pipeline Trace Visualization */}
          <div className="glass rounded-3xl border border-white/10 p-8 space-y-6">
            <h2 className="text-xs font-black uppercase tracking-widest text-slate-400 flex items-center gap-2">
              <span className="w-1 h-3 bg-emerald-500 rounded-full" />
              Pipeline Telemetry
            </h2>
            
            <div className="space-y-4">
              {trace.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-slate-600 text-xs italic font-medium">Telemetry idle. Initiate solver to capture trace data.</p>
                </div>
              ) : (
                <div className="relative border-l border-white/5 ml-2 pl-6 space-y-6">
                  {trace.map((t, i) => (
                    <div key={i} className="relative group">
                      <div className={`absolute -left-[31px] top-0 w-3 h-3 rounded-full border-2 border-slate-900 z-10 transition-colors ${
                        t.status === 'processing' ? 'bg-cyan-500 animate-pulse' : 
                        t.status === 'failed' || t.status === 'rejected' ? 'bg-rose-500' : 'bg-emerald-500'
                      }`} />
                      
                      <div className="space-y-1">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-bold text-slate-200">{t.stage}</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full border font-black uppercase tracking-tighter ${getStatusColor(t.status)}`}>
                            {t.status}
                          </span>
                        </div>
                        {t.details && (
                          <p className="text-xs text-slate-500 font-medium leading-relaxed">
                            {t.details}
                          </p>
                        )}
                        <span className="text-[10px] text-slate-700 font-mono">
                          {new Date(t.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-7 space-y-8">
          {error && (
            <div className="glass rounded-3xl border border-rose-500/30 bg-rose-500/5 p-8 flex gap-6 items-start">
              <div className="p-3 rounded-2xl bg-rose-500/20 text-rose-500">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              </div>
              <div className="space-y-2">
                <h3 className="font-black uppercase text-sm tracking-widest text-rose-500">Mission Aborted: Pipeline Fault</h3>
                <p className="text-rose-200/80 text-sm font-mono leading-relaxed bg-black/20 p-4 rounded-xl border border-white/5">{error}</p>
              </div>
            </div>
          )}

          {!result && !loading && !error && (
            <div className="glass rounded-3xl border border-white/5 bg-white/[0.01] p-24 flex flex-col items-center justify-center text-center space-y-6 h-full min-h-[600px]">
              <div className="w-20 h-20 rounded-3xl bg-slate-900 border border-white/5 flex items-center justify-center text-slate-700 shadow-2xl relative">
                <div className="absolute inset-0 bg-cyan-500/5 blur-2xl rounded-full" />
                <svg className="w-10 h-10 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.364-6.364l-.707-.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M12 7a5 5 0 015 5 5 5 0 01-5 5 5 5 0 01-5-5 5 5 0 015-5z" /></svg>
              </div>
              <div className="space-y-2 max-w-sm">
                <h3 className="text-slate-400 font-bold uppercase text-xs tracking-[0.2em]">Neural Link Standby</h3>
                <p className="text-slate-600 text-sm font-medium">The orchestration layer is awaiting a problem payload to begin computation.</p>
              </div>
            </div>
          )}

          {result && (
            <div className={`glass rounded-3xl border p-8 space-y-8 animate-slide-up h-full ${
              result.result?.status === 'rejected' || result.status === 'rejected'
                ? 'border-rose-500/30 bg-rose-500/[0.02]'
                : 'border-cyan-500/20 bg-cyan-500/[0.01]'
            }`}>
              <div className="flex items-center justify-between border-b border-white/5 pb-6">
                <div className="space-y-1">
                  <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-500/80">Computation Result</h2>
                  <div className="flex items-center gap-3">
                    <h3 className="text-xl font-bold text-white uppercase tracking-tight">Mission Resolution</h3>
                    <span className={`px-2 py-0.5 rounded-lg text-[10px] font-mono border ${
                      result.result?.status === 'rejected' || result.status === 'rejected'
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
                    }`}>
                      STRATEGY: {result.result?.method || result.method || 'UNKNOWN'}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Processing Time</p>
                  <p className="text-sm font-mono text-cyan-400">{latencyMs != null ? (latencyMs / 1000).toFixed(2) + 's' : '—'}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full ${isRejected ? 'bg-rose-500' : 'bg-cyan-500'}`} />
                    Final Answer
                  </label>
                  <div className={`p-6 rounded-2xl border text-white font-bold text-3xl flex items-center justify-center min-h-[120px] relative group ${
                    isRejected
                      ? 'bg-slate-950/80 border-rose-500/20 text-rose-200 text-base'
                      : 'bg-slate-950/80 border-cyan-500/30 shadow-[0_0_50px_-12px_rgba(6,182,212,0.3)]'
                  }`}>
                    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                      {String(r?.answer ?? 'N/A')}
                    </ReactMarkdown>
                    {!isRejected && (
                      <button
                        onClick={copyAnswer}
                        className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg bg-slate-800 border border-white/10 text-slate-400 hover:text-cyan-400"
                        title="Copy answer"
                      >
                        {copied
                          ? <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                          : <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                        }
                      </button>
                    )}
                  </div>
                </div>

                <div className="flex flex-col gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Domain Classification</label>
                    <div className="px-4 py-3 rounded-xl bg-slate-900/50 border border-white/5 text-xs text-slate-300 font-mono flex items-center justify-between">
                      <span className="capitalize">{domain || 'unclassified'}</span>
                      <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Confidence Score</label>
                    <div className={`px-4 py-3 rounded-xl border text-xs font-black uppercase flex items-center justify-between ${confidenceStyle}`}>
                      <span>{confidenceLabel}</span>
                      {verified && !mismatch && !isRejected && (
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Input Analysis — shown when there is a diagnosis */}
              {inputDiagnosis && (
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full ${isRejected ? 'bg-rose-500' : 'bg-emerald-500'}`} />
                    Stage 0 — Input Signal Analysis {isRejected ? '(BLOCKED)' : '(PASSED)'}
                  </label>
                  <div className={`p-5 rounded-2xl bg-slate-900/60 border space-y-3 ${isRejected ? 'border-rose-500/20' : 'border-emerald-500/20'}`}>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="space-y-1">
                        <p className="text-slate-600 font-black uppercase tracking-widest text-[9px]">Math Symbols Found</p>
                        <p className={`font-mono font-bold ${
                          inputDiagnosis.found_math_symbols?.length > 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}>
                          {inputDiagnosis.found_math_symbols?.length > 0
                            ? inputDiagnosis.found_math_symbols.join(', ')
                            : '— none detected'}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-slate-600 font-black uppercase tracking-widest text-[9px]">Math Keywords Found</p>
                        <p className={`font-mono font-bold ${
                          inputDiagnosis.found_math_keywords?.length > 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}>
                          {inputDiagnosis.found_math_keywords?.length > 0
                            ? inputDiagnosis.found_math_keywords.join(', ')
                            : '— none detected'}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-slate-600 font-black uppercase tracking-widest text-[9px]">Digits Present</p>
                        <p className={`font-mono font-bold ${
                          inputDiagnosis.has_digits ? 'text-emerald-400' : 'text-rose-400'
                        }`}>
                          {inputDiagnosis.has_digits ? '✓ yes' : '✗ no'}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-slate-600 font-black uppercase tracking-widest text-[9px]">Conversational Phrases</p>
                        <p className={`font-mono font-bold ${
                          inputDiagnosis.found_conversational?.length > 0 ? 'text-amber-400' : 'text-slate-500'
                        }`}>
                          {inputDiagnosis.found_conversational?.length > 0
                            ? inputDiagnosis.found_conversational.join(', ')
                            : '— none'}
                        </p>
                      </div>
                    </div>
                    {inputDiagnosis.rejection_reason && (
                      <div className="pt-3 border-t border-white/5">
                        <p className="text-[9px] font-black uppercase tracking-widest text-rose-500/80 mb-1">Rejection Reason</p>
                        <p className="text-xs text-rose-300 font-mono leading-relaxed">{inputDiagnosis.rejection_reason}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {(r?.answer_explanation || result?.reasoning) && (
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-600" />
                    Process Rationale
                  </label>
                  <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/5 text-sm text-slate-300 leading-relaxed font-medium">
                    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                      {r?.answer_explanation || result?.reasoning}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
              
              {r?.code && (
                <div className="space-y-3">
                  <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Generated Solution Logic</label>
                  <div className="p-4 rounded-2xl bg-black/40 border border-white/5">
                    <pre className="text-[11px] font-mono text-cyan-300/80 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                      {r.code}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
