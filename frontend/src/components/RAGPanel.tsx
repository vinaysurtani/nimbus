import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

export default function RAGPanel() {
  const [ingestText, setIngestText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [ingestStatus, setIngestStatus] = useState('')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState<string[]>([])
  const [querying, setQuerying] = useState(false)
  const [ingesting, setIngesting] = useState(false)

  const ingest = async () => {
    if (!ingestText.trim() && !file) return
    setIngesting(true)
    setIngestStatus('')
    try {
      if (file) {
        const form = new FormData()
        form.append('file', file)
        const res = await fetch('/api/v1/rag/ingest', { method: 'POST', body: form })
        const data = await res.json()
        setIngestStatus(`Stored ${data.chunks_stored} chunks`)
      } else {
        const res = await fetch('/api/v1/rag/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: ingestText }),
        })
        const data = await res.json()
        setIngestStatus(`Stored ${data.chunks_stored} chunks`)
      }
    } catch {
      setIngestStatus('Ingest failed')
    } finally {
      setIngesting(false)
    }
  }

  const query = async () => {
    if (!question.trim()) return
    setQuerying(true)
    setAnswer('')
    setSources([])
    try {
      const res = await fetch('/api/v1/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      const data = await res.json()
      setAnswer(data.answer)
      setSources(data.sources || [])
    } catch {
      setAnswer('Query failed.')
    } finally {
      setQuerying(false)
    }
  }

  return (
    <div className="panel">
      <div className="rag-grid">
        <div className="card">
          <h2>Ingest Document</h2>
          <textarea
            rows={6}
            placeholder="Paste document text here..."
            value={ingestText}
            onChange={e => setIngestText(e.target.value)}
          />
          <span style={{ color: '#666', fontSize: 12 }}>or upload a file</span>
          <input type="file" accept=".txt,.md" onChange={e => setFile(e.target.files?.[0] ?? null)} />
          <button onClick={ingest} disabled={ingesting || (!ingestText.trim() && !file)}>
            {ingesting ? 'Ingesting...' : 'Ingest'}
          </button>
          {ingestStatus && <span style={{ fontSize: 13, color: '#7c6af7' }}>{ingestStatus}</span>}
        </div>

        <div className="card">
          <h2>Query</h2>
          <div className="input-row">
            <input
              type="text"
              placeholder="Ask a question about your documents..."
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && query()}
            />
            <button onClick={query} disabled={querying || !question.trim()}>
              {querying ? '...' : 'Ask'}
            </button>
          </div>
          {answer && (
            <>
              <div className="answer-box">
                <ReactMarkdown>{answer}</ReactMarkdown>
              </div>
              {sources.length > 0 && (
                <div className="sources">
                  <span style={{ fontSize: 11, color: '#555', marginBottom: 4 }}>Sources</span>
                  {sources.map((s, i) => (
                    <div key={i} className="source-chip">{s.slice(0, 120)}…</div>
                  ))}
                </div>
              )}
            </>
          )}
          {!answer && <div className="empty">Ask a question to retrieve answers from your documents</div>}
        </div>
      </div>
    </div>
  )
}
