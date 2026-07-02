from odoo import models, fields, api, _
from datetime import datetime, timedelta,date
import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")



class CoSo(models.Model):
    _inherit = "ekids.coso"

    is_ketluan = fields.Boolean(compute="_compute_is_ketluan")

    def _compute_is_ketluan(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_role_ketluan = user.has_group('ekids_core.ketluan')

        for record in self:
           if (is_admin
               or is_role_ketluan):
               record.is_ketluan = True
           else:
               record.is_ketluan = False


    def action_xem_chuongtrinh_kanban(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH',
            'res_model': 'ekids.ct_chuongtrinh',
            'view_mode': 'kanban,list,form',
            'domain': [('coso_id', '=', self.id)],
            'target': 'current',
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_roiloan(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH MỤC [RỐI LOẠN]',
            'res_model': 'ekids.ct_dm_roiloan',
            'view_mode': 'list,kanban,form',

            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_lieuluong(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH MỤC [LIỀU LƯỢNG]',
            'res_model': 'ekids.ct_dm_lieuluong',
            'view_mode': 'list,kanban,form',

            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_mucdo(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH MỤC [MỨC ĐỘ]',
            'res_model': 'ekids.ct_dm_mucdo',
            'view_mode': 'list,kanban,form',

            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_phuongphap(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH MỤC [PHƯƠNG PHÁP]',
            'res_model': 'ekids.ct_dm_phuongphap',
            'view_mode': 'list,kanban,form',

            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_danhsach_hocsinh_ketluan(self):
        list_view_id = self.env.ref('ekids_canthiep.hocsinh_ketluan_inherit_list').id
        domain = [('coso_id', '=', self.id)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            },
        }

    def action_danhsach_hocsinh_lap_kehoach(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        list_view_id = self.env.ref('ekids_canthiep.hocsinh_lap_kehoach_inherit_list').id
        domain = [('coso_id', '=', self.id)]

        if is_admin == False:
            hocsinh_ids = kehoach_util.func_get_ids_hocsinh_theo_vaitro_lap_kehoach(self)
            domain = [('coso_id', '=', self.id),('id','in',hocsinh_ids)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            },
        }

    def action_danhsach_hocsinh_duyet_kehoach(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        list_view_id = self.env.ref('ekids_canthiep.hocsinh_duyet_kehoach_inherit_list').id
        domain = [('coso_id', '=', self.id)]
        if is_admin == False:
            hocsinh_ids = kehoach_util.func_get_ids_hocsinh_theo_vaitro_duyet_kehoach(self)
            domain = [('coso_id', '=', self.id),('id','in',hocsinh_ids)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            },
        }

    def action_danhsach_hocsinh_canthiep(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        list_view_id = self.env.ref('ekids_canthiep.hocsinh_canthiep_inherit_list').id
        domain = [('coso_id', '=', self.id)]
        if is_admin == False:
            hocsinh_ids = kehoach_util.func_get_ids_hocsinh_theo_vaitro_canthiep_kehoach(self)
            domain = [('coso_id', '=', self.id), ('id', 'in', hocsinh_ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            },
        }




