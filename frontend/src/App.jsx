import { useState, useEffect, useRef } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const getApiBase = () => {
  const url = import.meta.env.VITE_API_URL || ''
  return url.endsWith('/api') ? url : url + '/api'
}
const API_BASE = getApiBase()

// Windows 2000 Palette
const COLORS = ['#000080', '#008000', '#800000', '#808000', '#800080']

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
  const [allAgentsProfitData, setAllAgentsProfitData] = useState([])
  
  // Simulation params
  const [simConfig, setSimConfig] = useState({ num_agents: 5, turns_per_run: 10 })
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    fetchRuns()
    fetchTrends()
    fetchSummaries()
    fetchAgents()
    fetchAllAgentsProfits()

    const terminalInterval = setInterval(() => {
      if (activeTab === 'terminal') {
        fetchLatestRunForTerminal()
      }
    }, 5000)

    return () => clearInterval(terminalInterval)
  }, [activeTab])

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

  const startSimulation = async () => {
    setIsRunning(true)
    try {
      const res = await fetch(`${API_BASE}/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(simConfig)
      })
      if (res.ok) {
        await fetchRuns()
        await fetchTrends()
      }
    } catch (e) {
      console.error('Failed to start simulation:', e)
    } finally {
      setIsRunning(false)
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
    const timestamp = new Date(runDetail.start_time).toLocaleString()

    logs.push(`System Boot: ${timestamp}`)
    logs.push(`Loading kernel... OK`)
    logs.push(`Mounting volumes... OK`)
    logs.push(`Initializing Agent Environment...`)
    logs.push(`----------------------------------------`)
    logs.push(`Session ID: ${runDetail.id}`)

    const actions = runDetail.actions || []
    actions.forEach((action, i) => {
      const turnPrefix = `[Turn ${action.turn}]`
      logs.push(`${turnPrefix} ${action.agent_name}: ${action.action_type}`)
      if (action.reasoning) {
        logs.push(`  > ${action.reasoning.substring(0, 60)}...`)
      }
    })

    setTerminalLogs(logs)
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

  const formatTime = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleString('en-US', {
      month: 'numeric', day: 'numeric', year: '2-digit', hour: '2-digit', minute: '2-digit'
    })
  }

  return (
    <div className="min-h-screen p-4 flex flex-col font-sans text-[13px] bg-[#008080]">
      
      {/* Taskbar / Header */}
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
        
        {/* Left Column: Sidebar Controls */}
        <div className="w-64 flex flex-col gap-4">
          
          {/* Simulation Control Panel */}
          <div className="win-border-outset bg-[#c0c0c0] p-1">
            <div className="bg-[#000080] text-white px-2 py-0.5 font-bold text-sm mb-1">
              Control Panel
            </div>
            <div className="p-3">
              <div className="mb-3">
                <label className="block mb-1">Agents:</label>
                <select 
                  className="w-full win-border-inset p-1 bg-white"
                  value={simConfig.num_agents}
                  onChange={(e) => setSimConfig({...simConfig, num_agents: parseInt(e.target.value)})}
                >
                  <option value="3">3 Agents</option>
                  <option value="5">5 Agents</option>
                  <option value="8">8 Agents</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block mb-1">Turns:</label>
                <input 
                  type="number" 
                  className="w-full win-border-inset p-1 bg-white"
                  value={simConfig.turns_per_run}
                  onChange={(e) => setSimConfig({...simConfig, turns_per_run: parseInt(e.target.value)})}
                />
              </div>
              <button 
                onClick={startSimulation}
                disabled={isRunning}
                className="w-full win-button py-1 font-bold flex items-center justify-center gap-2"
              >
                {isRunning ? 'Running...' : 'Start Simulation'}
              </button>
            </div>
          </div>

          {/* System Status */}
          {trends && (
            <div className="win-border-outset bg-[#c0c0c0] p-1">
              <div className="bg-[#808080] text-white px-2 py-0.5 font-bold text-sm mb-1">
                <span>System Status</span>
              </div>
              <div className="p-2 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span>Status:</span>
                  <span className="font-bold text-[#008000]">Online</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Runs:</span>
                  <span>{trends.run_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg Profit:</span>
                  <span>{trends.avg_profit?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Gini Coeff:</span>
                  <span>{(trends.avg_gini * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Runs List */}
          <div className="win-border-outset bg-[#c0c0c0] p-1 flex-1 min-h-[300px] flex flex-col">
            <div className="bg-[#000080] text-white px-2 py-0.5 font-bold text-sm mb-1">
              <span>History</span>
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
                  <span>Run #{run.run_number}</span>
                  <span>{run.status === 'completed' ? 'Done' : '...'}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Main Content */}
        <div className="flex-1 flex flex-col gap-4">
          
          {/* Main Window */}
          <div className="win-border-outset bg-[#c0c0c0] p-1 flex-1 flex flex-col min-h-[600px]">
            <div className="bg-[#000080] text-white px-2 py-0.5 font-bold text-sm mb-1">
              Main Simulation View
            </div>

            {/* Menu Bar (inside window) */}
            <div className="flex gap-1 mb-2 px-1">
               {['dashboard', 'summaries', 'terminal'].map(tab => (
                 <button
                   key={tab}
                   onClick={() => setActiveTab(tab)}
                   className={`px-4 py-1 win-button capitalize ${activeTab === tab ? 'font-bold bg-white border-b-0 relative top-[1px] z-10' : ''}`}
                 >
                   {tab}
                 </button>
               ))}
            </div>

            {/* Content Area */}
            <div className="win-border-inset bg-[#dfdfdf] p-4 flex-1 overflow-y-auto">
              
              {activeTab === 'dashboard' && (
                <div className="h-full">
                  {!selectedRun ? (
                    <div className="h-full flex items-center justify-center text-gray-500">
                      <div className="text-center">
                        <img src="/computer.png" className="w-16 h-16 mx-auto mb-2 opacity-50 grayscale" alt="" />
                        <p>Select a run from the History panel to view details.</p>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Run Header */}
                      <div className="flex justify-between items-start">
                        <div>
                          <h2 className="text-lg font-bold">Run Analysis: #{selectedRun.run_number}</h2>
                          <p className="text-gray-600 text-xs">ID: {selectedRun.id}</p>
                        </div>
                        <div className="win-border-inset bg-white px-2 py-1 text-xs">
                          {formatTime(selectedRun.start_time)}
                        </div>
                      </div>

                      {/* Metrics Group */}
                      <fieldset className="border border-gray-400 p-2">
                        <legend className="px-1 text-xs text-blue-800">Performance Metrics</legend>
                        <div className="grid grid-cols-3 gap-4">
                           <div>
                              <div className="text-xs text-gray-600">Avg Profit</div>
                              <div className="font-bold text-lg">{selectedRun.metrics.avg_agent_profit?.toFixed(2)}</div>
                           </div>
                           <div>
                              <div className="text-xs text-gray-600">Gini Index</div>
                              <div className="font-bold text-lg">{selectedRun.metrics.gini_coefficient?.toFixed(4)}</div>
                           </div>
                           <div>
                              <div className="text-xs text-gray-600">Cooperation</div>
                              <div className="font-bold text-lg">{selectedRun.metrics.cooperation_rate?.toFixed(1)}%</div>
                           </div>
                        </div>
                      </fieldset>

                      {/* Agents Data Grid */}
                      <div className="win-border-inset bg-white p-0">
                        <table className="w-full text-left border-collapse text-xs">
                          <thead>
                            <tr className="bg-[#dfdfdf] border-b border-gray-400">
                              <th className="p-1 border-r border-gray-300">Agent Name</th>
                              <th className="p-1 border-r border-gray-300">Strategy</th>
                              <th className="p-1 border-r border-gray-300">Token A</th>
                              <th className="p-1 border-r border-gray-300">Token B</th>
                              <th className="p-1">Profit</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedRun.agent_states?.map((agent, i) => (
                              <tr key={i} className="hover:bg-blue-100">
                                <td className="p-1 border-r border-gray-200 border-b">{agent.agent_name}</td>
                                <td className="p-1 border-r border-gray-200 border-b">{agent.strategy}</td>
                                <td className="p-1 border-r border-gray-200 border-b text-right font-mono">{agent.token_a_balance?.toFixed(1)}</td>
                                <td className="p-1 border-r border-gray-200 border-b text-right font-mono">{agent.token_b_balance?.toFixed(1)}</td>
                                <td className={`p-1 border-b text-right font-bold ${agent.profit >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                                  {agent.profit?.toFixed(2)}
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
                <div className="h-full flex flex-col gap-4">
                  <div className="win-border-outset bg-white p-4 h-[300px]">
                    <h3 className="font-bold mb-2 text-xs">Global Profit Trends</h3>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={allAgentsProfitData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                        <XAxis dataKey="run" tick={{fontSize: 10}} />
                        <YAxis tick={{fontSize: 10}} />
                        <Tooltip contentStyle={{fontSize: 12, border: '1px solid gray'}} />
                        <Legend wrapperStyle={{fontSize: 10}} />
                        {agents.map((agent, i) => (
                          <Line
                            key={agent}
                            type="monotone"
                            dataKey={agent}
                            stroke={COLORS[i % COLORS.length]}
                            strokeWidth={1}
                            dot={{r: 2}}
                            name={agent.split('_')[1] || agent}
                          />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  
                  <div className="space-y-4">
                    {summaries.map(summary => {
                      // Handle raw JSON content (Python dict with single quotes)
                      let text = summary.summary_text || ''
                      try {
                        // Try direct JSON parse first (valid JSON)
                        const parsed = JSON.parse(text)
                        text = parsed.raw_content || parsed.content || parsed.text || text
                      } catch {
                        // Try Python dict syntax: {'key': 'value'}
                        try {
                          const pythonMatch = text.match(/^\s*\{\s*['"]raw_content['"]:\s*['"](.+?)['"]/s)
                          if (pythonMatch) {
                            text = pythonMatch[1]
                          } else {
                            // Remove wrapping {} if present
                            text = text.replace(/^\s*\{.*?raw_content.*?:\s*/s, '').replace(/\}\s*$/s, '')
                          }
                        } catch {}
                      }
                      return (
                        <fieldset key={summary.id} className="border border-gray-400 p-2 bg-white">
                          <legend className="px-1 font-bold">Run {summary.run_id} Report</legend>
                          <p className="text-xs font-mono whitespace-pre-wrap">{text}</p>
                        </fieldset>
                      )
                    })}
                  </div>
                </div>
              )}

              {activeTab === 'terminal' && (
                <div className="h-full flex flex-col">
                  <div className="bg-black text-gray-300 font-mono text-xs p-2 flex-1 overflow-y-auto win-border-inset">
                    {terminalLogs.length === 0 ? (
                      <div>C:\&gt; Waiting for simulation data...</div>
                    ) : (
                      terminalLogs.map((log, i) => (
                        <div key={i}>{log}</div>
                      ))
                    )}
                    {isTerminalConnected && <div className="animate-pulse">_</div>}
                  </div>
                </div>
              )}

            </div>
            
            {/* Status Bar */}
            <div className="mt-1 win-border-inset bg-[#dfdfdf] px-2 py-0.5 text-xs flex justify-between text-gray-600">
               <span>{activeTab.toUpperCase()} VIEW</span>
               <span>MEM: 64MB OK</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
