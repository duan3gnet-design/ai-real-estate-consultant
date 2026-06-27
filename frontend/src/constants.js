export const PROPERTY_TYPES = [
  'Căn hộ chung cư', 'Nhà phố', 'Biệt thự', 'Đất nền',
  'Shophouse', 'Văn phòng', 'Mặt bằng thương mại', 'Kho / Xưởng', 'Khách sạn / Căn hộ dịch vụ',
]

export const PROPERTY_STATUSES = [
  'Đang bán', 'Đang cho thuê', 'Bán & Cho thuê', 'Đã bán', 'Đã cho thuê', 'Tạm khóa',
]

export const LEGAL_STATUSES = [
  'Sổ đỏ (GCNQSDĐ)', 'Sổ hồng (GCNQSH)', 'Hợp đồng mua bán',
  'Giấy tờ hợp lệ khác', 'Chưa có sổ', 'Đang làm sổ',
]

export const DIRECTIONS = ['Đông', 'Tây', 'Nam', 'Bắc', 'Đông Nam', 'Đông Bắc', 'Tây Nam', 'Tây Bắc']

export const STATUS_COLORS = {
  'Đang bán':      { bg: 'rgba(34,197,94,0.15)',  text: '#22c55e', dot: '#22c55e' },
  'Đang cho thuê': { bg: 'rgba(59,130,246,0.15)', text: '#3b82f6', dot: '#3b82f6' },
  'Bán & Cho thuê':{ bg: 'rgba(168,85,247,0.15)', text: '#a855f7', dot: '#a855f7' },
  'Đã bán':        { bg: 'rgba(100,116,139,0.15)',text: '#64748b', dot: '#64748b' },
  'Đã cho thuê':   { bg: 'rgba(100,116,139,0.15)',text: '#64748b', dot: '#64748b' },
  'Tạm khóa':      { bg: 'rgba(239,68,68,0.15)',  text: '#ef4444', dot: '#ef4444' },
}

export const TYPE_ICONS = {
  'Căn hộ chung cư': '🏢', 'Nhà phố': '🏠', 'Biệt thự': '🏰',
  'Đất nền': '🌳', 'Shophouse': '🏪', 'Văn phòng': '🖥️',
  'Mặt bằng thương mại': '🏬', 'Kho / Xưởng': '🏭',
  'Khách sạn / Căn hộ dịch vụ': '🏨',
}

export const formatPrice = (val) => {
  if (!val) return '—'
  if (val >= 1000) return `${(val / 1000).toFixed(val % 1000 === 0 ? 0 : 1)} tỷ`
  return `${val.toLocaleString('vi-VN')} triệu`
}

export const formatArea = (val) => val ? `${val.toLocaleString('vi-VN')} m²` : '—'
