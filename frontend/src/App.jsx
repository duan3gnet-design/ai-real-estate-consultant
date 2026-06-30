import { useState } from 'react'
import { MessageSquare, Building2, ClipboardList, BookmarkPlus, CheckCircle2 } from 'lucide-react'
import TitleBar from './components/TitleBar'
import Sidebar from './components/Sidebar'
import MessageList from './components/MessageList'
import ChatInput from './components/ChatInput'
import PropertyManager from './components/PropertyManager'
import ConsultationManager from './components/ConsultationManager'
import SaveToConsultationModal from './components/SaveToConsultationModal'
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

  const [showSaveModal, setShowSaveModal] = useState(false)
  const [justSaved, setJustSaved] = useState(false)

  const statusLabel = {
    checking: 'Đang kết nối...',
    online: 'Backend sẵn sàng',
    error: 'Không kết nối được backend',
  }[backendStatus]

  const handleSaved = () => {
    setJustSaved(true)
    setTimeout(() => setJustSaved(false), 3000)
  }

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

                {/* Nút lưu cuộc chat hiện tại vào Lịch sử Tư vấn */}
                {messages.length > 0 && (
                  <button
                    onClick={() => setShowSaveModal(true)}
                    disabled={justSaved}
                    style={{
                      marginLeft: 'auto',
                      display: 'flex', alignItems: 'center', gap: 6,
                      padding: '5px 12px',
                      background: justSaved ? 'rgba(34,197,94,0.15)' : 'rgba(201,168,76,0.1)',
                      border: `1px solid ${justSaved ? 'rgba(34,197,94,0.3)' : 'rgba(201,168,76,0.25)'}`,
                      borderRadius: 20,
                      color: justSaved ? 'var(--green-500)' : 'var(--gold-400)',
                      fontSize: 11, fontWeight: 600,
                      cursor: justSaved ? 'default' : 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    {justSaved ? (
                      <><CheckCircle2 size={13} /> Đã lưu vào lịch sử</>
                    ) : (
                      <><BookmarkPlus size={13} /> Lưu vào lịch sử tư vấn</>
                    )}
                  </button>
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

      {showSaveModal && (
        <SaveToConsultationModal
          messages={messages}
          onClose={() => setShowSaveModal(false)}
          onSaved={handleSaved}
        />
      )}
    </div>
  )
}
