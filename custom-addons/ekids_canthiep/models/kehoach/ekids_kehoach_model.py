from odoo import models, fields, api
from datetime import  timedelta,date

from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")




class KeHoach(models.Model):
    _name = 'ekids.kehoach'
    _description = 'Kết luận Đánh giá & Định hướng Kế hoạch'
    _order = 'id desc'

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    name = fields.Char(string="Mã phiếu", required=True, compute="_compute_name")

    # 1. THÔNG TIN HỌC SINH
    hocsinh_id = fields.Many2one('ekids.hocsinh', string="Họ và tên", required=True, tracking=True)  # [cite: 2]


    trangthai = fields.Selection([
        (kehoach_util.TRANGTHAI_DOI_LAP_KEHOACH, "Kết luận đợi lập kế hoạch"),
        (kehoach_util.TRANGTHAI_DANG_LAP_KEHOACH, "Đang lập kế hoạch"),
        (kehoach_util.TRANGTHAI_DANG_CANTHIEP, "Đang can thiệp"),
        (kehoach_util.TRANGTHAI_HET_HIEULUC, "Kế hoạch hết hiệu lực"),


    ], string="Trạng thái",default=kehoach_util.TRANGTHAI_DOI_LAP_KEHOACH)

    trangthai_pheduyet = fields.Selection([
        (kehoach_util.PHEDUYET_DOI_DUYET, "Đợi phê duyệt"),
        (kehoach_util.PHEDUYET_CAN_DIEUCHINH, "Cần điều chỉnh lại"),
        (kehoach_util.PHEDUYET_DA_DUYET, "Đã được duyệt"),


    ], string="Trạng thái phê duyệt", default=kehoach_util.PHEDUYET_DOI_DUYET)

    tu_ngay = fields.Date(
        string="Từ ngày",
        default=fields.Date.context_today
    )

    # Default = Hôm nay + 31 ngày (Dùng hàm lambda để tính toán nhanh)
    den_ngay = fields.Date(
        string="Đến ngày",
        default=lambda self: fields.Date.context_today(self) + timedelta(days=31)
    )
    songay = fields.Integer(string="Số ngày",default=31)

    kehoach_muctieu_ids = fields.Many2many(comodel_name="ekids.kehoach_muctieu"
                                   , relation="ekids_kehoach_muctieu4kehoach_rel"
                                   , column1="kehoach_id"
                                   , column2="kehoach_muctieu_id"
                                   , string="Các mục tiêu cho kế hoạch")

    @api.onchange("tu_ngay")
    def _onchage_tu_ngay(self):
        for record in self:
            if record.tu_ngay:
                record.den_ngay = record.tu_ngay + timedelta(days=31)
            else:
                # Nếu người dùng xóa Từ ngày, có thể tự động xóa luôn Đến ngày cho đồng bộ
                record.den_ngay = False


    @api.onchange("den_ngay")
    def _onchage_den_ngay(self):
        for record in self:
            if record.tu_ngay and record.den_ngay:
                # Đóng ngoặc và thêm .days để lấy số nguyên
                record.songay = (record.den_ngay - record.tu_ngay).days
            else:
                # Nếu 1 trong 2 ô ngày bị trống, set số ngày về 0
                record.songay = 0





    def _compute_name(self):
        for kh in self:
            kh.name = kh.hocsinh_id.name

    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            result = super(KeHoach, self).create(vals)
            if result:
                # Tinh toan so ca trong
                result.func_tao_macdinh_kehoach_muctieu()
                records.append(result)
        return records[0] if len(records) == 1 else records

    @api.model
    def write(self, vals):
        result = super().write(vals)
        if result and "kehoach_linhvuc_ids" in vals:
            self.func_tao_macdinh_kehoach_muctieu()
        return result


    def func_tao_macdinh_kehoach_muctieu(self):
        # unlink cái cũ
        kh_muctieus = self.func_danhsach_kehoach_muctieu(self.id)
        if kh_muctieus:
            for kh_muctieu in kh_muctieus:
                kh_muctieu.unlink()
        # tao cai moi
        if self.kehoach_linhvuc_ids:
            for lv in self.kehoach_linhvuc_ids:
                muctieus = self.func_danhsach_muctieu(lv.linhvuc_id.id,lv.tuoi_id.id)
                if muctieus:
                    for muctieu in muctieus:
                        data={
                            'kehoach_id':self.id,
                            'muctieu_id':muctieu.id
                        }
                        self.env['ekids.kehoach_muctieu'].create(data)

    def func_danhsach_kehoach_muctieu(self, kehoach_id):
        domain = [('kehoach_id', '=', kehoach_id)]
        muctieus = self.env['ekids.kehoach_muctieu'].search(domain)
        return muctieus
    def func_danhsach_muctieu(self,linhvuc_id,tuoi_id):
        domain =[('linhvuc_id','=',linhvuc_id)]
        if tuoi_id:
            domain.append(('tuoi_id', '=', tuoi_id))
        muctieus = self.env['ekids.ct_muctieu'].search(domain)
        return muctieus
    def action_xem_ketluan(self):
        form_view_id = self.env.ref('ekids_canthiep.kehoach_ketluan_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.kehoach',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id
            },
        }

    def action_lap_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        kehoach = kehoach_util.func_get_kehoach_hocsinh(self,self.hocsinh_id)
        if kehoach:
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',
                'res_id': kehoach.id,
                'views': [(form_view_id, 'form')],
                'target': 'new',
                'domain': [('coso_id', '=', self.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id
                },
            }

    def action_gui_pheduyet(self):
        if self.trangthai == '01':
            self.trangthai ="02"

        form_view_id = self.env.ref('ekids_canthiep.kehoach_ketluan_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.kehoach',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id
            },
        }



