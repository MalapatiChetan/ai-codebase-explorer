const LANGUAGE_COLORS = {
  JavaScript: '#f7df1e',
  TypeScript: '#3178c6',
  Python: '#3776ab',
  Java: '#b07219',
  CSS: '#7c3aed',
  HTML: '#e34c26',
  Go: '#00add8',
  C: '#64748b',
  'C++': '#f34b7d',
  CSharp: '#178600',
  Shell: '#22c55e',
  Ruby: '#ef4444',
  PHP: '#4f5d95',
}

function MetricCard({ label, value }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <p className="text-[11px] uppercase tracking-[0.18em] text-gray-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p>
    </div>
  )
}

function CompactSection({ title, children, aside }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-gray-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        {aside}
      </div>
      <div className="p-4">{children}</div>
    </div>
  )
}

function CommitBars({ weeks }) {
  const sample = weeks.slice(-16)
  const max = Math.max(...sample.map((week) => week.total || 0), 1)

  return (
    <div className="flex h-28 items-end gap-1">
      {sample.map((week, index) => (
        <div key={`${week.week}-${index}`} className="flex flex-1 flex-col justify-end">
          <div
            className="rounded-t bg-blue-500"
            style={{ height: `${Math.max((week.total / max) * 100, week.total > 0 ? 8 : 2)}%` }}
            title={`${week.total} commits`}
          />
        </div>
      ))}
    </div>
  )
}

function LanguageBars({ languages }) {
  if (!languages?.length) {
    return <p className="text-sm text-gray-500">Language data is not available.</p>
  }

  return (
    <div className="space-y-3">
      {languages.map((language) => (
        <div key={language.name} className="space-y-2">
          <div className="flex items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: LANGUAGE_COLORS[language.name] || '#3b82f6' }}
              />
              <span className="text-gray-800">{language.name}</span>
            </div>
            <span className="text-gray-500">{language.percentage}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full"
              style={{
                width: `${language.percentage}%`,
                backgroundColor: LANGUAGE_COLORS[language.name] || '#3b82f6',
              }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

function RepositoryInsightsPanel({ insights, note, isLoading, error, username }) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-8 text-center text-sm text-gray-500 shadow-sm">
        <svg className="loading-spinner mx-auto mb-3 h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Loading repository insights...
      </div>
    )
  }

  if (error) {
    return <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
  }

  if (!insights) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white px-4 py-6 text-sm text-gray-500 shadow-sm">
        Select a repository to view GitHub insights.
      </div>
    )
  }

  const contribution = insights.contribution_summary

  return (
    <div className="space-y-4">
      {note ? <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">{note}</div> : null}

      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-lg font-semibold text-gray-900">{insights.repository?.full_name}</p>
            <p className="mt-1 text-sm text-gray-600">{insights.repository?.description || 'No description provided.'}</p>
          </div>
          {insights.repository?.html_url ? (
            <a href={insights.repository.html_url} target="_blank" rel="noreferrer" className="text-sm font-medium text-blue-600">
              Open on GitHub
            </a>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <MetricCard label="Stars" value={insights.stats.stars} />
        <MetricCard label="Forks" value={insights.stats.forks} />
        <MetricCard label="Open Issues" value={insights.stats.open_issues} />
        <MetricCard label="Updated" value={insights.repository?.updated_at ? new Date(insights.repository.updated_at).toLocaleDateString() : '-'} />
      </div>

      {contribution ? (
        <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
          <MetricCard label={`${username} Commits`} value={contribution.commits} />
          <MetricCard label="Contribution Share" value={`${contribution.percentage}%`} />
          <MetricCard
            label="Active Period"
            value={contribution.active_period?.start && contribution.active_period?.end
              ? `${new Date(contribution.active_period.start).toLocaleDateString()} - ${new Date(contribution.active_period.end).toLocaleDateString()}`
              : '-'}
          />
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.1fr,0.9fr]">
        <CompactSection title="Tech Stack">
          <LanguageBars languages={insights.languages} />
        </CompactSection>

        <CompactSection title="Commit Activity" aside={insights.commit_activity?.pending ? <span className="text-xs text-gray-500">Pending</span> : null}>
          {(insights.commit_activity?.weeks || []).length > 0 ? (
            <CommitBars weeks={insights.commit_activity.weeks} />
          ) : (
            <p className="text-sm text-gray-500">GitHub is still computing commit activity.</p>
          )}
        </CompactSection>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[0.95fr,1.05fr]">
        <CompactSection title="Top Contributors">
          <div className="space-y-3">
            {(insights.contributors || []).map((contributor) => (
              <div key={contributor.login} className="flex items-center gap-3 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2">
                <img src={contributor.avatar_url} alt={contributor.login} className="h-10 w-10 rounded-full border border-gray-200" />
                <div className="min-w-0 flex-1">
                  <a href={contributor.html_url} target="_blank" rel="noreferrer" className="truncate font-medium text-gray-900">
                    {contributor.login}
                  </a>
                  <p className="text-xs text-gray-500">{contributor.contributions} commits</p>
                </div>
              </div>
            ))}
          </div>
        </CompactSection>

        <CompactSection title="Code Frequency" aside={insights.code_frequency?.pending ? <span className="text-xs text-gray-500">Pending</span> : null}>
          {(insights.code_frequency?.weeks || []).length > 0 ? (
            <div className="space-y-3">
              {(insights.code_frequency.weeks || []).slice(-8).map((week) => (
                <div key={week[0]} className="grid grid-cols-[72px,1fr,1fr] items-center gap-3 text-xs text-gray-500">
                  <span>{new Date(week[0] * 1000).toLocaleDateString()}</span>
                  <div className="overflow-hidden rounded-full bg-gray-100">
                    <div
                      className="h-2 rounded-full bg-green-500"
                      style={{ width: `${Math.min((week[1] / Math.max(...insights.code_frequency.weeks.map((item) => item[1]), 1)) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="overflow-hidden rounded-full bg-gray-100">
                    <div
                      className="h-2 rounded-full bg-red-500"
                      style={{ width: `${Math.min((Math.abs(week[2]) / Math.max(...insights.code_frequency.weeks.map((item) => Math.abs(item[2])), 1)) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">GitHub is still computing code frequency.</p>
          )}
        </CompactSection>
      </div>
    </div>
  )
}

export default function GitHubExplorerPanel({
  githubUsername,
  onUsernameChange,
  onLoad,
  isLoading,
  error,
  activeTab,
  onTabChange,
  overview,
  repositories,
  selectedRepository,
  onSelectRepository,
  repositoryInsights,
  repositoryInsightsNote,
  repositoryInsightsError,
  isLoadingRepositoryInsights,
}) {
  const profile = overview?.profile
  const summary = overview?.summary

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <p className="text-xs uppercase tracking-[0.22em] text-gray-500">GitHub Explorer</p>
        <h2 className="mt-2 text-2xl font-semibold text-gray-900">Explore GitHub data without indexing</h2>
        <p className="mt-2 text-sm text-gray-600">
          Load a GitHub user profile and repository insights directly from the GitHub API. This section does not run repository analysis.
        </p>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            value={githubUsername}
            onChange={(event) => onUsernameChange(event.target.value)}
            placeholder="GitHub username"
            className="min-w-0 flex-1 rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
          <button
            type="button"
            onClick={onLoad}
            disabled={isLoading}
            className="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading ? 'Loading...' : 'Load Explorer'}
          </button>
        </div>
        {error ? <div className="mt-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      </div>

      <div className="flex items-center gap-2 border-b border-gray-200">
        {['overview', 'repositories'].map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => onTabChange(tab)}
            className={`rounded-t-xl px-4 py-2 text-sm font-medium transition ${
              activeTab === tab
                ? 'border border-gray-200 border-b-white bg-white text-blue-700'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab === 'overview' ? 'User Overview' : 'Repositories'}
          </button>
        ))}
      </div>

      {activeTab === 'overview' ? (
        overview ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-[0.95fr,1.05fr]">
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-start gap-4">
                  {profile?.avatar_url ? <img src={profile.avatar_url} alt={profile.login} className="h-20 w-20 rounded-full border border-gray-200" /> : null}
                  <div className="min-w-0">
                    <p className="text-xl font-semibold text-gray-900">{profile?.name || profile?.login}</p>
                    <p className="text-sm text-gray-500">@{profile?.login}</p>
                    {profile?.bio ? <p className="mt-2 text-sm text-gray-600">{profile.bio}</p> : null}
                    <div className="mt-3 flex flex-wrap gap-2 text-sm text-gray-600">
                      <span>{profile?.followers ?? 0} followers</span>
                      <span>{profile?.following ?? 0} following</span>
                      <span>{profile?.public_repos ?? 0} public repos</span>
                      <span>Joined {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : '-'}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <MetricCard label="Total Repositories" value={summary?.total_repositories ?? 0} />
                <MetricCard label="Most Used Language" value={summary?.most_used_language || '-'} />
                <MetricCard label="Most Starred Repo" value={summary?.most_starred_repository?.name || '-'} />
              </div>
            </div>

            <CompactSection title="Language Summary Across Repositories">
              <LanguageBars languages={overview.languages} />
            </CompactSection>
          </div>
        ) : (
          <div className="rounded-xl border border-gray-200 bg-white px-4 py-6 text-sm text-gray-500 shadow-sm">
            Load a GitHub username to view profile metrics and aggregated language usage.
          </div>
        )
      ) : (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[280px,1fr]">
          <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-200 px-4 py-3">
              <h3 className="text-sm font-semibold text-gray-900">Repositories</h3>
            </div>
            <div className="max-h-[70vh] overflow-y-auto p-2">
              {repositories.length > 0 ? (
                repositories.map((repo) => {
                  const isSelected = selectedRepository?.full_name === repo.full_name
                  return (
                    <button
                      key={repo.full_name}
                      type="button"
                      onClick={() => onSelectRepository(repo)}
                      className={`mb-2 w-full rounded-lg border px-3 py-3 text-left transition ${
                        isSelected
                          ? 'border-blue-200 bg-blue-50'
                          : 'border-gray-200 bg-white hover:border-blue-200 hover:bg-gray-50'
                      }`}
                    >
                      <p className="truncate text-sm font-semibold text-gray-900">{repo.name}</p>
                      <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
                        <span>{repo.language || 'Unknown'}</span>
                        <span>? {repo.stargazers_count}</span>
                      </div>
                    </button>
                  )
                })
              ) : (
                <p className="p-3 text-sm text-gray-500">Load a user to browse repositories.</p>
              )}
            </div>
          </div>

          <RepositoryInsightsPanel
            insights={repositoryInsights}
            note={repositoryInsightsNote}
            isLoading={isLoadingRepositoryInsights}
            error={repositoryInsightsError}
            username={githubUsername}
          />
        </div>
      )}
    </div>
  )
}
