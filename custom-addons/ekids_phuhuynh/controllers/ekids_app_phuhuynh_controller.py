from odoo import http
from odoo.http import request


class AppPhuHuynhController(http.Controller):

    # Định nghĩa đường link truy cập. Ví dụ: mydomain.com/app/phuhuynh
    @http.route('/app/phuhuynh', type='http', auth='public', website=True)
    def render_app_phu_huynh(self, **kwargs):
        # --- Ở đây anh có thể móc database Odoo để lấy dữ liệu thật ---
        # Ví dụ giả lập: (Sau này anh sẽ dùng request.env['ekids.hocphi'].search(...) để lấy)
        user = request.env.user
        if user:
            hocsinh = (request.env['ekids.hocsinh'].sudo()
                       .search([('user_id', '=', user.id)], limit=1))
            if hocsinh:
                data = {
                    'hocsinh': hocsinh.name,
                    'bietdanh': hocsinh.bietdanh,
                    'coso': hocsinh.coso_id.name,
                    'thong_bao_nha_truong': 'tra mẹ chú ý'
                }

        # Bắn dữ liệu vào template XML mà ta đã tạo ở Bước 3
        return request.render('ekids_phuhuynh.page_app_phuhuynh', data)