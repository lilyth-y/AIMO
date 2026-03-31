const stages = [
  { id: 'S1', title: 'Stage 1', name: 'Decomposition', desc: 'Labeling & Semantic Breakdown' },
  { id: 'S2', title: 'Stage 2', name: 'Retrieval', desc: 'Domain Experts Knowledge Fetching' },
  { id: 'S3', title: 'Stage 3', name: 'Routing', desc: 'Calculation Strategy Selection' },
  { id: 'S4', title: 'Stage 4', name: 'Execution', desc: 'Solving & Error Correction' },
  { id: 'S5', title: 'Stage 5', name: 'Verification', desc: 'Result Validation Router' },
]

export default function Overview() {
  return (
    <div className="space-y-20">
      {/* Hero Section */}
      <div className="space-y-6">
        <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl">
          Pipeline <span className="text-gradient">Intelligence</span>
        </h1>
        <p className="text-xl text-slate-400 max-w-3xl leading-relaxed">
          AIMO 5단계 파이프라인과 Fast Fail & Fallback 전략을 통한 고성능 수학 문제 풀이 시스템 개요입니다. 
          <span className="block mt-2 text-slate-500 text-lg">복잡한 논리 구조를 분해하고, 도메인 지식을 결합하여 최적의 해달을 도출합니다.</span>
        </p>
      </div>

      {/* Pipeline Visualization */}
      <section className="relative pt-10 pb-4">
        {/* Animated Connection Line */}
        <div className="absolute top-[76px] left-0 w-full px-12 hidden lg:block">
          <div className="pipeline-connection w-full" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-8 relative px-2">
          {stages.map((s, i) => (
            <div key={s.id} className="group flex flex-col items-center">
              {/* Stage Marker */}
              <div className="relative mb-8">
                <div className="absolute inset-0 bg-cyan-500/20 blur-xl rounded-full pulse-glow" />
                <div className="w-14 h-14 rounded-2xl bg-slate-900 border border-white/10 flex items-center justify-center relative z-10 group-hover:border-cyan-500/50 transition-all duration-300 ring-glow shadow-2xl">
                  <span className="text-base font-bold text-slate-400 group-hover:text-cyan-400 transition-colors">{s.id}</span>
                </div>
              </div>

              {/* Stage Card */}
              <div className="glass-premium p-6 rounded-2xl card-premium-hover w-full text-center border border-white/5">
                <div className="font-bold text-white text-lg mb-2 group-hover:text-cyan-400 transition-colors">{s.name}</div>
                <div className="text-xs text-slate-500 leading-relaxed font-medium uppercase tracking-wider">{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Mechanisms Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        <div className="glass-premium p-10 rounded-[2.5rem] card-premium-hover relative overflow-hidden group border border-white/5">
          <div className="absolute top-0 right-0 p-10 opacity-10 group-hover:opacity-20 transition-opacity">
            <svg className="w-24 h-24 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-cyan-400 ring-4 ring-cyan-400/20" />
            <span className="text-gradient-cyan">Fast Fail & Progress</span>
          </h3>
          <p className="text-slate-400 leading-relaxed text-base">
            각 단계에서 해를 찾지 못하거나 논리적 오류가 감지되면 즉시 다음 전략으로 Fallback 하거나 하위 문제로 분해하여 재시도합니다. 이는 불필요한 연산 낭비를 방지하고 성공 확률을 극대화합니다.
          </p>
        </div>

        <div className="glass-premium p-10 rounded-[2.5rem] card-premium-hover relative overflow-hidden group border border-white/5">
          <div className="absolute top-0 right-0 p-10 opacity-10 group-hover:opacity-20 transition-opacity">
            <svg className="w-24 h-24 text-amber-400 animate-spin-slow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ animationDuration: '8s' }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-amber-400 ring-4 ring-amber-400/20" />
            <span className="text-gradient-amber">RefineLoop Mechanism</span>
          </h3>
          <p className="text-slate-400 leading-relaxed text-base">
            검증 단계(Stage 5)에서 실패한 경우, 이전 단계의 컨텍스트를 유지한 채 Stage 3부터 다시 루프를 돌며 최적의 해를 찾아냅니다. 축적된 피드백을 통해 매 루프마다 문제 해결 전략을 정교화합니다.
          </p>
        </div>

        <div className="glass-premium p-10 rounded-[2.5rem] card-premium-hover relative overflow-hidden group border border-white/5 md:col-span-2">
          <div className="absolute top-0 right-0 p-10 opacity-5 group-hover:opacity-10 transition-opacity">
            <svg className="w-32 h-32 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118.75 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-indigo-400 ring-4 ring-indigo-400/20" />
            <span className="text-gradient">Core Strategy: Pass@k & Socratic Debate</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
            <div>
              <h4 className="text-lg font-bold text-slate-200 mb-2">Self-Consistency (Voting)</h4>
              <p className="text-slate-400 leading-relaxed text-sm">
                수학 문제의 정답은 단 하나의 수치로 <strong>수렴</strong>하지만, 계산 실수나 논리적 오류로 인한 오답은 제각기 다른 값으로 <strong>발산</strong>합니다. AIMO 파이프라인은 다양한 온도(Temperature)로 여러 해답 후보를 생성한 뒤 <strong>다수결 투표</strong>를 진행하여, 확률적 환각(Hallucination)을 수학적으로 상쇄시킵니다(Pass@k 원리).
              </p>
            </div>
            <div>
              <h4 className="text-lg font-bold text-slate-200 mb-2">Multi-Agent Debate</h4>
              <p className="text-slate-400 leading-relaxed text-sm">
                LLM은 정답을 '생성'하는 것보다 논리적 오류를 '검증'하는 데 훨씬 적은 인지 부하가 듭니다. Coder, Reviewer, Judge로 <strong>역할을 분리</strong>하여 LLM 특유의 확증 편향(자신이 내뱉은 토큰을 끝까지 정당화하려는 성향)을 끊어내고, 더 높은 정확도의 자기 교정(Self-Correction)을 달성합니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

