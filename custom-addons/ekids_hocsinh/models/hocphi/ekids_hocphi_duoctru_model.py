from odoo import api, fields, models
from datetime import datetime
import calendar

class HocPhiDuocTru(models.Model):
    _name = 'ekids.hocphi_duoctru'
    _description = 'Học phí được trừ khi nghỉ'
    # Khai báo các trường dữ liệu

    hocphi_id = fields.Many2one('ekids.hocphi', string="Học phí",required=True,ondelete="cascade")
    name = fields.Char("Nội dung được trừ",required=True)
    tien = fields.Float('Số tiền(vnđ)', digits=(10, 0),required=True)

