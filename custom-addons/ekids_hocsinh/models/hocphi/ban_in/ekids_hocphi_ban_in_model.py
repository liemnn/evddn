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




class HocPhiBanIn(models.TransientModel):
    _name = 'ekids.hocphi_banin'
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

        table_data = [['TT','Học sinh', 'Học phí(vnđ)'
                          ,'Phụ huynh ký xác nhận','Ghi chú'
                          ]]  # Header
        thang =self.thang
        nam =self.nam


        hocphis = self.env['ekids.hocphi'].search(
            [('coso_id', '=', self.coso_id.id)
                , ('thang_id.name', '=', str(thang))
                , ('nam_id.name', '=', str(nam))

             ])
        if hocphis:
            index =1
            for hocphi in hocphis:
                table_data = self.get_table_data_by_hocphi(table_data,index,hocphi)
                index =index +1
        return table_data



    #Tinh toán tháng

    def get_table_data_by_hocphi(self,table_data,index,hocphi):
        tien =string_util.number2string(hocphi.hocphi_phaidong)
        table_data.append([
            str(index),
            hocphi.hocsinh_id.name,
            tien,
            " ",
            " "
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
        return (self.env.ref('ekids_hocsinh.action_hocphi_banin_report')
                .report_action(self, data=data))


