# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import logging

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

        # 2. Lấy danh sách mục tiêu chi tiết của kế hoạch này
        targets_list = []
        count_dat = 0
        muctieus = baocao_gannhat.kehoach_linhvuc_ids.mapped('kehoach_muctieu_ids') if baocao_gannhat else []

        for idx, mt in enumerate(muctieus, 1):
            is_mastered = (getattr(mt, 'trangthai', '') == '1') or (getattr(mt, 'so_ngay_dat_lientiep', 0) >= 6)
            if is_mastered:
                count_dat += 1

            targets_list.append({
                'stt': idx,
                'linhvuc': mt.linhvuc_id.name if getattr(mt, 'linhvuc_id', False) else '',
                'tuoi': mt.tuoi_id.name if getattr(mt, 'tuoi_id', False) else '',
                'name': mt.name or '',
                'truoc_ct': f"{mt.solan_thu_dat}/{mt.solan_thu} ({mt.tyle_thu}%)" if getattr(mt, 'solan_thu', 0) else "0/10 (0%)",
                'sau_ct_rate': getattr(mt, 'tyle_trungbinh_canthiep', mt.tyle_thu or 0),
                'is_mastered': is_mastered,
                'dinh_huong': 'Khái quát tại nhà' if is_mastered else 'Tiếp tục duy trì'
            })

        total_targets = len(muctieus)
        rate_t1 = round((count_dat / total_targets * 100)) if total_targets else getattr(baocao_gannhat, 'tyle_dat_canthiep', 0)

        thoigian_str = ""
        if baocao_gannhat and baocao_gannhat.tu_ngay and baocao_gannhat.den_ngay:
            thoigian_str = f"Từ {baocao_gannhat.tu_ngay.strftime('%d/%m/%Y')} đến {baocao_gannhat.den_ngay.strftime('%d/%m/%Y')}"

        return {
            'has_plan': bool(baocao_gannhat),
            'hocsinh': {
                'name': self.name or '',
                'ngaysinh': self.ngaysinh.strftime('%d/%m/%Y') if hasattr(self, 'ngaysinh') and self.ngaysinh else '',
                'tuoi': getattr(self, 'tuoi', '') or '',
                'phuhuynh': getattr(self, 'ten_cha_me', '') or 'Đại diện Phụ huynh',
            },
            'tab1': {
                'ten': baocao_gannhat.name if baocao_gannhat else 'Chưa có kế hoạch',
                'thoigian': thoigian_str,
                'giaovien': baocao_gannhat.gv_lapkehoach_id.name if (baocao_gannhat and baocao_gannhat.gv_lapkehoach_id) else '',
                'quanly': baocao_gannhat.gv_kiemduyet_id.name if (baocao_gannhat and baocao_gannhat.gv_kiemduyet_id) else 'Ngô Thị Ngọc Hoàn',
                'tong_muctieu': total_targets or getattr(baocao_gannhat, 'tong_muctieu', 0),
                'dat_muctieu': count_dat,
                'tyle_dat': rate_t1,
                'targets': targets_list,
                'nhan_xet': (baocao_gannhat.desc if baocao_gannhat and baocao_gannhat.desc else (
                    "Trong tháng, trẻ có nhiều tiến bộ rõ rệt ở các phản ứng nghe gọi, ngồi bàn tập trung và giao tiếp mắt. "
                    "Cần tiếp tục phối hợp với phụ huynh đẩy mạnh tính khái quát tại gia đình."
                )) if baocao_gannhat else '',
            }
        }

    def func_get_baocao_kehoach(self,kehoach):

        baocao_linhvucs = []
        count_dat = 0
        muctieus = kehoach.kehoach_linhvuc_ids.mapped('kehoach_muctieu_ids') if kehoach else []

        for idx, mt in enumerate(muctieus, 1):
            is_mastered = (getattr(mt, 'trangthai', '') == '1') or (getattr(mt, 'so_ngay_dat_lientiep', 0) >= 6)
            if is_mastered:
                count_dat += 1

            baocao_linhvucs.append({
                'stt': idx,
                'linhvuc': mt.linhvuc_id.name if getattr(mt, 'linhvuc_id', False) else '',
                'tuoi': mt.tuoi_id.name if getattr(mt, 'tuoi_id', False) else '',
                'muctieu': mt.name or '',
                'truoc': f"{mt.solan_thu_dat}/{mt.solan_thu} ({mt.tyle_thu}%)" if getattr(mt, 'solan_thu',
                                                                                             0) else "0/10 (0%)",
                'sau': getattr(mt, 'tyle_trungbinh_canthiep', mt.solan_thu or 0),
                'mucdo': is_mastered,
                'dinh_huong': 'Khái quát tại nhà' if is_mastered else 'Tiếp tục duy trì'
            })

        total_targets = len(muctieus)
        rate_t1 = round((count_dat / total_targets * 100)) if total_targets else getattr(kehoach,
                                                                                         'tyle_dat_canthiep', 0)

        data ={
            "ten": kehoach.name,
            "tong_muctieu": kehoach.tong_muctieu,
            "tong_muctieu_dat": kehoach.tong_dat_kiemduyet,
            "linhvucs": baocao_linhvucs,
        }
        return data