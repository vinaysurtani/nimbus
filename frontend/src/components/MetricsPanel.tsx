import { useState, useEffect } from 'react'

interface Metric {
  endpoint: string
  total_requests: number
  avg_duration: number
  cached_requests: number
  cache_hit_rate: number
}

export default function MetricsPanel() {
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [lastUpdated, setLastUpdated] = useState('')

  const fetchMetrics = async () => {
    try {
      const res = await fetch('/api/v1/metrics')
      const data = await res.json()
      setMetrics(data.metrics || [])
      setLastUpdated(new Date().toLocaleTimeString())
    } catch {
      // silently retry on next tick
    }
  }

  useEffect(() => {
    fetchMetrics()
    const id = setInterval(fetchMetrics, 10000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 13, color: '#888' }}>Last hour · updates every 10s</span>
        {lastUpdated && <span style={{ fontSize: 12, color: '#555' }}>Updated {lastUpdated}</span>}
      </div>
      {metrics.length === 0 ? (
        <div className="empty">No requests yet — make some API calls and check back</div>
      ) : (
        <div className="metrics-grid">
          {metrics.map((m, i) => (
            <div key={i} className="metric-card">
              <h3>{m.endpoint}</h3>
              <div className="metric-row">
                <span>Total requests</span>
                <span className="metric-val">{m.total_requests}</span>
              </div>
              <div className="metric-row">
                <span>Avg latency</span>
                <span className="metric-val">{Math.round(m.avg_duration)} ms</span>
              </div>
              <div className="metric-row">
                <span>Cached</span>
                <span className="metric-val">{m.cached_requests}</span>
              </div>
              <div className="metric-row">
                <span>Cache hit rate</span>
                <span className="metric-val">{m.cache_hit_rate.toFixed(1)}%</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
