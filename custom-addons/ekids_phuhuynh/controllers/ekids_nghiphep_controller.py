# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from datetime import date
import html
import logging

_logger = logging.getLogger(__name__)


class NghiPhepController(http.Controller):

    @http.route('/ph/nghiphep', type='http', auth='user', website=True)
    def render_nghiphep_list(self, **kwargs):
        user = request.env.user
        # Tìm học sinh gắn với tài khoản phụ huynh
        hocsinh = request.env['ekids.hocsinh'].sudo().search([('user_id', '=', user.id)], limit=1)

        if not hocsinh:
            return request.redirect('/app/phuhuynh')

        # Lấy ngày hiện tại chuẩn theo múi giờ User (Asia/Ho_Chi_Minh)
        today = fields.Date.context_today(request.env.user)
        start_of_year = date(today.year, 1, 1)
        end_of_year = date(today.year, 12, 31)

        # Lấy danh sách nghỉ phép của bé trong năm nay
        records = request.env['ekids.hocsinh_nghiphep'].sudo().search([
            ('hocsinh_id', '=', hocsinh.id),
            ('tu_ngay', '>=', start_of_year),
            ('tu_ngay', '<=', end_of_year)
        ], order='tu_ngay desc')

        nghiphep_list = []
        for np in records:
            # Tính số ngày nghỉ (bao gồm cả ngày bắt đầu và kết thúc)
            so_ngay = (np.den_ngay - np.tu_ngay).days + 1 if np.tu_ngay and np.den_ngay else 0

            nghiphep_list.append({
                'id': np.id,
                'tu_ngay': np.tu_ngay,
                'den_ngay': np.den_ngay,
                'so_ngay': so_ngay,
                'desc': np.desc,  # Trường HTML lý do
                'is_mine': np.create_uid.id == user.id,  # Phân quyền: mình tạo hay trường tạo
                'is_hoantra_hocphi': np.is_hoantra_hocphi,
                'tyle_hoantra_hocphi': np.tyle_hoantra_hocphi,
            })

        return request.render('ekids_phuhuynh.nghiphep_page', {
            'hocsinh_id': hocsinh.id,
            'nghiphep_list': nghiphep_list,
            'today_str': today.strftime('%Y-%m-%d'),
        })

    @http.route('/ph/nghiphep/submit', type='json', auth='user', methods=['POST'])
    def submit_nghiphep(self, **post):
        """Xử lý nộp đơn mới"""
        hocsinh_id = post.get('hocsinh_id')
        lydo = post.get('lydo', '').strip()
        tu_ngay = post.get('tu_ngay')
        den_ngay = post.get('den_ngay')

        if not (hocsinh_id and lydo and tu_ngay and den_ngay):
            return {'success': False, 'error': 'Vui lòng điền đầy đủ thông tin.'}

        try:
            # Chống lỗi logic ngày tháng
            if tu_ngay > den_ngay:
                return {'success': False, 'error': 'Ngày bắt đầu không được sau ngày kết thúc.'}

            # Tạo bản ghi với lý do định dạng HTML
            request.env['ekids.hocsinh_nghiphep'].sudo().create({
                'hocsinh_id': int(hocsinh_id),
                'tu_ngay': tu_ngay,
                'den_ngay': den_ngay,
                'desc': f"<p>{html.escape(lydo)}</p>"
            })
            return {'success': True}
        except Exception as e:
            _logger.error(f"Error Submit Leave: {str(e)}")
            return {'success': False, 'error': "Lỗi máy chủ khi gửi đơn."}

    @http.route('/ph/nghiphep/delete', type='json', auth='user', methods=['POST'])
    def delete_nghiphep(self, **post):
        """Xử lý hủy đơn (Xóa bản ghi)"""
        nghiphep_id = post.get('nghiphep_id')
        user = request.env.user

        try:
            # Bảo mật: Chỉ tìm đơn đúng ID và phải do chính User này tạo
            record = request.env['ekids.hocsinh_nghiphep'].sudo().search([
                ('id', '=', int(nghiphep_id)),
                ('create_uid', '=', user.id)
            ], limit=1)

            if record:
                record.unlink()
                return {'success': True}
            return {'success': False, 'error': 'Bạn không có quyền xóa đơn này hoặc đơn không tồn tại.'}
        except Exception as e:
            return {'success': False, 'error': "Không thể thực hiện yêu cầu."}