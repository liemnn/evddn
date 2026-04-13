from odoo import http
from odoo.http import request


class AppPhuHuynhController(http.Controller):

    # Định nghĩa đường link truy cập. Ví dụ: mydomain.com/app/phuhuynh
    @http.route('/app/phuhuynh', type='http', auth='public', website=True)
    def render_app_phu_huynh(self, **kwargs):
        # --- Ở đây anh có thể móc database Odoo để lấy dữ liệu thật ---
        # Ví dụ giả lập: (Sau này anh sẽ dùng request.env['ekids.hocphi'].search(...) để lấy)
        data = {
            'ten_hoc_sinh': 'Nguyễn Ngọc Anh',
            'ten_lop': 'Lớp Cá Heo',
            'so_thong_bao': 5
        }

        # Bắn dữ liệu vào template XML mà ta đã tạo ở Bước 3
        return request.render('ekids_phuhuynh.page_app_phuhuynh', data)