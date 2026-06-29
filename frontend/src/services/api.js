const API_BASE = 'http://127.0.0.1:8765'

// ─── Health ───────────────────────────────────────────────────────────────────
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('Backend offline')
  return res.json()
}

// ─── Chat (SSE streaming) ─────────────────────────────────────────────────────
export async function streamChat(messages, model, onChunk, onDone, {
  filters = null, useConsultations = true,
} = {}) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages, model, stream: true,
      use_portfolio: true,
      use_consultations: useConsultations,
      filters,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Chat API error')
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.done) { onDone(); return }
        if (data.content) onChunk(data.content)
      } catch { /* ignore */ }
    }
  }
  onDone()
}

// ─── Properties CRUD ──────────────────────────────────────────────────────────
export async function fetchProperties(params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '' && v !== null) qs.append(k, v) })
  const res = await fetch(`${API_BASE}/properties?${qs}`)
  if (!res.ok) throw new Error('Lỗi tải danh sách BĐS')
  return res.json()
}
export async function createProperty(data) {
  const res = await fetch(`${API_BASE}/properties`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Lỗi tạo BĐS') }
  return res.json()
}
export async function updateProperty(id, data) {
  const res = await fetch(`${API_BASE}/properties/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Lỗi cập nhật BĐS') }
  return res.json()
}
export async function deleteProperty(id) {
  const res = await fetch(`${API_BASE}/properties/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Lỗi xóa BĐS')
  return res.json()
}
export async function importJson(file) {
  const form = new FormData(); form.append('file', file)
  const res = await fetch(`${API_BASE}/properties/import/json`, { method: 'POST', body: form })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Lỗi import JSON') }
  return res.json()
}
export async function importCsv(file) {
  const form = new FormData(); form.append('file', file)
  const res = await fetch(`${API_BASE}/properties/import/csv`, { method: 'POST', body: form })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Lỗi import CSV') }
  return res.json()
}
export async function fetchStats() {
  const res = await fetch(`${API_BASE}/properties/stats`)
  if (!res.ok) throw new Error('Lỗi tải thống kê')
  return res.json()
}

// ─── Consultations CRUD ───────────────────────────────────────────────────────
export async function fetchConsultations(params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '' && v !== null) qs.append(k, v) })
  const res = await fetch(`${API_BASE}/consultations?${qs}`)
  if (!res.ok) throw new Error('Lỗi tải danh sách tư vấn')
  return res.json()
}
export async function fetchConsultation(id) {
  const res = await fetch(`${API_BASE}/consultations/${id}`)
  if (!res.ok) throw new Error('Không tìm thấy buổi tư vấn')
  return res.json()
}
export async function createConsultation(data) {
  const res = await fetch(`${API_BASE}/consultations`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Lỗi tạo') }
  return res.json()
}
export async function updateConsultation(id, data) {
  const res = await fetch(`${API_BASE}/consultations/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Lỗi cập nhật') }
  return res.json()
}
export async function deleteConsultation(id) {
  const res = await fetch(`${API_BASE}/consultations/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Lỗi xóa')
  return res.json()
}
export async function fetchConsultationStats() {
  const res = await fetch(`${API_BASE}/consultations/stats`)
  if (!res.ok) throw new Error('Lỗi tải thống kê')
  return res.json()
}
export async function saveTranscriptChunks(sessionId, chunks) {
  const res = await fetch(`${API_BASE}/consultations/${sessionId}/transcript`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chunks }),
  })
  if (!res.ok) throw new Error('Lỗi lưu transcript')
  return res.json()
}
export async function fetchTranscript(sessionId) {
  const res = await fetch(`${API_BASE}/consultations/${sessionId}/transcript`)
  if (!res.ok) throw new Error('Lỗi tải transcript')
  return res.json()
}
export async function uploadRawTranscript(sessionId, file) {
  const form = new FormData(); form.append('file', file)
  const res = await fetch(`${API_BASE}/consultations/${sessionId}/transcript/text`, { method: 'POST', body: form })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Lỗi upload') }
  return res.json()
}
export async function analyzeSession(sessionId, model = 'llama-3.3-70b-versatile') {
  const res = await fetch(`${API_BASE}/consultations/analyze`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, model }),
  })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Lỗi phân tích') }
  return res.json()
}
export async function importConsultationsCsv(file) {
  const form = new FormData(); form.append('file', file)
  const res = await fetch(`${API_BASE}/consultations/import/csv`, { method: 'POST', body: form })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Lỗi import') }
  return res.json()
}
export async function importConsultationsJson(file) {
  const form = new FormData(); form.append('file', file)
  const res = await fetch(`${API_BASE}/consultations/import/json`, { method: 'POST', body: form })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Lỗi import') }
  return res.json()
}
