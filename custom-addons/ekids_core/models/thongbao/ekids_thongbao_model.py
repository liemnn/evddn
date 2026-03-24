from odoo import api, fields, models
from datetime import datetime


class ThongBao(models.Model):
    _name = 'ekids.thongbao'
    _description = 'Thông báo từ Nhà trường'
    _order = 'create_date desc'

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")

    name = fields.Char(string="Tiêu đề thông báo", required=True)
    noidung = fields.Html(string="Nội dung chi tiết", required=True)
    loai = fields.Selection([
        ('0', 'Thông báo học phí'),
        ('1', 'Thông tin Sức khỏe của trẻ'),
        ('2', 'Thông báo chung của nhà trường')
    ], string="Loại thông báo", default='0')

    trangthai = fields.Selection([
        ('0', 'Đang soạn thảo'),
        ('1', 'Đã gửi đến phụ huynh')
    ], string="Trạng thái", default='0', index=True)

    ngay_gui = fields.Datetime(string="Ngày gửi")

    # Liên kết thống kê
    chitiet_ids = fields.One2many('ekids.thongbao_phuhuynh', 'thongbao_id', string="Thống kê lượt xem")
    tong_dagui = fields.Integer(compute='_compute_thongke')
    tong_daxem = fields.Integer(compute='_compute_thongke')

    @api.depends('chitiet_ids.is_read')
    def _compute_thongke(self):
        for rec in self:
            rec.tong_dagui = len(rec.chitiet_ids)
            rec.tong_daxem = len(rec.chitiet_ids.filtered(lambda x: x.is_read))

    def action_gui_thongbao(self):
        """TỐI ƯU HIỆU NĂNG: Ghi hàng loạt (Batch Insert)"""
        for rec in self:
            # Lấy danh sách user_id của phụ huynh đang hoạt động
            hocsinh_ids = self.env['ekids.hocsinh'].search([('user_id', '!=', False)])

            # Dùng set để lọc trùng lặp (1 phụ huynh có 2 con chỉ nhận 1 tin nhắn)
            unique_users = set(hocsinh_ids.mapped('user_id.id'))

            # Chuẩn bị mảng dữ liệu để Bulk Insert
            vals_list = [{
                'thongbao_id': rec.id,
                'user_id': uid,
                'is_read': False
            } for uid in unique_users]

            # Bắn 1 câu lệnh SQL duy nhất xuống DB để tạo hàng ngàn bản ghi siêu tốc
            if vals_list:
                self.env['ekids.thongbao_phuhuynh'].create(vals_list)

            rec.write({
                'trangthai': '1',
                'ngay_gui': fields.Datetime.now()
            })

