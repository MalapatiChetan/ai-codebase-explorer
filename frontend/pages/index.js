import { useState, useCallback } from 'react'
import RepositoryInput from '../components/RepositoryInput'
import AnalysisSummary from '../components/AnalysisSummary'
import ArchitectureDiagram from '../components/ArchitectureDiagram'
import QuestionInput from '../components/QuestionInput'
import { analyzeRepository, getDiagram, queryArchitecture, healthCheck } from '../lib/api'

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [metadata, setMetadata] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [diagram, setDiagram] = useState(null)
  const [diagramError, setDiagramError] = useState(null)
  const [diagramLoading, setDiagramLoading] = useState(false)
  const [apiAvailable, setApiAvailable] = useState(true)

  // Check API availability on mount
  const checkApiHealth = useCallback(async () => {
    try {
      await healthCheck()
      setApiAvailable(true)
    } catch {
      setApiAvailable(false)
    }
  }, [])

  // Handle repository analysis
  const handleAnalyze = useCallback(
    async (repoUrl) => {
      setIsLoading(true)
      setError(null)
      setMetadata(null)
      setAnalysis(null)
      setDiagram(null)
      setDiagramError(null)

      try {
        // Analyze repository
        const result = await analyzeRepository(repoUrl)

        setMetadata(result.metadata)
        setAnalysis(result.analysis)

        // Fetch diagram
        if (result.metadata?.repository?.name) {
          setDiagramLoading(true)
          try {
            const diagramResult = await getDiagram(result.metadata.repository.name, 'mermaid')
            setDiagram(diagramResult.diagram)
            setDiagramError(null)
          } catch (err) {
            setDiagramError(err.message)
            setDiagram(null)
          } finally {
            setDiagramLoading(false)
          }
        }
      } catch (err) {
        setError(err.message)
        setMetadata(null)
        setAnalysis(null)
        setDiagram(null)
      } finally {
        setIsLoading(false)
      }
    },
    []
  )

  // Handle architecture query
  const handleQuery = useCallback(async (question) => {
    if (!metadata?.repository?.name) {
      throw new Error('No repository selected')
    }

    const result = await queryArchitecture(metadata.repository.name, question)
    return result
  }, [metadata])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Codebase Explainer</h1>
            <p className="text-sm text-gray-500">Repository Analysis & Architecture Q&A</p>
          </div>
          <div className="flex items-center gap-2">
            {apiAvailable ? (
              <span className="flex items-center gap-2 text-sm text-green-600">
                <span className="inline-block w-2 h-2 bg-green-600 rounded-full"></span>
                API Connected
              </span>
            ) : (
              <span className="flex items-center gap-2 text-sm text-red-600">
                <span className="inline-block w-2 h-2 bg-red-600 rounded-full animate-pulse"></span>
                API Unavailable
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* API Status Alert */}
        {!apiAvailable && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <p className="font-semibold">Backend API Unreachable</p>
            <p className="text-sm mt-1">
              Make sure the backend API is running at {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
            </p>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <p className="font-semibold">Error</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {/* Step 1: Repository Input */}
        <section>
          <RepositoryInput onAnalyze={handleAnalyze} isLoading={isLoading} />
        </section>

        {/* Step 2: Analysis Summary */}
        {metadata && (
          <section>
            <AnalysisSummary analysis={analysis} metadata={metadata} />
          </section>
        )}

        {/* Step 3: Architecture Diagram */}
        {metadata && (
          <section>
            <ArchitectureDiagram
              diagram={diagram}
              isLoading={diagramLoading}
              error={diagramError}
            />
          </section>
        )}

        {/* Step 4: Question Input */}
        {metadata && (
          <section>
            <QuestionInput
              repoName={metadata.repository.name}
              onQuery={handleQuery}
              isLoading={isLoading}
            />
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">About</h3>
              <p className="text-sm text-gray-600">
                AI Codebase Explainer analyzes GitHub repositories and provides architecture insights powered by AI.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Features</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Repository Analysis</li>
                <li>• Architecture Diagrams</li>
                <li>• AI-Powered Q&A</li>
                <li>• Framework Detection</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">API</h3>
              <p className="text-sm text-gray-600">
                Running on: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                <a href="/api/docs" className="text-blue-600 hover:underline">
                  API Documentation
                </a>
              </p>
            </div>
          </div>
          <div className="border-t border-gray-300 mt-8 pt-8 text-center text-sm text-gray-600">
            <p>&copy; 2026 AI Codebase Explainer. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
