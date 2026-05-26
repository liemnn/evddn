from odoo import models, fields, api, exceptions


class DanhMucTuoi(models.Model):
    _name = "ekids.ct_tuoi"
    _description = "Tuổi thực tế"

    sequence = fields.Integer(string="STT", default=1)
    chuongtrinh_id = fields.Many2one('ekids.ct_chuongtrinh', string='Chương trình')
    name = fields.Char(string="Tên")
    desc =fields.Html(string="Mô tả")


