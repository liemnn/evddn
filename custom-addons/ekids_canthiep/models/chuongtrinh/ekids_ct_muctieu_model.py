from odoo import models, fields, api, exceptions
import re
from bs4 import BeautifulSoup


class MucTieu(models.Model):
    _name = "ekids.ct_muctieu"
    _description = "Lĩnh vực"

    sequence = fields.Integer(string="STT", default=1)
    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực')
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi')

    name = fields.Html(string="Mục tiêu [Can thiệp]")
    chucnang = fields.Html(string="Trích yếu (mã)")
    thietke = fields.Html(string="Kỹ thuật/chiến lược")
    tieuchi_chuadat = fields.Char(string="Chưa đạt (-)")
    tieuchi_hinhthanh = fields.Char(string="Đang hình thành (+/-)")
    tieuchi_dat = fields.Char(string="Đạt (+)")


