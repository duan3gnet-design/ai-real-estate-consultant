import { useState } from 'react'
import { X, Save, BookmarkPlus } from 'lucide-react'
import { createConsultation, saveTranscriptChunks } from '../services/api'

const KET_QUA_OPTIONS = ['Chưa chốt', 'Chốt giao dịch', 'Hẹn lại', 'Đang cân nhắc', 'Từ chối']
const LOAI_NHU_CAU = ['Mua', 'Thuê', 'Đầu tư', 'Bán', 'Tư vấn chung']
const KENH = ['AI Chatbot', 'Facebook', 'Zalo', 'Walk-in', 'Referral', 'Website', 'Điện thoại', 'Khác']

function Field({ label, required, children }) {
  return (
    <div className="pf-field">
      <label className="pf-label">{label}{required && <span className="pf-required">*</span>}</label>
      {children}
    </div>
  )
}

/**
 * Chuyển messages chat (role: user/assistant) thành transcript chunks
 * (speaker: customer/consultant) để lưu đồng nhất với format lịch sử tư vấn.
 */
function messagesToChunks(messages) {
  return messages
    .filter(m => m.content?.trim())
    .map(m => ({
      speaker: m.role === 'user' ? 'customer' : 'consultant',
      content: m.content.trim(),
    }))
}

export default function SaveToConsultationModal({ messages, onClose, onSaved }) {
  const [form, setForm] = useState({
    ten_kh: '',
    nguoi_tu_van: '',
    kenh_tiep_can: 'AI Chatbot',
    loai_nhu_cau: '',
    loai_bds_quan_tam: '',
    khu_vuc_quan_tam: '',
    ngan_sach_min: '',
    ngan_sach_max: '',
    ket_qua: 'Chưa chốt',
    ly_do_tu_choi: '',
    ghi_chu: 'Tự động lưu từ cuộc trò chuyện với AI tư vấn.',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const set = key => val => setForm(prev => ({ ...prev, [key]: val }))

  const chunkCount = messagesToChunks(messages).length

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const clean = {}
      for (const [k, v] of Object.entries(form)) {
        clean[k] = (v === '' || v === null) ? null : v
      }

      // 1. Tạo session với metadata
      const session = await createConsultation(clean)

      // 2. Lưu transcript từ messages chat
      const chunks = messagesToChunks(messages)
      if (chunks.length > 0) {
        await saveTranscriptChunks(session.id, chunks)
      }

      onSaved?.(session)
      onClose()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="pf-modal" style={{ width: 560 }}>
        <div className="pf-header">
          <div className="pf-header-left">
            <BookmarkPlus size={18} style={{ color: 'var(--gold-500)' }} />
            <span className="pf-title">Lưu vào Lịch sử Tư vấn</span>
          </div>
          <button className="pf-close" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="pf-body">
          <div className="import-template-bar" style={{ marginBottom: 4 }}>
            <span>Cuộc trò chuyện này sẽ được lưu thành 1 buổi tư vấn với {chunkCount} đoạn transcript.</span>
          </div>

          <div className="pf-section-title"><span>👤</span>Khách hàng</div>
          <div className="pf-grid-2">
            <Field label="Họ tên khách">
              <input className="pf-input" value={form.ten_kh} placeholder="Nguyễn Văn A (nếu biết)"
                onChange={e => set('ten_kh')(e.target.value)} />
            </Field>
            <Field label="Tư vấn viên">
              <input className="pf-input" value={form.nguoi_tu_van} placeholder="Tên nhân viên / AI"
                onChange={e => set('nguoi_tu_van')(e.target.value)} />
            </Field>
          </div>
          <Field label="Kênh tiếp cận">
            <select className="pf-select" value={form.kenh_tiep_can} onChange={e => set('kenh_tiep_can')(e.target.value)}>
              {KENH.map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </Field>

          <div className="pf-section-title"><span>🎯</span>Nhu cầu</div>
          <div className="pf-grid-2">
            <Field label="Loại nhu cầu">
              <select className="pf-select" value={form.loai_nhu_cau} onChange={e => set('loai_nhu_cau')(e.target.value)}>
                <option value="">— Chọn —</option>
                {LOAI_NHU_CAU.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </Field>
            <Field label="Loại BĐS quan tâm">
              <input className="pf-input" value={form.loai_bds_quan_tam} placeholder="Căn hộ, nhà phố..."
                onChange={e => set('loai_bds_quan_tam')(e.target.value)} />
            </Field>
          </div>
          <Field label="Khu vực quan tâm">
            <input className="pf-input" value={form.khu_vuc_quan_tam} placeholder="Quận 2, TP.HCM"
              onChange={e => set('khu_vuc_quan_tam')(e.target.value)} />
          </Field>
          <div className="pf-grid-2">
            <Field label="Ngân sách từ (triệu)">
              <input className="pf-input" type="number" value={form.ngan_sach_min}
                onChange={e => set('ngan_sach_min')(e.target.value)} />
            </Field>
            <Field label="Ngân sách đến (triệu)">
              <input className="pf-input" type="number" value={form.ngan_sach_max}
                onChange={e => set('ngan_sach_max')(e.target.value)} />
            </Field>
          </div>

          <div className="pf-section-title"><span>📊</span>Kết quả</div>
          <Field label="Kết quả">
            <select className="pf-select" value={form.ket_qua} onChange={e => set('ket_qua')(e.target.value)}>
              {KET_QUA_OPTIONS.map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </Field>
          {(form.ket_qua === 'Từ chối' || form.ket_qua === 'Đang cân nhắc') && (
            <Field label="Lý do từ chối / băn khoăn">
              <textarea className="pf-textarea" rows={2} value={form.ly_do_tu_choi}
                onChange={e => set('ly_do_tu_choi')(e.target.value)} />
            </Field>
          )}
          <Field label="Ghi chú">
            <textarea className="pf-textarea" rows={2} value={form.ghi_chu}
              onChange={e => set('ghi_chu')(e.target.value)} />
          </Field>

          {error && <div className="import-error-box" style={{ marginTop: 4 }}>⚠️ {error}</div>}
        </div>

        <div className="pf-footer">
          <button className="btn-secondary" onClick={onClose}>Hủy</button>
          <button className="btn-primary pf-save-btn" onClick={handleSave} disabled={saving || chunkCount === 0}>
            <Save size={14} />
            {saving ? 'Đang lưu...' : 'Lưu vào lịch sử'}
          </button>
        </div>
      </div>
    </div>
  )
}
