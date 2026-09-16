from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


import logging
_logger = logging.getLogger(__name__)


try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")





class KetLuanWizard(models.TransientModel):
    _name = 'ekids.kehoach_ketluan_wizard'
    _description = 'Bảng tạm bổ sung mục tiêu'

    # 🌟 SỬA TẠI ĐÂY: Gỡ bỏ hoàn toàn thuộc tính required=True thừa thãi gây bẫy lỗi chặn lưu
    chuongtrinh_id = fields.Many2one('ekids.ct_chuongtrinh', string='Chương trình')
    linhvuc_ids = fields.One2many(
        'ekids.ct_linhvuc',
        'ketLuan_wizard_id',
        string="Các lĩnh vực thuộc kết luận lựa chọn"
    )  #