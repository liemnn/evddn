# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class ReportBaoCaoCanThiep(models.AbstractModel):
    _name = 'report.ekids_baocao.baocao_canthiep_template'
    _description = 'Báo cáo kết quả sử dụng phần mềm kế hoạch cá nhân'

    def _get_target_month_year(self, tu_ngay):
        """
        Quy định mốc ngày 15:
        - Trước hoặc bằng ngày 15: tính vào tháng đó
        - Sau ngày 15: tính vào tháng sau
        """
        if not tu_ngay:
            return False
        d = fields.Date.to_date(tu_ngay)
        if d.day <= 15:
            return (d.month, d.year)
        else:
            d_next = d + relativedelta(months=1)
            return (d_next.month, d_next.year)

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user
        today = fields.Date.today()

        # 1. Xác định 2 mốc tháng này và tháng tới
        m_thangnay = (today.month, today.year)
        d_toi = today + relativedelta(months=1)
        m_thangtoi = (d_toi.month, d_toi.year)

        # 2. Lấy danh sách cơ sở
        cosos = user.coso_ids
        coso_ids = cosos.ids

        # 3. Lấy tất cả học sinh đang theo học (trangthai = '1')
        hs_active_records = self.env['ekids.hocsinh'].search_read(
            domain=[('coso_id', 'in', coso_ids), ('trangthai', '=', '1')],
            fields=['id', 'coso_id']
        )
        dict_active_hs_by_coso = {}
        all_active_hs_ids = set()

        for hs in hs_active_records:
            cid = hs['coso_id'][0]
            hs_id = hs['id']
            dict_active_hs_by_coso.setdefault(cid, set()).add(hs_id)
            all_active_hs_ids.add(hs_id)

        # 4. Lấy số học sinh có KẾT LUẬN (Chỉ học sinh đang theo học)
        kl_records = self.env['ekids.kehoach_ketluan'].search_read(
            domain=[
                ('coso_id', 'in', coso_ids),
                ('hocsinh_id', 'in', list(all_active_hs_ids)),
                ('trangthai', 'in', ['0', '1', '-1'])
            ],
            fields=['coso_id', 'hocsinh_id']
        )
        dict_hs_ketluan = {}
        for r in kl_records:
            if r.get('coso_id') and r.get('hocsinh_id'):
                cid = r['coso_id'][0]
                hs_id = r['hocsinh_id'][0]
                dict_hs_ketluan.setdefault(cid, set()).add(hs_id)

        # 5. Lấy KẾ HOẠCH (Chỉ học sinh đang theo học)
        kh_records = self.env['ekids.kehoach'].search_read(
            domain=[
                ('coso_id', 'in', coso_ids),
                ('hocsinh_id', 'in', list(all_active_hs_ids))
            ],
            fields=['coso_id', 'hocsinh_id', 'tu_ngay', 'trangthai']
        )

        dict_hs_kehoach_all = {}
        dict_hs_kh_thangnay = {}
        dict_hs_kh_thangtoi = {}
        dict_hs_kh_choxuly = {}

        # Trạng thái ĐÃ DUYỆT: 1 (đang can thiệp), -1 (kết thúc)
        TRANGTHAI_DADUYET = ['1', '-1']

        for r in kh_records:
            if not r.get('coso_id') or not r.get('hocsinh_id'):
                continue
            cid = r['coso_id'][0]
            hs_id = r['hocsinh_id'][0]
            tt = str(r.get('trangthai', ''))

            # Đếm tổng học sinh đã từng có kế hoạch
            dict_hs_kehoach_all.setdefault(cid, set()).add(hs_id)

            # Cột: Đang đợi duyệt (trangthai == '0')
            if tt == '0':
                dict_hs_kh_choxuly.setdefault(cid, set()).add(hs_id)

            # Kế hoạch Tháng này & Tháng tới: Bắt buộc đã duyệt
            if tt in TRANGTHAI_DADUYET:
                m_target = self._get_target_month_year(r.get('tu_ngay'))
                if m_target == m_thangnay:
                    dict_hs_kh_thangnay.setdefault(cid, set()).add(hs_id)
                elif m_target == m_thangtoi:
                    dict_hs_kh_thangtoi.setdefault(cid, set()).add(hs_id)

        # 6. Tổng hợp dữ liệu
        rows = []
        stt = 1
        tong_so_hs = 0
        tong_hs_kl = 0
        tong_hs_kh = 0
        tong_kh_nay = 0
        tong_kh_toi = 0
        tong_kh_cho = 0

        for cs in cosos:
            so_hs = len(dict_active_hs_by_coso.get(cs.id, set()))
            so_hs_kl = len(dict_hs_ketluan.get(cs.id, set()))
            so_hs_kh = len(dict_hs_kehoach_all.get(cs.id, set()))

            kh_nay = len(dict_hs_kh_thangnay.get(cs.id, set()))
            kh_toi = len(dict_hs_kh_thangtoi.get(cs.id, set()))
            kh_cho = len(dict_hs_kh_choxuly.get(cs.id, set()))

            tong_so_hs += so_hs
            tong_hs_kl += so_hs_kl
            tong_hs_kh += so_hs_kh
            tong_kh_nay += kh_nay
            tong_kh_toi += kh_toi
            tong_kh_cho += kh_cho

            rows.append({
                'stt': stt,
                'ten_coso': cs.name,
                'so_hocsinh': so_hs,
                'so_hs_ketluan': so_hs_kl,
                'so_hs_kehoach': so_hs_kh,
                'kh_thangnay': kh_nay,
                'kh_thangtoi': kh_toi,
                'kh_choxuly': kh_cho,
                'ghichu': '',
            })
            stt += 1

        report_data = {
            'label_thangnay': f"Tháng {m_thangnay[0]}",
            'label_thangtoi': f"Tháng {m_thangtoi[0]}",
            'rows': rows,
            'tong_so_hs': tong_so_hs,
            'tong_hs_kl': tong_hs_kl,
            'tong_hs_kh': tong_hs_kh,
            'tong_kh_nay': tong_kh_nay,
            'tong_kh_toi': tong_kh_toi,
            'tong_kh_cho': tong_kh_cho,
        }

        return {
            'doc_ids': docids,
            'doc_model': 'ekids.coso',
            'docs': cosos,
            'data': report_data,
        }