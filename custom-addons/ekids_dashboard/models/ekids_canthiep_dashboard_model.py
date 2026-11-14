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
            # Tìm ngày Chủ nhật của tuần hiện tại
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
        if not month_str:
            month_str = today.strftime('%Y-%m')
        nam, thang = map(int, month_str.split('-'))

        first_day = date(nam, thang, 1)
        last_day = date(nam, thang, calendar.monthrange(nam, thang)[1])

        # 1. Lấy danh sách Trung tâm & Danh sách Tháng (6 tháng gần nhất)
        centers = [{'id': 'all', 'name': 'Tất cả trung tâm'}]
        if 'ekids.coso' in self.env:
            coso_recs = self.env['ekids.coso'].search([])
            centers[0]['name'] = f"Tất cả trung tâm ({len(coso_recs)})"
            for cs in coso_recs:
                centers.append({'id': str(cs.id), 'name': cs.name})

        months_options = []
        for i in range(6):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            val = f"{y}-{m:02d}"
            lbl = f"Tháng {m:02d}/{y}" + (" (Tháng này)" if i == 0 else "")
            months_options.append({'value': val, 'label': lbl})

        # 2. Sinh danh sách Tuần động theo tháng và xác định tuần mặc định
        weeks = self.get_weeks_of_month(nam, thang)
        if not week_index or week_index > len(weeks):
            # Mặc định chọn tuần chứa ngày hôm nay nếu đang xem tháng hiện tại, ngược lại chọn tuần 1
            week_index = 1
            if nam == today.year and thang == today.month:
                for w in weeks:
                    if w['date_from'] <= today.strftime('%Y-%m-%d') <= w['date_to']:
                        week_index = w['index']
                        break
        selected_week = next((w for w in weeks if w['index'] == week_index), weeks[0])

        # Điều kiện lọc Cơ sở dùng chung cho SQL
        coso_sql = ""
        params_coso = []
        if center_id != 'all':
            coso_sql = " AND coso_id = %s "
            params_coso = [int(center_id)]

        # ---------------------------------------------------------------------
        # 3. TRUY VẤN REAL-TIME TẦNG 1 & TẦNG 2 (GỘP 1 LẦN QUÉT SQL)
        # ---------------------------------------------------------------------
        # Lưu ý: Sửa lại tên bảng/cột trạng thái ('trangthai', 'state') khớp với model của bạn
        self.env.cr.execute(f"""
            SELECT
                COUNT(*) AS tong_hs
            FROM ekids_hocsinh
            WHERE active = TRUE
              AND trangthai = 'danghoc'
              {coso_sql}
        """, params_coso)
        tong_hs = self.env.cr.fetchone()[0] or 0

        # Truy vấn toàn bộ chỉ số Kế hoạch trong 1 câu SQL
        self.env.cr.execute(f"""
            SELECT
                -- Số HS có kế hoạch khung (6 tháng) còn hiệu lực trong tháng
                COUNT(DISTINCT hocsinh_id) FILTER (
                    WHERE loai_kehoach = 'khung'
                      AND ngay_batdau <= %s AND ngay_ketthuc >= %s
                ) AS hs_co_kh_khung,

                -- Tổng kế hoạch đã lập (lũy kế)
                COUNT(*) AS tong_kh_luy_ke,

                -- Số KH tháng đã lập trong tháng đang xem
                COUNT(*) FILTER (
                    WHERE loai_kehoach = 'thang'
                      AND nam = %s AND thang = %s
                ) AS kh_trong_thang,

                -- Số KH đang can thiệp (đã duyệt) trong tháng
                COUNT(*) FILTER (
                    WHERE loai_kehoach = 'thang'
                      AND nam = %s AND thang = %s
                      AND state = 'dangcanthiep'
                ) AS kh_dang_can_thiep,

                -- Số KH đang lập (nháp)
                COUNT(*) FILTER (
                    WHERE loai_kehoach = 'thang'
                      AND nam = %s AND thang = %s
                      AND state = 'draft'
                ) AS kh_dang_lap,

                -- Số KH đợi duyệt
                COUNT(*) FILTER (
                    WHERE loai_kehoach = 'thang'
                      AND nam = %s AND thang = %s
                      AND state = 'choduyet'
                ) AS kh_doi_duyet,

                -- Số KH sắp hết hạn (trong vòng 7 ngày tới)
                COUNT(*) FILTER (
                    WHERE state = 'dangcanthiep'
                      AND ngay_ketthuc BETWEEN %s AND %s
                ) AS kh_sap_het_han,

                -- Số HS duy nhất đã có kế hoạch trong tháng (để tính HS chưa có KH)
                COUNT(DISTINCT hocsinh_id) FILTER (
                    WHERE loai_kehoach = 'thang'
                      AND nam = %s AND thang = %s
                ) AS hs_da_co_kh_thang
            FROM ekids_kehoach
            WHERE active = TRUE
              {coso_sql}
        """, [
            last_day, first_day,
            nam, thang,
            nam, thang,
            nam, thang,
            nam, thang,
            today, today + timedelta(days=7),
            nam, thang,
        ] + params_coso)

        row_kh = self.env.cr.fetchone()
        hs_co_kh_khung = row_kh[0] or 0
        tong_kh_luy_ke = row_kh[1] or 0
        kh_trong_thang = row_kh[2] or 0
        kh_dang_can_thiep = row_kh[3] or 0
        kh_dang_lap = row_kh[4] or 0
        kh_doi_duyet = row_kh[5] or 0
        kh_sap_het_han = row_kh[6] or 0
        hs_da_co_kh_thang = row_kh[7] or 0
        hs_chua_co_kh = max(0, tong_hs - hs_da_co_kh_thang)

        pct_khung = round(hs_co_kh_khung / tong_hs * 100, 1) if tong_hs else 0
        pct_thang = round(kh_trong_thang / tong_hs * 100, 1) if tong_hs else 0

        # ---------------------------------------------------------------------
        # 4. BIỂU ĐỒ SO SÁNH TỪ T1 -> THÁNG ĐANG XEM (1 CÂU GROUP BY)
        # ---------------------------------------------------------------------
        self.env.cr.execute(f"""
            SELECT
                thang,
                COUNT(DISTINCT hocsinh_id) AS so_hs,
                COUNT(*) AS so_kh
            FROM ekids_kehoach
            WHERE active = TRUE
              AND loai_kehoach = 'thang'
              AND nam = %s
              AND thang <= %s
              {coso_sql}
            GROUP BY thang
            ORDER BY thang
        """, [nam, thang] + params_coso)

        chart_map = {r[0]: (r[1], r[2]) for r in self.env.cr.fetchall()}
        labels, bars, lines = [], [], []
        for m in range(1, thang + 1):
            labels.append(f"T{m}")
            bars.append(chart_map.get(m, (0, 0))[0])
            lines.append(chart_map.get(m, (0, 0))[1])

        # Tính tỷ lệ % thanh phân bổ Tầng 2
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
        # 5. BẢNG THỐNG KÊ CẬP NHẬT TUẦN (TẦNG 3) - DÙNG EXISTS TRÁNH NHÂN BẢN DÒNG
        # ---------------------------------------------------------------------
        coso_kh_sql = " AND kh.coso_id = %s " if center_id != 'all' else ""
        params_tuan = [
            selected_week['date_from'],
            selected_week['date_to'],
            nam,
            thang,
        ] + params_coso

        self.env.cr.execute(f"""
            SELECT
                hs.id AS student_id,
                hs.name AS student_name,
                kh.id AS plan_id,
                kh.name AS plan_name,
                gv.name AS teacher_name,
                EXISTS (
                    SELECT 1
                    FROM ekids_kehoach_ketqua2muctieu kq
                    WHERE kq.kehoach_id = kh.id
                      AND kq.ngay_danhgia BETWEEN %s AND %s
                      AND kq.ketqua IS NOT NULL
                ) AS is_done
            FROM ekids_kehoach kh
            JOIN ekids_hocsinh hs ON hs.id = kh.hocsinh_id
            LEFT JOIN ekids_giaovien gv ON gv.id = kh.giaovien_id
            WHERE kh.active = TRUE
              AND kh.loai_kehoach = 'thang'
              AND kh.nam = %s
              AND kh.thang = %s
              AND kh.state = 'dangcanthiep'
              {coso_kh_sql}
            ORDER BY hs.name, kh.id
        """, params_tuan)

        grouped_students = {}
        total_plans_week = 0
        done_count = 0

        # Bảng màu nhãn xoay vòng cho các kế hoạch của cùng 1 học sinh
        tag_palettes = [
            "",
            "background: #ede9fe; color: #6d28d9;",
            "background: #dcfce7; color: #15803d;",
            "background: #fef3c7; color: #b45309;",
        ]

        for r in self.env.cr.fetchall():
            st_id, st_name, plan_id, plan_name, gv_name, is_done = r
            if st_id not in grouped_students:
                grouped_students[st_id] = {
                    'stt': len(grouped_students) + 1,
                    'student_id': st_id,
                    'student_name': st_name,
                    'plans': [],
                }
            plan_idx = len(grouped_students[st_id]['plans'])
            grouped_students[st_id]['plans'].append({
                'plan_id': plan_id,
                'plan_name': plan_name,
                'tag_style': tag_palettes[plan_idx % len(tag_palettes)],
                'teacher_name': gv_name or 'Chưa phân công',
                'is_done': bool(is_done),
            })
            total_plans_week += 1
            if is_done:
                done_count += 1

        return {
            'centers': centers,
            'months_options': months_options,
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
                'students': list(grouped_students.values()),
                'total_plans': total_plans_week,
                'done_count': done_count,
                'pending_count': total_plans_week - done_count,
            }
        }