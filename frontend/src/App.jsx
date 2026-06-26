import { useState } from 'react'
import TitleBar from './components/TitleBar'
import Sidebar from './components/Sidebar'
import MessageList from './components/MessageList'
import ChatInput from './components/ChatInput'
import { useChat } from './hooks/useChat'
import { useScrollToBottom, useBackendStatus } from './hooks/useUtils'

export default function App() {
  const [model, setModel] = useState('llama-3.3-70b-versatile')
  const backendStatus = useBackendStatus()

  const {
    sessions,
    activeSessionId,
    messages,
    isStreaming,
    createSession,
    sendMessage,
    deleteSession,
    setActiveSessionId,
  } = useChat(model)

  const scrollRef = useScrollToBottom([messages, isStreaming])

  const statusLabel = {
    checking: 'Đang kết nối...',
    online: 'Backend đang chạy',
    error: 'Không kết nối được backend',
  }[backendStatus]

  return (
    <div className="app">
      <TitleBar />
      <div className="main-layout">
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onNewChat={createSession}
          onSelectSession={setActiveSessionId}
          onDeleteSession={deleteSession}
          model={model}
          onModelChange={setModel}
        />
        <div className="chat-area">
          <MessageList
            messages={messages}
            isStreaming={isStreaming}
            scrollRef={scrollRef}
            onSuggestion={(text) => sendMessage(text)}
          />
          <div className="status-bar">
            <div className={`status-dot ${backendStatus}`} />
            <span>{statusLabel}</span>
          </div>
          <ChatInput
            onSend={sendMessage}
            disabled={isStreaming || backendStatus === 'error'}
          />
        </div>
      </div>
    </div>
  )
}
