# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date
import calendar


class VanhanhDashboard(models.AbstractModel):
    _name = 'ekids.dashboard_vanhanh'
    _description = 'Dashboard Quản trị Hoạt động Trung tâm'

    @api.model
    def get_dashboard_data(self, coso_id=None, thang_nam=None):
        ngay_hientai = fields.Date.context_today(self)

        # 1. XÁC ĐỊNH DANH SÁCH CƠ SỞ & CƠ SỞ ĐANG CHỌN
        ds_coso = []
        user = self.env.user
        if 'ekids.coso' in self.env:
            if hasattr(user, 'coso_ids') and user.coso_ids and not user.has_group('base.group_system'):
                coso_recs = user.coso_ids
            else:
                coso_recs = self.env['ekids.coso'].search([], order='id asc')

            for cs in coso_recs:
                ds_coso.append({'id': str(cs.id), 'ten': cs.name})
        else:
            ds_coso = [
                {'id': '1', 'ten': 'Trung tâm eKids Cơ sở 1'},
                {'id': '2', 'ten': 'Trung tâm eKids Cơ sở 2'},
            ]

        ds_coso_id_hople = [c['id'] for c in ds_coso]
        if not coso_id or str(coso_id) not in ds_coso_id_hople:
            coso_macdinh = str(user.coso_id.id) if (hasattr(user, 'coso_id') and user.coso_id) else ''
            coso_id_str = coso_macdinh if coso_macdinh in ds_coso_id_hople else (ds_coso_id_hople[0] if ds_coso_id_hople else '0')
        else:
            coso_id_str = str(coso_id)

        coso_id_int = int(coso_id_str)

        # 2. XÁC ĐỊNH DANH SÁCH THÁNG & THÁNG ĐANG CHỌN
        ds_thang = []
        thang_hientai_ym = ngay_hientai.strftime('%Y-%m')
        for m in range(1, 13):
            val = f"{ngay_hientai.year}-{m:02d}"
            nhan = f"Tháng {m:02d}/{ngay_hientai.year}" + (" (Tháng này)" if val == thang_hientai_ym else "")
            ds_thang.append({'giatri': val, 'nhan': nhan})

        ds_thang_hople = [m['giatri'] for m in ds_thang]
        if not thang_nam or thang_nam not in ds_thang_hople:
            thang_nam = thang_hientai_ym

        nam, thang = map(int, thang_nam.split('-'))
        ngay_dau_thang = date(nam, thang, 1)
        ngay_cuoi_thang = date(nam, thang, calendar.monthrange(nam, thang)[1])
        ngay = ngay_hientai if (nam == ngay_hientai.year and thang == ngay_hientai.month) else ngay_cuoi_thang

        # 3. GỌI CÁC HÀM TÍNH TOÁN TỪNG PHẦN
        kpi_data = self.func_tinhtoan_kpi_vanhanh(
            coso_id=coso_id_int,
            nam=nam,
            thang=thang,
            ngay=ngay,
            ngay_dau_thang=ngay_dau_thang,
            ngay_cuoi_thang=ngay_cuoi_thang,
        )

        hocphi_thang = self.func_tinhtoan_cocau_hocphi_thang(
            coso_id=coso_id_int,
            nam=nam,
            thang=thang,
            ngay_dau_thang=ngay_dau_thang,
            ngay_cuoi_thang=ngay_cuoi_thang,
        )

        bieudo_data = self.func_tinhtoan_bieudo_taichinh_nam(
            coso_id=coso_id_int,
            nam=nam,
            thang=thang,
        )

        khoanchi_noibat = self.func_tinhtoan_khoanchi_noibat(
            coso_id=coso_id_int,
            nam=nam,
            thang=thang,
            ngay_dau_thang=ngay_dau_thang,
            ngay_cuoi_thang=ngay_cuoi_thang,
        )

        return {
            'ds_coso': ds_coso,
            'coso_id': coso_id_str,
            'ds_thang': ds_thang,
            'thang_nam': thang_nam,
            'thang': thang,
            'nam': nam,
            'kpi': kpi_data,
            'hocphi_thang': hocphi_thang,
            'bieudo': bieudo_data,
            'khoanchi_noibat': khoanchi_noibat,
        }

    # -------------------------------------------------------------------------
    # HÀM 1: 4 THẺ KPI TẦNG 1
    # -------------------------------------------------------------------------
    def func_tinhtoan_kpi_vanhanh(self, coso_id, nam, thang, ngay, ngay_dau_thang, ngay_cuoi_thang):
        # TODO: Thay bằng query thực tế lũy kế từ 01/01/{nam} đến ngày {ngay} và trong tháng [ngay_dau_thang, ngay_cuoi_thang]
        return {
            'ngay_hientai_str': ngay.strftime('%d/%m/%Y'),
            'tong_doanh_thu_nam': '4,512 tỷ',
            'tong_chi_nam': '3,266 tỷ',
            'loi_nhuan_nam': '1,246',
            'don_vi_loi_nhuan': 'tỷ đ',
            'tang_truong_nam': '+14.2%',

            'tong_hocsinh': 126,
            'hocsinh_moi_thang': 6,
            'hocsinh_nghi_thang': 2,
            'hocsinh_vang_homnay': 8,

            'tong_giaovien': 30,
            'giaovien_nghi_homnay': 2,

            'tong_chi_thang': '312,8',
            'chi_luong_thang': '248,6 tr',
            'chi_khac_thang': '64,2 tr',
        }

    # -------------------------------------------------------------------------
    # HÀM 2: BIỂU ĐỒ TRÒN DONUT CƠ CẤU HỌC PHÍ THÁNG ĐANG CHỌN
    # -------------------------------------------------------------------------
    def func_tinhtoan_cocau_hocphi_thang(self, coso_id, nam, thang, ngay_dau_thang, ngay_cuoi_thang):
        # TODO: Thay bằng query tổng hợp ekids.hocphi trong tháng
        da_thu = 412.50
        chua_thu = 107.50
        mien_giam = 28.45
        tong_hocphi = round(da_thu + chua_thu + mien_giam, 2)

        return {
            'tong_hocphi_str': f"{tong_hocphi:,.2f}".replace('.', ',') + " tr",

            'da_thu_val': da_thu,
            'da_thu_str': f"{da_thu:,.2f}".replace('.', ',') + " tr",
            'tyle_da_thu': round(da_thu / tong_hocphi * 100, 1) if tong_hocphi else 0,
            'tyle_da_thu_tron': round(da_thu / tong_hocphi * 100) if tong_hocphi else 0,

            'chua_thu_val': chua_thu,
            'chua_thu_str': f"{chua_thu:,.2f}".replace('.', ',') + " tr",
            'tyle_chua_thu': round(chua_thu / tong_hocphi * 100, 1) if tong_hocphi else 0,

            'mien_giam_val': mien_giam,
            'mien_giam_str': f"{mien_giam:,.2f}".replace('.', ',') + " tr",
            'tyle_mien_giam': round(mien_giam / tong_hocphi * 100, 1) if tong_hocphi else 0,
        }

    # -------------------------------------------------------------------------
    # HÀM 3: DỮ LIỆU BIỂU ĐỒ TỪ T1 -> THÁNG HIỆN TẠI
    # -------------------------------------------------------------------------
    def func_tinhtoan_bieudo_taichinh_nam(self, coso_id, nam, thang):
        today = fields.Date.context_today(self)
        thang_gioi_han = today.month if nam == today.year else (12 if nam < today.year else 0)

        # Dữ liệu mẫu 12 tháng (Đơn vị: Triệu đồng)
        mau_tong_thu = [322, 297, 365, 386, 398, 418, 434, 445, 466, 487, 431, 450]
        mau_tong_chi = [240, 226, 267, 278, 286, 298, 309, 314, 325, 337, 313, 320]
        mau_thu_hocphi = [310, 285, 350, 370, 380, 400, 415, 425, 445, 465, 412, 430]
        mau_chi_luong = [195, 190, 210, 215, 222, 228, 234, 238, 242, 245, 249, 252]
        mau_chi_vanhanh = [45, 36, 57, 63, 64, 70, 75, 76, 83, 92, 64, 68]

        nhan_thang = []
        cot_tong_thu, cot_tong_chi, duong_loi_nhuan = [], [], []
        cot_thu_hocphi, cot_chi_luong, cot_nguon_chi = [], [], []

        for m in range(1, thang_gioi_han + 1):
            thu = mau_tong_thu[m - 1]
            chi = mau_tong_chi[m - 1]
            loinhuan = round(thu - chi, 1)

            nhan_thang.append(f"T{m}")
            cot_tong_thu.append(thu)
            cot_tong_chi.append(chi)
            duong_loi_nhuan.append(loinhuan)

            cot_thu_hocphi.append(mau_thu_hocphi[m - 1])
            cot_chi_luong.append(mau_chi_luong[m - 1])
            cot_nguon_chi.append(mau_chi_vanhanh[m - 1])

        return {
            'nhan_thang': nhan_thang,
            # Biểu đồ chính Tầng 2: 2 cột (Tổng thu, Tổng chi) + 1 đường (Lợi nhuận)
            'tonghop_taichinh': {
                'cot_thu': cot_tong_thu,
                'cot_chi': cot_tong_chi,
                'duong_loinhuan': duong_loi_nhuan,
            },
            # Tầng 3 - Hàng 1: Thu học phí & Lương thực chi (cột + đường)
            'thu_hocphi': {'cot': cot_thu_hocphi, 'duong': cot_thu_hocphi},
            'chi_luong': {'cot': cot_chi_luong, 'duong': cot_chi_luong},
            # Tầng 3 - Hàng 2: Nguồn chi vận hành theo tháng (chỉ biểu đồ cột)
            'nguon_chi': {'cot': cot_nguon_chi},
        }

    # -------------------------------------------------------------------------
    # HÀM 4: KHOẢN CHI NỔI BẬT TRONG THÁNG (GÓC DƯỚI BÊN PHẢI)
    # -------------------------------------------------------------------------
    def func_tinhtoan_khoanchi_noibat(self, coso_id, nam, thang, ngay_dau_thang, ngay_cuoi_thang):
        return {
            'tong_chi_khac_str': '64,2 tr',
            'ds_khoanchi': [
                {'ten': 'Thực phẩm bếp', 'tyle': 54, 'mau': '#ef4444', 'giatri_str': '34,5 tr'},
                {'ten': 'Mặt bằng, điện', 'tyle': 28, 'mau': '#f59e0b', 'giatri_str': '18,2 tr'},
                {'ten': 'Giáo cụ, khác', 'tyle': 18, 'mau': '#2563eb', 'giatri_str': '11,5 tr'},
            ]
        }