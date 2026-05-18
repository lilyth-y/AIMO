
export default function Methodology() {
  return (
    <div className="space-y-16 animate-fade-in">
      <div className="space-y-4">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
          The <span className="text-gradient">AI Usage</span> Skeleton
        </h1>
        <p className="text-xl text-slate-400 max-w-3xl leading-relaxed">
          본 프로젝트는 단순한 애플리케이션을 넘어, AI를 어떻게 구조적으로 활용하고 제어할 것인지에 대한 <strong>방법론적 뼈대(Skeleton)</strong>를 제시합니다.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        {/* Pattern 1 */}
        <div className="glass p-8 rounded-3xl border-white/5 space-y-6">
          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
            <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
          </div>
          <h2 className="text-2xl font-bold text-white">1. Plan-First Orchestration</h2>
          <p className="text-slate-400 leading-relaxed">
            AI에게 곧바로 답을 요구하는 대신, 문제의 <strong>특징을 분류(Classification)</strong>하고 <strong>해결 전략(Routing)</strong>을 먼저 수립하도록 강제합니다. 이는 LLM의 고질적인 문제인 '성급한 결론'과 '계산 실수'를 원천적으로 차단하는 프레임워크입니다.
          </p>
          <ul className="space-y-2 text-sm text-slate-500">
            <li className="flex items-center gap-2"><span className="w-1 h-1 bg-cyan-500 rounded-full" /> 시뮬레이션 가능 여부 판별</li>
            <li className="flex items-center gap-2"><span className="w-1 h-1 bg-cyan-500 rounded-full" /> 도메인 특화 지식 검색 및 주입</li>
          </ul>
        </div>

        {/* Pattern 2 */}
        <div className="glass p-8 rounded-3xl border-white/5 space-y-6">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
            <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
          </div>
          <h2 className="text-2xl font-bold text-white">2. Tool-Integrated Reasoning</h2>
          <p className="text-slate-400 leading-relaxed">
            AI의 자연어 생성 능력과 Python/SymPy 같은 <strong>결정론적 코드 실행기</strong>를 결합합니다. AI는 논리를 짜고, 도구는 계산을 수행함으로써 100% 신뢰할 수 있는 수학적 정답을 도출하는 '뉴로-심볼릭' 아키텍처를 구현합니다.
          </p>
          <ul className="space-y-2 text-sm text-slate-500">
            <li className="flex items-center gap-2"><span className="w-1 h-1 bg-indigo-500 rounded-full" /> 동적 Python 코드 생성 및 샌드박스 실행</li>
            <li className="flex items-center gap-2"><span className="w-1 h-1 bg-indigo-500 rounded-full" /> 심볼릭 라이브러리를 이용한 수식 검증</li>
          </ul>
        </div>

        {/* Pattern 3 */}
        <div className="glass p-8 rounded-3xl border-white/5 space-y-6">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
            <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
          </div>
          <h2 className="text-2xl font-bold text-white">3. Multi-Agent Audit Loop</h2>
          <p className="text-slate-400 leading-relaxed">
            단일 모델의 편향성을 극복하기 위해 <strong>Adversarial Red-Teaming</strong> 구조를 채택합니다. 공격 에이전트(Red)가 논리적 허점을 찾아내면, 방어 에이전트(Defender)가 이를 보완하거나 루브릭을 수정하는 자가 교정 프로세스를 거칩니다.
          </p>
          <ul className="space-y-2 text-sm text-slate-500">
            <li className="flex items-center gap-2"><span className="w-1 h-1 bg-emerald-500 rounded-full" /> 모델 간 상호 비판 및 투표</li>
            <li className="flex items-center gap-2"><span className="w-1 h-1 bg-emerald-500 rounded-full" /> 최종 결과에 대한 인간 감사(Human Audit) 인터페이스</li>
          </ul>
        </div>

        {/* Pattern 4 */}
        <div className="glass p-8 rounded-3xl border-white/5 space-y-6">
          <div className="w-12 h-12 rounded-xl bg-rose-500/10 flex items-center justify-center border border-rose-500/20">
            <svg className="w-6 h-6 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          </div>
          <h2 className="text-2xl font-bold text-white">4. Reverse-Engineering Data</h2>
          <p className="text-slate-400 leading-relaxed">
            데이터 오염을 방지하고 참신성을 확보하기 위해 <strong>정답으로부터 문제를 생성</strong>하는 역공학 엔진을 탑재했습니다. 이는 AI가 '보고 외운 문제'가 아닌, '처음 보는 논리 구조'를 해결하도록 훈련시키는 핵심 전략입니다.
          </p>
          <ul className="space-y-2 text-sm text-slate-500">
            <li className="flex items-center gap-2"><span className="w-1 h-1 bg-rose-500 rounded-full" /> 무작위 정답 및 수식 구조 생성</li>
            <li className="flex items-center gap-2"><span className="w-1 h-1 bg-rose-500 rounded-full" /> 논리적 무결성이 보장된 합성 데이터 파이프라인</li>
          </ul>
        </div>
      </div>

      <div className="bg-slate-900/50 p-10 rounded-[3rem] border border-white/5 text-center space-y-6">
        <h3 className="text-3xl font-bold text-white italic">"Process over Product"</h3>
        <p className="text-slate-400 max-w-2xl mx-auto leading-relaxed">
          이 스켈레톤은 결과물보다 <strong>사고의 과정</strong>을 정교하게 설계하는 데 집중합니다. 수강생들은 이 구조를 바탕으로 어떠한 복잡한 문제도 AI와 함께 해결해 나갈 수 있는 체계적인 능력을 갖추게 됩니다.
        </p>
      </div>
    </div>
  )
}
