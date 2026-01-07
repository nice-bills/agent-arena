import { useState, useEffect } from 'react'
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
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved ? JSON.parse(saved) : false
  })

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode))
  }, [darkMode])

  useEffect(() => {
    fetchRuns()
    fetchTrends()
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

  const selectRun = async (runId) => {
    try {
      const res = await fetch(`${API_BASE}/runs/${runId}`)
      if (res.ok) {
        const data = await res.json()
        setSelectedRun(data)
      }
    } catch (e) {
      console.error('Failed to fetch run details:', e)
    }
  }

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-slate-900' : 'bg-slate-50'}`}>
      {/* Header */}
      <header className={`${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'} border-b px-6 py-4`}>
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-slate-800'}`}>DeFi Agent Arena</h1>
          <div className="flex gap-4 items-center">
            <span className={`text-sm ${trends ? 'text-green-500' : 'text-red-500'}`}>
              {trends ? 'Connected' : 'Disconnected'}
            </span>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`px-3 py-1.5 rounded text-sm ${
                darkMode
                  ? 'bg-slate-700 text-white hover:bg-slate-600'
                  : 'bg-slate-200 text-slate-800 hover:bg-slate-300'
              }`}
            >
              {darkMode ? 'Light' : 'Dark'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Refresh Section */}
        <section className={`${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'} rounded-lg border p-6 mb-8`}>
          <div className="flex justify-between items-center">
            <h2 className={`text-lg font-medium ${darkMode ? 'text-white' : 'text-slate-800'}`}>Simulation Data</h2>
            <button
              onClick={() => {
                fetchRuns()
                fetchTrends()
              }}
              className={`px-6 py-2 rounded ${
                darkMode
                  ? 'bg-slate-700 text-white hover:bg-slate-600'
                  : 'bg-slate-800 text-white hover:bg-slate-700'
              }`}
            >
              Refresh
            </button>
          </div>
        </section>

        {/* Trends Section */}
        {trends && (
          <section className={`${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'} rounded-lg border p-6 mb-8`}>
            <h2 className={`text-lg font-medium ${darkMode ? 'text-white' : 'text-slate-800'} mb-4`}>Trends</h2>
            <div className="grid grid-cols-4 gap-4">
              <div className={`${darkMode ? 'bg-slate-700' : 'bg-slate-50'} rounded p-4`}>
                <div className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Total Runs</div>
                <div className={`text-2xl font-semibold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{trends.run_count}</div>
              </div>
              <div className={`${darkMode ? 'bg-slate-700' : 'bg-slate-50'} rounded p-4`}>
                <div className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Avg Profit</div>
                <div className={`text-2xl font-semibold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{trends.avg_profit?.toFixed(2) || 0}</div>
              </div>
              <div className={`${darkMode ? 'bg-slate-700' : 'bg-slate-50'} rounded p-4`}>
                <div className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Avg Inequality</div>
                <div className={`text-2xl font-semibold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{(trends.avg_gini * 100).toFixed(1)}%</div>
              </div>
              <div className={`${darkMode ? 'bg-slate-700' : 'bg-slate-50'} rounded p-4`}>
                <div className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Profit Trend</div>
                <div className={`text-2xl font-semibold ${darkMode ? 'text-white' : 'text-slate-800'} capitalize`}>{trends.profit_trend}</div>
              </div>
            </div>
          </section>
        )}

        {/* Runs List */}
        <section className={`${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'} rounded-lg border p-6 mb-8`}>
          <h2 className={`text-lg font-medium ${darkMode ? 'text-white' : 'text-slate-800'} mb-4`}>Runs</h2>
          {runs.length === 0 ? (
            <p className={darkMode ? 'text-slate-400' : 'text-slate-500'}>No runs yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className={`border-b ${darkMode ? 'border-slate-700' : 'border-slate-200'} text-left`}>
                    <th className={`py-2 px-3 text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Run</th>
                    <th className={`py-2 px-3 text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Status</th>
                    <th className={`py-2 px-3 text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Started</th>
                    <th className={`py-2 px-3 text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run) => (
                    <tr key={run.id} className={`border-b ${darkMode ? 'border-slate-700' : 'border-slate-100'}`}>
                      <td className={`py-2 px-3 ${darkMode ? 'text-white' : 'text-slate-800'}`}>#{run.run_number}</td>
                      <td className="py-2 px-3">
                        <span className={`px-2 py-1 rounded text-xs ${
                          run.status === 'completed'
                            ? darkMode ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800'
                            : darkMode ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {run.status}
                        </span>
                      </td>
                      <td className={`py-2 px-3 text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>
                        {new Date(run.start_time).toLocaleString()}
                      </td>
                      <td className="py-2 px-3">
                        <button
                          onClick={() => selectRun(run.id)}
                          className={`text-sm ${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800'}`}
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
          <section className={`${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'} rounded-lg border p-6`}>
            <div className="flex justify-between items-center mb-4">
              <h2 className={`text-lg font-medium ${darkMode ? 'text-white' : 'text-slate-800'}`}>Run Details</h2>
              <button onClick={() => setSelectedRun(null)} className={`${darkMode ? 'text-slate-400 hover:text-white' : 'text-slate-500 hover:text-slate-700'}`}>
                Close
              </button>
            </div>

            {/* Metrics */}
            {selectedRun.metrics && (
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className={`${darkMode ? 'bg-slate-700' : 'bg-slate-50'} rounded p-4`}>
                  <div className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Gini Coefficient</div>
                  <div className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{selectedRun.metrics.gini_coefficient?.toFixed(4)}</div>
                </div>
                <div className={`${darkMode ? 'bg-slate-700' : 'bg-slate-50'} rounded p-4`}>
                  <div className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Avg Profit</div>
                  <div className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{selectedRun.metrics.avg_agent_profit?.toFixed(2)}</div>
                </div>
                <div className={`${darkMode ? 'bg-slate-700' : 'bg-slate-50'} rounded p-4`}>
                  <div className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Cooperation Rate</div>
                  <div className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{selectedRun.metrics.cooperation_rate?.toFixed(2)}</div>
                </div>
              </div>
            )}

            {/* Agents */}
            <h3 className={`font-medium ${darkMode ? 'text-white' : 'text-slate-800'} mb-3`}>Agents</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className={`border-b ${darkMode ? 'border-slate-700' : 'border-slate-200'} text-left`}>
                    <th className={`py-2 px-3 text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Agent</th>
                    <th className={`py-2 px-3 text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Token A</th>
                    <th className={`py-2 px-3 text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Token B</th>
                    <th className={`py-2 px-3 text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Profit</th>
                    <th className={`py-2 px-3 text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>Strategy</th>
                  </tr>
                </thead>
                <tbody>
                  {(selectedRun.agents || []).map((agent, i) => (
                    <tr key={i} className={`border-b ${darkMode ? 'border-slate-700' : 'border-slate-100'}`}>
                      <td className={`py-2 px-3 ${darkMode ? 'text-white' : 'text-slate-800'}`}>{agent.name}</td>
                      <td className={`py-2 px-3 ${darkMode ? 'text-slate-300' : 'text-slate-600'}`}>{agent.token_a?.toFixed(2)}</td>
                      <td className={`py-2 px-3 ${darkMode ? 'text-slate-300' : 'text-slate-600'}`}>{agent.token_b?.toFixed(2)}</td>
                      <td className={`py-2 px-3 ${agent.profit >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {agent.profit?.toFixed(2)}
                      </td>
                      <td className={`py-2 px-3 ${darkMode ? 'text-slate-300' : 'text-slate-600'}`}>{agent.strategy}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Actions */}
            {(selectedRun.actions || []).length > 0 && (
              <>
                <h3 className={`font-medium ${darkMode ? 'text-white' : 'text-slate-800'} mt-6 mb-3`}>Actions Log</h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {selectedRun.actions.slice(0, 20).map((action, i) => (
                    <div key={i} className={`${darkMode ? 'bg-slate-700' : 'bg-slate-50'} rounded p-3 text-sm`}>
                      <div className="flex gap-2 mb-1">
                        <span className={`font-medium ${darkMode ? 'text-white' : 'text-slate-800'}`}>{action.agent_name}</span>
                        <span className={darkMode ? 'text-slate-400' : 'text-slate-500'}>Turn {action.turn}</span>
                      </div>
                      <div className={darkMode ? 'text-slate-300' : 'text-slate-600'}>
                        <span className="font-medium">{action.action_type}</span>
                        {action.reasoning && (
                          <p className={`${darkMode ? 'text-slate-400' : 'text-slate-500'} mt-1 text-xs`}>{action.reasoning.substring(0, 150)}...</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>
        )}
      </main>
    </div>
  )
}

export default App
