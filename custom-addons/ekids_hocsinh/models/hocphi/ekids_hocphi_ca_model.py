from odoo import api, fields, models
from datetime import datetime
import calendar

class HocPhiCa(models.Model):
    _name = 'ekids.hocphi_ca'
    _description = 'Học phí theo ca can thiệp'
    # Khai báo các trường dữ liệu

    hocphi_id = fields.Many2one('ekids.hocphi', string="Học phí", required=True,ondelete="cascade")
    soca = fields.Integer('Số ca/tháng', required=True)
    dm_ca_id = fields.Many2one('ekids.hocphi_dm_ca', string="Loại ca can thiệp", required=True,ondelete="cascade")
    tien = fields.Float('Thành tiền (vnđ)', digits=(10, 0), required=True)
    desc = fields.Char(string="Ghi chú")

    @api.onchange('soca','dm_ca_id')
    def compute_hocphi_ca_tien(self):
        for ca in self:
            ca.tien = ca.soca * ca.dm_ca_id.tien