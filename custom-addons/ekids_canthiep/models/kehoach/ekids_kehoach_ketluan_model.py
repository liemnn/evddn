from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoachKetLuanLinhVuc(models.Model):
    _name = 'ekids.kehoach_ketluan'
    _description = 'Kết luận Đánh giá & Định hướng Kế hoạch'
    _order = 'id desc'

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    name = fields.Char(string="Mã phiếu", required=True, default='Mới')

    # 1. THÔNG TIN HỌC SINH
    hocsinh_id = fields.Many2one('ekids.hocsinh', string="Họ và tên", required=True, tracking=True)  # [cite: 2]

    # 2. CHẨN ĐOÁN & MỨC ĐỘ


    dm_roiloan_ids = fields.Many2many(comodel_name="ekids.ct_dm_roiloan"
                                      , relation="ekids_kehoach_ketluan2dm_roiloan_rel"
                                      , column1="ketluan_id"
                                      , column2="dm_roiloan_id"
                                      , string="Các vấn đề của trẻ")

    mucdo = fields.Selection([
        ('1', 'Cần can thiệp'),  # [cite: 12, 13]
        ('2', 'Cần can thiệp nhiều'),  # [cite: 14]
        ('3', 'Cần can thiệp rất nhiều')  # [cite: 15]
    ], string="Mức độ", required=True, default="1")

    # 3. ĐỊNH HƯỚNG CAN THIỆP
    lieuluong = fields.Char(string="Liều lượng can thiệp", required=True)

    # Gợi ý: Nếu bạn có model ekids.ct_chuongtrinh, hãy đổi thành Many2one. Ở đây dùng Char theo doc.
    chuongtrinh_ids = fields.Many2many(comodel_name="ekids.ct_chuongtrinh"
                                      , relation="ekids_kehoach_ketluan2chuongtrinh_rel"
                                      , column1="ketluan_id"
                                      , column2="chuongtrinh_id"
                                      , string="Chương trình can thiệp")

    phuongphap = fields.Char(string="Phương pháp can thiệp")  # [cite: 22]
    kythuat = fields.Char(string="Kỹ thuật can thiệp")

    # 4. LỊCH HẸN
    lichhen = fields.Char(string="Lịch hẹn lần sau")

    # 5. BẢNG CHI TIẾT ĐỘ TUỔI PHÁT TRIỂN
    ketluan_khung_ids = fields.One2many(
        'ekids.kehoach_ketluan_khung',
        'ketluan_id',
        string="10.	Đánh giá lên chương trình"
    )  #
    gv_danhgia = fields.Char(string="Chuyên gia đánh giá")
    ngay_danhgia= fields.Date(string="Ngày đánh giá")
    desc = fields.Html(string="Ghi chú")

    gv_lapkehoach_id = fields.Many2one('ekids.giaovien'
                                       , string="Giáo viên [Lập kế hoạch]")

    gv_kiemduyet_id = fields.Many2one('ekids.giaovien'
                                      , string="Giáo viên [Kiểm duyệt chuyên môn]")


    gv_canthiep_id = fields.Many2one('ekids.giaovien'
                                       , string="Giáo viên [Can thiệp]")


    trangthai = fields.Selection([
        ('0', 'Hết hiệu lực'),
        ('1', 'Đã kết luận')

    ], string="Trạng thái", default='1')

