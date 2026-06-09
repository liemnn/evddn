from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError
import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")




class KetLuan(models.Model):
    _name = 'ekids.kehoach_ketluan'
    _description = 'Kết luận Đánh giá & Định hướng Kế hoạch'
    _order = 'id desc'

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    name = fields.Char(string="Kết luận lần", required=True, compute="_compute_name")
    index = fields.Integer(string="STT", default=1, compute="_compute_index")
    # 1. THÔNG TIN HỌC SINH
    hocsinh_id = fields.Many2one('ekids.hocsinh', string="Họ và tên", required=True, tracking=True)  # [cite: 2]

    trangthai = fields.Selection([
        (kehoach_util.KETLUAN_DANG_TAO, "Đang soạn thảo"),
        (kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH, "Cho phép lập [Kế hoạch]"),
        (kehoach_util.KETLUAN_HET_HIEULUC, "Hết hiệu lực lập [Kế hoạch]"),

    ], string="Trạng thái", default=kehoach_util.KETLUAN_DANG_TAO)

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
    kehoach_linhvuc_ids = fields.One2many(
        'ekids.kehoach_linhvuc',
        'ketluan_id',
        string="10.	Đánh giá lên chương trình"
    )  #
    gv_danhgia = fields.Char(string="Chuyên gia đánh giá")
    ngay_danhgia= fields.Date(string="Ngày đánh giá")
    desc = fields.Html(string="Ghi chú")

    gv_lapkehoach_id = fields.Many2one('ekids.giaovien'
                                       , string="Giáo viên [Lập kế hoạch]", required=True)

    gv_kiemduyet_id = fields.Many2one('ekids.giaovien'
                                      , string="Giáo viên [Kiểm duyệt chuyên môn]", required=True)


    gv_canthiep_id = fields.Many2one('ekids.giaovien'
                                       , string="Giáo viên [Can thiệp]", required=True)

    def _compute_name(self):
        for record in self:
            record.name = string_util.date2string(record.ngay_danhgia) +"-"+ record.gv_danhgia

    def _compute_index(self):
        index = len(self)
        for record in self:
            record.index = index
            index -= 1

    def action_lap_kehoach(self):
        return None

    def create(self, vals):
        hocsinh_id = vals['hocsinh_id']
        if hocsinh_id:
            hocsinh = self.browse(hocsinh_id)
            if hocsinh:
                kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self, hocsinh, kehoach_util.KETLUAN_DANG_TAO)
                if kehoach:
                    raise UserError("Đang có Kết luận ở trạng thái [Đang soạn thảo] bản không thể tạo kết luận mới")
                else:
                    ketluan = super().create(vals)
                    return ketluan
        raise UserError("Không thể tạo [Kết luận] mới vui lòng kiểm tra lại")

    def write(self, vals):

        ketluan = super().write(vals)

        return ketluan

    def unlink(self):
        ketluan = super().unlink()
        return ketluan