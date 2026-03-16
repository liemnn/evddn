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


class BaoCaoNguonLucWizard(models.TransientModel):
    _name = 'ekids.baocao_nguonluc'
    _description = 'Báo cáo lợi nhuận của cơ sở'

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", readonly=True)

    tu_thang = fields.Selection(
        [('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng',
        required=True,
        default='1'

    )

    tu_nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 5, datetime.now().year + 1)],
        string="Năm",
        required=True,
        default=lambda self: str(date.today().year)
    )

    den_thang = fields.Selection(
        [('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng',
        required=True,
        default='1'
    )

    den_nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 5, datetime.now().year + 2)],
        string="Năm",
        required=True,
        default=lambda self: str(date.today().year +1)
        )


    def get_table_data(self):

        table_data = [['Tháng','Năm'
                          ,'[1] Tổng Học sinh'
                          ,'Nghỉ trong tháng'
                          ,'Mới trong tháng'
                          ,'[2] Tổng Giáo viên'
                          ]]  # Header
        tu_thang =self.tu_thang
        tu_nam =self.tu_nam
        den_thang = self.den_thang
        den_nam = self.den_nam
        ngay_first = date(int(tu_nam),int(tu_thang),1)
        ngay_last = date(int(den_nam), int(den_thang), 1)

        ngay =ngay_first
        sum={
            'tong':0,
            'nghi':0,
            'moi':0
        }
        while ngay <= ngay_last:
            table_data =self.get_table_data_by_thang(table_data, ngay.year,ngay.month,sum)
            ngay = ngay + relativedelta(months=1)

        # cho tổng 1 nam
        table_data.append([
            'Tổng',
            '',
            self.number2string(sum['tong']),
            self.number2string(sum['nghi']),
            self.number2string(sum['moi']),
            '',
        ])


        return table_data



    #Tinh toán tháng

    def get_table_data_by_thang(self,table_data,nam,thang,sum):
        tong_hs = self.sum_tong_hocsinh_trong_thang(nam,thang)
        hs_nghi = self.sum_tong_hocsinh_nghỉ_trong_thang(nam, thang)
        hs_moi = self.sum_tong_hocsinh_moi_trong_thang(nam, thang)
        giaovien = self.sum_tong_giaovien_trong_thang(nam, thang)


        table_data.append([
            'Tháng '+str(thang),
            str(nam),
            self.number2string(tong_hs),
            self.number2string(hs_nghi),
            self.number2string(hs_moi),
            self.number2string(giaovien),
        ])
        if sum['tong']<=0:
            sum['tong']=tong_hs
        sum['tong'] =int (sum['tong'])+hs_moi -hs_nghi
        sum['nghi'] = int(sum['nghi']) + hs_nghi
        sum['moi'] = int(sum['moi']) + hs_moi

        return table_data




    def sum_tong_hocsinh_trong_thang(self,nam,thang):
        count = self.env['ekids.hocphi'].search_count([
                                    ('coso_id','=',self.coso_id.id)
                                    ,('nam_id.name', '=', str(nam))
                                    ,('thang_id.name', '=', str(thang))
                                    ])
        return  count
    def sum_tong_hocsinh_nghỉ_trong_thang(self,nam,thang):
        days = ngay_util.func_get_cacngay_trong_thang(nam, thang)
        ngay_dauthang = days[0]
        ngay_cuoithang = days[len(days) - 1]

        count = self.env['ekids.hocphi'].search_count([
                                    ('coso_id','=',self.coso_id.id)
                                    ,('hocsinh_id.ngay_nghihoc', '>=', ngay_dauthang)
                                    ,('hocsinh_id.ngay_nghihoc', '<=', ngay_cuoithang)
                                    ]
                                    )
        return count

    def sum_tong_hocsinh_moi_trong_thang(self,nam,thang):
        days = ngay_util.func_get_cacngay_trong_thang(nam, thang)
        ngay_dauthang = days[0]
        ngay_cuoithang = days[len(days) - 1]
        count = self.env['ekids.hocphi'].search_count([
            ('coso_id', '=', self.coso_id.id)
            , ('hocsinh_id.ngay_nhaphoc', '>=', ngay_dauthang)
            , ('hocsinh_id.ngay_nhaphoc', '<=', ngay_cuoithang)
        ])
        return count


    def sum_tong_giaovien_trong_thang(self,nam,thang):
        luong_thang = self.env['ekids.luong_thang'].search([
            ('coso_id', '=', self.coso_id.id)
            , ('nam_id.name', '=', str(nam))
            , ('name', '=', str(thang))
        ], limit=1)
        if luong_thang:
            return luong_thang.tong_giaovien
        else:
            return 0

    #Tinh toán tổng của năm







    def action_xem_baocao(self):
        data = {
            'nam': self.tu_nam,
            'table_data': self.get_table_data()

        }
        return (self.env.ref('ekids_baocao.action_report_view_nguonluc')
                .report_action(self, data=data))


    def number2string(self,total):
        total = "{:,.0f}".format(total)
        return total

    def string2number(self, s):
        if not s:
            return 0
        # bỏ dấu phẩy ngăn cách hàng nghìn
        s = s.replace(",", "").strip()
        return float(s)