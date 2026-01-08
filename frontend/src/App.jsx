import { useState, useEffect, useRef } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell
} from 'recharts'

const getApiBase = () => {
  const url = import.meta.env.VITE_API_URL || ''
  return url.endsWith('/api') ? url : url + '/api'
}
const API_BASE = getApiBase()

const COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']

function App() {
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [trends, setTrends] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [terminalLogs, setTerminalLogs] = useState([])
  const [isTerminalConnected, setIsTerminalConnected] = useState(false)
  const [summaries, setSummaries] = useState([])
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [agentProfitData, setAgentProfitData] = useState([])

  useEffect(() => {
    fetchRuns()
    fetchTrends()
    fetchLatestRunForTerminal()
    fetchSummaries()
    fetchAgents()
  }, [])

  const fetchRuns = async () => {
    try {
      const res = await fetch(`${API_BASE}/runs`)
      if (res.ok) {
        const data = await res.json()
        setRuns(data.runs || [])
      }
    } catch (e) {
      console.error('Failed to fetch runs:', e)
    }
  }

  const fetchTrends = async () => {
    try {
      const res = await fetch(`${API_BASE}/analysis/trends`)
      if (res.ok) {
        const data = await res.json()
        setTrends(data)
      }
    } catch (e) {
      console.error('Failed to fetch trends:', e)
    }
  }

  const fetchSummaries = async () => {
    try {
      const res = await fetch(`${API_BASE}/summaries`)
      if (res.ok) {
        const data = await res.json()
        setSummaries(data.summaries || [])
      }
    } catch (e) {
      console.error('Failed to fetch summaries:', e)
    }
  }

  const fetchAgents = async () => {
    try {
      const res = await fetch(`${API_BASE}/agents`)
      if (res.ok) {
        const data = await res.json()
        setAgents(data.agents || [])
        if (data.agents?.length > 0) {
          setSelectedAgent(data.agents[0])
        }
      }
    } catch (e) {
      console.error('Failed to fetch agents:', e)
    }
  }

  const fetchAgentProfits = async (agentName) => {
    if (!agentName) return
    try {
      const res = await fetch(`${API_BASE}/agents/${agentName}/profits`)
      if (res.ok) {
        const data = await res.json()
        const grouped = {}
        data.data?.forEach(item => {
          const runKey = `Run ${item.run}`
          if (!grouped[runKey]) {
            grouped[runKey] = { run: item.run, name: runKey }
          }
          grouped[runKey].profit = item.profit
        })
        setAgentProfitData(Object.values(grouped))
      }
    } catch (e) {
      console.error('Failed to fetch agent profits:', e)
    }
  }

  useEffect(() => {
    if (selectedAgent) {
      fetchAgentProfits(selectedAgent)
    }
  }, [selectedAgent])

  const fetchLatestRunForTerminal = async () => {
    try {
      const res = await fetch(`${API_BASE}/runs`)
      if (res.ok) {
        const data = await res.json()
        const latestRun = data.runs?.find(r => r.status === 'completed')
        if (latestRun) {
          const detailRes = await fetch(`${API_BASE}/runs/${latestRun.id}`)
          if (detailRes.ok) {
            const detail = await detailRes.json()
            generateTerminalLogs(detail)
            setIsTerminalConnected(true)
          }
        }
      }
    } catch (e) {
      console.error('Failed to fetch terminal data:', e)
    }
  }

  const generateTerminalLogs = (runDetail) => {
    const logs = []
    const timestamp = new Date(runDetail.start_time).toLocaleString()

    logs.push(`%c[SYSTEM]%c =========================================`)
    logs.push(`%c[SYSTEM]%c   DEFI AGENT ARENA - SIMULATION LOG`)
    logs.push(`%c[SYSTEM]%c =========================================`)
    logs.push(`%c[SYSTEM]%c Session: ${runDetail.id} | ${timestamp}`)
    logs.push(`%c[SYSTEM]%c -----------------------------------------`)

    const actions = runDetail.actions || []
    actions.forEach((action, i) => {
      const actionEmoji = {
        'swap': '<->',
        'provide_liquidity': '~',
        'propose_alliance': '=',
        'do_nothing': 'z'
      }[action.action_type] || '.'

      const turnPrefix = `[T${action.turn}]`
      logs.push(`%c[AGENT]%c ${turnPrefix} ${action.agent_name}: ${actionEmoji} ${action.action_type}`)
      if (action.reasoning) {
        const shortReason = action.reasoning.substring(0, 80).replace(/\n/g, ' ')
        logs.push(`%c[REASON]%c   "${shortReason}..."`)
      }
    })

    logs.push(`%c[SYSTEM]%c -----------------------------------------`)
    logs.push(`%c[METRICS]%c Gini: ${runDetail.metrics?.gini_coefficient?.toFixed(4) || 0} | Profit: ${runDetail.metrics?.avg_agent_profit?.toFixed(2) || 0}`)
    logs.push(`%c[SYSTEM]%c =========================================`)

    setTerminalLogs(logs)
  }

  const selectRun = async (runId) => {
    try {
      const res = await fetch(`${API_BASE}/runs/${runId}`)
      if (res.ok) {
        const data = await res.json()
        setSelectedRun(data)
        if (activeTab === 'terminal') {
          generateTerminalLogs(data)
        }
      }
    } catch (e) {
      console.error('Failed to fetch run details:', e)
    }
  }

  const formatTime = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    })
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-700 rounded-xl flex items-center justify-center">
                <svg width="28" height="28" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="rgba(255,255,255,0.2)"/>
                  <circle cx="35" cy="45" r="10" fill="white"/>
                  <circle cx="65" cy="45" r="10" fill="white"/>
                  <circle cx="50" cy="68" r="10" fill="white"/>
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">DeFi Agent Arena</h1>
                <p className="text-slate-500 text-sm">Multi-Agent LLM Simulation</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                trends ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                <span className={`w-2 h-2 rounded-full ${trends ? 'bg-green-400' : 'bg-red-400'}`}></span>
                <span className="text-sm font-medium">{trends ? 'Live' : 'Offline'}</span>
              </div>
            </div>
          </div>

          {/* Stats Bar */}
          {trends && (
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-slate-800/50 rounded-lg px-4 py-3 border border-slate-700/50">
                <div className="text-slate-400 text-xs uppercase tracking-wide">Total Runs</div>
                <div className="text-2xl font-bold text-white mt-1">{trends.run_count}</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg px-4 py-3 border border-slate-700/50">
                <div className="text-slate-400 text-xs uppercase tracking-wide">Avg Profit</div>
                <div className={`text-2xl font-bold mt-1 ${trends.avg_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {trends.avg_profit >= 0 ? '+' : ''}{trends.avg_profit?.toFixed(2) || 0}
                </div>
              </div>
              <div className="bg-slate-800/50 rounded-lg px-4 py-3 border border-slate-700/50">
                <div className="text-slate-400 text-xs uppercase tracking-wide">Inequality</div>
                <div className="text-2xl font-bold text-white mt-1">{(trends.avg_gini * 100).toFixed(1)}%</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg px-4 py-3 border border-slate-700/50">
                <div className="text-slate-400 text-xs uppercase tracking-wide">Trend</div>
                <div className="text-2xl font-bold text-white mt-1 capitalize">{trends.profit_trend}</div>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-6xl mx-auto px-6 pt-6 flex gap-2">
        {['dashboard', 'summaries', 'terminal'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab
                ? 'bg-green-500 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {activeTab === 'dashboard' ? (
          <>
            {/* Runs Grid */}
            <section className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">Simulation Runs</h2>
                <button
                  onClick={() => { fetchRuns(); fetchTrends(); }}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 text-sm transition-colors"
                >
                  Refresh
                </button>
              </div>
              {runs.length === 0 ? (
                <div className="bg-slate-800/50 rounded-xl p-12 text-center border border-slate-700/50">
                  <p className="text-slate-500">No runs yet. Trigger a simulation to get started.</p>
                </div>
              ) : (
                <div className="grid gap-3">
                  {runs.map((run) => (
                    <div
                      key={run.id}
                      onClick={() => selectRun(run.id)}
                      className={`bg-slate-800/50 rounded-xl p-4 border cursor-pointer transition-all hover:bg-slate-800 hover:border-slate-600 ${
                        selectedRun?.id === run.id ? 'border-green-500/50 bg-slate-800' : 'border-slate-700/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-sm ${
                            run.status === 'completed'
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-yellow-500/20 text-yellow-400'
                          }`}>
                            #{run.run_number}
                          </div>
                          <div>
                            <div className="text-white font-medium">Run {run.run_number}</div>
                            <div className="text-slate-500 text-sm">{formatTime(run.start_time)}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            run.status === 'completed'
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-yellow-500/20 text-yellow-400'
                          }`}>
                            {run.status}
                          </span>
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-slate-600">
                            <path d="M9 18l6-6-6-6"/>
                          </svg>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Run Detail */}
            {selectedRun && (
              <section className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-white">Run #{selectedRun.run_number} Details</h2>
                  <button
                    onClick={() => setSelectedRun(null)}
                    className="text-slate-500 hover:text-white transition-colors"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                  </button>
                </div>

                {/* Metrics */}
                {selectedRun.metrics && (
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/30">
                      <div className="text-slate-400 text-sm mb-1">Gini Coefficient</div>
                      <div className="text-2xl font-bold text-white">{selectedRun.metrics.gini_coefficient?.toFixed(4)}</div>
                      <div className="text-xs text-slate-500 mt-1">Equality measure</div>
                    </div>
                    <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/30">
                      <div className="text-slate-400 text-sm mb-1">Avg Profit</div>
                      <div className={`text-2xl font-bold ${selectedRun.metrics.avg_agent_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {selectedRun.metrics.avg_agent_profit >= 0 ? '+' : ''}{selectedRun.metrics.avg_agent_profit?.toFixed(2)}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">Per agent</div>
                    </div>
                    <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/30">
                      <div className="text-slate-400 text-sm mb-1">Cooperation</div>
                      <div className="text-2xl font-bold text-white">{selectedRun.metrics.cooperation_rate?.toFixed(1)}%</div>
                      <div className="text-xs text-slate-500 mt-1">Alliance rate</div>
                    </div>
                  </div>
                )}

                {/* Agent Cards */}
                <h3 className="text-white font-medium mb-3">Agents</h3>
                <div className="grid grid-cols-5 gap-3">
                  {(selectedRun.agent_states || []).map((agent, i) => (
                    <div key={i} className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/30">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-white font-bold text-sm">
                          {agent.agent_name.split('_')[1]}
                        </div>
                        <div className="text-white font-medium text-sm">{agent.agent_name}</div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">Token A</span>
                          <span className="text-white">{agent.token_a_balance?.toFixed(0)}</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">Token B</span>
                          <span className="text-white">{agent.token_b_balance?.toFixed(0)}</span>
                        </div>
                        <div className="pt-2 border-t border-slate-600/30">
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-400">Profit</span>
                            <span className={`text-sm font-bold ${agent.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {agent.profit >= 0 ? '+' : ''}{agent.profit?.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 pt-3 border-t border-slate-600/30">
                        <span className="text-xs text-slate-500 capitalize">{agent.strategy?.replace('_', ' ')}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        ) : activeTab === 'summaries' ? (
          <>
            {/* Agent Profit Chart */}
            <section className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6 mb-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-white">Agent Performance</h2>
                  <p className="text-slate-500 text-sm">Profit trajectory across runs</p>
                </div>
                <select
                  value={selectedAgent || ''}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-700 text-white border border-slate-600 text-sm"
                >
                  {agents.map(agent => (
                    <option key={agent} value={agent}>{agent}</option>
                  ))}
                </select>
              </div>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={agentProfitData}>
                    <defs>
                      <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                      labelStyle={{ color: '#fff' }}
                    />
                    <Area
                      type="monotone"
                      dataKey="profit"
                      stroke="#22c55e"
                      strokeWidth={2}
                      fill="url(#profitGradient)"
                      name="Profit"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>

            {/* Run Summaries */}
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">Run Summaries</h2>
                <button
                  onClick={() => fetchSummaries()}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 text-sm transition-colors"
                >
                  Refresh
                </button>
              </div>
              {summaries.length === 0 ? (
                <div className="bg-slate-800/50 rounded-xl p-12 text-center border border-slate-700/50">
                  <p className="text-slate-500">No summaries yet. Summaries are generated after each run.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {summaries.map((summary) => (
                    <div key={summary.id} className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center text-green-400 font-bold">
                            {summary.run_id}
                          </div>
                          <div>
                            <div className="text-white font-medium">Run {summary.run_id}</div>
                            <div className="text-slate-500 text-sm">{formatTime(summary.created_at)}</div>
                          </div>
                        </div>
                      </div>
                      <div className="prose prose-invert max-w-none">
                        <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{summary.summary_text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        ) : (
          /* Terminal Tab */
          <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-slate-700 flex items-center justify-center">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-green-400">
                    <rect x="2" y="3" width="20" height="14" rx="2"/>
                    <path d="M8 21h8M12 17v4"/>
                  </svg>
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-white">Terminal</h2>
                  <p className="text-slate-500 text-sm">Agent activity logs</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
                  isTerminalConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                }`}>
                  <span className={`w-2 h-2 rounded-full ${isTerminalConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></span>
                  {isTerminalConnected ? 'LIVE' : 'OFFLINE'}
                </div>
                <button
                  onClick={() => fetchLatestRunForTerminal()}
                  className="px-4 py-2 rounded-lg bg-green-500 text-white hover:bg-green-600 text-sm font-medium transition-colors"
                >
                  Load Latest
                </button>
              </div>
            </div>

            {/* Terminal Output */}
            <div className="bg-slate-950 rounded-lg p-4 font-mono text-sm overflow-y-auto max-h-[500px]">
              {terminalLogs.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-48 text-slate-500">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="mb-4 opacity-50">
                    <rect x="2" y="3" width="20" height="14" rx="2"/>
                    <path d="M8 21h8M12 17v4"/>
                  </svg>
                  <p>No simulation data loaded.</p>
                  <p className="text-sm mt-2">Click "Load Latest" to view agent activity.</p>
                </div>
              ) : (
                <pre className="text-green-400">
                  {terminalLogs.map((log, i) => {
                    const parts = log.match(/%c\[([^\]]+)\]%c (.*)/)
                    if (parts) {
                      const type = parts[1]
                      const content = parts[2]
                      const colorClass = {
                        '[SYSTEM]': 'text-slate-400',
                        '[AGENT]': 'text-green-300',
                        '[REASON]': 'text-yellow-400/70 italic',
                        '[METRICS]': 'text-blue-300'
                      }[type] || 'text-green-400'

                      return (
                        <div key={i} className="mb-1">
                          <span className="text-slate-600">[{type}]</span>{' '}
                          <span className={colorClass}>{content}</span>
                        </div>
                      )
                    }
                    return <div key={i} className="mb-1 opacity-50">{log}</div>
                  })}
                </pre>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
