import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const SUGGESTIONS = [
  { icon: '🏙️', text: 'Tư vấn mua căn hộ tại Hà Nội dưới 3 tỷ đồng' },
  { icon: '📈', text: 'Phân tích tiềm năng đầu tư đất nền vùng ven 2024' },
  { icon: '💰', text: 'Cách tính toán vay ngân hàng mua nhà hợp lý' },
  { icon: '⚖️', text: 'Những lưu ý pháp lý khi mua bán bất động sản' },
]

function WelcomeScreen({ onSuggestion }) {
  return (
    <div className="welcome">
      <div className="welcome-icon">🏠</div>
      <h1 className="welcome-title">
        Chào mừng đến với<br />
        <span>AI Tư Vấn BĐS</span>
      </h1>
      <p className="welcome-subtitle">
        Chuyên gia bất động sản AI với hơn 15 năm kinh nghiệm —
        tư vấn mua bán, đầu tư, pháp lý và tài chính BĐS tại Việt Nam.
      </p>
      <div className="suggestion-grid">
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            className="suggestion-card"
            onClick={() => onSuggestion(s.text)}
          >
            <span className="suggestion-icon">{s.icon}</span>
            <span className="suggestion-text">{s.text}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="message assistant" style={{ animation: 'fadeInUp 0.2s ease' }}>
      <div className="message-avatar">🏠</div>
      <div className="message-bubble">
        <div className="typing-indicator">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
      </div>
    </div>
  )
}

export default function MessageList({ messages, isStreaming, scrollRef, onSuggestion }) {
  if (messages.length === 0) {
    return (
      <div className="chat-area" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <WelcomeScreen onSuggestion={onSuggestion} />
      </div>
    )
  }

  const showTyping = isStreaming && messages[messages.length - 1]?.role !== 'assistant'

  return (
    <div className="messages-container" ref={scrollRef}>
      {messages.map((msg) => (
        <div key={msg.id} className={`message ${msg.role}`}>
          <div className="message-avatar">
            {msg.role === 'assistant' ? '🏠' : '👤'}
          </div>
          <div className="message-bubble">
            {msg.role === 'assistant' && msg.streaming && msg.content === '' ? (
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            ) : msg.role === 'assistant' ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content}
              </ReactMarkdown>
            ) : (
              <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
