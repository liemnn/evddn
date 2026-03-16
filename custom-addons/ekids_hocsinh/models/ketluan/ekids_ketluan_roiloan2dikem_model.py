from odoo import models, fields, api, exceptions


class KetLuanRoiloan2Kikem(models.Model):
    _name = "ekids.ketluan_roiloan2dikem"
    _description = "Lĩnh vực"

    sequence = fields.Integer(string="STT", default=1)
    ketluan_id = fields.Many2one("ekids.ketluan", string="Kế hoạch")
    dm_roiloan_id = fields.Many2one("ekids.ct_dm_roiloan", string="Dạng [Rối loạn]")
    chuongtrinh_id = fields.Many2one("ekids.ct_chuongtrinh", string="Chương trình")
    dm_capdo_id = fields.Many2one("ekids.ct_dm_capdo", string="Cấp độ")



