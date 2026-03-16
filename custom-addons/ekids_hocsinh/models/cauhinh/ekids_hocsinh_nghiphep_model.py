import logging
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)
class HocSinhNghiPhep(models.Model):
    _name = "ekids.hocsinh_nghiphep"
    _description = "Nghỉ phép của học sinh"
    _order = 'tu_ngay desc'

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="cascade")
    tu_ngay = fields.Date(string="Nghỉ từ ngày",required=True)
    den_ngay = fields.Date(string="Nghỉ đến ngày",required=True)
    desc = fields.Html(string="Lý do nghỉ")
    is_hoantra_hocphi = fields.Boolean(string="Cho phép thiết lập % hoàn trả [Học phí] riêng",default=False)
    tyle_hoantra_hocphi = fields.Integer(string="Tỷ lệ % sẽ được hoàn trả [Học phí] tháng tơi", default=0)

    @api.constrains('tu_ngay', 'den_ngay')
    def _constrains_nghiLe(self):
        for rec in self:
            if rec.tu_ngay > rec.den_ngay:
                raise ValidationError("Chọn [Ngày bắt đầu] phải nhỏ hơn [Ngày kết thúc]")
