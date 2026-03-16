from odoo import models, fields, api, _
from passlib.context import CryptContext

class User(models.Model):
    _inherit = 'res.users'


    @api._model_create_single
    def create(self, vals):
        # Gán đối tác vừa tạo vào đơn hàng
        # Tạo giáo viên
        vals['lang'] = 'vi_VN'
        vals['tz'] = 'Asia/Ho_Chi_Minh'
        record = super(User, self).create(vals)
        if record:
            if 'hocsinh_id' in self.env.context:
                hocsinh_id = self.env.context['hocsinh_id']
                if hocsinh_id:
                    hocsinh = self.env['ekids.hocsinh'].search([('id', '=', hocsinh_id)])
                    if hocsinh:
                        hocsinh.write({'user_id': record.id})
                        group = self.env.ref('ekids_core.phuhuynh')  # gán quyền phụ huynh cho user
                        if group:
                            record.groups_id = [(4, group.id)]  # thêm group


        return record



