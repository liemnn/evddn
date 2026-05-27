from odoo import models, fields, api, exceptions


class KeHoach(models.Model):
    _name = "ekids.kehoach"
    _description = "Kế hoạch"

    coso_id = fields.Many2one("ekids.coso", related="chuongtrinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="restrict",index=True)

    trangthai = fields.Selection([
        ("0", "Không có kế hoạch"),
        ("1", "Đang can thiệp"),
        ("2", "Kế hoạch đang lập"),

    ]
        , string="Kế hoạch học sinh", default="0", required=True)

    tiendo = fields.Integer(string="Tiến độ hoàn thành")

