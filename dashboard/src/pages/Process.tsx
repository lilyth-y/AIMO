import { useState, useEffect, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface Problem {
  problem: string
  solution: string
  answer: string
  source: string
  problem_type: string
  question_type: string
}

/* ─────── XAI 유형별 난이도 & 설명 ─────── */
const TYPE_META: Record<string, { difficulty: number; color: string; xaiNote: string }> = {
  Geometry: {
    difficulty: 85, color: 'rose',
    xaiNote: 'AI에게 "눈"이 없으므로, 도형을 좌표계로 변환하여 대수적으로 풀이합니다. 시각적 직관 없이 순수 기호 조작에 의존하기 때문에 증명 문제에서 특히 어려움을 겪습니다.',
  },
  Algebra: {
    difficulty: 40, color: 'emerald',
    xaiNote: 'AI가 가장 잘 해결하는 유형입니다. 기호 조작과 패턴 인식은 Transformer 아키텍처의 강점입니다.',
  },
  Combinatorics: {
    difficulty: 75, color: 'amber',
    xaiNote: '경우의 수를 체계적으로 세거나 구성적 증명을 하는 데 어려움을 겪습니다. "창의적 구성"이 필요한 문제에서 실패율이 높습니다.',
  },
  'Number Theory': {
    difficulty: 70, color: 'indigo',
    xaiNote: '모듈러 연산과 소수 판별은 잘 수행하지만, 복잡한 정수론적 논증에서는 논리적 비약이 발생할 수 있습니다.',
  },
  Inequalities: {
    difficulty: 65, color: 'cyan',
    xaiNote: 'AM-GM, Cauchy-Schwarz 등 표준 기법은 잘 적용하지만, 비표준적 부등식 증명에서 실패합니다.',
  },
  Calculus: {
    difficulty: 35, color: 'emerald',
    xaiNote: '미분·적분 공식 적용은 기계적으로 잘 수행합니다. 절차적 계산에 강합니다.',
  },
  Other: {
    difficulty: 50, color: 'slate',
    xaiNote: '분류되지 않은 기타 유형입니다.',
  },
}

/* ─────── 기하학 XAI 데모 단계 ─────── */
const GEO_STEPS = [
  {
    label: '원래 문제 (시각적)',
    content: '> "삼각형 ABC에서 꼭짓점 A에서 BC로 내린 수선의 발 D, DM⊥AC, DN⊥BC..."\n\n사람은 삼각형을 **머릿속에 그려서** 직관적으로 이해합니다.\n\n하지만 AI에게는 **시각 능력이 없습니다**.',
  },
  {
    label: 'AI 번역: 좌표 변환',
    content: 'AI는 기하학 문제를 **좌표계로 변환**합니다:\n\n$$A=(x_a, y_a),\\quad B=(0,0),\\quad C=(c, 0)$$\n\n수선의 발 D는 정사영으로 계산:\n$$D = \\left(\\frac{\\vec{BA}\\cdot\\vec{BC}}{|\\vec{BC}|^2}\\right)\\vec{BC}$$',
  },
  {
    label: 'AI 풀이: 대수적 계산',
    content: '좌표가 설정되면, 모든 기하학적 관계가 **방정식**이 됩니다:\n\n- 수직 조건: $\\vec{DM}\\cdot\\vec{AC}=0$\n- 거리 공식: $|PQ|=\\sqrt{(x_p-x_q)^2+(y_p-y_q)^2}$\n- 각도: $\\cos\\theta=\\frac{\\vec{u}\\cdot\\vec{v}}{|\\vec{u}||\\vec{v}|}$\n\n→ 시각적 직관 없이 **순수 기호 조작**으로 풀이',
  },
  {
    label: 'XAI 관점: 한계',
    content: '### 왜 기하학이 어려운가?\n\n1. **보조선 문제**: 사람은 직관으로 그리지만, AI는 모든 가능한 보조선을 탐색해야 합니다\n2. **증명 vs 계산**: 좌표 기하학은 "값"은 계산할 수 있지만, "왜"를 설명하기 어렵습니다\n3. **시각적 패턴**: 대칭, 닮음 등 시각적으로 명백한 관계를 AI는 대수적으로 발견해야 합니다',
  },
]

/* ─────── 단계별 풀이 시연 ─────── */
const DEMO_STEPS = [
  {
    label: '1단계: 문제 해석', color: 'cyan',
    content: '주어진 조건을 파악합니다:\n- 평면 벡터 $\\vec{a}=(1,2)$\n- $|\\vec{c}|=3\\sqrt{5}$, $\\vec{a} \\parallel \\vec{c}$\n\n→ 병렬 조건에서 $\\vec{c}=\\lambda \\vec{a}$임을 도출',
  },
  {
    label: '2단계: 수학적 변환', color: 'indigo',
    content: '$\\vec{c}=(\\lambda, 2\\lambda)$로 놓으면\n\n$$|\\vec{c}|=\\sqrt{\\lambda^2+(2\\lambda)^2}=\\sqrt{5\\lambda^2}=3\\sqrt{5}$$\n\n$$\\lambda^2=9 \\implies \\lambda=\\pm 3$$',
  },
  {
    label: '3단계: 내적 계산', color: 'emerald',
    content: '$(4\\vec{a}-\\vec{b})\\perp(2\\vec{a}+\\vec{b})$ 조건에서\n\n$$(4\\vec{a}-\\vec{b})\\cdot(2\\vec{a}+\\vec{b})=0$$\n$$8|\\vec{a}|^2+2\\vec{a}\\cdot\\vec{b}-|\\vec{b}|^2=0$$\n$$8\\times5+2\\vec{a}\\cdot\\vec{b}-45=0$$',
  },
  {
    label: '4단계: 최종 답 도출', color: 'amber',
    content: '$$\\vec{a}\\cdot\\vec{b}=\\frac{5}{2}$$\n\n$$\\cos\\theta=\\frac{\\vec{a}\\cdot\\vec{b}}{|\\vec{a}|\\times|\\vec{b}|}=\\frac{\\frac{5}{2}}{\\sqrt{5}\\times3\\sqrt{5}}=\\boxed{\\frac{1}{6}}$$',
  },
]

const colorMap: Record<string, string> = {
  cyan: 'border-cyan-500/30 bg-cyan-500/5',
  indigo: 'border-indigo-500/30 bg-indigo-500/5',
  emerald: 'border-emerald-500/30 bg-emerald-500/5',
  amber: 'border-amber-500/30 bg-amber-500/5',
}

const dotColorMap: Record<string, string> = {
  cyan: 'bg-cyan-400', indigo: 'bg-indigo-400', emerald: 'bg-emerald-400', amber: 'bg-amber-400',
}

const diffBarColor: Record<string, string> = {
  rose: 'bg-rose-500', emerald: 'bg-emerald-500', amber: 'bg-amber-500',
  indigo: 'bg-indigo-500', cyan: 'bg-cyan-500', slate: 'bg-slate-500',
}

export default function Process() {
  const [activeStep, setActiveStep] = useState(0)
  const [geoStep, setGeoStep] = useState(0)
  const [problems, setProblems] = useState<Problem[]>([])
  const [selectedIdx, setSelectedIdx] = useState(0)

  useEffect(() => {
    fetch('/numina_eval_balanced.json')
      .then(r => r.json())
      .then(d => setProblems(d))
      .catch(() => { })
  }, [])

  const typeStats = useMemo(() => {
    const map = new Map<string, { count: number; proofCount: number; sources: Set<string> }>()
    problems.forEach(p => {
      const t = p.problem_type || 'Other'
      if (!map.has(t)) map.set(t, { count: 0, proofCount: 0, sources: new Set() })
      const s = map.get(t)!
      s.count++
      if (p.question_type === 'proof') s.proofCount++
      s.sources.add(p.source)
    })
    return [...map.entries()]
      .map(([type, stats]) => ({
        type, ...stats,
        meta: TYPE_META[type] || TYPE_META.Other,
      }))
      .sort((a, b) => b.count - a.count)
  }, [problems])

  const selectedProblem = problems[selectedIdx]
  const Md = ({ children }: { children: string }) => (
    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>{children}</ReactMarkdown>
  )

  return (
    <div className="space-y-16">
      {/* ────────── 헤더 ────────── */}
      <div className="space-y-4">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
          XAI <span className="text-gradient">Reasoning</span>
        </h1>
        <p className="text-lg text-slate-400 max-w-3xl leading-relaxed">
          <strong className="text-white">설명 가능한 AI(XAI)</strong> 관점에서 수학 문제 풀이 과정을 분석합니다.
          AI에게 <strong className="text-cyan-400">"눈"이 없는 상태</strong>에서 기하학 문제를 어떻게 풀고,
          유형별 난이도 차이가 왜 발생하는지 설명합니다.
        </p>
      </div>

      {/* ────────── 블랙박스 설명 ────────── */}
      <section className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center gap-3">
          <span className="w-8 h-8 rounded-lg bg-rose-500/20 flex items-center justify-center text-[10px] font-black text-rose-400">B</span>
          AI 블랙박스란?
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass rounded-2xl p-6 border-cyan-500/20 text-center space-y-3">
            <div className="w-10 h-10 mx-auto rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center font-black text-cyan-400 text-sm">IN</div>
            <h3 className="font-bold text-cyan-400">입력 (Input)</h3>
            <p className="text-sm text-slate-400">수학 문제가 <strong className="text-white">텍스트</strong>로 입력됩니다. 도형, 그래프 등 시각 정보는 모두 기호로 변환됩니다.</p>
          </div>
          <div className="glass rounded-2xl p-6 border-rose-500/30 bg-rose-500/[0.03] text-center space-y-3 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-rose-500/5 to-transparent pointer-events-none" />
            <div className="w-10 h-10 mx-auto rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center font-black text-rose-400 text-sm">?</div>
            <h3 className="font-bold text-rose-400">블랙박스</h3>
            <p className="text-sm text-slate-400"><strong className="text-rose-300">수십억 파라미터</strong>가 상호작용. <em>어떤 경로</em>로 답에 도달했는지 관찰 불가.</p>
            <div className="flex justify-center gap-1">
              {[...Array(7)].map((_, i) => (
                <div key={i} className="w-2 h-2 rounded-full bg-rose-500/40 animate-pulse" style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
          </div>
          <div className="glass rounded-2xl p-6 border-emerald-500/20 text-center space-y-3">
            <div className="w-10 h-10 mx-auto rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center font-black text-emerald-400 text-sm">CoT</div>
            <h3 className="font-bold text-emerald-400">출력 (Output)</h3>
            <p className="text-sm text-slate-400">CoT를 통해 <strong className="text-emerald-300">중간 추론 과정</strong>을 함께 출력하여 <strong className="text-white">해석 가능성</strong>을 확보합니다.</p>
          </div>
        </div>
      </section>

      {/* ────────── 유형별 난이도 분석 ────────── */}
      {typeStats.length > 0 && (
        <section className="space-y-6">
          <h2 className="text-2xl font-bold flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-[10px] font-black text-amber-400">D</span>
            유형별 난이도 분석
          </h2>
          <p className="text-slate-400 text-sm max-w-2xl">
            데이터셋의 <strong className="text-white">{problems.length}개 문제</strong>를 유형별로 분류하고,
            AI가 각 유형에서 겪는 어려움의 정도를 분석합니다.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {typeStats.map(s => (
              <div key={s.type} className="glass rounded-2xl p-5 border-white/5 card-hover group space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-white">{s.type}</h3>
                    <span className="text-xs text-slate-500">{s.count}문제 · 증명형 {s.proofCount}개</span>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-bold border ${s.meta.difficulty >= 70 ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                      s.meta.difficulty >= 50 ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                        'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    }`}>
                    {s.meta.difficulty >= 70 ? 'High' : s.meta.difficulty >= 50 ? 'Med' : 'Low'} Difficulty
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-500">AI 해결 난이도</span>
                    <span className="text-slate-400 font-mono">{s.meta.difficulty}/100</span>
                  </div>
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all ${diffBarColor[s.meta.color]}`}
                      style={{ width: `${s.meta.difficulty}%` }} />
                  </div>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed border-t border-white/5 pt-3">{s.meta.xaiNote}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ────────── 기하학 without Eyes ────────── */}
      <section className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center gap-3">
          <span className="w-8 h-8 rounded-lg bg-rose-500/20 flex items-center justify-center text-[10px] font-black text-rose-400">G</span>
          "눈 없는 AI"의 기하학 풀이
        </h2>
        <p className="text-slate-400 text-sm max-w-2xl">
          인간은 도형을 <strong className="text-white">시각적으로</strong> 인식합니다. 하지만 AI에게는 눈이 없습니다.
          AI가 기하학 문제를 어떻게 "보지 않고" 풀이하는지 단계별로 확인하세요.
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
          <div className="space-y-3">
            {GEO_STEPS.map((step, i) => (
              <button key={i} onClick={() => setGeoStep(i)}
                className={`w-full text-left px-4 py-3 rounded-xl border transition-all flex items-center gap-3 ${geoStep === i ? 'border-rose-500/30 bg-rose-500/5 shadow-lg' : 'border-white/5 bg-white/[0.02] hover:bg-white/[0.05]'
                  }`}>
                <span className={`w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-black ${geoStep === i ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-500'}`}>{i + 1}</span>
                <span className={`text-sm font-semibold ${geoStep === i ? 'text-white' : 'text-slate-400'}`}>{step.label}</span>
              </button>
            ))}
          </div>
          <div className="glass rounded-2xl p-8 border-rose-500/10 bg-rose-500/[0.02] transition-all min-h-[280px]">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-2 h-2 rounded-full bg-rose-400" />
              <h3 className="font-bold text-lg">{GEO_STEPS[geoStep].label}</h3>
            </div>
            <div className="prose prose-invert max-w-none prose-p:leading-relaxed text-slate-200 prose-blockquote:border-rose-500/30 prose-blockquote:text-slate-300 prose-h3:text-rose-400">
              <Md>{GEO_STEPS[geoStep].content}</Md>
            </div>
          </div>
        </div>
      </section>

      {/* ────────── 대수학 풀이 시연 ────────── */}
      <section className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center gap-3">
          <span className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center text-[10px] font-black text-cyan-400">A</span>
          대수학 풀이 시연
        </h2>
        <p className="text-slate-400 text-sm">벡터 문제의 단계별 추론 과정을 따라가 보세요.</p>
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
          <div className="space-y-3">
            {DEMO_STEPS.map((step, i) => (
              <button key={i} onClick={() => setActiveStep(i)}
                className={`w-full text-left px-4 py-3 rounded-xl border transition-all flex items-center gap-3 ${activeStep === i ? `${colorMap[step.color]} shadow-lg` : 'border-white/5 bg-white/[0.02] hover:bg-white/[0.05]'
                  }`}>
                <span className={`w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-black ${activeStep === i ? `${dotColorMap[step.color].replace('bg-', 'bg-')}/20 text-white` : 'bg-slate-800 text-slate-500'}`}>{i + 1}</span>
                <span className={`text-sm font-semibold ${activeStep === i ? 'text-white' : 'text-slate-400'}`}>{step.label}</span>
              </button>
            ))}
          </div>
          <div className={`glass rounded-2xl p-8 ${colorMap[DEMO_STEPS[activeStep].color]} transition-all min-h-[280px]`}>
            <div className="flex items-center gap-2 mb-6">
              <div className={`w-2 h-2 rounded-full ${dotColorMap[DEMO_STEPS[activeStep].color]}`} />
              <h3 className="font-bold text-lg">{DEMO_STEPS[activeStep].label}</h3>
            </div>
            <div className="prose prose-invert max-w-none prose-p:leading-relaxed text-slate-200">
              <Md>{DEMO_STEPS[activeStep].content}</Md>
            </div>
          </div>
        </div>
      </section>

      {/* ────────── CoT 풀이 탐색 ────────── */}
      {problems.length > 0 && (
        <section className="space-y-6">
          <h2 className="text-2xl font-bold flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center text-[10px] font-black text-indigo-400">C</span>
            실제 CoT 풀이 탐색
          </h2>
          <div className="flex flex-wrap gap-2">
            {problems.slice(0, 12).map((p, i) => (
              <button key={i} onClick={() => setSelectedIdx(i)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${selectedIdx === i ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-white/[0.03] text-slate-500 border border-white/5 hover:text-slate-300'
                  }`}>
                #{i + 1} {p.problem_type}
              </button>
            ))}
          </div>

          {selectedProblem && (
            <div className="glass rounded-2xl overflow-hidden border-white/5">
              <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                <div className="flex items-center gap-3">
                  <span className="px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-400 text-[10px] font-bold uppercase border border-cyan-500/20">{selectedProblem.source}</span>
                  <span className="px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 text-[10px] font-bold border border-indigo-500/20">{selectedProblem.problem_type}</span>
                  <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 text-[10px] font-bold border border-amber-500/20">{selectedProblem.question_type}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">Answer:</span>
                  <div className="px-3 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 text-sm font-bold border border-emerald-500/20">
                    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]} components={{ p: ({ node, ...props }) => <span {...props} /> }}>
                      {`$${selectedProblem.answer || 'proof'}$`}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
              <div className="p-6 space-y-6">
                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-cyan-500" />Problem</div>
                  <div className="bg-slate-900/40 p-6 rounded-2xl border border-white/5 prose prose-invert max-w-none text-base leading-relaxed">
                    <Md>{selectedProblem.problem}</Md>
                  </div>
                </div>
                <details className="group/details">
                  <summary className="flex items-center gap-2 text-xs font-bold text-slate-500 cursor-pointer hover:text-slate-300 transition-colors uppercase tracking-widest list-none">
                    <span className="w-4 h-4 rounded-md bg-slate-800 flex items-center justify-center group-open/details:rotate-90 transition-transform">
                      <svg width="6" height="10" viewBox="0 0 6 10" fill="none"><path d="M1 1L5 5L1 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                    </span>
                    Chain of Thought
                  </summary>
                  <div className="mt-4 bg-indigo-500/[0.03] p-6 rounded-2xl border border-indigo-500/10 prose prose-invert max-w-none text-sm leading-relaxed">
                    <Md>{selectedProblem.solution}</Md>
                  </div>
                </details>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
