import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const text = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)

    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const resp = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })

      const reader = resp.body!.getReader()
      const decoder = new TextDecoder()
      let accumulated = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const raw = decoder.decode(value, { stream: true })
        for (const line of raw.split('\n')) {
          if (line.startsWith('data: ')) {
            const chunk = line.slice(6)
            if (chunk === '[DONE]') break
            accumulated += chunk
            setMessages(prev => [
              ...prev.slice(0, -1),
              { role: 'assistant', content: accumulated },
            ])
          }
        }
      }
    } catch {
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: 'Error reaching the service.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <div className="messages">
        {messages.length === 0 && (
          <div className="empty">Send a message to start chatting with Claude</div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.role === 'assistant'
              ? <ReactMarkdown>{m.content || '▋'}</ReactMarkdown>
              : m.content}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="input-row">
        <input
          type="text"
          value={input}
          placeholder="Message Claude..."
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          disabled={loading}
        />
        <button onClick={send} disabled={loading || !input.trim()}>
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  )
}
