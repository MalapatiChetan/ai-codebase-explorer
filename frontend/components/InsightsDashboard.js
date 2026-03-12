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

export default function InsightsDashboard({ insights, isLoading, error, note }) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-8 text-center text-sm text-gray-500 shadow-sm">
        <svg className="loading-spinner mx-auto mb-3 h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Loading GitHub insights...
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    )
  }

  if (!insights) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white px-4 py-6 text-sm text-gray-500 shadow-sm">
        Analyze a repository to load GitHub insights.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {note ? (
        <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          {note}
        </div>
      ) : null}

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <MetricCard label="Stars" value={insights.stats.stars} />
        <MetricCard label="Forks" value={insights.stats.forks} />
        <MetricCard label="Watchers" value={insights.stats.watchers} />
        <MetricCard label="Open Issues" value={insights.stats.open_issues} />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.1fr,0.9fr]">
        <CompactSection title="Tech Stack">
          <div className="space-y-3">
            {(insights.languages || []).map((language) => (
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
                <img
                  src={contributor.avatar_url}
                  alt={contributor.login}
                  className="h-10 w-10 rounded-full border border-gray-200"
                />
                <div className="min-w-0 flex-1">
                  <a href={contributor.html_url} target="_blank" rel="noreferrer" className="truncate font-medium text-gray-900">
                    {contributor.login}
                  </a>
                  <p className="text-xs text-gray-500">{contributor.contributions} commits</p>
                </div>
                <div className="w-24 overflow-hidden rounded-full bg-gray-200">
                  <div
                    className="h-2 rounded-full bg-violet-500"
                    style={{
                      width: `${(contributor.contributions / Math.max(...insights.contributors.map((item) => item.contributions), 1)) * 100}%`,
                    }}
                  />
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
              <div className="flex gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-green-500" />Additions</span>
                <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-red-500" />Deletions</span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">GitHub is still computing code frequency.</p>
          )}
        </CompactSection>
      </div>
    </div>
  )
}
