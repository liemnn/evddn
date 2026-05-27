from odoo import models, fields, api, exceptions


class KeHoach(models.Model):
    _name = "ekids.kehoach"
    _description = "Kế hoạch"

    coso_id = fields.Many2one("ekids.coso", related="chuongtrinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="restrict",index=True)

    tu_ngay = fields.Date(string="Từ ngày", required=True)
    den_ngay = fields.Date(string="Đến ngày", required=True)
    songay = fields.Integer(string="Số ngày")

    trangthai = fields.Selection([
        ("0", "Đang lập"),
        ("-1", "Yêu cầu chỉnh sửa"),
        ("1", "Đang can thiệp"),
        ("2", "Đã được phê duyệt")

    ]
        , string="Kế hoạch", default="0", required=True)



