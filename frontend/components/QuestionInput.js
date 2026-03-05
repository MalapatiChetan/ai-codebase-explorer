import { useState } from 'react'

export default function QuestionInput({ repoName, onQuery, isLoading }) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [error, setError] = useState(null)
  const [localLoading, setLocalLoading] = useState(false)
  const [expandedAnswer, setExpandedAnswer] = useState(false)

  if (!repoName) {
    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!question.trim()) {
      setError('Please enter a question')
      return
    }

    setError(null)
    setLocalLoading(true)

    try {
      const result = await onQuery(question)
      setAnswer(result)
      setExpandedAnswer(false)
      setQuestion('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLocalLoading(false)
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-2xl font-bold text-gray-900">
          Ask About the Architecture
        </h2>
        <p className="text-gray-600 mt-1 text-sm">
          Ask questions about {repoName}'s architecture
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card-body space-y-4">
        <div>
          <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
            Your Question
          </label>
          <div className="flex gap-2">
            <input
              id="question"
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., What is the main purpose of this project?"
              disabled={localLoading || isLoading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={localLoading || isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition-colors disabled:cursor-not-allowed whitespace-nowrap"
            >
              {localLoading ? (
                <svg className="loading-spinner w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                'Ask'
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* Suggested Questions */}
        <div>
          <p className="text-xs font-medium text-gray-600 mb-2">Popular Questions:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {[
              'What is this project?',
              'How is it structured?',
              'What technologies are used?',
              'What are the main components?',
            ].map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setQuestion(q)}
                disabled={localLoading || isLoading}
                className="text-left text-sm px-3 py-2 bg-gray-100 hover:bg-blue-100 text-gray-700 hover:text-blue-700 rounded border border-gray-300 hover:border-blue-400 transition-colors disabled:cursor-not-allowed disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </form>

      {/* Answer Display */}
      {answer && (
        <div className="card-footer bg-blue-50 border-t-2 border-blue-200">
          <div className="mb-3">
            <p className="text-sm font-semibold text-gray-700 mb-1">Question:</p>
            <p className="text-gray-800">{answer.question}</p>
          </div>
          <div className="mb-3">
            <p className="text-sm font-semibold text-gray-700 mb-1">Answer:</p>
            <div className={`bg-white p-3 rounded border border-blue-200 text-gray-800 whitespace-pre-wrap break-words text-sm leading-relaxed overflow-auto ${expandedAnswer ? 'max-h-none' : 'max-h-96'}`}>
              {answer.answer}
            </div>
            <button
              type="button"
              onClick={() => setExpandedAnswer((prev) => !prev)}
              className="mt-2 text-xs text-blue-700 hover:text-blue-900 underline"
            >
              {expandedAnswer ? 'Collapse answer' : 'Show full answer'}
            </button>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">
              Mode: <span className="font-semibold">{answer.mode}</span>
            </span>
            {answer.note && (
              <span className="text-xs text-gray-500 italic">{answer.note}</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
