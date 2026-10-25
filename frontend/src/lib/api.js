const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
const ANALYZE = import.meta.env.VITE_ANALYZE_ENDPOINT || '/api/analyze'
const LIBRARY = import.meta.env.VITE_LIBRARY_ENDPOINT || '/api/songs'

async function request(url, options) {
  const response = await fetch(url, options)
  const raw = await response.text()
  let data = {}
  try { data = raw ? JSON.parse(raw) : {} } catch { data = { detail: raw } }
  if (!response.ok) throw new Error(data.detail || data.message || `Backend returned HTTP ${response.status}`)
  return data
}
export async function analyzeAudio(file, onProgress = () => {}) {
  const form = new FormData()
  form.append('file', file)
  onProgress('Uploading audio…')
  // Keep the response unmodified: the normalizer in App understands common result shapes.
  const endpoint = `${BASE}${ANALYZE.startsWith('/') ? ANALYZE : `/${ANALYZE}`}`
  onProgress('Analyzing instruments and musical features…')
  return request(endpoint, { method: 'POST', body: form })
}
export async function getLibrary() {
  const endpoint = `${BASE}${LIBRARY.startsWith('/') ? LIBRARY : `/${LIBRARY}`}`
  return request(endpoint)
}
export function apiBase() { return BASE }
