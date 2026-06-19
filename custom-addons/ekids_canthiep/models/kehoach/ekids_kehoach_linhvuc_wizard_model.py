from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoach2LinhVucWizard(models.TransientModel):
    _name = 'ekids.kehoach_linhvuc_wizard'
    _description = 'Bảng tạm bổ sung mục tiêu'

    kehoach_linhvuc_id = fields.Many2one("ekids.kehoach_linhvuc", string="Dòng lĩnh vực mẹ", required=True,
                                         ondelete="cascade")

    # 🌟 SỬA TẠI ĐÂY: Gỡ bỏ hoàn toàn thuộc tính required=True thừa thãi gây bẫy lỗi chặn lưu
    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', related="kehoach_linhvuc_id.linhvuc_id", string='Lĩnh vực')
    tuoi_id = fields.Many2one('ekids.ct_tuoi', related="kehoach_linhvuc_id.tuoi_id", string='Độ tuổi')

    muctieu_ids = fields.Many2many(
        comodel_name="ekids.ct_muctieu",
        relation="ekids_kehoach_linhvuc_wizard2muctieu_rel",
        column1="wizard_id",
        column2="muctieu_id",
        string="Mục tiêu bổ sung",
    )

    @api.model
    def default_get(self, fields_list):
        res = super(KeHoach2LinhVucWizard, self).default_get(fields_list)
        kehoach_linhvuc_id = self.env.context.get('default_kehoach_linhvuc_id')
        if kehoach_linhvuc_id:
            kehoach_linhvuc = self.env['ekids.kehoach_linhvuc'].browse(kehoach_linhvuc_id)
            if kehoach_linhvuc.exists():
                existing_mau_ids = kehoach_linhvuc.kehoach_muctieu_ids.mapped('muctieu_id').ids
                res['muctieu_ids'] = [(6, 0, existing_mau_ids)]
        return res

    def action_xac_nhan_luu(self):
        self.ensure_one()

        if not self.kehoach_linhvuc_id:
            raise ValidationError("Lỗi hệ thống: Chưa nhận được thông tin dòng lĩnh vực mẹ!")

        # 🌟 Sử dụng hàm đồng bộ thông minh (Sync Difference) chống crash database do ràng buộc kết quả học sinh
        current_chosen_mau_ids = self.muctieu_ids.ids
        existing_records = self.env['ekids.kehoach_muctieu'].search([
            ('kehoach_linhvuc_id', '=', self.kehoach_linhvuc_id.id)
        ])
        old_mau_ids = existing_records.mapped('muctieu_id').ids

        # 1. Xóa các mục tiêu bị giáo viên BỎ TÍCH ngoài giao diện Pop-up
        to_delete = existing_records.filtered(lambda r: r.muctieu_id.id not in current_chosen_mau_ids)
        if to_delete:
            for rec_to_del in to_delete:
                # Kiểm tra xem mục tiêu này đã được chấm điểm tiến độ hàng ngày ở bảng kết quả chưa
                has_result = self.env['ekids.kehoach_ketqua2muctieu'].search_count([
                    ('kehoach_muctieu_id', '=', rec_to_del.id)
                ])
                if has_result > 0:
                    raise ValidationError(
                        f"Không thể loại bỏ mục tiêu [{rec_to_del.muctieu_id.name}] vì giáo viên "
                        f"đã ghi nhận kết quả tiến độ can thiệp lâm sàng hàng ngày cho mục tiêu này!"
                    )
                rec_to_del.unlink()

        # 2. Thêm mới các mục tiêu vừa được giáo viên TÍCH THÊM vào lưới
        vals_list = []
        for baimau in self.muctieu_ids:
            if baimau.id not in old_mau_ids:
                vals_list.append({
                    'kehoach_linhvuc_id': self.kehoach_linhvuc_id.id,
                    'muctieu_id': baimau.id,
                    'sequence': baimau.sequence,
                    'trangthai': '0',
                })

        if vals_list:
            self.env['ekids.kehoach_muctieu'].create(vals_list)

        #cap nhat truoc sau

        muctieus = self.env['ekids.kehoach_muctieu'].search([
            ('kehoach_linhvuc_id', '=', self.kehoach_linhvuc_id.id)
        ],order="sequence asc, id desc")
        if muctieus:
            muctieu_truoc = None
            for muctieu in muctieus:
                setattr(muctieu,"kehoach_muctieu_truoc_id",muctieu_truoc)
                muctieu_truoc = muctieu




        return {'type': 'ir.actions.act_window_close'}