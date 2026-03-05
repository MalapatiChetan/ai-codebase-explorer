import { useEffect, useRef } from 'react'
import mermaid from 'mermaid'

export default function ArchitectureDiagram({ diagram, isLoading, error }) {
  const container = useRef(null)

  useEffect(() => {
    if (!diagram || !container.current) return

    // Initialize Mermaid
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
    })

    // Clear previous diagram
    container.current.innerHTML = ''

    // Add diagram content
    const svg = document.createElement('div')
    svg.className = 'mermaid'
    svg.textContent = diagram

    container.current.appendChild(svg)

    // Render diagram
    mermaid.contentLoaded()
  }, [diagram])

  if (isLoading) {
    return (
      <div className="card">
        <div className="card-header">
          <h2 className="text-2xl font-bold text-gray-900">Architecture Diagram</h2>
        </div>
        <div className="card-body flex items-center justify-center min-h-96">
          <div className="text-center">
            <svg className="loading-spinner w-12 h-12 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-gray-600">Loading diagram...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card border-red-200">
        <div className="card-header bg-red-50">
          <h2 className="text-2xl font-bold text-gray-900">Architecture Diagram</h2>
        </div>
        <div className="card-body">
          <div className="error-message">
            {error}
          </div>
        </div>
      </div>
    )
  }

  if (!diagram) {
    return null
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-2xl font-bold text-gray-900">Architecture Diagram</h2>
        <p className="text-gray-600 mt-1 text-sm">Mermaid diagram visualization</p>
      </div>
      <div className="card-body overflow-x-auto">
        <div
          ref={container}
          className="flex justify-center items-start min-h-96"
          style={{ minWidth: '100%' }}
        />
      </div>
    </div>
  )
}
