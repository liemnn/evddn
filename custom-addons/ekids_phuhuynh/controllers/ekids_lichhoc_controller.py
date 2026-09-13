# -*- coding: utf-8 -*-
import logging
from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PhuHuynhLichHocController(http.Controller):

    @http.route(['/ph/lichhoc', '/ph/lichhocs'], type='http', auth='user', website=True)
    def render_lichhoc_list(self, **kwargs):
        user = request.env.user
        # Tìm học sinh gắn với tài khoản phụ huynh đang đăng nhập
        hocsinh = request.env['ekids.hocsinh'].sudo().search([('user_id', '=', user.id)], limit=1)

        if not hocsinh:
            return request.redirect('/app/phuhuynh')

        # Lấy danh sách ca can thiệp / lịch học của bé
        ca_canthiep_list = request.env['ekids.hocsinh_ca_canthiep'].sudo().search([
            ('hocsinh_id', '=', hocsinh.id)
        ], order='sequence asc, tu_ngay desc, id desc')

        return request.render('ekids_phuhuynh.lichhoc_list_mobile_template', {
            'hocsinh': hocsinh,
            'ca_canthiep_list': ca_canthiep_list,
        })