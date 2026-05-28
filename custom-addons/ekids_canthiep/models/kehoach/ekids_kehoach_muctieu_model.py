from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoach2MucTieu(models.Model):
    _name = 'ekids.kehoach_muctieu'
    _description = 'Các mục tiêu cho kế hoạch'
    _order = 'id desc'

    sequence = fields.Integer(string="STT", default=1)
    kehoach_id = fields.Many2one("ekids.kehoach", string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")

    kehoach_linhvuc_id = fields.Many2one('ekids.kehoach_linhvuc'
                                         , string='Lĩnh vực'
                                         , required=True, ondelete="cascade")

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc',
                                 related="muctieu_id.linhvuc_id", string='Lĩnh vực', required=True, ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi',
                              related="muctieu_id.tuoi_id", required=True, ondelete="cascade")

    muctieu_id = fields.Many2one('ekids.ct_muctieu', string='Mục tiêu', required=True, ondelete="cascade")

