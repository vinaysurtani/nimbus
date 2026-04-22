import { useState } from 'react'
import ChatPanel from './components/ChatPanel'
import RAGPanel from './components/RAGPanel'
import MetricsPanel from './components/MetricsPanel'

type Tab = 'chat' | 'rag' | 'metrics'

export default function App() {
  const [tab, setTab] = useState<Tab>('chat')

  return (
    <>
      <div className="header">
        <h1>Nimbus AI</h1>
        <span>microservices · claude · rag</span>
      </div>
      <div className="tabs">
        {(['chat', 'rag', 'metrics'] as Tab[]).map(t => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'chat' ? 'Chat' : t === 'rag' ? 'RAG' : 'Metrics'}
          </button>
        ))}
      </div>
      {tab === 'chat' && <ChatPanel />}
      {tab === 'rag' && <RAGPanel />}
      {tab === 'metrics' && <MetricsPanel />}
    </>
  )
}
