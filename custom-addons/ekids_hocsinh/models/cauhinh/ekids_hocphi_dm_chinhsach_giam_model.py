from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DanhMucChinhSachGiamHocPhi(models.Model):
    _name = "ekids.hocphi_dm_chinhsach_giam"
    _description = "Chính sách giảm học phí"
    _order = "sequence desc"

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    name = fields.Char(string="Tên chính sách giảm ",required=True)

    is_giam_theo_tyle = fields.Boolean(string="Giảm theo tỷ lệ % khi bật, theo số tiền khi tăt", default=True)
    tyle_giam = fields.Integer(string="Tỷ lệ % giảm học phí", default=0)

    tien = fields.Float(string='Số tiền(vnđ)', digits=(10, 0))

    desc = fields.Html(string="Mô tả")
    trangthai = fields.Selection([("0", "Không hoạt động")
                                     , ("1", "Đang hoạt động")], default="1", required=True)

    hocsinh_ids = fields.Many2many(
        comodel_name="ekids.hocsinh",
        relation="ekids_hocphi_chinhsach_hocsinh_rel",  # Chung bảng trung gian
        column1="chinhsach_id",  # Cột trỏ về chính model này
        column2="hocsinh_id",  # Cột trỏ về model học sinh
        string="Các Học sinh đang áp dụng",
    )




