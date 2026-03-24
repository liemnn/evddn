from odoo import api, fields, models
from datetime import datetime
class ThongBaoPhuHuynh(models.Model):
    _name = 'ekids.thongbao_phuhuynh'
    _description = 'Hộp thư Phụ huynh'
    _order = 'is_read asc, id desc'  # Tin chưa đọc luôn nổi lên trên

    # Các trường vật lý (Chiếm dung lượng siêu nhỏ)
    thongbao_id = fields.Many2one('ekids.thongbao', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', required=True, index=True)  # Index để truy vấn hộp thư cực nhanh
    is_read = fields.Boolean(string="Đã xem", default=False, index=True)  # Index để lọc tin chưa đọc
    ngay_xem = fields.Datetime(string="Thời gian xem")

    # TỐI ƯU LƯU TRỮ: Dùng store=False để móc dữ liệu từ bảng gốc ra xem mà không tốn ổ cứng
    name = fields.Char(related='thongbao_id.name', string="Tiêu đề", store=False)
    noidung = fields.Html(related='thongbao_id.noidung', string="Nội dung", store=False)
    loai_thongbao = fields.Selection(related='thongbao_id.loai', store=False)
    ngay_gui = fields.Datetime(related='thongbao_id.ngay_gui', store=False)

    def action_doc_thongbao(self):
        """Hàm mở thư và đánh dấu đã đọc an toàn"""
        self.ensure_one()
        if not self.is_read:
            # Dùng sudo() để Phụ huynh có quyền update trạng thái của chính mình
            self.sudo().write({
                'is_read': True,
                'ngay_xem': fields.Datetime.now()
            })

        return {
            'name': 'Chi tiết Thông báo',
            'type': 'ir.actions.act_window',
            'res_model': 'ekids.thongbao_phuhuynh',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'flags': {'mode': 'readonly'},
            'context': {'create': False, 'edit': False}
        }