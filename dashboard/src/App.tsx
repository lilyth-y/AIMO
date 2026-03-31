import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Overview from './pages/Overview'
import Accuracy from './pages/Accuracy'
import Process from './pages/Process'
import ProblemViewer from './pages/ProblemViewer'
import Comparison from './pages/Comparison'

function NavLink({ to, label }: { to: string; label: string }) {
  const location = useLocation()
  const isActive = location.pathname === to

  return (
    <Link
      to={to}
      className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${isActive
          ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
        }`}
    >
      {label}
    </Link>
  )
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col selection:bg-cyan-500/30">
      <header className="sticky top-0 z-50 glass border-b border-white/5 px-6 py-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-indigo-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <span className="text-slate-950 font-bold text-lg">A</span>
            </div>
            <span className="font-bold text-xl tracking-tight text-white group-hover:text-cyan-400 transition-colors">
              AIMO <span className="text-slate-500 font-medium">Dashboard</span>
            </span>
          </Link>
          <nav className="flex items-center gap-1 bg-slate-900/40 p-1 rounded-full border border-white/5">
            <NavLink to="/" label="개요" />
            <NavLink to="/accuracy" label="정확도" />
            <NavLink to="/process" label="풀이 과정" />
            <NavLink to="/problems" label="문제/수식" />
            <NavLink to="/comparison" label="비교/분석" />
          </nav>
        </div>
      </header>

      <main className="flex-1 w-full max-w-6xl mx-auto px-6 py-12 animate-fade-in">
        {children}
      </main>

      <footer className="py-12 border-t border-white/5 text-center">
        <p className="text-slate-600 text-sm font-medium">
          &copy; 2026 AIMO Research Group. All rights reserved.
        </p>
      </footer>
    </div>
  )
}

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/accuracy" element={<Accuracy />} />
        <Route path="/process" element={<Process />} />
        <Route path="/problems" element={<ProblemViewer />} />
        <Route path="/comparison" element={<Comparison />} />
      </Routes>
    </Layout>
  )
}

export default App
