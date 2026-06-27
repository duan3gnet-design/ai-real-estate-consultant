import { useState } from 'react'
import { Plus, Upload, Search, Filter, RefreshCw, Edit2, Trash2, ChevronLeft, ChevronRight, TrendingUp, Home, DollarSign, Database } from 'lucide-react'
import { useProperties } from '../hooks/useProperties'
import PropertyForm from './PropertyForm'
import ImportModal from './ImportModal'
import { PROPERTY_TYPES, PROPERTY_STATUSES, LEGAL_STATUSES, STATUS_COLORS, TYPE_ICONS, formatPrice, formatArea } from '../constants'

// ─── Stats Cards ─────────────────────────────────────────────────────────────
function StatsBar({ stats }) {
  if (!stats) return null
  return (
    <div className="pm-stats">
      <div className="pm-stat-card">
        <Database size={16} style={{ color: 'var(--gold-500)' }} />
        <div><div className="pm-stat-val">{stats.total.toLocaleString('vi-VN')}</div><div className="pm-stat-label">Tổng BĐS</div></div>
      </div>
      <div className="pm-stat-card">
        <Home size={16} style={{ color: '#3b82f6' }} />
        <div>
          <div className="pm-stat-val">{stats.by_trang_thai?.find(s => s.trang_thai === 'Đang bán')?.cnt || 0}</div>
          <div className="pm-stat-label">Đang bán</div>
        </div>
      </div>
      <div className="pm-stat-card">
        <TrendingUp size={16} style={{ color: '#a855f7' }} />
        <div>
          <div className="pm-stat-val">{stats.by_trang_thai?.find(s => s.trang_thai === 'Đang cho thuê')?.cnt || 0}</div>
          <div className="pm-stat-label">Đang cho thuê</div>
        </div>
      </div>
      <div className="pm-stat-card">
        <DollarSign size={16} style={{ color: 'var(--green-500)' }} />
        <div>
          <div className="pm-stat-val">{formatPrice(stats.avg_gia_ban)}</div>
          <div className="pm-stat-label">Giá TB bán</div>
        </div>
      </div>
    </div>
  )
}

// ─── Filter Bar ───────────────────────────────────────────────────────────────
function FilterBar({ filters, setFilter, resetFilters, onSearch }) {
  const [searchText, setSearchText] = useState('')
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="pm-filterbar">
      <div className="pm-filterbar-row1">
        <div className="pm-search-wrap">
          <Search size={14} className="pm-search-icon" />
          <input
            className="pm-search-input"
            placeholder="Tìm tên, địa chỉ, mô tả..."
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && onSearch(searchText)}
          />
          {searchText && (
            <button className="pm-search-clear" onClick={() => { setSearchText(''); onSearch('') }}>×</button>
          )}
        </div>
        <button className="btn-icon" onClick={() => onSearch(searchText)} title="Tìm kiếm">
          <Search size={14} />
        </button>
        <button className={`btn-icon ${expanded ? 'active' : ''}`} onClick={() => setExpanded(!expanded)} title="Bộ lọc">
          <Filter size={14} />
        </button>
        <button className="btn-icon" onClick={resetFilters} title="Xóa bộ lọc">
          <RefreshCw size={14} />
        </button>
      </div>

      {expanded && (
        <div className="pm-filters-expanded">
          <select className="pm-filter-select" value={filters.loai} onChange={e => setFilter('loai', e.target.value)}>
            <option value="">Tất cả loại</option>
            {PROPERTY_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className="pm-filter-select" value={filters.trang_thai} onChange={e => setFilter('trang_thai', e.target.value)}>
            <option value="">Tất cả trạng thái</option>
            {PROPERTY_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <input className="pm-filter-input" placeholder="Tỉnh/TP" value={filters.tinh_thanh} onChange={e => setFilter('tinh_thanh', e.target.value)} />
          <input className="pm-filter-input" placeholder="Quận/Huyện" value={filters.quan_huyen} onChange={e => setFilter('quan_huyen', e.target.value)} />
          <input className="pm-filter-input" type="number" placeholder="Giá bán từ (tr)" value={filters.gia_ban_min} onChange={e => setFilter('gia_ban_min', e.target.value)} />
          <input className="pm-filter-input" type="number" placeholder="Giá bán đến (tr)" value={filters.gia_ban_max} onChange={e => setFilter('gia_ban_max', e.target.value)} />
          <input className="pm-filter-input" type="number" placeholder="DT từ (m²)" value={filters.dien_tich_min} onChange={e => setFilter('dien_tich_min', e.target.value)} />
          <input className="pm-filter-input" type="number" placeholder="Số PN tối thiểu" value={filters.so_phong_ngu_min} onChange={e => setFilter('so_phong_ngu_min', e.target.value)} />
          <select className="pm-filter-select" value={filters.phap_ly} onChange={e => setFilter('phap_ly', e.target.value)}>
            <option value="">Tất cả pháp lý</option>
            {LEGAL_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="pm-filter-select" value={filters.sort_by} onChange={e => setFilter('sort_by', e.target.value)}>
            <option value="created_at">Mới nhất</option>
            <option value="gia_ban">Giá bán</option>
            <option value="gia_thue">Giá thuê</option>
            <option value="dien_tich_san">Diện tích</option>
            <option value="ten">Tên A-Z</option>
          </select>
          <select className="pm-filter-select" value={filters.sort_dir} onChange={e => setFilter('sort_dir', e.target.value)}>
            <option value="desc">Giảm dần</option>
            <option value="asc">Tăng dần</option>
          </select>
        </div>
      )}
    </div>
  )
}

// ─── Status Badge ─────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const c = STATUS_COLORS[status] || { bg: 'rgba(100,116,139,0.15)', text: '#64748b' }
  return (
    <span style={{ background: c.bg, color: c.text, padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap' }}>
      {status}
    </span>
  )
}

// ─── Property Row ─────────────────────────────────────────────────────────────
function PropertyRow({ prop, onEdit, onDelete }) {
  const icon = TYPE_ICONS[prop.loai] || '🏠'
  const profit = prop.gia_ban && prop.gia_mua_vao
    ? ((prop.gia_ban - prop.gia_mua_vao) / prop.gia_mua_vao * 100).toFixed(1)
    : null

  return (
    <tr className="pm-row">
      <td className="pm-td pm-td-name">
        <div className="pm-prop-name">
          <span className="pm-prop-icon">{icon}</span>
          <div>
            <div className="pm-prop-title">{prop.ten}</div>
            <div className="pm-prop-addr">{prop.dia_chi}, {prop.quan_huyen || ''} {prop.tinh_thanh}</div>
            {prop.ma_bds && <div className="pm-prop-code">#{prop.ma_bds}</div>}
          </div>
        </div>
      </td>
      <td className="pm-td"><StatusBadge status={prop.trang_thai} /></td>
      <td className="pm-td pm-td-num">
        {formatArea(prop.dien_tich_san || prop.dien_tich_dat)}
        {prop.so_phong_ngu ? <div style={{ fontSize: 11, color: 'var(--slate-400)' }}>{prop.so_phong_ngu} PN</div> : null}
      </td>
      <td className="pm-td pm-td-num">
        {prop.gia_ban ? <div className="pm-price-sale">{formatPrice(prop.gia_ban)}</div> : null}
        {prop.gia_thue ? <div className="pm-price-rent">{formatPrice(prop.gia_thue)}/th</div> : null}
        {!prop.gia_ban && !prop.gia_thue && <span style={{ color: 'var(--slate-500)' }}>—</span>}
      </td>
      <td className="pm-td">
        {profit !== null ? (
          <span style={{ color: +profit >= 0 ? 'var(--green-500)' : 'var(--red-500)', fontWeight: 600, fontSize: 12 }}>
            {+profit >= 0 ? '+' : ''}{profit}%
          </span>
        ) : <span style={{ color: 'var(--slate-500)' }}>—</span>}
      </td>
      <td className="pm-td">{prop.phap_ly ? <span style={{ fontSize: 11, color: 'var(--slate-300)' }}>{prop.phap_ly}</span> : '—'}</td>
      <td className="pm-td pm-td-actions">
        <button className="pm-action-btn edit" onClick={() => onEdit(prop)} title="Chỉnh sửa"><Edit2 size={13} /></button>
        <button className="pm-action-btn delete" onClick={() => onDelete(prop)} title="Xóa"><Trash2 size={13} /></button>
      </td>
    </tr>
  )
}

// ─── Pagination ───────────────────────────────────────────────────────────────
function Pagination({ page, totalPages, total, pageSize, onPage }) {
  if (totalPages <= 1) return null
  const pages = []
  const start = Math.max(1, page - 2)
  const end = Math.min(totalPages, page + 2)
  for (let i = start; i <= end; i++) pages.push(i)

  return (
    <div className="pm-pagination">
      <span className="pm-pagination-info">
        {((page - 1) * pageSize + 1).toLocaleString()}–{Math.min(page * pageSize, total).toLocaleString()} / {total.toLocaleString()} BĐS
      </span>
      <div className="pm-pagination-btns">
        <button className="pm-page-btn" disabled={page === 1} onClick={() => onPage(page - 1)}><ChevronLeft size={14} /></button>
        {start > 1 && <><button className="pm-page-btn" onClick={() => onPage(1)}>1</button><span className="pm-page-ellipsis">…</span></>}
        {pages.map(p => <button key={p} className={`pm-page-btn ${p === page ? 'active' : ''}`} onClick={() => onPage(p)}>{p}</button>)}
        {end < totalPages && <><span className="pm-page-ellipsis">…</span><button className="pm-page-btn" onClick={() => onPage(totalPages)}>{totalPages}</button></>}
        <button className="pm-page-btn" disabled={page === totalPages} onClick={() => onPage(page + 1)}><ChevronRight size={14} /></button>
      </div>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function PropertyManager() {
  const {
    items, total, totalPages, stats, loading, error,
    filters, setFilter, resetFilters,
    create, update, remove, importFile, reload,
  } = useProperties()

  const [showForm, setShowForm] = useState(false)
  const [editTarget, setEditTarget] = useState(null)
  const [showImport, setShowImport] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [searchMode, setSearchMode] = useState(false) // true = dùng FTS search endpoint

  const handleSave = async (data) => {
    setSaving(true)
    try {
      if (editTarget?.id) await update(editTarget.id, data)
      else await create(data)
      setShowForm(false)
      setEditTarget(null)
    } catch (e) {
      alert('Lỗi: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (prop) => {
    if (!confirm(`Xóa "${prop.ten}"?\nHành động này không thể hoàn tác.`)) return
    try { await remove(prop.id) }
    catch (e) { alert('Lỗi xóa: ' + e.message) }
  }

  const handleSearch = (text) => {
    // Tìm kiếm bằng cách reload với keyword — backend FTS sẽ xử lý
    // Đây là approach đơn giản: filter tinh_thanh/quan_huyen
    // Nếu muốn full FTS thì thêm endpoint /properties/search
    reload({ ...filters, tinh_thanh: '', quan_huyen: '', page: 1 })
  }

  return (
    <div className="pm-root">
      {/* Header */}
      <div className="pm-header">
        <div>
          <h1 className="pm-title">Danh mục Bất động sản</h1>
          <p className="pm-subtitle">Quản lý toàn bộ dữ liệu BĐS của công ty</p>
        </div>
        <div className="pm-header-actions">
          <button className="btn-secondary pm-btn" onClick={() => setShowImport(true)}>
            <Upload size={14} /> Import CSV/JSON
          </button>
          <button className="btn-primary pm-btn" onClick={() => { setEditTarget(null); setShowForm(true) }}>
            <Plus size={14} /> Thêm BĐS
          </button>
        </div>
      </div>

      {/* Stats */}
      <StatsBar stats={stats} />

      {/* Filters */}
      <FilterBar filters={filters} setFilter={setFilter} resetFilters={resetFilters} onSearch={handleSearch} />

      {/* Table */}
      <div className="pm-table-wrap">
        {loading && (
          <div className="pm-loading">
            <div className="pm-spinner" />
            <span>Đang tải...</span>
          </div>
        )}

        {error && (
          <div className="pm-error">⚠️ {error} <button onClick={reload} style={{ marginLeft: 8, textDecoration: 'underline', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}>Thử lại</button></div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="pm-empty">
            <div style={{ fontSize: 48, marginBottom: 12 }}>🏠</div>
            <div style={{ color: 'var(--slate-300)', fontSize: 15, fontWeight: 500 }}>Chưa có bất động sản nào</div>
            <div style={{ color: 'var(--slate-500)', fontSize: 13, marginTop: 4 }}>Thêm mới hoặc import file CSV/JSON</div>
          </div>
        )}

        {!loading && items.length > 0 && (
          <table className="pm-table">
            <thead>
              <tr className="pm-thead-row">
                <th className="pm-th">Bất động sản</th>
                <th className="pm-th">Trạng thái</th>
                <th className="pm-th">Diện tích</th>
                <th className="pm-th">Giá</th>
                <th className="pm-th">Lợi nhuận</th>
                <th className="pm-th">Pháp lý</th>
                <th className="pm-th" style={{ width: 80 }}>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {items.map(prop => (
                <PropertyRow key={prop.id} prop={prop}
                  onEdit={p => { setEditTarget(p); setShowForm(true) }}
                  onDelete={handleDelete}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      <Pagination
        page={filters.page} totalPages={totalPages}
        total={total} pageSize={filters.page_size}
        onPage={p => setFilter('page', p)}
      />

      {/* Modals */}
      {showForm && (
        <PropertyForm
          initial={editTarget}
          onSave={handleSave}
          onClose={() => { setShowForm(false); setEditTarget(null) }}
          saving={saving}
        />
      )}

      {showImport && (
        <ImportModal
          onImport={importFile}
          onClose={() => setShowImport(false)}
        />
      )}
    </div>
  )
}
