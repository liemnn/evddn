# -*- coding: utf-8 -*-
import logging
import textwrap
import uuid
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, http

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import kehoach_util
except ImportError as e:
    _logger.warning("Không thể import ekids_func: %s", e)


class HocSinhKeHoachHoSoAbstractModel(models.AbstractModel):
    _register = False
    _description = 'Abstract Xử lý dữ liệu Hồ sơ can thiệp'

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_print_hoso_report(self):
        """Action in báo cáo trực tiếp từ Form view"""
        self.ensure_one()
        return self.env.ref('ekids_canthiep.kehoach_hoso_template_action').report_action(self)

    # =========================================================================
    # MAIN DATA BUILDER (UNIFIED TIMELINE + SMART VIEW SWITCHER)
    # =========================================================================
    def _get_hoso_report_data(self):
        """Chuẩn bị dữ liệu cho Hồ sơ can thiệp theo trục thời gian thống nhất"""
        self.ensure_one()
        KeHoachModel = self.env['ekids.kehoach']

        # 1. Lấy toàn bộ lịch sử kế hoạch theo trục thời gian (mới nhất lên đầu)
        ds_kehoach, selected_plan = self._resolve_timeline_plans(KeHoachModel)

        # 2. Xác định trạng thái kế hoạch đang chọn:
        #    '-1' = Đã kết thúc (có báo cáo), '1' = Đang can thiệp, '0' = Đang lập
        is_closed = bool(selected_plan and selected_plan.trangthai == '-1')

        # 3. Xác định chế độ xem (view_mode): 'report' | 'full' | 'compact'
        req_mode = self._get_request_param('view_mode', context_key='view_mode')
        if is_closed:
            view_mode = req_mode if req_mode in ['report', 'full', 'compact'] else 'report'
        else:
            # Kế hoạch đang lập / đang can thiệp chưa có báo cáo -> mặc định mở bản đầy đủ ('full')
            view_mode = req_mode if req_mode in ['full', 'compact'] else 'full'

        # 4. Dữ liệu báo cáo tổng kết (chỉ tính khi kỳ đã đóng)
        tab1_data = self.func_get_baocao_kehoach(selected_plan) if is_closed else self._get_empty_baocao_data()

        # 5. Profile & Token chia sẻ
        profile_data = self._build_hocsinh_profile()

        # 6. Thông tin giáo viên & chuyên môn của kỳ đang chọn
        gv_name = selected_plan.gv_lapkehoach_id.name if selected_plan and selected_plan.gv_lapkehoach_id else 'Chưa phân công'
        ql_name = selected_plan.gv_kiemduyet_id.name if selected_plan and selected_plan.gv_kiemduyet_id else 'Ngô Thị Ngọc Hoàn'

        return {
            'has_any_plan': bool(selected_plan),
            'is_closed': is_closed,
            'current_plan_id': selected_plan.id if selected_plan else 0,
            'selected_plan': selected_plan,
            'view_mode': view_mode,
            'ds_kehoach': ds_kehoach,
            'hocsinh': profile_data,
            'tab1': tab1_data,
            'plan_giaovien': gv_name,
            'plan_quanly': ql_name,
            'plan_status_code': selected_plan.trangthai if selected_plan else '',
            'plan_status_label': self._get_plan_status_label(selected_plan.trangthai) if selected_plan else '',
        }

    def _get_plan_status_label(self, code):
        mapping = {
            '-1': 'Đã hoàn thành',
            '1': 'Đang can thiệp',
            '0': 'Đang lập kế hoạch',
        }
        return mapping.get(str(code), 'Đang thực hiện')

    # =========================================================================
    # TIMELINE RESOLVER
    # =========================================================================
    def _resolve_timeline_plans(self, KeHoachModel):
        """Lấy toàn bộ kế hoạch của trẻ sắp xếp theo dòng thời gian giảm dần"""
        """Chỉ lấy các kế hoạch Đang can thiệp ('1') hoặc Đã kết thúc ('-1'), bỏ qua kế hoạch đang lập/chờ duyệt"""
        all_plans = KeHoachModel.search(
            [
                ('hocsinh_id', '=', self.id),
                ('trangthai', 'in', [
                    kehoach_util.KEHOACH_DANG_CANTHIEP,  # '1'
                    kehoach_util.KEHOACH_HET_HIEULUC,  # '-1'
                ]),
            ],
            order='tu_ngay desc, den_ngay desc, id desc'
        )

        ds_kehoach = []
        valid_ids = set()
        for p in all_plans:
            valid_ids.add(p.id)
            gv_name = p.gv_lapkehoach_id.name if p.gv_lapkehoach_id else 'Chưa phân công'
            ten_kh = p.name or 'Kế hoạch'
            tu_str = p.tu_ngay.strftime('%d/%m') if p.tu_ngay else ''
            den_str = p.den_ngay.strftime('%d/%m/%Y') if p.den_ngay else ''
            thoigian = f"{tu_str} - {den_str}" if tu_str and den_str else ''

            st_code = str(p.trangthai or '0')
            is_done = (st_code == '-1')

            # Đồng bộ tỷ lệ hoàn thành trên Timeline khớp 100% với KPI báo cáo bên dưới
            if is_done:
                tyle_dat = self._compute_plan_mastery_rate(p)
                badge_text = f"Hoàn thành • Đạt {tyle_dat}%"
                st_type = 'done'
            elif st_code == '1':
                tyle_dat = round(p.tyle_dat_canthiep or 0)
                badge_text = "Đang can thiệp"
                st_type = 'active'
            else:
                tyle_dat = 0
                badge_text = "Đang lập Kế hoạch"
                st_type = 'draft'

            ds_kehoach.append({
                'id': p.id,
                'ten': ten_kh,
                'thoigian': thoigian,
                'gv_name': gv_name,
                'trangthai': st_code,
                'is_done': is_done,
                'tyle_dat': tyle_dat,
                'badge_text': badge_text,
                'st_type': st_type,
            })

        param_id = self._get_request_param('kehoach_id', context_key='kehoach_id')
        selected_record = False
        if param_id:
            try:
                pid = int(param_id)
                if pid in valid_ids:
                    selected_record = KeHoachModel.browse(pid)
            except (ValueError, TypeError):
                pass

        if not selected_record and all_plans:
            selected_record = all_plans[0]

        return ds_kehoach, selected_record

    def _compute_plan_mastery_rate(self, kehoach):
        """Tính tỷ lệ % mục tiêu đạt của một kế hoạch theo đúng tiêu chí của Báo cáo tổng kết"""
        if not kehoach:
            return 0
        muctieus = kehoach.kehoach_linhvuc_ids.kehoach_muctieu_ids
        total_targets = len(muctieus)
        if not total_targets:
            return round(getattr(kehoach, 'tyle_dat_kiemduyet', 0) or getattr(kehoach, 'tyle_dat_canthiep', 0) or 0)

        count_dat = 0
        for mt in muctieus:
            tyle_sau = mt.tyle_kiemduyet if mt.tyle_kiemduyet > 0 else (getattr(mt, 'tyle_canthiep', 0) or mt.tyle_thu)
            is_mastered = (tyle_sau >= 80) or (mt.trangthai_kiemduyet == '1') or (mt.trangthai == '1')
            if is_mastered:
                count_dat += 1

        return round((count_dat / total_targets) * 100)

    # =========================================================================
    # TAB 1 LOGIC: BÁO CÁO KẾT QUẢ KỲ ĐÃ ĐÓNG (trangthai == '-1')
    # =========================================================================
    def func_get_baocao_kehoach(self, kehoach):
        """Tổng hợp kết quả can thiệp, dữ liệu phân nhóm lĩnh vực và tọa độ SVG biểu đồ"""
        if not kehoach:
            return self._get_empty_baocao_data()

        linhvuc_lines = kehoach.kehoach_linhvuc_ids.sorted(key=lambda r: r.sequence)

        count_dat = 0
        total_targets = 0
        cung_co_dict = {}
        duy_tri_dict = {}
        linhvucs_grouped = []
        chart_linhvucs = []

        global_idx = 1
        for lv_line in linhvuc_lines:
            mts = lv_line.kehoach_muctieu_ids.sorted(key=lambda m: (m.sequence, m.id))
            # Ẩn hoàn toàn lĩnh vực không có mục tiêu nào khỏi báo cáo, biểu đồ và chỉ số điểm trũng
            if not mts:
                continue

            lv_name = lv_line.linhvuc_id.name if lv_line.linhvuc_id else 'Khác'
            tuoi_name = lv_line.tuoi_id.name if lv_line.tuoi_id else ''

            chuongtrinh = (
                lv_line.tuoi_id.chuongtrinh_id.name
                if lv_line.tuoi_id and lv_line.tuoi_id.chuongtrinh_id
                else (lv_line.chuongtrinh_id.name if hasattr(lv_line, 'chuongtrinh_id') and lv_line.chuongtrinh_id else '')
            )

            targets = []
            for mt in mts:
                total_targets += 1
                item_data, is_mastered = self._format_tab1_target(mt, global_idx)
                targets.append(item_data)
                global_idx += 1

                if is_mastered:
                    count_dat += 1
                    cung_co_dict.setdefault(lv_name, []).append(item_data['muctieu'])
                else:
                    duy_tri_dict.setdefault(lv_name, []).append(item_data['muctieu'])
            lv_line._compute_tyle()
            avg_thu = lv_line.tyle_thu
            avg_dat = lv_line.tyle_dat
            linhvucs_grouped.append({
                'linhvuc': lv_name,
                'tuoi': tuoi_name,
                'chuongtrinh': chuongtrinh,
                'avg_thu': avg_thu,
                'avg_dat': avg_dat,
                'tien_bo': avg_dat - avg_thu,
                'total_mt': len(targets),
                'targets': targets,
            })

            chart_linhvucs.append({
                'name': lv_name,
                'lines': textwrap.wrap(lv_name, width=9) if lv_name else ['Khác'],
                'tyle_thu': avg_thu,
                'tyle_dat': avg_dat,
            })

        chart_data = self._build_svg_chart_data(chart_linhvucs)

        sorted_temp = sorted(chart_linhvucs, key=lambda x: x['tyle_dat'], reverse=True)
        but_pha = f"{sorted_temp[0]['name']} ({sorted_temp[0]['tyle_dat']}%)" if sorted_temp else "Chưa có"
        diem_trung = f"{sorted_temp[-1]['name']} ({sorted_temp[-1]['tyle_dat']}%)" if sorted_temp else "Chưa có"

        tong_dat = count_dat if total_targets else getattr(kehoach, 'tong_dat_kiemduyet', 0)
        rate_t1 = round((tong_dat / total_targets * 100)) if total_targets else getattr(kehoach, 'tyle_dat_kiemduyet', 0) or getattr(kehoach, 'tyle_dat_canthiep', 0)

        return {
            "ten": kehoach.name or 'Kế hoạch',
            "giaovien": kehoach.gv_lapkehoach_id.name if kehoach.gv_lapkehoach_id else 'Chưa phân công',
            "tieu_de_hien_thi": f"{kehoach.name or 'Kế hoạch'} (Giáo viên: {kehoach.gv_lapkehoach_id.name if kehoach.gv_lapkehoach_id else 'Chưa phân công'})",
            "quanly": kehoach.gv_kiemduyet_id.name if kehoach.gv_kiemduyet_id else 'Ngô Thị Ngọc Hoàn',
            "tong_muctieu": kehoach.tong_muctieu or total_targets,
            "tong_muctieu_dat": tong_dat,
            "tyle_dat": rate_t1,
            "diem_trung": diem_trung,
            "but_pha": but_pha,
            "nhan_xet": getattr(kehoach, 'nhanxet', False) or kehoach.desc or "",
            "dinh_huong_thang_toi": getattr(kehoach, 'dinhhuong', False) or "",
            "dinh_huong_cung_co": [{'linhvuc': k, 'targets': v} for k, v in cung_co_dict.items()],
            "dinh_huong_duy_tri": [{'linhvuc': k, 'targets': v} for k, v in duy_tri_dict.items()],
            "ten_thang_toi": self._compute_label_thang_toi(kehoach),
            "linhvucs_grouped": linhvucs_grouped,
            "chart": chart_data,
        }

    def _format_tab1_target(self, mt, stt):
        """Định dạng dữ liệu 1 mục tiêu của báo cáo"""
        tyle_sau = mt.tyle_kiemduyet if mt.tyle_kiemduyet > 0 else (getattr(mt, 'tyle_canthiep', 0) or mt.tyle_thu)
        is_mastered = (tyle_sau >= 80) or (mt.trangthai_kiemduyet == '1') or (mt.trangthai == '1')
        muc_do_label = "Củng cố" if is_mastered else "Duy trì"
        dinh_huong = mt.dinhhuong_kiemduyet or ('Khái quát hóa tại gia đình' if is_mastered else 'Tiếp tục duy trì sang tháng sau')
        ten_mt = mt.name or mt.muctieu_them or ''

        return {
            'stt': stt,
            'muctieu': ten_mt,
            'truoc': f"{mt.solan_thu_dat}/{mt.solan_thu} ({mt.tyle_thu}%)" if mt.solan_thu else "0/10 (0%)",
            'sau': tyle_sau,
            'muc_do': muc_do_label,
            'is_mastered': is_mastered,
            'dinh_huong': dinh_huong,
        }, is_mastered

    def _build_svg_chart_data(self, chart_linhvucs):
        """Tính toán tọa độ pixel (X, Y) cho đồ thị SVG tiến bộ lâm sàng"""
        total_items = len(chart_linhvucs)
        x_start, x_end = 75, 845
        x_step = (x_end - x_start) / max(total_items - 1, 1) if total_items > 1 else 0

        svg_points_thu, svg_points_dat, chart_items = [], [], []
        for i, item in enumerate(chart_linhvucs):
            x = round(x_start + (i * x_step if total_items > 1 else 385))
            y_thu = min(max(round(165 - (item['tyle_thu'] / 100.0 * 130)), 25), 165)
            y_dat = min(max(round(165 - (item['tyle_dat'] / 100.0 * 130)), 25), 165)

            svg_points_thu.append(f"{x},{y_thu}")
            svg_points_dat.append(f"{x},{y_dat}")
            chart_items.append({
                'lines': item['lines'],
                'tyle_thu': item['tyle_thu'],
                'tyle_dat': item['tyle_dat'],
                'x': x,
                'y_thu': y_thu,
                'y_dat': y_dat,
            })

        points_thu_str = " ".join(svg_points_thu)
        points_dat_str = " ".join(svg_points_dat)
        polygon_dat_str = f"{chart_items[0]['x']},165 {points_dat_str} {chart_items[-1]['x']},165" if chart_items else ""

        return {
            "items": chart_items,
            "points_thu": points_thu_str,
            "points_dat": points_dat_str,
            "polygon_dat": polygon_dat_str,
        }

    def _build_hocsinh_profile(self):
        """Chuẩn bị đối tượng thông tin học sinh và đường dẫn chia sẻ an toàn"""
        avatar_field = 'avatar_128'
        has_avatar = False
        if hasattr(self, 'avatar_128') and self.avatar_128:
            has_avatar = True
            avatar_field = 'avatar_128'
        elif hasattr(self, 'image_128') and self.image_128:
            has_avatar = True
            avatar_field = 'image_128'

        co_so_name = self.coso_id.name if hasattr(self, 'coso_id') and self.coso_id else 'CHUYÊN BIỆT TỪ SƠN - TRỤ SỞ CHÍNH'

        raw_status = getattr(self, 'trangthai_hoc', '') or getattr(self, 'trangthai', '') or 'Đang theo học'
        trang_thai_label = 'Đang theo học' if raw_status in ['dang_hoc', '1', 'Đang theo học'] else (raw_status or 'Đang theo học')

        if hasattr(self, 'access_token') and not self.access_token:
            self.access_token = str(uuid.uuid4())

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        token_val = getattr(self, 'access_token', '') or str(self.id)
        share_link = getattr(self, 'share_url', False) or f"{base_url}/hocsinh/hosocanthiep/{token_val}"

        return {
            'id': self.id,
            'name': self.name or '',
            'co_so': co_so_name,
            'trang_thai': trang_thai_label,
            'ngaysinh': self.ngaysinh.strftime('%d/%m/%Y') if hasattr(self, 'ngaysinh') and self.ngaysinh else '',
            'tuoi': getattr(self, 'tuoi', '') or '',
            'phuhuynh': getattr(self, 'ten_cha_me', '') or 'Đại diện Phụ huynh',
            'has_avatar': has_avatar,
            'avatar_field': avatar_field,
            'share_url': share_link,
        }

    def _compute_label_thang_toi(self, kehoach):
        """Tính tên nhãn tháng tiếp theo cho kế hoạch"""
        if kehoach.den_ngay:
            next_date = kehoach.den_ngay + relativedelta(days=1)
            return f"THÁNG {next_date.month}/{next_date.year}"
        if kehoach.tu_ngay:
            next_date = kehoach.tu_ngay + relativedelta(months=1)
            return f"THÁNG {next_date.month}/{next_date.year}"
        return "THÁNG TỚI"

    def _get_request_param(self, param_name, context_key=None, default=False):
        """Đọc an toàn tham số từ HTTP Request hoặc Context"""
        val = False
        try:
            if http.request and hasattr(http.request, 'params'):
                val = http.request.params.get(param_name)
        except Exception:
            pass

        if not val and context_key:
            val = self.env.context.get(context_key)
        return val or default

    def _get_empty_baocao_data(self):
        """Dữ liệu dự phòng khi chưa có kế hoạch nào được chọn"""
        return {
            'ten': 'Chưa có kế hoạch',
            'tieu_de_hien_thi': 'Chưa có kế hoạch',
            'giaovien': '',
            'quanly': '',
            'tong_muctieu': 0,
            'tong_muctieu_dat': 0,
            'tyle_dat': 0,
            'diem_trung': 'Chưa xác định',
            'but_pha': 'Chưa xác định',
            'nhan_xet': '',
            'dinh_huong_thang_toi': '',
            'dinh_huong_cung_co': [],
            'dinh_huong_duy_tri': [],
            'ten_thang_toi': 'THÁNG TỚI',
            'linhvucs_grouped': [],
            'chart': {'items': [], 'points_thu': '', 'points_dat': '', 'polygon_dat': ''}
        }
