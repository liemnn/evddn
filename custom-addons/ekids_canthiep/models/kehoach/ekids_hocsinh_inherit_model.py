from odoo import models, fields, api, exceptions
from datetime import  timedelta,date
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

    trangthai_ketluan = fields.Selection([
        (kehoach_util.HOCSINH_CHUA_CO_KEHOACH, "Chưa có [Kết luận] đánh giá"),
        (kehoach_util.HOCSINH_DOI_LAP_KEHOACH, "Đợi lập kế hoạch"),
        (kehoach_util.HOCSINH_DANG_LAP_KEHOACH, "Đang lập kế hoạch"),
        (kehoach_util.HOCSINH_DANG_CANTHIEP, "Đang can thiệp"),
        (kehoach_util.HOCSINH_HET_HIEULUC, "Hết hiệu lực"),
        (kehoach_util.HOCSINH_DA_DUYET, "Đã duyệt đợi ngày can thiệp"),
        (kehoach_util.HOCSINH_DOI_DUYET, "Kế hoạch đợi duyệt"),
        (kehoach_util.HOCSINH_CAN_DIEUCHINH, "Kế hoạch cần chỉnh sửa"),

    ], string="Trạng thái kế hoạch", compute="_compute_trangthai_ketluan")

    trangthai_kehoach = fields.Selection([
        (kehoach_util.HOCSINH_CHUA_CO_KEHOACH, "Chưa có [Kết luận] đánh giá"),
        (kehoach_util.HOCSINH_DOI_LAP_KEHOACH, "Đợi lập kế hoạch"),
        (kehoach_util.HOCSINH_DANG_LAP_KEHOACH, "Đang lập kế hoạch"),
        (kehoach_util.HOCSINH_DANG_CANTHIEP, "Đang can thiệp"),
        (kehoach_util.HOCSINH_HET_HIEULUC, "Hết hiệu lực"),
        (kehoach_util.HOCSINH_DA_DUYET, "Đã duyệt đợi ngày can thiệp"),
        (kehoach_util.HOCSINH_DOI_DUYET, "Kế hoạch đợi duyệt"),
        (kehoach_util.HOCSINH_CAN_DIEUCHINH, "Kế hoạch cần chỉnh sửa"),


    ],string="Trạng thái kế hoạch",compute="_compute_trangthai_kehoach")







    kehoach_ids = fields.One2many("ekids.kehoach",
             "hocsinh_id", string="Các kế hoạch can thệp của học sinh")


    def _compute_trangthai_kehoach(self):
        today =date.today()
        for hs in self:
            kh = self.func_get_kehoach_hocsinh(hs)
            trangthai=""
            if not kh:
                trangthai= kehoach_util.HOCSINH_CHUA_CO_KEHOACH
            else:
                # có kế hoạch rồi
                if kh.trangthai == kehoach_util.TRANGTHAI_DOI_LAP_KEHOACH:
                    #doi lập kế hoạch
                   trangthai= kehoach_util.HOCSINH_DOI_LAP_KEHOACH
                elif kh.trangthai == kehoach_util.TRANGTHAI_DANG_LAP_KEHOACH:
                    # dang trong quá trình lap ke hoach
                    if kh.trangthai_pheduyet == kehoach_util.PHEDUYET_DOI_DUYET:
                        trangthai = kehoach_util.HOCSINH_DOI_DUYET
                    elif kh.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH:
                        trangthai = kehoach_util.HOCSINH_CAN_DIEUCHINH
                    else:
                       trangthai = kehoach_util.PHEDUYET_DA_DUYET
                else:
                    # dang can thiep
                    if kh.trangthai== kehoach_util.TRANGTHAI_HET_HIEULUC:
                        trangthai = kehoach_util.HOCSINH_HET_HIEULUC
                    else:

                        if kh.den_ngay < today:
                            trangthai = kehoach_util.HOCSINH_HET_HIEULUC
                        elif (today >= kh.tu_ngay
                                and today <= kh.den_ngay):
                            trangthai = kehoach_util.HOCSINH_DANG_CANTHIEP
                        else:
                            trangthai = kehoach_util.HOCSINH_DA_DUYET
            hs.trangthai_kehoach =trangthai


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
            kehoach.trangthai = kehoach_util.TRANGTHAI_DANG_LAP_KEHOACH
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',
                'res_id': kehoach.id,
                'views': [(form_view_id, 'form')],
                'target': 'current',
                'domain': [('coso_id', '=', self.coso_id.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id
                },
            }

    def action_duyet_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        kehoach = kehoach_util.func_get_kehoach_hocsinh(self,self)
        if kehoach:
            kehoach.trangthai = kehoach_util.TRANGTHAI_DANG_LAP_KEHOACH
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',
                'res_id': kehoach.id,
                'views': [(form_view_id, 'form')],
                'target': 'current',
                'domain': [('coso_id', '=', self.coso_id.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id
                },
            }

    def action_xem_kehoach(self):
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
                'domain': [('coso_id', '=', self.coso_id.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id
                },
            }

    def action_canthiep(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        kehoach = kehoach_util.func_get_kehoach_hocsinh(self,self)
        if kehoach:
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach_muctieu',
                'view_mode': 'kanban,list',
                'target': 'current',
                'domain': [('kehoach_id', '=', kehoach.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_kehoach_id': kehoach.id
                },
            }

    def action_xem_danhsach_kehoach(self):
        kanban_view_id = self.env.ref('ekids_canthiep.danhsach_kehoach_kanban').id
        form_view_id = self.env.ref('ekids_canthiep.kehoach_ketluan_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH KẾ HOẠCH',
            'res_model': 'ekids.kehoach',
            'view_mode': 'kanban',
            'views': [(kanban_view_id, 'kanban'),(form_view_id, 'form')],
            'target': 'current',
            'domain': [('hocsinh_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id
            },
        }
