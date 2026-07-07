function App() {
  return (
    <div>
      <h1>Homelab Dashboard</h1>
    </div>
  )
}



import { useState, useEffect } from "react"

function CpuDisplay() {
  // useState creates a variable that React watches
  // when it changes, React re-renders the component
  const [cpu, setCpu] = useState(null)
  //     ^         ^         ^
  //   value   updater   initial value

  // useEffect runs code when the component loads
  useEffect(() => {
    fetch("http://your-api/nodes/capital/status")
      .then(response => response.json())
      .then(data => setCpu(data.cpu))
  }, []) // the empty [] means "only run once on load"

  return (
    <div>
      <p>CPU: {cpu}%</p>
    </div>
  )
}


export default App