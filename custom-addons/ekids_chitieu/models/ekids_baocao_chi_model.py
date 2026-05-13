from odoo import models, fields, api
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import html2plaintext

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



class BaoCaoChiWizard(models.TransientModel):
    _name = 'ekids.chitieu_baocao_chi'
    _description = 'Báo cáo chi của nội dung'

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", readonly=True)

    loai = fields.Selection([("0", "Chi"), ("1", "Thu khác (ngoài học phí)")], string="Phân loại", required=True,
                            default="0")

    loai_baocao = fields.Selection([("0", "Tổng hợp theo [Hạng mục]")
                                       , ("1", "Chi tiết các khoản chi")], string="Phân loại", required=True,
                            default="0")

    tu_ngay = fields.Date(
        string="Từ ngày",
        default=lambda self: fields.Date.context_today(self).replace(day=1)
    )

    den_ngay = fields.Date(
        string="Đến ngày",
        default=lambda self: fields.Date.context_today(self)
    )


    dm_chi_ids = fields.Many2many("ekids.chitieu_dm_loaichi", string="Danh mục chi cần lọc")

    def get_table_data(self):
        table_data = [[]]

        if self.loai_baocao == '1':
            table_data = [['TT', 'Ngày'
                              , 'Số tiền (vnđ)'
                              , 'Loại chi'
                              , 'Mô tả'
                              , 'Người chi'
                              , 'Ngày ghi nhận'
                           ]]  # Header
            datas = self.get_danhsach_chi_theo_thoigian()
            if datas:
                index=1
                for data in datas:
                    self.get_table_data_by_chi(table_data,index,data)
                    index =index+1

            table_data = self.get_table_data_tong(table_data)
        else:
            table_data = [['TT', 'Loại chi'
                              , 'Tổng tiền (vnđ)'
                           ]]  # Header

            datas = self.get_danhsach_dm_loaichi()
            if datas:
                index = 1
                for data in datas:
                    self.get_table_data_by_loaichi(table_data, index, data)
                    index = index + 1



        return table_data



    #Tinh toán tháng

    def get_table_data_by_chi(self,table_data,index,data):
        mota_sach = html2plaintext(data.desc) if data.desc else ''
        table_data.append([
            str(index),
            string_util.date2string(data.ngaychi),
            string_util.number2string(data.tien),
            data.dm_loaichi_id.name,
            mota_sach,
            data.create_uid.name,
            string_util.date2string_format(data.create_date,"%H:%M %d/%m/%Y"),


        ])

        return table_data

    def get_table_data_by_loaichi(self, table_data, index, data):
        tien =self.sum_tien_theo_loaichi(data.id)
        table_data.append([
            str(index),
            data.name,
            string_util.number2string(tien),

        ])

        return table_data

    def sum_tien_theo_loaichi(self, dm_loaichi_id):
       # 1. Xây dựng bộ lọc (Domain) cơ bản (Bắt buộc phải có Cơ sở và Khoảng thời gian)
        domain = [
            ('coso_id', '=', self.coso_id.id),
            ('ngaychi', '>=', self.tu_ngay),
            ('ngaychi', '<=', self.den_ngay),
        ]

        # 2. Nếu người dùng có chọn cụ thể Loại chi, thì nhồi thêm điều kiện vào Domain
        if dm_loaichi_id:
            domain.append(('dm_loaichi_id', '=', dm_loaichi_id))

        # 3. Tính tổng (Dùng phương pháp Query trực tiếp xuống DB để đạt tốc độ cao nhất)
        # Hàm read_group của Odoo tương đương với lệnh: SELECT SUM(tien) FROM ekids_chitieu_chi WHERE ...
        ket_qua = self.env['ekids.chitieu_chi'].read_group(
            domain=domain,
            fields=['tien'],
            groupby=[]  # Không group by, gộp chung tất cả thành 1 cục
        )

        # 4. Trả kết quả về an toàn (Nếu không có dữ liệu thì trả về 0.0)
        if ket_qua and ket_qua[0].get('tien'):
            return ket_qua[0]['tien']

        return 0.0

    def get_danhsach_chi_theo_thoigian(self):
        domain =[
            ('coso_id','=',self.coso_id.id)
            ,('ngaychi','>=',self.tu_ngay)
            ,('ngaychi', '<=', self.den_ngay)

        ]
        if self.dm_chi_ids and len(self.dm_chi_ids)>0:
            domain.append(('dm_loaichi_id', 'in', self.dm_chi_ids.ids))

        result = self.env['ekids.chitieu_chi'].search(domain)
        return result

    def get_danhsach_dm_loaichi(self):
        if self.dm_chi_ids:
            return self.dm_chi_ids
        else:
            domain =[
                ('coso_id','=',self.coso_id.id)
                ,('trangthai','=','1')


            ]
            result = self.env['ekids.chitieu_dm_loaichi'].search(domain)
            return result








    #Tinh toán tổng của năm

    def get_table_data_tong(self,table_data):
        tong =0

        if table_data:
            i=0
            for data in table_data:
                if i == 0:
                    i =i+1
                    continue
                tong += string_util.string2number(data[2])
                i = i+1



        table_data.append([
            '','Tổng',
            string_util.number2string(tong),
            '', '','', ''
        ])
        return table_data

    def action_xem_baocao(self):
        # Lấy ngày giờ hiện tại chuẩn theo múi giờ của người dùng thao tác
        current_time = fields.Datetime.context_timestamp(self, fields.Datetime.now())

        # Định dạng lại chuỗi
        formatted = current_time.strftime("Vào hồi %H:%M ngày %d/%m/%Y")

        data = {
            'coso': self.coso_id.fullname,
            'thoigian': formatted,
            'tu_ngay': string_util.date2string(self.tu_ngay),
            'den_ngay': string_util.date2string(self.den_ngay),
            'table_data': self.get_table_data()
        }
        return (self.env.ref('ekids_chitieu.action_baocao_chi_view')
                .report_action(self, data=data))


