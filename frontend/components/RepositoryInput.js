import { useState } from 'react'

export default function RepositoryInput({ onAnalyze, isLoading }) {
  const [repoUrl, setRepoUrl] = useState('')
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!repoUrl.trim()) {
      setError('Please enter a repository URL')
      return
    }

    if (!repoUrl.startsWith('https://github.com/')) {
      setError('URL must be a valid GitHub URL (https://github.com/...)')
      return
    }

    setError(null)
    await onAnalyze(repoUrl)
  }

  return (
    <div className="card">
      <div className="card-header">
        <h1 className="text-3xl font-bold text-gray-900">
          AI Codebase Explainer
        </h1>
        <p className="text-gray-600 mt-2">
          Analyze GitHub repositories and explore architecture insights
        </p>
      </div>
      
      <form onSubmit={handleSubmit} className="card-body space-y-4">
        <div>
          <label htmlFor="repo-url" className="block text-sm font-medium text-gray-700 mb-2">
            GitHub Repository URL
          </label>
          <input
            id="repo-url"
            type="url"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repository"
            disabled={isLoading}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition-colors disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="loading-spinner w-5 h-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing Repository...
            </span>
          ) : (
            'Analyze Repository'
          )}
        </button>
      </form>
    </div>
  )
}
