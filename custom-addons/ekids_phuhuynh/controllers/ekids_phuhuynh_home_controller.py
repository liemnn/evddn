# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home


class PhuHuynhHomeController(Home):

    def _login_redirect(self, uid, redirect=None):
        """
        1. Xử lý điều hướng ngay sau khi đăng nhập thành công
        """
        if uid:
            user = request.env['res.users'].sudo().browse(uid)
            # Kiểm tra xem tài khoản này có phải là Phụ huynh gắn với Học sinh không
            hocsinh = request.env['ekids.hocsinh'].sudo().search([('user_id', '=', user.id)], limit=1)
            if hocsinh:
                return '/ph/home'

        # Nếu là tài khoản Admin / Giáo viên / Nhân viên -> dùng luồng chuẩn của Odoo
        return super()._login_redirect(uid, redirect=redirect)

    @http.route('/', type='http', auth='public', website=True, sitemap=False)
    def index(self, **kw):
        """
        2. Xử lý khi truy cập trang gốc domain (http://evddn.vn/)
        """
        # Nếu chưa đăng nhập -> chuyển về trang login
        if not request.session.uid:
            return request.redirect('/web/login')

        user = request.env['res.users'].sudo().browse(request.session.uid)
        hocsinh = request.env['ekids.hocsinh'].sudo().search([('user_id', '=', user.id)], limit=1)

        # Nếu là tài khoản Phụ huynh -> vào Mobile App Home
        if hocsinh:
            return request.redirect('/ph/home')

        # Nếu là Admin/Giáo viên/Nhân viên -> vào Backend Web Client
        return request.redirect('/web')