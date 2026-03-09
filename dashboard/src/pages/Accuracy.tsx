import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

interface ResultsData {
  dataset: string
  timestamp: string
  results: any[]
}

const COLORS = ['#22d3ee', '#334155']

export default function Accuracy() {
  const [data, setData] = useState<ResultsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/results/numina_balanced_results.json')
      .then(res => res.json())
      .then(json => {
        setData(json)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load accuracy data:', err)
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
      데이터를 불러올 수 없습니다.
    </div>
  )

  const total = data.results.length
  const correct = data.results.filter(r => r.is_correct).length
  const accuracy = (correct / total) * 100

  const pieData = [
    { name: 'Correct', value: correct },
    { name: 'Incorrect', value: total - correct }
  ]

  return (
    <div className="space-y-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Success <span className="text-gradient">Analysis</span>
          </h1>
          <p className="text-slate-400 font-medium">
            Dataset: <span className="text-slate-200">{data.dataset}</span> • Last Run: <span className="text-slate-200">{new Date(data.timestamp).toLocaleDateString()}</span>
          </p>
        </div>
        <div className="flex gap-4">
          <div className="glass px-6 py-3 rounded-2xl border-white/5 shadow-xl">
            <div className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">Overall Accuracy</div>
            <div className="text-3xl font-black text-cyan-400">{accuracy.toFixed(1)}%</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 glass p-8 rounded-3xl border-white/5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-5">
            <div className="w-32 h-32 rounded-full border-[12px] border-cyan-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-8 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            Accuracy Distribution
          </h2>
          <div style={{ width: '100%', height: 350 }} className="flex items-center justify-center">
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={80}
                  outerRadius={110}
                  paddingAngle={8}
                  dataKey="value"
                  stroke="none"
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                  itemStyle={{ color: '#f8fafc' }}
                />
                <Legend iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass p-6 rounded-2xl border-white/5 card-hover">
            <div className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-4">Metric Breakdown</div>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-slate-400">Total Samples</span>
                  <span className="text-sm font-bold text-white">{total}</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-slate-400" style={{ width: '100%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-slate-400">Correct Answers</span>
                  <span className="text-sm font-bold text-emerald-400">{correct}</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500" style={{ width: `${accuracy}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-slate-400">Incorrect</span>
                  <span className="text-sm font-bold text-rose-400">{total - correct}</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-rose-500" style={{ width: `${100 - accuracy}%` }} />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-mesh p-6 rounded-2xl border border-cyan-500/10">
            <h4 className="text-cyan-400 font-bold text-sm mb-2">Evaluation Note</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              본 결과는 Balanced NuminaMath-1.5 서브셋을 기반으로 산출되었습니다. 난이도별 가중치가 적용되지 않은 순수 정확도 지표입니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
