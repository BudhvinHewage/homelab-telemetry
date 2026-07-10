import { useState, useEffect } from "react"

function CpuDisplay() {
  const [data, setData] = useState(null)

  useEffect(() => {
    const fetchData = () => {
      fetch("http://192.168.0.76:8001/nodes/capital/status")
        .then(response => response.json())
        .then(json => setData(json))
    }

    fetchData()

    const interval = setInterval(fetchData, 5000)

    return () => clearInterval(interval)
  }, []) 

  if (data == null) {return <p>Loading...</p>}

  return (
    <div>
      <p>CPU Usage: {data.cpu}%</p>
    </div>
  )
}

function App() {
  return (
    <div>
      <h1>Homelab Dashboard</h1>
      <CpuDisplay />
    </div>
  )
}

export default App