from odoo import models, fields, api, _
from passlib.context import CryptContext
from odoo.exceptions import UserError, ValidationError
import logging
from odoo.http import request
_logger = logging.getLogger(__name__)

class User(models.Model):
    _inherit = 'res.users'


    #password = fields.Char("Mật khẩu")

    coso_ids = fields.Many2many(comodel_name="ekids.coso"
                                ,relation="ekids_users4coso_ids_rel"
                                ,column1="user_id"
                                ,column2="coso_id"
                                ,string="Quản lý các cơ sở"
                                ,required=True
                                ,default=lambda self: self.env['ekids.coso']
                                    .search([],limit=5).ids)

    @api._model_create_single
    def create(self, vals):
        # Gán đối tác vừa tạo vào đơn hàng
        # Tạo giáo viên
        if not vals["password"]:
            raise ValidationError(
                _("Bạn chưa nhập mật khẩu hoặc Số điện thoại để khởi tạo tài khoản cho Giáo viên"))
        try:
            vals['lang']='vi_VN'
            vals['tz'] = 'Asia/Ho_Chi_Minh'
            record = super(User, self).create(vals)
            return self.func_gan_userid_vao_giaovien(record)
        except Exception as e:
            _logger.exception(e)
            login = self.env.context['default_login']
            if login:
                user = self.env['res.users'].search([('login', '=', login)],limit=1)
                if user:
                    count_giaoviens = self.env['ekids.giaovien'].search_count([('user_id', '=',user.id)])
                    if count_giaoviens <= 0:
                        return self.func_gan_userid_vao_giaovien(user)
                    else:
                        raise ValidationError(
                            _("Tài khoản [Số điện thoại] đã có người khác sử dụng!"))
                raise ValidationError(
                    _("Tài khoản [Số điện thoại] đã có người khác sử dụng!"))
            else:
                raise ValidationError(
                    _("Tài khoản [Số điện thoại] đã có người khác sử dụng!"))

    def func_gan_userid_vao_giaovien(self,user):
        if user:
            if 'default_giaovien_id' in self.env.context:
                giaovien_id = self.env.context['default_giaovien_id']
                if giaovien_id:
                    giaovien = self.env['ekids.giaovien'].search([('id', '=', giaovien_id)])
                    if giaovien:
                        giaovien.write({'user_id': user.id})
                        group = self.env.ref('ekids_core.giaovien')  # gán quyền phụ huynh cho user
                        if group:
                            user.groups_id = [(4, group.id)]  # thêm group

        return user




    def action_reset_password(self):
        # Ví dụ: Gửi email đặt lại mật khẩu (nếu cần)
        for user in self:
            user.sudo().with_context(create_user=True).action_reset_password()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Password Reset',
                'message': f'The password reset email has been sent to {self.name}.',
                'type': 'success',  # Loại thông báo: success, warning, danger
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

