const API_BASE = 'http://127.0.0.1:8765'

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('Backend offline')
  return res.json()
}

export async function getModels() {
  const res = await fetch(`${API_BASE}/models`)
  if (!res.ok) throw new Error('Cannot fetch models')
  return res.json()
}

/**
 * Stream chat từ backend
 * @param {Array} messages - [{role, content}]
 * @param {string} model
 * @param {function} onChunk - callback mỗi chunk text
 * @param {function} onDone - callback khi xong
 */
export async function streamChat(messages, model, onChunk, onDone) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, model, stream: true }),
  })

  if (!res.ok) {
    const err = await res.json()
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
        if (data.done) {
          onDone()
          return
        }
        if (data.content) onChunk(data.content)
      } catch {
        // ignore parse errors
      }
    }
  }
  onDone()
}
