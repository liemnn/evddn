from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
    from odoo.addons.ekids_func import giaovien_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")






class KetLuanGiaoVienWizard(models.TransientModel):
    _name = 'ekids.kehoach_ketluan_giaovien_wizard'
    _description = 'Phân công lại giáo viên trong kết luận'

    gv_canthiep_wizard_id = fields.Many2one('ekids.kehoach_ketluan_phancong_lai_wizard', string="Thuộc phân công lại", required=True)  # [cite: 2]

    kehoach_id = fields.Many2one("ekids.kehoach", string="Kế hoạch", required=True)

    gv_canthiep_id = fields.Many2one('ekids.giaovien'
                                      , string="Giáo viên [Lập/can thiệp]", required=True)

    trangthai = fields.Selection([
        (kehoach_util.KEHOACH_DANG_LAP, "Đang lập"),
        (kehoach_util.KEHOACH_DANG_PHEDUYET, "Đang kiểm duyệt"),
        (kehoach_util.KEHOACH_DANG_CANTHIEP, "Đang can thiệp"),
        (kehoach_util.KEHOACH_HET_HIEULUC, "Hết hiệu lực"),

    ], string="Trạng thái", compute="_compute_trangthai")

    @api.depends("kehoach_id")
    def _compute_trangthai(self):
        for record in self:
            record.trangthai = record.kehoach_id.trangthai
