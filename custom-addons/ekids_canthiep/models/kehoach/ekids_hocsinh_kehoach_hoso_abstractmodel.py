# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HocSinhKeHoachHoSoAbstractModel(models.AbstractModel):
    _register = False
    _description = 'Abstract Xử lý dữ liệu Hồ sơ can thiệp'

    def action_print_hoso_report(self):
        """Action nút bấm in báo cáo trực tiếp từ Form view"""
        self.ensure_one()
        return self.env.ref('ekids_canthiep.action_report_kehoach_hoso').report_action(self)

    def _get_hoso_report_data(self):
        """Chuẩn bị dữ liệu: Thông tin học sinh và Tab 1 (Báo cáo tháng gần nhất)"""
        self.ensure_one()

        # 1. Lọc kế hoạch đã kết thúc (trangthai == '-1')
        kehoach_da_ketthucs = self.kehoach_ids.filtered(lambda p: getattr(p, 'trangthai', '') == '-1')

        # Sắp xếp theo ngày kết thúc (den_ngay) hoặc tu_ngay giảm dần
        baocaos = kehoach_da_ketthucs.sorted(
            key=lambda p: p.den_ngay or p.tu_ngay or fields.Date.today(),
            reverse=True
        )
        baocao_gannhat = baocaos[0] if baocaos else False

        # Fallback: Nếu chưa có kế hoạch đóng (-1), lấy kỳ có den_ngay mới nhất
        if not baocao_gannhat and self.kehoach_ids:
            all_sorted = self.kehoach_ids.sorted(
                key=lambda p: p.den_ngay or p.tu_ngay or fields.Date.today(),
                reverse=True
            )
            baocao_gannhat = all_sorted[0]

        tab1 = self.func_get_baocao_kehoach(baocao_gannhat)

        return {
            'has_plan': bool(baocao_gannhat),
            'hocsinh': {
                'name': self.name or '',
                'ngaysinh': self.ngaysinh.strftime('%d/%m/%Y') if hasattr(self, 'ngaysinh') and self.ngaysinh else '',
                'tuoi': getattr(self, 'tuoi', '') or '',
                'phuhuynh': getattr(self, 'ten_cha_me', '') or 'Đại diện Phụ huynh',
            },
            'tab1': tab1
        }

    def func_get_baocao_kehoach(self, kehoach):
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
                'linhvucs': [],
                'chart': {'items': [], 'points_thu': '', 'points_dat': '', 'polygon_dat': ''}
            }

        baocao_linhvucs = []
        count_dat = 0
        muctieus = kehoach.kehoach_linhvuc_ids.mapped('kehoach_muctieu_ids')

        for idx, mt in enumerate(muctieus, 1):
            is_mastered = (getattr(mt, 'trangthai_kiemduyet', '') == '1') or \
                          (getattr(mt, 'trangthai', '') == '1') or \
                          (getattr(mt, 'so_ngay_dat_lientiep', 0) >= 6)

            if is_mastered:
                count_dat += 1

            tyle_sau = getattr(mt, 'tyle_kiemduyet', 0) or getattr(mt, 'tyle_trungbinh_canthiep', 0) or getattr(mt, 'tyle_thu', 0)

            baocao_linhvucs.append({
                'stt': idx,
                'linhvuc': mt.linhvuc_id.name if getattr(mt, 'linhvuc_id', False) else '',
                'tuoi': mt.tuoi_id.name if getattr(mt, 'tuoi_id', False) else '',
                'muctieu': mt.name or '',
                'truoc': f"{mt.solan_thu_dat}/{mt.solan_thu} ({mt.tyle_thu}%)" if getattr(mt, 'solan_thu', 0) else "0/10 (0%)",
                'sau': tyle_sau,
                'mucdo': is_mastered,
                'dinh_huong': getattr(mt, 'dinhhuong_kiemduyet', False) or (
                    'Khái quát hóa tại gia đình' if is_mastered else 'Tiếp tục duy trì sang tháng sau')
            })

        total_targets = len(muctieus)
        tong_dat = getattr(kehoach, 'tong_dat_kiemduyet', 0) or count_dat
        rate_t1 = round((tong_dat / total_targets * 100)) if total_targets else getattr(kehoach, 'tyle_dat_canthiep', 0)

        # 🌟 GOM NHÓM DỮ LIỆU ĐỒ THỊ TRỰC TIẾP TỪ MUCTIEUS (HOÀN TOÀN TRÁNH TRUY VẤN KEHOACH_LINHVUC)
        groups = {}
        for m in muctieus:
            lv_id = m.linhvuc_id.id if m.linhvuc_id else 0
            lv_name = m.linhvuc_id.name if m.linhvuc_id else 'Khác'
            if lv_id not in groups:
                groups[lv_id] = {
                    'name': lv_name,
                    'list_thu': [],
                    'list_dat': []
                }
            t_thu = getattr(m, 'tyle_thu', 0) or 0
            t_dat = getattr(m, 'tyle_kiemduyet', 0) or getattr(m, 'tyle_trungbinh_canthiep', 0) or t_thu
            groups[lv_id]['list_thu'].append(t_thu)
            groups[lv_id]['list_dat'].append(t_dat)

        chart_linhvucs = []
        for g in groups.values():
            avg_thu = round(sum(g['list_thu']) / len(g['list_thu'])) if g['list_thu'] else 0
            avg_dat = round(sum(g['list_dat']) / len(g['list_dat'])) if g['list_dat'] else 0
            r_name = g['name']
            s_name = r_name if len(r_name) <= 12 else r_name[:10] + '..'
            chart_linhvucs.append({
                'name': r_name,
                'short_name': s_name,
                'tyle_thu': avg_thu,
                'tyle_dat': avg_dat,
            })

        # Tính tọa độ X, Y cho biểu đồ đường SVG (viewBox: 0 0 900 215)
        svg_points_thu = []
        svg_points_dat = []
        chart_items = []
        total_items = len(chart_linhvucs)
        x_start = 75
        x_end = 845
        x_step = (x_end - x_start) / max(total_items - 1, 1) if total_items > 1 else 0

        for i, item in enumerate(chart_linhvucs):
            x = round(x_start + (i * x_step if total_items > 1 else 385))
            y_thu = round(170 - (item['tyle_thu'] / 100.0 * 132))
            y_dat = round(170 - (item['tyle_dat'] / 100.0 * 132))

            y_thu = min(max(y_thu, 25), 170)
            y_dat = min(max(y_dat, 25), 170)

            svg_points_thu.append(f"{x},{y_thu}")
            svg_points_dat.append(f"{x},{y_dat}")
            chart_items.append({
                'short_name': item['short_name'],
                'full_name': item['name'],
                'tyle_thu': item['tyle_thu'],
                'tyle_dat': item['tyle_dat'],
                'x': x,
                'y_thu': y_thu,
                'y_dat': y_dat,
            })

        points_thu_str = " ".join(svg_points_thu)
        points_dat_str = " ".join(svg_points_dat)
        polygon_dat_str = ""
        if chart_items:
            polygon_dat_str = f"{chart_items[0]['x']},170 " + points_dat_str + f" {chart_items[-1]['x']},170"

        # Tìm lĩnh vực Bứt phá và Điểm trũng
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
            "nhan_xet": kehoach.desc or (
                "Trong tháng, trẻ có nhiều tiến bộ rõ rệt ở các phản ứng nghe gọi, ngồi bàn tập trung và giao tiếp mắt. "
                "Cần tiếp tục phối hợp với phụ huynh đẩy mạnh tính khái quát tại gia đình."
            ),
            "linhvucs": baocao_linhvucs,
            "chart": {
                "items": chart_items,
                "points_thu": points_thu_str,
                "points_dat": points_dat_str,
                "polygon_dat": polygon_dat_str,
            }
        }