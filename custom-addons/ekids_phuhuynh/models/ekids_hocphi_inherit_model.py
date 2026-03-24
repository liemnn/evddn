from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


import uuid
import calendar

class HocPhiInherit(models.Model):
    _inherit = "ekids.hocphi"



    @api.model
    def action_danhsach_hocphi_hocsinh(self):
        # Lấy giáo viên gắn với user hiện tại
        user = self.env.user
        if user:
            hocsinh = (self.env['ekids.hocsinh'].sudo()
                        .search([('user_id', '=', user.id)], limit=1))
            if hocsinh:

                list_view_id = self.env.ref('ekids_phuhuynh.hocphi_kanban_view').id


                return {
                    'type': 'ir.actions.act_window',
                    'name': 'THÔNG BÁO HỌC PHÍ ĐẾN PHỤ HUYNH: ',
                    'res_model': 'ekids.hocphi',
                    'view_mode': 'kanban',
                    'views': [(list_view_id, 'kanban')],
                    'domain': [('hocsinh_id', '=', hocsinh.id)],
                    'target': 'current',
                }
