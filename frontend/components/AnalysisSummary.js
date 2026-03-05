export default function AnalysisSummary({ analysis, metadata }) {
  if (!metadata) return null

  const repo = metadata.repository
  const info = metadata.analysis
  const frameworks = metadata.frameworks || {}
  const patterns = metadata.architecture_patterns || []

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-2xl font-bold text-gray-900">
          {repo.name}
        </h2>
        <p className="text-gray-600 mt-1">{repo.url}</p>
      </div>

      <div className="card-body space-y-6">
        {/* Overview Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Primary Language</h3>
            <p className="text-2xl font-bold text-blue-600">{info.primary_language}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Total Files</h3>
            <p className="text-2xl font-bold text-green-600">{info.file_count}</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Languages</h3>
            <p className="text-2xl font-bold text-purple-600">{info.languages.length}</p>
          </div>
        </div>

        {/* Architecture Info */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Architecture</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">
                {info.has_backend && info.has_frontend ? '✅ Full Stack' : info.has_backend ? '✅ Backend Focus' : '✅ Frontend Focus'}
              </p>
              {info.has_backend && <p className="text-sm text-gray-600">• Has Backend: Yes</p>}
              {info.has_frontend && <p className="text-sm text-gray-600">• Has Frontend: Yes</p>}
            </div>
            {patterns.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Patterns</p>
                <div className="flex flex-wrap gap-2">
                  {patterns.map((pattern) => (
                    <span
                      key={pattern}
                      className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium"
                    >
                      {pattern}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Frameworks */}
        {Object.keys(frameworks).length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Detected Frameworks</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(frameworks)
                .sort((a, b) => b[1].confidence - a[1].confidence)
                .slice(0, 6)
                .map(([name, info]) => (
                  <div key={name} className="bg-gray-50 p-3 rounded border border-gray-200">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-semibold text-gray-900">{name}</span>
                      <span className="text-sm font-medium text-blue-600">
                        {Math.round(info.confidence * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${info.confidence * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Technology Stack */}
        {metadata.tech_stack && metadata.tech_stack.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Technology Stack</h3>
            <div className="flex flex-wrap gap-2">
              {metadata.tech_stack.slice(0, 12).map((tech) => (
                <span
                  key={tech}
                  className="inline-block bg-gray-200 text-gray-800 px-3 py-1 rounded-full text-sm font-medium"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* AI Analysis */}
        {analysis && analysis.analysis && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">AI Analysis</h3>
            <div className="bg-gray-50 p-4 rounded border border-gray-200 text-sm text-gray-700 whitespace-pre-wrap max-h-60 overflow-y-auto">
              {typeof analysis.analysis === 'string'
                ? analysis.analysis
                : analysis.analysis.raw_analysis}
            </div>
            {analysis.analysis.note && (
              <p className="text-xs text-gray-500 mt-2 italic">{analysis.analysis.note}</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
