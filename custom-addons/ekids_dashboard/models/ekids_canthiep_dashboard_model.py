# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date, timedelta
import calendar


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
            })
            curr = week_end + timedelta(days=1)
            idx += 1
        return weeks

    @api.model
    def get_dashboard_data(self, center_id='all', month_str=None, week_index=None):
        today = fields.Date.context_today(self)

        # 1A. LẤY DANH SÁCH CƠ SỞ THỰC TẾ TRONG HỆ THỐNG (ĐỂ LỌC THẬT)
        centers = []
        user = self.env.user
        if 'ekids.coso' in self.env:
            if hasattr(user, 'coso_ids') and user.coso_ids and not user.has_group('base.group_system'):
                coso_recs = user.coso_ids
            else:
                coso_recs = self.env['ekids.coso'].search([])

            if len(coso_recs) > 1:
                centers.append({'id': 'all', 'name': f'Tất cả trung tâm ({len(coso_recs)})'})
            for cs in coso_recs:
                centers.append({'id': str(cs.id), 'name': cs.name})
        else:
            centers = [
                {'id': 'all', 'name': 'Tất cả trung tâm (2)'},
                {'id': '1', 'name': 'Trung tâm eKids Cơ sở 1'},
                {'id': '2', 'name': 'Trung tâm eKids Cơ sở 2'},
            ]

        valid_center_ids = [c['id'] for c in centers]
        if str(center_id) not in valid_center_ids:
            center_id = valid_center_ids[0] if valid_center_ids else 'all'

        # 1B. LẤY DANH SÁCH 12 THÁNG GẦN NHẤT ĐỂ LỌC
        months_options = []
        current_ym = today.strftime('%Y-%m')
        for i in range(12):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            val = f"{y}-{m:02d}"
            lbl = f"Tháng {m:02d}/{y}" + (" (Tháng này)" if val == current_ym else "")
            months_options.append({'value': val, 'label': lbl})

        if not month_str:
            month_str = current_ym
        nam, thang = map(int, month_str.split('-'))

        # 2. SINH DANH SÁCH TUẦN ĐỘNG THEO THÁNG
        weeks = self.get_weeks_of_month(nam, thang)
        if not week_index or int(week_index) > len(weeks):
            week_index = 1
            if nam == today.year and thang == today.month:
                for w in weeks:
                    if w['date_from'] <= today.strftime('%Y-%m-%d') <= w['date_to']:
                        week_index = w['index']
                        break
        else:
            week_index = int(week_index)

        selected_week = next((w for w in weeks if w['index'] == week_index), weeks[0])

        # ---------------------------------------------------------------------
        # 3. DỮ LIỆU GIẢ LẬP TẦNG 1 & TẦNG 2 (BIẾN THIÊN THEO CƠ SỞ & THÁNG)
        # ---------------------------------------------------------------------
        # Hệ số nhân giả lập để khi đổi Cơ sở hoặc Tháng thấy số liệu thay đổi trực quan
        scale = 1.0 if center_id == 'all' else 0.55
        month_offset = (12 - thang)

        tong_hs = max(10, int(round((126 - month_offset * 2) * scale)))
        hs_co_kh_khung = max(8, int(round((121 - month_offset * 2) * scale)))
        tong_kh_luy_ke = max(50, int(round((842 - month_offset * 45) * scale)))
        kh_trong_thang = max(8, int(round((118 - month_offset * 2) * scale)))
        kh_dang_can_thiep = max(6, int(round((112 - month_offset * 2) * scale)))

        kh_dang_lap = 4 if center_id == 'all' else 2
        kh_doi_duyet = 2 if center_id == 'all' else 1
        kh_sap_het_han = 9 if center_id == 'all' else 4
        hs_chua_co_kh = max(0, tong_hs - kh_trong_thang)

        pct_khung = round(hs_co_kh_khung / tong_hs * 100, 1) if tong_hs else 0
        pct_thang = round(kh_trong_thang / tong_hs * 100, 1) if tong_hs else 0

        # ---------------------------------------------------------------------
        # 4. DỮ LIỆU GIẢ LẬP BIỂU ĐỒ TỪ T1 -> THÁNG ĐANG XEM
        # ---------------------------------------------------------------------
        base_bars = [105, 102, 110, 112, 115, 118, 120, 121, 123, 125, 126, 128]
        base_lines = [98, 95, 105, 108, 110, 112, 115, 116, 118, 120, 118, 122]

        labels, bars, lines = [], [], []
        for m in range(1, thang + 1):
            labels.append(f"T{m}")
            bars.append(int(round(base_bars[m - 1] * scale)))
            lines.append(int(round(base_lines[m - 1] * scale)))

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

        # ---------------------------------------------------------------------
        # 5. DỮ LIỆU GIẢ LẬP BẢNG THỐNG KÊ CẬP NHẬT TUẦN (TẦNG 3)
        # ---------------------------------------------------------------------
        # Đảo trạng thái done/pending nhẹ theo tuần được chọn để test bộ lọc Tuần
        is_even_week = (week_index % 2 == 0)

        mock_students = [
            {
                'stt': 1,
                'student_id': 101,
                'student_name': 'Nguyễn Minh Khôi',
                'plans': [
                    {
                        'plan_id': 1001,
                        'plan_name': 'Can thiệp cá nhân 1-1 (Ngôn ngữ)',
                        'tag_style': '',
                        'teacher_name': 'Phùng Thị Lan',
                        'is_done': True,
                    },
                    {
                        'plan_id': 1002,
                        'plan_name': 'Can thiệp Vận động & Hành vi',
                        'tag_style': 'background: #ede9fe; color: #6d28d9;',
                        'teacher_name': 'Dương Thị Xim',
                        'is_done': not is_even_week,
                    },
                ],
            },
            {
                'stt': 2,
                'student_id': 102,
                'student_name': 'Trần Bảo An',
                'plans': [
                    {
                        'plan_id': 1003,
                        'plan_name': f'Kế hoạch can thiệp tháng {thang:02d}',
                        'tag_style': '',
                        'teacher_name': 'Dương Thị Xim',
                        'is_done': False,
                    },
                ],
            },
            {
                'stt': 3,
                'student_id': 103,
                'student_name': 'Lê Gia Hân',
                'plans': [
                    {
                        'plan_id': 1004,
                        'plan_name': 'Can thiệp cá nhân 1-1',
                        'tag_style': '',
                        'teacher_name': 'Nguyễn Thu Hà',
                        'is_done': True,
                    },
                    {
                        'plan_id': 1005,
                        'plan_name': 'Kế hoạch lớp Bán trú',
                        'tag_style': 'background: #dcfce7; color: #15803d;',
                        'teacher_name': 'Lê Thị Mai Anh',
                        'is_done': True,
                    },
                ],
            },
            {
                'stt': 4,
                'student_id': 104,
                'student_name': 'Phạm Đức Duy',
                'plans': [
                    {
                        'plan_id': 1006,
                        'plan_name': 'Can thiệp cá nhân 1-1',
                        'tag_style': '',
                        'teacher_name': 'Phùng Thị Lan',
                        'is_done': is_even_week,
                    },
                ],
            },
            {
                'stt': 5,
                'student_id': 105,
                'student_name': 'Đỗ Hoàng Nam',
                'plans': [
                    {
                        'plan_id': 1007,
                        'plan_name': 'Can thiệp Nhận thức - Ngôn ngữ',
                        'tag_style': '',
                        'teacher_name': 'Lê Thị Mai Anh',
                        'is_done': False,
                    },
                    {
                        'plan_id': 1008,
                        'plan_name': 'Can thiệp Nhóm kỹ năng',
                        'tag_style': 'background: #fef3c7; color: #b45309;',
                        'teacher_name': 'Trần Thanh Thảo',
                        'is_done': not is_even_week,
                    },
                ],
            },
        ]

        # Nếu lọc 1 cơ sở cụ thể, lấy 3 học sinh đầu để thấy danh sách thay đổi
        if center_id != 'all':
            mock_students = mock_students[:3]

        all_plans = [p for st in mock_students for p in st['plans']]
        done_count = sum(1 for p in all_plans if p['is_done'])
        pending_count = len(all_plans) - done_count

        return {
            'centers': centers,
            'selected_center_id': str(center_id),
            'months_options': months_options,
            'selected_month': month_str,
            'weeks': weeks,
            'selected_week_index': selected_week['index'],
            'kpi': {
                'total_students': tong_hs,
                'students_with_6m': hs_co_kh_khung,
                'pct_khung': pct_khung,
                'pct_khung_int': round(pct_khung),
                'total_plans_all_time': tong_kh_luy_ke,
                'plans_in_month': kh_trong_thang,
                'pct_thang': pct_thang,
                'pct_thang_int': round(pct_thang),
                'active_plans_in_month': kh_dang_can_thiep,
            },
            'chart_compare': {'labels': labels, 'bars': bars, 'lines': lines},
            'ops_status': ops_status,
            'weekly': {
                'students': mock_students,
                'total_plans': len(all_plans),
                'done_count': done_count,
                'pending_count': pending_count,
            }
        }