import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "realestate.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
        -- ══════════════════════════════════════════
        --  PROPERTIES (giữ nguyên)
        -- ══════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_bds TEXT UNIQUE, ten TEXT NOT NULL, loai TEXT NOT NULL,
            trang_thai TEXT NOT NULL DEFAULT 'Đang bán',
            dia_chi TEXT NOT NULL, phuong_xa TEXT, quan_huyen TEXT, tinh_thanh TEXT NOT NULL,
            vi_do REAL, kinh_do REAL,
            dien_tich_dat REAL, dien_tich_san REAL, so_tang INTEGER,
            so_phong_ngu INTEGER, so_toilet INTEGER, huong TEXT,
            mat_tien REAL, duong_vao REAL,
            gia_ban REAL, gia_thue REAL, gia_mua_vao REAL, nam_mua INTEGER, phi_quan_ly REAL,
            phap_ly TEXT, nam_xay_dung INTEGER, quy_hoach TEXT,
            tien_ich TEXT, mo_ta TEXT, ghi_chu_noi_bo TEXT,
            nguoi_phu_trach TEXT, so_dien_thoai TEXT, anh_urls TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_prop_loai       ON properties(loai);
        CREATE INDEX IF NOT EXISTS idx_prop_trang_thai ON properties(trang_thai);
        CREATE INDEX IF NOT EXISTS idx_prop_tinh_thanh ON properties(tinh_thanh);
        CREATE INDEX IF NOT EXISTS idx_prop_quan_huyen ON properties(quan_huyen);
        CREATE INDEX IF NOT EXISTS idx_prop_gia_ban    ON properties(gia_ban);
        CREATE INDEX IF NOT EXISTS idx_prop_gia_thue   ON properties(gia_thue);
        CREATE INDEX IF NOT EXISTS idx_prop_dien_tich  ON properties(dien_tich_san);
        CREATE INDEX IF NOT EXISTS idx_prop_phong_ngu  ON properties(so_phong_ngu);
        CREATE VIRTUAL TABLE IF NOT EXISTS properties_fts USING fts5(
            id UNINDEXED, ten, dia_chi, phuong_xa, quan_huyen, tinh_thanh,
            loai, tien_ich, mo_ta, quy_hoach,
            content='properties', content_rowid='id', tokenize='unicode61'
        );
        CREATE TRIGGER IF NOT EXISTS prop_fts_insert AFTER INSERT ON properties BEGIN
            INSERT INTO properties_fts(rowid,id,ten,dia_chi,phuong_xa,quan_huyen,tinh_thanh,loai,tien_ich,mo_ta,quy_hoach)
            VALUES(NEW.id,NEW.id,NEW.ten,NEW.dia_chi,NEW.phuong_xa,NEW.quan_huyen,NEW.tinh_thanh,NEW.loai,NEW.tien_ich,NEW.mo_ta,NEW.quy_hoach);
        END;
        CREATE TRIGGER IF NOT EXISTS prop_fts_update AFTER UPDATE ON properties BEGIN
            INSERT INTO properties_fts(properties_fts,rowid,id,ten,dia_chi,phuong_xa,quan_huyen,tinh_thanh,loai,tien_ich,mo_ta,quy_hoach)
            VALUES('delete',OLD.id,OLD.id,OLD.ten,OLD.dia_chi,OLD.phuong_xa,OLD.quan_huyen,OLD.tinh_thanh,OLD.loai,OLD.tien_ich,OLD.mo_ta,OLD.quy_hoach);
            INSERT INTO properties_fts(rowid,id,ten,dia_chi,phuong_xa,quan_huyen,tinh_thanh,loai,tien_ich,mo_ta,quy_hoach)
            VALUES(NEW.id,NEW.id,NEW.ten,NEW.dia_chi,NEW.phuong_xa,NEW.quan_huyen,NEW.tinh_thanh,NEW.loai,NEW.tien_ich,NEW.mo_ta,NEW.quy_hoach);
        END;
        CREATE TRIGGER IF NOT EXISTS prop_fts_delete AFTER DELETE ON properties BEGIN
            INSERT INTO properties_fts(properties_fts,rowid,id,ten,dia_chi,phuong_xa,quan_huyen,tinh_thanh,loai,tien_ich,mo_ta,quy_hoach)
            VALUES('delete',OLD.id,OLD.id,OLD.ten,OLD.dia_chi,OLD.phuong_xa,OLD.quan_huyen,OLD.tinh_thanh,OLD.loai,OLD.tien_ich,OLD.mo_ta,OLD.quy_hoach);
        END;
        CREATE TRIGGER IF NOT EXISTS prop_updated_at AFTER UPDATE ON properties BEGIN
            UPDATE properties SET updated_at=datetime('now','localtime') WHERE id=NEW.id;
        END;

        -- ══════════════════════════════════════════
        --  CONSULTATION SESSIONS — metadata CRM
        -- ══════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS consultation_sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_session      TEXT UNIQUE,                -- mã định danh riêng (từ CRM)

            -- Thông tin khách hàng (có thể ẩn danh)
            ten_kh          TEXT,
            dien_thoai_kh   TEXT,
            kenh_tiep_can   TEXT,                       -- Facebook, Zalo, Walk-in, Referral...
            nguoi_tu_van    TEXT,                       -- tên nhân viên tư vấn

            -- Nhu cầu khách hàng
            loai_nhu_cau    TEXT,                       -- Mua, Thuê, Đầu tư, Bán
            loai_bds_quan_tam TEXT,                     -- Căn hộ, Nhà phố...
            khu_vuc_quan_tam  TEXT,
            ngan_sach_min   REAL,                       -- triệu VNĐ
            ngan_sach_max   REAL,
            dien_tich_yc    TEXT,                       -- yêu cầu diện tích
            so_pn_yc        INTEGER,
            tieu_chi_khac   TEXT,                       -- ghi chú nhu cầu

            -- Kết quả
            ket_qua         TEXT DEFAULT 'Chưa chốt',  -- Chốt giao dịch | Hẹn lại | Từ chối | Đang cân nhắc
            bds_chot_id     INTEGER REFERENCES properties(id),
            bds_da_gioi_thieu TEXT,                     -- JSON array id BĐS đã giới thiệu
            ly_do_tu_choi   TEXT,
            ghi_chu         TEXT,

            -- Thời gian
            thoi_gian_bat_dau TEXT,
            thoi_gian_ket_thuc TEXT,
            thoi_luong_phut INTEGER,                    -- thời lượng tư vấn (phút)

            -- Transcript (nếu có)
            co_transcript   INTEGER DEFAULT 0,          -- 0/1

            -- Điểm chất lượng (AI chấm sau)
            diem_chat_luong REAL,                       -- 0-10
            ai_feedback     TEXT,                       -- JSON: strengths, weaknesses, suggestions

            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_cs_ket_qua       ON consultation_sessions(ket_qua);
        CREATE INDEX IF NOT EXISTS idx_cs_nguoi_tv      ON consultation_sessions(nguoi_tu_van);
        CREATE INDEX IF NOT EXISTS idx_cs_loai_nhu_cau  ON consultation_sessions(loai_nhu_cau);
        CREATE INDEX IF NOT EXISTS idx_cs_created_at    ON consultation_sessions(created_at);
        CREATE INDEX IF NOT EXISTS idx_cs_khu_vuc       ON consultation_sessions(khu_vuc_quan_tam);

        -- ══════════════════════════════════════════
        --  TRANSCRIPT CHUNKS — FTS search
        -- ══════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS transcript_chunks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,               -- thứ tự chunk trong session
            speaker     TEXT,                           -- 'consultant' | 'customer' | 'unknown'
            content     TEXT NOT NULL,                  -- nội dung đoạn transcript
            start_time  REAL,                           -- giây (nếu có từ audio)
            end_time    REAL,
            -- labels AI tự động (JSON array strings)
            topics      TEXT,                           -- JSON: ["giá cả", "pháp lý", "vị trí"]
            sentiment   TEXT,                           -- positive/neutral/negative
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_tc_session ON transcript_chunks(session_id);
        CREATE INDEX IF NOT EXISTS idx_tc_speaker ON transcript_chunks(speaker);

        -- FTS5 cho transcript chunks
        CREATE VIRTUAL TABLE IF NOT EXISTS transcript_fts USING fts5(
            id UNINDEXED,
            session_id UNINDEXED,
            speaker,
            content,
            topics,
            content='transcript_chunks',
            content_rowid='id',
            tokenize='unicode61'
        );
        CREATE TRIGGER IF NOT EXISTS tc_fts_insert AFTER INSERT ON transcript_chunks BEGIN
            INSERT INTO transcript_fts(rowid,id,session_id,speaker,content,topics)
            VALUES(NEW.id,NEW.id,NEW.session_id,NEW.speaker,NEW.content,NEW.topics);
        END;
        CREATE TRIGGER IF NOT EXISTS tc_fts_delete AFTER DELETE ON transcript_chunks BEGIN
            INSERT INTO transcript_fts(transcript_fts,rowid,id,session_id,speaker,content,topics)
            VALUES('delete',OLD.id,OLD.id,OLD.session_id,OLD.speaker,OLD.content,OLD.topics);
        END;

        -- ══════════════════════════════════════════
        --  UPDATED_AT triggers cho consultations
        -- ══════════════════════════════════════════
        CREATE TRIGGER IF NOT EXISTS cs_updated_at AFTER UPDATE ON consultation_sessions BEGIN
            UPDATE consultation_sessions SET updated_at=datetime('now','localtime') WHERE id=NEW.id;
        END;
    """)
    conn.commit()
    conn.close()
    print(f"[DB] Initialized at {DB_PATH}")
