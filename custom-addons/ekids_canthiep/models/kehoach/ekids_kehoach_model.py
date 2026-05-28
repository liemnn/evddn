from odoo import models, fields, api, exceptions


class KeHoach(models.Model):
    _name = "ekids.kehoach"
    _description = "Kế hoạch"

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="restrict")
    ketluan_id = fields.Many2one("ekids.kehoach_ketluan", string="Kết luận", required=True, ondelete="restrict")

    tu_ngay = fields.Date(string="Từ ngày", required=True)
    den_ngay = fields.Date(string="Đến ngày", required=True)
    songay = fields.Integer(string="Số ngày")

    trangthai = fields.Selection([
        ("0", "Đang lập kế hoạch"),
        ("1", "Đang can thiệp"),
        ("2", "Kế hoạch đã phê duyệt"),
        ("-1", "Kế hoạch hết hiệu lực"),
        ("-2", "Kế hoạch cần chỉnh sửa"),


    ]
        , string="Kế hoạch", default="0", required=True)



