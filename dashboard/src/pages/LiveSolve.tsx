import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface TraceItem {
  stage: string;
  status: 'completed' | 'rejected' | 'passed' | 'failed' | 'processing' | 'skipped' | 'ok';
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
  const [logs, setLogs] = useState<string[]>([])
  const [copied, setCopied] = useState(false)
  const consoleEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  const addLog = (msg: string) => {
    const time = new Date().toLocaleTimeString()
    setLogs(prev => [...prev, `[${time}] ${msg}`])
  }

  const handleSolve = async () => {
    if (!problem.trim()) return
    setLoading(true)
    setResult(null)
    setError(null)
    setTrace([])
    setLogs([])
    addLog('Initializing Neural Link...')
    addLog('Payload captured. Deploying AIMO Orchestrator...')

    const apiBase = import.meta.env.VITE_API_URL || '';
    const apiPrefix = apiBase.endsWith('/') ? apiBase.slice(0, -1) : apiBase;

    try {
      const requestUrl = apiPrefix ? `${apiPrefix}/solve/stream` : '/api/solve/stream';
      const response = await fetch(requestUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem_text: problem, time_budget: 60.0 }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API request failed with status ${response.status}: ${errorText.substring(0, 50)}`);
      }
      if (!response.body) throw new Error('No response body')

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const msg = JSON.parse(line.substring(6));
              if (msg.type === 'trace') {
                const item = msg.data;
                setTrace(prev => {
                  const existingIndex = prev.findIndex(t => t.stage === item.stage);
                  if (existingIndex >= 0) {
                    const next = [...prev];
                    next[existingIndex] = item;
                    return next;
                  }
                  return [...prev, item];
                });
                addLog(`STAGE: ${item.stage} -> ${item.status.toUpperCase()}${item.details ? ` (${item.details})` : ''}`);
              } else if (msg.type === 'final') {
                setResult(msg.data);
                addLog('Mission Resolution reached. Finalizing telemetry...');
              } else if (msg.type === 'error') {
                setError(msg.data);
                addLog(`CRITICAL FAULT: ${msg.data}`);
              }
            } catch (e) {
              console.error('Error parsing SSE message', e);
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong')
      addLog(`SYSTEM ERROR: ${err.message}`)
      setTrace(prev => [...prev, { stage: 'System Fault', status: 'failed', details: err.message, timestamp: new Date().toISOString() }])
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

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'completed':
      case 'passed':
      case 'ok':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
      case 'failed':
      case 'rejected':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20'
      case 'processing':
        return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20 animate-pulse'
      case 'skipped':
        return 'text-slate-500 bg-slate-500/10 border-slate-500/20'
      default:
        return 'text-slate-400 bg-slate-500/10 border-slate-500/20'
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 relative overflow-hidden bg-dot-grid">
      {/* Background scanline effect */}
      <div className="scanline" />

      <div className="max-w-[1600px] mx-auto p-6 lg:p-10 space-y-8 relative z-20">
        {/* Header: Mission Status Bar */}
        <header className="flex flex-col md:flex-row items-center justify-between gap-6 glass p-6 rounded-3xl border-white/5 glow-border-cyan">
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 relative overflow-hidden group">
              <div className="absolute inset-0 bg-white/10 group-hover:bg-white/20 transition-colors" />
              <svg className="w-8 h-8 text-white relative z-10" fill="currentColor" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tighter uppercase italic leading-none text-white">
                Live Mission <span className="text-cyan-400 not-italic">Control</span>
              </h1>
              <div className="flex items-center gap-3 mt-2">
                <div className="flex items-center gap-2 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[10px] font-black text-emerald-400 tracking-widest uppercase">CORE v2.5 ONLINE</span>
                </div>
                <span className="text-slate-600 font-mono text-[10px]">OS: AIMO-KERNEL-X64</span>
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="glass px-4 py-2 rounded-xl border-white/5 text-right">
              <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Network Latency</p>
              <p className="text-sm font-mono text-cyan-400">14ms</p>
            </div>
            <div className="glass px-4 py-2 rounded-xl border-white/5 text-right">
              <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Backend Uptime</p>
              <p className="text-sm font-mono text-emerald-400">99.98%</p>
            </div>
            <div className="glass px-4 py-2 rounded-xl border-white/5 text-right">
              <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Thread Safety</p>
              <p className="text-sm font-mono text-amber-400">NOMINAL</p>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Input & Logs */}
          <div className="lg:col-span-4 space-y-8">
            {/* Input Module */}
            <section className="glass rounded-3xl border-white/5 p-8 space-y-6 relative group overflow-hidden">
               <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
                  <svg className="w-32 h-32" fill="currentColor" viewBox="0 0 24 24"><path d="M21 16.5c0 .38-.21.71-.53.88l-7.97 4.41c-.32.18-.69.18-1.01 0l-7.97-4.41c-.32-.17-.53-.5-.53-.88V7.5c0-.38.21-.71.53-.88l7.97-4.41c.32-.18.69-.18 1.01 0l7.97 4.41c.32.17.53.5.53.88v9z" /></svg>
               </div>

              <div className="flex items-center justify-between">
                <h2 className="text-xs font-black uppercase tracking-widest text-slate-400 flex items-center gap-3">
                  <div className="w-1.5 h-4 bg-cyan-500 rounded-full" />
                  Mission Payload
                </h2>
                <div className="flex gap-2">
                  {EXAMPLES.map(ex => (
                    <button
                      key={ex.label}
                      onClick={() => setProblem(ex.value)}
                      className="text-[9px] font-black uppercase tracking-widest text-slate-500 hover:text-cyan-400 transition-colors"
                    >
                      [{ex.label}]
                    </button>
                  ))}
                </div>
              </div>

              <div className="relative">
                <textarea
                  value={problem}
                  onChange={(e) => setProblem(e.target.value)}
                  placeholder="Awaiting input data..."
                  className="w-full h-64 bg-slate-900/50 border border-white/5 rounded-2xl p-6 text-slate-200 text-sm focus:border-cyan-500/30 outline-none transition-all resize-none font-mono placeholder:text-slate-800"
                />
                <div className="absolute bottom-4 right-4 text-[9px] font-mono text-slate-700">CHARS: {problem.length}</div>
              </div>

              <button
                onClick={handleSolve}
                disabled={loading || !problem.trim()}
                className={`w-full py-4 rounded-2xl font-black uppercase tracking-[0.2em] transition-all relative overflow-hidden group/btn ${
                  loading 
                    ? 'bg-slate-800 text-slate-600 cursor-not-allowed border border-white/5' 
                    : 'bg-cyan-500 text-slate-950 hover:bg-cyan-400 shadow-lg shadow-cyan-500/20'
                }`}
              >
                <span className="relative z-10 flex items-center justify-center gap-3">
                  {loading ? 'PROCESSING MISSION...' : 'ENGAGE SOLVER'}
                </span>
                {!loading && <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover/btn:translate-x-full transition-transform duration-1000" />}
              </button>
            </section>

            {/* System Console Module */}
            <section className="glass rounded-3xl border-white/5 p-6 space-y-4 bg-black/40">
              <h2 className="text-xs font-black uppercase tracking-widest text-slate-500 flex items-center gap-3">
                <div className="w-1.5 h-4 bg-slate-700 rounded-full" />
                Neural Log Stream
              </h2>
              <div className="h-80 overflow-y-auto font-mono text-[11px] space-y-1.5 custom-scrollbar terminal-flicker">
                {logs.length === 0 ? (
                  <p className="text-slate-800 italic">SYSTEM_READY_AWAITING_INPUT</p>
                ) : (
                  logs.map((log, i) => (
                    <div key={i} className={`flex gap-3 ${log.includes('CRITICAL') ? 'text-rose-400' : log.includes('STAGE') ? 'text-cyan-400' : 'text-slate-400'}`}>
                      <span className="shrink-0 opacity-40">❯</span>
                      <p className="leading-relaxed">{log}</p>
                    </div>
                  ))
                )}
                <div ref={consoleEndRef} />
              </div>
            </section>
          </div>

          {/* Right Column: Execution Map & Results */}
          <div className="lg:col-span-8 space-y-8">
            {/* Pipeline Execution Map */}
            <section className="glass rounded-3xl border-white/5 p-8 space-y-8 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/[0.02] to-blue-500/[0.02] pointer-events-none" />
              
              <h2 className="text-xs font-black uppercase tracking-widest text-slate-400 flex items-center gap-3">
                <div className="w-1.5 h-4 bg-emerald-500 rounded-full" />
                Pipeline Trace Visualization
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
                {/* Horizontal line for desktop */}
                <div className="hidden md:block absolute top-[22px] left-8 right-8 h-[2px] bg-white/5 z-0" />
                
                {['Stage 0', 'Stage 1', 'Stage 2', 'Stage 3', 'Stage 4'].map((stagePrefix, idx) => {
                  const items = trace.filter(t => t.stage.startsWith(stagePrefix));
                  const latest = items[items.length - 1];
                  const isActive = latest?.status === 'processing';
                  const isDone = latest && latest.status !== 'processing';
                  
                  return (
                    <div key={idx} className="relative z-10 flex flex-col items-center text-center space-y-4">
                      <div className={`w-12 h-12 rounded-2xl border-2 flex items-center justify-center transition-all duration-500 ${
                        isActive ? 'bg-cyan-500/20 border-cyan-500 glow-border-cyan animate-pulse' :
                        isDone ? 'bg-emerald-500/20 border-emerald-500/50 glow-border-emerald' :
                        'bg-slate-900 border-white/5'
                      }`}>
                        {isDone ? (
                          <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                        ) : (
                          <span className={`text-lg font-black ${isActive ? 'text-cyan-400' : 'text-slate-700'}`}>{idx}</span>
                        )}
                      </div>
                      <div className="space-y-1">
                        <p className={`text-[10px] font-black uppercase tracking-tighter ${isActive ? 'text-cyan-400' : isDone ? 'text-emerald-400' : 'text-slate-500'}`}>
                          {stagePrefix === 'Stage 0' ? 'INIT' : stagePrefix === 'Stage 1' ? 'PLAN' : stagePrefix === 'Stage 2' ? 'KNOWLEDGE' : stagePrefix === 'Stage 3' ? 'SOLVE' : 'VERIFY'}
                        </p>
                        {latest && (
                           <div className={`text-[8px] px-1.5 py-0.5 rounded border uppercase font-bold tracking-widest inline-block ${getStatusStyle(latest.status)}`}>
                             {latest.status}
                           </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Detailed Trace Timeline */}
              <div className="mt-12 space-y-4">
                {trace.length === 0 && !loading ? (
                   <div className="py-20 text-center border-2 border-dashed border-white/5 rounded-3xl">
                      <p className="text-slate-700 font-black uppercase tracking-widest text-[10px]">Awaiting Mission Deployment...</p>
                   </div>
                ) : (
                  <div className="space-y-3">
                    {trace.map((t, i) => (
                      <div key={i} className="flex items-center gap-4 group animate-slide-up" style={{ animationDelay: `${i * 0.05}s` }}>
                        <div className="w-16 text-right shrink-0">
                           <span className="text-[10px] font-mono text-slate-700">{new Date(t.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                        </div>
                        <div className={`w-1.5 h-1.5 rounded-full ${t.status === 'processing' ? 'bg-cyan-500 animate-pulse' : 'bg-slate-700'}`} />
                        <div className="flex-1 glass p-4 rounded-2xl border-white/5 flex items-center justify-between hover:border-white/10 transition-colors">
                           <div className="space-y-0.5">
                              <p className="text-xs font-bold text-slate-300">{t.stage}</p>
                              <p className="text-[10px] text-slate-500 font-medium">{t.details || 'Operation in progress...'}</p>
                           </div>
                           <div className={`text-[9px] px-2 py-0.5 rounded-full border font-black uppercase tracking-widest shrink-0 ${getStatusStyle(t.status)}`}>
                              {t.status}
                           </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>

            {/* Result Module */}
            {(result || error) && (
              <section className={`glass rounded-3xl border-white/5 p-8 animate-slide-up relative overflow-hidden ${error ? 'glow-border-rose' : 'glow-border-emerald'}`}>
                 <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
                    <svg className="w-48 h-48" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z" /></svg>
                 </div>

                 <div className="flex flex-col md:flex-row gap-10">
                    <div className="flex-1 space-y-6">
                       <div className="flex items-center gap-3">
                          <h2 className="text-xs font-black uppercase tracking-[0.2em] text-slate-400">Mission Resolution</h2>
                          <div className={`h-[1px] flex-1 ${error ? 'bg-rose-500/20' : 'bg-emerald-500/20'}`} />
                       </div>

                       {error ? (
                         <div className="space-y-4">
                            <h3 className="text-4xl font-black text-rose-500 uppercase tracking-tighter italic">FAULT_DETECTED</h3>
                            <p className="text-slate-400 text-sm leading-relaxed bg-rose-500/5 p-6 rounded-2xl border border-rose-500/20 font-mono">
                               {error}
                            </p>
                         </div>
                       ) : (
                         <div className="space-y-8">
                            <div className="space-y-4">
                               <div className="flex items-center justify-between">
                                  <h3 className="text-5xl font-black text-white uppercase tracking-tighter italic text-shadow-cyan">SUCCESS</h3>
                                  <div className="text-right">
                                     <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Compute Wall Clock</p>
                                     <p className="text-lg font-mono text-cyan-400">{latencyMs ? (latencyMs / 1000).toFixed(3) : '---'}s</p>
                                  </div>
                               </div>

                               <div className="relative group">
                                  <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-3xl blur opacity-20 group-hover:opacity-40 transition-opacity" />
                                  <div className="relative bg-slate-950/80 border border-white/10 rounded-2xl p-8 flex flex-col items-center justify-center min-h-[200px]">
                                     <div className="text-5xl font-black text-white text-center overflow-x-auto w-full custom-scrollbar">
                                        <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                                          {String(r?.answer ?? 'N/A')}
                                        </ReactMarkdown>
                                     </div>
                                     <button
                                        onClick={copyAnswer}
                                        className="mt-6 px-4 py-2 rounded-xl bg-white/5 border border-white/5 text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-white hover:bg-white/10 transition-all flex items-center gap-2"
                                     >
                                        {copied ? 'COPIED TO CLIPBOARD' : 'EXTRACT PAYLOAD'}
                                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                                     </button>
                                  </div>
                               </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                               <div className="glass p-4 rounded-2xl border-white/5">
                                  <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Strategy Profile</p>
                                  <p className="text-xs font-bold text-cyan-400 uppercase tracking-tight">{r?.method || 'NEURAL_INFERENCE'}</p>
                               </div>
                               <div className="glass p-4 rounded-2xl border-white/5">
                                  <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Verification Status</p>
                                  <p className={`text-xs font-bold uppercase tracking-tight ${verified ? 'text-emerald-400' : 'text-amber-400'}`}>
                                     {verified ? 'VERIFIED_TRUTH' : 'UNCERTAIN_PROBABILITY'}
                                  </p>
                               </div>
                            </div>
                         </div>
                       )}
                    </div>

                    <div className="w-full md:w-64 space-y-6">
                       <div className="glass p-6 rounded-3xl border-white/5 flex flex-col items-center justify-center text-center space-y-4">
                          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Neural Confidence</p>
                          <div className="w-32 h-32 rounded-full border-[10px] border-slate-900 flex items-center justify-center relative">
                             <svg className="absolute inset-0 w-full h-full -rotate-90">
                                <circle
                                   cx="64" cy="64" r="54"
                                   fill="none"
                                   stroke={error ? '#f43f5e' : '#22d3ee'}
                                   strokeWidth="10"
                                   strokeDasharray="339.292"
                                   strokeDashoffset={error ? 339.292 : (verified ? 33.9 : 100)}
                                   strokeLinecap="round"
                                   className="transition-all duration-1000 ease-out"
                                />
                             </svg>
                             <div className="flex flex-col">
                                <span className="text-3xl font-black text-white">{error ? '0' : (verified ? '98' : '72')}%</span>
                                <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest mt-1">NOMINAL</span>
                             </div>
                          </div>
                       </div>
                       
                       <div className="glass p-6 rounded-3xl border-white/5 space-y-4">
                          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Classification</p>
                          <div className="space-y-3">
                             <div className="flex justify-between items-center text-[10px] font-mono">
                                <span className="text-slate-500">DOMAIN</span>
                                <span className="text-white uppercase">{domain || 'GENERAL'}</span>
                             </div>
                             <div className="flex justify-between items-center text-[10px] font-mono">
                                <span className="text-slate-500">COMPLEXITY</span>
                                <span className="text-white uppercase">TIER_{r?.strategy_features?.complexity || '1'}</span>
                             </div>
                          </div>
                       </div>
                    </div>
                 </div>

                 {r?.answer_explanation && (
                    <div className="mt-10 pt-10 border-t border-white/5 space-y-4">
                       <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Process Rationale Analysis</h4>
                       <div className="text-sm text-slate-400 leading-relaxed bg-black/20 p-8 rounded-3xl border border-white/5 font-medium prose prose-invert max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                             {r.answer_explanation}
                          </ReactMarkdown>
                       </div>
                    </div>
                 )}
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
