// Quiz.tsx - Quiz Generator Component
// User types a topic, AI generates MCQ questions

import { useState } from 'react'

// TypeScript: define what a Question looks like
interface Question {
  question: string
  options: string[]
  answer: string
  explanation: string
}

function Quiz() {
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('beginner')
  const [questions, setQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<{[key: number]: string}>({})
  const [submitted, setSubmitted] = useState(false)
  const [score, setScore] = useState(0)

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const generateQuiz = async () => {
    if (!topic.trim()) return
    setLoading(true)
    setQuestions([])
    setSelected({})
    setSubmitted(false)

    try {
      const response = await fetch(`${API_URL}/quiz/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          num_questions: 3,
          difficulty
        })
      })
      const data = await response.json()
      setQuestions(data.questions || [])
    } catch (error) {
      console.error('Quiz generation failed')
    }
    setLoading(false)
  }

  const submitQuiz = () => {
    let correct = 0
    questions.forEach((q, i) => {
      if (selected[i] === q.answer) correct++
    })
    setScore(correct)
    setSubmitted(true)
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-purple-400 mb-2">🧠 Quiz Generator</h1>
        <p className="text-gray-400 mb-6">Generate a quiz on any topic!</p>

        {/* Quiz settings */}
        <div className="bg-gray-800 p-4 rounded-xl mb-6 space-y-3">
          <input
            type="text"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            placeholder="Enter topic (e.g. Python, React, SQL)"
            className="w-full bg-gray-700 text-white p-3 rounded-lg outline-none focus:ring-2 focus:ring-purple-500"
          />
          <select
            value={difficulty}
            onChange={e => setDifficulty(e.target.value)}
            className="w-full bg-gray-700 text-white p-3 rounded-lg outline-none"
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
          <button
            onClick={generateQuiz}
            disabled={loading}
            className="w-full bg-purple-600 hover:bg-purple-700 p-3 rounded-lg font-bold disabled:opacity-50"
          >
            {loading ? '⏳ Generating Quiz...' : '🎯 Generate Quiz'}
          </button>
        </div>

        {/* Questions */}
        {questions.map((q, i) => (
          <div key={i} className="bg-gray-800 p-4 rounded-xl mb-4">
            <p className="font-bold mb-3">Q{i+1}: {q.question}</p>
            <div className="space-y-2">
              {q.options.map((opt, j) => (
                <button
                  key={j}
                  onClick={() => !submitted && setSelected(prev => ({...prev, [i]: opt}))}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    submitted
                      ? opt === q.answer
                        ? 'bg-green-700 border-green-500'
                        : opt === selected[i]
                          ? 'bg-red-700 border-red-500'
                          : 'bg-gray-700 border-gray-600'
                      : selected[i] === opt
                        ? 'bg-purple-700 border-purple-500'
                        : 'bg-gray-700 border-gray-600 hover:bg-gray-600'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
            {submitted && (
              <p className="text-sm text-gray-400 mt-2">💡 {q.explanation}</p>
            )}
          </div>
        ))}

        {/* Submit button */}
        {questions.length > 0 && !submitted && (
          <button
            onClick={submitQuiz}
            className="w-full bg-green-600 hover:bg-green-700 p-3 rounded-lg font-bold"
          >
            Submit Quiz
          </button>
        )}

        {/* Score */}
        {submitted && (
          <div className="bg-gray-800 p-4 rounded-xl text-center">
            <p className="text-2xl font-bold text-purple-400">
              Score: {score}/{questions.length}
            </p>
            <p className="text-gray-400 mt-1">
              {score === questions.length ? '🎉 Perfect!' : score > questions.length/2 ? '👍 Good job!' : '📚 Keep studying!'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Quiz