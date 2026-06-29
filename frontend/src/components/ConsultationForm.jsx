import { useState, useEffect } from 'react'
import { X, Save, MessageSquare } from 'lucide-react'

const EMPTY = {
  ma_session: '', ten_kh: '', dien_thoai_kh: '', kenh_tiep_can: '', nguoi_tu_van: '',
  loai_nhu_cau: '', loai_bds_quan_tam: '', khu_vuc_quan_tam: '',
  ngan_sach_min: '', ngan_sach_max: '', dien_tich_yc: '', so_pn_yc: '',
  tieu_chi_khac: '', ket_qua: 'Chưa chốt', bds_chot_id: '', bds_da_gioi_thieu: '',
  ly_do_tu_choi: '', ghi_chu: '',
  thoi_gian_bat_dau: '', thoi_gian_ket_thuc: '', thoi_luong_phut: '',
}

const BDS_TYPES = ['Căn hộ chung cư','Nhà phố','Biệt thự','Đất nền','Shophouse','Văn phòng','Mặt bằng thương mại','Kho / Xưởng']

function Field({ label, required, children }) {
  return (
    <div className="pf-field">
      <label className="pf-label">{label}{required && <span className="pf-required">*</span>}</label>
      {children}
    </div>
  )
}

export default function ConsultationForm({ initial, onSave, onClose, saving, ketQuaOptions, loaiOptions, kenhOptions }) {
  const [form, setForm] = useState(initial ? { ...EMPTY, ...initial } : { ...EMPTY })
  const [tab, setTab] = useState('khach')

  useEffect(() => { setForm(initial ? { ...EMPTY, ...initial } : { ...EMPTY }) }, [initial])
  const set = k => v => setForm(p => ({ ...p, [k]: v }))

  const handleSave = () => {
    const clean = {}
    for (const [k, v] of Object.entries(form)) {
      clean[k] = (v === '' || v === null || v === undefined) ? null : v
    }
    onSave(clean)
  }

  const TABS = [
    { id: 'khach', label: 'Khách hàng' },
    { id: 'nhu_cau', label: 'Nhu cầu' },
    { id: 'ket_qua', label: 'Kết quả' },
    { id: 'thoi_gian', label: 'Thời gian' },
  ]

  const inp = (key, type = 'text', placeholder = '') => (
    <input className="pf-input" type={type} value={form[key] ?? ''} placeholder={placeholder}
      onChange={e => set(key)(e.target.value)} />
  )
  const sel = (key, options, placeholder) => (
    <select className="pf-select" value={form[key] ?? ''} onChange={e => set(key)(e.target.value)}>
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  )
  const tex = (key, placeholder, rows = 2) => (
    <textarea className="pf-textarea" value={form[key] ?? ''} placeholder={placeholder}
      rows={rows} onChange={e => set(key)(e.target.value)} />
  )

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="pf-modal">
        <div className="pf-header">
          <div className="pf-header-left">
            <MessageSquare size={18} style={{ color: 'var(--gold-500)' }} />
            <span className="pf-title">{initial?.id ? 'Chỉnh sửa buổi tư vấn' : 'Thêm buổi tư vấn'}</span>
          </div>
          <button className="pf-close" onClick={onClose}><X size={16} /></button>
        </div>
        <div className="pf-tabs">
          {TABS.map(t => (
            <button key={t.id} className={`pf-tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>
        <div className="pf-body">
          {tab === 'khach' && (
            <>
              <div className="pf-section-title"><span>👤</span>Thông tin khách hàng</div>
              <div className="pf-grid-2">
                <Field label="Mã session">{inp('ma_session', 'text', 'TV001')}</Field>
                <Field label="Họ tên khách">{inp('ten_kh', 'text', 'Nguyễn Văn A')}</Field>
              </div>
              <div className="pf-grid-2">
                <Field label="Số điện thoại">{inp('dien_thoai_kh', 'tel', '0901...')}</Field>
                <Field label="Kênh tiếp cận">{sel('kenh_tiep_can', kenhOptions, '— Chọn kênh —')}</Field>
              </div>
              <Field label="Tư vấn viên">{inp('nguoi_tu_van', 'text', 'Tên nhân viên')}</Field>
            </>
          )}
          {tab === 'nhu_cau' && (
            <>
              <div className="pf-section-title"><span>🎯</span>Nhu cầu khách hàng</div>
              <div className="pf-grid-2">
                <Field label="Loại nhu cầu">{sel('loai_nhu_cau', loaiOptions, '— Chọn —')}</Field>
                <Field label="Loại BĐS quan tâm">{sel('loai_bds_quan_tam', BDS_TYPES, '— Chọn —')}</Field>
              </div>
              <Field label="Khu vực quan tâm">{inp('khu_vuc_quan_tam', 'text', 'Quận 2, TP.HCM')}</Field>
              <div className="pf-grid-2">
                <Field label="Ngân sách từ (triệu)">{inp('ngan_sach_min', 'number', '2000')}</Field>
                <Field label="Ngân sách đến (triệu)">{inp('ngan_sach_max', 'number', '5000')}</Field>
              </div>
              <div className="pf-grid-2">
                <Field label="Yêu cầu diện tích">{inp('dien_tich_yc', 'text', 'Từ 60m²')}</Field>
                <Field label="Số phòng ngủ">{inp('so_pn_yc', 'number', '2')}</Field>
              </div>
              <Field label="Tiêu chí khác">{tex('tieu_chi_khac', 'Gần trường học, view đẹp, nội thất...')}</Field>
            </>
          )}
          {tab === 'ket_qua' && (
            <>
              <div className="pf-section-title"><span>📊</span>Kết quả tư vấn</div>
              <Field label="Kết quả" required>{sel('ket_qua', ketQuaOptions)}</Field>
              <div className="pf-grid-2">
                <Field label="ID BĐS đã chốt">{inp('bds_chot_id', 'number', 'ID BĐS')}</Field>
                <Field label="BĐS đã giới thiệu (IDs)">{inp('bds_da_gioi_thieu', 'text', '1,2,3')}</Field>
              </div>
              {(form.ket_qua === 'Từ chối' || form.ket_qua === 'Đang cân nhắc') && (
                <Field label="Lý do từ chối / băn khoăn">{tex('ly_do_tu_choi', 'Giá quá cao, vị trí không phù hợp...')}</Field>
              )}
              <Field label="Ghi chú">{tex('ghi_chu', 'Ghi chú thêm về buổi tư vấn...', 3)}</Field>
            </>
          )}
          {tab === 'thoi_gian' && (
            <>
              <div className="pf-section-title"><span>⏱️</span>Thời gian</div>
              <div className="pf-grid-2">
                <Field label="Bắt đầu">{inp('thoi_gian_bat_dau', 'datetime-local')}</Field>
                <Field label="Kết thúc">{inp('thoi_gian_ket_thuc', 'datetime-local')}</Field>
              </div>
              <Field label="Thời lượng (phút)">{inp('thoi_luong_phut', 'number', '30')}</Field>
            </>
          )}
        </div>
        <div className="pf-footer">
          <button className="btn-secondary" onClick={onClose}>Hủy</button>
          <button className="btn-primary pf-save-btn" onClick={handleSave} disabled={saving}>
            <Save size={14} />{saving ? 'Đang lưu...' : 'Lưu'}
          </button>
        </div>
      </div>
    </div>
  )
}
