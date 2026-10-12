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

        d_thangnay_15 = date(today.year, today.month, 15)
        d_thangtruoc_15 = d_thangnay_15 - relativedelta(months=1)
        d_thangtoi_15 = d_thangnay_15 + relativedelta(months=1)

        # 2. Lấy danh sách cơ sở
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

            # Cột: Tổng HS có kết luận bất kỳ
            dict_hs_has_kl.setdefault(cid, set()).add(hs_id)

            # Cột: Tổng HS có kết luận cho phép lập KH (có ít nhất 1 kết luận trangthai == '1')
            if tt_kl == '1':
                dict_hs_kl_chopheplap.setdefault(cid, set()).add(hs_id)

        # 5. Lấy KẾ HOẠCH (Chỉ học sinh đang theo học)
        kh_records = self.env['ekids.kehoach'].search_read(
            domain=[
                ('coso_id', 'in', coso_ids),
                ('hocsinh_id', 'in', list(all_active_hs_ids)),
            ],
            fields=['id', 'coso_id', 'hocsinh_id', 'tu_ngay', 'trangthai', 'trangthai_pheduyet']
        )

        # A. Tập hợp theo ĐẦU HỌC SINH (Dùng set để không trùng)
        dict_hs_co_kh = {}

        # B. Đếm SỐ LƯỢNG KẾ HOẠCH (Dùng biến int đếm số record kế hoạch)
        dict_kh_soanthao_cnt = {}
        dict_kh_daduyet_cnt = {}

        dict_kh_nay_all_cnt = {}
        dict_kh_nay_daduyet_cnt = {}
        dict_kh_toi_all_cnt = {}
        dict_kh_toi_daduyet_cnt = {}

        dict_kh_doiduyet_cnt = {}
        dict_kh_dangcanthiep_cnt = {}

        TRANGTHAI_DADUYET = ['1', '-1']

        for r in kh_records:
            if not r.get('coso_id') or not r.get('hocsinh_id'):
                continue
            cid = r['coso_id'][0]
            hs_id = r['hocsinh_id'][0]
            tt = str(r.get('trangthai', ''))
            tt_pd = str(r.get('trangthai_pheduyet', ''))
            tu_ngay = fields.Date.to_date(r.get('tu_ngay')) if r.get('tu_ngay') else False

            # --- NHÓM 1: TÍNH THEO ĐẦU HỌC SINH ---
            # Ghi nhận học sinh đã có ít nhất một kế hoạch
            dict_hs_co_kh.setdefault(cid, set()).add(hs_id)

            # --- NHÓM 2: TÍNH THEO SỐ LƯỢNG KẾ HOẠCH (RECORDS) ---
            is_approved = (tt in TRANGTHAI_DADUYET or tt_pd in ['1', 'da_duyet'])

            # Cột: Tổng số KH được phê duyệt
            if is_approved:
                dict_kh_daduyet_cnt[cid] = dict_kh_daduyet_cnt.get(cid, 0) + 1
            # Cột: Tổng số KH đang soạn thảo (bao gồm cả bản ghi đang lập, cần điều chỉnh, chờ duyệt)
            else:
                dict_kh_soanthao_cnt[cid] = dict_kh_soanthao_cnt.get(cid, 0) + 1

            # Cột: Kế hoạch đang đợi duyệt (trangthai = '2' và trangthai_pheduyet = '0')
            if tt in ['2', 'dang_pheduyet'] and tt_pd in ['0', 'doi_duyet']:
                dict_kh_doiduyet_cnt[cid] = dict_kh_doiduyet_cnt.get(cid, 0) + 1

            # Cột: Kế hoạch đang can thiệp (trangthai = '1' và tu_ngay <= today)
            if tt in ['1', 'dang_canthiep'] and tu_ngay and tu_ngay <= today:
                dict_kh_dangcanthiep_cnt[cid] = dict_kh_dangcanthiep_cnt.get(cid, 0) + 1

            # Chu kỳ kế hoạch tháng này
            if tu_ngay and d_thangtruoc_15 < tu_ngay <= d_thangnay_15:
                dict_kh_nay_all_cnt[cid] = dict_kh_nay_all_cnt.get(cid, 0) + 1
                if is_approved:
                    dict_kh_nay_daduyet_cnt[cid] = dict_kh_nay_daduyet_cnt.get(cid, 0) + 1

            # Chu kỳ kế hoạch tháng tới
            if tu_ngay and d_thangnay_15 < tu_ngay <= d_thangtoi_15:
                dict_kh_toi_all_cnt[cid] = dict_kh_toi_all_cnt.get(cid, 0) + 1
                if is_approved:
                    dict_kh_toi_daduyet_cnt[cid] = dict_kh_toi_daduyet_cnt.get(cid, 0) + 1

        # 6. Tổng hợp dữ liệu hiển thị theo từng cơ sở
        rows = []
        stt = 1
        totals = {
            'so_hs': 0,
            'hs_kl': 0,
            'hs_kl_chopheplap': 0,
            'hs_co_kh': 0,
            'hs_chua_co_kh': 0,
            'kh_soanthao': 0,
            'kh_daduyet': 0,
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
            # Học sinh chưa có KH nào = Tổng HS đang học - Đã có KH (chuẩn xác 100%)
            v_hs_chua_co_kh = max(0, v_so_hs - v_hs_co_kh)

            # Lấy số lượng bản ghi kế hoạch
            v_kh_soanthao = dict_kh_soanthao_cnt.get(cs.id, 0)
            v_kh_daduyet = dict_kh_daduyet_cnt.get(cs.id, 0)

            v_kh_nay_all = dict_kh_nay_all_cnt.get(cs.id, 0)
            v_kh_nay_daduyet = dict_kh_nay_daduyet_cnt.get(cs.id, 0)
            v_kh_toi_all = dict_kh_toi_all_cnt.get(cs.id, 0)
            v_kh_toi_daduyet = dict_kh_toi_daduyet_cnt.get(cs.id, 0)

            v_kh_doiduyet = dict_kh_doiduyet_cnt.get(cs.id, 0)
            v_kh_dangcanthiep = dict_kh_dangcanthiep_cnt.get(cs.id, 0)

            # Cộng dồn hàng TỔNG CỘNG
            totals['so_hs'] += v_so_hs
            totals['hs_kl'] += v_hs_kl
            totals['hs_kl_chopheplap'] += v_hs_kl_chopheplap
            totals['hs_co_kh'] += v_hs_co_kh
            totals['hs_chua_co_kh'] += v_hs_chua_co_kh
            totals['kh_soanthao'] += v_kh_soanthao
            totals['kh_daduyet'] += v_kh_daduyet
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
                'hs_chua_co_kh': v_hs_chua_co_kh,
                'kh_soanthao': v_kh_soanthao,
                'kh_daduyet': v_kh_daduyet,
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