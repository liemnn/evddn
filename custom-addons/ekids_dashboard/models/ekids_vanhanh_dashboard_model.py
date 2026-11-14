# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date
import calendar


class VanhanhDashboard(models.AbstractModel):
    _name = 'ekids.dashboard_vanhanh'
    _description = 'Dashboard Quản trị Hoạt động Trung tâm'

    @api.model
    def get_dashboard_data(self, center_id=None, month_str=None):
        ngay_hientai = fields.Date.context_today(self)

        # 1. XÁC ĐỊNH CƠ SỞ ĐANG CHỌN -> coso_id (int)
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

        # 2. XÁC ĐỊNH THÁNG, NĂM & NGÀY ĐANG CHỌN (TRONG NĂM HIỆN TẠI)
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
        ngay = ngay_hientai if (nam == ngay_hientai.year and thang == ngay_hientai.month) else ngay_cuoi_thang

        # 3. GỌI CÁC HÀM TÍNH TOÁN TỪNG PHẦN
        kpi_data = self.func_tinhtoan_kpi_vanhanh(
            coso_id=coso_id,
            nam=nam,
            thang=thang,
            ngay=ngay,
            ngay_dau_thang=ngay_dau_thang,
            ngay_cuoi_thang=ngay_cuoi_thang,
        )

        tuition_donut = self.func_tinhtoan_cocau_hocphi_thang(
            coso_id=coso_id,
            nam=nam,
            thang=thang,
            ngay_dau_thang=ngay_dau_thang,
            ngay_cuoi_thang=ngay_cuoi_thang,
        )

        charts_data = self.func_tinhtoan_bieudo_taichinh_nam(
            coso_id=coso_id,
            nam=nam,
            thang=thang,
        )

        top_expenses = self.func_tinhtoan_khoanchi_noibat(
            coso_id=coso_id,
            nam=nam,
            thang=thang,
            ngay_dau_thang=ngay_dau_thang,
            ngay_cuoi_thang=ngay_cuoi_thang,
        )

        return {
            'centers': centers,
            'selected_center_id': selected_cs_str,
            'months_options': months_options,
            'selected_month': month_str,
            'thang': thang,
            'nam': nam,
            'kpi': kpi_data,
            'tuition_donut': tuition_donut,
            'charts': charts_data,
            'top_expenses': top_expenses,
        }

    # -------------------------------------------------------------------------
    # HÀM 1: 4 THẺ KPI TẦNG 1 (DOANH THU NĂM, HỌC SINH, GIÁO VIÊN, TỔNG CHI)
    # -------------------------------------------------------------------------
    def func_tinhtoan_kpi_vanhanh(self, coso_id, nam, thang, ngay, ngay_dau_thang, ngay_cuoi_thang):
        # TODO: Thay bằng query thực tế trên ekids.hocphi, ekids.hocsinh, ekids.giaovien, ekids.luong, ekids.thuchi
        return {
            'year_revenue_str': '4,512',
            'year_revenue_unit': 'tỷ đ',
            'year_growth': '+14.2%',
            'year_tuition_str': '4,32 tỷ',
            'year_other_income_str': '188,5 tr',

            'total_students': 126,
            'absent_students_today': 8,

            'total_teachers': 30,
            'absent_teachers_today': 2,

            'month_expense_str': '312,8',
            'month_salary_str': '248,6 tr',
            'month_other_expense_str': '64,2 tr',
        }

    # -------------------------------------------------------------------------
    # HÀM 2: BIỂU ĐỒ TRÒN DONUT CƠ CẤU HỌC PHÍ THÁNG ĐANG CHỌN
    # -------------------------------------------------------------------------
    def func_tinhtoan_cocau_hocphi_thang(self, coso_id, nam, thang, ngay_dau_thang, ngay_cuoi_thang):
        # TODO: Thay bằng query tổng hợp ekids.hocphi trong tháng
        paid = 412.50
        unpaid = 107.50
        exempt = 28.45
        total = round(paid + unpaid + exempt, 2)

        return {
            'total_str': f"{total:,.2f}".replace('.', ',') + " tr",
            'paid_val': paid,
            'paid_str': f"{paid:,.2f}".replace('.', ',') + " tr",
            'paid_pct': round(paid / total * 100, 1) if total else 0,
            'paid_pct_int': round(paid / total * 100) if total else 0,

            'unpaid_val': unpaid,
            'unpaid_str': f"{unpaid:,.2f}".replace('.', ',') + " tr",
            'unpaid_pct': round(unpaid / total * 100, 1) if total else 0,

            'exempt_val': exempt,
            'exempt_str': f"{exempt:,.2f}".replace('.', ',') + " tr",
            'exempt_pct': round(exempt / total * 100, 1) if total else 0,
        }

    # -------------------------------------------------------------------------
    # HÀM 3: 4 BIỂU ĐỒ TỪ T1 -> THÁNG HIỆN TẠI (LỢI NHUẬN, HỌC PHÍ, LƯƠNG, THU-CHI)
    # -------------------------------------------------------------------------
    def func_tinhtoan_bieudo_taichinh_nam(self, coso_id, nam, thang):
        today = fields.Date.context_today(self)
        thang_gioi_han = today.month if nam == today.year else (12 if nam < today.year else 0)

        # Dữ liệu mẫu 12 tháng
        sample_profit = [82, 71, 98, 108, 112, 120, 125, 131, 141, 150, 118, 130]
        sample_tuition = [310, 285, 350, 370, 380, 400, 415, 425, 445, 465, 412, 430]
        sample_salary = [195, 190, 210, 215, 222, 228, 234, 238, 242, 245, 249, 252]
        sample_income = [322, 297, 365, 386, 398, 418, 434, 445, 466, 487, 431, 450]
        sample_expense = [240, 226, 267, 278, 286, 298, 309, 314, 325, 337, 313, 320]

        labels = []
        profit_bars, tuition_bars, salary_bars, io_in_bars, io_out_lines = [], [], [], [], []

        for m in range(1, thang_gioi_han + 1):
            labels.append(f"T{m}")
            profit_bars.append(sample_profit[m - 1])
            tuition_bars.append(sample_tuition[m - 1])
            salary_bars.append(sample_salary[m - 1])
            io_in_bars.append(sample_income[m - 1])
            io_out_lines.append(sample_expense[m - 1])

        return {
            'labels': labels,
            'profit': {'bars': profit_bars, 'lines': profit_bars},
            'tuition': {'bars': tuition_bars, 'lines': tuition_bars},
            'salary': {'bars': salary_bars, 'lines': salary_bars},
            'io': {'bars': io_in_bars, 'lines': io_out_lines},
        }

    # -------------------------------------------------------------------------
    # HÀM 4: KHOẢN CHI NỔI BẬT TRONG THÁNG (GÓC DƯỚI BÊN PHẢI)
    # -------------------------------------------------------------------------
    def func_tinhtoan_khoanchi_noibat(self, coso_id, nam, thang, ngay_dau_thang, ngay_cuoi_thang):
        return {
            'other_income_str': '18,5 tr',
            'total_other_expense_str': '64,2 tr',
            'items': [
                {'label': 'Thực phẩm bếp', 'pct': 54, 'color': '#ef4444', 'val_str': '34,5 tr'},
                {'label': 'Mặt bằng, điện', 'pct': 28, 'color': '#f59e0b', 'val_str': '18,2 tr'},
                {'label': 'Giáo cụ, khác', 'pct': 18, 'color': '#2563eb', 'val_str': '11,5 tr'},
            ]
        }