from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoachKetLuan(models.Model):
    _name = 'ekids.kehoach_ketluan'
    _description = 'Kết luận Khung đánh giá'
    _order = 'id desc'

    sequence = fields.Integer(string="STT", default=1)
    kehoach_id = fields.Many2one("ekids.kehoach", string="Thuộc kế hoạch nào",
                                     required=True,
                                     ondelete="cascade")

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True,ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True,ondelete="cascade")
