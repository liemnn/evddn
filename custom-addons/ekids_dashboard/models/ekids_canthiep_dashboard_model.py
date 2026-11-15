# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
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


class CanthiepDashboard(models.AbstractModel):
    _name = 'ekids.dashboard_canthiep'
    _description = 'Dashboard Hoạt động Can thiệp Real-time'

    @api.model
    def get_weeks_of_month(self, nam, thang):
        """Tự động chia các tuần (Thứ 2 - Chủ nhật) trong tháng được chọn"""
        first_day = date(nam, thang, 1)
        last_day = date(nam, thang, calendar.monthrange(nam, thang)[1])
        weeks = []
        curr = first_day
        idx = 1
        while curr <= last_day:
            days_to_sunday = 6 - curr.weekday()
            week_end = min(curr + timedelta(days=days_to_sunday), last_day)
            weeks.append({
                'index': idx,
                'label': f"Tuần {idx} ({curr.strftime('%d/%m')} - {week_end.strftime('%d/%m/%Y')})",
                'date_from': curr.strftime('%Y-%m-%d'),
                'date_to': week_end.strftime('%Y-%m-%d'),
                'd_from': curr,
                'd_to': week_end,
            })
            curr = week_end + timedelta(days=1)
            idx += 1
        return weeks

    @api.model
    def get_dashboard_data(self, center_id=None, month_str=None, week_index=None):
        ngay_hientai = fields.Date.context_today(self)

        # 1. XÁC ĐỊNH CƠ SỞ ĐANG CHỌN
        centers = []
        user = self.env.user
        if 'ekids.coso' in self.env:
            if hasattr(user, 'coso_ids') and user.coso_ids and not user.has_group('base.group_system'):
                coso_recs = user.coso_ids
            else:
                coso_recs = self.env['ekids.coso'].search([], order='id asc')

            for cs in coso_recs:
                centers.append({'id': str(cs.id), 'name': cs.name})
        else:
            centers = [
                {'id': '1', 'name': 'Trung tâm eKids Cơ sở 1'},
                {'id': '2', 'name': 'Trung tâm eKids Cơ sở 2'},
            ]

        valid_center_ids = [c['id'] for c in centers]
        if not center_id or str(center_id) not in valid_center_ids:
            default_cs = str(user.coso_id.id) if (hasattr(user, 'coso_id') and user.coso_id) else ''
            selected_cs_str = default_cs if default_cs in valid_center_ids else (valid_center_ids[0] if valid_center_ids else '0')
        else:
            selected_cs_str = str(center_id)

        coso_id = int(selected_cs_str)

        # 2. XÁC ĐỊNH THÁNG, NĂM & NGÀY ĐANG CHỌN
        months_options = []
        current_ym = ngay_hientai.strftime('%Y-%m')
        for m in range(1, 13):
            val = f"{ngay_hientai.year}-{m:02d}"
            lbl = f"Tháng {m:02d}/{ngay_hientai.year}" + (" (Tháng này)" if val == current_ym else "")
            months_options.append({'value': val, 'label': lbl})

        valid_months = [m['value'] for m in months_options]
        if not month_str or month_str not in valid_months:
            month_str = current_ym

        nam, thang = map(int, month_str.split('-'))
        ngay_dau_thang = date(nam, thang, 1)
        ngay_cuoi_thang = date(nam, thang, calendar.monthrange(nam, thang)[1])
        ngay = ngay_hientai if (nam == ngay_hientai.year and thang == ngay_hientai.month) else date(nam, thang, 15)

        # 3. XÁC ĐỊNH TUẦN ĐANG CHỌN (CHO BẢNG TẦNG 3)
        weeks = self.get_weeks_of_month(nam, thang)
        if not week_index or int(week_index) > len(weeks):
            week_index = 1
            if nam == ngay_hientai.year and thang == ngay_hientai.month:
                for w in weeks:
                    if w['d_from'] <= ngay_hientai <= w['d_to']:
                        week_index = w['index']
                        break
        else:
            week_index = int(week_index)

        selected_week = next((w for w in weeks if w['index'] == week_index), weeks[0])

        # 4. GỌI CÁC HÀM TÍNH TOÁN ĐỒNG BỘ VỚI BÁO CÁO CAN THIỆP
        kpi_data, ops_status = self._calc_kpi_and_ops(
            coso_id=coso_id,
            nam=nam,
            thang=thang,
            ngay=ngay,
            ngay_dau_thang=ngay_dau_thang,
            ngay_cuoi_thang=ngay_cuoi_thang,
        )

        chart_compare = self.func_tinhtoan_luytien_kehoach_trongnam(
            coso_id=coso_id,
            nam=nam,
            thang=thang,
        )

        weekly_data = self.func_tinhtoan_quatrinh_capnhat_ketqua_canthiep(
            coso_id=coso_id,
            nam=nam,
            thang=thang,
            tuan_tu_ngay=selected_week['d_from'],
            tuan_den_ngay=selected_week['d_to'],
        )

        clean_weeks = [
            {k: v for k, v in w.items() if k in ('index', 'label', 'date_from', 'date_to')}
            for w in weeks
        ]

        return {
            'centers': centers,
            'selected_center_id': selected_cs_str,
            'months_options': months_options,
            'selected_month': month_str,
            'weeks': clean_weeks,
            'selected_week_index': selected_week['index'],
            'kpi': kpi_data,
            'chart_compare': chart_compare,
            'ops_status': ops_status,
            'weekly': weekly_data,
        }

    # -------------------------------------------------------------------------
    # HÀM 1: TÍNH TOÁN 5 THẺ KPI & 4 CHỈ SỐ HỒ SƠ (KHỚP 100% BÁO CÁO CAN THIỆP)
    # -------------------------------------------------------------------------
    def _calc_kpi_and_ops(self, coso_id, nam, thang, ngay, ngay_dau_thang, ngay_cuoi_thang):
        # Mốc chu kỳ ngày 15 chuẩn theo ekids_baocao_canthiep_model.py
        d_thangnay_15 = date(nam, thang, 15)
        d_thangtruoc_15 = d_thangnay_15 - relativedelta(months=1)

        # 1. Tập học sinh đang theo học (trangthai = '1') của cơ sở
        hs_active_records = self.env['ekids.hocsinh'].search_read(
            domain=[('coso_id', '=', coso_id), ('trangthai', '=', '1')],
            fields=['id']
        )
        active_hs_ids = {hs['id'] for hs in hs_active_records}
        tong_hs = len(active_hs_ids)

        # 2. Học sinh có kết luận cho phép lập kế hoạch (tính theo ĐẦU HỌC SINH duy nhất)
        kl_records = self.env['ekids.kehoach_ketluan'].search_read(
            domain=[
                ('coso_id', '=', coso_id),
                ('hocsinh_id', 'in', list(active_hs_ids)),
                ('trangthai', '=', '1'),
            ],
            fields=['hocsinh_id']
        ) if active_hs_ids else []
        hs_co_kh_khung = len({r['hocsinh_id'][0] for r in kl_records if r.get('hocsinh_id')})

        # 3. Toàn bộ kế hoạch của học sinh đang theo học
        kh_records = self.env['ekids.kehoach'].search_read(
            domain=[
                ('coso_id', '=', coso_id),
                ('hocsinh_id', 'in', list(active_hs_ids)),
            ],
            fields=['id', 'hocsinh_id', 'tu_ngay', 'den_ngay', 'trangthai', 'trangthai_pheduyet']
        ) if active_hs_ids else []

        TRANGTHAI_DADUYET = ['1', '-1']
        ngay_sap_hethan = ngay + timedelta(days=10)

        tong_kh_luy_ke = 0          # Tổng số KH được phê duyệt (lũy kế)
        kh_trong_thang = 0          # Tổng số KH trong chu kỳ tháng (d_thangtruoc_15 < tu_ngay <= d_thangnay_15)
        hs_co_kh_thang = set()      # Đầu học sinh đã có KH trong chu kỳ tháng
        kh_dang_can_thiep = 0       # KH đang can thiệp (trangthai in ['1', 'dang_canthiep'] và tu_ngay <= ngay)
        kh_dang_lap = 0             # KH đang soạn thảo (trangthai == '0')
        kh_doi_duyet = 0            # KH đang đợi duyệt (trangthai in ['2', 'dang_pheduyet'] và trangthai_pheduyet in ['0', 'doi_duyet'])
        kh_sap_het_han = 0          # KH đang can thiệp sắp hết hạn trong 10 ngày tới

        for r in kh_records:
            if not r.get('hocsinh_id'):
                continue
            hs_id = r['hocsinh_id'][0]
            tt = str(r.get('trangthai', ''))
            tt_pd = str(r.get('trangthai_pheduyet', ''))
            tu_ngay = fields.Date.to_date(r.get('tu_ngay')) if r.get('tu_ngay') else False
            den_ngay = fields.Date.to_date(r.get('den_ngay')) if r.get('den_ngay') else False

            is_approved = (tt in TRANGTHAI_DADUYET or tt_pd in ['1', 'da_duyet'])

            # Lũy kế kế hoạch đã được phê duyệt
            if is_approved:
                tong_kh_luy_ke += 1

            # Kế hoạch đang can thiệp (khớp cột "KH đang can thiệp" trên báo cáo)
            if tt in ['1', 'dang_canthiep'] and tu_ngay and tu_ngay <= ngay:
                kh_dang_can_thiep += 1
                if den_ngay and ngay <= den_ngay <= ngay_sap_hethan:
                    kh_sap_het_han += 1

            # Kế hoạch đang đợi duyệt (khớp cột "KH đang đợi duyệt" trên báo cáo)
            if tt in ['2', 'dang_pheduyet'] and tt_pd in ['0', 'doi_duyet']:
                kh_doi_duyet += 1

            # Kế hoạch đang soạn thảo (trạng thái '0' / '-1' chưa duyệt)
            if tt in ['0', 'dang_lap'] and not is_approved:
                kh_dang_lap += 1

            # Chu kỳ kế hoạch tháng này (d_thangtruoc_15 < tu_ngay <= d_thangnay_15)
            if tu_ngay and d_thangtruoc_15 < tu_ngay <= d_thangnay_15:
                kh_trong_thang += 1
                hs_co_kh_thang.add(hs_id)

        # Học sinh đang theo học nhưng chưa có KH nào trong chu kỳ tháng
        hs_chua_co_kh = max(0, tong_hs - len(hs_co_kh_thang))

        pct_khung = round(hs_co_kh_khung / tong_hs * 100, 1) if tong_hs else 0
        pct_thang = round(len(hs_co_kh_thang) / tong_hs * 100, 1) if tong_hs else 0

        kpi = {
            'total_students': tong_hs,
            'students_with_6m': hs_co_kh_khung,
            'pct_khung': pct_khung,
            'pct_khung_int': round(pct_khung),
            'total_plans_all_time': tong_kh_luy_ke,
            'plans_in_month': kh_trong_thang,
            'pct_thang': pct_thang,
            'pct_thang_int': round(pct_thang),
            'active_plans_in_month': kh_dang_can_thiep,
        }

        total_ops = kh_dang_can_thiep + kh_dang_lap + kh_doi_duyet + hs_chua_co_kh
        ops_status = {
            'active': kh_dang_can_thiep,
            'draft': kh_dang_lap,
            'to_approve': kh_doi_duyet,
            'expiring': kh_sap_het_han,
            'no_plan': hs_chua_co_kh,
            'pct_active': round(kh_dang_can_thiep / total_ops * 100, 1) if total_ops else 0,
            'pct_draft': round(kh_dang_lap / total_ops * 100, 1) if total_ops else 0,
            'pct_approve': round(kh_doi_duyet / total_ops * 100, 1) if total_ops else 0,
            'pct_no_plan': round(hs_chua_co_kh / total_ops * 100, 1) if total_ops else 0,
        }
        return kpi, ops_status

    # -------------------------------------------------------------------------
    # HÀM 2: BIỂU ĐỒ SO SÁNH TỪ THÁNG 1 ĐẾN THÁNG ĐANG CHỌN (CHU KỲ NGÀY 15)
    # -------------------------------------------------------------------------
    def func_tinhtoan_luytien_kehoach_trongnam(self, coso_id, nam, thang=None):
        hs_active_records = self.env['ekids.hocsinh'].search_read(
            domain=[('coso_id', '=', coso_id), ('trangthai', '=', '1')],
            fields=['id']
        )
        active_hs_ids = [hs['id'] for hs in hs_active_records]

        kh_records = self.env['ekids.kehoach'].search_read(
            domain=[
                ('coso_id', '=', coso_id),
                ('hocsinh_id', 'in', active_hs_ids),
            ],
            fields=['tu_ngay']
        ) if active_hs_ids else []

        tu_ngay_list = [
            fields.Date.to_date(r['tu_ngay'])
            for r in kh_records if r.get('tu_ngay')
        ]

        labels, bars, lines = [], [], []
        for m in range(1, thang + 1):
            d_thangnay_15 = date(nam, m, 15)
            d_thangtruoc_15 = d_thangnay_15 - relativedelta(months=1)

            tong_hs = hocsinh_util.func_tong_hocsinh_trongthang(self, coso_id, nam, m)
            kh_trong_thang = sum(1 for d in tu_ngay_list if d_thangtruoc_15 < d <= d_thangnay_15)

            labels.append(f"T{m}")
            bars.append(tong_hs)
            lines.append(kh_trong_thang)

        return {
            'labels': labels,
            'bars': bars,
            'lines': lines,
        }

    # -------------------------------------------------------------------------
    # HÀM 3: BẢNG THỐNG KÊ GIÁO VIÊN CẬP NHẬT KẾT QUẢ TUẦN (TẦNG 3)
    # -------------------------------------------------------------------------
    def func_tinhtoan_quatrinh_capnhat_ketqua_canthiep(self, coso_id, nam, thang, tuan_tu_ngay=None, tuan_den_ngay=None):
        d_thangnay_15 = date(nam, thang, 15)
        d_thangtruoc_15 = d_thangnay_15 - relativedelta(months=1)

        tu_ngay_tuan = tuan_tu_ngay or date(nam, thang, 1)
        den_ngay_tuan = tuan_den_ngay or date(nam, thang, calendar.monthrange(nam, thang)[1])

        # Lấy kế hoạch của học sinh đang theo học trong chu kỳ tháng này
        kehoach_recs = self.env['ekids.kehoach'].search([
            ('coso_id', '=', coso_id),
            ('hocsinh_id.trangthai', '=', '1'),
            ('tu_ngay', '>', d_thangtruoc_15),
            ('tu_ngay', '<=', d_thangnay_15),
        ], order='hocsinh_id asc, id asc')

        # Kiểm tra cập nhật kết quả trong khoảng ngày của tuần đang chọn
        last_update_map = {}
        if kehoach_recs:
            kq_groups = self.env['ekids.kehoach_ketqua2muctieu']._read_group(
                domain=[
                    ('kehoach_muctieu_id.kehoach_linhvuc_id.kehoach_id', 'in', kehoach_recs.ids),
                    ('ngay', '>=', tu_ngay_tuan),
                    ('ngay', '<=', den_ngay_tuan),
                    '|', '|',
                    ('is_giaovien_capnhat', '=', True),
                    ('solan_thu_dat', '>', 0),
                    ('trangthai', 'in', ['0', '1', '2']),
                ],
                groupby=['kehoach_muctieu_id'],
                aggregates=['ngay:max'],
            )
            for muctieu, max_ngay in kq_groups:
                if muctieu and max_ngay:
                    kh_id = muctieu.kehoach_linhvuc_id.kehoach_id.id
                    if kh_id not in last_update_map or max_ngay > last_update_map[kh_id]:
                        last_update_map[kh_id] = max_ngay

        grouped_students = {}
        total_plans = 0
        done_count = 0

        tag_palettes = [
            "",
            "background: #ede9fe; color: #6d28d9;",
            "background: #dcfce7; color: #15803d;",
            "background: #fef3c7; color: #b45309;",
        ]

        for kh in kehoach_recs:
            hs = kh.hocsinh_id
            if not hs:
                continue

            if hs.id not in grouped_students:
                grouped_students[hs.id] = {
                    'stt': len(grouped_students) + 1,
                    'student_id': hs.id,
                    'student_name': hs.name or '',
                    'plans': [],
                }

            last_date = last_update_map.get(kh.id)
            is_done = bool(last_date)

            gv_rec = getattr(kh, 'gv_lapkehoach_id', False) or getattr(kh, 'giaovien_id', False)
            gv_name = gv_rec.name if gv_rec else 'Chưa phân công'
            plan_idx = len(grouped_students[hs.id]['plans'])

            grouped_students[hs.id]['plans'].append({
                'plan_id': kh.id,
                'plan_name': kh.name or f"Kế hoạch tháng {thang:02d}/{nam}",
                'tag_style': tag_palettes[plan_idx % len(tag_palettes)],
                'teacher_name': gv_name,
                'is_done': is_done,
                'last_update_date': last_date.strftime('%d/%m/%Y') if last_date else '',
            })

            total_plans += 1
            if is_done:
                done_count += 1

        students_sorted = sorted(grouped_students.values(), key=lambda x: x['student_name'])
        for idx, st in enumerate(students_sorted, start=1):
            st['stt'] = idx

        return {
            'students': students_sorted,
            'total_plans': total_plans,
            'done_count': done_count,
            'pending_count': total_plans - done_count,
        }