from odoo import models, fields, api, exceptions
import re
from bs4 import BeautifulSoup


class MucTieu(models.Model):
    _name = "ekids.ct_muctieu"
    _description = "Lĩnh vực"

    coso_id = fields.Many2one("ekids.coso", related="linhvuc_id.coso_id", string="Cơ sở", required=True,ondelete="restrict")
    chuongtrinh_id = fields.Many2one("ekids.ct_chuongtrinh", related="linhvuc_id.chuongtrinh_id", string="Chương trình", required=True,
                              ondelete="restrict")

    sequence = fields.Integer(string="STT", default=1)
    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực')
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi')

    name = fields.Char(string="Tên")
    chucnang = fields.Html(string="Chức năng phát triển cốt lõi & Lập luận lâm sàng")
    thietke = fields.Html(string="Thiết kế hoạt động cho giáo viên Theo mô tả (ABC)")
    tieuchi_chuadat = fields.Char(string="Chưa đạt (-)")
    tieuchi_hinhthanh = fields.Char(string="Đang hình thành (+/-)")
    tieuchi_dat = fields.Char(string="Đạt (+)")


