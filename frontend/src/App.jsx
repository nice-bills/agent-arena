import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const getApiBase = () => {
  const url = import.meta.env.VITE_API_URL || ''
  return url.endsWith('/api') ? url : url + '/api'
}
const API_BASE = getApiBase()

function App() {
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [trends, setTrends] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [terminalLogs, setTerminalLogs] = useState([])
  const [isTerminalConnected, setIsTerminalConnected] = useState(false)

  useEffect(() => {
    fetchRuns()
    fetchTrends()
    fetchLatestRunForTerminal()
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
    const timestamp = new Date(runDetail.start_time).toISOString().split('T')[0]

    logs.push(`%c[SYSTEM]%c DeFi Agent Arena v1.0`)
    logs.push(`%c[SYSTEM]%c Session started: ${timestamp}`)
    logs.push(`%c[SYSTEM]%c Initializing ${runDetail.agents?.length || 0} agents...`)
    logs.push(`%c[SYSTEM]%c Pool reserves: A=1000, B=1000`)
    logs.push(`%c[SYSTEM]%c --- BEGIN SIMULATION ---`)

    const actions = runDetail.actions || []
    actions.forEach((action, i) => {
      const actionEmoji = {
        'swap': '<->',
        'provide_liquidity': '~',
        'propose_alliance': '=',
        'do_nothing': 'z'
      }[action.action_type] || '.'

      logs.push(`%c[AGENT]%c ${action.agent_name} > Turn ${action.turn}: ${actionEmoji} ${action.action_type}`)
      if (action.reasoning) {
        const shortReason = action.reasoning.substring(0, 100).replace(/\n/g, ' ')
        logs.push(`%c[REASON]%c "${shortReason}..."`)
      }
    })

    logs.push(`%c[SYSTEM]%c --- SIMULATION COMPLETE ---`)
    logs.push(`%c[METRICS]%c Gini: ${runDetail.metrics?.gini_coefficient?.toFixed(4) || 0}`)
    logs.push(`%c[METRICS]%c Avg Profit: ${runDetail.metrics?.avg_agent_profit?.toFixed(2) || 0}`)

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

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-slate-700 border-b px-6 py-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <svg width="36" height="36" viewBox="0 0 100 100" className="opacity-90">
              <circle cx="50" cy="50" r="45" fill="currentColor" className="text-slate-700"/>
              <circle cx="35" cy="45" r="12" className="text-green-500"/>
              <circle cx="65" cy="45" r="12" className="text-green-500"/>
              <circle cx="50" cy="70" r="12" className="text-green-500"/>
              <line x1="35" y1="45" x2="65" y2="45" stroke="currentColor" strokeWidth="4" className="text-slate-800"/>
              <line x1="35" y1="45" x2="50" y2="70" stroke="currentColor" strokeWidth="4" className="text-slate-800"/>
              <line x1="65" y1="45" x2="50" y2="70" stroke="currentColor" strokeWidth="4" className="text-slate-800"/>
            </svg>
            <h1 className="text-xl font-semibold text-white">DeFi Agent Arena</h1>
          </div>
          <span className={`text-sm ${trends ? 'text-green-500' : 'text-red-500'}`}>
            {trends ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-6xl mx-auto px-6 pt-6 flex gap-4 border-b border-slate-700">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`pb-3 px-4 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'dashboard'
              ? 'border-green-500 text-white'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          Dashboard
        </button>
        <button
          onClick={() => setActiveTab('terminal')}
          className={`pb-3 px-4 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'terminal'
              ? 'border-green-500 text-white'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          Terminal
        </button>
      </div>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {activeTab === 'dashboard' ? (
          <>
            {/* Refresh Section */}
            <section className="bg-slate-800 border-slate-700 rounded-lg border p-6 mb-8">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-white">Simulation Data</h2>
                <button
                  onClick={() => {
                    fetchRuns()
                    fetchTrends()
                  }}
                  className="px-6 py-2 rounded bg-slate-700 text-white hover:bg-slate-600"
                >
                  Refresh
                </button>
              </div>
            </section>

            {/* Trends Section */}
            {trends && (
              <section className="bg-slate-800 border-slate-700 rounded-lg border p-6 mb-8">
                <h2 className="text-lg font-medium text-white mb-4">Trends</h2>
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-slate-700 rounded p-4">
                    <div className="text-sm text-slate-400">Total Runs</div>
                    <div className="text-2xl font-semibold text-white">{trends.run_count}</div>
                  </div>
                  <div className="bg-slate-700 rounded p-4">
                    <div className="text-sm text-slate-400">Avg Profit</div>
                    <div className="text-2xl font-semibold text-white">{trends.avg_profit?.toFixed(2) || 0}</div>
                  </div>
                  <div className="bg-slate-700 rounded p-4">
                    <div className="text-sm text-slate-400">Avg Inequality</div>
                    <div className="text-2xl font-semibold text-white">{(trends.avg_gini * 100).toFixed(1)}%</div>
                  </div>
                  <div className="bg-slate-700 rounded p-4">
                    <div className="text-sm text-slate-400">Profit Trend</div>
                    <div className="text-2xl font-semibold text-white capitalize">{trends.profit_trend}</div>
                  </div>
                </div>
              </section>
            )}

            {/* Runs List */}
            <section className="bg-slate-800 border-slate-700 rounded-lg border p-6 mb-8">
              <h2 className="text-lg font-medium text-white mb-4">Runs</h2>
              {runs.length === 0 ? (
                <p className="text-slate-400">No runs yet.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-700 text-left">
                        <th className="py-2 px-3 text-sm font-medium text-slate-400">Run</th>
                        <th className="py-2 px-3 text-sm font-medium text-slate-400">Status</th>
                        <th className="py-2 px-3 text-sm font-medium text-slate-400">Started</th>
                        <th className="py-2 px-3 text-sm font-medium text-slate-400">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {runs.map((run) => (
                        <tr key={run.id} className="border-b border-slate-700">
                          <td className="py-2 px-3 text-white">#{run.run_number}</td>
                          <td className="py-2 px-3">
                            <span className={`px-2 py-1 rounded text-xs ${
                              run.status === 'completed'
                                ? 'bg-green-900 text-green-300'
                                : 'bg-yellow-900 text-yellow-300'
                            }`}>
                              {run.status}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-sm text-slate-400">
                            {new Date(run.start_time).toLocaleString()}
                          </td>
                          <td className="py-2 px-3">
                            <button
                              onClick={() => selectRun(run.id)}
                              className="text-sm text-blue-400 hover:text-blue-300"
                            >
                              View
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            {/* Run Detail */}
            {selectedRun && (
              <section className="bg-slate-800 border-slate-700 rounded-lg border p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-medium text-white">Run Details</h2>
                  <button onClick={() => setSelectedRun(null)} className="text-slate-400 hover:text-white">
                    Close
                  </button>
                </div>

                {selectedRun.metrics && (
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-slate-700 rounded p-4">
                      <div className="text-sm text-slate-400">Gini Coefficient</div>
                      <div className="text-xl font-semibold text-white">{selectedRun.metrics.gini_coefficient?.toFixed(4)}</div>
                    </div>
                    <div className="bg-slate-700 rounded p-4">
                      <div className="text-sm text-slate-400">Avg Profit</div>
                      <div className="text-xl font-semibold text-white">{selectedRun.metrics.avg_agent_profit?.toFixed(2)}</div>
                    </div>
                    <div className="bg-slate-700 rounded p-4">
                      <div className="text-sm text-slate-400">Cooperation Rate</div>
                      <div className="text-xl font-semibold text-white">{selectedRun.metrics.cooperation_rate?.toFixed(2)}</div>
                    </div>
                  </div>
                )}

                <h3 className="font-medium text-white mb-3">Agents</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-700 text-left">
                        <th className="py-2 px-3 text-sm font-medium text-slate-400">Agent</th>
                        <th className="py-2 px-3 text-sm font-medium text-slate-400">Token A</th>
                        <th className="py-2 px-3 text-sm font-medium text-slate-400">Token B</th>
                        <th className="py-2 px-3 text-sm font-medium text-slate-400">Profit</th>
                        <th className="py-2 px-3 text-sm font-medium text-slate-400">Strategy</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(selectedRun.agents || []).map((agent, i) => (
                        <tr key={i} className="border-b border-slate-700">
                          <td className="py-2 px-3 text-white">{agent.name}</td>
                          <td className="py-2 px-3 text-slate-300">{agent.token_a?.toFixed(2)}</td>
                          <td className="py-2 px-3 text-slate-300">{agent.token_b?.toFixed(2)}</td>
                          <td className={`py-2 px-3 ${agent.profit >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                            {agent.profit?.toFixed(2)}
                          </td>
                          <td className="py-2 px-3 text-slate-300">{agent.strategy}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </>
        ) : (
          /* Terminal Tab - Retro Style */
          <div className="bg-slate-800 border-slate-700 rounded-lg border p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-medium text-white">Agent Terminal</h2>
              <div className="flex gap-4 items-center">
                <span className={`flex items-center gap-2 text-sm ${isTerminalConnected ? 'text-green-500' : 'text-red-500'}`}>
                  <span className={`w-2 h-2 rounded-full ${isTerminalConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
                  {isTerminalConnected ? 'LIVE' : 'OFFLINE'}
                </span>
                <button
                  onClick={() => fetchLatestRunForTerminal()}
                  className="px-4 py-1.5 rounded text-sm bg-slate-700 text-white hover:bg-slate-600"
                >
                  Load Latest
                </button>
              </div>
            </div>

            {/* Retro Terminal */}
            <div className="font-mono text-sm p-4 rounded-lg overflow-y-auto max-h-[600px] bg-slate-950">
              <pre className="text-green-400">
                {terminalLogs.length === 0 ? (
                  <span className="opacity-50">No simulation data loaded. Click "Load Latest" to view agent activity.</span>
                ) : (
                  terminalLogs.map((log, i) => {
                    const parts = log.match(/%c\[([^\]]+)\]%c (.*)/)
                    if (parts) {
                      return (
                        <div key={i} className="mb-1">
                          <span className="text-slate-500">[{parts[1]}]</span>{' '}
                          <span className={parts[1] === '[SYSTEM]' || parts[1] === '[METRICS]' ? 'text-green-400' : parts[1] === '[REASON]' ? 'text-yellow-400 opacity-80' : 'text-white'}>
                            {parts[2]}
                          </span>
                        </div>
                      )
                    }
                    return <div key={i} className="mb-1 opacity-50">{log}</div>
                  })
                )}
              </pre>
            </div>

            <div className="mt-4 text-xs text-slate-500">
              Tip: Select a run from the Dashboard to view its terminal logs
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
