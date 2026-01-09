import { useState, useEffect, useRef } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const getApiBase = () => {
  const url = import.meta.env.VITE_API_URL || ''
  return url.endsWith('/api') ? url : url + '/api'
}
const API_BASE = getApiBase()

const COLORS = ['#000080', '#008000', '#800000', '#808000', '#800080']

function App() {
  const [loading, setLoading] = useState(true)
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [trends, setTrends] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [summaries, setSummaries] = useState([])
  const [agents, setAgents] = useState([])
  const [allAgentsProfitData, setAllAgentsProfitData] = useState([])
  const [runDetails, setRunDetails] = useState({})
  const summariesRef = useRef(null)

  useEffect(() => {
    loadAllData()
  }, [])

  const loadAllData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        fetchRuns(),
        fetchTrends(),
        fetchSummaries(),
        fetchAllAgentsProfits()
      ])
    } finally {
      setLoading(false)
    }
  }

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

  const fetchAllAgentsProfits = async () => {
    try {
      const res = await fetch(`${API_BASE}/agents/all-profits`)
      if (res.ok) {
        const data = await res.json()
        setAllAgentsProfitData(data.data || [])
        setAgents(data.agents || [])
      }
    } catch (e) {
      console.error('Failed to fetch all agents profits:', e)
    }
  }

  const selectRun = async (runId) => {
    if (runDetails[runId]) {
      setSelectedRun(runDetails[runId])
      return
    }
    try {
      const res = await fetch(`${API_BASE}/runs/${runId}`)
      if (res.ok) {
        const data = await res.json()
        setRunDetails(prev => ({ ...prev, [runId]: data }))
        setSelectedRun(data)
      }
    } catch (e) {
      console.error('Failed to fetch run details:', e)
    }
  }

  const formatTime = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleString('en-US', {
      month: 'numeric', day: 'numeric', year: '2-digit', hour: '2-digit', minute: '2-digit'
    })
  }

  const getFilteredSummaries = () => {
    if (!selectedRun) return summaries
    return summaries.filter(s => s.run_id === selectedRun.run_number)
  }

  if (loading) {
    return (
      <div className="min-h-screen p-4 flex flex-col font-sans text-[13px] bg-[#008080]">
        <div className="win-border-outset bg-[#c0c0c0] p-1 flex justify-between items-center mb-4">
          <div className="flex items-center gap-2 px-2">
            <div className="w-4 h-4 bg-gradient-to-br from-blue-400 to-blue-600 border border-black"></div>
            <h1 className="font-bold">DeFi Agent Arena v1.0</h1>
          </div>
          <div className="win-border-inset bg-white px-2 py-0.5 text-xs font-mono">
            {new Date().toLocaleTimeString()}
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="win-border-outset bg-[#c0c0c0] p-8 text-center">
            <div className="inline-block w-6 h-6 border-2 border-black border-t-transparent animate-spin mb-4"></div>
            <p className="font-bold">Loading...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-4 flex flex-col font-sans text-[13px] bg-[#008080]">

      {/* Header */}
      <div className="win-border-outset bg-[#c0c0c0] p-1 flex justify-between items-center mb-4">
        <div className="flex items-center gap-2 px-2">
          <div className="w-4 h-4 bg-gradient-to-br from-blue-400 to-blue-600 border border-black"></div>
          <h1 className="font-bold">DeFi Agent Arena v1.0</h1>
        </div>
        <div className="win-border-inset bg-white px-2 py-0.5 text-xs font-mono">
          {new Date().toLocaleTimeString()}
        </div>
      </div>

      <div className="flex gap-4 flex-1 items-start">
        {/* Left Column: History */}
        <div className="w-48 flex flex-col gap-4">
          <div className="win-border-outset bg-[#c0c0c0] p-1 flex-1 min-h-[500px] flex flex-col">
            <div className="bg-[#000080] text-white px-2 py-0.5 font-bold text-sm mb-1">
              History
            </div>
            <div className="win-border-inset bg-white flex-1 overflow-y-auto p-1 h-full">
              {runs.map(run => (
                <div
                  key={run.id}
                  onClick={() => selectRun(run.id)}
                  className={`cursor-pointer px-1 py-0.5 flex justify-between items-center text-xs hover:bg-[#000080] hover:text-white ${
                    selectedRun?.id === run.id ? 'bg-[#000080] text-white border border-dotted border-white' : ''
                  }`}
                >
                  <span>#{run.run_number}</span>
                  <span>{run.status === 'completed' ? 'Done' : '...'}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Main Content */}
        <div className="flex-1 flex flex-col gap-4">
          <div className="win-border-outset bg-[#c0c0c0] p-1 flex-1 flex flex-col min-h-[600px]">
            <div className="bg-[#000080] text-white px-2 py-0.5 font-bold text-sm mb-1">
              Main Simulation View
            </div>

            {/* Tabs */}
            <div className="flex gap-1 mb-2 px-1">
               {['dashboard', 'summaries'].map(tab => (
                 <button
                   key={tab}
                   onClick={() => {
                     setActiveTab(tab)
                     // Restore scroll position for summaries
                     if (tab === 'summaries' && summariesRef.current) {
                       setTimeout(() => {
                         summariesRef.current.scrollTop = summariesRef.current.scrollTop
                       }, 100)
                     }
                   }}
                   className={`px-4 py-1 win-button capitalize ${activeTab === tab ? 'font-bold bg-white border-b-0 relative top-[1px] z-10' : ''}`}
                 >
                   {tab}
                 </button>
               ))}
            </div>

            {/* Content Area */}
            <div className="win-border-inset bg-[#dfdfdf] p-4 flex-1 overflow-y-auto">
              {activeTab === 'dashboard' && (
                <div className="space-y-4">
                  {/* Stats Bar */}
                  <div className="grid grid-cols-4 gap-2">
                    <div className="win-border-inset bg-white p-2 text-center">
                      <div className="text-xs text-gray-600">Total Runs</div>
                      <div className="font-bold text-lg">{trends?.run_count || 0}</div>
                    </div>
                    <div className="win-border-inset bg-white p-2 text-center">
                      <div className="text-xs text-gray-600">Avg Profit</div>
                      <div className={`font-bold text-lg ${(trends?.avg_profit || 0) >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                        {(trends?.avg_profit || 0) >= 0 ? '+' : ''}{trends?.avg_profit?.toFixed(2) || '0.00'}
                      </div>
                    </div>
                    <div className="win-border-inset bg-white p-2 text-center">
                      <div className="text-xs text-gray-600">Gini</div>
                      <div className="font-bold text-lg">{((trends?.avg_gini || 0) * 100).toFixed(1)}%</div>
                    </div>
                    <div className="win-border-inset bg-white p-2 text-center">
                      <div className="text-xs text-gray-600">Cooperation</div>
                      <div className="font-bold text-lg">{trends?.cooperation_rate?.toFixed(1) || '0.0'}%</div>
                    </div>
                  </div>

                  {/* Agent Chart - ALL AGENTS TOGETHER */}
                  <div className="win-border-outset bg-white p-4 h-[280px]">
                    <h3 className="font-bold mb-2 text-xs">All Agents Performance</h3>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={allAgentsProfitData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                        <XAxis dataKey="run" tick={{fontSize: 10}} label={{ value: 'Run', position: 'insideBottom', offset: -5 }} />
                        <YAxis tick={{fontSize: 10}} label={{ value: 'Profit', angle: -90, position: 'insideLeft' }} />
                        <Tooltip contentStyle={{fontSize: 12, border: '1px solid gray'}} />
                        <Legend wrapperStyle={{fontSize: 10}} />
                        {agents.map((agent, i) => (
                          <Line
                            key={agent}
                            type="monotone"
                            dataKey={agent}
                            stroke={COLORS[i % COLORS.length]}
                            strokeWidth={2}
                            dot={{r: 3}}
                            name={agent.split('_')[1] || agent}
                          />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Run Details or Empty State */}
                  {!selectedRun ? (
                    <div className="win-border-inset bg-white p-8 text-center text-gray-500">
                      <p>Select a run from History to view details</p>
                    </div>
                  ) : (
                    <div className="win-border-outset bg-[#c0c0c0] p-1">
                      <div className="bg-[#808080] text-white px-2 py-0.5 font-bold text-xs mb-1">
                        Run #{selectedRun.run_number} Details
                      </div>
                      <div className="win-border-inset bg-white p-0">
                        <table className="w-full text-left border-collapse text-xs">
                          <thead>
                            <tr className="bg-[#dfdfdf] border-b border-gray-400">
                              <th className="p-1 border-r border-gray-300">Agent</th>
                              <th className="p-1 border-r border-gray-300">Strategy</th>
                              <th className="p-1 border-r border-gray-300 text-right">Token A</th>
                              <th className="p-1 border-r border-gray-300 text-right">Token B</th>
                              <th className="p-1 text-right">Profit</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedRun.agent_states?.map((agent, i) => (
                              <tr key={i} className="hover:bg-blue-100">
                                <td className="p-1 border-r border-gray-200 border-b font-bold">{agent.agent_name}</td>
                                <td className="p-1 border-r border-gray-200 border-b">{agent.strategy}</td>
                                <td className="p-1 border-r border-gray-200 border-b text-right font-mono">{agent.token_a_balance?.toFixed(1)}</td>
                                <td className="p-1 border-r border-gray-200 border-b text-right font-mono">{agent.token_b_balance?.toFixed(1)}</td>
                                <td className={`p-1 border-b text-right font-bold ${agent.profit >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                                  {agent.profit >= 0 ? '+' : ''}{agent.profit?.toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'summaries' && (
                <div ref={summariesRef} className="h-full flex flex-col gap-4">
                  <div className="win-border-outset bg-[#c0c0c0] p-1 flex-shrink-0">
                    <div className="bg-[#808080] text-white px-2 py-0.5 font-bold text-xs mb-1">
                      Filtered by Selected Run
                    </div>
                    <p className="text-xs text-gray-600 px-2 pb-2">
                      Showing {getFilteredSummaries().length} summary(s) for Run #{selectedRun?.run_number || 'None'}
                    </p>
                  </div>

                  <div className="space-y-4 flex-1 overflow-y-auto">
                    {getFilteredSummaries().length === 0 ? (
                      <div className="win-border-inset bg-white p-8 text-center text-gray-500">
                        <p>Select a run from History to view its summary</p>
                      </div>
                    ) : (
                      getFilteredSummaries().map(summary => {
                        let text = summary.summary_text || ''
                        try {
                          const parsed = JSON.parse(text)
                          text = parsed.raw_content || parsed.content || parsed.text || text
                        } catch {
                          const match = text.match(/^\s*\{.*?raw_content.*?:\s*(.+)/s)
                          if (match) text = match[1].replace(/\}\s*$/s, '')
                        }
                        return (
                          <fieldset key={summary.id} className="border border-gray-400 p-2 bg-white">
                            <legend className="px-1 font-bold">Run {summary.run_id} Report</legend>
                            <p className="text-xs font-mono whitespace-pre-wrap">{text}</p>
                          </fieldset>
                        )
                      })
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Status Bar */}
            <div className="mt-1 win-border-inset bg-[#dfdfdf] px-2 py-0.5 text-xs flex justify-between text-gray-600">
               <span>{activeTab.toUpperCase()} VIEW</span>
               <span>{runs.length} runs | {agents.length} agents</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
