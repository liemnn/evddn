from odoo import api, fields, models
from datetime import datetime
import calendar
from odoo.exceptions import ValidationError

class LuongDMChamCongKPI(models.Model):
    _name = "ekids.luong_dm_chamcong_kpi"
    _description = "Định nghĩa danh mục điểm danh chấm công Kpi"

    sequence = fields.Integer(string="TT", required=True, default=1)
    dm_chamcong_id = fields.Many2one("ekids.luong_dm_chamcong", string="KPI", required=True, ondelete="cascade")
    code = fields.Char(string="Mã", required=True)
    name =fields.Char(string="Tên",required=True)
    donvi = fields.Char(string="Đơn vị", required=True)
    is_tyle_phantram = fields.Boolean(string="Giá trị là tỷ lệ %", default=False)
