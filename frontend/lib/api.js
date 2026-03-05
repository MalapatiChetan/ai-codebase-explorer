import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Repository Analysis
export const analyzeRepository = async (repoUrl) => {
  try {
    const response = await apiClient.post('/api/analyze', {
      repo_url: repoUrl,
      include_ai_analysis: true,
      include_diagrams: true,
    })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to analyze repository')
  }
}

// Get Diagram
export const getDiagram = async (repoName, format = 'mermaid') => {
  try {
    const response = await apiClient.get(`/api/diagrams/${repoName}`, {
      params: { format },
    })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to retrieve diagram')
  }
}

// Query Architecture
export const queryArchitecture = async (repositoryName, question) => {
  try {
    const response = await apiClient.post('/api/query', {
      repository_name: repositoryName,
      question,
    })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to query architecture')
  }
}

// Health Check
export const healthCheck = async () => {
  try {
    const response = await apiClient.get('/api/health')
    return response.data
  } catch (error) {
    throw new Error('Backend API is not available')
  }
}

// Get Info
export const getApiInfo = async () => {
  try {
    const response = await apiClient.get('/api/info')
    return response.data
  } catch (error) {
    throw new Error('Failed to retrieve API information')
  }
}

export default apiClient
