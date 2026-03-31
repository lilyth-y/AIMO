import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'

interface ModelStats {
  name: string
  accuracy: number
  total_solved: number
  categories: {
    algebra: number
    geometry: number
    number_theory: number
    combinatorics: number
  }
}

interface ErrorType {
  type: string
  count: number
  description: string
  color: string
}

interface ComparisonData {
  dataset: string
  baseline_model: ModelStats
  aimo_agent: ModelStats
  error_analysis: ErrorType[]
}

const CUSTOM_COLORS = ['#ef4444', '#f59e0b', '#6366f1', '#64748b', '#14b8a6']

export default function Comparison() {
  const [data, setData] = useState<ComparisonData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/results/comparison_data.json')
      .then(res => res.json())
      .then(json => {
        setData(json)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load comparison data:', err)
        setLoading(false)
      })
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="w-8 h-8 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
    </div>
  )

  if (!data) return (
    <div className="glass p-8 rounded-3xl border-rose-500/20 text-rose-400 text-center">
      비교 데이터를 불러올 수 없습니다.
    </div>
  )

  const comparisonChartData = [
    {
      name: 'Algebra',
      [data.baseline_model.name]: data.baseline_model.categories.algebra,
      [data.aimo_agent.name]: data.aimo_agent.categories.algebra,
    },
    {
      name: 'Geometry',
      [data.baseline_model.name]: data.baseline_model.categories.geometry,
      [data.aimo_agent.name]: data.aimo_agent.categories.geometry,
    },
    {
      name: 'Number Theory',
      [data.baseline_model.name]: data.baseline_model.categories.number_theory,
      [data.aimo_agent.name]: data.aimo_agent.categories.number_theory,
    },
    {
      name: 'Combinatorics',
      [data.baseline_model.name]: data.baseline_model.categories.combinatorics,
      [data.aimo_agent.name]: data.aimo_agent.categories.combinatorics,
    }
  ]

  const errorChartData = data.error_analysis.map(err => ({
    name: err.type,
    value: err.count,
    color: err.color
  }))

  return (
    <div className="space-y-16 animate-fade-in">
      <div className="space-y-4 w-full">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Performance <span className="text-gradient">Comparisons</span>
          </h1>
          <div className="flex flex-col items-end gap-2 relative z-50">
            <div className="flex items-center gap-3 px-5 py-2.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 w-fit shadow-lg shadow-indigo-500/5">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse" />
              <span className="text-sm font-bold text-indigo-400">Evaluation Dataset:</span>
              <span className="text-sm font-black text-white">{data.dataset}</span>
            </div>
          </div>
        </div>
        <p className="text-lg text-slate-400 max-w-2xl leading-relaxed">
          격리(Isolate)가 증명된 글로벌 표준 벤치마크를 활용하여, Base 모델 대비 AIMO 에이전트의 범용적 성능(Generalization) 향상폭을 심층 분석합니다.<br/>
          <span className="text-sm border-l-2 border-cyan-500/50 pl-3 mt-3 block text-slate-500">
            <strong className="text-cyan-400/80">Key Driver:</strong> 성능 차이의 핵심은 단일 시도(Zero-shot)를 넘어서는 <strong>다수결 투표(Pass@k 수렴성)</strong>와 <strong>Multi-Agent 토론(확증 편향 제거)</strong> 메커니즘에 있습니다.
          </span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Baseline Card */}
        <div className="glass p-8 rounded-3xl border-white/5 relative overflow-hidden group">
          <div className="absolute inset-0 bg-slate-800/20 opacity-0 group-hover:opacity-100 transition-opacity" />
          <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-2">Baseline</h3>
          <h2 className="text-2xl font-bold text-white mb-6">{data.baseline_model.name}</h2>
          <div className="flex items-end gap-2">
            <span className="text-5xl font-black text-slate-300">{data.baseline_model.accuracy.toFixed(1)}</span>
            <span className="text-xl text-slate-500 font-bold mb-1">%</span>
          </div>
          <div className="mt-4 w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-slate-600" style={{ width: `${data.baseline_model.accuracy}%` }} />
          </div>
        </div>

        {/* AIMO Card */}
        <div className="glass-premium p-8 rounded-3xl relative overflow-hidden group">
          <div className="absolute inset-0 bg-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/20 blur-3xl rounded-full -mr-16 -mt-16" />
          <h3 className="text-sm font-bold text-cyan-500 uppercase tracking-widest mb-2 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
            Proposed
          </h3>
          <h2 className="text-2xl font-bold text-white mb-6">{data.aimo_agent.name}</h2>
          <div className="flex items-end gap-2">
            <span className="text-5xl font-black text-cyan-400">{data.aimo_agent.accuracy.toFixed(1)}</span>
            <span className="text-xl text-cyan-500/50 font-bold mb-1">%</span>
          </div>
          <div className="mt-4 w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-cyan-500 relative" style={{ width: `${data.aimo_agent.accuracy}%` }}>
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-[shimmer_2s_infinite]" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Radar/Bar Chart Section */}
        <div className="glass p-8 rounded-3xl border-white/5 space-y-8">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-500" />
            Category Accuracy Comparison
          </h2>
          <div className="h-[300px] w-full">
            <ResponsiveContainer>
              <BarChart data={comparisonChartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val}%`} />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                  itemStyle={{ color: '#f8fafc' }}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                <Bar dataKey={data.baseline_model.name} fill="#475569" radius={[4, 4, 0, 0]} />
                <Bar dataKey={data.aimo_agent.name} fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Error Analysis Section */}
        <div className="glass p-8 rounded-3xl border-white/5 space-y-8">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            Error Analysis (Incorrect Cases)
          </h2>
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="h-[200px] w-[200px] shrink-0">
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={errorChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {errorChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                    itemStyle={{ color: '#f8fafc' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="flex-1 space-y-4 w-full">
              {data.error_analysis.map((err, idx) => (
                <div key={idx} className="bg-slate-900/40 p-3 rounded-xl border border-white/5 flex items-start gap-3">
                  <div className="w-3 h-3 rounded-full mt-1.5 shrink-0" style={{ backgroundColor: err.color }} />
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-bold text-slate-200">{err.type}</span>
                      <span className="text-xs font-bold text-slate-500">{err.count} cases</span>
                    </div>
                    <p className="text-xs text-slate-400">{err.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
