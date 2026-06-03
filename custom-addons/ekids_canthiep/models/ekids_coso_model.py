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


    def action_xem_chuongtrinh_kanban(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.ct_chuongtrinh',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_roiloan(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.ct_dm_roiloan',
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_kehoach_canthiep(self):
        list_view_id = self.env.ref('ekids_canthiep.kehoach_hocsinh_inherit_list').id
        form_view_id = self.env.ref('ekids_canthiep.kehoach_hocsinh_inherit_form').id
        hocsinh_ids = kehoach_util.func_get_ids_hocsinh_theo_vaitro(self)
        domain =[('coso_id', '=', self.id)]
        if hocsinh_ids:
            domain = [('coso_id', '=', self.id),('id','in',hocsinh_ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list,form',
            'views': [(list_view_id, 'list'),(form_view_id, 'form')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            },
        }




