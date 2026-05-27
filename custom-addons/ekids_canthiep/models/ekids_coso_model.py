from odoo import models, fields, api, _
from datetime import datetime, timedelta,date

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

    def action_xem_kehoach_canthiep(self):
        list_view_id = self.env.ref('ekids_canthiep.kehoach_hocsinh_inherit_list').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            },
        }




