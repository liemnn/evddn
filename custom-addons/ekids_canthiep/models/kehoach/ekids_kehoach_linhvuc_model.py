from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoach2LinhVuc(models.Model):
    _name = 'ekids.kehoach_linhvuc'
    _description = 'Các mục tiêu cho kế hoạch'
    _order = "sequence asc"

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

    is_readonly = fields.Boolean(compute="_compute_is_readonly")

    def _compute_is_readonly(self):
        for record in self:
            record.is_readonly = record.kehoach_id.is_readonly

    @api.depends('kehoach_muctieu_ids')
    def _compute_muctieu_html(self):
        for rec in self:
            html_str = ""

            # KIỂM TRA: Nếu có dữ liệu thật thì render thật
            if rec.kehoach_muctieu_ids:
                html_str = '<div class="d-flex flex-column gap-2 mt-1">'
                targets = rec.kehoach_muctieu_ids

                # Vòng lặp tự động sinh số thứ tự tuyến tính 1, 2, 3...
                for idx, target in enumerate(targets, 1):

                    # 🌟 LOGIC TỰ ĐỘNG ĐỔ BADGE THEO NGUỒN GỐC MỤC TIÊU
                    if target.kehoach_muctieu_thangtruoc_id:
                        # Nhãn Đỏ Pastel cho mục tiêu cũ tháng trước chuyển sang
                        badge_nguon_goc = """
                        <span style="display: inline-block; padding: 2px 6px; font-size: 11px; font-weight: 700; 
                                     color: #DC2626; background-color: #FEF2F2; border: 1px solid #FCA5A5; 
                                     border-radius: 6px; white-space: nowrap; margin-left: auto;">
                            <i class="fa fa-history" style="margin-right: 2px; font-size: 10px;"></i>Tháng trước chuyển sang
                        </span>
                        """
                    else:
                        # Nhãn Xanh Lá Pastel cho mục tiêu mới lập của tháng này
                        badge_nguon_goc = """
                        <span style="display: inline-block; padding: 2px 6px; font-size: 11px; font-weight: 700; 
                                     color: #16A34A; background-color: #F0FDF4; border: 1px solid #BBF7D0; 
                                     border-radius: 6px; white-space: nowrap; margin-left: auto;">
                            <i class="fa fa-star" style="margin-right: 2px; font-size: 10px;"></i>Mới
                        </span>
                        """

                    html_str += f"""
                        <div class="d-flex align-items-center gap-2 p-2 rounded-2" 
                             style="background-color: #F8FAFC; border: 1px solid #F1F5F9; margin-bottom: 4px;">
                            <span class="d-flex align-items-center justify-content-center font-monospace" 
                                  style="width: 22px; height: 22px; background: linear-gradient(135deg, #38BDF8 0%, #0284C7 100%); 
                                         color: white; font-weight: 900; font-size: 11px; border-radius: 50%; flex-shrink: 0;">
                                {idx}
                            </span>

                            <span style="font-size: 13px; font-weight: 600; color: #334155; line-height: 1.4; white-space: normal; max-width: 70%;">
                                {target.muctieu_id.name or ''}
                            </span>

                            {badge_nguon_goc}
                        </div>
                        """

                html_str += '</div>'

            rec.muctieu_html = html_str

    def action_xem_danhsach_ct_muctieu(self):
        self.ensure_one()

        wizard_id = self.env.context.get('default_wizard_id')
        # Tìm ID của Form View của bảng tạm Wizard anh em mình vừa tạo ở Bước 2
        wizard_form_id = self.env.ref('ekids_canthiep.kehoach_linhvuc_wizard_form').id
        muctieu_thangtruoc_ids=[]
        kehoach_muctieus = self.kehoach_muctieu_ids
        if kehoach_muctieus:
            for kehoach_muctieu in kehoach_muctieus:
                if kehoach_muctieu.kehoach_muctieu_thangtruoc_id:
                    muctieu_thangtruoc_ids.append(kehoach_muctieu.muctieu_id.id)

        url= {
            'type': 'ir.actions.act_window',
            'name': 'CÁC MỤC TRONG LĨNH VỰC CỦA KẾ HOẠCH',
            'res_model': 'ekids.kehoach_linhvuc_wizard',
            'view_mode': 'form',
            'views': [(wizard_form_id, 'form')],
            'target': 'new',
            'context': {
                'search_default_linhvuc_id': self.linhvuc_id.id,
                'search_default_tuoi_id': self.tuoi_id.id,

                # 🌟 BỔ SUNG DÒNG NÀY: Truyền ID dòng hiện tại sang để điền vào trường bắt buộc của Wizard
                'default_kehoach_linhvuc_id': self.id,

                'default_kehoach_id': self.kehoach_id.id,
                'default_linhvuc_id': self.linhvuc_id.id,
                'default_tuoi_id': self.tuoi_id.id,
                'default_hocsinh_id': self.kehoach_id.hocsinh_id.id,
                'default_muctieu_thangtruoc_ids':muctieu_thangtruoc_ids,

                'edit': False,
                'create': True,
                'delete': False,
            },
        }
        if wizard_id:
            url["res_id"]= wizard_id
        return url
