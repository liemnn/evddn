import logging
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)
class GiaoVienNghiPhep(models.Model):
    _name = "ekids.giaovien_nghiphep"
    _description = "Nghỉ phép của giáo viên"
    _order = 'tu_ngay desc'


    coso_id = fields.Many2one("ekids.coso",string="Cơ sở",related="giaovien_id.coso_id", store=True)
    giaovien_id = fields.Many2one("ekids.giaovien", string="Giáo viên",required=True, ondelete="restrict")

    tu_ngay = fields.Date(string="Nghỉ từ ngày",required=True)
    den_ngay = fields.Date(string="Nghỉ đến ngày",required=True)
    desc = fields.Html(string="Lý do nghỉ")
    loai = fields.Selection([("0","Nghỉ tính vào phép (không trừ lương)")
                                     , ("1","Nghỉ (bị trừ lương)")
                                    , ("2", "Nghỉ hưởng BHXH (Ốm,đẻ...)")

                                     ], default="1")

    @api.constrains('tu_ngay', 'den_ngay')
    def _constrains_nghiLe(self):
        for rec in self:
            if rec.tu_ngay > rec.den_ngay:
                raise ValidationError("Chọn [Ngày bắt đầu] phải nhỏ hơn [Ngày kết thúc]")

