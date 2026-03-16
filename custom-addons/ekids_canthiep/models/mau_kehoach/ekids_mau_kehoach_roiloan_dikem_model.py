from odoo import models, fields, api, exceptions


class MauKeHoach2RoiLoanDiKem(models.Model):
    _name = "ekids.mau_kehoach_roiloan_dikem"
    _description = "Lĩnh vực"

    mau_kehoach_id = fields.Many2one("ekids.mau_kehoach", string="Mẫu kế hoạch")
    dm_roiloan_id = fields.Many2one("ekids.ct_dm_roiloan", string="Dạng [Rối loạn] đi kèm")
    chuongtrinh_id = fields.Many2one("ekids.ct_chuongtrinh", string="[Chương trình] can thiệp")
    dm_capdo_id = fields.Many2one("ekids.ct_dm_capdo", string="[Cấp độ] can thiệp")



