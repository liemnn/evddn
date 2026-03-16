from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError

class LuongInherit(models.Model):
    _inherit = "ekids.luong"

    def action_danhsach_bangluong_giaovien(self):
        # Lấy giáo viên gắn với user hiện tại
        user = self.env.user
        if user:
            giaovien = (self.env['ekids.giaovien']
                        .search([('user_id', '=', user.id)], limit=1))
            if giaovien:
                list_view_id = self.env.ref('ekids_giaovien_myprofile.luong_inherit_list').id
                form_view_id = self.env.ref('ekids_giaovien.luong_form').id

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'LƯƠNG: ' + giaovien.name,
                    'res_model': 'ekids.luong',
                    'view_mode': 'list,form',
                    'views': [(list_view_id, 'list'),(form_view_id,'form')],
                    'domain': [('giaovien_id', '=', giaovien.id)],
                    'target': 'current',
                }








