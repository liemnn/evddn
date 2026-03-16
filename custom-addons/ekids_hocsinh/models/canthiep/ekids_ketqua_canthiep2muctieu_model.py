from odoo import models, fields, api, exceptions


class KetQuaCanThiep2Muctieu(models.Model):
    _name = "ekids.kehoach_ketqua2muctieu"
    _description = "Kết quả can thiệp theo mục tiêu hàng tháng"


    muctieu_id = fields.Many2one('ekids.kehoach_muctieu2thang', string='Mục tiêu [Can thiệp]')

    name = fields.Selection(
        selection=[(str(i), str(i)) for i in range(1, 31)],
        string="Ngày của tháng"
    )
    desc = fields.Html(string="Mô tả")

    ketqua = fields.Selection([("", "")
                                     ,("+", "+ Làm được")
                                     , ("-", "- Không làm được")
                                     , ("+/-", "+/- Lúc được, lúc không")
                                  ], string="Kết quả [Can thiệp]"
                                 , default="",)

