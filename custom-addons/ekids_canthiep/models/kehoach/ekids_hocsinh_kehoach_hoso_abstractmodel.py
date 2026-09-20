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
        self.ensure_one()
        return self.env.ref('ekids_canthiep.action_report_kehoach_hoso').report_action(self)

    def _get_hoso_report_data(self):
        self.ensure_one()
        KeHoachModel = self.env['ekids.kehoach']

        # 1. TAB 1: Danh sach bao cao da dong (-1)
        kh_da_dong_data = KeHoachModel.search_read(
            domain=[('hocsinh_id', '=', self.id), ('trangthai', '=', '-1')],
            fields=['id', 'name', 'gv_lapkehoach_id', 'tyle_dat_canthiep'],
            order='den_ngay desc, tu_ngay desc'
        )

        if not kh_da_dong_data:
            kh_da_dong_data = KeHoachModel.search_read(
                domain=[('hocsinh_id', '=', self.id)],
                fields=['id', 'name', 'gv_lapkehoach_id', 'tyle_dat_canthiep'],
                order='den_ngay desc, tu_ngay desc'
            )

        ds_baocao = []
        for kh in kh_da_dong_data:
            gv_name = kh['gv_lapkehoach_id'][1] if kh.get('gv_lapkehoach_id') else 'Chưa phân công'
            ten_kh = kh['name'] or 'Kế hoạch'
            ds_baocao.append({
                'id': kh['id'],
                'ten': ten_kh,
                'gv_name': gv_name,
                'label': f"{ten_kh} (Giáo viên: {gv_name})",
                'tyle_dat': kh.get('tyle_dat_canthiep') or 0,
            })

        selected_kh_id = False
        try:
            if http.request and hasattr(http.request, 'params'):
                selected_kh_id = http.request.params.get('kehoach_id')
        except Exception:
            pass

        if not selected_kh_id:
            selected_kh_id = self.env.context.get('kehoach_id')

        baocao_duoc_chon = False
        if selected_kh_id:
            baocao_duoc_chon = KeHoachModel.browse(int(selected_kh_id)).exists()

        if not baocao_duoc_chon and kh_da_dong_data:
            baocao_duoc_chon = KeHoachModel.browse(kh_da_dong_data[0]['id'])

        tab1 = self.func_get_baocao_kehoach(baocao_duoc_chon)

        # 2. TAB 2: Danh sach ke hoach dang can thiep (trangthai == '1')
        domain_thangtoi = [
            ('hocsinh_id', '=', self.id),
            ('trangthai', '=', '1')
        ]
        kehoach_dang_canthiep_ids = KeHoachModel.search(domain_thangtoi, order='tu_ngay desc, den_ngay desc')

        if not kehoach_dang_canthiep_ids and hasattr(kehoach_util, 'KEHOACH_DANG_CANTHIEP'):
            val_ct = getattr(kehoach_util, 'KEHOACH_DANG_CANTHIEP')
            kehoach_dang_canthiep_ids = KeHoachModel.search([
                ('hocsinh_id', '=', self.id),
                ('trangthai', '=', str(val_ct))
            ], order='tu_ngay desc, den_ngay desc')

        ds_kehoach_thangtoi = []
        for p in kehoach_dang_canthiep_ids:
            gv_p = p.gv_lapkehoach_id.name if p.gv_lapkehoach_id else 'Chưa phân công'
            ten_p = p.name or 'Kế hoạch can thiệp'
            ds_kehoach_thangtoi.append({
                'id': p.id,
                'ten': ten_p,
                'gv_name': gv_p,
                'label': f"{ten_p} (Giáo viên: {gv_p})"
            })

        selected_thangtoi_id = False
        try:
            if http.request and hasattr(http.request, 'params'):
                selected_thangtoi_id = http.request.params.get('thangtoi_id')
        except Exception:
            pass

        kh_thangtoi_duoc_chon = False
        if selected_thangtoi_id:
            kh_thangtoi_duoc_chon = KeHoachModel.browse(int(selected_thangtoi_id)).exists()

        if not kh_thangtoi_duoc_chon and kehoach_dang_canthiep_ids:
            kh_thangtoi_duoc_chon = kehoach_dang_canthiep_ids[0]

        tab2 = self.func_get_kehoach_tomtat_thangtoi(kh_thangtoi_duoc_chon, baocao_duoc_chon)

        active_tab = 'tab1'
        try:
            if http.request and hasattr(http.request, 'params'):
                active_tab = http.request.params.get('active_tab', 'tab1')
        except Exception:
            pass

        # Safe avatar / image detection in Python
        has_avatar = False
        avatar_field = 'avatar_128'
        if hasattr(self, 'avatar_128') and self.avatar_128:
            has_avatar = True
            avatar_field = 'avatar_128'
        elif hasattr(self, 'image_128') and self.image_128:
            has_avatar = True
            avatar_field = 'image_128'

        co_so_name = self.co_so_id.name if hasattr(self,
                                                   'co_so_id') and self.co_so_id else 'CHUYÊN BIỆT TỪ SƠN - TRỤ SỞ CHÍNH'
        trang_thai_hoc = getattr(self, 'trangthai_hoc', '') or getattr(self, 'trangthai', '') or 'Đang theo học'
        if trang_thai_hoc == 'dang_hoc' or trang_thai_hoc == '1':
            trang_thai_label = 'Đang theo học'
        elif isinstance(trang_thai_hoc, str) and trang_thai_hoc in ['Đang theo học', 'dang_hoc']:
            trang_thai_label = 'Đang theo học'
        else:
            trang_thai_label = trang_thai_hoc or 'Đang theo học'

        return {
            'has_plan': bool(baocao_duoc_chon),
            'has_plan_thangtoi': bool(kh_thangtoi_duoc_chon),
            'current_plan_id': baocao_duoc_chon.id if baocao_duoc_chon else 0,
            'current_thangtoi_id': kh_thangtoi_duoc_chon.id if kh_thangtoi_duoc_chon else 0,
            'active_tab': active_tab,
            'hocsinh': {
                'id': self.id,
                'name': self.name or '',
                'co_so': co_so_name,
                'trang_thai': trang_thai_label,
                'ngaysinh': self.ngaysinh.strftime('%d/%m/%Y') if hasattr(self, 'ngaysinh') and self.ngaysinh else '',
                'tuoi': getattr(self, 'tuoi', '') or '',
                'phuhuynh': getattr(self, 'ten_cha_me', '') or 'Đại diện Phụ huynh',
                'has_avatar': has_avatar,
                'avatar_field': avatar_field,
            },
            'tab1': tab1,
            'tab2': tab2,
            'ds_baocao': ds_baocao,
            'ds_kehoach_thangtoi': ds_kehoach_thangtoi
        }

    def func_get_baocao_kehoach(self, kehoach):
        if not kehoach:
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
                'linhvucs_grouped': [],
                'chart': {'items': [], 'points_thu': '', 'points_dat': '', 'polygon_dat': ''}
            }

        muctieus = self.env['ekids.kehoach_muctieu'].search([('kehoach_id', '=', kehoach.id)])
        if not muctieus:
            muctieus = kehoach.kehoach_linhvuc_ids.mapped('kehoach_muctieu_ids')

        count_dat = 0
        groups = {}

        for idx, mt in enumerate(muctieus, 1):
            is_mastered = (getattr(mt, 'trangthai_kiemduyet', '') == '1') or \
                          (getattr(mt, 'trangthai', '') == '1') or \
                          (getattr(mt, 'so_ngay_dat_lientiep', 0) >= 6)

            if is_mastered:
                count_dat += 1

            tyle_sau = getattr(mt, 'tyle_kiemduyet', 0) or getattr(mt, 'tyle_trungbinh_canthiep', 0) or getattr(mt,
                                                                                                                'tyle_thu',
                                                                                                                0)
            muc_do_label = "Củng cố" if tyle_sau >= 80 else "Duy trì"

            dinh_huong_text = getattr(mt, 'dinhhuong_kiemduyet', False) or ''
            if not dinh_huong_text:
                dinh_huong_text = 'Khái quát hóa tại gia đình' if is_mastered else 'Tiếp tục duy trì sang tháng sau'

            lv_name = mt.linhvuc_id.name if mt.linhvuc_id else 'Khác'
            tuoi_name = mt.tuoi_id.name if mt.tuoi_id else ''
            lv_key = (lv_name, tuoi_name)

            if lv_key not in groups:
                groups[lv_key] = {
                    'linhvuc': lv_name,
                    'tuoi': tuoi_name,
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
                'truoc': f"{mt.solan_thu_dat}/{mt.solan_thu} ({mt.tyle_thu}%)" if getattr(mt, 'solan_thu',
                                                                                          0) else "0/10 (0%)",
                'sau': tyle_sau,
                'muc_do': muc_do_label,
                'is_mastered': is_mastered,
                'dinh_huong': dinh_huong_text
            })

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

        ten_kh = kehoach.name or 'Kế hoạch'
        gv_name = kehoach.gv_lapkehoach_id.name if kehoach.gv_lapkehoach_id else 'Chưa phân công'

        return {
            "ten": ten_kh,
            "giaovien": gv_name,
            "tieu_de_hien_thi": f"{ten_kh} (Giáo viên: {gv_name})",
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

    def func_get_kehoach_tomtat_thangtoi(self, kehoach, kehoach_truoc=False):
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

        muctieus = self.env['ekids.kehoach_muctieu'].search([('kehoach_id', '=', kehoach.id)])
        if not muctieus:
            muctieus = kehoach.kehoach_linhvuc_ids.mapped('kehoach_muctieu_ids')

        prev_mt_names = set()
        if kehoach_truoc:
            prev_mts = self.env['ekids.kehoach_muctieu'].search([('kehoach_id', '=', kehoach_truoc.id)])
            if not prev_mts:
                prev_mts = kehoach_truoc.kehoach_linhvuc_ids.mapped('kehoach_muctieu_ids')
            prev_mt_names = {m.name.strip().lower() for m in prev_mts if m.name}

        groups = {}

        for idx, mt in enumerate(muctieus, 1):
            lv_name = mt.linhvuc_id.name if mt.linhvuc_id else 'Khác'
            tuoi_name = mt.tuoi_id.name if mt.tuoi_id else ''
            lv_key = (lv_name, tuoi_name)

            if lv_key not in groups:
                groups[lv_key] = {
                    'linhvuc': lv_name,
                    'tuoi': tuoi_name,
                    'targets': [],
                    'list_thu': []
                }

            t_thu = getattr(mt, 'tyle_thu', 0) or 0
            groups[lv_key]['list_thu'].append(t_thu)

            ten_mt = mt.name or getattr(mt, 'muctieu_them', '') or ''

            is_chuyen_tiep = False
            if hasattr(mt, 'is_chuyen_tiep') and mt.is_chuyen_tiep:
                is_chuyen_tiep = True
            elif hasattr(mt, 'loai_muctieu') and mt.loai_muctieu in ['chuyen_tiep', 'duy_tri']:
                is_chuyen_tiep = True
            elif ten_mt.strip().lower() in prev_mt_names:
                is_chuyen_tiep = True

            loai_label = "Tháng trước chuyển qua" if is_chuyen_tiep else "Mới"
            ghichu_text = getattr(mt, 'dinhhuong_kiemduyet', False) or getattr(mt, 'ghichu',
                                                                               False) or 'Thực hiện can thiệp theo quy trình chuẩn'

            groups[lv_key]['targets'].append({
                'stt': idx,
                'muctieu': ten_mt,
                'truoc_pct': f"{t_thu}%",
                'solan_thu': f"{getattr(mt, 'solan_thu_dat', 0)}/{getattr(mt, 'solan_thu', 10)}",
                'loai_muctieu': loai_label,
                'is_chuyen_tiep': is_chuyen_tiep,
                'ghichu': ghichu_text
            })

        linhvucs_grouped = []
        for g in groups.values():
            avg_thu = round(sum(g['list_thu']) / len(g['list_thu'])) if g['list_thu'] else 0
            linhvucs_grouped.append({
                'linhvuc': g['linhvuc'],
                'tuoi': g['tuoi'],
                'avg_thu': avg_thu,
                'total_mt': len(g['targets']),
                'targets': g['targets']
            })

        ten_kh = kehoach.name or 'Kế hoạch tháng tới'
        gv_name = kehoach.gv_lapkehoach_id.name if kehoach.gv_lapkehoach_id else 'Chưa phân công'

        return {
            'ten': ten_kh,
            'giaovien': gv_name,
            'tieu_de_hien_thi': f"{ten_kh} (Giáo viên: {gv_name})",
            'quanly': kehoach.gv_kiemduyet_id.name if kehoach.gv_kiemduyet_id else 'Ngô Thị Ngọc Hoàn',
            'tong_muctieu': len(muctieus),
            'trangthai_text': 'Đang can thiệp',
            'linhvucs_grouped': linhvucs_grouped
        }