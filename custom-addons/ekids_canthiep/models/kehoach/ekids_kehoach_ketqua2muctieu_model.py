from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoachKetQua2MucTieu(models.Model):
    _name = 'ekids.kehoach_ketqua2muctieu'
    _description = 'Kết quả thực hiện can thiệp'
    _order = 'id desc'



    kehoach_muctieu_id = fields.Many2one("ekids.kehoach_muctieu",
                                 string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")

    ngay = fields.Date(string="Ngày",required=True)

    ketqua = fields.Selection([
        ("1", "Đạt (+)"),
        ("-1", "Chưa đạt (-)"),
        ("0", "Đang hình thành (+/-)"),


    ], string="Trạng thái",required=True)

    desc = fields.Html(string="Mô tả")


