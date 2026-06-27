import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "realestate.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # hiệu suất ghi tốt hơn
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Khởi tạo schema SQLite với FTS5 cho full-text search."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    # Bảng chính
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS properties (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_bds            TEXT UNIQUE,
            ten               TEXT NOT NULL,
            loai              TEXT NOT NULL,
            trang_thai        TEXT NOT NULL DEFAULT 'Đang bán',

            dia_chi           TEXT NOT NULL,
            phuong_xa         TEXT,
            quan_huyen        TEXT,
            tinh_thanh        TEXT NOT NULL,
            vi_do             REAL,
            kinh_do           REAL,

            dien_tich_dat     REAL,
            dien_tich_san     REAL,
            so_tang           INTEGER,
            so_phong_ngu      INTEGER,
            so_toilet         INTEGER,
            huong             TEXT,
            mat_tien          REAL,
            duong_vao         REAL,

            gia_ban           REAL,
            gia_thue          REAL,
            gia_mua_vao       REAL,
            nam_mua           INTEGER,
            phi_quan_ly       REAL,

            phap_ly           TEXT,
            nam_xay_dung      INTEGER,
            quy_hoach         TEXT,

            tien_ich          TEXT,
            mo_ta             TEXT,
            ghi_chu_noi_bo    TEXT,

            nguoi_phu_trach   TEXT,
            so_dien_thoai     TEXT,
            anh_urls          TEXT,

            created_at        TEXT DEFAULT (datetime('now','localtime')),
            updated_at        TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Indexes thường dùng khi filter
        CREATE INDEX IF NOT EXISTS idx_prop_loai       ON properties(loai);
        CREATE INDEX IF NOT EXISTS idx_prop_trang_thai ON properties(trang_thai);
        CREATE INDEX IF NOT EXISTS idx_prop_tinh_thanh ON properties(tinh_thanh);
        CREATE INDEX IF NOT EXISTS idx_prop_quan_huyen ON properties(quan_huyen);
        CREATE INDEX IF NOT EXISTS idx_prop_gia_ban    ON properties(gia_ban);
        CREATE INDEX IF NOT EXISTS idx_prop_gia_thue   ON properties(gia_thue);
        CREATE INDEX IF NOT EXISTS idx_prop_dien_tich  ON properties(dien_tich_san);
        CREATE INDEX IF NOT EXISTS idx_prop_phong_ngu  ON properties(so_phong_ngu);

        -- FTS5 virtual table cho full-text search tiếng Việt
        CREATE VIRTUAL TABLE IF NOT EXISTS properties_fts USING fts5(
            id UNINDEXED,
            ten,
            dia_chi,
            phuong_xa,
            quan_huyen,
            tinh_thanh,
            loai,
            tien_ich,
            mo_ta,
            quy_hoach,
            content='properties',
            content_rowid='id',
            tokenize='unicode61'
        );

        -- Triggers giữ FTS đồng bộ với bảng chính
        CREATE TRIGGER IF NOT EXISTS prop_fts_insert AFTER INSERT ON properties BEGIN
            INSERT INTO properties_fts(rowid, id, ten, dia_chi, phuong_xa, quan_huyen,
                tinh_thanh, loai, tien_ich, mo_ta, quy_hoach)
            VALUES (NEW.id, NEW.id, NEW.ten, NEW.dia_chi, NEW.phuong_xa, NEW.quan_huyen,
                NEW.tinh_thanh, NEW.loai, NEW.tien_ich, NEW.mo_ta, NEW.quy_hoach);
        END;

        CREATE TRIGGER IF NOT EXISTS prop_fts_update AFTER UPDATE ON properties BEGIN
            INSERT INTO properties_fts(properties_fts, rowid, id, ten, dia_chi, phuong_xa,
                quan_huyen, tinh_thanh, loai, tien_ich, mo_ta, quy_hoach)
            VALUES ('delete', OLD.id, OLD.id, OLD.ten, OLD.dia_chi, OLD.phuong_xa,
                OLD.quan_huyen, OLD.tinh_thanh, OLD.loai, OLD.tien_ich, OLD.mo_ta, OLD.quy_hoach);
            INSERT INTO properties_fts(rowid, id, ten, dia_chi, phuong_xa, quan_huyen,
                tinh_thanh, loai, tien_ich, mo_ta, quy_hoach)
            VALUES (NEW.id, NEW.id, NEW.ten, NEW.dia_chi, NEW.phuong_xa, NEW.quan_huyen,
                NEW.tinh_thanh, NEW.loai, NEW.tien_ich, NEW.mo_ta, NEW.quy_hoach);
        END;

        CREATE TRIGGER IF NOT EXISTS prop_fts_delete AFTER DELETE ON properties BEGIN
            INSERT INTO properties_fts(properties_fts, rowid, id, ten, dia_chi, phuong_xa,
                quan_huyen, tinh_thanh, loai, tien_ich, mo_ta, quy_hoach)
            VALUES ('delete', OLD.id, OLD.id, OLD.ten, OLD.dia_chi, OLD.phuong_xa,
                OLD.quan_huyen, OLD.tinh_thanh, OLD.loai, OLD.tien_ich, OLD.mo_ta, OLD.quy_hoach);
        END;

        -- Trigger cập nhật updated_at
        CREATE TRIGGER IF NOT EXISTS prop_updated_at AFTER UPDATE ON properties BEGIN
            UPDATE properties SET updated_at = datetime('now','localtime') WHERE id = NEW.id;
        END;
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Initialized at {DB_PATH}")
