from odoo import api, fields, models
from datetime import datetime
class ThongBaoPhuHuynhInherit(models.Model):
    _inherit = 'ekids.thongbao_phuhuynh'

    @api.model
    def action_danhsach_thongbao_phuhuynh(self):
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
