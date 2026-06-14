from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoach2LinhVucWizard(models.TransientModel):
    _name = 'ekids.kehoach_linhvuc_wizard'
    _description = 'Bảng tạm về lựa chọn lập kế hoạch'

    # Nên giữ lại ràng buộc cascade ở Many2one gốc này để dọn dẹp sạch sẽ nếu xóa kế hoạch mẹ
    kehoach_id = fields.Many2one("ekids.kehoach", string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True)
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True)

    # 🌟 CẬP NHẬT: Giữ nguyên tên bảng quan hệ mới của anh nhưng đưa DOMAIN lọc động quay trở lại
    muctieu_ids = fields.Many2many(
        comodel_name="ekids.ct_muctieu",
        relation="ekids_kehoach_linhvucwizard2muctieu_rel",
        column1="linhvucwizard_id",
        column2="muctieu_id",
        string="Các mục tiêu cho lĩnh vực",
        domain="[('linhvuc_id', '=', linhvuc_id), ('tuoi_id', '=', tuoi_id)]"
    )

    def action_xac_nhan(self):
        return None