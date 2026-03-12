import { useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function QuestionInput({
  repoName,
  onQuery,
  isLoading,
  conversation = [],
  onConversationChange,
}) {
  const [question, setQuestion] = useState('')
  const [error, setError] = useState(null)
  const [localLoading, setLocalLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)
  const messages = useMemo(() => conversation || [], [conversation])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, localLoading])

  const resizeTextarea = () => {
    if (!textareaRef.current) {
      return
    }
    textareaRef.current.style.height = 'auto'
    textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`
  }

  const handleChange = (event) => {
    setQuestion(event.target.value)
    resizeTextarea()
  }

  const handleSubmit = async (event) => {
    if (event) {
      event.preventDefault()
    }

    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || !repoName) {
      return
    }

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmedQuestion,
    }
    const nextMessages = [...messages, userMessage]

    setError(null)
    setLocalLoading(true)
    onConversationChange(nextMessages)
    setQuestion('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      const historyForBackend = messages.map((message) => ({
        role: message.role,
        content: message.content,
      }))
      const result = await onQuery(trimmedQuestion, historyForBackend)
      onConversationChange([
        ...nextMessages,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: result.answer,
          mode: result.mode,
          note: result.note,
        },
      ])
    } catch (err) {
      setError(err.message)
    } finally {
      setLocalLoading(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex h-full min-h-[420px] flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.18em] text-gray-500">Chat</p>
            <h3 className="mt-1 text-sm font-semibold text-gray-900">
              {repoName ? `Ask ${repoName}` : 'Repository Chat'}
            </h3>
          </div>
          <span className="text-xs text-gray-500">{messages.length} messages</span>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 px-4 py-6 text-sm text-gray-500">
            Start with a question about architecture, request flow, responsibilities, or improvement ideas.
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((message, index) => {
              const isUser = message.role === 'user'
              return (
                <div
                  key={message.id || `${message.role}-${index}`}
                  className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[88%] rounded-2xl px-4 py-3 shadow-sm ${isUser ? 'rounded-br-md bg-blue-600 text-white' : 'rounded-bl-md border border-gray-200 bg-gray-50 text-gray-900'}`}>
                    {!isUser ? (
                      <div className="mb-1.5 flex items-center justify-between gap-3 text-[11px] uppercase tracking-[0.15em] text-gray-500">
                        <span>Assistant</span>
                        {message.mode ? <span>{message.mode}</span> : null}
                      </div>
                    ) : null}

                    {isUser ? (
                      <p className="m-0 whitespace-pre-wrap break-words text-sm leading-6">{message.content}</p>
                    ) : (
                      <div className="markdown-message">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            code({ inline, children, ...props }) {
                              if (inline) {
                                return <code {...props}>{children}</code>
                              }
                              return (
                                <pre>
                                  <code {...props}>{children}</code>
                                </pre>
                              )
                            },
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    )}

                    {!isUser && message.note ? (
                      <p className="mt-2 text-xs text-gray-500">{message.note}</p>
                    ) : null}
                  </div>
                </div>
              )
            })}

            {localLoading ? (
              <div className="flex justify-start">
                <div className="max-w-[88%] rounded-2xl rounded-bl-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600">
                  <span className="inline-flex items-center gap-2">
                    <span className="loading-spinner inline-block h-4 w-4 rounded-full border-2 border-blue-200 border-t-blue-600" />
                    Gemini is generating a response...
                  </span>
                </div>
              </div>
            ) : null}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="sticky bottom-0 border-t border-gray-200 bg-white px-4 py-3">
        <form onSubmit={handleSubmit} className="space-y-2">
          <div className="flex items-end gap-3">
            <textarea
              ref={textareaRef}
              rows={1}
              value={question}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              disabled={!repoName || localLoading || isLoading}
              placeholder={repoName ? 'Ask about the repository architecture...' : 'Analyze a repository to start chatting'}
              className="min-h-[44px] max-h-[180px] flex-1 resize-none rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-gray-100"
            />
            <button
              type="submit"
              disabled={!repoName || localLoading || isLoading || !question.trim()}
              className="flex h-[44px] w-[44px] items-center justify-center rounded-xl bg-blue-600 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              aria-label="Send message"
            >
              <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h12m-5-5 5 5-5 5" />
              </svg>
            </button>
          </div>
          <div className="flex items-center justify-between gap-3 text-xs text-gray-500">
            <span>Enter to send. Shift+Enter for a new line.</span>
            {error ? <span className="text-red-600">{error}</span> : null}
          </div>
        </form>
      </div>
    </div>
  )
}
