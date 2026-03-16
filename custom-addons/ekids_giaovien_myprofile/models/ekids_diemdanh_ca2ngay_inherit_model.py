from reportlab.graphics.barcode.qr import isLevel

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar


class DiemDanhCa2NgayInherit(models.Model):
    _inherit= "ekids.diemdanh_ca2ngay"



    def func_xacnhan_hoc(self):
        self.trangthai ='1'
        self.func_xacnhan_chamcong_giaovien2ngay()

    def func_xacnhan_nghi(self):
        self.trangthai ='-1'
        self.func_xacnhan_chamcong_giaovien2ngay()

    def func_xacnhan_chamcong_giaovien2ngay(self):
        diemdanh_ca2ngays = self.env['ekids.diemdanh_ca2ngay'].search([
            ('giaovien_id', '=', self.giaovien_id.id),
            ('ngay', '=', self.ngay),
        ])
        if diemdanh_ca2ngays:
            is_hoanthanh =True
            for diemdanh_ca2ngay in diemdanh_ca2ngays:
                if diemdanh_ca2ngay == '0':
                    is_hoanthanh =False
            if is_hoanthanh == True:
                chamcong_giaovien2ngay = self.env['ekids.chamcong_giaovien2ngay'].search([
                    ('giaovien_id', '=', self.giaovien_id.id),
                    ('ngay', '=', self.ngay),
                ])
                if chamcong_giaovien2ngay:
                    setattr(chamcong_giaovien2ngay,'trangthai','1')
