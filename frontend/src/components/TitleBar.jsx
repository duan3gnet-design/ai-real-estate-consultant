import { Minus, Square, X } from 'lucide-react'

export default function TitleBar() {
  const isElectron = !!window.electronAPI

  if (!isElectron) return null

  return (
    <div className="titlebar">
      <div className="titlebar-brand">
        <div className="titlebar-logo">🏠</div>
        <span className="titlebar-title">AI Tư Vấn Bất Động Sản</span>
      </div>
      <div className="titlebar-controls">
        <button className="titlebar-btn" onClick={() => window.electronAPI.minimize()} title="Thu nhỏ">
          <Minus size={12} />
        </button>
        <button className="titlebar-btn" onClick={() => window.electronAPI.maximize()} title="Phóng to">
          <Square size={11} />
        </button>
        <button className="titlebar-btn close" onClick={() => window.electronAPI.close()} title="Đóng">
          <X size={13} />
        </button>
      </div>
    </div>
  )
}
