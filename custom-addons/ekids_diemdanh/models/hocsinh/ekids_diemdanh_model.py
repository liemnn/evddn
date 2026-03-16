from odoo import models, fields, api, _

from odoo.exceptions import UserError
from datetime import datetime,date,timedelta

from odoo.exceptions import ValidationError
import calendar
import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")



class DiemDanh(models.Model):
    _name = "ekids.diemdanh"
    _description = "Điểm danh học sinh theo học"
    _order = "id desc,nam desc ,thang desc"

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True)
    name = fields.Char(string="Tên hiển thị", compute="_compute_diemdanh_name", readonly=True)
    thang = fields.Selection(
        [('1', 'Tháng 1'),('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng',
        required=True,
        default = lambda self: str(date.today().month))
    nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 10, datetime.now().year + 5)]
        , string="Năm",required=True,
        default=lambda self: str(date.today().year))

    hocsinh2thang_ids = fields.One2many("ekids.diemdanh_hocsinh2thang",
                                    "diemdanh_id", string="Thuộc Tháng đểm danh")





    def _compute_diemdanh_name(self):
        for e in self:
            name =""
            if e.thang:
                name += e.thang
            if e.nam:
                name += '/'+e.nam
            e.name =name





    def action_xem_diemdanh_hocsinh2thang(self):
        # điểm danh đã được tạo
        self.func_tao_macdinh_diemdanh_hocsinh2thang()
        name ='THÁNG '+self.thang +"/" + self.nam
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'ekids.diemdanh_hocsinh2thang',
            'view_mode': 'list',
            'target': 'current',
            'domain': [
                ('coso_id', '=', self.coso_id.id),
                ('diemdanh_id', '=', self.id),
            ],

            'context': {
                'default_coso_id': self.coso_id.id,
                'default_diemdanh_id': self.id,
                'default_thang': self.thang,
                'default_nam': self.nam

            }
        }




    def func_tao_macdinh_diemdanh_hocsinh2thang(self):
        # b1: tìm tất cả học sinh học trong tháng này
        days = ngay_util.func_get_cacngay_trong_thang(int(self.nam), int(self.thang))
        ngay_dauthang = days[0]
        ngay_cuoithang = days[len(days) - 1]
        nam = ngay_cuoithang.year
        thang = ngay_cuoithang.month

        hocsinhs = hocsinh_util.func_get_hocsinhs_trong_thang(self, self.coso_id.id, nam, thang)

        hocsinh2thangs = self.env['ekids.diemdanh_hocsinh2thang'].search(
            [
                ('coso_id', '=', self.coso_id.id),
                ('diemdanh_id', '=', self.id)

            ])
        hocsinh2_ids = hocsinh2thangs.mapped('hocsinh_id.id')
        if hocsinhs:
            nghiles = nghile_util.func_get_nghiles_trong_khoang_thoigian(self,self.coso_id,None, ngay_dauthang,ngay_cuoithang)
            coso_hoatdongs = coso_util.func_get_ngay_hoatdongs(self.coso_id, nam, thang)
            nghipheps = hocsinh_util.func_get_nghipheps_tatca_hocsinh(self,self.coso_id, nam, thang)
            diemdanh_thangtruoc =self.func_get_diemdanh_theo_thang()
            ca_tangcuongs = hocsinh_util.func_get_cas_tangcuong_tatca_hocsinh(self, self.coso_id,nam,thang)
            for hs in hocsinhs:
                 if hs.id not in hocsinh2_ids:
                    data = {
                        'coso_id': self.coso_id.id,
                        'diemdanh_id': self.id,
                        'hocsinh_id': hs.id,

                    }
                    hocsinh2thang = self.env['ekids.diemdanh_hocsinh2thang'].create(data)
                    hocsinh2thang.func_tinhtoan_giatri_hocsinh2ngay(nghiles, coso_hoatdongs, nghipheps,ca_tangcuongs,True)
                    #job queue để tính toán ngay nghi le thang truoc
                    hocsinh2thang.func_tinhtoan_hocbu_cho_hocsinh2thang_khoitao(diemdanh_thangtruoc)
                 else:
                     # tinh toan lại các du lieu đã có chấp nhận for lai
                     for hocsinh2thang in hocsinh2thangs:
                         if hocsinh2thang.hocsinh_id.id == hs.id:
                             hocsinh2thang.func_tinhtoan_giatri_hocsinh2ngay(nghiles, coso_hoatdongs, nghipheps,ca_tangcuongs,False)





    def func_thuchien_diemdanh_theo_ngay(self, ngay, hs_vangs):
        diemdanhs = self.env['ekids.diemdanh_hocsinh2thang'].search(
                    [
                        ('coso_id', '=', self.coso_id.id),
                        ('diemdanh_id', '=', self.id)

                    ])
        if diemdanhs:
            for hs_diemdanh in diemdanhs:
                field_name = f'd{ngay}'
                hocsinh_id =hs_diemdanh.hocsinh_id
                if hs_vangs and hocsinh_id in hs_vangs:
                    setattr(hs_diemdanh, field_name, False)
                else:
                    setattr(hs_diemdanh, field_name, True)

    def func_get_diemdanh_theo_thang(self):
        nam = self.nam
        thang = self.thang
        ngay_dauthang = date(int(nam), int(thang), 1)
        ngay_dauthang_truoc = ngay = ngay_dauthang - timedelta(days=1)

        diemdanh = self.env['ekids.diemdanh'].search(
                    [
                        ('coso_id', '=', self.coso_id.id),
                        ('thang', '=',str(ngay_dauthang_truoc.month)),
                        ('nam', '=', str(ngay_dauthang_truoc.year)),

                    ],limit=1)
        return  diemdanh










