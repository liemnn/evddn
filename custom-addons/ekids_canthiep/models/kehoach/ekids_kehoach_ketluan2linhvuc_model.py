from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KetLuan2LinhVuc(models.Model):
    _name = 'ekids.kehoach_ketluan2linhvuc'
    _description = 'Các lĩnh vực thuộc kết luận'
    _order = 'sequence asc,id desc'

    sequence = fields.Integer(string="STT", default=1)
    ketluan_id = fields.Many2one("ekids.kehoach_ketluan", string="Thuộc kết luận nào",
                                 required=True,
                                 ondelete="cascade")

    chuongtrinh_id = fields.Many2one(
        'ekids.ct_chuongtrinh',
        string='Chương trình',
        required=True,
        ondelete="cascade",
        default=lambda self: self.env['ekids.ct_chuongtrinh'].search([], limit=1, order='id asc').id
    )

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True, ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True, ondelete="cascade")

