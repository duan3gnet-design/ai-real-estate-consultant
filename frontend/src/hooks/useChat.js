import { useState, useCallback } from 'react'
import { streamChat } from '../services/api'

export function useChat(model) {
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [isStreaming, setIsStreaming] = useState(false)

  const activeSession = sessions.find(s => s.id === activeSessionId) ?? null
  const messages = activeSession?.messages ?? []

  const createSession = useCallback(() => {
    const id = Date.now().toString()
    setSessions(prev => [{
      id,
      title: 'Cuộc trò chuyện mới',
      messages: [],
      createdAt: new Date(),
    }, ...prev])
    setActiveSessionId(id)
    return id
  }, [])

  const sendMessage = useCallback(async (content) => {
    if (!content.trim() || isStreaming) return

    let sessionId = activeSessionId
    if (!sessionId) {
      sessionId = Date.now().toString()
      setSessions(prev => [{
        id: sessionId,
        title: content.slice(0, 40) + (content.length > 40 ? '...' : ''),
        messages: [],
        createdAt: new Date(),
      }, ...prev])
      setActiveSessionId(sessionId)
    }

    const userMsg = { role: 'user', content, id: Date.now() }

    setSessions(prev => prev.map(s =>
      s.id === sessionId ? {
        ...s,
        messages: [...s.messages, userMsg],
        title: s.messages.length === 0
          ? content.slice(0, 40) + (content.length > 40 ? '...' : '')
          : s.title,
      } : s
    ))

    const assistantMsgId = Date.now() + 1

    setSessions(prev => prev.map(s =>
      s.id === sessionId
        ? { ...s, messages: [...s.messages, { role: 'assistant', content: '', id: assistantMsgId, streaming: true }] }
        : s
    ))

    setIsStreaming(true)

    try {
      const historyMessages = sessions.find(s => s.id === sessionId)?.messages ?? []
      const allMessages = [...historyMessages, userMsg].map(({ role, content }) => ({ role, content }))

      await streamChat(allMessages, model,
        // onChunk
        (chunk) => {
          setSessions(prev => prev.map(s =>
            s.id === sessionId ? {
              ...s,
              messages: s.messages.map(m =>
                m.id === assistantMsgId ? { ...m, content: m.content + chunk } : m
              ),
            } : s
          ))
        },
        // onDone
        () => {
          setSessions(prev => prev.map(s =>
            s.id === sessionId ? {
              ...s,
              messages: s.messages.map(m =>
                m.id === assistantMsgId ? { ...m, streaming: false } : m
              ),
            } : s
          ))
          setIsStreaming(false)
        },
        // options — bật consultation RAG
        { useConsultations: true },
      )
    } catch (err) {
      setSessions(prev => prev.map(s =>
        s.id === sessionId ? {
          ...s,
          messages: s.messages.map(m =>
            m.id === assistantMsgId
              ? { ...m, content: `❌ Lỗi: ${err.message}`, streaming: false }
              : m
          ),
        } : s
      ))
      setIsStreaming(false)
    }
  }, [activeSessionId, sessions, isStreaming, model])

  const deleteSession = useCallback((id) => {
    setSessions(prev => prev.filter(s => s.id !== id))
    if (activeSessionId === id) setActiveSessionId(null)
  }, [activeSessionId])

  return {
    sessions, activeSession, activeSessionId, messages, isStreaming,
    createSession, sendMessage, deleteSession, setActiveSessionId,
  }
}
