from odoo import api, fields, models
from datetime import datetime
import calendar

class HocPhiBanTru(models.Model):
    _name = 'ekids.hocphi_bantru'
    _description = 'Học phí bán trú'
    # Khai báo các trường dữ liệu
    name = fields.Char(string="Tên khoản thu")
    hocphi_id = fields.Many2one('ekids.hocphi', string="Học phí",required=True,ondelete="cascade")
    thungoai_id = fields.Many2one('ekids.hocphi_thungoai', string='Khoản thu', ondelete="cascade")
    dm_thu_bantru_id = fields.Many2one('ekids.hocphi_dm_thu_bantru', string="Danh mục thu học phi", required=False, ondelete="cascade")
    tien = fields.Float('Số tiền(vnđ)', digits=(10, 0), required=True)






