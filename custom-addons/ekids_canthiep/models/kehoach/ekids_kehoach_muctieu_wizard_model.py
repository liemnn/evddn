from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoach2MucTieuWizard(models.TransientModel):
    _name = 'ekids.kehoach_muctieu_wizard'
    _description = 'Thêm mục mới va kế hoạch'
    _order = 'id desc'

    kehoach_id = fields.Many2one('ekids.kehoach', string='Kế hoạch', required=True)

    # Các trường bộ lọc
    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True)
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True)

    # Chọn nhiều mục tiêu
    muctieu_ids = fields.Many2many(comodel_name="ekids.ct_muctieu"
                                   , relation="ekids_kehoach_muctieu_wizard4kehoach_rel"
                                   , column1="kehoach_id"
                                   , column2="muctieu_id"
                                   , string="Các mục tiêu cho kế hoạch")

    def action_xacnhan(self):
        self.ensure_one()
        if not self.muctieu_ids:
            return {'type': 'ir.actions.act_window_close'}

        # 1. TÌM HOẶC TẠO MỚI LĨNH VỰC (CẤP 2)
        # Để đảm bảo mục tiêu sinh ra có chỗ chứa (kehoach_linhvuc_id)
        LinhVucObj = self.env['ekids.kehoach_linhvuc']
        kh_linhvuc = LinhVucObj.search([
            ('kehoach_id', '=', self.kehoach_id.id),
            ('linhvuc_id', '=', self.linhvuc_id.id),
            ('tuoi_id', '=', self.tuoi_id.id)
        ], limit=1)

        # Nếu lĩnh vực và tuổi này chưa từng được thêm vào kế hoạch, hãy tạo nó
        if not kh_linhvuc:
            kh_linhvuc = LinhVucObj.create({
                'kehoach_id': self.kehoach_id.id,
                'linhvuc_id': self.linhvuc_id.id,
                'tuoi_id': self.tuoi_id.id,
            })

        # 2. TẠO CÁC MỤC TIÊU CHI TIẾT (CẤP 3)
        MucTieuObj = self.env['ekids.kehoach_muctieu']
        for mt in self.muctieu_ids:
            # Kiểm tra chống trùng lặp (nếu mục tiêu này đã có trong lĩnh vực thì bỏ qua)
            exist = MucTieuObj.search([
                ('kehoach_linhvuc_id', '=', kh_linhvuc.id),
                ('muctieu_id', '=', mt.id)
            ], limit=1)

            if not exist:
                MucTieuObj.create({
                    'kehoach_id': self.kehoach_id.id,
                    'kehoach_linhvuc_id': kh_linhvuc.id,
                    'muctieu_id': mt.id,
                })

        # Đóng popup sau khi xử lý xong
        return {'type': 'ir.actions.act_window_close'}