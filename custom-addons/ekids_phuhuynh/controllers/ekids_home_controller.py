from odoo import http,fields
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



class HomeController(http.Controller):

    # Định nghĩa đường link truy cập. Ví dụ: mydomain.com/app/phuhuynh
    @http.route('/ph/home', type='http', auth='public', website=True)
    def render_app_phu_huynh(self, **kwargs):
        # --- Ở đây anh có thể móc database Odoo để lấy dữ liệu thật ---
        # Ví dụ giả lập: (Sau này anh sẽ dùng request.env['ekids.hocphi'].search(...) để lấy)
        user = request.env.user
        if user:
            hocsinh = (request.env['ekids.hocsinh'].sudo()
                       .search([('user_id', '=', user.id)], limit=1))
            if hocsinh:
                today = date.today()
                hocphi_thang_nay = request.env['ekids.hocphi'].sudo().search([
                    ('hocsinh_id', '=', hocsinh.id),
                    ('thang_id.name', '=', str(today.month)),
                    ('nam_id.name', '=', str(today.year)),
                    ('trangthai', 'in', ['0','2']),
                ], limit=1)
                thongbaos = self.func_get_thongbaos(hocsinh,hocphi_thang_nay)
                data = {
                    'hocsinh': hocsinh.name,
                    'bietdanh': hocsinh.bietdanh,
                    'coso': hocsinh.coso_id.name,
                    'thongbao': thongbaos,
                    # Khai báo mặc định để chống lỗi QWeb
                    'hocphi_id': False,
                    'hocphi_phaidong': 0,
                    'hocphi_thang': '',
                    'hocphi_nam': '',
                }

                if hocphi_thang_nay:
                    data['hocphi_id'] =hocphi_thang_nay.id
                    data['hocphi_phaidong'] = hocphi_thang_nay.hocphi_phaidong
                    data['hocphi_thang'] = hocphi_thang_nay.thang_id.name
                    data['hocphi_nam'] = hocphi_thang_nay.nam_id.name

        # Bắn dữ liệu vào template XML mà ta đã tạo ở Bước 3
        return request.render('ekids_phuhuynh.page_app_phuhuynh', data)


    def func_get_thongbaos(self,hocsinh,hocphi):
        thongbao=""
        #Thông báo 1:  học phí
        if hocphi:
            thongbao += ("Phụ huynh hãy hoàn thành nộp học phí tháng "
                         + hocphi.thang_id.name
                         + " năm "
                         + hocphi.nam_id.name)+"."
        #TB từ nhà trường
        tbs =self.func_get_thongbao_trongngay(hocsinh.coso_id.id)
        if tbs:
            for tb in tbs:
                thongbao += "    "+tb.name+'.'
        return  thongbao

    def func_get_thongbao_trongngay(self, coso_id=None):
        """
        Hàm lấy danh sách thông báo có hiệu lực trong ngày hôm nay.
        Có thể truyền thêm coso_id để lọc riêng thông báo của cơ sở đó.
        """
        # Dùng context_today để lấy ngày chuẩn theo múi giờ của User (Tránh lỗi lệch giờ)
        today = fields.Date.context_today(request.env.user)

        # Xây dựng bộ lọc (Domain)
        domain = [
            ('trangthai', '=', '1'),  # Chỉ lấy thông báo đã gửi
            ('tu_ngay', '<=', today),  # Ngày bắt đầu <= Hôm nay
            ('den_ngay', '>=', today)  # Ngày kết thúc >= Hôm nay
        ]

        # Nếu có truyền ID cơ sở thì lọc thêm theo cơ sở
        if coso_id:
            domain.append(('coso_id', '=', coso_id))

        # Thực hiện truy vấn và sắp xếp thông báo mới nhất lên đầu
        thongbaos = request.env['ekids.thongbao'].sudo().search(domain)

        return thongbaos



