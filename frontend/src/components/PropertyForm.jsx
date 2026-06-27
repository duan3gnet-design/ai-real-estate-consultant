import { useState, useEffect } from 'react'
import { X, Save, Building } from 'lucide-react'
import { PROPERTY_TYPES, PROPERTY_STATUSES, LEGAL_STATUSES, DIRECTIONS } from '../constants'

const EMPTY = {
  ma_bds: '', ten: '', loai: 'Căn hộ chung cư', trang_thai: 'Đang bán',
  dia_chi: '', phuong_xa: '', quan_huyen: '', tinh_thanh: '',
  vi_do: '', kinh_do: '',
  dien_tich_dat: '', dien_tich_san: '', so_tang: '', so_phong_ngu: '', so_toilet: '',
  huong: '', mat_tien: '', duong_vao: '',
  gia_ban: '', gia_thue: '', gia_mua_vao: '', nam_mua: '', phi_quan_ly: '',
  phap_ly: '', nam_xay_dung: '', quy_hoach: '',
  tien_ich: '', mo_ta: '', ghi_chu_noi_bo: '',
  nguoi_phu_trach: '', so_dien_thoai: '', anh_urls: '',
}

function Field({ label, required, children }) {
  return (
    <div className="pf-field">
      <label className="pf-label">{label}{required && <span className="pf-required">*</span>}</label>
      {children}
    </div>
  )
}

function Input({ value, onChange, type = 'text', placeholder, ...rest }) {
  return (
    <input
      className="pf-input"
      type={type}
      value={value ?? ''}
      placeholder={placeholder}
      onChange={e => onChange(e.target.value)}
      {...rest}
    />
  )
}

function Select({ value, onChange, options, placeholder }) {
  return (
    <select className="pf-select" value={value ?? ''} onChange={e => onChange(e.target.value)}>
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  )
}

function Textarea({ value, onChange, placeholder, rows = 3 }) {
  return (
    <textarea
      className="pf-textarea"
      value={value ?? ''}
      placeholder={placeholder}
      rows={rows}
      onChange={e => onChange(e.target.value)}
    />
  )
}

function SectionTitle({ icon, title }) {
  return (
    <div className="pf-section-title">
      <span>{icon}</span>
      {title}
    </div>
  )
}

export default function PropertyForm({ initial = null, onSave, onClose, saving }) {
  const [form, setForm] = useState(initial ? { ...EMPTY, ...initial } : { ...EMPTY })
  const [tab, setTab] = useState('basic')

  useEffect(() => {
    setForm(initial ? { ...EMPTY, ...initial } : { ...EMPTY })
  }, [initial])

  const set = (key) => (val) => setForm(prev => ({ ...prev, [key]: val }))

  const handleSave = () => {
    if (!form.ten?.trim()) return alert('Vui lòng nhập tên BĐS')
    if (!form.dia_chi?.trim()) return alert('Vui lòng nhập địa chỉ')
    if (!form.tinh_thanh?.trim()) return alert('Vui lòng nhập tỉnh/thành phố')
    // Làm sạch số rỗng
    const clean = {}
    for (const [k, v] of Object.entries(form)) {
      if (v === '' || v === null || v === undefined) clean[k] = null
      else clean[k] = v
    }
    onSave(clean)
  }

  const TABS = [
    { id: 'basic',    label: 'Cơ bản' },
    { id: 'detail',   label: 'Chi tiết' },
    { id: 'finance',  label: 'Tài chính' },
    { id: 'legal',    label: 'Pháp lý & Mô tả' },
    { id: 'contact',  label: 'Liên hệ' },
  ]

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="pf-modal">
        {/* Header */}
        <div className="pf-header">
          <div className="pf-header-left">
            <Building size={18} style={{ color: 'var(--gold-500)' }} />
            <span className="pf-title">{initial?.id ? 'Chỉnh sửa BĐS' : 'Thêm BĐS mới'}</span>
          </div>
          <button className="pf-close" onClick={onClose}><X size={16} /></button>
        </div>

        {/* Tabs */}
        <div className="pf-tabs">
          {TABS.map(t => (
            <button
              key={t.id}
              className={`pf-tab ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
            >{t.label}</button>
          ))}
        </div>

        {/* Body */}
        <div className="pf-body">

          {tab === 'basic' && (
            <>
              <SectionTitle icon="📋" title="Thông tin cơ bản" />
              <div className="pf-grid-2">
                <Field label="Mã BĐS"><Input value={form.ma_bds} onChange={set('ma_bds')} placeholder="BDS001" /></Field>
                <Field label="Tên BĐS" required><Input value={form.ten} onChange={set('ten')} placeholder="Căn hộ Vinhomes..." /></Field>
              </div>
              <div className="pf-grid-2">
                <Field label="Loại BĐS" required><Select value={form.loai} onChange={set('loai')} options={PROPERTY_TYPES} /></Field>
                <Field label="Trạng thái"><Select value={form.trang_thai} onChange={set('trang_thai')} options={PROPERTY_STATUSES} /></Field>
              </div>

              <SectionTitle icon="📍" title="Vị trí" />
              <Field label="Địa chỉ" required><Input value={form.dia_chi} onChange={set('dia_chi')} placeholder="Số nhà, tên đường..." /></Field>
              <div className="pf-grid-3">
                <Field label="Phường/Xã"><Input value={form.phuong_xa} onChange={set('phuong_xa')} placeholder="Phường 1" /></Field>
                <Field label="Quận/Huyện"><Input value={form.quan_huyen} onChange={set('quan_huyen')} placeholder="Quận 1" /></Field>
                <Field label="Tỉnh/TP" required><Input value={form.tinh_thanh} onChange={set('tinh_thanh')} placeholder="TP. Hồ Chí Minh" /></Field>
              </div>
              <div className="pf-grid-2">
                <Field label="Vĩ độ (Lat)"><Input type="number" value={form.vi_do} onChange={set('vi_do')} placeholder="10.762622" /></Field>
                <Field label="Kinh độ (Lng)"><Input type="number" value={form.kinh_do} onChange={set('kinh_do')} placeholder="106.660172" /></Field>
              </div>
            </>
          )}

          {tab === 'detail' && (
            <>
              <SectionTitle icon="📐" title="Thông số diện tích" />
              <div className="pf-grid-2">
                <Field label="Diện tích đất (m²)"><Input type="number" value={form.dien_tich_dat} onChange={set('dien_tich_dat')} placeholder="100" /></Field>
                <Field label="Diện tích sàn/SD (m²)"><Input type="number" value={form.dien_tich_san} onChange={set('dien_tich_san')} placeholder="80" /></Field>
              </div>
              <div className="pf-grid-3">
                <Field label="Số tầng"><Input type="number" value={form.so_tang} onChange={set('so_tang')} placeholder="3" /></Field>
                <Field label="Số phòng ngủ"><Input type="number" value={form.so_phong_ngu} onChange={set('so_phong_ngu')} placeholder="2" /></Field>
                <Field label="Số toilet"><Input type="number" value={form.so_toilet} onChange={set('so_toilet')} placeholder="2" /></Field>
              </div>
              <div className="pf-grid-3">
                <Field label="Hướng"><Select value={form.huong} onChange={set('huong')} options={DIRECTIONS} placeholder="— Chọn hướng —" /></Field>
                <Field label="Mặt tiền (m)"><Input type="number" value={form.mat_tien} onChange={set('mat_tien')} placeholder="5" /></Field>
                <Field label="Đường vào (m)"><Input type="number" value={form.duong_vao} onChange={set('duong_vao')} placeholder="6" /></Field>
              </div>

              <SectionTitle icon="🏗️" title="Xây dựng" />
              <div className="pf-grid-2">
                <Field label="Năm xây dựng"><Input type="number" value={form.nam_xay_dung} onChange={set('nam_xay_dung')} placeholder="2020" /></Field>
                <Field label="Quy hoạch"><Input value={form.quy_hoach} onChange={set('quy_hoach')} placeholder="Đất ở đô thị" /></Field>
              </div>
            </>
          )}

          {tab === 'finance' && (
            <>
              <SectionTitle icon="💰" title="Giá bán / cho thuê" />
              <div className="pf-grid-2">
                <Field label="Giá bán (triệu VNĐ)"><Input type="number" value={form.gia_ban} onChange={set('gia_ban')} placeholder="3500" /></Field>
                <Field label="Giá thuê (triệu/tháng)"><Input type="number" value={form.gia_thue} onChange={set('gia_thue')} placeholder="15" /></Field>
              </div>
              <Field label="Phí quản lý (triệu/tháng)"><Input type="number" value={form.phi_quan_ly} onChange={set('phi_quan_ly')} placeholder="3" /></Field>

              <SectionTitle icon="📊" title="Lịch sử đầu tư (nội bộ)" />
              <div className="pf-grid-2">
                <Field label="Giá mua vào (triệu VNĐ)"><Input type="number" value={form.gia_mua_vao} onChange={set('gia_mua_vao')} placeholder="3000" /></Field>
                <Field label="Năm mua"><Input type="number" value={form.nam_mua} onChange={set('nam_mua')} placeholder="2021" /></Field>
              </div>
              {form.gia_ban && form.gia_mua_vao && (
                <div className="pf-profit-box">
                  <span>Lợi nhuận ước tính:</span>
                  <strong style={{ color: (+form.gia_ban - +form.gia_mua_vao) >= 0 ? 'var(--green-500)' : 'var(--red-500)' }}>
                    {(+form.gia_ban - +form.gia_mua_vao) >= 0 ? '+' : ''}
                    {(+form.gia_ban - +form.gia_mua_vao).toLocaleString('vi-VN')} triệu
                    ({form.gia_mua_vao > 0 ? (((+form.gia_ban - +form.gia_mua_vao) / +form.gia_mua_vao * 100).toFixed(1)) : 0}%)
                  </strong>
                </div>
              )}
            </>
          )}

          {tab === 'legal' && (
            <>
              <SectionTitle icon="⚖️" title="Pháp lý" />
              <Field label="Tình trạng pháp lý"><Select value={form.phap_ly} onChange={set('phap_ly')} options={LEGAL_STATUSES} placeholder="— Chọn tình trạng —" /></Field>

              <SectionTitle icon="📝" title="Mô tả & Tiện ích" />
              <Field label="Tiện ích xung quanh">
                <Textarea value={form.tien_ich} onChange={set('tien_ich')} placeholder="Gần trường học, bệnh viện, siêu thị, hồ bơi..." rows={2} />
              </Field>
              <Field label="Mô tả chi tiết">
                <Textarea value={form.mo_ta} onChange={set('mo_ta')} placeholder="Mô tả tổng quan về bất động sản..." rows={4} />
              </Field>
              <Field label="Ghi chú nội bộ">
                <Textarea value={form.ghi_chu_noi_bo} onChange={set('ghi_chu_noi_bo')} placeholder="Chỉ dùng nội bộ, không hiển thị cho khách..." rows={2} />
              </Field>
              <Field label="URLs ảnh (phân cách bằng dấu phẩy)">
                <Textarea value={form.anh_urls} onChange={set('anh_urls')} placeholder="https://..., https://..." rows={2} />
              </Field>
            </>
          )}

          {tab === 'contact' && (
            <>
              <SectionTitle icon="👤" title="Người phụ trách" />
              <div className="pf-grid-2">
                <Field label="Họ tên"><Input value={form.nguoi_phu_trach} onChange={set('nguoi_phu_trach')} placeholder="Nguyễn Văn A" /></Field>
                <Field label="Số điện thoại"><Input value={form.so_dien_thoai} onChange={set('so_dien_thoai')} placeholder="0901234567" /></Field>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="pf-footer">
          <button className="btn-secondary" onClick={onClose}>Hủy</button>
          <button className="btn-primary pf-save-btn" onClick={handleSave} disabled={saving}>
            <Save size={14} />
            {saving ? 'Đang lưu...' : 'Lưu BĐS'}
          </button>
        </div>
      </div>
    </div>
  )
}
