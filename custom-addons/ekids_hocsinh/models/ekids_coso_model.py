import ast
import json
from collections import defaultdict
from datetime import timedelta,date,datetime

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
            return {
                'type': 'ir.actions.act_window',
                'name': name,
                'res_model': 'ekids.hocphi',
                'view_mode': 'list,kanban,form',
                'order': 'hocsinh_id.name asc',
                'target': 'current',
                'domain': [('coso_id', '=', self.id),('thang_id', '=', hocphi2thang.id)],
                'context': {
                    'default_coso_id': self.id,
                    'default_nam': hocphi2thang.nam_id.name,
                    'default_thang': hocphi2thang.name

                }
            }

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
    def func_macdinh_tao_hocphi_thang_nay(self):
        today = date.today()
        if self.is_thu_hocphi_dauthang == False:
            # Bước 1: về ngày 1 tháng hiện tại
            first_day_this_month = today.replace(day=1)
            # Bước 2: lùi 1 ngày → cuối tháng trước
            last_day_last_month = first_day_this_month - timedelta(days=1)
            today = last_day_last_month

        year = today.year
        month =today.month

        hocphi2nam = self.env['ekids.hocphi_nam'].search(
            [('coso_id', '=', self.id)
                , ('name', '=', str(year))

             ])
        if not hocphi2nam:
            data ={
                'coso_id': self.id,
                'name':  str(year),
            }
            hocphi2nam = self.env['ekids.hocphi_nam'].create(data)

        hocphi2thang= self.env['ekids.hocphi_thang'].search(
            [('coso_id', '=', self.id)
                , ('nam_id', '=',hocphi2nam.id)
                , ('name', '=', str(month))

             ])
        if not hocphi2thang:
            data = {
                'coso_id': self.id,
                'nam_id': hocphi2nam.id,
                'name': str(month),
            }
            hocphi2thang = self.env['ekids.hocphi_thang'].create(data)
        return hocphi2thang


    def action_cauhinh_hocphi_dm_thu_bantru(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CẤU HÌNH - THU BÁN TRÚ (LỚP CHUNG)',
            'res_model': 'ekids.hocphi_dm_thu_bantru',
            'view_mode': 'list,form',
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
            'view_mode': 'list,form',
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

    # KEHOACH --> CLICK LỰA CHỌN COSO ra kanban học sinh
    def action_view_ekid_hocsinh_canthiep_kehoach_hocsinh(self):
        self.ensure_one()
        user = self.env.user
        view_id = self.env.ref('ekids_hocsinh.kehoach_hocsinh_kanban_view').id

        domain = [('id', '=', -1)]  # default rỗng

        gv = self.env['ekids.giaovien'].search([('user_id', '=', user.id)], limit=1)
        if gv:
            ketluans = self.env['ekids.ketluan'].search([
                ('gv_lapkehoach_id', '=', gv.id),
                ('trangthai', '=', '0')
            ])
            if ketluans:
                hocsinh_ids = ketluans.mapped('hocsinh_id.id')
                domain = [('id', 'in', hocsinh_ids)]

        return {
            'type': 'ir.actions.act_window',
            'name': _('HỌC SINH'),
            'res_model': 'ekids.hocsinh',
            'view_mode': 'kanban',
            'views': [(view_id, 'kanban')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.id,
            },
            'flags': {
                'kanban': {'create': False}
            }
        }








