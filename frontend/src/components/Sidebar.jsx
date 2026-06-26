import { MessageSquare, Plus, Trash2, Bot } from 'lucide-react'
import { clsx } from 'clsx'

const MODELS = [
  { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B' },
  { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B (Nhanh)' },
  { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B' },
  { id: 'gemma2-9b-it', name: 'Gemma 2 9B' },
]

function formatTime(date) {
  const d = new Date(date)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return 'Vừa xong'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} phút trước`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} giờ trước`
  return d.toLocaleDateString('vi-VN')
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  model,
  onModelChange,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          <Plus size={16} />
          Cuộc trò chuyện mới
        </button>
      </div>

      {sessions.length > 0 && (
        <div className="sidebar-section-title">Lịch sử</div>
      )}

      <div className="sessions-list">
        {sessions.map(session => (
          <div
            key={session.id}
            className={clsx('session-item', session.id === activeSessionId && 'active')}
            onClick={() => onSelectSession(session.id)}
          >
            <MessageSquare size={14} className="session-icon" />
            <div className="session-info">
              <div className="session-title">{session.title}</div>
              <div className="session-meta">{formatTime(session.createdAt)}</div>
            </div>
            <button
              style={{
                background: 'none', border: 'none', color: 'var(--slate-400)',
                cursor: 'pointer', padding: '2px', borderRadius: '4px',
                opacity: 0, transition: 'opacity 0.15s',
                display: 'flex', alignItems: 'center',
              }}
              className="session-delete"
              onClick={(e) => { e.stopPropagation(); onDeleteSession(session.id) }}
              title="Xóa"
              onMouseEnter={e => e.currentTarget.style.opacity = 1}
              onMouseLeave={e => e.currentTarget.style.opacity = 0}
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}

        {sessions.length === 0 && (
          <div style={{ padding: '20px 12px', textAlign: 'center', color: 'var(--slate-500)', fontSize: '12px' }}>
            Chưa có cuộc trò chuyện nào
          </div>
        )}
      </div>

      <div className="sidebar-footer">
        <div className="model-label">Model AI</div>
        <select
          className="model-selector"
          value={model}
          onChange={e => onModelChange(e.target.value)}
        >
          {MODELS.map(m => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>

        <div style={{
          marginTop: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          color: 'var(--slate-500)',
          fontSize: '11px',
        }}>
          <Bot size={12} />
          Powered by Groq API
        </div>
      </div>
    </aside>
  )
}
