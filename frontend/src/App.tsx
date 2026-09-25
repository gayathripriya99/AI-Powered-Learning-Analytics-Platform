import { useState, useEffect } from 'react'
import DocumentUpload from './DocumentUpload'
import Quiz from './Quiz'

interface Message {
  role: 'user' | 'ai'
  content: string
}

type Page = 'chat' | 'documents' | 'quiz'

function App() {
  // Load messages from localStorage on startup
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem('chat_messages')
    return saved ? JSON.parse(saved) : []
  })
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState<Page>('chat')
  const [quizTopic, setQuizTopic] = useState('')

  const API_URL = import.meta.env.VITE_API_URL ||
    (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')
      ? 'https://ai-powered-learning-analytics-platform.onrender.com'
      : 'http://localhost:8000')

  // Save messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('chat_messages', JSON.stringify(messages))
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, session_id: 'default' })
      })
      const data = await response.json()
      const aiMessage = data.response || 'I could not generate a response.'
      setMessages(prev => [...prev, { role: 'ai', content: aiMessage }])

      if (data.redirect_to_quiz && data.suggested_topic) {
        setQuizTopic(data.suggested_topic)
        setPage('quiz')
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: 'Error: Could not connect to AI' }])
    }
    setLoading(false)
  }

  // Clear chat history
  const clearChat = () => {
    setMessages([])
    localStorage.removeItem('chat_messages')
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">

      {/* Header with Navigation */}
      <div className="bg-gray-800 p-4 border-b border-gray-700">
        <h1 className="text-2xl font-bold text-purple-400 text-center mb-3">
          🎓 Priya Mentor AI
        </h1>
        <p className="text-gray-400 text-sm text-center mb-3">
          Your Personal AI Learning Companion
        </p>
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage('chat')}
            className={`px-4 py-2 rounded-lg font-bold transition-colors ${page === 'chat' ? 'bg-purple-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            💬 Chat
          </button>
          <button
            onClick={() => setPage('documents')}
            className={`px-4 py-2 rounded-lg font-bold transition-colors ${page === 'documents' ? 'bg-purple-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            📄 Documents
          </button>
          <button
            onClick={() => setPage('quiz')}
            className={`px-4 py-2 rounded-lg font-bold transition-colors ${page === 'quiz' ? 'bg-purple-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            🧠 Quiz
          </button>
        </div>
      </div>

      {/* Pages */}
      {page === 'documents' ? (
        <DocumentUpload />
      ) : page === 'quiz' ? (
        <Quiz initialTopic={quizTopic} />
      ) : (
        <>
          {/* Chat header with clear button */}
          <div className="flex justify-between items-center px-4 py-2 bg-gray-850 border-b border-gray-700">
            <span className="text-gray-400 text-sm">{messages.length} messages</span>
            <button
              onClick={clearChat}
              className="text-red-400 hover:text-red-300 text-sm px-3 py-1 rounded border border-red-800 hover:border-red-600"
            >
              🗑 Clear Chat
            </button>
          </div>

          {/* Chat messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-20">
                <p className="text-4xl mb-4">👋</p>
                <p className="text-xl">Hi! I'm your AI mentor.</p>
                <p>Ask me anything to get started!</p>
              </div>
            )}

            {messages.map((msg, index) => (
              <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-2xl p-3 rounded-lg ${msg.role === 'user' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-100'}`}>
                  <p className="text-xs opacity-70 mb-1">{msg.role === 'user' ? 'You' : '🤖 Priya AI'}</p>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-700 p-3 rounded-lg">
                  <p className="text-xs opacity-70 mb-1">🤖 Priya AI</p>
                  <p className="animate-pulse">Thinking...</p>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="p-4 bg-gray-800 border-t border-gray-700 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder="Ask me anything..."
              className="flex-1 bg-gray-700 text-white p-3 rounded-lg outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button
              onClick={sendMessage}
              disabled={loading}
              className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg font-bold disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default App