from odoo import models, fields, api, exceptions


class DanhMucMucDo(models.Model):
    _name = "ekids.ct_dm_mucdo"
    _description = "Mức độ"

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True,ondelete="restrict")

    name = fields.Char(string="Tên",required=True)
    desc =fields.Html(string="Mô tả")
    trangthai = fields.Selection([("0", "Không hoạt động")
    , ("1", "Đang hoạt động")], default="1", required=True)

