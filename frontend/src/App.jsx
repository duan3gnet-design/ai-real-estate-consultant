import { useState } from 'react'
import { MessageSquare, Building2, ClipboardList } from 'lucide-react'
import TitleBar from './components/TitleBar'
import Sidebar from './components/Sidebar'
import MessageList from './components/MessageList'
import ChatInput from './components/ChatInput'
import PropertyManager from './components/PropertyManager'
import ConsultationManager from './components/ConsultationManager'
import { useChat } from './hooks/useChat'
import { useScrollToBottom, useBackendStatus } from './hooks/useUtils'

const TABS = [
  { id: 'chat',          label: 'Tư vấn AI',      icon: MessageSquare },
  { id: 'portfolio',     label: 'Danh mục BĐS',   icon: Building2 },
  { id: 'consultations', label: 'Lịch sử Tư vấn', icon: ClipboardList },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [model, setModel] = useState('llama-3.3-70b-versatile')
  const backendStatus = useBackendStatus()

  const {
    sessions, activeSessionId, messages, isStreaming,
    createSession, sendMessage, deleteSession, setActiveSessionId,
  } = useChat(model)

  const scrollRef = useScrollToBottom([messages, isStreaming])

  const statusLabel = {
    checking: 'Đang kết nối...',
    online: 'Backend sẵn sàng',
    error: 'Không kết nối được backend',
  }[backendStatus]

  return (
    <div className="app">
      <TitleBar />
      <div className="main-layout">
        {/* Sidebar — chỉ hiện ở tab chat */}
        {activeTab === 'chat' && (
          <Sidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            onNewChat={createSession}
            onSelectSession={setActiveSessionId}
            onDeleteSession={deleteSession}
            model={model}
            onModelChange={setModel}
          />
        )}

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Tab bar */}
          <div className="app-tabs">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                className={`app-tab ${activeTab === id ? 'active' : ''}`}
                onClick={() => setActiveTab(id)}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </div>

          {/* Chat */}
          {activeTab === 'chat' && (
            <div className="chat-area">
              <MessageList
                messages={messages}
                isStreaming={isStreaming}
                scrollRef={scrollRef}
                onSuggestion={sendMessage}
              />
              <div className="status-bar">
                <div className={`status-dot ${backendStatus}`} />
                <span>{statusLabel}</span>
                {backendStatus === 'online' && (
                  <span style={{ color: 'var(--slate-500)', marginLeft: 8 }}>
                    · RAG Hybrid Search (BĐS + Lịch sử tư vấn)
                  </span>
                )}
              </div>
              <ChatInput
                onSend={sendMessage}
                disabled={isStreaming || backendStatus === 'error'}
              />
            </div>
          )}

          {/* BĐS Manager */}
          {activeTab === 'portfolio' && (
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <PropertyManager />
            </div>
          )}

          {/* Consultation Manager */}
          {activeTab === 'consultations' && (
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <ConsultationManager />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
