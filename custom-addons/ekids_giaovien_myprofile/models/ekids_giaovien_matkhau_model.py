import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from passlib.context import CryptContext

_logger = logging.getLogger(__name__)


class GiaoVienMatKhauWizard(models.TransientModel):
  _name = 'ekids.giaovien_matkhau'
  _description = 'Wizard đổi mật khẩu cá nhân'

  old_password = fields.Char(string='Mật khẩu hiện tại', required=True)
  new_password = fields.Char(string='Mật khẩu mới', required=True)
  confirm_password = fields.Char(string='Xác nhận mật khẩu mới', required=True)

  def action_xacnhan_doi_matkhau(self):
    self.ensure_one()

    # 1. Kiểm tra mật khẩu mới và xác nhận có khớp nhau không
    if self.new_password != self.confirm_password:
      raise UserError(
          _(
              '[Mật khẩu mới] bạn nhập vào ô [Xác nhận mật khẩu mới] không'
              ' khớp. Vui lòng kiểm tra lại!'
          )
      )

    # 2. Kiểm tra độ dài tối thiểu
    if len(self.new_password) < 6:
      raise UserError(_('Mật khẩu mới phải có ít nhất 6 ký tự.'))

    user = self.env.user

    # 3. Xác thực mật khẩu cũ bằng cách so sánh chuỗi băm trong database
    self.env.cr.execute(
        'SELECT password FROM res_users WHERE id = %s', (user.id,)
    )
    res = self.env.cr.fetchone()
    stored_password_hash = res[0] if res else ''

    is_valid = False
    if stored_password_hash:
      try:
        pwd_context = CryptContext(
            schemes=['pbkdf2_sha512', 'bcrypt', 'plaintext'], deprecated='auto'
        )
        is_valid = pwd_context.verify(self.old_password, stored_password_hash)
      except Exception as e:
        _logger.warning('Lỗi khi verify mật khẩu: %s', e)
        is_valid = False

    if not is_valid:
      raise UserError(_('Mật khẩu hiện tại không chính xác. Vui lòng nhập lại!'))

    # 4. Tiến hành đổi mật khẩu bằng phương thức write chuẩn của Odoo (Khắc phục hoàn toàn lỗi positional argument)
    try:
      user.sudo().write({'password': self.new_password})
    except Exception as e:
      raise UserError(_('Không thể cập nhật mật khẩu: %s') % e)

    # 5. Thông báo thành công và đóng popup
    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': _('Thành công'),
            'message': 'Mật khẩu của bạn đã được thay đổi thành công!',
            'type': 'success',
            'sticky': False,
            'next': {'type': 'ir.actions.act_window_close'},
        },
    }