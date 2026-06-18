from odoo import models, fields, api
from datetime import  timedelta,date
from odoo.exceptions import ValidationError


class KeHoachKetQua2MucTieu(models.Model):
    _name = 'ekids.kehoach_ketqua2muctieu'
    _description = 'Kết quả thực hiện can thiệp'
    _order = 'id desc'



    kehoach_muctieu_id = fields.Many2one("ekids.kehoach_muctieu",
                                 string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")

    ngay = fields.Date(string="Ngày",required=True)

    ketqua = fields.Selection([
        ("1", "Đạt (+)"),
        ("-1", "Chưa đạt (-)"),
        ("0", "Đang hình thành (+/-)"),


    ], string="Trạng thái")

    desc = fields.Html(string="Mô tả")

    is_readonly = fields.Boolean(string="Các trạng thái được phép sửa",compute="_compute_is_readonly")

    def _compute_is_readonly(self):
        # Dùng context_today để lấy ngày chuẩn theo múi giờ của giáo viên
        today = fields.Date.context_today(self)

        for record in self:
            # Nếu bản ghi chưa có ngày (trường hợp tạo mới chưa lưu), mặc định cho sửa
            if not record.ngay:
                record.is_readonly = False
                continue

            # 1. Tương lai: Không cho sửa
            if record.ngay > today:
                record.is_readonly = True

            # 2. Quá khứ & Hiện tại: Kiểm tra tiếp điều kiện kết quả
            else:
                # Nếu ĐÃ ghi nhận kết quả (trường ketqua có giá trị)
                if record.ketqua:
                    # Tính khoảng cách số ngày từ ngày can thiệp đến hôm nay
                    khoang_cach_ngay = (today - record.ngay).days

                    if khoang_cach_ngay > 3:
                        # Đã quá 3 ngày -> Khóa sổ
                        record.is_readonly = True
                    else:
                        # Vẫn trong hạn 3 ngày -> Cho phép sửa
                        record.is_readonly = False

                # Nếu CHƯA ghi nhận kết quả
                else:
                    # Vẫn cho phép sửa/nhập mới
                    record.is_readonly = False

    def action_set_chuadat(self):
        for rec in self:
            if not rec.is_readonly: rec.ketqua = '-1'
        url = self.func_get_url_back()
        return url

    def action_set_hinhthanh(self):
        for rec in self:
            if not rec.is_readonly: rec.ketqua = '0'
        url = self.func_get_url_back()
        return url

    def action_set_dat(self):
        for rec in self:
            if not rec.is_readonly: rec.ketqua = '1'
        url =self.func_get_url_back()
        return url

    def action_vao_form_ghichu(self):
        # Đảm bảo chỉ thao tác trên 1 bản ghi
        self.ensure_one()

        return {
            'name': 'CHI TIẾT CAN THIỆP',
            'type': 'ir.actions.act_window',
            'res_model': 'ekids.kehoach_ketqua2muctieu',
            'res_id': self.id,  # Trỏ chính xác vào ID của dòng đang click
            'view_mode': 'form',
            'target': 'new',  # Tiếp tục mở một mini-popup đè lên (Odoo hỗ trợ Modal lồng Modal)
        }

    def action_save_ghichu(self):
        # Đảm bảo thao tác trên đúng 1 bản ghi hiện tại
        self.ensure_one()

        # Odoo đã tự lưu dữ liệu. Giờ ta chỉ việc ra lệnh mở lại Kanban Popup
        return {
            'name': 'KẾT QUẢ CAN THIỆP',
            'type': 'ir.actions.act_window',
            'res_model': 'ekids.kehoach_muctieu',
            'res_id': self.kehoach_muctieu_id.id,  # Trỏ chính xác vào ID của dòng đang click
            'view_mode': 'form',
            # Lọc đúng dữ liệu của mục tiêu đang xem để Kanban hiện đúng danh sách
            'target': 'new',
            'context': self.env.context,
        }

    def func_get_url_back(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'KẾT QUẢ CAN THIỆP',
            'res_model': 'ekids.kehoach_muctieu',
            'res_id': self.kehoach_muctieu_id.id,  # Trỏ chính xác vào ID của dòng đang click
            'view_mode': 'form',
            'target': 'new',

        }



