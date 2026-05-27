from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoachKetLuan(models.Model):
    _name = 'ekids.kehoach_ketluan'
    _description = 'Kết luận Đánh giá & Định hướng Kế hoạch'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Kế thừa để có tính năng ghi log lịch sử
    _order = 'id desc'

    name = fields.Char(string="Mã phiếu", required=True, copy=False, readonly=True, default='Mới')

    # 1. THÔNG TIN HỌC SINH
    hocsinh_id = fields.Many2one('ekids.hocsinh', string="Họ và tên", required=True, tracking=True)  # [cite: 2]
    ngaysinh = fields.Date(related='hocsinh_id.ngaysinh', string="Ngày tháng năm sinh", readonly=True)  # [cite: 3]

    # 2. CHẨN ĐOÁN & MỨC ĐỘ
    ten_roiloan = fields.Selection([
        ('asd', 'Rối loạn phổ Tự Kỷ'),  # [cite: 4, 5]
        ('delay', 'Trễ phát triển'),  # [cite: 6]
        ('adhd', 'Tăng động giảm chú ý (ADHD)'),  # [cite: 7]
        ('id', 'Khuyết tật trí tuệ'),  # [cite: 8]
        ('speech', 'Chậm nói'),  # [cite: 9]
        ('comm', 'Rối loạn giao tiếp'),  # [cite: 10]
        ('learning', 'Khuyết tật học tập')  # [cite: 11]
    ], string="Tên rối loạn", required=True, tracking=True)

    mucdo = fields.Selection([
        ('1', 'Cần can thiệp'),  # [cite: 12, 13]
        ('2', 'Cần can thiệp nhiều'),  # [cite: 14]
        ('3', 'Cần can thiệp rất nhiều')  # [cite: 15]
    ], string="Mức độ", required=True, tracking=True)

    # 3. ĐỊNH HƯỚNG CAN THIỆP
    lieuluong = fields.Selection([
        ('1h', '1 giờ/ ngày'),  # [cite: 16, 17]
        ('2h', '2 giờ/ ngày'),  # [cite: 18]
        ('3h', '3 giờ/ ngày'),  # [cite: 19]
        ('over_3h', 'Trên 3 giờ/ ngày')  # [cite: 20]
    ], string="Liều lượng can thiệp", required=True)

    # Gợi ý: Nếu bạn có model ekids.ct_chuongtrinh, hãy đổi thành Many2one. Ở đây dùng Char theo doc.
    chuongtrinh_canthiep = fields.Char(
        string="Chương trình can thiệp",
        default="Chương trình can thiệp Từ Sơn xuất sắc."  # [cite: 21]
    )

    phuongphap = fields.Char(string="Phương pháp can thiệp", default="ABA, AAC")  # [cite: 22]
    kythuat = fields.Text(string="Kỹ thuật can thiệp", default="Các kỹ thuật can thiệp của ABA")  # [cite: 23]

    # 4. LỊCH HẸN
    lichhen = fields.Selection([
        ('6_month', 'Đánh giá lại sau 6 tháng can thiệp'),  # [cite: 24, 25]
        ('12_month', 'Đánh giá lại sau 12 tháng can thiệp'),  # [cite: 26]
        ('age_4', 'Đánh giá lại khi trẻ đủ 4 tuổi'),  # [cite: 27]
        ('age_6', 'Đánh giá lại khi trẻ đủ 6 tuổi'),  # [cite: 28]
        ('program', 'Đánh giá lên chương trình (quản lý chuyên môn + giáo viên được phân công)')  # [cite: 29]
    ], string="Lịch hẹn lần sau")

    # 5. BẢNG CHI TIẾT ĐỘ TUỔI PHÁT TRIỂN
    chitiet_ids = fields.One2many(
        'ekids.kehoach_ketluan_chitiet',
        'ketluan_id',
        string="Bảng đánh giá mức độ phát triển"
    )  #

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('done', 'Đã chốt Kết luận')
    ], string="Trạng thái", default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Mới') == 'Mới':
                # Bạn cần tạo một sequence có code là 'ekids.kehoach_ketluan' trong Odoo
                vals['name'] = self.env['ir.sequence'].next_by_code('ekids.kehoach_ketluan') or 'Mới'
        return super().create(vals_list)


# MODEL PHỤ: CHI TIẾT CÁC LĨNH VỰC TRONG BẢNG (Dòng chi tiết)
class KeHoachKetLuanChiTiet(models.Model):
    _name = 'ekids.kehoach_ketluan_chitiet'
    _description = 'Chi tiết mức độ phát triển theo lĩnh vực'

    ketluan_id = fields.Many2one('ekids.kehoach_ketluan', string="Kết luận", ondelete='cascade')

    # Gợi ý: Thay vì dùng Selection tĩnh, nên dùng Many2one trỏ về bảng ekids.ct_linhvuc của bạn
    linhvuc = fields.Selection([
        ('gt_tiepnhan', 'Giao tiếp tiếp nhận'),
        ('gt_bieudat', 'Giao tiếp biểu đạt'),
        ('xh', 'Kỹ năng xã hội'),
        ('batchuoc', 'Bắt chước'),
        ('nhanthuc', 'Nhận thức'),
        ('choi', 'Chơi'),
        ('vd_tinh', 'Vận động tinh'),
        ('vd_tho', 'Vận động thô'),
        ('hanhvi', 'Hành vi'),
        ('taptrung', 'Tập trung chú ý'),
        ('tuphucvu', 'Kỹ năng tự phục vụ')
    ], string="Lĩnh vực", required=True)  #

    tuoi_phattrien = fields.Char(string="Độ tuổi phát triển", placeholder="VD: 12 tháng")  #
    ghi_chu = fields.Char(string="Ghi chú thêm")