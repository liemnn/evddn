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
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")




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

        # =====================================================================
        # BƯỚC 1: XÁC ĐỊNH CƠ SỞ ĐANG CHỌN -> TRẢ VỀ BIẾN SỐ NGUYÊN: coso_id
        # =====================================================================
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

        # --> BIẾN CƠ SỞ ĐANG CHỌN (kiểu int để dùng trực tiếp trong ORM/SQL)
        coso_id = int(selected_cs_str)

        # =====================================================================
        # BƯỚC 2: XÁC ĐỊNH THÁNG, NĂM & NGÀY ĐANG CHỌN
        # =====================================================================
        months_options = []
        current_ym = ngay_hientai.strftime('%Y-%m')
        for m in range(1, 13):
            val = f"{ngay_hientai.year}-{m:02d}"
            lbl = f"Tháng {m:02d}/{ngay_hientai.year}" + (" (Tháng này)" if val == current_ym else "")
            months_options.append({'value': val, 'label': lbl})

        valid_months = [m['value'] for m in months_options]
        if not month_str or month_str not in valid_months:
            month_str = current_ym

        # --> CÁC BIẾN THÁNG, NĂM, NGÀY ĐẦU THÁNG, NGÀY CUỐI THÁNG ĐANG CHỌN
        nam, thang = map(int, month_str.split('-'))
        ngay_dau_thang = date(nam, thang, 1)
        ngay_cuoi_thang = date(nam, thang, calendar.monthrange(nam, thang)[1])
        # Biến 'ngay' đại diện cho ngày đang xét trong tháng (nếu là tháng hiện tại thì lấy hôm nay, tháng khác lấy cuối tháng)
        ngay = ngay_hientai if (nam == ngay_hientai.year and thang == ngay_hientai.month) else ngay_cuoi_thang

        # =====================================================================
        # BƯỚC 3: XÁC ĐỊNH TUẦN ĐANG CHỌN (CHO BẢNG TẦNG 3)
        # =====================================================================
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
        tuan_tu_ngay = selected_week['d_from']
        tuan_den_ngay = selected_week['d_to']

        # =====================================================================
        # BƯỚC 4: GỌI CÁC HÀM TÍNH TOÁN VỚI THAM SỐ ĐÃ CHUẨN HÓA
        # Bạn chỉ cần viết logic tính toán vào 3 hàm con bên dưới
        # =====================================================================
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
        )

        # Loại bỏ key d_from/d_to kiểu date trước khi trả JSON về OWL
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
    # HÀM 1: TÍNH TOÁN 5 THẺ KPI (TẦNG 1) & 4 CHỈ SỐ TÌNH TRẠNG HỒ SƠ (TẦNG 2)
    # -------------------------------------------------------------------------
    def _calc_kpi_and_ops(self, coso_id, nam, thang, ngay, ngay_dau_thang, ngay_cuoi_thang):
        """
        Tham số đầu vào sẵn có:
        - coso_id (int): ID cơ sở đang chọn
        - nam (int), thang (int): Năm & Tháng đang chọn
        - ngay (date): Ngày đang xét (hôm nay nếu là tháng hiện tại, ngược lại là cuối tháng)
        - ngay_dau_thang (date), ngay_cuoi_thang (date): Khoảng ngày của tháng đang chọn
        """
        # TODO: Thay các biến dưới đây bằng lệnh ORM / SQL tính từ coso_id, nam, thang, ngay...
        tong_hs = hocsinh_util.func_tong_hocsinh_trongthang(self, coso_id, nam, thang)
        hs_co_kh_khung = kehoach_util.func_count_ketluan_trangthais(self,coso_id,[kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH])
        tong_kh_luy_ke = kehoach_util.func_count_kehoach_trangthais(self,coso_id,0,[kehoach_util.KEHOACH_DANG_PHEDUYET,kehoach_util.KEHOACH_DANG_CANTHIEP,kehoach_util.KEHOACH_HET_HIEULUC],None)
        ngay = date(nam,thang,15)
        trangthais =[kehoach_util.KEHOACH_DANG_LAP
                    ,kehoach_util.KEHOACH_DANG_PHEDUYET
                    ,kehoach_util.KEHOACH_DANG_CANTHIEP
                    ,kehoach_util.KEHOACH_HET_HIEULUC]
        kh_trong_thang = kehoach_util.func_count_kehoach_trangthais(self,coso_id,0,trangthais,ngay)
        kh_dang_can_thiep = kehoach_util.func_count_kehoach_trangthais(self,coso_id,0,[kehoach_util.KEHOACH_DANG_CANTHIEP],ngay)

        kh_dang_lap = kehoach_util.func_count_kehoach_trangthais(self,coso_id,0,[kehoach_util.KEHOACH_DANG_LAP],ngay)
        kh_doi_duyet = kehoach_util.func_count_kehoach_trangthais(self,coso_id,0,[kehoach_util.KEHOACH_DANG_PHEDUYET],ngay)
        kh_sap_het_han = kehoach_util.func_count_kehoach_trangthais(self,coso_id,10,[kehoach_util.KEHOACH_DANG_CANTHIEP],ngay)
        hs_chua_co_kh = max(0, tong_hs - kh_trong_thang)

        pct_khung = round(hs_co_kh_khung / tong_hs * 100, 1) if tong_hs else 0
        pct_thang = round(kh_trong_thang / tong_hs * 100, 1) if tong_hs else 0

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
    # HÀM 2: TÍNH TOÁN BIỂU ĐỒ SO SÁNH TỪ THÁNG 1 ĐẾN THÁNG ĐANG CHỌN (TẦNG 2)
    # -------------------------------------------------------------------------
    def func_tinhtoan_luytien_kehoach_trongnam(self, coso_id, nam, thang=None):


        labels, bars, lines = [], [], []

        # 2. Lặp qua từng tháng từ T1 đến tháng giới hạn để tính toán
        for m in range(1, thang + 1):


            tong_hs = hocsinh_util.func_tong_hocsinh_trongthang(self, coso_id, nam, m)
            trangthais = [kehoach_util.KEHOACH_DANG_LAP
                , kehoach_util.KEHOACH_DANG_PHEDUYET
                , kehoach_util.KEHOACH_DANG_CANTHIEP
                , kehoach_util.KEHOACH_HET_HIEULUC]

            ngay = date(nam, m, 15)
            kh_trong_thang = kehoach_util.func_count_kehoach_trangthais(self, coso_id, 0, trangthais, ngay)

            labels.append(f"T{m}")
            bars.append(tong_hs)
            lines.append(kh_trong_thang)

        return {
            'labels': labels,
            'bars': bars,
            'lines': lines,
        }

    # -------------------------------------------------------------------------
    # HÀM 3: TÍNH TOÁN BẢNG GIÁO VIÊN CẬP NHẬT KẾT QUẢ TUẦN (TẦNG 3)
    # -------------------------------------------------------------------------
    def func_tinhtoan_quatrinh_capnhat_ketqua_canthiep(self, coso_id, nam, thang):
        """
        Lấy danh sách kế hoạch trong tháng/năm của cơ sở coso_id
        và kiểm tra ngày gần nhất giáo viên cập nhật kết quả trong tháng.
        """
        tu_ngay = date(nam, thang, 1)
        last_day = calendar.monthrange(nam, thang)[1]
        den_ngay = date(nam, thang, last_day)

        # 1. Lấy danh sách kế hoạch của cơ sở trong tháng
        kh_model = self.env['ekids.kehoach']
        kh_fields = kh_model._fields
        domain_kh = [('coso_id', '=', coso_id)]

        if 'nam' in kh_fields and 'thang' in kh_fields:
            thang_val = str(thang) if kh_fields['thang'].type == 'selection' else thang
            nam_val = str(nam) if kh_fields['nam'].type == 'selection' else nam
            domain_kh += [('nam', '=', nam_val), ('thang', '=', thang_val)]
        elif 'tu_ngay' in kh_fields and 'den_ngay' in kh_fields:
            domain_kh += [('tu_ngay', '<=', den_ngay), ('den_ngay', '>=', tu_ngay)]
        elif 'ngay_batdau' in kh_fields and 'ngay_ketthuc' in kh_fields:
            domain_kh += [('ngay_batdau', '<=', den_ngay), ('ngay_ketthuc', '>=', tu_ngay)]
        elif 'ngay' in kh_fields:
            domain_kh += [('ngay', '>=', tu_ngay), ('ngay', '<=', den_ngay)]

        kehoach_recs = kh_model.search(domain_kh, order='hocsinh_id asc, id asc')

        # 2. Nhóm trực tiếp theo 'kehoach_muctieu_id' (field trực tiếp trên ekids.kehoach_ketqua2muctieu)
        last_update_map = {}
        if kehoach_recs:
            kq_groups = self.env['ekids.kehoach_ketqua2muctieu']._read_group(
                domain=[
                    ('kehoach_muctieu_id.kehoach_linhvuc_id.kehoach_id', 'in', kehoach_recs.ids),
                    ('ngay', '>=', tu_ngay),
                    ('ngay', '<=', den_ngay),
                    '|', '|',
                    ('is_giaovien_capnhat', '=', True),
                    ('solan_thu_dat', '>', 0),
                    ('trangthai', 'in', ['0', '1', '2']),
                ],
                groupby=['kehoach_muctieu_id'],
                aggregates=['ngay:max'],
            )
            # Quy đổi ngày cập nhật lớn nhất từ từng mục tiêu lên kế hoạch cha
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