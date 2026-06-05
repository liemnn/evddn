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

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True, ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True, ondelete="cascade")

    muctieu_ids = fields.Many2many(comodel_name="ekids.ct_muctieu"
                                           , relation="ekids_kehoach_ct_muctieu4kehoach_rel"
                                           , column1="kehoach_id"
                                           , column2="muctieu_id"
                                           , string="Các mục tiêu cho kế hoạch")

    # TRƯỜNG MỚI: Tự động biên dịch danh sách bài học thành giao diện hàng lối sang trọng
    muctieu_html = fields.Html(string="Giao diện danh sách bài học", compute="_compute_muctieu_html", store=False)

    @api.depends('muctieu_ids')
    def _compute_muctieu_html(self):
        for rec in self:
            html_str =""

            # KIỂM TRA: Nếu có dữ liệu thật thì render thật, nếu trống thì đổ dữ liệu giả lập DEMO
            if rec.muctieu_ids:
                html_str = '<div class="d-flex flex-column gap-2 mt-1">'
                targets = rec.muctieu_ids

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
                                {target.name}
                            </span>
                        </div>
                        """

                html_str += '</div>'
            rec.muctieu_html = html_str