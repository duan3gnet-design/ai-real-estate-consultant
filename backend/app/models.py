from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class PropertyType(str, Enum):
    can_ho = "Căn hộ chung cư"
    nha_pho = "Nhà phố"
    biet_thu = "Biệt thự"
    dat_nen = "Đất nền"
    shophouse = "Shophouse"
    van_phong = "Văn phòng"
    mat_bang = "Mặt bằng thương mại"
    kho_xuong = "Kho / Xưởng"
    khach_san = "Khách sạn / Căn hộ dịch vụ"


class PropertyStatus(str, Enum):
    dang_ban = "Đang bán"
    dang_cho_thue = "Đang cho thuê"
    ban_va_cho_thue = "Bán & Cho thuê"
    da_ban = "Đã bán"
    da_cho_thue = "Đã cho thuê"
    tam_khoa = "Tạm khóa"


class LegalStatus(str, Enum):
    so_do = "Sổ đỏ (GCNQSDĐ)"
    so_hong = "Sổ hồng (GCNQSH)"
    hop_dong = "Hợp đồng mua bán"
    giay_to_hop_le = "Giấy tờ hợp lệ khác"
    chua_co_so = "Chưa có sổ"
    dang_lam_so = "Đang làm sổ"


class PropertyCreate(BaseModel):
    # Thông tin cơ bản
    ma_bds: Optional[str] = None
    ten: str = Field(..., min_length=1, description="Tên BĐS")
    loai: PropertyType
    trang_thai: PropertyStatus = PropertyStatus.dang_ban

    # Vị trí
    dia_chi: str = Field(..., description="Địa chỉ đầy đủ")
    phuong_xa: Optional[str] = None
    quan_huyen: Optional[str] = None
    tinh_thanh: str = Field(..., description="Tỉnh/Thành phố")
    vi_do: Optional[float] = None
    kinh_do: Optional[float] = None

    # Thông số vật lý
    dien_tich_dat: Optional[float] = Field(None, description="Diện tích đất (m²)")
    dien_tich_san: Optional[float] = Field(None, description="Diện tích sàn / sử dụng (m²)")
    so_tang: Optional[int] = None
    so_phong_ngu: Optional[int] = None
    so_toilet: Optional[int] = None
    huong: Optional[str] = None
    mat_tien: Optional[float] = Field(None, description="Chiều rộng mặt tiền (m)")
    duong_vao: Optional[float] = Field(None, description="Chiều rộng đường vào (m)")

    # Tài chính
    gia_ban: Optional[float] = Field(None, description="Giá bán (triệu VNĐ)")
    gia_thue: Optional[float] = Field(None, description="Giá thuê (triệu VNĐ/tháng)")
    gia_mua_vao: Optional[float] = Field(None, description="Giá mua vào (triệu VNĐ)")
    nam_mua: Optional[int] = None
    phi_quan_ly: Optional[float] = Field(None, description="Phí quản lý (triệu VNĐ/tháng)")

    # Pháp lý
    phap_ly: Optional[LegalStatus] = None
    nam_xay_dung: Optional[int] = None
    quy_hoach: Optional[str] = None

    # Tiện ích & Mô tả
    tien_ich: Optional[str] = Field(None, description="Tiện ích xung quanh, nội thất")
    mo_ta: Optional[str] = Field(None, description="Mô tả chi tiết")
    ghi_chu_noi_bo: Optional[str] = Field(None, description="Ghi chú nội bộ")

    # Liên hệ
    nguoi_phu_trach: Optional[str] = None
    so_dien_thoai: Optional[str] = None

    # Ảnh
    anh_urls: Optional[str] = Field(None, description="URLs ảnh, phân cách bằng dấu phẩy")


class PropertyUpdate(PropertyCreate):
    ten: Optional[str] = None
    loai: Optional[PropertyType] = None
    dia_chi: Optional[str] = None
    tinh_thanh: Optional[str] = None


class PropertyResponse(PropertyCreate):
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PropertyFilter(BaseModel):
    loai: Optional[PropertyType] = None
    trang_thai: Optional[PropertyStatus] = None
    tinh_thanh: Optional[str] = None
    quan_huyen: Optional[str] = None
    gia_ban_min: Optional[float] = None
    gia_ban_max: Optional[float] = None
    gia_thue_min: Optional[float] = None
    gia_thue_max: Optional[float] = None
    dien_tich_min: Optional[float] = None
    dien_tich_max: Optional[float] = None
    so_phong_ngu_min: Optional[int] = None
    phap_ly: Optional[LegalStatus] = None
    page: int = 1
    page_size: int = 20


class ImportResult(BaseModel):
    total: int
    success: int
    failed: int
    errors: list[str] = []
