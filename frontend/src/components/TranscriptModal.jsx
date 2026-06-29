import { useState, useEffect, useRef } from 'react'
import { X, Upload, Plus, Trash2 } from 'lucide-react'
import { fetchTranscript, saveTranscriptChunks, uploadRawTranscript } from '../services/api'

const SPEAKERS = [
  { value: 'consultant', label: 'Tư vấn viên' },
  { value: 'customer',   label: 'Khách hàng' },
  { value: 'unknown',    label: 'Không rõ' },
]

function ChunkRow({ chunk, index, onChange, onDelete }) {
  return (
    <div className="tc-chunk-row">
      <select
        className="tc-speaker-sel"
        value={chunk.speaker || 'unknown'}
        onChange={e => onChange(index, 'speaker', e.target.value)}
      >
        {SPEAKERS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
      </select>
      <textarea
        className="tc-content-inp"
        value={chunk.content || ''}
        rows={2}
        onChange={e => onChange(index, 'content', e.target.value)}
        placeholder="Nội dung đoạn thoại..."
      />
      <button className="pm-action-btn delete" onClick={() => onDelete(index)} title="Xóa dòng">
        <Trash2 size={12} />
      </button>
    </div>
  )
}

export default function TranscriptModal({ session, onClose }) {
  const [chunks, setChunks] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [msg, setMsg] = useState('')
  const fileRef = useRef()

  useEffect(() => {
    fetchTranscript(session.id)
      .then(data => setChunks(data.length > 0 ? data : [{ speaker: 'consultant', content: '' }]))
      .catch(() => setChunks([{ speaker: 'consultant', content: '' }]))
      .finally(() => setLoading(false))
  }, [session.id])

  const handleChange = (idx, key, val) => {
    setChunks(prev => prev.map((c, i) => i === idx ? { ...c, [key]: val } : c))
  }

  const handleDelete = (idx) => {
    setChunks(prev => prev.filter((_, i) => i !== idx))
  }

  const addChunk = () => {
    const lastSpeaker = chunks[chunks.length - 1]?.speaker || 'consultant'
    const nextSpeaker = lastSpeaker === 'consultant' ? 'customer' : 'consultant'
    setChunks(prev => [...prev, { speaker: nextSpeaker, content: '' }])
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const valid = chunks.filter(c => c.content?.trim())
      await saveTranscriptChunks(session.id, valid)
      setMsg(`✅ Đã lưu ${valid.length} đoạn transcript`)
    } catch (e) {
      setMsg('❌ Lỗi: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleUploadFile = async (file) => {
    if (!file) return
    setUploading(true); setMsg('')
    try {
      const result = await uploadRawTranscript(session.id, file)
      const fresh = await fetchTranscript(session.id)
      setChunks(fresh)
      setMsg(`✅ Đã import ${result.saved} đoạn từ file`)
    } catch (e) {
      setMsg('❌ ' + e.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="pf-modal" style={{ width: 740, maxHeight: '90vh' }}>
        <div className="pf-header">
          <div className="pf-header-left">
            <span style={{ fontSize: 16 }}>💬</span>
            <span className="pf-title">
              Transcript — {session.ten_kh || 'Ẩn danh'} ({session.created_at?.slice(0, 10)})
            </span>
          </div>
          <button className="pf-close" onClick={onClose}><X size={16} /></button>
        </div>

        {/* Toolbar */}
        <div style={{ padding: '10px 20px', borderBottom: '1px solid rgba(255,255,255,0.07)', display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: 12 }}
            onClick={() => fileRef.current?.click()} disabled={uploading}>
            <Upload size={12} /> {uploading ? 'Đang import...' : 'Upload file .txt'}
          </button>
          <input ref={fileRef} type="file" accept=".txt,.md" style={{ display: 'none' }}
            onChange={e => handleUploadFile(e.target.files[0])} />
          <span style={{ fontSize: 11, color: 'var(--slate-400)' }}>
            Hỗ trợ format: [TV]: nội dung / [KH]: nội dung
          </span>
          {msg && <span style={{ fontSize: 12, color: msg.startsWith('✅') ? '#22c55e' : '#ef4444', marginLeft: 'auto' }}>{msg}</span>}
        </div>

        {/* Chunks */}
        <div className="pf-body" style={{ gap: 0, padding: '12px 20px' }}>
          {loading && <div style={{ textAlign: 'center', color: 'var(--slate-400)', padding: 32 }}>Đang tải...</div>}
          {!loading && chunks.map((c, i) => (
            <ChunkRow key={i} chunk={c} index={i} onChange={handleChange} onDelete={handleDelete} />
          ))}
          {!loading && (
            <button
              onClick={addChunk}
              style={{ marginTop: 8, padding: '6px 14px', background: 'transparent', border: '1px dashed rgba(201,168,76,0.3)', borderRadius: 6, color: 'var(--gold-500)', cursor: 'pointer', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6, width: '100%', justifyContent: 'center' }}
            >
              <Plus size={13} /> Thêm đoạn thoại
            </button>
          )}
        </div>

        <div className="pf-footer">
          <span style={{ fontSize: 12, color: 'var(--slate-400)' }}>{chunks.length} đoạn</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn-secondary" onClick={onClose}>Đóng</button>
            <button className="btn-primary" onClick={handleSave} disabled={saving || loading}>
              {saving ? 'Đang lưu...' : 'Lưu transcript'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
