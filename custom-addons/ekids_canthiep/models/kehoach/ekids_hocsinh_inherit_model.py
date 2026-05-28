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
        ("00", "Chưa có kết luận đánh giá"),
        ("01", "Kết luận đợi lập kế hoạch"),
        ("0", "Đang lập kế hoạch"),
        ("1", "Đang can thiệp"),
        ("2", "Kế hoạch đã phê duyệt"),
        ("-1", "Kế hoạch hết hiệu lực"),
        ("-2", "Kế hoạch cần chỉnh sửa"),

    ],string="Trạng thái kế hoạch",compute="_compute_trangthai_kehoach")

    is_co_ketluan =fields.Boolean(string="Xem có kết luận còn hiệu lực không",compute="_compute_is_co_ketluan")

    kehoach_ids = fields.One2many("ekids.kehoach",
             "hocsinh_id", string="Các kế hoạch can thệp của học sinh")

    def _compute_is_co_ketluan(self):
        for hs in self:
            domain =[('hocsinh_id','=',hs.id),
            ('trangthai', '=', '1'),
            ]
            count = self.env['ekids.kehoach_ketluan'].search_count(domain)
        if count >0:
            hs.is_co_ketluan = True
        else:
            hs.is_co_ketluan = False

    def action_khoitao_ketluan(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.kehoach_ketluan',
            'view_mode': 'form',
            'target': 'new',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id
            },
        }

    def action_lap_kehoach(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.kehoach_ketluan',
            'view_mode': 'form',
            'target': 'new',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id
            },
        }




    def _compute_trangthai_kehoach(self):
        for hs in self:
            sl_kh_conhieuluc = self.func_soluong_ketluan_con_hieuluc(hs)
            if sl_kh_conhieuluc <=0:
                #th1: chưa có kết luận
                hs.trangthai_kehoach = "00"
            else:
                kehoach = self.func_get_kehoach_con_hieuluc(hs)
                if kehoach:
                    hs.trangthai_kehoach = kehoach.trangthai
                else:
                    # có kế ket luan chưa có kế hoạch
                    hs.trangthai_kehoach="01"

    def func_soluong_ketluan_con_hieuluc(self, hocsinh):
        count = self.env['ekids.kehoach'].search_count(
            [('hocsinh_id', '=', hocsinh.id),
             ('trangthai', '=', '1'),

        ])
        return count

    def func_get_kehoach_con_hieuluc(self, hocsinh):
        kehoach = self.env['ekids.kehoach'].search([
                            ('hocsinh_id', '=', hocsinh.id),
                            ('trangthai', '=', '1')]
                    ,limit=1)
        return kehoach
