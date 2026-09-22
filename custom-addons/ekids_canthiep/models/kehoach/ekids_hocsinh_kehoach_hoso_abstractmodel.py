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
    # MAIN DATA BUILDER
    # =========================================================================
    def _get_hoso_report_data(self):
        """Chuẩn bị dữ liệu cho Tab 1 (Báo cáo kết quả) & Tab 2 (Kế hoạch đang can thiệp)"""
        self.ensure_one()
        KeHoachModel = self.env['ekids.kehoach']

        # 1. TAB 1: Kế hoạch đã kết thúc (trangthai == '-1')
        ds_baocao, baocao_duoc_chon = self._resolve_tab1_plan(KeHoachModel)
        tab1_data = self.func_get_baocao_kehoach(baocao_duoc_chon)

        # 2. TAB 2: Kế hoạch đang can thiệp
        ds_thangtoi, kh_thangtoi_duoc_chon = self._resolve_tab2_plan(KeHoachModel)
        tab2_data = self.func_get_kehoach_tomtat_thangtoi(kh_thangtoi_duoc_chon, baocao_duoc_chon)

        # 3. Phối hợp Context/HTTP Params cho active tab
        active_tab = self._get_request_param('active_tab', default='tab1')

        # 4. Profile & Token chia sẻ
        profile_data = self._build_hocsinh_profile()

        return {
            'has_plan': bool(baocao_duoc_chon),
            'has_plan_thangtoi': bool(kh_thangtoi_duoc_chon),
            'current_plan_id': baocao_duoc_chon.id if baocao_duoc_chon else 0,
            'current_thangtoi_id': kh_thangtoi_duoc_chon.id if kh_thangtoi_duoc_chon else 0,
            'active_tab': active_tab,
            'hocsinh': profile_data,
            'tab1': tab1_data,
            'tab2': tab2_data,
            'ds_baocao': ds_baocao,
            'ds_kehoach_thangtoi': ds_thangtoi,
        }

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
            lv_name = lv_line.linhvuc_id.name if lv_line.linhvuc_id else 'Khác'
            tuoi_name = lv_line.tuoi_id.name if lv_line.tuoi_id else ''
            mts = lv_line.kehoach_muctieu_ids.sorted(key=lambda m: (m.sequence, m.id))

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

            avg_thu = lv_line.tyle_thu
            avg_dat = lv_line.tyle_dat
            linhvucs_grouped.append({
                'linhvuc': lv_name,
                'tuoi': tuoi_name,
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

        # Biểu đồ SVG
        chart_data = self._build_svg_chart_data(chart_linhvucs)

        # Chỉ số bứt phá / Điểm trũng (Sắp xếp bản sao tạm, không đổi thứ tự bảng)
        sorted_temp = sorted(chart_linhvucs, key=lambda x: x['tyle_dat'], reverse=True)
        but_pha = f"{sorted_temp[0]['name']} ({sorted_temp[0]['tyle_dat']}%)" if sorted_temp else "Chưa có"
        diem_trung = f"{sorted_temp[-1]['name']} ({sorted_temp[-1]['tyle_dat']}%)" if sorted_temp else "Chưa có"

        tong_dat = getattr(kehoach, 'tong_dat_kiemduyet', 0) or count_dat
        rate_t1 = round((tong_dat / total_targets * 100)) if total_targets else getattr(kehoach, 'tyle_dat_canthiep', 0)

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

    # =========================================================================
    # TAB 2 LOGIC: KẾ HOẠCH ĐANG CAN THIỆP (THÁNG TỚI)
    # =========================================================================
    def func_get_kehoach_tomtat_thangtoi(self, kehoach, kehoach_truoc=False):
        """Tổng hợp danh mục mục tiêu cho kế hoạch đang can thiệp"""
        if not kehoach:
            return {
                'ten': 'Chưa có kế hoạch',
                'tieu_de_hien_thi': 'Chưa có kế hoạch',
                'giaovien': 'Chưa phân công',
                'quanly': 'Ngô Thị Ngọc Hoàn',
                'tong_muctieu': 0,
                'trangthai_text': 'Chưa lập',
                'linhvucs_grouped': []
            }

        prev_mt_names = set()
        if kehoach_truoc:
            prev_mts = kehoach_truoc.kehoach_linhvuc_ids.mapped('kehoach_muctieu_ids')
            prev_mt_names = {m.name.strip().lower() for m in prev_mts if m.name}

        linhvuc_lines = kehoach.kehoach_linhvuc_ids.sorted(key=lambda r: r.sequence)
        linhvucs_grouped = []
        total_targets_count = 0
        global_idx = 1

        for lv_line in linhvuc_lines:
            lv_name = lv_line.linhvuc_id.name if lv_line.linhvuc_id else 'Khác'
            tuoi_name = lv_line.tuoi_id.name if lv_line.tuoi_id else ''
            chuongtrinh = lv_line.tuoi_id.chuongtrinh_id.name if lv_line.tuoi_id and lv_line.tuoi_id.chuongtrinh_id else ''
            mts = lv_line.kehoach_muctieu_ids.sorted(key=lambda m: (m.sequence, m.id))

            targets = []
            for mt in mts:
                total_targets_count += 1
                targets.append(self._format_tab2_target(mt, global_idx, prev_mt_names))
                global_idx += 1

            linhvucs_grouped.append({
                'linhvuc': lv_name,
                'tuoi': tuoi_name,
                'chuongtrinh': chuongtrinh,
                'avg_thu': lv_line.tyle_thu,
                'total_mt': len(targets),
                'targets': targets
            })

        gv_name = kehoach.gv_lapkehoach_id.name if kehoach.gv_lapkehoach_id else 'Chưa phân công'
        return {
            'ten': kehoach.name or 'Kế hoạch tháng tới',
            'giaovien': gv_name,
            'tieu_de_hien_thi': f"{kehoach.name or 'Kế hoạch tháng tới'} (Giáo viên: {gv_name})",
            'quanly': kehoach.gv_kiemduyet_id.name if kehoach.gv_kiemduyet_id else 'Ngô Thị Ngọc Hoàn',
            'tong_muctieu': total_targets_count,
            'trangthai_text': 'Đang can thiệp',
            'linhvucs_grouped': linhvucs_grouped
        }

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================
    def _resolve_tab1_plan(self, KeHoachModel):
        """Xác định danh sách dropdown và bản ghi được chọn cho Tab 1
        Chỉ lấy và cho phép chọn các kế hoạch đã kết thúc (trangthai == '-1')
        """
        kh_data = KeHoachModel.search_read(
            domain=[('hocsinh_id', '=', self.id), ('trangthai', '=', '-1')],
            fields=['id', 'name', 'gv_lapkehoach_id', 'tyle_dat_canthiep'],
            order='den_ngay desc, tu_ngay desc'
        )

        ds_baocao = []
        valid_plan_ids = set()
        for kh in kh_data:
            valid_plan_ids.add(kh['id'])
            gv_name = kh['gv_lapkehoach_id'][1] if kh.get('gv_lapkehoach_id') else 'Chưa phân công'
            ten_kh = kh['name'] or 'Kế hoạch'
            ds_baocao.append({
                'id': kh['id'],
                'ten': ten_kh,
                'gv_name': gv_name,
                'label': f"{ten_kh} (Giáo viên: {gv_name})",
                'tyle_dat': kh.get('tyle_dat_canthiep') or 0,
            })

        param_id = self._get_request_param('kehoach_id', context_key='kehoach_id')
        selected_record = False

        if param_id:
            try:
                plan_id_int = int(param_id)
                # Chỉ chấp nhận nếu kế hoạch này thực sự nằm trong danh sách đã đóng ('-1')
                if plan_id_int in valid_plan_ids:
                    selected_record = KeHoachModel.browse(plan_id_int)
            except (ValueError, TypeError):
                pass

        if not selected_record and kh_data:
            selected_record = KeHoachModel.browse(kh_data[0]['id'])

        return ds_baocao, selected_record

    def _resolve_tab2_plan(self, KeHoachModel):
        """Xác định danh sách dropdown và bản ghi được chọn cho Tab 2"""
        status_val = getattr(kehoach_util, 'KEHOACH_DANG_CANTHIEP', '1')
        kehoach_ids = KeHoachModel.search(
            [('hocsinh_id', '=', self.id), ('trangthai', '=', str(status_val))],
            order='tu_ngay desc, den_ngay desc'
        )

        ds_thangtoi = []
        for p in kehoach_ids:
            gv_name = p.gv_lapkehoach_id.name if p.gv_lapkehoach_id else 'Chưa phân công'
            ten_kh = p.name or 'Kế hoạch can thiệp'
            ds_thangtoi.append({
                'id': p.id,
                'ten': ten_kh,
                'gv_name': gv_name,
                'label': f"{ten_kh} (Giáo viên: {gv_name})"
            })

        param_id = self._get_request_param('thangtoi_id', context_key='thangtoi_id')
        selected_record = False
        if param_id:
            selected_record = KeHoachModel.browse(int(param_id)).exists()
        if not selected_record and kehoach_ids:
            selected_record = kehoach_ids[0]

        return ds_thangtoi, selected_record

    def _format_tab1_target(self, mt, stt):
        """Định dạng dữ liệu 1 mục tiêu của báo cáo Tab 1"""
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

    def _format_tab2_target(self, mt, stt, prev_mt_names):
        """Định dạng dữ liệu 1 mục tiêu của kế hoạch tháng tới Tab 2"""
        t_thu = getattr(mt, 'tyle_thu', 0) or 0
        ten_mt = mt.name or getattr(mt, 'muctieu_them', '') or ''

        # Chuẩn hóa kiểm tra: Many2one rỗng trong Odoo là False/None
        is_chuyen_tiep = bool(getattr(mt, 'kehoach_muctieu_thangtruoc_id', False))



        return {
            'stt': stt,
            'muctieu': ten_mt,
            'truoc_pct': f"{t_thu}%",
            'solan_thu': f"{getattr(mt, 'solan_thu_dat', 0)}/{getattr(mt, 'solan_thu', 10)}",
            'loai_muctieu': "Tháng trước chuyển qua" if is_chuyen_tiep else "Mới",
            'is_chuyen_tiep': is_chuyen_tiep,
            'ghichu': getattr(mt, 'dinhhuong_kiemduyet', False) or getattr(mt, 'ghichu', False) or 'Thực hiện can thiệp theo quy trình chuẩn',
        }

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