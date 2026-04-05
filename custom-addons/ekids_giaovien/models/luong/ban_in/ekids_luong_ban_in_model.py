from odoo import models, fields, api
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
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




class LuongBanIn(models.TransientModel):
    _name = 'ekids.luong_banin'
    _description = 'Bản In học phí'

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", readonly=True)

    thang = fields.Selection(
        [('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng',
        required=True,
        default='1'

    )

    nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 5, datetime.now().year + 1)],
        string="Năm",
        required=True,
        default=lambda self: str(date.today().year)
    )


    def get_table_data(self):

        table_data = [['TT'
                        ,'Giáo viên'
                        ,'Thâm niên'
                        ,'Công'
                        ,'Nghỉ'
                        ,'1.Được (+)'
                        ,'2.Bị(-)'
                        ,'3.Thông tin'
                        ,'4.Nhà trường đóng'
                        ,'5.Lương=1-2'
                        ,'6.Nhà trường thực chi=4+5'

                          ]]  # Header
        thang =self.thang
        nam =self.nam


        luongs = self.env['ekids.luong'].search(
            [('coso_id', '=', self.coso_id.id)
                , ('thang_id.name', '=', str(thang))
                , ('nam_id.name', '=', str(nam))

             ])
        if luongs:
            index =1
            nhatruong_thuho=0
            tong_thongtin=0
            tien_luong=0
            tong_nhatruong_chi=0

            for luong in luongs:
                table_data = self.get_table_data_by_luong(table_data,index,luong)
                index =index +1
                #tinh tong
                nhatruong_thuho += luong.nhatruong_thuho
                tong_thongtin += luong.tong_thongtin
                tien_luong += luong.luong
                tong_nhatruong_chi += luong.tong_nhatruong_chi
            #bang tong
            table_data.append([
                '',
                'Tổng',
                '',
                '',
                '',
                '',
                '',
                string_util.number2string(nhatruong_thuho),
                string_util.number2string(tong_thongtin),
                string_util.number2string(tien_luong),
                string_util.number2string(tong_nhatruong_chi)

            ])

        return table_data



    #Tinh toán tháng

    def get_table_data_by_luong(self,table_data,index,luong):
        tham_nien = luong.tham_nien
        ngaycong = luong.ngaycong
        so_ngaynghi = luong.so_ngaynghi
        tong_cong =string_util.number2string(luong.tong_cong)
        tong_tru = string_util.number2string(luong.tong_tru)
        nhatruong_thuho =string_util.number2string(luong.nhatruong_thuho)
        tong_thongtin =string_util.number2string(luong.tong_thongtin)
        tien_luong = string_util.number2string(luong.luong)
        tong_nhatruong_chi = string_util.number2string(luong.tong_nhatruong_chi)

        table_data.append([
            str(index),
            luong.giaovien_id.name,
            str(tham_nien),
            str(ngaycong),
            str(so_ngaynghi),
            tong_cong,
            tong_tru,
            nhatruong_thuho,
            tong_thongtin,
            tien_luong,
            tong_nhatruong_chi

        ])
        return table_data



    def action_xem_banin(self):
        today = date.today()
        formatted = today.strftime("Vào hồi %H:%M  ngày %d/%m/%Y")
        data = {
            'coso': self.coso_id.fullname,
            'thoigian':formatted,
            'nam': self.nam,
            'thang': self.thang,
            'table_data': self.get_table_data()

        }
        return (self.env.ref('ekids_giaovien.action_luong_banin_report')
                .report_action(self, data=data))


