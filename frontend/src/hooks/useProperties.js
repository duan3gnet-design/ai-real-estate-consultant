import { useState, useCallback, useEffect } from 'react'
import { fetchProperties, fetchStats, createProperty, updateProperty, deleteProperty, importCsv, importJson } from '../services/api'

export function useProperties() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [filters, setFilters] = useState({
    page: 1, page_size: 20,
    loai: '', trang_thai: '', tinh_thanh: '', quan_huyen: '',
    gia_ban_min: '', gia_ban_max: '', gia_thue_min: '', gia_thue_max: '',
    dien_tich_min: '', dien_tich_max: '', so_phong_ngu_min: '', phap_ly: '',
    sort_by: 'created_at', sort_dir: 'desc',
  })

  const load = useCallback(async (overrides = {}) => {
    setLoading(true)
    setError(null)
    try {
      const params = { ...filters, ...overrides }
      const data = await fetchProperties(params)
      setItems(data.items)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [filters])

  const loadStats = useCallback(async () => {
    try { setStats(await fetchStats()) } catch { /* silent */ }
  }, [])

  useEffect(() => { load() }, [filters])
  useEffect(() => { loadStats() }, [])

  const setFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, page: key === 'page' ? value : 1 }))
  }, [])

  const resetFilters = useCallback(() => {
    setFilters(prev => ({
      ...prev,
      loai: '', trang_thai: '', tinh_thanh: '', quan_huyen: '',
      gia_ban_min: '', gia_ban_max: '', gia_thue_min: '', gia_thue_max: '',
      dien_tich_min: '', dien_tich_max: '', so_phong_ngu_min: '', phap_ly: '',
      page: 1,
    }))
  }, [])

  const create = useCallback(async (data) => {
    const prop = await createProperty(data)
    await load()
    await loadStats()
    return prop
  }, [load, loadStats])

  const update = useCallback(async (id, data) => {
    const prop = await updateProperty(id, data)
    await load()
    return prop
  }, [load])

  const remove = useCallback(async (id) => {
    await deleteProperty(id)
    await load()
    await loadStats()
  }, [load, loadStats])

  const importFile = useCallback(async (file) => {
    const isJson = file.name.endsWith('.json')
    const result = isJson ? await importJson(file) : await importCsv(file)
    await load()
    await loadStats()
    return result
  }, [load, loadStats])

  return {
    items, total, totalPages, stats, loading, error,
    filters, setFilter, resetFilters,
    create, update, remove, importFile,
    reload: load,
  }
}
