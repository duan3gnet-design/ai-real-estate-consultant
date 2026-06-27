import { useState, useRef } from 'react'
import { X, Upload, Download, FileText, CheckCircle, AlertCircle } from 'lucide-react'

const TEMPLATE_CSV_URL = 'http://127.0.0.1:8765/properties/template'

export default function ImportModal({ onImport, onClose }) {
  const [dragOver, setDragOver] = useState(false)
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef()

  const handleFile = (f) => {
    if (!f) return
    if (!f.name.endsWith('.csv') && !f.name.endsWith('.json')) {
      alert('Chỉ hỗ trợ file .csv hoặc .json')
      return
    }
    setFile(f)
    setResult(null)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleImport = async () => {
    if (!file) return
    setLoading(true)
    try {
      const res = await onImport(file)
      setResult(res)
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setLoading(false)
    }
  }

  const downloadTemplate = () => {
    const csvContent = `ma_bds,ten,loai,trang_thai,dia_chi,phuong_xa,quan_huyen,tinh_thanh,dien_tich_dat,dien_tich_san,so_tang,so_phong_ngu,so_toilet,huong,mat_tien,duong_vao,gia_ban,gia_thue,gia_mua_vao,nam_mua,phi_quan_ly,phap_ly,nam_xay_dung,quy_hoach,tien_ich,mo_ta,nguoi_phu_trach,so_dien_thoai,anh_urls,ghi_chu_noi_bo
BDS001,Căn hộ Vinhomes 2PN,Căn hộ chung cư,Đang bán,"720A Điện Biên Phủ",Phường 22,Bình Thạnh,TP. Hồ Chí Minh,,68,,2,2,Đông Nam,,,4200,,3500,2020,3,Sổ hồng (GCNQSH),2018,Đất ở đô thị,"Hồ bơi, gym, siêu thị","Căn hộ view sông, nội thất đầy đủ",Nguyễn Văn A,0901234567,,`
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'template_bds.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ width: 540 }}>
        <div className="pf-header" style={{ marginBottom: 20 }}>
          <div className="pf-header-left">
            <Upload size={18} style={{ color: 'var(--gold-500)' }} />
            <span className="pf-title">Import dữ liệu BĐS</span>
          </div>
          <button className="pf-close" onClick={onClose}><X size={16} /></button>
        </div>

        {/* Download template */}
        <div className="import-template-bar">
          <FileText size={14} style={{ color: 'var(--gold-500)' }} />
          <span>Tải file mẫu để điền đúng định dạng</span>
          <button className="btn-secondary" style={{ padding: '5px 12px', fontSize: 12 }} onClick={downloadTemplate}>
            <Download size={12} style={{ marginRight: 4 }} />
            Template CSV
          </button>
        </div>

        {/* Drop zone */}
        {!result && (
          <div
            className={`import-dropzone ${dragOver ? 'dragover' : ''} ${file ? 'has-file' : ''}`}
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
          >
            <input ref={inputRef} type="file" accept=".csv,.json" style={{ display: 'none' }}
              onChange={e => handleFile(e.target.files[0])} />
            {file ? (
              <>
                <div className="import-file-icon">📄</div>
                <div className="import-file-name">{file.name}</div>
                <div className="import-file-size">{(file.size / 1024).toFixed(1)} KB</div>
              </>
            ) : (
              <>
                <Upload size={32} style={{ color: 'var(--slate-400)', marginBottom: 10 }} />
                <div style={{ color: 'var(--slate-300)', fontSize: 14, fontWeight: 500 }}>
                  Kéo thả file vào đây
                </div>
                <div style={{ color: 'var(--slate-500)', fontSize: 12, marginTop: 4 }}>
                  hoặc click để chọn file .CSV / .JSON
                </div>
              </>
            )}
          </div>
        )}

        {/* Result */}
        {result && !result.error && (
          <div className="import-result">
            <div className="import-result-header">
              <CheckCircle size={20} style={{ color: 'var(--green-500)' }} />
              <span>Import hoàn tất</span>
            </div>
            <div className="import-stats">
              <div className="import-stat"><span>Tổng dòng</span><strong>{result.total}</strong></div>
              <div className="import-stat success"><span>Thành công</span><strong>{result.success}</strong></div>
              <div className="import-stat failed"><span>Thất bại</span><strong>{result.failed}</strong></div>
            </div>
            {result.errors?.length > 0 && (
              <div className="import-errors">
                <div className="import-errors-title"><AlertCircle size={13} /> Lỗi chi tiết:</div>
                {result.errors.slice(0, 10).map((e, i) => (
                  <div key={i} className="import-error-row">{e}</div>
                ))}
                {result.errors.length > 10 && <div className="import-error-row">...và {result.errors.length - 10} lỗi khác</div>}
              </div>
            )}
          </div>
        )}

        {result?.error && (
          <div className="import-error-box">
            <AlertCircle size={16} />
            {result.error}
          </div>
        )}

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>{result ? 'Đóng' : 'Hủy'}</button>
          {!result && (
            <button className="btn-primary" onClick={handleImport} disabled={!file || loading}>
              <Upload size={14} />
              {loading ? 'Đang import...' : 'Bắt đầu import'}
            </button>
          )}
          {result && !result.error && (
            <button className="btn-primary" onClick={() => { setFile(null); setResult(null) }}>
              Import thêm
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
