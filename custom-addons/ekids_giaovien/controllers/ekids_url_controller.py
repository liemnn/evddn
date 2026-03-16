# controllers/main.py
from odoo import http
from odoo.http import request
from werkzeug.utils import redirect

class GiaoVienController(http.Controller):

    @http.route(['/ekids/giaovien', '/ekids/giaovien/<int:menu_id>'],
                type='http', auth='user', methods=['GET'], csrf=False)
    def open_giaovien_menu(self, menu_id=None, **kw):
        # dùng sudo để tránh quyền đọc block nếu cần (tùy thiết kế)
        user = request.env.user.sudo()
        gv = (request.env['ekids.giaovien'].sudo()
              .search([('user_id', '=', user.id)], limit=1))
        if gv:
            # redirect tới client view form của bản ghi
            # kèm menu_id nếu bạn muốn highlight menu (không bắt buộc)
            url = '/web#id=%s&model=ekids.giaovien&view_type=form' % (gv.id,)
            if menu_id:
                url += '&menu_id=%s' % int(menu_id)
            return redirect(url)
        else:
            # fallback: vào danh sách giáo viên
            return redirect('/web#model=ekids.giaovien&view_type=list')
