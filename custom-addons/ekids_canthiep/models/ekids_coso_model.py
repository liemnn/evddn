from odoo import models, fields, api, _
from datetime import datetime, timedelta,date

class CoSo(models.Model):
    _inherit = "ekids.coso"


    def action_xem_chuongtrinh_kanban(self):
        kanban_view_id = self.env.ref('ekids_canthiep.ct_chuongtrinh_kanban').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.ct_chuongtrinh',
            'view_mode': 'list,form',
            'views': [(kanban_view_id, 'kanban')],
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }




