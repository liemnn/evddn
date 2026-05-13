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

    tu_ngay = fields.Date(
        string="Từ ngày",
        default=lambda self: fields.Date.context_today(self).replace(day=1)
    )

    den_ngay = fields.Date(
        string="Đến ngày",
        default=lambda self: fields.Date.context_today(self) + relativedelta(day=31)
    )


    dm_chi_ids = fields.One2many("ekids.chitieu_dm_loaichi",
                              "coso_id", string="Chi tiêu của cơ sở")

    def get_table_data(self):

        table_data = [['TT','Ngày'
                          ,'Số tiền (vnđ)'
                          ,'Loại chi'
                          ,'Mô tả'
                          ,'Người chi'
                          ,'Ngày ghi nhận'
                          ]]  # Header

        datas = self.get_danhsach_chi_theo_thoigian()
        if datas:
            index=1
            for data in datas:
                self.get_table_data_by_chi(table_data,index,data)
                index =index+1

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


    def get_danhsach_chi_theo_thoigian(self):
        domain =[
            ('coso_id','=',self.coso_id.id)
            ,('ngaychi','>=',self.tu_ngay)
            ,('ngaychi', '<=', self.den_ngay)

        ]
        if self.dm_chi_ids and len(self.dm_chi_ids)>0:
            domain.append([('dm_loaichi_id', 'in', self.dm_chi_ids.ids)])

        result = self.env['ekids.chitieu_chi'].search(domain)
        return result






    #Tinh toán tổng của năm

    def get_table_data_by_nam(self,table_data):
        hocphi = 0
        thukhac = 0
        luong = 0
        thuho = 0
        chikhac = 0
        loinhuan=0

        if table_data:
            i=0
            for data in table_data:
                if i == 0:
                    i =i+1
                    continue
                hocphi += string_util.string2number(data[2])
                thukhac +=  string_util.string2number(data[3])
                luong += string_util.string2number(data[4])
                thuho += string_util.string2number(data[5])
                chikhac +=  string_util.string2number(data[6])
                loinhuan += string_util.string2number(data[7])
                i = i+1



        table_data.append([
            'TỔNG THEO NĂM TÀI CHÍNH','',
            string_util.number2string(hocphi),
            string_util.number2string(thukhac),
            string_util.number2string(luong),
            string_util.number2string(thuho),
            string_util.number2string(chikhac),
            string_util.number2string(loinhuan)
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


