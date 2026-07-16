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
    from odoo.addons.ekids_func import giaovien_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")

class KeHoachKetQua2MucTieu(models.Model):
    _name = 'ekids.kehoach_ketqua2muctieu'
    _description = 'Kết quả thực hiện can thiệp'
    _order = 'ngay asc, id asc'



    kehoach_muctieu_id = fields.Many2one("ekids.kehoach_muctieu",
                                 string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")

    ngay = fields.Date(string="Ngày",required=True)

    trangthai = fields.Selection([
        ("0", "Không can thiệp"),
        ("1", "Đạt (+)"),
        ("-1", "Chưa đạt (-)"),
        ("2", "Đang hình thành (+/-)"),


    ], string="Trạng thái",default="0")


    desc = fields.Html(string="Mô tả")

    is_readonly = fields.Boolean(string="Các trạng thái được phép sửa",compute="_compute_is_readonly")
    # 🌟 BỔ SUNG: Trường phân loại mốc ngày phục vụ Widget Giao diện Ma trận
    is_date_status = fields.Selection([
        ("-1", "Quá khứ"),
        ("0", "Hôm nay"),
        ("1", "Tương lai")
    ], string="Mốc thời gian", compute="_compute_is_date_status",default="1")

    loai = fields.Selection([
        ("1", "Đi học"),
        ("0", "Ngày trong tương lai"),
        ("-1", "Ngày không đi hoc"),
    ], string="Phân loại", default="1", compute="_compute_loai")

    def _compute_loai(self):
        for record in self:
            hocsinh = record.kehoach_muctieu_id.kehoach_id.hocsinh_id

            loai = kehoach_util.func_kehoach_ketqua2muctieu(self,hocsinh,record.ngay)
            if loai in ['1','11']:
                record.loai ='1'
            elif loai in ['0']:
                record.loai = '0'
            else:
                record.loai = '-1'



    def _compute_is_date_status(self):
        # Lấy ngày hôm nay chuẩn theo múi giờ local của giáo viên đăng nhập
        today = fields.Date.context_today(self)
        for record in self:
            if not record.ngay:
                record.is_date_status = "-1"
                continue

            if record.ngay < today:
                record.is_date_status = "-1"  # Quá khứ
            elif record.ngay == today:
                record.is_date_status = "0"  # Hôm nay
            else:
                record.is_date_status = "1"  # Tương lai


    def _compute_is_readonly(self):
        # Dùng context_today để lấy ngày chuẩn theo múi giờ của giáo viên
        today = fields.Date.context_today(self)
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        for record in self:
            # Nếu bản ghi chưa có ngày (trường hợp tạo mới chưa lưu), mặc định cho sửa
            is_readonly = False

            # 1. Tương lai: Không cho sửa
            if record.ngay > today:
                is_readonly = True
            # 2. Quá khứ & Hiện tại: Kiểm tra tiếp điều kiện kết quả
            else:
                # Nếu ĐÃ ghi nhận kết quả (trường ketqua có giá trị)
                if record.trangthai:
                    # Tính khoảng cách số ngày từ ngày can thiệp đến hôm nay
                    khoang_cach_ngay = (today - record.ngay).days

                    if khoang_cach_ngay > 5:
                        # Đã quá 3 ngày -> Khóa sổ
                        is_readonly = True
            if is_admin:
                is_readonly = False
            else:
                if is_readonly == False:
                    giaoviens = self.kehoach_muctieu_id.kehoach_linhvuc_id.kehoach_id.ketluan_id.gv_canthiep_ids
                    if giaoviens:
                        user_ids = giaoviens.mapped('user_id').ids
                        if user_ids and user.id in user_ids:
                            is_readonly = True
                   


            record.is_readonly = is_readonly

    def action_set_chuadat(self):
        for rec in self:
            if not rec.is_readonly:
                setattr(rec,"trangthai","-1")
        url = self.func_get_url_back()
        return url

    def action_set_hinhthanh(self):
        for rec in self:
            if not rec.is_readonly:
                setattr(rec,"trangthai","0")
        url = self.func_get_url_back()
        return url

    def action_set_dat(self):
        for rec in self:
            if not rec.is_readonly:
                setattr(rec, "trangthai", "1")
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
        form_view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_capnhat_ketqua_form').id  # chú ý id chính xác

        return {
            'type': 'ir.actions.act_window',
            'name': 'KẾT QUẢ CAN THIỆP',
            'res_model': 'ekids.kehoach_muctieu',
            'res_id': self.kehoach_muctieu_id.id,  # Trỏ chính xác vào ID của dòng đang click
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'target': 'new',

        }



