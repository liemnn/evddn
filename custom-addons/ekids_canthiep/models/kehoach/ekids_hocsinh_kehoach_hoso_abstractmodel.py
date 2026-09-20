# -*- coding: utf-8 -*-
from odoo import models, fields, api, http
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import logging
import textwrap

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
    from odoo.addons.ekids_func import giaovien_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func: {e}")


class HocSinhKeHoachHoSoAbstractModel(models.AbstractModel):
    _register = False
    _description = 'Abstract Xử lý dữ liệu Hồ sơ can thiệp'

    def action_print_hoso_report(self):
        """Action nút bấm in báo cáo trực tiếp từ Form view"""
        self.ensure_one()
        return self.env.ref('ekids_canthiep.action_report_kehoach_hoso').report_action(self)

    def _get_hoso_report_data(self):
        """Chuẩn bị dữ liệu: Nhận diện kỳ báo cáo chọn từ URL hoặc mặc định kỳ mới nhất"""
        self.ensure_one()

        # 1. Lọc tất cả kế hoạch đã kết thúc (trangthai == '-1')
        kehoach_da_ketthucs = self.kehoach_ids.filtered(lambda p: getattr(p, 'trangthai', '') == '-1')

        # Sắp xếp theo ngày giảm dần
        baocaos = kehoach_da_ketthucs.sorted(
            key=lambda p: p.den_ngay or p.tu_ngay or fields.Date.today(),
            reverse=True
        )

        target_list = baocaos if baocaos else self.kehoach_ids.sorted(
            key=lambda p: p.den_ngay or p.tu_ngay or fields.Date.today(),
            reverse=True
        )

        baocao_duoc_chon = target_list[0] if target_list else False

        # Nhận diện tham số kehoach_id từ URL query string hoặc context
        selected_kh_id = False
        try:
            if http.request and hasattr(http.request, 'params'):
                selected_kh_id = http.request.params.get('kehoach_id')
        except Exception:
            pass

        if not selected_kh_id:
            selected_kh_id = self.env.context.get('kehoach_id')

        if selected_kh_id:
            found_kh = self.kehoach_ids.filtered(lambda k: k.id == int(selected_kh_id))
            if found_kh:
                baocao_duoc_chon = found_kh[0]

        # Trích xuất dữ liệu chi tiết của kỳ được chỉ định
        tab1 = self.func_get_baocao_kehoach(baocao_duoc_chon)

        # 2. Danh sách nhẹ các kỳ để nạp vào Dropdown chọn nhanh
        ds_baocao = []
        for kh in target_list:
            ds_baocao.append({
                'id': kh.id,
                'ten': kh.name or 'Kế hoạch',
                'tu_ngay': kh.tu_ngay.strftime('%d/%m/%Y') if kh.tu_ngay else '',
                'den_ngay': kh.den_ngay.strftime('%d/%m/%Y') if kh.den_ngay else '',
                'tyle_dat': getattr(kh, 'tyle_dat_canthiep', 0),
            })

        return {
            'has_plan': bool(baocao_duoc_chon),
            'current_plan_id': baocao_duoc_chon.id if baocao_duoc_chon else 0,
            'hocsinh': {
                'name': self.name or '',
                'ngaysinh': self.ngaysinh.strftime('%d/%m/%Y') if hasattr(self, 'ngaysinh') and self.ngaysinh else '',
                'tuoi': getattr(self, 'tuoi', '') or '',
                'phuhuynh': getattr(self, 'ten_cha_me', '') or 'Đại diện Phụ huynh',
            },
            'tab1': tab1,
            'ds_baocao': ds_baocao
        }

    def func_get_baocao_kehoach(self, kehoach):
        """Hàm trích xuất dữ liệu chi tiết, phân nhóm và vẽ SVG cho 1 kế hoạch"""
        if not kehoach:
            return {
                'ten': 'Chưa có kế hoạch',
                'thoigian': '',
                'giaovien': '',
                'quanly': '',
                'tong_muctieu': 0,
                'tong_muctieu_dat': 0,
                'tyle_dat': 0,
                'diem_trung': 'Chưa xác định',
                'but_pha': 'Chưa xác định',
                'nhan_xet': '',
                'linhvucs_grouped': [],
                'chart': {'items': [], 'points_thu': '', 'points_dat': '', 'polygon_dat': ''}
            }

        muctieus = kehoach.kehoach_linhvuc_ids.mapped('kehoach_muctieu_ids')
        count_dat = 0

        # Gom nhóm mục tiêu theo từng Lĩnh vực + Độ tuổi
        groups = {}
        for idx, mt in enumerate(muctieus, 1):
            is_mastered = (getattr(mt, 'trangthai_kiemduyet', '') == '1') or \
                          (getattr(mt, 'trangthai', '') == '1') or \
                          (getattr(mt, 'so_ngay_dat_lientiep', 0) >= 6)

            if is_mastered:
                count_dat += 1

            tyle_sau = getattr(mt, 'tyle_kiemduyet', 0) or getattr(mt, 'tyle_trungbinh_canthiep', 0) or getattr(mt, 'tyle_thu', 0)

            # Phân loại mức độ: >= 80% là Củng cố, < 80% là Duy trì
            muc_do_label = "Củng cố" if tyle_sau >= 80 else "Duy trì"

            # Lấy ý kiến định hướng trực tiếp từ trường dinhhuong_kiemduyet
            dinh_huong_text = getattr(mt, 'dinhhuong_kiemduyet', False) or ''
            if not dinh_huong_text:
                dinh_huong_text = 'Khái quát hóa tại gia đình' if is_mastered else 'Tiếp tục duy trì sang tháng sau'

            lv_key = (mt.linhvuc_id.id if mt.linhvuc_id else 0, mt.tuoi_id.id if mt.tuoi_id else 0)
            if lv_key not in groups:
                groups[lv_key] = {
                    'linhvuc': mt.linhvuc_id.name if mt.linhvuc_id else 'Khác',
                    'tuoi': mt.tuoi_id.name if mt.tuoi_id else '',
                    'targets': [],
                    'list_thu': [],
                    'list_dat': []
                }

            t_thu = getattr(mt, 'tyle_thu', 0) or 0
            groups[lv_key]['list_thu'].append(t_thu)
            groups[lv_key]['list_dat'].append(tyle_sau)

            groups[lv_key]['targets'].append({
                'stt': idx,
                'muctieu': mt.name or '',
                'truoc': f"{mt.solan_thu_dat}/{mt.solan_thu} ({mt.tyle_thu}%)" if getattr(mt, 'solan_thu', 0) else "0/10 (0%)",
                'sau': tyle_sau,
                'muc_do': muc_do_label,
                'is_mastered': is_mastered,
                'dinh_huong': dinh_huong_text
            })

        # Xây dựng danh sách nhóm hiển thị bảng & Dữ liệu biểu đồ SVG
        linhvucs_grouped = []
        chart_linhvucs = []

        for g in groups.values():
            avg_thu = round(sum(g['list_thu']) / len(g['list_thu'])) if g['list_thu'] else 0
            avg_dat = round(sum(g['list_dat']) / len(g['list_dat'])) if g['list_dat'] else 0

            linhvucs_grouped.append({
                'linhvuc': g['linhvuc'],
                'tuoi': g['tuoi'],
                'avg_thu': avg_thu,
                'avg_dat': avg_dat,
                'total_mt': len(g['targets']),
                'targets': g['targets']
            })

            # Tự động ngắt dòng cho tên lĩnh vực (8-10 ký tự/dòng, không cắt ba chấm '...')
            wrapped_lines = textwrap.wrap(g['linhvuc'], width=9) if g['linhvuc'] else ['Khác']
            chart_linhvucs.append({
                'name': g['linhvuc'],
                'lines': wrapped_lines,
                'tyle_thu': avg_thu,
                'tyle_dat': avg_dat,
            })

        total_targets = len(muctieus)
        tong_dat = getattr(kehoach, 'tong_dat_kiemduyet', 0) or count_dat
        rate_t1 = round((tong_dat / total_targets * 100)) if total_targets else getattr(kehoach, 'tyle_dat_canthiep', 0)

        # Tính tọa độ biểu đồ đường SVG (viewBox: 0 0 900 250)
        svg_points_thu, svg_points_dat, chart_items = [], [], []
        total_items = len(chart_linhvucs)
        x_start, x_end = 75, 845
        x_step = (x_end - x_start) / max(total_items - 1, 1) if total_items > 1 else 0

        for i, item in enumerate(chart_linhvucs):
            x = round(x_start + (i * x_step if total_items > 1 else 385))
            y_thu = round(165 - (item['tyle_thu'] / 100.0 * 130))
            y_dat = round(165 - (item['tyle_dat'] / 100.0 * 130))
            y_thu = min(max(y_thu, 25), 165)
            y_dat = min(max(y_dat, 25), 165)

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
        polygon_dat_str = f"{chart_items[0]['x']},165 " + points_dat_str + f" {chart_items[-1]['x']},165" if chart_items else ""

        sorted_linhvucs = sorted(chart_linhvucs, key=lambda x: x['tyle_dat'], reverse=True)
        but_pha_str = f"{sorted_linhvucs[0]['name']} ({sorted_linhvucs[0]['tyle_dat']}%)" if sorted_linhvucs else "Chưa có"
        diem_trung_str = f"{sorted_linhvucs[-1]['name']} ({sorted_linhvucs[-1]['tyle_dat']}%)" if sorted_linhvucs else "Chưa có"

        thoigian_str = ""
        if kehoach.tu_ngay and kehoach.den_ngay:
            thoigian_str = f"Từ ngày {kehoach.tu_ngay.strftime('%d/%m/%Y')} đến ngày {kehoach.den_ngay.strftime('%d/%m/%Y')}"

        return {
            "ten": kehoach.name or '',
            "thoigian": thoigian_str,
            "giaovien": kehoach.gv_lapkehoach_id.name if kehoach.gv_lapkehoach_id else '',
            "quanly": kehoach.gv_kiemduyet_id.name if kehoach.gv_kiemduyet_id else 'Ngô Thị Ngọc Hoàn',
            "tong_muctieu": kehoach.tong_muctieu or total_targets,
            "tong_muctieu_dat": tong_dat,
            "tyle_dat": rate_t1,
            "diem_trung": diem_trung_str,
            "but_pha": but_pha_str,
            "nhan_xet": kehoach.desc or "Trong tháng, trẻ có nhiều tiến bộ rõ rệt ở các phản ứng nghe gọi, ngồi bàn tập trung và giao tiếp mắt.",
            "linhvucs_grouped": linhvucs_grouped,
            "chart": {
                "items": chart_items,
                "points_thu": points_thu_str,
                "points_dat": points_dat_str,
                "polygon_dat": polygon_dat_str,
            }
        }