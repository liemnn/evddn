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
    def get_dashboard_data(self, center_id=None, month_str=None, week_index=None):
        today = fields.Date.context_today(self)

        # 1A. DANH SÁCH CƠ SỞ (KHÔNG CÓ "TẤT CẢ", MẶC ĐỊNH CHỌN 1 CƠ SỞ ĐẦU TIÊN)
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
            # Ưu tiên lấy cơ sở mặc định của user nếu nằm trong danh sách hợp lệ, ngược lại lấy cơ sở đầu tiên
            default_cs = str(user.coso_id.id) if (hasattr(user, 'coso_id') and user.coso_id) else ''
            if default_cs in valid_center_ids:
                center_id = default_cs
            else:
                center_id = valid_center_ids[0] if valid_center_ids else '0'
        else:
            center_id = str(center_id)

        # 1B. DANH SÁCH THÁNG: CHỈ CÁC THÁNG TRONG NĂM NAY, MẶC ĐỊNH LÀ THÁNG NÀY
        months_options = []
        current_ym = today.strftime('%Y-%m')
        for m in range(1, 13):
            val = f"{today.year}-{m:02d}"
            lbl = f"Tháng {m:02d}/{today.year}" + (" (Tháng này)" if val == current_ym else "")
            months_options.append({'value': val, 'label': lbl})

        valid_months = [m['value'] for m in months_options]
        if not month_str or month_str not in valid_months:
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
        # Tạo hệ số riêng theo ID cơ sở để thấy rõ sự khác biệt khi chuyển cơ sở
        cs_index = valid_center_ids.index(center_id) if center_id in valid_center_ids else 0
        scale = 1.0 if cs_index == 0 else max(0.5, 1.0 - cs_index * 0.25)
        month_offset = abs(today.month - thang)

        tong_hs = max(10, int(round((86 - month_offset * 2) * scale)))
        hs_co_kh_khung = max(8, int(round((82 - month_offset * 2) * scale)))
        tong_kh_luy_ke = max(40, int(round((520 - month_offset * 30) * scale)))
        kh_trong_thang = max(8, int(round((80 - month_offset * 2) * scale)))
        kh_dang_can_thiep = max(6, int(round((75 - month_offset * 2) * scale)))

        kh_dang_lap = 3 if cs_index == 0 else 2
        kh_doi_duyet = 2 if cs_index == 0 else 1
        kh_sap_het_han = 5 if cs_index == 0 else 3
        hs_chua_co_kh = max(0, tong_hs - kh_trong_thang)

        pct_khung = round(hs_co_kh_khung / tong_hs * 100, 1) if tong_hs else 0
        pct_thang = round(kh_trong_thang / tong_hs * 100, 1) if tong_hs else 0

        # ---------------------------------------------------------------------
        # 4. DỮ LIỆU GIẢ LẬP BIỂU ĐỒ TỪ T1 -> THÁNG ĐANG XEM
        # ---------------------------------------------------------------------
        base_bars = [70, 72, 74, 75, 77, 79, 80, 82, 84, 85, 86, 88]
        base_lines = [65, 68, 70, 72, 74, 75, 76, 78, 79, 80, 80, 84]

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
        ]

        if cs_index > 0:
            mock_students = mock_students[:2]

        all_plans = [p for st in mock_students for p in st['plans']]
        done_count = sum(1 for p in all_plans if p['is_done'])
        pending_count = len(all_plans) - done_count

        return {
            'centers': centers,
            'selected_center_id': center_id,
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