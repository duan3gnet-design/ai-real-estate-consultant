const API_BASE = 'http://127.0.0.1:8765'

// ─── Health ────────────────────────────────────────────────────────────────
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('Backend offline')
  return res.json()
}

// ─── Chat (SSE streaming) ───────────────────────────────────────────────────
export async function streamChat(messages, model, onChunk, onDone, filters = null) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, model, stream: true, use_portfolio: true, filters }),
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

// ─── Properties CRUD ────────────────────────────────────────────────────────
export async function fetchProperties(params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '' && v !== null) qs.append(k, v) })
  const res = await fetch(`${API_BASE}/properties?${qs}`)
  if (!res.ok) throw new Error('Lỗi tải danh sách BĐS')
  return res.json()
}

export async function fetchProperty(id) {
  const res = await fetch(`${API_BASE}/properties/${id}`)
  if (!res.ok) throw new Error('Không tìm thấy BĐS')
  return res.json()
}

export async function createProperty(data) {
  const res = await fetch(`${API_BASE}/properties`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Lỗi tạo BĐS')
  }
  return res.json()
}

export async function updateProperty(id, data) {
  const res = await fetch(`${API_BASE}/properties/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Lỗi cập nhật BĐS')
  }
  return res.json()
}

export async function deleteProperty(id) {
  const res = await fetch(`${API_BASE}/properties/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Lỗi xóa BĐS')
  return res.json()
}

export async function importJson(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/properties/import/json`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Lỗi import JSON')
  }
  return res.json()
}

export async function importCsv(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/properties/import/csv`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Lỗi import CSV')
  }
  return res.json()
}

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/properties/stats`)
  if (!res.ok) throw new Error('Lỗi tải thống kê')
  return res.json()
}
