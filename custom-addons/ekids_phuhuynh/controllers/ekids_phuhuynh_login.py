from odoo import http
from odoo.http import request
# Nạp thư viện Home mặc định của Odoo để ghi đè
from odoo.addons.web.controllers.home import Home


class PhuHuynhLogin(Home):

    def _login_redirect(self, uid, redirect=None):
        # Lấy thông tin User vừa đăng nhập thành công
        user = request.env['res.users'].sudo().browse(uid)

        # 1. KỂM TRA BỨC TƯỜNG LỬA: Nếu là Phụ huynh
        # 'ekids_app_phuhuynh' là tên thư mục module của anh
        if user.has_group('ekids_core.phuhuynh'):
            # Ép họ nhảy thẳng vào đường link App tĩnh của anh
            return '/app/phuhuynh'

        # 2. LỐI ĐI CHUẨN: Nếu không phải phụ huynh (là nhân viên, admin...)
        # Trả lại cho Odoo tự xử lý nhảy vào màn hình làm việc /web như bình thường
        return super(PhuHuynhLogin, self)._login_redirect(uid, redirect=redirect)