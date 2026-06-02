from odoo import models, fields, api, exceptions
import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")



class HocSinhInherit(models.Model):
    _inherit = "ekids.hocsinh"

    trangthai_kehoach = fields.Selection([
        ("0", "Chưa có kết luận đánh giá"),
        ("00", "Kết luận đợi lập kế hoạch"),
        ("01", "Đang lập kế hoạch"),
        ("1", "Đang can thiệp"),
        ("02", "Kế hoạch đã phê duyệt"),
        ("-1", "Kế hoạch hết hiệu lực"),
        ("03", "Kế hoạch cần chỉnh sửa"),

    ],string="Trạng thái kế hoạch",compute="_compute_trangthai_kehoach")




    kehoach_ids = fields.One2many("ekids.kehoach",
             "hocsinh_id", string="Các kế hoạch can thệp của học sinh")






    def _compute_trangthai_kehoach(self):
        for hs in self:
            kehoach = self.func_get_kehoach_hocsinh(hs)
            if kehoach:
                #th1: chưa có kết luận
                hs.trangthai_kehoach = kehoach.trangthai
            else:
                hs.trangthai_kehoach ="0"

    def func_get_kehoach_hocsinh(self, hocsinh):
        kehoach = self.env['ekids.kehoach'].search([
                            ('hocsinh_id', '=', hocsinh.id),
                            ]
                    , order="tu_ngay desc, id desc",limit=1)
        return kehoach


    def action_khoitao_ketluan(self):
        form_view_id = self.env.ref('ekids_canthiep.kehoach_ketluan_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.kehoach',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id
            },
        }

    def action_lap_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        kehoach = kehoach_util.func_get_kehoach_hocsinh(self,self)
        if kehoach:
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',
                'res_id': kehoach.id,
                'views': [(form_view_id, 'form')],
                'target': 'current',
                'domain': [('coso_id', '=', self.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id
                },
            }
