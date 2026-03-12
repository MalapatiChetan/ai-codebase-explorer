import { useCallback, useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import QuestionInput from '../components/QuestionInput'
import InsightsDashboard from '../components/InsightsDashboard'
import ArchitectureDiagram from '../components/ArchitectureDiagram'
import GitHubExplorerPanel from '../components/GitHubExplorerPanel'
import {
  analyzeRepository,
  getDiagram,
  queryArchitecture,
  getRepositoryInsights,
  getGitHubRepositoryInsights,
  getGitHubUserOverview,
  getUserRepositories,
  healthCheck,
} from '../lib/api'

const NAV_ITEMS = [
  { id: 'codebase', label: 'Codebase', icon: '</>' },
  { id: 'explorer', label: 'GitHub Explorer', icon: 'GH' },
]

const ANALYZE_STEPS = [
  'cloning repository',
  'scanning files',
  'generating code chunks',
  'creating embeddings',
  'uploading vectors',
  'indexing complete',
]

function NavButton({ item, collapsed, active, onClick }) {
  return (
    <button
      type="button"
      onClick={() => onClick(item.id)}
      className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm font-medium transition ${
        active
          ? 'border border-blue-200 bg-blue-50 text-blue-700'
          : 'border border-transparent text-gray-600 hover:bg-gray-50 hover:text-gray-900'
      }`}
    >
      <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-white text-xs font-semibold text-gray-700">
        {item.icon}
      </span>
      {!collapsed ? <span>{item.label}</span> : null}
    </button>
  )
}

export default function Home() {
  const [apiAvailable, setApiAvailable] = useState(true)
  const [activeSection, setActiveSection] = useState('codebase')
  const [activeCodebaseTab, setActiveCodebaseTab] = useState('chat')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [repoUrl, setRepoUrl] = useState('')
  const [githubUsername, setGithubUsername] = useState('')
  const [conversation, setConversation] = useState([])
  const [metadata, setMetadata] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [diagram, setDiagram] = useState(null)
  const [insights, setInsights] = useState(null)
  const [insightsNote, setInsightsNote] = useState(null)
  const [insightsError, setInsightsError] = useState(null)
  const [pageError, setPageError] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isLoadingInsights, setIsLoadingInsights] = useState(false)
  const [analyzeStepIndex, setAnalyzeStepIndex] = useState(-1)
  const [showProgress, setShowProgress] = useState(false)
  const [showSuccessStatus, setShowSuccessStatus] = useState(false)

  const [explorerTab, setExplorerTab] = useState('overview')
  const [explorerRepos, setExplorerRepos] = useState([])
  const [explorerOverview, setExplorerOverview] = useState(null)
  const [selectedExplorerRepo, setSelectedExplorerRepo] = useState(null)
  const [explorerRepoInsights, setExplorerRepoInsights] = useState(null)
  const [explorerRepoInsightsNote, setExplorerRepoInsightsNote] = useState(null)
  const [explorerError, setExplorerError] = useState(null)
  const [explorerRepoInsightsError, setExplorerRepoInsightsError] = useState(null)
  const [isLoadingExplorer, setIsLoadingExplorer] = useState(false)
  const [isLoadingExplorerRepoInsights, setIsLoadingExplorerRepoInsights] = useState(false)

  const indexedChunks = metadata?.indexing?.chunk_count || 0
  const activeRepoIndicator = metadata?.repository?.name || 'No repository loaded'

  const checkApiHealth = useCallback(async () => {
    try {
      await healthCheck()
      setApiAvailable(true)
    } catch {
      setApiAvailable(false)
    }
  }, [])

  useEffect(() => {
    checkApiHealth()
  }, [checkApiHealth])

  useEffect(() => {
    if (!isAnalyzing) {
      return
    }

    setShowProgress(true)
    setShowSuccessStatus(false)
    setAnalyzeStepIndex(0)
    const interval = window.setInterval(() => {
      setAnalyzeStepIndex((current) => Math.min(current + 1, ANALYZE_STEPS.length - 2))
    }, 1200)

    return () => window.clearInterval(interval)
  }, [isAnalyzing])

  useEffect(() => {
    if (!showSuccessStatus) {
      return
    }

    const collapseTimer = window.setTimeout(() => {
      setShowSuccessStatus(false)
    }, 3200)

    return () => window.clearTimeout(collapseTimer)
  }, [showSuccessStatus])

  const loadInsights = useCallback(async (repositoryName) => {
    if (!repositoryName) {
      return
    }

    setIsLoadingInsights(true)
    setInsightsError(null)

    try {
      const result = await getRepositoryInsights(repositoryName)
      setInsights(result.insights)
      setInsightsNote(result.note || null)
    } catch (err) {
      setInsights(null)
      setInsightsNote(null)
      setInsightsError(err.message)
    } finally {
      setIsLoadingInsights(false)
    }
  }, [])

  const analyzeRepo = useCallback(async (url) => {
    const trimmedUrl = (url || repoUrl).trim()
    if (!trimmedUrl) {
      setPageError('Enter a GitHub repository URL.')
      return
    }

    setIsAnalyzing(true)
    setPageError(null)
    setMetadata(null)
    setAnalysis(null)
    setDiagram(null)
    setInsights(null)
    setInsightsNote(null)
    setInsightsError(null)
    setConversation([])
    setActiveCodebaseTab('chat')

    try {
      const result = await analyzeRepository(trimmedUrl)
      setRepoUrl(trimmedUrl)
      setMetadata(result.metadata)
      setAnalysis(result.analysis || null)

      if (result.metadata?.repository?.name) {
        try {
          const diagramResult = await getDiagram(result.metadata.repository.name, 'mermaid')
          setDiagram(diagramResult.diagram)
        } catch {
          setDiagram(null)
        }

        await loadInsights(result.metadata.repository.name)
      }

      setAnalyzeStepIndex(ANALYZE_STEPS.length - 1)
      setShowProgress(false)
      setShowSuccessStatus(true)
      setActiveSection('codebase')
    } catch (err) {
      setPageError(err.message)
      setShowProgress(false)
    } finally {
      setIsAnalyzing(false)
    }
  }, [loadInsights, repoUrl])

  const handleQuery = useCallback(async (question, conversationHistory = []) => {
    if (!metadata?.repository?.name) {
      throw new Error('Analyze a repository first')
    }

    return queryArchitecture(metadata.repository.name, question, conversationHistory)
  }, [metadata])

  const loadExplorerData = useCallback(async () => {
    const username = githubUsername.trim()
    if (!username) {
      setExplorerError('Enter a GitHub username.')
      return
    }

    setIsLoadingExplorer(true)
    setExplorerError(null)

    try {
      const [overviewResult, repositoriesResult] = await Promise.all([
        getGitHubUserOverview(username),
        getUserRepositories(username),
      ])
      const repositories = repositoriesResult.repositories || []
      setExplorerOverview(overviewResult.overview || null)
      setExplorerRepos(repositories)
      setExplorerTab('overview')
      setSelectedExplorerRepo(null)
      setExplorerRepoInsights(null)
      setExplorerRepoInsightsNote(null)
      setExplorerRepoInsightsError(null)
    } catch (err) {
      setExplorerOverview(null)
      setExplorerRepos([])
      setSelectedExplorerRepo(null)
      setExplorerRepoInsights(null)
      setExplorerRepoInsightsNote(null)
      setExplorerRepoInsightsError(null)
      setExplorerError(err.message)
    } finally {
      setIsLoadingExplorer(false)
    }
  }, [githubUsername])

  const loadExplorerRepoInsights = useCallback(async (repository) => {
    if (!repository?.owner || !repository?.name) {
      return
    }

    setSelectedExplorerRepo(repository)
    setExplorerTab('repositories')
    setIsLoadingExplorerRepoInsights(true)
    setExplorerRepoInsightsError(null)

    try {
      const result = await getGitHubRepositoryInsights(repository.owner, repository.name, githubUsername.trim())
      setExplorerRepoInsights(result.insights)
      setExplorerRepoInsightsNote(result.note || null)
    } catch (err) {
      setExplorerRepoInsights(null)
      setExplorerRepoInsightsNote(null)
      setExplorerRepoInsightsError(err.message)
    } finally {
      setIsLoadingExplorerRepoInsights(false)
    }
  }, [githubUsername])

  return (
    <div className="h-screen overflow-hidden bg-white text-gray-900">
      <header className="fixed inset-x-0 top-0 z-40 border-b border-gray-200 bg-white">
        <div className="flex h-14 items-center justify-between px-4 sm:px-6">
          <p className="text-base font-semibold text-gray-900">Codebase AI Explorer</p>
          <p className="truncate text-sm text-gray-500">{activeRepoIndicator}</p>
        </div>
      </header>

      <div className="flex h-full pt-14">
        <aside className={`fixed bottom-0 left-0 top-14 ${sidebarCollapsed ? 'w-[88px]' : 'w-[260px]'} border-r border-gray-200 bg-gray-50 transition-all duration-200`}>
          <div className="flex h-full flex-col gap-4 overflow-hidden p-4">
            <div className="flex items-center justify-between gap-2">
              {!sidebarCollapsed ? (
                <div>
                  <p className="text-xs uppercase tracking-[0.22em] text-gray-500">Repository Assistant</p>
                  <h1 className="mt-1 text-lg font-semibold text-gray-900">Navigation</h1>
                </div>
              ) : <div />}
              <button
                type="button"
                onClick={() => setSidebarCollapsed((current) => !current)}
                className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 transition hover:bg-gray-100"
                aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              >
                {sidebarCollapsed ? '>' : '<'}
              </button>
            </div>

            <nav className="space-y-2">
              {NAV_ITEMS.map((item) => (
                <NavButton
                  key={item.id}
                  item={item}
                  collapsed={sidebarCollapsed}
                  active={activeSection === item.id}
                  onClick={setActiveSection}
                />
              ))}
            </nav>

            {!sidebarCollapsed ? (
              <div className="mt-auto rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Status</p>
                <div className="mt-3 flex items-center gap-2">
                  <span className={`inline-block h-2.5 w-2.5 rounded-full ${apiAvailable ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-sm text-gray-700">{apiAvailable ? 'API connected' : 'API unavailable'}</span>
                </div>
                {metadata?.repository?.name ? (
                  <div className="mt-4 space-y-1 text-sm text-gray-600">
                    <p className="font-medium text-gray-900">{metadata.repository.name}</p>
                    {indexedChunks ? <p>{indexedChunks} indexed chunks</p> : null}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </aside>

        <main className={`min-w-0 flex-1 overflow-y-auto ${sidebarCollapsed ? 'ml-[88px]' : 'ml-[260px]'}`}>
          {activeSection === 'codebase' ? (
            <div className="flex min-h-full flex-col">
              <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/95 px-4 py-3 shadow-sm backdrop-blur sm:px-6">
                <div className="flex flex-col gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-col gap-2 lg:flex-row lg:items-center">
                      <input
                        type="url"
                        value={repoUrl}
                        onChange={(event) => setRepoUrl(event.target.value)}
                        disabled={isAnalyzing}
                        placeholder="https://github.com/owner/repository"
                        className="min-w-0 flex-1 rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-gray-100"
                      />
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => analyzeRepo()}
                          disabled={isAnalyzing}
                          className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {isAnalyzing ? 'Analyzing...' : 'Analyze Repository'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                {showProgress ? (
                  <div className="progress-fade mt-3 overflow-hidden rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
                      {ANALYZE_STEPS.map((step, index) => {
                        const isCompleted = analyzeStepIndex > index
                        const isCurrent = analyzeStepIndex === index
                        return (
                          <div key={step} className="inline-flex items-center gap-2">
                            <span className={`inline-flex items-center gap-1 ${
                              isCompleted ? 'text-green-700' : isCurrent ? 'text-blue-700' : 'text-gray-400'
                            }`}>
                              <span className={`inline-block h-1.5 w-1.5 rounded-full ${
                                isCompleted ? 'bg-green-600' : isCurrent ? 'bg-blue-600' : 'bg-gray-300'
                              }`} />
                              {step}
                            </span>
                            {index < ANALYZE_STEPS.length - 1 ? <span className="text-gray-300">-&gt;</span> : null}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ) : null}
                {showSuccessStatus && metadata?.repository?.name ? (
                  <div className="success-slide mt-3 inline-flex flex-wrap items-center gap-3 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
                    {indexedChunks ? <span>Index ready | {indexedChunks} chunks</span> : <span>Index ready</span>}
                  </div>
                ) : null}
                {pageError ? (
                  <div className="mt-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {pageError}
                  </div>
                ) : null}
              </header>

              <div className="flex flex-1 flex-col gap-4 px-4 py-4 sm:px-6">
                <div className="sticky top-[72px] z-10 -mx-4 border-b border-gray-200 bg-white px-4 sm:-mx-6 sm:px-6">
                  <div className="flex items-center gap-2">
                    {['chat', 'insights', 'architecture'].map((tab) => (
                      <button
                        key={tab}
                        type="button"
                        onClick={() => setActiveCodebaseTab(tab)}
                        className={`rounded-t-xl px-4 py-2 text-sm font-medium transition ${
                          activeCodebaseTab === tab
                            ? 'border border-gray-200 border-b-white bg-white text-blue-700'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                      >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                {activeCodebaseTab === 'chat' ? (
                  <section className="min-h-0 flex-1">
                    <QuestionInput
                      repoName={metadata?.repository?.name}
                      onQuery={handleQuery}
                      isLoading={isAnalyzing}
                      conversation={conversation}
                      onConversationChange={setConversation}
                    />
                  </section>
                ) : null}

                {activeCodebaseTab === 'insights' ? (
                  <section className="shrink-0">
                    <InsightsDashboard
                      insights={insights}
                      isLoading={isLoadingInsights}
                      error={insightsError}
                      note={insightsNote}
                    />
                  </section>
                ) : null}

                {activeCodebaseTab === 'architecture' ? (
                  <section className="space-y-4">
                    <ArchitectureDiagram
                      diagram={diagram}
                      isLoading={isAnalyzing && !diagram}
                      error={!diagram && metadata ? 'Architecture diagram is not available for this repository.' : null}
                    />
                    <div className="card">
                      <div className="card-header">
                        <h3 className="text-lg font-semibold text-gray-900">Project Analysis</h3>
                      </div>
                      <div className="card-body">
                        <div className="markdown-message">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {analysis?.analysis?.raw_analysis || analysis?.analysis || 'Analyze a repository to see the project analysis summary.'}
                          </ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  </section>
                ) : null}
              </div>
            </div>
          ) : (
            <div className="min-h-full px-4 py-6 sm:px-6">
              <GitHubExplorerPanel
                githubUsername={githubUsername}
                onUsernameChange={setGithubUsername}
                onLoad={loadExplorerData}
                isLoading={isLoadingExplorer}
                error={explorerError}
                activeTab={explorerTab}
                onTabChange={setExplorerTab}
                overview={explorerOverview}
                repositories={explorerRepos}
                selectedRepository={selectedExplorerRepo}
                onSelectRepository={loadExplorerRepoInsights}
                repositoryInsights={explorerRepoInsights}
                repositoryInsightsNote={explorerRepoInsightsNote}
                repositoryInsightsError={explorerRepoInsightsError}
                isLoadingRepositoryInsights={isLoadingExplorerRepoInsights}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
