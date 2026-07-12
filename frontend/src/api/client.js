const BASE_URL = import.meta.env.VITE_API_BASE_URL

export const getStatus = (node) => 
    fetch(`${BASE_URL}/nodes/${node}/status`).then(res => res.json())

export const getMetrics = (node, hours) =>
    fetch(`${BASE_URL}/nodes/${node}/metrics?hours=${hours}`).then(res => res.json())

export const getHealth = (node) =>
    fetch(`${BASE_URL}/nodes/${node}/health`).then(res => res.json())