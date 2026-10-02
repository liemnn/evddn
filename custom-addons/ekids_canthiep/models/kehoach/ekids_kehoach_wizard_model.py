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





class KeHoachWizard(models.TransientModel):
    _name = 'ekids.kehoach_wizard'
    _description = 'Bảng tạm bổ sung mục tiêu'

    kehoach_id = fields.Many2one('ekids.kehoach', string='Kế hoạch', required=True)
    coso_id = fields.Many2one('ekids.coso', string='Cơ sở', related='kehoach_id.coso_id')

    chuongtrinh_id = fields.Many2one(
        'ekids.ct_chuongtrinh',
        string='Chương trình',
        required=True
    )
    linhvuc_id = fields.Many2one(
        'ekids.ct_linhvuc',
        string='Lĩnh vực',
        required=True,
        domain="[('chuongtrinh_id', '=', chuongtrinh_id)]"
    )
    tuoi_id = fields.Many2one(
        'ekids.ct_tuoi',
        string='Độ tuổi phát triển',
        required=True
    )

    # Reset Lĩnh vực khi đổi Chương trình
    @api.onchange('chuongtrinh_id')
    def _onchange_chuongtrinh_id(self):
        if self.chuongtrinh_id:
            self.linhvuc_id = False

    def action_them_linhvuc_vao_kehoach(self):
        self.ensure_one()
        kehoach = self.kehoach_id

        # Kiểm tra trùng lặp nếu lĩnh vực này đã có trong kế hoạch
        existing = kehoach.kehoach2linhvuc_ids.filtered(
            lambda r: r.linhvuc_id.id == self.linhvuc_id.id
        )
        if existing:
            raise UserError(f"Lĩnh vực [{self.linhvuc_id.name}] đã có trong kế hoạch này!")

        # 1. Thêm dòng vào bảng kehoach2linhvuc_ids
        vals_linhvuc = {
            'kehoach_id': kehoach.id,
            'chuongtrinh_id': self.chuongtrinh_id.id,
            'linhvuc_id': self.linhvuc_id.id,
            'tuoi_id': self.tuoi_id.id,
        }
        # Nếu model kehoach2linhvuc có coso_id
        if hasattr(self.env['ekids.kehoach2linhvuc'], 'coso_id'):
            vals_linhvuc['coso_id'] = kehoach.coso_id.id

        new_kh_lv = self.env['ekids.kehoach2linhvuc'].create(vals_linhvuc)

        # 2. (Tùy chọn) Tự động nhặt các mục tiêu từ kho chương trình sang kế hoạch (nếu quy trình của bạn cần)
        muctieus = self.env['ekids.dm_muctieu'].search([
            ('linhvuc_id', '=', self.linhvuc_id.id),
            ('tuoi_id', '=', self.tuoi_id.id),
        ], order='sequence asc, id asc')

        for mt in muctieus:
            vals_mt = {
                'kehoach_id': kehoach.id,
                'kehoach2linhvuc_id': new_kh_lv.id,
                'muctieu_id': mt.id,
                'name': mt.name,
                'solan_thu': 10,
                'trangthai': '0',
            }
            if hasattr(self.env['ekids.kehoach_muctieu'], 'coso_id'):
                vals_mt['coso_id'] = kehoach.coso_id.id
            self.env['ekids.kehoach_muctieu'].create(vals_mt)

        return {'type': 'ir.actions.act_window_close'}