from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class GiaoVienHocTapCongTac(models.Model):
    _name = "ekids.giaovien_hoctapcongtac"
    _description = "Quá trình học tập công tác"


    sequence = fields.Integer(string="Thứ tự", default=1)
    giaovien_id = fields.Many2one('ekids.giaovien', string="Giáo viên",required=True)
    tu_ngay = fields.Date(string="Nghỉ từ ngày", required=True)
    den_ngay = fields.Date(string="Nghỉ đến ngày")
    name = fields.Char(string="Nơi học tập/làm việc",required=True)
    chucvu = fields.Char(string="Bằng cấp/Chức vụ", required=True)
    thanhtich = fields.Char(string="Thành tích đạt được (nếu có)")


