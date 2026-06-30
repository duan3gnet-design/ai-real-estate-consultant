import { useState, useEffect, useCallback } from 'react'
import {
  Plus, Upload, RefreshCw, Edit2, Trash2, ChevronLeft, ChevronRight,
  FileText, Star, TrendingUp, Users, CheckCircle, XCircle, Clock,
  BarChart2, Brain, Download,
} from 'lucide-react'
import {
  fetchConsultations, fetchConsultationStats, createConsultation,
  updateConsultation, deleteConsultation, analyzeSession,
  importConsultationsCsv, importConsultationsJson,
  fetchTranscript, uploadRawTranscript,
} from '../services/api'
import ConsultationForm from './ConsultationForm'
import TranscriptModal from './TranscriptModal'
import AnalysisModal from './AnalysisModal'
import ImportModal from './ImportModal'

// ─── Constants ────────────────────────────────────────────────────────────────
const KET_QUA_COLORS = {
  'Chốt giao dịch': { bg: 'rgba(34,197,94,0.15)',  text: '#22c55e' },
  'Hẹn lại':         { bg: 'rgba(59,130,246,0.15)', text: '#3b82f6' },
  'Đang cân nhắc':   { bg: 'rgba(168,85,247,0.15)', text: '#a855f7' },
  'Từ chối':          { bg: 'rgba(239,68,68,0.15)',  text: '#ef4444' },
  'Chưa chốt':        { bg: 'rgba(100,116,139,0.15)',text: '#64748b' },
}
const KET_QUA_OPTIONS = ['Chưa chốt', 'Chốt giao dịch', 'Hẹn lại', 'Đang cân nhắc', 'Từ chối']
const LOAI_NHU_CAU = ['Mua', 'Thuê', 'Đầu tư', 'Bán', 'Tư vấn chung']
const KENH = ['Facebook', 'Zalo', 'Walk-in', 'Referral', 'Website', 'Điện thoại', 'Email', 'Khác']

function Badge({ label, type }) {
  const c = KET_QUA_COLORS[label] || { bg: 'rgba(100,116,139,0.15)', text: '#64748b' }
  return (
    <span style={{ background: c.bg, color: c.text, padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap' }}>
      {label}
    </span>
  )
}

function ScoreBadge({ score }) {
  if (!score) return <span style={{ color: 'var(--slate-500)', fontSize: 12 }}>—</span>
  const color = score >= 8 ? '#22c55e' : score >= 6 ? '#f59e0b' : '#ef4444'
  return (
    <span style={{ color, fontWeight: 700, fontSize: 14, display: 'flex', alignItems: 'center', gap: 3 }}>
      <Star size={12} fill={color} stroke={color} />
      {score.toFixed(1)}
    </span>
  )
}

// ─── Stats Bar ────────────────────────────────────────────────────────────────
function StatsBar({ stats }) {
  if (!stats) return null
  return (
    <div className="pm-stats">
      <div className="pm-stat-card">
        <Users size={16} style={{ color: 'var(--gold-500)' }} />
        <div><div className="pm-stat-val">{stats.total?.toLocaleString('vi-VN')}</div><div className="pm-stat-label">Tổng buổi TV</div></div>
      </div>
      <div className="pm-stat-card">
        <CheckCircle size={16} style={{ color: '#22c55e' }} />
        <div><div className="pm-stat-val" style={{ color: '#22c55e' }}>{stats.ti_le_chot}%</div><div className="pm-stat-label">Tỷ lệ chốt</div></div>
      </div>
      <div className="pm-stat-card">
        <Clock size={16} style={{ color: '#3b82f6' }} />
        <div><div className="pm-stat-val">{stats.avg_duration_phut} ph</div><div className="pm-stat-label">Thời lượng TB</div></div>
      </div>
      <div className="pm-stat-card">
        <Star size={16} style={{ color: '#f59e0b' }} />
        <div><div className="pm-stat-val">{stats.avg_diem_chat_luong || '—'}</div><div className="pm-stat-label">Điểm CL TB</div></div>
      </div>
    </div>
  )
}

// ─── Session Row ──────────────────────────────────────────────────────────────
function SessionRow({ s, onEdit, onDelete, onViewTranscript, onAnalyze }) {
  const [analyzing, setAnalyzing] = useState(false)

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try { await onAnalyze(s.id) }
    finally { setAnalyzing(false) }
  }

  return (
    <tr className="pm-row">
      <td className="pm-td" style={{ minWidth: 200 }}>
        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--slate-100)' }}>
          {s.ten_kh || 'Ẩn danh'}
        </div>
        <div style={{ fontSize: 11, color: 'var(--slate-400)', marginTop: 2 }}>
          {s.nguoi_tu_van || '—'} · {s.kenh_tiep_can || '—'}
        </div>
        {s.ma_session && <div style={{ fontSize: 10, color: 'var(--gold-500)', marginTop: 2 }}>#{s.ma_session}</div>}
      </td>
      <td className="pm-td">
        <div style={{ fontSize: 12, color: 'var(--slate-200)' }}>{s.loai_nhu_cau || '—'}</div>
        <div style={{ fontSize: 11, color: 'var(--slate-400)', marginTop: 2 }}>{s.loai_bds_quan_tam || ''}</div>
        {s.khu_vuc_quan_tam && <div style={{ fontSize: 11, color: 'var(--slate-500)' }}>{s.khu_vuc_quan_tam}</div>}
      </td>
      <td className="pm-td" style={{ textAlign: 'right' }}>
        {(s.ngan_sach_min || s.ngan_sach_max) ? (
          <div style={{ fontSize: 12, color: 'var(--gold-400)', fontWeight: 600 }}>
            {s.ngan_sach_min ? `${(+s.ngan_sach_min).toLocaleString('vi-VN')}` : '0'}
            {' – '}
            {s.ngan_sach_max ? `${(+s.ngan_sach_max).toLocaleString('vi-VN')} tr` : '?'}
          </div>
        ) : <span style={{ color: 'var(--slate-500)', fontSize: 12 }}>—</span>}
        {s.thoi_luong_phut && <div style={{ fontSize: 11, color: 'var(--slate-500)', marginTop: 2 }}>{s.thoi_luong_phut} ph</div>}
      </td>
      <td className="pm-td"><Badge label={s.ket_qua || 'Chưa chốt'} /></td>
      <td className="pm-td"><ScoreBadge score={s.diem_chat_luong} /></td>
      <td className="pm-td" style={{ fontSize: 11, color: 'var(--slate-400)' }}>
        {s.created_at ? new Date(s.created_at).toLocaleDateString('vi-VN') : '—'}
      </td>
      <td className="pm-td pm-td-actions">
        <button className="pm-action-btn edit" onClick={() => onViewTranscript(s)} title="Xem transcript">
          <FileText size={13} />
        </button>
        <button
          className="pm-action-btn edit"
          onClick={handleAnalyze}
          disabled={analyzing}
          title="AI phân tích"
          style={{ color: analyzing ? 'var(--gold-500)' : undefined }}
        >
          <Brain size={13} />
        </button>
        <button className="pm-action-btn edit" onClick={() => onEdit(s)} title="Chỉnh sửa"><Edit2 size={13} /></button>
        <button className="pm-action-btn delete" onClick={() => onDelete(s)} title="Xóa"><Trash2 size={13} /></button>
      </td>
    </tr>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function ConsultationManager() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [filters, setFiltersState] = useState({
    page: 1, page_size: 20, ket_qua: '', nguoi_tu_van: '',
    loai_nhu_cau: '', khu_vuc: '', tu_ngay: '', den_ngay: '',
    sort_by: 'created_at', sort_dir: 'desc',
  })

  const [showForm, setShowForm] = useState(false)
  const [editTarget, setEditTarget] = useState(null)
  const [showImport, setShowImport] = useState(false)
  const [transcriptTarget, setTranscriptTarget] = useState(null)
  const [analysisData, setAnalysisData] = useState(null)
  const [analysisSession, setAnalysisSession] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async (overrides = {}) => {
    setLoading(true); setError(null)
    try {
      const params = { ...filters, ...overrides }
      const data = await fetchConsultations(params)
      setItems(data.items); setTotal(data.total); setTotalPages(data.total_pages)
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }, [filters])

  const loadStats = useCallback(async () => {
    try { setStats(await fetchConsultationStats()) } catch { /* silent */ }
  }, [])

  useEffect(() => { load() }, [filters])
  useEffect(() => { loadStats() }, [])

  const setFilter = (key, value) =>
    setFiltersState(prev => ({ ...prev, [key]: value, page: key === 'page' ? value : 1 }))

  const resetFilters = () =>
    setFiltersState(prev => ({
      ...prev, ket_qua: '', nguoi_tu_van: '', loai_nhu_cau: '', khu_vuc: '',
      tu_ngay: '', den_ngay: '', page: 1,
    }))

  const handleSave = async (data) => {
    setSaving(true)
    try {
      if (editTarget?.id) await updateConsultation(editTarget.id, data)
      else await createConsultation(data)
      setShowForm(false); setEditTarget(null)
      await load(); await loadStats()
    } catch (e) { alert('Lỗi: ' + e.message) }
    finally { setSaving(false) }
  }

  const handleDelete = async (s) => {
    if (!confirm(`Xóa buổi tư vấn của "${s.ten_kh || 'Ẩn danh'}"?`)) return
    try { await deleteConsultation(s.id); await load(); await loadStats() }
    catch (e) { alert('Lỗi: ' + e.message) }
  }

  const handleAnalyze = async (sessionId) => {
    const session = items.find(s => s.id === sessionId)
    try {
      const result = await analyzeSession(sessionId)
      if (result.error) { alert('AI lỗi: ' + result.error); return }
      setAnalysisData(result)
      setAnalysisSession(session)
      await load()
    } catch (e) { alert('Lỗi phân tích: ' + e.message) }
  }

  const handleImport = async (file) => {
    const isJson = file.name.endsWith('.json')
    const result = isJson ? await importConsultationsJson(file) : await importConsultationsCsv(file)
    await load(); await loadStats()
    return result
  }

  const downloadTemplate = () => {
    const csv = `ma_session,ten_kh,dien_thoai_kh,kenh_tiep_can,nguoi_tu_van,loai_nhu_cau,loai_bds_quan_tam,khu_vuc_quan_tam,ngan_sach_min,ngan_sach_max,tieu_chi_khac,ket_qua,ly_do_tu_choi,ghi_chu,thoi_gian_bat_dau,thoi_luong_phut
TV001,Nguyễn Văn A,0901234567,Zalo,Trần Thị B,Mua,Căn hộ chung cư,Quận 2 TP.HCM,3000,5000,Gần trường học,Chốt giao dịch,,Khách hài lòng với Vinhomes,2024-01-15 09:00:00,45
TV002,Lê Thị C,0912345678,Facebook,Nguyễn Văn D,Đầu tư,Đất nền,Nhơn Trạch Đồng Nai,500,1000,Gần KCN,Từ chối,Giá quá cao,Cần tư vấn thêm về pháp lý,2024-01-16 14:00:00,30`
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'template_tu_van.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="pm-root">
      {/* Header */}
      <div className="pm-header">
        <div>
          <h1 className="pm-title">Lịch sử Tư vấn</h1>
          <p className="pm-subtitle">Quản lý buổi tư vấn · AI phân tích chất lượng · RAG nâng cao</p>
        </div>
        <div className="pm-header-actions">
          <button className="btn-secondary pm-btn" onClick={downloadTemplate} title="Tải template CSV">
            <Download size={14} /> Template
          </button>
          <button className="btn-secondary pm-btn" onClick={() => setShowImport(true)}>
            <Upload size={14} /> Import
          </button>
          <button className="btn-primary pm-btn" onClick={() => { setEditTarget(null); setShowForm(true) }}>
            <Plus size={14} /> Thêm buổi TV
          </button>
        </div>
      </div>

      <StatsBar stats={stats} />

      {/* Filter bar */}
      <div className="pm-filterbar" style={{ paddingBottom: 8 }}>
        <div className="pm-filterbar-row1" style={{ flexWrap: 'wrap', gap: 8 }}>
          <select className="pm-filter-select" value={filters.ket_qua} onChange={e => setFilter('ket_qua', e.target.value)}>
            <option value="">Tất cả kết quả</option>
            {KET_QUA_OPTIONS.map(k => <option key={k} value={k}>{k}</option>)}
          </select>
          <select className="pm-filter-select" value={filters.loai_nhu_cau} onChange={e => setFilter('loai_nhu_cau', e.target.value)}>
            <option value="">Tất cả nhu cầu</option>
            {LOAI_NHU_CAU.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
          <input className="pm-filter-input" placeholder="Khu vực" value={filters.khu_vuc} onChange={e => setFilter('khu_vuc', e.target.value)} />
          <input className="pm-filter-input" placeholder="Tư vấn viên" value={filters.nguoi_tu_van} onChange={e => setFilter('nguoi_tu_van', e.target.value)} />
          <input className="pm-filter-input" type="date" value={filters.tu_ngay} onChange={e => setFilter('tu_ngay', e.target.value)} title="Từ ngày" />
          <input className="pm-filter-input" type="date" value={filters.den_ngay} onChange={e => setFilter('den_ngay', e.target.value)} title="Đến ngày" />
          <button className="btn-icon" onClick={resetFilters} title="Xóa bộ lọc"><RefreshCw size={14} /></button>
        </div>
      </div>

      {/* Table */}
      <div className="pm-table-wrap">
        {loading && <div className="pm-loading"><div className="pm-spinner" /><span>Đang tải...</span></div>}
        {error && <div className="pm-error">⚠️ {error}</div>}
        {!loading && !error && items.length === 0 && (
          <div className="pm-empty">
            <div style={{ fontSize: 48, marginBottom: 12 }}>💬</div>
            <div style={{ color: 'var(--slate-300)', fontSize: 15, fontWeight: 500 }}>Chưa có dữ liệu tư vấn</div>
            <div style={{ color: 'var(--slate-500)', fontSize: 13, marginTop: 4 }}>Thêm mới hoặc import file CSV/JSON</div>
          </div>
        )}
        {!loading && items.length > 0 && (
          <table className="pm-table">
            <thead>
              <tr className="pm-thead-row">
                <th className="pm-th">Khách hàng</th>
                <th className="pm-th">Nhu cầu</th>
                <th className="pm-th" style={{ textAlign: 'right' }}>Ngân sách</th>
                <th className="pm-th">Kết quả</th>
                <th className="pm-th">Điểm AI</th>
                <th className="pm-th">Ngày</th>
                <th className="pm-th" style={{ width: 120 }}>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {items.map(s => (
                <SessionRow key={s.id} s={s}
                  onEdit={s => { setEditTarget(s); setShowForm(true) }}
                  onDelete={handleDelete}
                  onViewTranscript={setTranscriptTarget}
                  onAnalyze={handleAnalyze}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pm-pagination">
          <span className="pm-pagination-info">
            {((filters.page - 1) * filters.page_size + 1).toLocaleString()}–{Math.min(filters.page * filters.page_size, total).toLocaleString()} / {total.toLocaleString()} buổi
          </span>
          <div className="pm-pagination-btns">
            <button className="pm-page-btn" disabled={filters.page === 1} onClick={() => setFilter('page', filters.page - 1)}><ChevronLeft size={14} /></button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const p = Math.max(1, Math.min(filters.page - 2, totalPages - 4)) + i
              return <button key={p} className={`pm-page-btn ${p === filters.page ? 'active' : ''}`} onClick={() => setFilter('page', p)}>{p}</button>
            })}
            <button className="pm-page-btn" disabled={filters.page === totalPages} onClick={() => setFilter('page', filters.page + 1)}><ChevronRight size={14} /></button>
          </div>
        </div>
      )}

      {/* Modals */}
      {showForm && (
        <ConsultationForm
          initial={editTarget}
          onSave={handleSave}
          onClose={() => { setShowForm(false); setEditTarget(null) }}
          saving={saving}
          ketQuaOptions={KET_QUA_OPTIONS}
          loaiOptions={LOAI_NHU_CAU}
          kenhOptions={KENH}
        />
      )}
      {showImport && (
        <ImportModal onImport={handleImport} onClose={() => setShowImport(false)} />
      )}
      {transcriptTarget && (
        <TranscriptModal session={transcriptTarget} onClose={() => setTranscriptTarget(null)} />
      )}
      {analysisData && analysisSession && (
        <AnalysisModal
          data={analysisData}
          session={analysisSession}
          onClose={() => { setAnalysisData(null); setAnalysisSession(null) }}
        />
      )}
    </div>
  )
}
