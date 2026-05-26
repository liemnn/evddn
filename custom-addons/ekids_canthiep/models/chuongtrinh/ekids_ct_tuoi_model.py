from odoo import models, fields, api, exceptions


class DanhMucTuoi(models.Model):
    _name = "ekids.ct_tuoi"
    _description = "Tuổi thực tế"

    chuongtrinh_id = fields.Many2one('ekids.ct_chuongtrinh', string='Chương trình')

    ma = fields.Char(string="Mã")
    name = fields.Char(string="Tên")
    desc =fields.Html(string="Mô tả")


