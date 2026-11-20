# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date, timedelta
import calendar
import logging

_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import giaovien_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
    from odoo.addons.ekids_func import kehoach_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func: {e}")

class GiaovienDashboard(models.AbstractModel):
    _name = 'ekids.dashboard_giaovien'
    _description = 'Dashboard Cá nhân Giáo viên Can thiệp'

    # =========================================================================
    # NHÓM 1: HÀM TIỆN ÍCH ĐỊNH DẠNG & THỜI GIAN
    # =========================================================================
    def _xacdinh_nam_taichinh(self, nam_thucte, thang_thucte):
        return nam_thucte - 1 if thang_thucte == 1 else nam_thucte

    def _ds_thang_cua_nam_taichinh(self, nam_taichinh):
        ds = [(nam_taichinh, m) for m in range(2, 13)]
        ds.append((nam_taichinh + 1, 1))
        return ds

    def _lamtron_nghin(self, sotien):
        return int(round((sotien or 0.0) / 1000.0)) * 1000

    def _dinhdang_vnd(self, sotien, co_donvi=True):
        chuoi = f"{self._lamtron_nghin(sotien):,}"
        return f"{chuoi} vnđ" if co_donvi else chuoi

    def _dinhdang_trieu_bieudo(self, sotien):
        giatri_tr = round((sotien or 0.0) / 1_000_000.0, 1)
        if giatri_tr == 0:
            giatri_tr = 0.0
        return f"{giatri_tr:,.1f}".replace('.', ',') + "tr"



    def _lay_anh_giaovien(self, gv):
        """Trích xuất chuỗi base64 avatar từ giáo viên hoặc user liên kết"""
        for ten_truong in ('image_128', 'avatar_128', 'image_1920', 'image'):
            if ten_truong in gv._fields and getattr(gv, ten_truong, False):
                giatri = getattr(gv, ten_truong)
                return giatri.decode('utf-8') if isinstance(giatri, bytes) else str(giatri)

        if getattr(gv, 'user_id', False):
            ban_ghi_user = gv.user_id.sudo()
            for ten_truong in ('avatar_128', 'image_128'):
                if ten_truong in ban_ghi_user._fields and getattr(ban_ghi_user, ten_truong, False):
                    giatri = getattr(ban_ghi_user, ten_truong)
                    return giatri.decode('utf-8') if isinstance(giatri, bytes) else str(giatri)
        return False

    # =========================================================================
    # NHÓM 2: CÁC HÀM ĐỘC LẬP TÍNH TOÁN TỪNG CHỈ SỐ (ƯU TIÊN SEARCH_COUNT & READ_GROUP)
    # =========================================================================
    def _lay_ds_hocsinh_phutrach(self, gv_id):
        """
        Chỉ search trực tiếp trên ekids.kehoach_ketluan:
        - Học sinh đang theo học (hocsinh_id.trangthai = '1')
        - Kết luận đang cho phép lập kế hoạch (trangthai = '1')
        - Được giao cho giáo viên (gv_canthiep_ids in [gv_id])
        """

        if 'ekids.kehoach_ketluan' not in self.env:
            return {}

        kl_model = self.env['ekids.kehoach_ketluan'].sudo()
        sapxep = 'ngay desc, id desc' if 'ngay' in kl_model._fields else (
            'tu_ngay desc, id desc' if 'tu_ngay' in kl_model._fields else 'id desc'
        )
        domain = kl_model.search_read(
            domain=[
                ('hocsinh_id.trangthai', '=', '1'),
                ('trangthai', '=', '1'),
                ('gv_canthiep_ids', 'in', [gv_id]),
            ],
            fields=['hocsinh_id'],
            order=sapxep,
        )

        ds_hs_phutrach = {}
        for dong in domain:
            hs_tuple = dong.get('hocsinh_id')
            if hs_tuple and hs_tuple[0] not in ds_hs_phutrach:
                hs_id = hs_tuple[0]
                ds_hs_phutrach[hs_id] = {
                    'id': hs_id,
                    'ten': hs_tuple[1],
                    'so_ca': 0,
                }
        return ds_hs_phutrach

    def _tao_domain_kehoach_thang(self, ds_hs_id, ngay_dau_thang, ngay_20_thang):
        """Domain cơ bản cho kế hoạch đã lập giao khoảng mùng 01 -> 20 của tháng"""
        return [
            ('hocsinh_id', 'in', ds_hs_id),
            ('tu_ngay', '<=', ngay_20_thang),
            ('den_ngay', '>=', ngay_dau_thang),
        ]

    def _dem_kehoach_dang_canthiep(self, giaovien_id):
        """Đếm số lượng kế hoạch đang can thiệp (trangthai = '1') bằng search_count"""

        domain = [('trangthai', '=', kehoach_util.KEHOACH_DANG_CANTHIEP)
            ,('gv_lapkehoach_id', '=', giaovien_id)
            ,('hocsinh_id.trangthai', '=', '1')]
        return self.env['ekids.kehoach'].sudo().search_count(domain)

    def _dem_kehoach_dang_co(self, giaovien_id):
        """Đếm số lượng kế hoạch đang can thiệp (trangthai = '1') bằng search_count"""

        domain = [('trangthai', 'in', ['0','2','1'])
            ,('gv_lapkehoach_id', '=', giaovien_id)
            ,('hocsinh_id.trangthai', '=', '1')]
        return self.env['ekids.kehoach'].sudo().search_count(domain)

    def _dem_kehoach_soan_choduyet(self, ds_hs_id, ngay_dau_thang, ngay_20_thang):
        """Đếm số lượng kế hoạch đang soạn thảo hoặc chờ duyệt ('0', '2') bằng search_count"""
        if not ds_hs_id:
            return 0
        domain = self._tao_domain_kehoach_thang(ds_hs_id, ngay_dau_thang, ngay_20_thang) + [('trangthai', 'in', ['0', '2'])]
        return self.env['ekids.kehoach'].sudo().search_count(domain)

    def _dem_kehoach_sap_hethan(self, ds_hs_id, ngay_dau_thang, ngay_20_thang, ngay_xet):
        """Đếm số kế hoạch đang can thiệp sắp hết hạn trong vòng 10 ngày tới bằng search_count"""
        if not ds_hs_id:
            return 0
        ngay_sap_hethan = ngay_xet + timedelta(days=10)
        domain = self._tao_domain_kehoach_thang(ds_hs_id, ngay_dau_thang, ngay_20_thang) + [
            ('trangthai', '=', '1'),
            ('den_ngay', '>=', ngay_xet),
            ('den_ngay', '<=', ngay_sap_hethan),
        ]
        return self.env['ekids.kehoach'].sudo().search_count(domain)

    def _lay_tap_hs_da_lap_kehoach(self, ds_hs_id, ngay_dau_thang, ngay_20_thang):
        """Lấy tập ID học sinh đã có ít nhất 1 kế hoạch (mọi trạng thái) bằng _read_group"""
        if not ds_hs_id:
            return set()
        domain = self._tao_domain_kehoach_thang(ds_hs_id, ngay_dau_thang, ngay_20_thang)
        nhom_hs = self.env['ekids.kehoach'].sudo()._read_group(
            domain=domain,
            groupby=['hocsinh_id'],
            aggregates=['__count'],
        )
        return {hs_rec.id for hs_rec, _ in nhom_hs if hs_rec}

    def _lay_bang_capnhat_tuan(self, gv_id, ds_hs_phutrach, tap_hs_da_lap_kh, tu_ngay_tuan, den_ngay_tuan, nam, thang):
        """
        Lấy tất cả kế hoạch mà giáo viên đang trực tiếp can thiệp:
        - gv_lapkehoach_id == gv_id
        - trangthai == '1' (Đang can thiệp)
        - hocsinh_id.trangthai == '1' (Đang theo học)
        Kèm theo các học sinh phụ trách chưa có kế hoạch nào để theo dõi.
        """
        ds_kh = self.env['ekids.kehoach'].sudo().search_read(
            domain=[
                ('gv_lapkehoach_id', '=', gv_id),
                ('trangthai', '=', '1'),
                ('hocsinh_id.trangthai', '=', '1'),
            ],
            fields=['id', 'name', 'hocsinh_id'],
            order='hocsinh_id asc, id asc',
        )

        # Kiểm tra ngày cập nhật kết quả mới nhất trong tuần hiện tại bằng _read_group
        bando_ngay_capnhat = {}
        ds_kh_id = [r['id'] for r in ds_kh]
        if ds_kh_id:
            nhom_kq = self.env['ekids.kehoach_ketqua2muctieu'].sudo()._read_group(
                domain=[
                    ('kehoach_muctieu_id.kehoach_linhvuc_id.kehoach_id', 'in', ds_kh_id),
                    ('ngay', '>=', tu_ngay_tuan),
                    ('ngay', '<=', den_ngay_tuan),
                    '|',
                    ('is_giaovien_capnhat', '=', True),
                    ('trangthai', 'in', ['0', '1', '2']),
                ],
                groupby=['kehoach_muctieu_id'],
                aggregates=['ngay:max'],
            )
            for muctieu, ngay_lonnhat in nhom_kq:
                if muctieu and ngay_lonnhat:
                    kh_id = muctieu.kehoach_linhvuc_id.kehoach_id.id
                    if kh_id not in bando_ngay_capnhat or ngay_lonnhat > bando_ngay_capnhat[kh_id]:
                        bando_ngay_capnhat[kh_id] = ngay_lonnhat

        # Gom nhóm kế hoạch đang can thiệp theo từng học sinh
        kh_theo_hs = {}
        ten_hs_tu_kh = {}
        so_kh_da_capnhat = 0
        so_kh_chua_capnhat = 0

        for r in ds_kh:
            hs_tuple = r.get('hocsinh_id')
            if not hs_tuple:
                continue
            hs_id, hs_ten = hs_tuple[0], hs_tuple[1]
            ten_hs_tu_kh[hs_id] = hs_ten

            kh_id = r['id']
            ngay_cuoi = bando_ngay_capnhat.get(kh_id)
            da_capnhat = bool(ngay_cuoi)

            if da_capnhat:
                so_kh_da_capnhat += 1
            else:
                so_kh_chua_capnhat += 1

            kh_theo_hs.setdefault(hs_id, []).append({
                'kehoach_id': kh_id,
                'ten_kehoach': r.get('name') or f"Kế hoạch T{thang:02d}/{nam}",
                'da_capnhat': da_capnhat,
                'ngay_capnhat': ngay_cuoi.strftime('%d/%m/%Y') if ngay_cuoi else '',
            })

        # Tổng hợp danh sách hiển thị (gồm tất cả học sinh có KH đang can thiệp + học sinh phụ trách chưa có KH)
        tap_tatca_hs_id = set(ds_hs_phutrach.keys()) | set(kh_theo_hs.keys())
        ds_tonghop_hs = []
        for hs_id in tap_tatca_hs_id:
            thongtin = ds_hs_phutrach.get(hs_id)
            ds_tonghop_hs.append({
                'id': hs_id,
                'ten': thongtin['ten'] if thongtin else ten_hs_tu_kh.get(hs_id, ''),
                'so_ca': thongtin['so_ca'] if thongtin else 0,
            })

        ds_dong_hocsinh = []
        for thongtin_hs in sorted(ds_tonghop_hs, key=lambda x: x['ten'] or ''):
            hs_id = thongtin_hs['id']
            ds_kh_dang_ct = kh_theo_hs.get(hs_id, [])
            if ds_kh_dang_ct:
                for kh_item in ds_kh_dang_ct:
                    ds_dong_hocsinh.append({
                        'hocsinh_id': hs_id,
                        'ten_hocsinh': thongtin_hs['ten'],
                        'so_ca': thongtin_hs['so_ca'],
                        'kehoach_id': kh_item['kehoach_id'],
                        'ten_kehoach': kh_item['ten_kehoach'],
                        'trangthai': 'da_capnhat' if kh_item['da_capnhat'] else 'chua_capnhat',
                        'ngay_capnhat': kh_item['ngay_capnhat'],
                    })
            elif hs_id not in tap_hs_da_lap_kh:
                ds_dong_hocsinh.append({
                    'hocsinh_id': hs_id,
                    'ten_hocsinh': thongtin_hs['ten'],
                    'so_ca': thongtin_hs['so_ca'],
                    'kehoach_id': False,
                    'ten_kehoach': '',
                    'trangthai': 'chua_co_kh',
                    'ngay_capnhat': '',
                })

        for stt, dong in enumerate(ds_dong_hocsinh, start=1):
            dong['stt'] = stt

        return ds_dong_hocsinh, so_kh_da_capnhat, so_kh_chua_capnhat

    def _lay_chuyencan_thang(self, gv_id, nam, thang, ngay_dau_thang, ngay_cuoi_thang):
        """Tính số ngày nghỉ phép & buổi vắng mặt trong tháng"""
        ngay_nghi_phep = 0.0
        buoi_vang_mat = 0.0

        if 'ekids.chamcong_giaovien2thang' in self.env:
            ds_cc = self.env['ekids.chamcong_giaovien2thang'].sudo().search_read(
                domain=[
                    ('giaovien_id', '=', gv_id),
                    ('chamcong_loai2thang_id.nam', '=', str(nam)),
                    ('chamcong_loai2thang_id.thang', '=', str(thang)),
                ],
                fields=['tong_nghiphep', 'tong_nghi_cangay', 'tong_dilam_nuabuoi'],
                limit=1,
            )
            if ds_cc:
                cc = ds_cc[0]
                ngay_nghi_phep = cc.get('tong_nghiphep') or 0.0
                buoi_vang_mat = (cc.get('tong_nghi_cangay') or 0) + ((cc.get('tong_dilam_nuabuoi') or 0) * 0.5)
                return round(ngay_nghi_phep, 1), round(buoi_vang_mat, 1)

        if 'ekids.giaovien_nghiphep' in self.env:
            ds_np = self.env['ekids.giaovien_nghiphep'].sudo().search_read(
                domain=[
                    ('giaovien_id', '=', gv_id),
                    ('tu_ngay', '<=', ngay_cuoi_thang),
                    ('den_ngay', '>=', ngay_dau_thang),
                ],
                fields=['tu_ngay', 'den_ngay', 'loai'],
            )
            for np in ds_np:
                ngay_bd = max(np['tu_ngay'], ngay_dau_thang)
                ngay_kt = min(np['den_ngay'], ngay_cuoi_thang)
                so_ngay = float((ngay_kt - ngay_bd).days + 1)
                if np.get('loai') == '0':
                    ngay_nghi_phep += so_ngay
                else:
                    buoi_vang_mat += so_ngay

        return round(ngay_nghi_phep, 1), round(buoi_vang_mat, 1)

    def _lay_dulieu_luong_nam(self, gv_id, ds_cap_thang, ngay_hientai, nam_chon, thang_chon):
        """Tính lương tháng đang chọn & dữ liệu biểu đồ lương cả năm tài chính bằng 1 lần search_read"""
        luong_thang_nay = 0.0
        thuong_thang_nay = 0.0
        nhan_thang, giatri_cot, nhan_trieu, nhan_daydu = [], [], [], []

        if 'ekids.luong' not in self.env:
            return luong_thang_nay, thuong_thang_nay, {
                'nhan_thang': nhan_thang,
                'giatri_cot': giatri_cot,
                'nhan_trieu': nhan_trieu,
                'nhan_daydu': nhan_daydu,
            }

        ds_nam = list({str(y) for y, _ in ds_cap_thang})
        ds_luong = self.env['ekids.luong'].sudo().search_read(
            domain=[
                ('giaovien_id', '=', gv_id),
                ('thang_id.nam_id.name', 'in', ds_nam),
            ],
            fields=['luong', 'tong_thuong', 'thang_id', 'nam_id'],
        )

        bando_luong = {}
        for r in ds_luong:
            thang_str = r['thang_id'][1] if r.get('thang_id') else ''
            nam_str = r['nam_id'][1] if r.get('nam_id') else ''
            if nam_str and thang_str:
                bando_luong[(nam_str, thang_str)] = r

        for y_m, m_val in ds_cap_thang:
            if (y_m, m_val) > (ngay_hientai.year, ngay_hientai.month):
                break

            ban_ghi_l = bando_luong.get((str(y_m), str(m_val)))
            tien_vnd_chan = self._lamtron_nghin(ban_ghi_l['luong'] if ban_ghi_l else 0.0)

            if y_m == nam_chon and m_val == thang_chon:
                luong_thang_nay = tien_vnd_chan
                thuong_thang_nay = self._lamtron_nghin(ban_ghi_l['tong_thuong'] if ban_ghi_l else 0.0)

            nhan_thang.append(f"T{m_val}")
            giatri_cot.append(tien_vnd_chan)
            nhan_trieu.append(self._dinhdang_trieu_bieudo(tien_vnd_chan))
            nhan_daydu.append(self._dinhdang_vnd(tien_vnd_chan))

        return luong_thang_nay, thuong_thang_nay, {
            'nhan_thang': nhan_thang,
            'giatri_cot': giatri_cot,
            'nhan_trieu': nhan_trieu,
            'nhan_daydu': nhan_daydu,
        }

    # =========================================================================
    # NHÓM 3: HÀM ĐIỀU PHỐI CHÍNH GỌI TỪ OWL FRONTEND
    # =========================================================================
    @api.model
    def get_dashboard_data(self, thang_nam=None, giaovien_id=None, month_str=None, **kwargs):
        thang_nam = thang_nam or month_str
        ngay_hientai = fields.Date.context_today(self)
        if not giaovien_id:
            gv= giaovien_util.func_get_giaoviens_tu_user(self)
            if gv:
                giaovien_id = gv.id



        ntc_hientai = self._xacdinh_nam_taichinh(ngay_hientai.year, ngay_hientai.month)
        ds_cap_thang = self._ds_thang_cua_nam_taichinh(ntc_hientai)

        thang_hientai_ym = ngay_hientai.strftime('%Y-%m')
        ds_thang = [
            {
                'giatri': f"{y_val}-{m_val:02d}",
                'nhan': f"Tháng {m_val:02d}/{y_val}" + (" (Tháng này)" if f"{y_val}-{m_val:02d}" == thang_hientai_ym else ""),
            }
            for y_val, m_val in ds_cap_thang
        ]
        ds_thang_hople = [m['giatri'] for m in ds_thang]
        if not thang_nam or thang_nam not in ds_thang_hople:
            thang_nam = thang_hientai_ym

        nam, thang = map(int, thang_nam.split('-'))
        ngay_dau_thang = date(nam, thang, 1)
        ngay_20_thang = date(nam, thang, 20)
        ngay_cuoi_thang = date(nam, thang, calendar.monthrange(nam, thang)[1])
        ngay_xet = ngay_hientai if (nam == ngay_hientai.year and thang == ngay_hientai.month) else ngay_20_thang

        tu_ngay_tuan = ngay_hientai - timedelta(days=ngay_hientai.weekday())
        den_ngay_tuan = tu_ngay_tuan + timedelta(days=6)

        # 1. Tập trẻ phụ trách & các chỉ số kế hoạch
        ds_hs_phutrach = self._lay_ds_hocsinh_phutrach(gv.id)
        ds_hs_id = list(ds_hs_phutrach.keys())

        tap_hs_da_lap_kh = self._lay_tap_hs_da_lap_kehoach(ds_hs_id, ngay_dau_thang, ngay_20_thang)
        kh_dang_canthiep = self._dem_kehoach_dang_canthiep(giaovien_id)
        kh_soan_choduyet = self._dem_kehoach_soan_choduyet(ds_hs_id, ngay_dau_thang, ngay_20_thang)
        kh_sap_hethan = self._dem_kehoach_sap_hethan(ds_hs_id, ngay_dau_thang, ngay_20_thang, ngay_xet)
        kh_dang_co = self._dem_kehoach_dang_co(giaovien_id)
        tong_hs_phutrach = len(ds_hs_phutrach)
        hs_da_co_kh = len(tap_hs_da_lap_kh)
        hs_chua_co_kh = max(0, tong_hs_phutrach - kh_dang_co)
        tyle_lap_kh = round(hs_da_co_kh / tong_hs_phutrach * 100, 1) if tong_hs_phutrach else 0

        # 2. Bảng theo dõi cập nhật tuần này
        ds_dong_hocsinh, so_kh_da_capnhat, so_kh_chua_capnhat = self._lay_bang_capnhat_tuan(
            gv.id, ds_hs_phutrach, tap_hs_da_lap_kh, tu_ngay_tuan, den_ngay_tuan, nam, thang
        )
        tong_kh_tuan = so_kh_da_capnhat + so_kh_chua_capnhat
        tyle_cham_tuan = round(so_kh_da_capnhat / tong_kh_tuan * 100) if tong_kh_tuan else 0

        # 3. Chuyên cần & nghỉ phép
        ngay_nghi_phep, buoi_vang_mat = self._lay_chuyencan_thang(
            gv.id, nam, thang, ngay_dau_thang, ngay_cuoi_thang
        )

        # 4. Lương thực lĩnh & biểu đồ lương cả năm
        luong_thang_nay, thuong_thang_nay, bieudo_luong = self._lay_dulieu_luong_nam(
            gv.id, ds_cap_thang, ngay_hientai, nam, thang
        )

        return {
            'co_giaovien': True,
            'giaovien': {
                'id': gv.id,
                'ten': gv.name or '',
                'anh_base64': self._lay_anh_giaovien(gv),
                'ten_coso': gv.coso_id.name if getattr(gv, 'coso_id', False) else '',
                'chuoi_tuan': f"{tu_ngay_tuan.strftime('%d/%m/%Y')} – {den_ngay_tuan.strftime('%d/%m/%Y')}",
            },
            'ds_thang': ds_thang,
            'thang_nam': thang_nam,
            'thang': thang,
            'nam': nam,
            'kpi': {
                'tong_hs': tong_hs_phutrach,
                'hs_da_co_kh': hs_da_co_kh,
                'hs_chua_co_kh': hs_chua_co_kh,
                'tyle_lap_kh': tyle_lap_kh,
                'so_kh_da_capnhat': so_kh_da_capnhat,
                'so_kh_chua_capnhat': so_kh_chua_capnhat,
                'tong_kh_tuan': tong_kh_tuan,
                'tyle_cham_tuan': tyle_cham_tuan,
                'ngay_nghi_phep': ngay_nghi_phep,
                'buoi_vang_mat': buoi_vang_mat,
                'luong_thuclinh_str': self._dinhdang_vnd(luong_thang_nay, co_donvi=False),
                'thuong_str': self._dinhdang_vnd(thuong_thang_nay),
            },
            'tinhtrang_hoso': {
                'dang_canthiep': kh_dang_canthiep,
                'soan_choduyet': kh_soan_choduyet,
                'sap_hethan': kh_sap_hethan,
                'chua_co_kh': hs_chua_co_kh,
            },
            'bieudo_luong': bieudo_luong,
            'ds_dong_hocsinh': ds_dong_hocsinh,
        }