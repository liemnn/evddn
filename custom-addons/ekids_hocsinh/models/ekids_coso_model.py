import ast
import json
from collections import defaultdict
from datetime import timedelta,date,datetime
from odoo.osv import expression

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")



class CoSo(models.Model):
    _inherit = "ekids.coso"


    hocphi_dm_chinhsach_giam_ids = fields.One2many("ekids.hocphi_dm_chinhsach_giam",
                                                   "coso_id", string="Chính sách giảm học phí")

    def action_view_ekids_hocsinh_kanban_action_window(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Học sinh của cơ sở',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            }
        }

    def action_xem_toanbo_hocphi_nam(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'HỌC PHÍ',
            'res_model': 'ekids.hocphi_nam',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id
            }
        }

    def action_tinh_hocphi_thang_nay(self):
        hocphi2thang = self.func_macdinh_tao_hocphi_thang_nay()
        if hocphi2thang:
            hocphi2thang.action_view_khoitao_hocphi_hocsinh()


            name = "HỌC PHÍ THÁNG "+str(hocphi2thang.name).upper()+"/"+ str(hocphi2thang.nam_id.name)
            domain = self.func_get_domain_trong_khoang_thoigian(hocphi2thang)

            return {
                'type': 'ir.actions.act_window',
                'name': name,
                'res_model': 'ekids.hocphi',
                'view_mode': 'list,kanban,form',
                'order': 'hocsinh_id.name asc',
                'target': 'current',
                'domain': domain,
                'context': {
                    'default_coso_id': self.id,
                    'default_nam': hocphi2thang.nam_id.name,
                    'default_thang': hocphi2thang.name

                }
            }

    def action_tinh_hocphi_thang_tieptheo(self):
        hocphi2thang = self.func_macdinh_tao_hocphi_thang_tieptheo()
        if hocphi2thang:
            hocphi2thang.action_view_khoitao_hocphi_hocsinh()


            name = "HỌC PHÍ THÁNG "+str(hocphi2thang.name).upper()+"/"+ str(hocphi2thang.nam_id.name)
            domain = self.func_get_domain_trong_khoang_thoigian(hocphi2thang)

            return {
                'type': 'ir.actions.act_window',
                'name': name,
                'res_model': 'ekids.hocphi',
                'view_mode': 'list,kanban,form',
                'order': 'hocsinh_id.name asc',
                'target': 'current',
                'domain': domain,
                'context': {
                    'default_coso_id': self.id,
                    'default_nam': hocphi2thang.nam_id.name,
                    'default_thang': hocphi2thang.name

                }
            }

    def func_xoa_hocphi_khi_hocsinh_nghi_trongthang(self,hocphi2thang):
        hocphi_ids = hocphi2thang.hocphi_ids
        if hocphi_ids:
            nam = int(hocphi2thang.nam_id.name)
            thang = int(hocphi2thang.name)
            days = ngay_util.func_get_cacngay_trong_thang(nam,thang)
            tu_ngay =days[0]

            for hocphi in hocphi_ids:
                ngay_nghihoc = hocphi.hocsinh_id.ngay_nghihoc
                if ngay_nghihoc:
                    if ngay_nghihoc < tu_ngay:
                        hocphi.with_context(unlink_by_system=True).unlink()
                        #hocphi.unlink()



    def func_get_domain_trong_khoang_thoigian(self,hocphi2thang):
        nam = int(hocphi2thang.nam_id.name)
        thang = int(hocphi2thang.name)
        ngays = ngay_util.func_get_cacngay_trong_thang(nam, thang)
        tu_ngay = ngays[0]
        den_ngay = ngays[len(ngays) - 1]

        today = date.today()
        thang_today =today.month
        nam_today = today.year
        domain = [('coso_id', '=', self.id), ('thang_id', '=', hocphi2thang.id)]
        if (thang_today == thang
            and nam_today == nam):
            # xoa những học sinh đã nghỉ tháng này
            self.func_xoa_hocphi_khi_hocsinh_nghi_trongthang(hocphi2thang)

            domain_chung = [('coso_id', '=', self.id),
                     ('thang_id', '=', hocphi2thang.id),
                     ('hocsinh_id.ngay_nhaphoc', '<=', den_ngay)
                     ]



            # Nhóm 1: Học sinh đang theo học
            domain_theohoc = [
                ('hocsinh_id.trangthai', '=', '1'),
            ]

            # Nhóm 2: Học sinh đã nghỉ nhưng nghỉ trong tháng tìm kiếm
            domain_danghi = [
                ('hocsinh_id.ngay_nghihoc', '!=', False),
                ('hocsinh_id.ngay_nghihoc', '>=', tu_ngay)
            ]


            domain = expression.AND([
                domain_chung,
                expression.OR([
                    domain_theohoc,
                    domain_danghi
                ])
            ])

        return domain

    def action_quanly_khoan_thungoai(self):

            return {
                'type': 'ir.actions.act_window',
                'name': 'THU NGOÀI',
                'res_model': 'ekids.hocphi_thungoai',
                'view_mode': 'list,form',
                'target': 'current',
                'domain': [('coso_id', '=', self.id)],
                'context': {
                    'default_coso_id': self.id

                }
            }

    def func_macdinh_tao_hocphi_thang_tieptheo(self):
        today = fields.Date.context_today(self)

        current_year = today.year
        current_month = today.month

        # Tính tháng tiếp theo và xử lý chuyển năm khi là tháng 12
        if current_month == 12:
            month = 1
            year = current_year + 1
        else:
            month = current_month + 1
            year = current_year

        hocphi2thang = self.func_macdinh_tao_hocphi(year, month)
        return hocphi2thang
    def func_macdinh_tao_hocphi_thang_nay(self):
        today = date.today()
        # Mốc ngày 1 tháng hiện tại
        ngay_dauthang = today.replace(day=1)

        if self.is_thu_hocphi_dauthang == True:
            # TH1: Thu học phí ĐẦU THÁNG
            # - Hôm nay < 28: Thu học phí tháng này
            # - Hôm nay >= 28: Thu học phí tháng tiếp theo (Ví dụ: 31/10 -> Tháng 11)
            if today.day >= 28:
                # Nhảy sang ngày 28 của tháng hiện tại rồi cộng thêm 5 ngày để chắc chắn sang tháng sau
                target_date = ngay_dauthang.replace(day=28) + timedelta(days=5)
            else:
                target_date = ngay_dauthang
        else:
            # TH2: Thu học phí CUỐI THÁNG
            # - Hôm nay >= 28: Thu học phí tháng này (Ví dụ: 31/10 -> Tháng 10)
            # - Hôm nay < 28: Thu học phí tháng trước (Ví dụ: 20/10 -> Tháng 9)
            if today.day >= 28:
                target_date = ngay_dauthang
            else:
                # Ngày 1 tháng này lùi 1 ngày -> ngày cuối của tháng trước
                target_date = ngay_dauthang - timedelta(days=1)

        year = target_date.year
        month = target_date.month

        hocphi2thang = self.func_macdinh_tao_hocphi(year, month)
        return hocphi2thang




    def func_macdinh_tao_hocphi(self,nam,thang):

        hocphi2nam = self.env['ekids.hocphi_nam'].search(
            [('coso_id', '=', self.id)
                , ('name', '=', str(nam))

             ])
        if not hocphi2nam:
            data ={
                'coso_id': self.id,
                'name':  str(nam),
            }
            hocphi2nam = self.env['ekids.hocphi_nam'].create(data)

        hocphi2thang= self.env['ekids.hocphi_thang'].search(
            [('coso_id', '=', self.id)
                , ('nam_id', '=',hocphi2nam.id)
                , ('name', '=', str(thang))

             ])
        if not hocphi2thang:
            data = {
                'coso_id': self.id,
                'nam_id': hocphi2nam.id,
                'name': str(thang),
            }
            hocphi2thang = self.env['ekids.hocphi_thang'].create(data)
        return hocphi2thang




    def action_cauhinh_hocphi_dm_thu_bantru(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CẤU HÌNH - THU BÁN TRÚ (LỚP CHUNG)',
            'res_model': 'ekids.hocphi_dm_thu_bantru',
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            }
        }



    def action_cauhinh_hocphi_dm_ca(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CẤU HÌNH - CA/LỚP CAN THIỆP',
            'res_model': 'ekids.hocphi_dm_ca',
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            }
        }

    def action_cauhinh_hocphi_dm_chinhsach_giam(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'CẤU HÌNH - DANH MỤC GIẢM HỌC PHÍ',
            'res_model': 'ekids.hocphi_dm_chinhsach_giam',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            }
        }

    def action_xem_hocphi_dm(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'CẤU HÌNH - MỤC THU HỌC PHÍ',
            'res_model': 'ekids.hocphi_dm',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
            }
        }





    def action_view_ekid_hocsinh_print_hocphi(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cấu hình thông tin phục vụ Print học phí:' + self.name,
            'res_model': 'ekids.hocphi_in_phieuthu',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai':'1'

            }

        }








