from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoach2LinhVuc(models.Model):
    _name = 'ekids.kehoach_linhvuc'
    _description = 'Các mục tiêu cho kế hoạch'
    _order = 'id desc'

    sequence = fields.Integer(string="STT", default=1)
    kehoach_id = fields.Many2one("ekids.kehoach", string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")

    chuongtrinh_id = fields.Many2one(
        'ekids.ct_chuongtrinh',
        string='Chương trình',
        required=True,
        ondelete="cascade",
    )

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True, ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True, ondelete="cascade")

    kehoach_muctieu_ids = fields.One2many(
        comodel_name="ekids.kehoach_muctieu",
        inverse_name="kehoach_linhvuc_id",
        string="Các mục tiêu cho kế hoạch"
    )


    # TRƯỜNG MỚI: Tự động biên dịch danh sách bài học thành giao diện hàng lối sang trọng
    muctieu_html = fields.Html(string="Giao diện danh sách bài học", compute="_compute_muctieu_html", store=False)

    @api.depends('kehoach_muctieu_ids')
    def _compute_muctieu_html(self):
        for rec in self:
            html_str =""

            # KIỂM TRA: Nếu có dữ liệu thật thì render thật, nếu trống thì đổ dữ liệu giả lập DEMO
            if rec.kehoach_muctieu_ids:
                html_str = '<div class="d-flex flex-column gap-2 mt-1">'
                targets = rec.kehoach_muctieu_ids

                # Vòng lặp tự động sinh số thứ tự tuyến tính 1, 2, 3...
                for idx, target in enumerate(targets, 1):
                    html_str += f"""
                        <div class="d-flex align-items-start gap-2 p-2 rounded-2" 
                             style="background-color: #F8FAFC; border: 1px solid #F1F5F9; margin-bottom: 4px;">
                            <span class="d-flex align-items-center justify-content-center font-monospace" 
                                  style="width: 22px; height: 22px; background: linear-gradient(135deg, #38BDF8 0%, #0284C7 100%); 
                                         color: white; font-weight: 900; font-size: 11px; border-radius: 50%; flex-shrink: 0; margin-top: 1px;">
                                {idx}
                            </span>
                            <span style="font-size: 13px; font-weight: 600; color: #334155; line-height: 1.4; white-space: normal;">
                                {target.muctieu_id.name}
                            </span>
                        </div>
                        """

                html_str += '</div>'
            rec.muctieu_html = html_str

    def action_xem_linhvucwizard2muctieu(self):
        # Lấy ID của danh sách list view danh mục mục tiêu mẫu
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_linhvuc_wizard_form').id

        return {
            'type': 'ir.actions.act_window',
            'name': 'LỰA CHỌN MỤC TIÊU CHO KẾ HOẠCH',
            'res_model': 'ekids.kehoach_linhvuc_wizard',
            'view_mode': 'form',  # 🌟 SỬA TỪ 'form' THÀNH 'list' để hiện danh sách
            'views': [(form_view_id, 'form')],  # Chuẩn Odoo 18
            'target': 'new',  # Mở dạng Pop-up
            'context': {
                # Ép bộ lọc tự động chỉ hiển thị các mục tiêu thuộc Lĩnh vực và Độ tuổi này
                'search_default_linhvuc_id': self.linhvuc_id.id,
                'search_default_tuoi_id': self.tuoi_id.id,

                # Truyền ngầm các thông tin này sang Context để lát nữa bốc đầu xử lý dữ liệu
                'default_kehoach_id': self.kehoach_id.id,
                'default_linhvuc_id': self.linhvuc_id.id,
                'default_tuoi_id': self.tuoi_id.id,

                'edit': False,  # 🚫 Tắt hoàn toàn tính năng và ẩn nút [Sửa]
                'create': False,  # 🚫 Tắt tính năng và ẩn nút [Tạo mới]
                'delete': False,  # 🚫 Tắt tính năng và ẩn nút [Xóa]
            },
        }

    def action_xem_danhsach_ct_muctieu(self):
        # Lấy ID của danh sách list view danh mục mục tiêu mẫu
        list_view_id = self.env.ref('ekids_canthiep.ct_muctieu_list').id

        return {
            'type': 'ir.actions.act_window',
            'name': 'LỰA CHỌN MỤC TIÊU CHO KẾ HOẠCH',
            'res_model': 'ekids.ct_muctieu',
            'view_mode': 'list',  # 🌟 SỬA TỪ 'form' THÀNH 'list' để hiện danh sách
            'views': [(list_view_id, 'list')],  # Chuẩn Odoo 18
            'target': 'new',  # Mở dạng Pop-up
            'context': {
                # Ép bộ lọc tự động chỉ hiển thị các mục tiêu thuộc Lĩnh vực và Độ tuổi này
                'search_default_linhvuc_id': self.linhvuc_id.id,
                'search_default_tuoi_id': self.tuoi_id.id,

                # Truyền ngầm các thông tin này sang Context để lát nữa bốc đầu xử lý dữ liệu
                'default_kehoach_id': self.kehoach_id.id,
                'default_linhvuc_id': self.linhvuc_id.id,
                'default_tuoi_id': self.tuoi_id.id,

                'edit': False,  # 🚫 Tắt hoàn toàn tính năng và ẩn nút [Sửa]
                'create': False,  # 🚫 Tắt tính năng và ẩn nút [Tạo mới]
                'delete': False,  # 🚫 Tắt tính năng và ẩn nút [Xóa]
            },
        }

