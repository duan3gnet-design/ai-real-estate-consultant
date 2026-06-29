import { X, Star, TrendingUp, TrendingDown, Lightbulb, Target } from 'lucide-react'

function ScoreRing({ value, label, size = 56 }) {
  const pct = Math.min(value / 10, 1)
  const r = (size / 2) - 5
  const circ = 2 * Math.PI * r
  const dash = pct * circ
  const color = value >= 8 ? '#22c55e' : value >= 6 ? '#f59e0b' : '#ef4444'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={4} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={4}
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.6s ease' }} />
        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central"
          fill={color} fontSize={size < 50 ? 10 : 13} fontWeight="700"
          style={{ transform: 'rotate(90deg)', transformOrigin: '50% 50%' }}>
          {value?.toFixed(1)}
        </text>
      </svg>
      <span style={{ fontSize: 10, color: 'var(--slate-400)', textAlign: 'center', maxWidth: size }}>{label}</span>
    </div>
  )
}

function ListSection({ icon: Icon, title, items, color }) {
  if (!items?.length) return null
  return (
    <div className="am-section">
      <div className="am-section-title" style={{ color }}>
        <Icon size={14} /> {title}
      </div>
      <ul className="am-list">
        {items.map((item, i) => (
          <li key={i} className="am-list-item" style={{ borderLeftColor: color }}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export default function AnalysisModal({ data, session, onClose }) {
  const detail = data.diem_chi_tiet || {}
  const detailItems = [
    { key: 'kham_pha_nhu_cau',    label: 'Khám phá nhu cầu' },
    { key: 'trinh_bay_san_pham',   label: 'Trình bày SP' },
    { key: 'xu_ly_objection',      label: 'Xử lý phản đối' },
    { key: 'ky_nang_chot_sale',    label: 'Chốt sale' },
    { key: 'thai_do_chuyen_nghiep',label: 'Chuyên nghiệp' },
  ]

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="am-modal">
        {/* Header */}
        <div className="pf-header">
          <div className="pf-header-left">
            <span style={{ fontSize: 18 }}>🧠</span>
            <div>
              <div className="pf-title">Phân tích AI buổi tư vấn</div>
              <div style={{ fontSize: 11, color: 'var(--slate-400)', marginTop: 2 }}>
                {session?.ten_kh || 'Ẩn danh'} · {session?.nguoi_tu_van || ''} · {session?.created_at?.slice(0, 10)}
              </div>
            </div>
          </div>
          <button className="pf-close" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="am-body">
          {/* Tổng điểm + chi tiết */}
          <div className="am-scores-row">
            <div className="am-score-main">
              <ScoreRing value={data.diem_tong || 0} label="Tổng điểm" size={80} />
              <div style={{ fontSize: 12, color: 'var(--slate-300)', marginTop: 8, textAlign: 'center', maxWidth: 120 }}>
                {data.diem_tong >= 8 ? '🌟 Xuất sắc' : data.diem_tong >= 6 ? '👍 Tốt' : '⚠️ Cần cải thiện'}
              </div>
            </div>
            <div className="am-scores-detail">
              {detailItems.map(({ key, label }) => (
                detail[key] !== undefined && (
                  <div key={key} className="am-score-bar-row">
                    <span className="am-score-bar-label">{label}</span>
                    <div className="am-score-bar-wrap">
                      <div className="am-score-bar-fill" style={{
                        width: `${(detail[key] / 10) * 100}%`,
                        background: detail[key] >= 8 ? '#22c55e' : detail[key] >= 6 ? '#f59e0b' : '#ef4444',
                      }} />
                    </div>
                    <span className="am-score-bar-val">{detail[key]?.toFixed(1)}</span>
                  </div>
                )
              ))}
            </div>
          </div>

          {/* Tóm tắt */}
          {data.phan_tich_tom_tat && (
            <div className="am-summary">
              <Star size={14} style={{ color: 'var(--gold-500)', flexShrink: 0, marginTop: 1 }} />
              <p>{data.phan_tich_tom_tat}</p>
            </div>
          )}

          {/* Điểm mạnh / yếu / gợi ý */}
          <div className="am-lists">
            <ListSection icon={TrendingUp}  title="Điểm mạnh"      items={data.diem_manh}          color="#22c55e" />
            <ListSection icon={TrendingDown} title="Điểm yếu"      items={data.diem_yeu}            color="#ef4444" />
            <ListSection icon={Lightbulb}   title="Gợi ý cải thiện" items={data.goi_y_cai_thien}    color="#f59e0b" />
          </div>

          {/* Cơ hội còn lại */}
          {data.co_hoi_con_lai && (
            <div className="am-opportunity">
              <Target size={14} style={{ color: '#3b82f6', flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#3b82f6', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>Cơ hội tiếp theo</div>
                <p style={{ fontSize: 13, color: 'var(--slate-200)', lineHeight: 1.6 }}>{data.co_hoi_con_lai}</p>
              </div>
            </div>
          )}
        </div>

        <div className="pf-footer">
          <button className="btn-primary" onClick={onClose}>Đóng</button>
        </div>
      </div>
    </div>
  )
}
