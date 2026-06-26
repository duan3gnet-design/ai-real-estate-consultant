import { useEffect, useRef, useCallback, useState } from 'react'

export function useAutoResize(value) {
  const ref = useRef(null)
  useEffect(() => {
    if (!ref.current) return
    ref.current.style.height = 'auto'
    ref.current.style.height = Math.min(ref.current.scrollHeight, 160) + 'px'
  }, [value])
  return ref
}

export function useScrollToBottom(deps) {
  const ref = useRef(null)
  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight
    }
  }, deps)
  return ref
}

export function useBackendStatus() {
  const [status, setStatus] = useState('checking') // checking | online | error

  useEffect(() => {
    let cancelled = false
    const check = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8765/health', { signal: AbortSignal.timeout(3000) })
        if (!cancelled) setStatus(res.ok ? 'online' : 'error')
      } catch {
        if (!cancelled) setStatus('error')
      }
    }
    check()
    const interval = setInterval(check, 10000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [])

  return status
}
