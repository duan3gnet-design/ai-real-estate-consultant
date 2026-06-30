"""
Elasticsearch Client — Singleton connection
=============================================
Kết nối tới Elasticsearch chạy local qua Docker (mặc định http://localhost:9200).
Khởi tạo indices với mapping phù hợp cho:
  - properties              (structured + full-text + dense_vector)
  - consultation_sessions   (structured + full-text + dense_vector)
  - transcript_chunks       (full-text + dense_vector, liên kết qua session_id)

Dùng ID tự tăng riêng (sequence giả lập bằng index counter) để giữ
API trả về `id` dạng số nguyên giống cũ, tránh phải đổi toàn bộ frontend.
"""
import os
import threading
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ES_USER = os.getenv("ELASTICSEARCH_USER")
ES_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")

VECTOR_DIMS = 384  # paraphrase-multilingual-MiniLM-L12-v2

IDX_PROPERTIES = "properties"
IDX_SESSIONS = "consultation_sessions"
IDX_CHUNKS = "transcript_chunks"
IDX_COUNTERS = "id_counters"   # index phụ để cấp ID số nguyên tăng dần

_client: Elasticsearch | None = None
_lock = threading.Lock()


def get_es() -> Elasticsearch:
    global _client
    with _lock:
        if _client is None:
            kwargs = {"hosts": [ES_URL], "request_timeout": 30}
            if ES_USER and ES_PASSWORD:
                kwargs["basic_auth"] = (ES_USER, ES_PASSWORD)
            _client = Elasticsearch(**kwargs)
        return _client


def next_id(counter_name: str) -> int:
    """
    Cấp số ID nguyên tăng dần, atomic, dùng ES script update làm counter.
    counter_name: 'properties' | 'consultation_sessions' | 'transcript_chunks'
    """
    es = get_es()
    resp = es.update(
        index=IDX_COUNTERS,
        id=counter_name,
        script={
            "source": "ctx._source.value += 1",
            "lang": "painless",
        },
        upsert={"value": 1},
    )
    # Lấy giá trị mới nhất
    doc = es.get(index=IDX_COUNTERS, id=counter_name)
    return doc["_source"]["value"]


# ─── Mappings ─────────────────────────────────────────────────────────────────

_PROPERTIES_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "ma_bds": {"type": "keyword"},
            "ten": {"type": "text", "analyzer": "standard", "fields": {"keyword": {"type": "keyword"}}},
            "loai": {"type": "keyword"},
            "trang_thai": {"type": "keyword"},

            "dia_chi": {"type": "text"},
            "phuong_xa": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "quan_huyen": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "tinh_thanh": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "vi_do": {"type": "float"},
            "kinh_do": {"type": "float"},

            "dien_tich_dat": {"type": "float"},
            "dien_tich_san": {"type": "float"},
            "so_tang": {"type": "integer"},
            "so_phong_ngu": {"type": "integer"},
            "so_toilet": {"type": "integer"},
            "huong": {"type": "keyword"},
            "mat_tien": {"type": "float"},
            "duong_vao": {"type": "float"},

            "gia_ban": {"type": "float"},
            "gia_thue": {"type": "float"},
            "gia_mua_vao": {"type": "float"},
            "nam_mua": {"type": "integer"},
            "phi_quan_ly": {"type": "float"},

            "phap_ly": {"type": "keyword"},
            "nam_xay_dung": {"type": "integer"},
            "quy_hoach": {"type": "text"},

            "tien_ich": {"type": "text"},
            "mo_ta": {"type": "text"},
            "ghi_chu_noi_bo": {"type": "text"},

            "nguoi_phu_trach": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "so_dien_thoai": {"type": "keyword"},
            "anh_urls": {"type": "text", "index": False},

            "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm:ss||epoch_millis"},
            "updated_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm:ss||epoch_millis"},

            "embedding": {
                "type": "dense_vector",
                "dims": VECTOR_DIMS,
                "index": True,
                "similarity": "cosine",
            },
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "default": {"type": "standard"}
            }
        },
    },
}

_SESSIONS_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "ma_session": {"type": "keyword"},

            "ten_kh": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "dien_thoai_kh": {"type": "keyword"},
            "kenh_tiep_can": {"type": "keyword"},
            "nguoi_tu_van": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},

            "loai_nhu_cau": {"type": "keyword"},
            "loai_bds_quan_tam": {"type": "keyword"},
            "khu_vuc_quan_tam": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "ngan_sach_min": {"type": "float"},
            "ngan_sach_max": {"type": "float"},
            "dien_tich_yc": {"type": "text"},
            "so_pn_yc": {"type": "integer"},
            "tieu_chi_khac": {"type": "text"},

            "ket_qua": {"type": "keyword"},
            "bds_chot_id": {"type": "integer"},
            "bds_da_gioi_thieu": {"type": "text", "index": False},
            "ly_do_tu_choi": {"type": "text"},
            "ghi_chu": {"type": "text"},

            "thoi_gian_bat_dau": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm||yyyy-MM-dd'T'HH:mm:ss||epoch_millis"},
            "thoi_gian_ket_thuc": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm||yyyy-MM-dd'T'HH:mm:ss||epoch_millis"},
            "thoi_luong_phut": {"type": "integer"},

            "co_transcript": {"type": "integer"},
            "diem_chat_luong": {"type": "float"},
            "ai_feedback": {"type": "text", "index": False},

            "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm:ss||epoch_millis"},
            "updated_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm:ss||epoch_millis"},

            "embedding": {
                "type": "dense_vector",
                "dims": VECTOR_DIMS,
                "index": True,
                "similarity": "cosine",
            },
        }
    },
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
}

_CHUNKS_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "session_id": {"type": "integer"},
            "chunk_index": {"type": "integer"},
            "speaker": {"type": "keyword"},
            "content": {"type": "text"},
            "start_time": {"type": "float"},
            "end_time": {"type": "float"},
            "topics": {"type": "text"},
            "sentiment": {"type": "keyword"},
            "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm:ss||epoch_millis"},

            "embedding": {
                "type": "dense_vector",
                "dims": VECTOR_DIMS,
                "index": True,
                "similarity": "cosine",
            },
        }
    },
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
}

_COUNTERS_MAPPING = {
    "mappings": {
        "properties": {
            "value": {"type": "long"},
        }
    },
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
}


def init_es():
    """Tạo các index nếu chưa tồn tại."""
    es = get_es()

    indices = {
        IDX_PROPERTIES: _PROPERTIES_MAPPING,
        IDX_SESSIONS: _SESSIONS_MAPPING,
        IDX_CHUNKS: _CHUNKS_MAPPING,
        IDX_COUNTERS: _COUNTERS_MAPPING,
    }

    for name, body in indices.items():
        if not es.indices.exists(index=name):
            es.indices.create(index=name, body=body)
            print(f"[ES] Created index '{name}'")
        else:
            print(f"[ES] Index '{name}' already exists")

    print(f"[ES] Connected to {ES_URL}")
