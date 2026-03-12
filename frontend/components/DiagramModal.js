import { useEffect, useRef } from 'react'
import mermaid from 'mermaid'

export default function DiagramModal({ isOpen, diagram, onClose, repoName }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!isOpen || !diagram || !containerRef.current) {
      return
    }

    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
    })

    containerRef.current.innerHTML = ''
    const node = document.createElement('div')
    node.className = 'mermaid'
    node.textContent = diagram
    containerRef.current.appendChild(node)
    mermaid.contentLoaded()
  }, [isOpen, diagram])

  useEffect(() => {
    if (!isOpen) {
      return
    }

    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-8 backdrop-blur-sm">
      <div className="w-full max-w-6xl rounded-2xl border border-gray-200 bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-gray-500">Architecture Diagram</p>
            <h3 className="mt-1 text-lg font-semibold text-gray-900">{repoName}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 transition hover:bg-gray-50"
          >
            Close
          </button>
        </div>
        <div className="max-h-[80vh] overflow-auto p-5">
          {diagram ? (
            <div ref={containerRef} className="min-h-[420px] rounded-xl border border-gray-200 bg-gray-50 p-4" />
          ) : (
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-6 text-sm text-gray-500">
              Diagram is not available for this repository.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
