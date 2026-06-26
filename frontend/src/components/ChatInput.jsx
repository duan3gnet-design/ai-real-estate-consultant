import { useState, useCallback } from 'react'
import { Send, Mic } from 'lucide-react'
import { useAutoResize } from '../hooks/useUtils'

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const textareaRef = useAutoResize(value)

  const handleSend = useCallback(() => {
    if (!value.trim() || disabled) return
    onSend(value.trim())
    setValue('')
  }, [value, disabled, onSend])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  return (
    <div className="input-area">
      <div className="input-wrapper">
        <textarea
          ref={textareaRef}
          className="chat-input"
          placeholder="Hỏi về bất động sản... (Enter để gửi, Shift+Enter xuống dòng)"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={!value.trim() || disabled}
          title="Gửi (Enter)"
        >
          <Send size={15} />
        </button>
      </div>
      <div className="input-hint">
        AI có thể mắc sai sót — hãy xác minh thông tin quan trọng với chuyên gia
      </div>
    </div>
  )
}
