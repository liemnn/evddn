from odoo import models, fields, api, exceptions


class MauKeHoachCanThiepThang(models.Model):
    _name = "ekids.mau_kehoach_thang"
    _description = "MẪU [KẾ HOẠCH] THÁNG"

    mau_kehoach_id = fields.Many2one("ekids.mau_kehoach", string="Mẫu kế hoạch")
    name = fields.Selection([("1", "Tháng thứ 1"),
                             ("2", "Tháng thứ 2"),
                             ("3", "Tháng thứ 3"),
                             ("4", "Tháng thứ 4"),
                             ("5", "Tháng thứ 5"),
                             ("6", "Tháng thứ 6"),
                             ("7", "Tháng thứ 7"),
                             ("8", "Tháng thứ 8"),
                             ("9", "Tháng thứ 9"),
                             ("10", "Tháng thứ 10"),
                             ("11", "Tháng thứ 11"),
                             ("12", "Tháng thứ 12")]
                            , string="Chọn tháng thứ")

    muctieu_ids = fields.One2many("ekids.mau_kehoach_muctieu2thang",
                                  "mau_kehoach_thang_id", string="Mục tiêu can thiệp")

    tong_muctieu = fields.Integer(string="Tổng mục tiêu", readonly=True, compute="_compute_tong_muctieu")

    def _compute_tong_muctieu(self):
        for thang in self:
            total = (self.env['ekids.mau_kehoach_muctieu2thang']
                     .search_count([('mau_kehoach_thang_id', '=', thang.id)]))
            thang.tong_muctieu = total
