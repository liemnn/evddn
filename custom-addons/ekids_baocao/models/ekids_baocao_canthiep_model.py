# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class ReportBaoCaoCanThiep(models.AbstractModel):
    _name = 'report.ekids_baocao.baocao_canthiep_template'
    _description = 'Báo cáo kết quả sử dụng phần mềm kế hoạch cá nhân'

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user
        today = fields.Date.today()

        # 1. Xác định nhãn tháng & các mốc chu kỳ ngày 15
        m_thangnay = (today.month, today.year)
        d_toi = today + relativedelta(months=1)
        m_thangtoi = (d_toi.month, d_toi.year)

        # Mốc ngày 15 chuẩn xác của tháng này, tháng trước và tháng tới
        d_thangnay_15 = date(today.year, today.month, 15)
        d_thangtruoc_15 = d_thangnay_15 - relativedelta(months=1)
        d_thangtoi_15 = d_thangnay_15 + relativedelta(months=1)

        # 2. Lấy danh sách cơ sở phân quyền của người dùng
        cosos = user.coso_ids
        coso_ids = cosos.ids

        # 3. Lấy tất cả học sinh đang theo học (trangthai = '1')
        hs_active_records = self.env['ekids.hocsinh'].search_read(
            domain=[('coso_id', 'in', coso_ids), ('trangthai', '=', '1')],
            fields=['id', 'coso_id']
        )
        dict_active_hs = {}
        all_active_hs_ids = set()

        for hs in hs_active_records:
            cid = hs['coso_id'][0]
            hs_id = hs['id']
            dict_active_hs.setdefault(cid, set()).add(hs_id)
            all_active_hs_ids.add(hs_id)

        # 4. Lấy dữ liệu KẾT LUẬN của học sinh đang theo học
        kl_records = self.env['ekids.kehoach_ketluan'].search_read(
            domain=[
                ('coso_id', 'in', coso_ids),
                ('hocsinh_id', 'in', list(all_active_hs_ids)),
            ],
            fields=['coso_id', 'hocsinh_id', 'trangthai']
        )
        dict_hs_has_kl = {}
        dict_hs_kl_chopheplap = {}

        for r in kl_records:
            if not r.get('coso_id') or not r.get('hocsinh_id'):
                continue
            cid = r['coso_id'][0]
            hs_id = r['hocsinh_id'][0]
            tt_kl = str(r.get('trangthai', ''))

            # Cột: Tổng HS có Kết luận bất kỳ
            dict_hs_has_kl.setdefault(cid, set()).add(hs_id)

            # Cột: Tổng HS có Kết luận cho phép lập Kế hoạch (trangthai == '1')
            if tt_kl == '1':
                dict_hs_kl_chopheplap.setdefault(cid, set()).add(hs_id)

        # 5. Lấy KẾ HOẠCH (Chỉ học sinh đang theo học)
        # Sắp xếp tu_ngay desc, id desc để lấy đúng kế hoạch mới nhất của mỗi học sinh
        kh_records = self.env['ekids.kehoach'].search_read(
            domain=[
                ('coso_id', 'in', coso_ids),
                ('hocsinh_id', 'in', list(all_active_hs_ids)),
            ],
            fields=['coso_id', 'hocsinh_id', 'tu_ngay', 'trangthai', 'trangthai_pheduyet'],
            order='tu_ngay desc, id desc'
        )

        dict_hs_co_kh = {}
        dict_hs_kh_dangsoanthao = {}
        dict_hs_kh_daduyet = {}

        dict_kh_nay_all = {}
        dict_kh_nay_daduyet = {}
        dict_kh_toi_all = {}
        dict_kh_toi_daduyet = {}

        dict_kh_doiduyet = {}
        dict_kh_dangcanthiep = {}

        TRANGTHAI_DADUYET = ['1', '-1']

        # Map lưu kế hoạch mới nhất / đại diện của từng học sinh: {hs_id: (trangthai, trangthai_pheduyet, coso_id)}
        hs_latest_kh_status = {}

        for r in kh_records:
            if not r.get('coso_id') or not r.get('hocsinh_id'):
                continue
            cid = r['coso_id'][0]
            hs_id = r['hocsinh_id'][0]
            tt = str(r.get('trangthai', ''))
            tt_pd = str(r.get('trangthai_pheduyet', ''))
            tu_ngay = fields.Date.to_date(r.get('tu_ngay')) if r.get('tu_ngay') else False

            # Ghi nhận kế hoạch mới nhất của mỗi học sinh (do đã order desc từ đầu)
            if hs_id not in hs_latest_kh_status:
                hs_latest_kh_status[hs_id] = (tt, tt_pd, cid)

            # Cột: Kế hoạch đang đợi duyệt (trangthai = '2' và trangthai_pheduyet = '0')[cite: 8]
            if tt in ['2', 'dang_pheduyet'] and tt_pd in ['0', 'doi_duyet']:
                dict_kh_doiduyet.setdefault(cid, set()).add(hs_id)

            # Cột: Kế hoạch đang can thiệp thực tế (trangthai = '1' và tu_ngay <= today)[cite: 3, 8]
            if tt in ['1', 'dang_canthiep'] and tu_ngay and tu_ngay <= today:
                dict_kh_dangcanthiep.setdefault(cid, set()).add(hs_id)

            # Chu kỳ kế hoạch tháng này: sau ngày 15 tháng trước đến hết ngày 15 tháng này
            if tu_ngay and d_thangtruoc_15 < tu_ngay <= d_thangnay_15:
                dict_kh_nay_all.setdefault(cid, set()).add(hs_id)
                if tt in TRANGTHAI_DADUYET:
                    dict_kh_nay_daduyet.setdefault(cid, set()).add(hs_id)

            # Chu kỳ kế hoạch tháng tới: sau ngày 15 tháng này đến hết ngày 15 tháng tới
            if tu_ngay and d_thangnay_15 < tu_ngay <= d_thangtoi_15:
                dict_kh_toi_all.setdefault(cid, set()).add(hs_id)
                if tt in TRANGTHAI_DADUYET:
                    dict_kh_toi_daduyet.setdefault(cid, set()).add(hs_id)

        # 🌟 PHÂN NHÓM CHUẨN XÁC THEO HỌC SINH:
        # "Đang đợi duyệt" được gộp vào "Đang soạn thảo"
        # Đảm bảo: Đang soạn thảo + Đã duyệt = Đã có KH
        for hs_id, (tt, tt_pd, cid) in hs_latest_kh_status.items():
            # Cột: Tổng số HS đã có Kế hoạch
            dict_hs_co_kh.setdefault(cid, set()).add(hs_id)

            # Nhóm 1: Đã duyệt (Sẵn sàng can thiệp / Hết hiệu lực)
            if tt in TRANGTHAI_DADUYET or tt_pd in ['1', 'da_duyet']:
                dict_hs_kh_daduyet.setdefault(cid, set()).add(hs_id)
            # Nhóm 2: Đang soạn thảo (Bao gồm: Đang soạn, Cần điều chỉnh, và Đang đợi duyệt)
            else:
                dict_hs_kh_dangsoanthao.setdefault(cid, set()).add(hs_id)

        # 6. Tổng hợp dữ liệu hiển thị theo từng cơ sở
        rows = []
        stt = 1
        totals = {
            'so_hs': 0,
            'hs_kl': 0,
            'hs_kl_chopheplap': 0,
            'hs_co_kh': 0,
            'hs_kh_dangsoanthao': 0,
            'hs_kh_daduyet': 0,
            'kh_nay_all': 0,
            'kh_nay_daduyet': 0,
            'kh_toi_all': 0,
            'kh_toi_daduyet': 0,
            'kh_doiduyet': 0,
            'kh_dangcanthiep': 0,
        }

        for cs in cosos:
            v_so_hs = len(dict_active_hs.get(cs.id, set()))
            v_hs_kl = len(dict_hs_has_kl.get(cs.id, set()))
            v_hs_kl_chopheplap = len(dict_hs_kl_chopheplap.get(cs.id, set()))

            v_hs_co_kh = len(dict_hs_co_kh.get(cs.id, set()))
            v_hs_kh_dangsoanthao = len(dict_hs_kh_dangsoanthao.get(cs.id, set()))
            v_hs_kh_daduyet = len(dict_hs_kh_daduyet.get(cs.id, set()))

            v_kh_nay_all = len(dict_kh_nay_all.get(cs.id, set()))
            v_kh_nay_daduyet = len(dict_kh_nay_daduyet.get(cs.id, set()))
            v_kh_toi_all = len(dict_kh_toi_all.get(cs.id, set()))
            v_kh_toi_daduyet = len(dict_kh_toi_daduyet.get(cs.id, set()))

            v_kh_doiduyet = len(dict_kh_doiduyet.get(cs.id, set()))
            v_kh_dangcanthiep = len(dict_kh_dangcanthiep.get(cs.id, set()))

            # Cộng dồn hàng TỔNG CỘNG
            totals['so_hs'] += v_so_hs
            totals['hs_kl'] += v_hs_kl
            totals['hs_kl_chopheplap'] += v_hs_kl_chopheplap
            totals['hs_co_kh'] += v_hs_co_kh
            totals['hs_kh_dangsoanthao'] += v_hs_kh_dangsoanthao
            totals['hs_kh_daduyet'] += v_hs_kh_daduyet
            totals['kh_nay_all'] += v_kh_nay_all
            totals['kh_nay_daduyet'] += v_kh_nay_daduyet
            totals['kh_toi_all'] += v_kh_toi_all
            totals['kh_toi_daduyet'] += v_kh_toi_daduyet
            totals['kh_doiduyet'] += v_kh_doiduyet
            totals['kh_dangcanthiep'] += v_kh_dangcanthiep

            rows.append({
                'stt': stt,
                'ten_coso': cs.name,
                'so_hs': v_so_hs,
                'hs_kl': v_hs_kl,
                'hs_kl_chopheplap': v_hs_kl_chopheplap,
                'hs_co_kh': v_hs_co_kh,
                'hs_kh_dangsoanthao': v_hs_kh_dangsoanthao,
                'hs_kh_daduyet': v_hs_kh_daduyet,
                'kh_nay_all': v_kh_nay_all,
                'kh_nay_daduyet': v_kh_nay_daduyet,
                'kh_toi_all': v_kh_toi_all,
                'kh_toi_daduyet': v_kh_toi_daduyet,
                'kh_doiduyet': v_kh_doiduyet,
                'kh_dangcanthiep': v_kh_dangcanthiep,
            })
            stt += 1

        report_data = {
            'label_thangnay': f"Tháng {m_thangnay[0]}/{m_thangnay[1]}",
            'label_thangtoi': f"Tháng {m_thangtoi[0]}/{m_thangtoi[1]}",
            'rows': rows,
            'totals': totals,
        }

        return {
            'doc_ids': docids,
            'doc_model': 'ekids.coso',
            'docs': cosos,
            'data': report_data,
        }