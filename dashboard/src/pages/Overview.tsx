const stages = [
  { id: 'S1', title: 'Stage 1', name: 'Decomposition', desc: 'Labeling & Semantic Breakdown' },
  { id: 'S2', title: 'Stage 2', name: 'Retrieval', desc: 'Domain Experts Knowledge Fetching' },
  { id: 'S3', title: 'Stage 3', name: 'Routing', desc: 'Calculation Strategy Selection' },
  { id: 'S4', title: 'Stage 4', name: 'Execution', desc: 'Solving & Error Correction' },
  { id: 'S5', title: 'Stage 5', name: 'Verification', desc: 'Result Validation Router' },
]

export default function Overview() {
  return (
    <div className="space-y-16">
      <div className="space-y-4">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
          Pipeline <span className="text-gradient">Intelligence</span>
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl leading-relaxed">
          AIMO 5단계 파이프라인과 Fast Fail & Fallback 전략을 통한 고성능 수학 문제 풀이 시스템 개요입니다.
        </p>
      </div>

      <section className="relative px-4">
        {/* Connection Line */}
        <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gradient-to-r from-cyan-500/20 via-indigo-500/20 to-emerald-500/20 -translate-y-1/2 hidden lg:block" />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 relative">
          {stages.map((s, i) => (
            <div key={s.id} className="group flex flex-col items-center">
              <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-white/10 flex items-center justify-center mb-6 z-10 group-hover:border-cyan-500/50 transition-colors shadow-xl">
                <span className="text-sm font-bold text-slate-500 group-hover:text-cyan-400">{s.id}</span>
              </div>
              <div className="glass p-5 rounded-2xl border border-white/5 card-hover w-full text-center">
                <div className="font-bold text-white mb-1">{s.name}</div>
                <div className="text-xs text-slate-500 leading-relaxed">{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="glass p-8 rounded-3xl border border-white/5 card-hover relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
            <div className="w-24 h-24 rounded-full border-8 border-cyan-400" />
          </div>
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            Fast Fail & Progress
          </h3>
          <p className="text-slate-400 leading-relaxed text-sm">
            각 단계에서 해를 찾지 못하거나 논리적 오류가 감지되면 즉시 다음 전략으로 Fallback 하거나 하위 문제로 분해하여 재시도합니다.
          </p>
        </div>

        <div className="glass p-8 rounded-3xl border border-white/5 card-hover relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
            <div className="w-24 h-24 rounded-full border-8 border-amber-400 animate-pulse" />
          </div>
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            RefineLoop Mechanism
          </h3>
          <p className="text-slate-400 leading-relaxed text-sm">
            검증 단계(Stage 5)에서 실패한 경우, 이전 단계의 컨텍스트를 유지한 채 Stage 3부터 다시 루프를 돌며 최적의 해를 찾아냅니다.
          </p>
        </div>
      </div>
    </div>
  )
}
