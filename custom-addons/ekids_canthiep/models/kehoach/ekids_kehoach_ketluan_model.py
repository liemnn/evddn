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
    lieuluong = fields.Selection([
        ('1', '1 giờ/ ngày'),  # [cite: 12, 13]
        ('2', '2 giờ/ ngày'),  # [cite: 14]
        ('3', '3 giờ/ ngày'),  # [cite: 15]
        ('4', 'Trên 3 giờ/ ngày')  # [cite: 15]
    ], string="Liều lượng", required=True, default="1")



    # Gợi ý: Nếu bạn có model ekids.ct_chuongtrinh, hãy đổi thành Many2one. Ở đây dùng Char theo doc.
    chuongtrinh_ids = fields.Many2many(comodel_name="ekids.ct_chuongtrinh"
                                      , relation="ekids_kehoach_ketluan2chuongtrinh_rel"
                                      , column1="ketluan_id"
                                      , column2="chuongtrinh_id"
                                      , string="Chương trình can thiệp")


    phuongphap = fields.Selection([
        ('1', 'ABA'),  # [cite: 12, 13]
        ('2', 'AAC'),  # [cite: 14]
        ('3', 'TEACCH')  # [cite: 15]

    ], string="Phương pháp", default="1")

    kythuat = fields.Char(string="Kỹ thuật can thiệp")

    # 4. LỊCH HẸN

    lichhen = fields.Selection([
        ('1', 'Đánh giá lại sau 6 tháng can thiệp'),  # [cite: 12, 13]
        ('2', 'Đánh giá lại sau 12 tháng can thiệp'),  # [cite: 14]
        ('3', 'Đánh giá lại khi trẻ đủ 4 tuổi'), # [cite: 15]
        ('4', 'Đánh giá lại khi trẻ đủ 6 tuổi')  # [cite: 15]
    ], string="Lịch hẹn lần sau", default="1")

    # 5. BẢNG CHI TIẾT ĐỘ TUỔI PHÁT TRIỂN
    linhvuc_ids = fields.One2many(
        'ekids.kehoach_ketluan2linhvuc',
        'ketluan_id',
        string="Các lĩnh vực thuộc kết luận"
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

    is_readonly = fields.Boolean(compute="_compute_is_readonly")

    kehoach_ids = fields.One2many("ekids.kehoach", "ketluan_id"
                                , string="Các kế hoạch")

    def _compute_is_readonly(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_role_ketluan = user.has_group('ekids_core.ketluan')

        for record in self:
            if record.trangthai not in ['0']:
                record.is_readonly = True
            else:
                if is_admin or is_role_ketluan:
                    record.is_readonly = False
                else:
                    record.is_readonly = True

    def _compute_name(self):
        for record in self:
            record.name = string_util.date2string(record.ngay_danhgia) +"-"+ record.gv_danhgia

    def _compute_index(self):
        index = len(self)
        for record in self:
            record.index = index
            index -= 1

    def action_lap_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.kehoach_form').id

        kehoach = self.hocsinh_id.func_tao_kehoach_macdinh(self)
        if kehoach:
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',
                'views': [(form_view_id, 'form')],
                'res_id': kehoach.id,
                'target': 'current',
                'domain': [('coso_id', '=', self.coso_id.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_kehoach_id': kehoach.id,
                    'default_ketluan_id': self.id,
                    'default_hocsinh_id': self.hocsinh_id.id
                },
            }

    @api.model_create_multi
    def create(self, vals_list):
        # 1. Duyệt qua danh sách dữ liệu đầu vào (Hỗ trợ cả tạo đơn và tạo hàng loạt)

        for vals in vals_list:
            hocsinh_id = vals.get('hocsinh_id')

            if hocsinh_id:
                # 2. Sử dụng search_count để đếm nhanh số phiếu [Đang lập] của học sinh này dưới DB
                # SELECT COUNT này quét thẳng vào index nên tốc độ xử lý siêu tốc (< 5ms)
                draft_count = self.env['ekids.kehoach_ketluan'].search_count([
                    ('hocsinh_id', '=', hocsinh_id),
                    ('trangthai', '=', kehoach_util.KETLUAN_DANG_TAO)
                ])

                # 3. Chốt chặn bảo mật
                if draft_count > 0:
                    hocsinh = self.env['ekids.hocsinh'].browse(hocsinh_id)
                    raise UserError(
                        f"Học sinh [{hocsinh.name}] đang có một phiếu Kết luận ở trạng thái [Đang lập]. "
                        f"Vui lòng hoàn thiện hoặc hủy phiếu cũ trước khi tạo kết luận mới!"
                    )
            else:
                raise UserError("Không thể tạo phiếu Kết luận mới khi trường [Học sinh] đang bị bỏ trống!")

        # 4. Gọi super() DUY NHẤT MỘT LẦN ở cuối cùng để lưu hàng loạt xuống Database
        return super(KetLuan, self).create(vals_list)



    def write(self, vals):
        # 1. Chốt chặn an toàn: Chỉ tính toán nếu trường 'trangthai' thực sự nằm trong danh sách thay đổi
        if 'trangthai' in vals:
            user = self.env.user
            is_admin = user.has_group('base.group_system')

            trangthai_moi = vals.get('trangthai')

            # 2. Vòng lặp chống lỗi Multi-record (Expected singleton)
            for rec in self:
                trangthai_cu = rec.trangthai

                # Chỉ xử lý kiểm tra nếu trạng thái MỚI khác trạng thái CŨ
                if trangthai_cu != trangthai_moi:

                    # TH1: Từ [Cho phép lập KH] quay về [Đang lập] -> Check xem có kế hoạch con chưa
                    if trangthai_cu == kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH:
                        if trangthai_moi == kehoach_util.KETLUAN_DANG_TAO:
                            # Mẹo Odoo: Chỉ cần check 'if rec.kehoach_ids' thay vì dùng len() > 0 để tối ưu tốc độ
                            if rec.kehoach_ids:  # Thay bằng tên trường kế hoạch chính xác trên model của bạn
                                raise UserError(
                                    "Đã tồn tại [Kế hoạch] gắn với kết luận này, không thể chuyển ngược về trạng thái [Đang lập]!"
                                )

                    # TH2: Phiếu đã [Hết hiệu lực] -> Cấm tuyệt đối không cho bẻ lái sang trạng thái khác
                    elif trangthai_cu == kehoach_util.KETLUAN_HET_HIEULUC:
                        if is_admin == False:
                            raise UserError(
                                "Hồ sơ kết luận này đã hết hiệu lực, không thể thay đổi [Trạng thái]!"
                            )

        # 3. Gọi hàm super() ở cuối cùng sau khi đã vượt qua tất cả các tầng kiểm duyệt bảo mật
        return super(KetLuan, self).write(vals)



    def unlink(self):
        for rec in self:
            if (rec.trangthai == kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH
                    or rec.trangthai == kehoach_util.KETLUAN_HET_HIEULUC):
                raise UserError(
                    "Không cho phép xóa [Kết luận] khi đang lập kế hoạch hoặc hết hiệu lực")

        return super(KetLuan, self).unlink()