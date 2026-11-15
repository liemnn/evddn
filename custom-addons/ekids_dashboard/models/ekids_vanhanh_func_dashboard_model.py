# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date
import logging

_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import giaovien_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func: {e}")


class VanhanhFuncDashboard(models.AbstractModel):
    _inherit = 'ekids.dashboard_vanhanh'

    # =========================================================================
    # NHÓM HÀM ĐỊNH DẠNG SỐ TIỀN VNĐ & TRIỆU ĐỒNG CHO BIỂU ĐỒ
    # =========================================================================
    def _lamtron_nghin(self, sotien):
        """Làm tròn số tiền đến hàng nghìn đồng: 1,215,678,507 -> 1,215,679,000"""
        return int(round((sotien or 0.0) / 1000.0)) * 1000

    def _dinhdang_vnd(self, sotien, co_donvi=True):
        """Định dạng số tiền VNĐ làm tròn đến hàng nghìn: 1,000,000 vnđ"""
        so_chan_nghin = self._lamtron_nghin(sotien)
        chuoi = f"{so_chan_nghin:,}"
        return f"{chuoi} vnđ" if co_donvi else chuoi

    def _dinhdang_trieu_bieudo(self, sotien):
        """Định dạng triệu đồng có dấu phẩy thập phân để hiển thị trên đỉnh biểu đồ: 124,5tr"""
        val_tr = round((sotien or 0.0) / 1_000_000.0, 1)
        if val_tr == 0:
            val_tr = 0.0
        chuoi = f"{val_tr:,.1f}".replace('.', ',')
        return f"{chuoi}tr"

    def _sum_hocphi_thang(self, coso_id, nam_str, thang_str):
        if 'ekids.hocphi' not in self.env:
            return 0.0
        res = self.env['ekids.hocphi'].read_group(
            domain=[
                ('coso_id', '=', coso_id),
                ('thang_id.nam_id.name', '=', nam_str),
                ('thang_id.name', '=', thang_str),
            ],
            fields=['hocphi_phaidong'],
            groupby=[],
        )
        return res[0]['hocphi_phaidong'] if (res and res[0].get('hocphi_phaidong')) else 0.0

    def _sum_thu_khac_thang(self, coso_id, nam_str, thang_str):
        if 'ekids.chitieu_thu' not in self.env:
            return 0.0
        res = self.env['ekids.chitieu_thu'].read_group(
            domain=[
                ('coso_id', '=', coso_id),
                ('thang_id.nam_id.name', '=', nam_str),
                ('thang_id.name', '=', thang_str),
            ],
            fields=['tien'],
            groupby=[],
        )
        return res[0]['tien'] if (res and res[0].get('tien')) else 0.0

    def _sum_luong_thang(self, coso_id, nam_str, thang_str):
        if 'ekids.luong' not in self.env:
            return 0.0, 0.0
        res = self.env['ekids.luong'].read_group(
            domain=[
                ('coso_id', '=', coso_id),
                ('thang_id.nam_id.name', '=', nam_str),
                ('thang_id.name', '=', thang_str),
            ],
            fields=['tong_nhatruong_chi', 'nhatruong_thuho'],
            groupby=[],
        )
        if not res:
            return 0.0, 0.0
        luong = res[0].get('tong_nhatruong_chi') or 0.0
        thuho = res[0].get('nhatruong_thuho') or 0.0
        return luong, thuho

    def _sum_chi_khac_thang(self, coso_id, nam_str, thang_str):
        if 'ekids.chitieu_chi' not in self.env:
            return 0.0
        res = self.env['ekids.chitieu_chi'].read_group(
            domain=[
                ('coso_id', '=', coso_id),
                ('thang_id.nam_id.name', '=', nam_str),
                ('thang_id.name', '=', thang_str),
            ],
            fields=['tien'],
            groupby=[],
        )
        return res[0]['tien'] if (res and res[0].get('tien')) else 0.0

    def _tinh_taichinh_mot_thang(self, coso_id, nam, thang):
        nam_str = str(nam)
        thang_str = str(thang)

        hocphi = self._sum_hocphi_thang(coso_id, nam_str, thang_str)
        thukhac = self._sum_thu_khac_thang(coso_id, nam_str, thang_str)
        tong_thu = hocphi + thukhac

        luong, thuho = self._sum_luong_thang(coso_id, nam_str, thang_str)
        chikhac = self._sum_chi_khac_thang(coso_id, nam_str, thang_str)
        tong_chi = luong + thuho + chikhac
        loinhuan = tong_thu - tong_chi

        return {
            'hocphi': hocphi,
            'thukhac': thukhac,
            'tong_thu': tong_thu,
            'luong_va_bhxh': luong + thuho,
            'chikhac': chikhac,
            'tong_chi': tong_chi,
            'loinhuan': loinhuan,
        }

    def _dem_nghiphep_trong_ngay(self, model_name, coso_id, ngay):
        try:
            if model_name not in self.env:
                return 0
            rec_model = self.env[model_name]
            f_map = rec_model._fields
            domain = []

            if 'coso_id' in f_map:
                domain.append(('coso_id', '=', coso_id))
            elif 'hocsinh_id' in f_map:
                domain.append(('hocsinh_id.coso_id', '=', coso_id))
            elif 'giaovien_id' in f_map:
                domain.append(('giaovien_id.coso_id', '=', coso_id))

            if 'tu_ngay' in f_map and 'den_ngay' in f_map:
                domain += [('tu_ngay', '<=', ngay), ('den_ngay', '>=', ngay)]
            elif 'ngay_batdau' in f_map and 'ngay_ketthuc' in f_map:
                domain += [('ngay_batdau', '<=', ngay), ('ngay_ketthuc', '>=', ngay)]
            elif 'ngay_nghi' in f_map:
                domain.append(('ngay_nghi', '=', ngay))
            elif 'ngay' in f_map:
                domain.append(('ngay', '=', ngay))
            else:
                return 0

            return rec_model.search_count(domain)
        except Exception as e:
            _logger.warning(f"Lỗi đếm nghỉ phép {model_name}: {e}")
            return 0

    # =========================================================================
    # HÀM 1: 4 THẺ KPI TẦNG 1 (LÀM TRÒN ĐẾN NGHÌN ĐỒNG - ĐƠN VỊ vnđ)
    # =========================================================================
    def func_tinhtoan_kpi_vanhanh(self, coso_id, nam_taichinh, nam, thang, ngay, ngay_dau_thang, ngay_cuoi_thang):
        ds_cap_thang_ntc = self._ds_thang_cua_nam_taichinh(nam_taichinh)

        luyke_thu = 0.0
        luyke_chi = 0.0
        tc_thang_dang_xem = {'tong_thu': 0.0, 'tong_chi': 0.0, 'luong_va_bhxh': 0.0, 'chikhac': 0.0}

        for y_m, m_val in ds_cap_thang_ntc:
            tc_m = self._tinh_taichinh_mot_thang(coso_id, y_m, m_val)
            luyke_thu += tc_m['tong_thu']
            luyke_chi += tc_m['tong_chi']
            if y_m == nam and m_val == thang:
                tc_thang_dang_xem = tc_m
                break

        luyke_loinhuan = luyke_thu - luyke_chi
        tyle_loinhuan = round((luyke_loinhuan / luyke_thu * 100), 1) if luyke_thu > 0 else 0.0
        dau_tangtruong = "+" if tyle_loinhuan >= 0 else ""

        if nam == nam_taichinh and thang == 2:
            khoang_luyke = f"T02/{nam_taichinh}"
        elif nam == nam_taichinh:
            khoang_luyke = f"T02 - T{thang:02d}/{nam_taichinh}"
        else:
            khoang_luyke = f"T02/{nam_taichinh} - T{thang:02d}/{nam}"

        tong_hocsinh = hocsinh_util.sum_tong_hocsinh_trong_thang(self, [coso_id], nam, thang)
        hocsinh_nghi_thang = hocsinh_util.sum_tong_hocsinh_nghi_trong_thang(self, [coso_id], nam, thang)
        hocsinh_moi_thang = hocsinh_util.sum_tong_hocsinh_moi_trong_thang(self, [coso_id], nam, thang)
        tong_giaovien = giaovien_util.sum_tong_giaovien_trong_thang(self, [coso_id], nam, thang)

        hs_vang_homnay = self._dem_nghiphep_trong_ngay('ekids.hocsinh_nghiphep', coso_id, ngay)
        gv_nghi_homnay = self._dem_nghiphep_trong_ngay('ekids.giaovien_nghiphep', coso_id, ngay)

        return {
            'ngay_hientai_str': ngay.strftime('%d/%m/%Y'),
            'khoang_thang_luyke': khoang_luyke,
            'tong_doanh_thu_nam': self._dinhdang_vnd(luyke_thu),
            'tong_chi_nam': self._dinhdang_vnd(luyke_chi),
            'loi_nhuan_nam': self._dinhdang_vnd(luyke_loinhuan, co_donvi=False),
            'don_vi_loi_nhuan': 'vnđ',
            'tang_truong_nam': f"{dau_tangtruong}{tyle_loinhuan}% LN",

            'tong_hocsinh': tong_hocsinh,
            'hocsinh_moi_thang': hocsinh_moi_thang,
            'hocsinh_nghi_thang': hocsinh_nghi_thang,
            'hocsinh_vang_homnay': hs_vang_homnay,

            'tong_giaovien': tong_giaovien,
            'giaovien_nghi_homnay': gv_nghi_homnay,

            'tong_chi_thang': self._dinhdang_vnd(tc_thang_dang_xem['tong_chi'], co_donvi=False),
            'chi_luong_thang': self._dinhdang_vnd(tc_thang_dang_xem['luong_va_bhxh']),
            'chi_khac_thang': self._dinhdang_vnd(tc_thang_dang_xem['chikhac']),
        }

    # =========================================================================
    # HÀM 2: BIỂU ĐỒ TRÒN DONUT CƠ CẤU HỌC PHÍ THÁNG ĐANG CHỌN
    # - Tổng học phí = hocphi (gốc)
    # - Miễn giảm = hocphi_giam (hiển thị riêng, KHÔNG tính vào % biểu đồ thu)
    # - Biểu đồ Donut tính 100% trên Tổng tiền cần thu (da_thu + chua_thu)
    # =========================================================================
    def func_tinhtoan_cocau_hocphi_thang(self, coso_id, nam, thang, ngay_dau_thang, ngay_cuoi_thang):
        nam_str = str(nam)
        thang_str = str(thang)

        hp_recs = self.env['ekids.hocphi'].search([
            ('coso_id', '=', coso_id),
            ('thang_id.nam_id.name', '=', nam_str),
            ('thang_id.name', '=', thang_str),
        ]) if 'ekids.hocphi' in self.env else []

        da_thu = 0.0
        chua_thu = 0.0
        mien_giam = 0.0

        # Trạng thái đã đóng tiền thực tế trên model ekids.hocphi:
        trangthai_dathu = {'10', '11', '12', '3'}

        for hp in hp_recs:
            phai_dong = hp.hocphi_phaidong or 0.0
            tien_giam = hp.hocphi_giam or 0.0

            mien_giam += tien_giam
            if hp.trangthai in trangthai_dathu:
                da_thu += phai_dong
            else:
                chua_thu += phai_dong

        # Tổng lượng tiền thực tế cần thu của trung tâm = Đã thu + Chưa thu
        tong_can_thu = da_thu + chua_thu
        # Tổng học phí trước miễn giảm
        tong_hocphi = tong_can_thu + mien_giam

        return {
            'tong_hocphi_str': self._dinhdang_vnd(tong_hocphi),
            'tong_can_thu_str': self._dinhdang_vnd(tong_can_thu),

            'da_thu_val': self._lamtron_nghin(da_thu),
            'da_thu_str': self._dinhdang_vnd(da_thu),
            'tyle_da_thu': round(da_thu / tong_can_thu * 100, 1) if tong_can_thu > 0 else 0,
            'tyle_da_thu_tron': round(da_thu / tong_can_thu * 100) if tong_can_thu > 0 else 0,

            'chua_thu_val': self._lamtron_nghin(chua_thu),
            'chua_thu_str': self._dinhdang_vnd(chua_thu),
            'tyle_chua_thu': round(chua_thu / tong_can_thu * 100, 1) if tong_can_thu > 0 else 0,

            'mien_giam_str': self._dinhdang_vnd(mien_giam),
        }

    # =========================================================================
    # HÀM 3: DỮ LIỆU 4 BIỂU ĐỒ THEO NĂM TÀI CHÍNH (ĐƠN VỊ TRIỆU ĐỒNG: 124,5tr)
    # =========================================================================
    def func_tinhtoan_bieudo_taichinh_nam(self, coso_id, nam_taichinh, nam, thang):
        today = fields.Date.context_today(self)
        ds_cap_thang_ntc = self._ds_thang_cua_nam_taichinh(nam_taichinh)

        nhan_thang = []
        cot_tong_thu, cot_tong_chi, duong_loi_nhuan = [], [], []
        nhan_thu, nhan_chi, nhan_ln = [], [], []
        full_thu, full_chi, full_ln = [], [], []

        cot_thu_hocphi, cot_chi_luong, cot_nguon_chi = [], [], []
        nhan_hp, nhan_luong, nhan_chikhac = [], [], []
        full_hp, full_luong, full_chikhac = [], [], []

        for y_m, m_val in ds_cap_thang_ntc:
            if (y_m, m_val) > (today.year, today.month):
                break

            tc = self._tinh_taichinh_mot_thang(coso_id, y_m, m_val)
            thu_vnd = self._lamtron_nghin(tc['tong_thu'])
            chi_vnd = self._lamtron_nghin(tc['tong_chi'])
            ln_vnd = self._lamtron_nghin(tc['loinhuan'])
            hp_vnd = self._lamtron_nghin(tc['hocphi'])
            luong_vnd = self._lamtron_nghin(tc['luong_va_bhxh'])
            chikhac_vnd = self._lamtron_nghin(tc['chikhac'])

            nhan_thang.append(f"T{m_val}")

            cot_tong_thu.append(thu_vnd)
            cot_tong_chi.append(chi_vnd)
            duong_loi_nhuan.append(ln_vnd)

            nhan_thu.append(self._dinhdang_trieu_bieudo(thu_vnd))
            nhan_chi.append(self._dinhdang_trieu_bieudo(chi_vnd))
            nhan_ln.append(self._dinhdang_trieu_bieudo(ln_vnd))

            full_thu.append(self._dinhdang_vnd(thu_vnd))
            full_chi.append(self._dinhdang_vnd(chi_vnd))
            full_ln.append(self._dinhdang_vnd(ln_vnd))

            cot_thu_hocphi.append(hp_vnd)
            nhan_hp.append(self._dinhdang_trieu_bieudo(hp_vnd))
            full_hp.append(self._dinhdang_vnd(hp_vnd))

            cot_chi_luong.append(luong_vnd)
            nhan_luong.append(self._dinhdang_trieu_bieudo(luong_vnd))
            full_luong.append(self._dinhdang_vnd(luong_vnd))

            cot_nguon_chi.append(chikhac_vnd)
            nhan_chikhac.append(self._dinhdang_trieu_bieudo(chikhac_vnd))
            full_chikhac.append(self._dinhdang_vnd(chikhac_vnd))

        return {
            'nhan_thang': nhan_thang,
            'tonghop_taichinh': {
                'cot_thu': cot_tong_thu,
                'cot_chi': cot_tong_chi,
                'duong_loinhuan': duong_loi_nhuan,
                'nhan_thu': nhan_thu,
                'nhan_chi': nhan_chi,
                'nhan_ln': nhan_ln,
                'full_thu': full_thu,
                'full_chi': full_chi,
                'full_ln': full_ln,
            },
            'thu_hocphi': {
                'cot': cot_thu_hocphi,
                'duong': cot_thu_hocphi,
                'nhan': nhan_hp,
                'full': full_hp,
            },
            'chi_luong': {
                'cot': cot_chi_luong,
                'duong': cot_chi_luong,
                'nhan': nhan_luong,
                'full': full_luong,
            },
            'nguon_chi': {
                'cot': cot_nguon_chi,
                'nhan': nhan_chikhac,
                'full': full_chikhac,
            },
        }

    # =========================================================================
    # HÀM 4: CHI TIÊU VẬN HÀNH TRONG THÁNG ĐƯỢC CHỌN (LÀM TRÒN NGHÌN ĐỒNG)
    # =========================================================================
    def _lay_ten_khoan_chi(self, rec):
        f_map = rec._fields
        bo_qua = {'coso_id', 'thang_id', 'nam_id', 'create_uid', 'write_uid', 'company_id', 'currency_id'}
        for fname, field in f_map.items():
            if field.type == 'many2one' and fname not in bo_qua:
                val = getattr(rec, fname, False)
                if val and hasattr(val, 'display_name') and val.display_name:
                    return val.display_name

        for fname in ('name', 'ten', 'noidung', 'lydo', 'ghichu', 'desc', 'display_name'):
            if fname in f_map:
                val = getattr(rec, fname, False)
                if val:
                    return str(val).strip()

        return 'Khoản chi khác'

    def func_tinhtoan_khoanchi_noibat(self, coso_id, nam, thang, ngay_dau_thang, ngay_cuoi_thang):
        nam_str = str(nam)
        thang_str = str(thang)

        chi_recs = self.env['ekids.chitieu_chi'].search([
            ('coso_id', '=', coso_id),
            ('thang_id.nam_id.name', '=', nam_str),
            ('thang_id.name', '=', thang_str),
        ]) if 'ekids.chitieu_chi' in self.env else []

        tong_chitieu_thang = sum(r.tien for r in chi_recs)

        nhom_chi = {}
        for r in chi_recs:
            ten_nhom = self._lay_ten_khoan_chi(r)
            nhom_chi[ten_nhom] = nhom_chi.get(ten_nhom, 0.0) + (r.tien or 0.0)

        top_items = sorted(nhom_chi.items(), key=lambda x: x[1], reverse=True)[:4]
        bang_mau = ['#ef4444', '#f59e0b', '#2563eb', '#8b5cf6']
        ds_khoanchi = []

        for idx, (ten, sotien) in enumerate(top_items):
            tyle = round(sotien / tong_chitieu_thang * 100) if tong_chitieu_thang > 0 else 0
            ds_khoanchi.append({
                'ten': ten,
                'tyle': tyle,
                'mau': bang_mau[idx % len(bang_mau)],
                'giatri_str': self._dinhdang_vnd(sotien),
            })

        return {
            'tong_chitieu_thang_str': self._dinhdang_vnd(tong_chitieu_thang),
            'ds_khoanchi': ds_khoanchi,
        }