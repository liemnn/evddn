from odoo import api, fields, models
from datetime import datetime
import calendar

class LuongHangMuc(models.Model):
    _name = 'ekids.luong_hangmuc'
    _description = 'Luong Giáo viên'

    # Khai báo các trường dữ liệu
    sequence = fields.Integer(string="STT", default=1)
    luong_id = fields.Many2one('ekids.luong', string="Lương",ondelete="cascade")
    name = fields.Char(string="Mục lương (+)",required=True)
    desc = fields.Text(string="Mô tả")
    tien = fields.Float('Số tiền(vnđ)', digits=(10, 0),required=True)
    sukien_id = fields.Many2one('ekids.luong_sukien', string='Khoản lương sự kiện', ondelete="restrict")
    loai = fields.Selection(
        [("1", "Được cộng tiền"),
         ("-1", "Bị trừ tiền (giáo viên phải nộp)"),
         ("-2", "Bị trừ tiền (nhà trường thu hộ)"),
         ("0", "Nhà trường chi trả"),
         ("2", "Thông tin"),
         ], string="Khoản",required=True)




