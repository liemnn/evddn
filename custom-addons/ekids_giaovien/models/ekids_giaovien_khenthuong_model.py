from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class GiaoVienKhenThuong(models.Model):
    _name = "ekids.giaovien_khenthuong"
    _description = "Đối tượng giáo viên của cơ sở"

    coso_id = fields.Many2one("ekids.coso", related="giaovien_id.coso_id", store=True)

    sequence = fields.Integer(string="Thứ tự", default=1)
    giaovien_id = fields.Many2one('ekids.giaovien', string="Giáo viên",required=True)
    name = fields.Char(string="Tên [Thành tích /Kỷ luật]",required=True)
    nam = fields.Selection([(str(year), str(year))
                             for year in range(datetime.now().year - 20,
                                               datetime.now().year + 1)], string="Năm", required=True)
    loai = fields.Selection([
        ("0", "Kỷ luật"),
        ("1", "Khen thưởng")
    ], 'Loại hình', required=True)
    desc = fields.Html(string="Mô tả")
