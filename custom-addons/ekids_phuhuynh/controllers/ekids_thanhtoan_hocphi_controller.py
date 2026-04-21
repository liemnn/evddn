from odoo import http
from odoo.http import request
from datetime import date,datetime,timedelta

import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
    from odoo.addons.ekids_func import hocsinh_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")


class ThanhToanHocPhiController(http.Controller):
    # ... các code cũ giữ nguyên ...

    # 1. RENDER TRANG CHI TIẾT THANH TOÁN
    # 1. RENDER GIAO DIỆN XÁC NHẬN THANH TOÁN
    # RENDER TRANG CHI TIẾT THANH TOÁN
    @http.route('/ph/hocphi/thanhtoan/<int:hocphi_id>', type='http', auth='user', website=True)
    def render_thanhtoan_page(self, hocphi_id, **kwargs):
        user = request.env.user

        # Kiểm tra bảo mật: Học phí phải thuộc về con của user này
        hocphi = request.env['ekids.hocphi'].sudo().search([
            ('id', '=', hocphi_id),
            ('hocsinh_id.user_id', '=', user.id)
        ], limit=1)

        if not hocphi:
            return request.redirect('/ph/hocphi')

        # DỮ LIỆU TRUYỀN RA XML (Đảm bảo có biến 'hocsinh')
        data = {
            'hp': hocphi,
            'coso': hocphi.coso_id,
            'hocsinh': hocphi.hocsinh_id,  # <--- BẮT BUỘC PHẢI CÓ DÒNG NÀY
        }

        return request.render('ekids_phuhuynh.payment_page', data)

    # 2. API CẬP NHẬT TRẠNG THÁI = '13' KHI CLICK NÚT
    @http.route('/ph/hocphi/confirm_pay', type='json', auth='user', methods=['POST'])
    def confirm_payment_status(self, hocphi_id):
        user = request.env.user
        hocphi = request.env['ekids.hocphi'].sudo().search([
            ('id', '=', int(hocphi_id)),
            ('hocsinh_id.user_id', '=', user.id)
        ], limit=1)

        if hocphi:
            # Cập nhật trạng thái chờ xác nhận
            hocphi.write({'trangthai': '01'})
            return {'success': True}

        return {'success': False, 'error': 'Lỗi dữ liệu xác thực'}