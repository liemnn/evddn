from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError

class GiaoVienInherit(models.Model):
    _inherit = "ekids.giaovien"





    def action_mo_hoso_canhan(self):
        # Lấy giáo viên gắn với user hiện tại
        user = self.env.user
        if user:
            giaovien = (self.env['ekids.giaovien']
                        .search([('user_id', '=', user.id)], limit=1))
            if giaovien:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Giáo viên của cơ sở',
                    'res_model': 'ekids.giaovien',
                    'view_mode': 'form',
                    'res_id': giaovien.id,
                    'target': 'current',
                    'context': {'form_view_initial_mode': 'view'}

                }






