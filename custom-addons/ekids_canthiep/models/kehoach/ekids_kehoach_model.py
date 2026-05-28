from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoach(models.Model):
    _name = 'ekids.kehoach'
    _description = 'Kết luận Đánh giá & Định hướng Kế hoạch'
    _order = 'id desc'

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    name = fields.Char(string="Mã phiếu", required=True, default='Mới')

    # 1. THÔNG TIN HỌC SINH
    hocsinh_id = fields.Many2one('ekids.hocsinh', string="Họ và tên", required=True, tracking=True)  # [cite: 2]

    # 2. CHẨN ĐOÁN & MỨC ĐỘ

    trangthai = fields.Selection([
        ("00", "Kết luận đợi lập kế hoạch"),
        ("01", "Đang lập kế hoạch"),
        ("1", "Đang can thiệp"),
        ("02", "Kế hoạch đã phê duyệt"),
        ("-1", "Kế hoạch hết hiệu lực"),
        ("03", "Kế hoạch cần chỉnh sửa"),

    ], string="Trạng thái",default="00")


    tu_ngay = fields.Date(string="Từ ngày")
    den_ngay = fields.Date(string="Đến ngày")
    songay = fields.Integer(string="Số ngày")

    muctieu_ids = fields.One2many("ekids.kehoach_muctieu",
                                  "kehoach_id", string="Mục tiêu")

