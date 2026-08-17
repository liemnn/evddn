# -*- coding: utf-8 -*-
import logging
from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import kehoach_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.kehoach_util: {e}")


class PhuHuynhKeHoachController(http.Controller):

    # 🌟 1. DANH SÁCH KẾ HOẠCH CỦA HỌC SINH (Sắp xếp từ mới nhất -> cũ nhất)
    @http.route('/ph/kehoachs', type='http', auth='user', website=True)
    def render_kehoach_list(self, **kwargs):
        user = request.env.user
        hocsinh = request.env['ekids.hocsinh'].sudo().search([('user_id', '=', user.id)], limit=1)

        if not hocsinh:
            return request.redirect('/app/phuhuynh')

        kehoachs = request.env['ekids.kehoach'].sudo().search([
            ('hocsinh_id', '=', hocsinh.id),
            ('trangthai', 'in', [kehoach_util.KEHOACH_DANG_CANTHIEP, kehoach_util.KEHOACH_HET_HIEULUC])
        ], order='tu_ngay desc, id desc')

        return request.render('ekids_phuhuynh.kehoach_list_mobile_template', {
            'hocsinh': hocsinh,
            'kehoachs': kehoachs,
            'KEHOACH_DANG_CANTHIEP': kehoach_util.KEHOACH_DANG_CANTHIEP,
            'KEHOACH_HET_HIEULUC': kehoach_util.KEHOACH_HET_HIEULUC,
        })

    # 🌟 2. XEM CHI TIẾT KẾ HOẠCH BẢN THU GỌN
    @http.route('/ph/kehoach/<int:kehoach_id>', type='http', auth='user', website=True)
    def render_kehoach_detail(self, kehoach_id, **kwargs):
        user = request.env.user
        hocsinh = request.env['ekids.hocsinh'].sudo().search([('user_id', '=', user.id)], limit=1)

        # Chặn bảo mật: Phụ huynh chỉ xem được kế hoạch của con mình
        kehoach = request.env['ekids.kehoach'].sudo().search([
            ('id', '=', kehoach_id),
            ('hocsinh_id', '=', hocsinh.id if hocsinh else 0)
        ], limit=1)

        if not kehoach:
            return request.redirect('/ph/kehoachs')

        return request.render('ekids_phuhuynh.kehoach_detail_mobile_template', {
            'o': kehoach,
            'hocsinh': hocsinh,
        })