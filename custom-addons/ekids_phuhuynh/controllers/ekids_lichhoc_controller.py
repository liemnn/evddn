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



class LichHocController(http.Controller):

    # Định nghĩa đường link truy cập. Ví dụ: mydomain.com/app/phuhuynh
    @http.route('/ph/lichhoc/<int:nam>/<int:thang>', type='http', auth='public', website=True)
    def render_app_phu_huynh(self,nam,thang, **kwargs):
        # --- Ở đây anh có thể móc database Odoo để lấy dữ liệu thật ---
        # Ví dụ giả lập: (Sau này anh sẽ dùng request.env['ekids.hocphi'].search(...) để lấy)
        user = request.env.user
        qcontext = {
            'danh_sach_ngay': []
        }
        if user:
            hocsinh = (request.env['ekids.hocsinh'].sudo()
                       .search([('user_id', '=', user.id)], limit=1))
            if hocsinh:
                data =self.func_get_ca2hocsinh(hocsinh)
                qcontext['danh_sach_ngay'] = data


        # Bắn dữ liệu vào template XML mà ta đã tạo ở Bước 3
        return request.render('ekids_phuhuynh.lichhoc', qcontext)

    def func_get_lichhoc(self, hocsinh):
        today = date.today()
        diemdanh = (request.env['ekids.diemdanh_hocsinh2thang']
                    .sudo().search([('hocsinh_id', '=', hocsinh.id),
                                    ('diemdanh_id.thang', '=', str(today.month)),
                                    ('diemdanh_id.nam', '=', str(today.year)),
                                    ]))
        if diemdanh:
           return self.func_get_lichhoc_trongthang(hocsinh)
        else:
           return self.func_get_ca2hocsinh(hocsinh)

    def func_get_lichhoc_trongthang(self,hocsinh):
        days = ngay_util.get_ngays_luive_mungmot()
        data=[]
        for day in days:
            cas =self.func_get_thongtin_ca_trongthang(hocsinh,day)
            data.append({
                'week': str(day.weekday()),
                'date': day,
                'cas': cas,
            })
        return data

    def func_get_ca_trongngay(self, hocsinh, ngay):
        ca2ngays = request.env['ekids.diemdanh_ca2ngay'].search([
            ('hocsinh_id', '=', hocsinh.id),
            ('ngay', '=', ngay),
        ])
        data = []
        if ca2ngays:
            for ca2ngay in ca2ngays:
                dm_ca = ca2ngay.hocphi_dm_ca_id
                gia = string_util.number2string(dm_ca.tien)
                values = {
                    'tu': dm_ca.tu,
                    'den': dm_ca.den,
                    'ca': dm_ca.name,
                    # Đổi chữ 'tien' thành 'gia' để khớp 100% với file XML
                    'gia': gia,
                    'trangthai': ca2ngay.trangthai
                }
                data.append(values)

        else:
            #không có ca trong ngay
            ca2thus =hocsinh_util.func_get_tinhtoan_ca2thu_theo_thu(hocsinh,ngay)




        return data



    def func_get_ca2hocsinh(self,hocsinh):
        today = date.today()

        ca2hocsinhs =  request.env['ekids.hocsinh_ca_canthiep'].sudo().search([('hocsinh_id', '=', hocsinh.id)])
        thus = self.func_get_ngay_trong_tuan()
        if thus:
            data =[]
            for thu in thus:
                week = thu['week']
                cas= self.func_get_thongtin_ca_trongngay(thu,ca2hocsinhs)
                data.append({
                    'week': thu['week'],
                    'date': thu['date'],
                    'cas':cas,
                })
            return  data

    def func_get_thongtin_ca_trongngay(self, thu, ca2hocsinhs):
        data = []
        for ca in ca2hocsinhs:
            if thu['week'] in ca.name:

                # Bổ sung thuật toán Format tiền: 150000.0 -> 150.000
                tien_format = "{:,.0f}".format(ca.dm_ca_id.tien).replace(',', '.') if ca.dm_ca_id.tien else False

                values = {
                    'tu': ca.tu,
                    'den': ca.den,
                    'ca': ca.dm_ca_id.name,
                    # Đổi chữ 'tien' thành 'gia' để khớp 100% với file XML
                    'gia': tien_format,
                    'trangthai':'Đã học'
                }

                if ca.giaovien_id:
                    values['giaovien'] = ca.giaovien_id.name

                data.append(values)

        return data


    def func_get_ngay_trong_tuan(self):
        """
        Hàm trả về danh sách 7 ngày của tuần hiện tại (Từ Thứ 2 đến Chủ Nhật).
        Đồng thời đánh dấu ngày nào là hôm nay.
        """
        # Lấy ngày hôm nay
        today = date.today()

        # weekday() trả về từ 0 (Thứ 2) đến 6 (Chủ Nhật)
        # Lấy ngày bắt đầu của tuần (Thứ 2) bằng cách trừ đi số ngày tương ứng với weekday()
        ngay_dau_tuan = today - timedelta(days=today.weekday())

        # Danh sách mapping tên thứ bằng Tiếng Việt
        weeks = [
            "T2", "T3", "T4", "T5",
            "T6", "T7", "CN"
        ]

        data = []

        # Duyệt qua 7 ngày trong tuần
        for i in range(7):
            ngay_hien_tai = ngay_dau_tuan + timedelta(days=i)
            la_hom_nay = (ngay_hien_tai == today)

            values = {
                "week": weeks[i],
            }

            if la_hom_nay == True:
                values['date'] = "Hôm nay"
            else:
                values['date'] = ngay_hien_tai.strftime("%d/%m/%Y")
            data.append(values)

        return data


