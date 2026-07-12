import { useState, useEffect } from "react"
import { getStatus, getHealth, getMetrics } from "./api/client"
import { LineChart, Line, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, YAxis } from "recharts"

function App() {
  const [status, setStatus] = useState(null)
  const [health, setHealth] = useState(null)
  const [metrics, setMetrics] = useState(null)

  useEffect(() => {
    const fetchStatus = () => {
      getStatus("capital").then(data => setStatus(data))
    }
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const fetchHealth = () => {
      getHealth("capital").then(data => setHealth(data))
    }
    fetchHealth()
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const fetchMetrics = () => {
      getMetrics("capital", 1).then(data => setMetrics(data))
    }
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 300000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-6">Homelab Dashboard</h1>
      <div className="grid grid-cols-3 gap-4">
        <ServerCard data={status} health={health} />
        <CpuCard data={status} metrics={metrics} />
        <MemoryCard data={status} metrics={metrics} />
        <TempCard data={status} metrics={metrics} />
        <DiskCard data={status} />
      </div>
    </div>
  )
}

function ServerCard({ data, health }) {
  if (!data || !health) return <p>Loading...</p>
  return (
    <div className="bg-gray-800 rounded-xl p-4 h-48 flex flex-col">
      <h2 className="text-lg font-semibold mb-3">capital</h2>
      <div className="flex-1 flex flex-col justify-center gap-1">
        <p className="text-gray-400">Status <span className={`float-right ${health.status === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>{health.status}</span></p>
        <p className="text-gray-400">Uptime <span className="text-white float-right">{Math.floor(data.uptime / 3600)}h {Math.floor((data.uptime % 3600) / 60)}m</span></p>
        <p className="text-gray-400">Last Seen <span className="text-white float-right">{new Date(health.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></p>
        <p className="text-gray-400">Last Update <span className="text-white float-right">{Math.round(health.seconds_since_last_snapshot)}s ago</span></p>
      </div>
    </div>
  )
}

function CpuCard({ data, metrics }) {
  if (!data) return <p>Loading...</p>

  const chartData = metrics ? metrics.map(snapshot => ({
    time: snapshot.timestamp,
    value: snapshot.cpu
  })) : []

  return (
    <div className="bg-gray-800 rounded-xl p-4 h-48 flex flex-col">
      <h2 className="text-lg font-semibold mb-3">Processor</h2>
      <div className="flex gap-4 flex-1">
        <div className="flex-1 flex flex-col justify-center">
          <p className="text-gray-400">CPU Usage <span className="text-white float-right">{data.cpu}%</span></p>
          <p className="text-gray-400">Load Average <span className="text-white float-right">{data.loadaverage}</span></p>
        </div>
        <div className="flex-1 bg-gray-900 rounded-lg p-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <Line dataKey="value" stroke="#3b82f6" dot={false} />
              <Tooltip />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

function MemoryCard({ data, metrics }) {
  if (!data) return <p>Loading...</p>

  const chartData = metrics ? metrics.map(snapshot => ({
    time: snapshot.timestamp,
    value: snapshot.memory_used
  })) : []

  return (
    <div className="bg-gray-800 rounded-xl p-4 h-48 flex flex-col">
      <h2 className="text-lg font-semibold mb-3">Memory</h2>
      <div className="flex gap-4 flex-1">
        <div className="flex-1 flex flex-col justify-center">
          <p className="text-gray-400">Used <span className="text-white float-right">{data.memory_used} GB</span></p>
          <p className="text-gray-400">Total <span className="text-white float-right">{data.memory_total} GB</span></p>
          <p className="text-gray-400">Swap <span className="text-white float-right">{data.swap_used} GB</span></p>
        </div>
        <div className="flex-1 bg-gray-900 rounded-lg p-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <YAxis domain={[0, data.memory_total]} hide={true} />
              <Line dataKey="value" stroke="#f97316" dot={false} />
              <Tooltip />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

function TempCard({ data, metrics }) {
  if (!data) return <p>Loading...</p>

  const chartData = metrics ? metrics.map(snapshot => ({
    time: snapshot.timestamp,
    value: snapshot.cpu_package
  })) : []

  return (
    <div className="bg-gray-800 rounded-xl p-4 h-48 flex flex-col">
      <h2 className="text-lg font-semibold mb-3">Temperatures</h2>
      <div className="flex gap-4 flex-1">
        <div className="flex-1 flex flex-col justify-center">
          <p className="text-gray-400">CPU Package <span className="text-white float-right">{data.cpu_package}°C</span></p>
          <p className="text-gray-400">NVMe 0 <span className="text-white float-right">{data.nvme0}°C</span></p>
          <p className="text-gray-400">NVMe 1 <span className="text-white float-right">{data.nvme1}°C</span></p>
          <p className="text-gray-400">Network <span className="text-white float-right">{data.network}°C</span></p>
        </div>
        <div className="flex-1 bg-gray-900 rounded-lg p-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <Line dataKey="value" stroke="#f43f5e" dot={false} />
              <Tooltip />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

function DiskCard({ data }) {
  if (!data) return <p>Loading...</p>

  const used = data.rootfs_used
  const total = 1800
  const free = total - used

  const donutData = [
    { name: "Used", value: used },
    { name: "Free", value: free }
  ]

  return (
    <div className="bg-gray-800 rounded-xl p-4 h-48 flex flex-col">
      <h2 className="text-lg font-semibold mb-3">Storage</h2>
      <div className="flex gap-4 flex-1">
        <div className="flex-1 flex flex-col justify-center">
          <p className="text-gray-400">Used <span className="text-white float-right">{used} GB</span></p>
          <p className="text-gray-400">Free <span className="text-white float-right">{free.toFixed(0)} GB</span></p>
        </div>
        <div className="flex-1 bg-gray-900 rounded-lg p-2">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={donutData} innerRadius={35} outerRadius={55} dataKey="value" strokeWidth={0}>
                <Cell fill="#3b82f6" />
                <Cell fill="#1f2937" />
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default App