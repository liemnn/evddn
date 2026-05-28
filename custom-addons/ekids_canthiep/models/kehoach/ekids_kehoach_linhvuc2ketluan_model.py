from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoachLinhVuc2KetLuan(models.Model):
    _name = 'ekids.kehoach_linhvuc2ketluan'
    _description = 'Kết lận lựa chọn lĩnh vực nào'
    _order = 'id desc'

    sequence = fields.Integer(string="STT", default=1)
    kehoach_id = fields.Many2one("ekids.kehoach", string="Thuộc kế hoạch nào",
                                     required=True,
                                     ondelete="cascade")

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True,ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True,ondelete="cascade")
