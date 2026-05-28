from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoach2LinhVuc(models.Model):
    _name = 'ekids.kehoach_linhvuc'
    _description = 'Các mục tiêu cho kế hoạch'
    _order = 'id desc'

    sequence = fields.Integer(string="STT", default=1)
    kehoach_id = fields.Many2one("ekids.kehoach", string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True, ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True, ondelete="cascade")

    muctieu_ids = fields.One2many("ekids.kehoach_muctieu",
                                  "kehoach_linhvuc_id", string="Mục tiêu")

