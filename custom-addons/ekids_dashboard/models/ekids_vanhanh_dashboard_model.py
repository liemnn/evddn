# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date
import calendar


class VanhanhDashboard(models.AbstractModel):
    _name = 'ekids.dashboard_vanhanh'
    _description = 'Dashboard Quản trị Hoạt động Trung tâm'

    def _xacdinh_nam_taichinh(self, nam_thucte, thang_thucte):
        """Năm tài chính bắt đầu từ Tháng 2 năm N đến hết Tháng 1 năm N+1"""
        return nam_thucte - 1 if thang_thucte == 1 else nam_thucte

    def _ds_thang_cua_nam_taichinh(self, nam_taichinh):
        """Trả về danh sách 12 cặp (nam_thucte, thang_thucte) từ 02/N đến 01/(N+1)"""
        ds = []
        for m in range(2, 13):
            ds.append((nam_taichinh, m))
        ds.append((nam_taichinh + 1, 1))
        return ds

    @api.model
    def get_dashboard_data(self, coso_id=None, nam_taichinh=None, thang_nam=None):
        ngay_hientai = fields.Date.context_today(self)
        ntc_hientai = self._xacdinh_nam_taichinh(ngay_hientai.year, ngay_hientai.month)

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

        # 2. XÁC ĐỊNH DANH SÁCH NĂM TÀI CHÍNH (TỪ THÁNG 2 NĂM N ĐẾN HẾT THÁNG 1 NĂM N+1)
        ds_ntc = []
        for y in range(ntc_hientai - 3, ntc_hientai + 1):
            ds_ntc.append({
                'giatri': str(y),
                'nhan': f"Năm tài chính {y} (02/{y} - 01/{y + 1})",
            })

        ds_ntc_hople = [n['giatri'] for n in ds_ntc]
        if not nam_taichinh or str(nam_taichinh) not in ds_ntc_hople:
            ntc_chon = ntc_hientai
        else:
            ntc_chon = int(nam_taichinh)

        # 3. XÁC ĐỊNH DANH SÁCH 12 THÁNG TRONG NĂM TÀI CHÍNH ĐANG CHỌN
        ds_cap_thang_ntc = self._ds_thang_cua_nam_taichinh(ntc_chon)
        ds_thang = []
        thang_hientai_ym = ngay_hientai.strftime('%Y-%m')

        for y_val, m_val in ds_cap_thang_ntc:
            val = f"{y_val}-{m_val:02d}"
            nhan = f"Tháng {m_val:02d}/{y_val}" + (" (Tháng này)" if val == thang_hientai_ym else "")
            ds_thang.append({'giatri': val, 'nhan': nhan})

        ds_thang_hople = [m['giatri'] for m in ds_thang]
        if not thang_nam or thang_nam not in ds_thang_hople:
            if thang_hientai_ym in ds_thang_hople:
                thang_nam = thang_hientai_ym
            else:
                thang_nam = ds_thang_hople[-1]

        nam, thang = map(int, thang_nam.split('-'))
        ngay_dau_thang = date(nam, thang, 1)
        ngay_cuoi_thang = date(nam, thang, calendar.monthrange(nam, thang)[1])
        ngay = ngay_hientai if (nam == ngay_hientai.year and thang == ngay_hientai.month) else ngay_cuoi_thang

        # 4. GỌI CÁC HÀM TÍNH TOÁN TỪ FILE FUNC
        kpi_data = self.func_tinhtoan_kpi_vanhanh(
            coso_id=coso_id_int,
            nam_taichinh=ntc_chon,
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
            nam_taichinh=ntc_chon,
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
            'ds_ntc': ds_ntc,
            'nam_taichinh': str(ntc_chon),
            'nhan_nam_taichinh': f"Năm tài chính {ntc_chon} (02/{ntc_chon} - 01/{ntc_chon + 1})",
            'ds_thang': ds_thang,
            'thang_nam': thang_nam,
            'thang': thang,
            'nam': nam,
            'kpi': kpi_data,
            'hocphi_thang': hocphi_thang,
            'bieudo': bieudo_data,
            'khoanchi_noibat': khoanchi_noibat,
        }