from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoachKetLuanKhung(models.Model):
    _name = 'ekids.kehoach_ketluan_khung'
    _description = 'Kết luận Khung đánh giá'
    _order = 'id desc'

    sequence = fields.Integer(string="STT", default=1)
    ketluan_id = fields.Many2one("ekids.kehoach_ketluan", string="Thuộc kết luận nào",
                                     required=True,
                                     ondelete="cascade")

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True,ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True,ondelete="cascade")
