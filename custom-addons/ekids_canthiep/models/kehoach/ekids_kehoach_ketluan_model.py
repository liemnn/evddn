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

    dm_mucdo_id = fields.Many2one('ekids.ct_dm_mucdo', string='Mức độ', ondelete="restrict")


    dm_lieuluong_id = fields.Many2one('ekids.ct_dm_lieuluong', string='Liều lượng', ondelete="restrict")
    # 3. ĐỊNH HƯỚNG CAN THIỆP

    hinhthuc = fields.Char(string="Hình thức [Can thiệp]")

    dm_phuongphap_id = fields.Many2one('ekids.ct_dm_phuongphap', string='Phương pháp', ondelete="restrict")


    kythuat = fields.Char(string="Kỹ thuật can thiệp")

    # 4. LỊCH HẸN

    dm_lichhen_id = fields.Many2one('ekids.ct_dm_lichhen', string='Lịch hẹn', ondelete="restrict")


    # 5. BẢNG CHI TIẾT ĐỘ TUỔI PHÁT TRIỂN
    linhvuc_ids = fields.One2many(
        'ekids.kehoach_ketluan2linhvuc',
        'ketluan_id',
        string="Các lĩnh vực thuộc kết luận"
    )  #



    dm_gv_danhgia_id = fields.Many2one('ekids.ct_dm_cg_danhgia', string='Chuyên gia đánh giá', ondelete="restrict")

    ngay_danhgia= fields.Date(string="Ngày đánh giá")
    desc = fields.Html(string="Ghi chú")


    gv_kiemduyet_id = fields.Many2one('ekids.giaovien'
                                      , string="Giáo viên [Kiểm duyệt chuyên môn]", required=True)

    gv_canthiep_ids = fields.Many2many(comodel_name="ekids.giaovien"
                                       , relation="ekids_kehoach_giaovien2ketluan_rel"
                                       , column1="ketluan_id"
                                       , column2="giaovien_id"
                                       , string="Phân công [Lập kế hoạch/Can thiệp]")

    is_readonly = fields.Boolean(compute="_compute_is_readonly")

    kehoach_ids = fields.One2many("ekids.kehoach", "ketluan_id"
                                , string="Các kế hoạch")

    tong_kehoach = fields.Integer(string="Tổng kế hoạch",compute="_compute_tong_kehoach")

    # Đổi kiểu dữ liệu từ Char sang Html
    linhvucs = fields.Html(string="Lĩnh vực can thiệp", compute="_compute_linhvucs")

    # Giữ nguyên trường kiểu Text để không bị sinh thẻ <p> rác
    linhvucs = fields.Text(string="Lĩnh vực can thiệp", compute="_compute_linhvucs")

    # 1. Định nghĩa lại trường Many2many kèm theo thuộc tính compute và store=True
    chuongtrinh_ids = fields.Many2many(
        comodel_name="ekids.ct_chuongtrinh",
        relation="ekids_kehoach_ketluan2chuongtrinh_rel",
        column1="ketluan_id",
        column2="chuongtrinh_id",
        string="Chương trình can thiệp",
        compute="_compute_chuongtrinh_ids",
        store=False  # Lưu vào DB để bộ lọc (Filter) và Bản in QWeb truy xuất nhanh hơn
    )

    chuongtrinh = fields.Char(string="Tên chương trình", compute="_compute_chuongtrinh")

    # 2. Viết hàm tính toán tự động phụ thuộc vào bảng chi tiết
    @api.depends('linhvuc_ids.chuongtrinh_id')
    def _compute_chuongtrinh_ids(self):
        for record in self:
            # Lấy toàn bộ text tên chương trình từ bảng chi tiết, dùng set() để lọc trùng
            chuongtrinh_ids = set()
            if record.linhvuc_ids:
                for line in record.linhvuc_ids:
                    if line.chuongtrinh_id:
                        # strip() để xóa khoảng trắng thừa nếu chuyên gia gõ tay bị lệch
                        chuongtrinh_ids.add(line.chuongtrinh_id.id)

            if chuongtrinh_ids:
                # Tìm kiếm các bản ghi danh mục chương trình tương ứng với tập hợp tên trên
                # Dùng toán tử 'in' để tìm kiếm hàng loạt, tối ưu tốc độ xử lý phần cứng
                chuongtrinh_records = self.env['ekids.ct_chuongtrinh'].search([
                    ('id', 'in', list(chuongtrinh_ids))
                ])
                # Gán trực tiếp Recordset tìm được vào trường Many2many
                record.chuongtrinh_ids = chuongtrinh_records
            else:
                # Nếu bảng chi tiết trống, làm sạch trường Many2many (xóa hết tag)
                record.chuongtrinh_ids = [(5, 0, 0)]

    def _compute_linhvucs(self):
        for record in self:
            lines = []
            if record.linhvuc_ids:
                for lv in record.linhvuc_ids:
                    name = lv.linhvuc_id.name if lv.linhvuc_id else ""
                    tuoi = lv.tuoi_id.name if lv.tuoi_id else ""
                    # Thêm dấu gạch đầu dòng vào định dạng cấu trúc chuỗi
                    lines.append(f"- {name} ({tuoi})")

            # Nối các dòng lại với nhau bằng ký tự xuống dòng \n
            record.linhvucs = "\n".join(lines) if lines else ""

    def _compute_chuongtrinh(self):
        for record in self:
            name =""
            chuongtrinh_ids = record.chuongtrinh_ids
            if chuongtrinh_ids:
                for ct in chuongtrinh_ids:
                    if name == "":
                        name = ct.title
                    else:
                        name = name +", "+ct.title
            record.chuongtrinh = name

    def _compute_tong_kehoach(self):
        for record in self:
            if record.kehoach_ids:
                record.tong_kehoach = len(record.kehoach_ids)
            else:
                record.tong_kehoach = 0
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
            name = string_util.date2string(record.ngay_danhgia)
            if record.dm_gv_danhgia_id:
                name= name +"-" + record.dm_gv_danhgia_id.name
            record.name=name
    def _compute_index(self):
        index = len(self)
        for record in self:
            record.index = index
            index -= 1

    def action_lap_kehoach(self):


        kehoach = self.hocsinh_id.func_tao_kehoach_macdinh(self)
        if kehoach:
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',

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
        user = self.env.user
        is_admin = user.has_group('base.group_system')
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
                            if is_admin == False:
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
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for rec in self:
            if is_admin == False:
                if (rec.trangthai == kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH
                        or rec.trangthai == kehoach_util.KETLUAN_HET_HIEULUC):
                    raise UserError(
                        "Không cho phép xóa [Kết luận] khi đang lập kế hoạch hoặc hết hiệu lực")

        return super(KetLuan, self).unlink()



    def action_chon_copy_ketluan(self):
        default_hocsinh_id = self.env.context.get("default_hocsinh_id")
        default_ketluan_id = self.env.context.get("default_ketluan_id")
        self.func_copy_ketluan_tu_nguon(default_ketluan_id,default_hocsinh_id)
        return None

    def func_copy_ketluan_tu_nguon(self, ketluan_nguon_id, hocsinh_id):
        """
        Hàm copy thông tin từ một kết luận nguồn sang một kết luận mới cho học sinh chỉ định.
        Cập nhật: Tương thích hoàn toàn với các trường danh mục Many2one và cơ chế compute tự động.
        :param ketluan_nguon_id: ID hoặc record của kết luận gốc (nguon)
        :param hocsinh_id: ID của học sinh nhận kết luận mới
        :return: Record kết luận mới được tạo ra
        """
        # 1. Đảm bảo lấy đúng bản ghi nguồn (Hỗ trợ truyền vào dạng ID hoặc Bản ghi)
        source = self.browse(ketluan_nguon_id) if isinstance(ketluan_nguon_id, int) else ketluan_nguon_id
        if not source.exists():
            raise UserError("Không tìm thấy dữ liệu kết luận nguồn để sao chép!")

        if not hocsinh_id:
            raise UserError("Vui lòng chỉ định Học sinh nhận dữ liệu sao chép!")

        # 2. Chuẩn bị dữ liệu cho các trường cơ bản và trường Many2one / Many2many mới
        vals = {
            'hocsinh_id': hocsinh_id,
            'trangthai': '0',  # Luôn để trạng thái mặc định ban đầu là 'Đang soạn thảo' (KETLUAN_DANG_TAO)

            # --- CẬP NHẬT: Ánh xạ chuẩn sang các trường Many2one mới ---
            'dm_mucdo_id': source.dm_mucdo_id.id if source.dm_mucdo_id else False,
            'dm_lieuluong_id': source.dm_lieuluong_id.id if source.dm_lieuluong_id else False,
            'dm_phuongphap_id': source.dm_phuongphap_id.id if source.dm_phuongphap_id else False,
            'dm_lichhen_id': source.dm_lichhen_id.id if source.dm_lichhen_id else False,
            'dm_gv_danhgia_id': source.dm_gv_danhgia_id.id if source.dm_gv_danhgia_id else False,

            # --- Giữ nguyên các trường Text/Html/Char cơ bản ---
            'hinhthuc': source.hinhthuc,
            'kythuat': source.kythuat,
            'desc': source.desc,
            'ngay_danhgia': source.ngay_danhgia or fields.Date.today(),  # Nếu nguồn trống thì lấy ngày hôm nay
            'gv_kiemduyet_id': source.gv_kiemduyet_id.id if source.gv_kiemduyet_id else False,

            # --- Copy các quan hệ Many2many bằng Command SET (6) ---
            'dm_roiloan_ids': [(6, 0, source.dm_roiloan_ids.ids)],
            'gv_canthiep_ids': [(6, 0, source.gv_canthiep_ids.ids)],

            # Ghi chú: Bỏ qua chuongtrinh_ids vì trường này là compute store=False,
            # hệ thống sẽ tự sinh thông qua bảng chi tiết linhvuc_ids phía dưới.
        }

        # 3. Nhân bản dữ liệu chi tiết của bảng One2many (linhvuc_ids)
        # Sử dụng lệnh [(0, 0, values)] để tạo mới hoàn toàn các dòng chi tiết phụ thuộc vào bản ghi cha mới
        linhvuc_lines = []
        for line in source.linhvuc_ids:
            linhvuc_lines.append((0, 0, {
                # Giữ nguyên trường ẩn nếu có hoặc bỏ sequence nếu không sử dụng
                'sequence': getattr(line, 'sequence', 0),
                'chuongtrinh_id': line.chuongtrinh_id.id if line.chuongtrinh_id else False,
                'linhvuc_id': line.linhvuc_id.id if line.linhvuc_id else False,
                'tuoi_id': line.tuoi_id.id if line.tuoi_id else False,
            }))

        if linhvuc_lines:
            vals['linhvuc_ids'] = linhvuc_lines

        # 4. Thực hiện tạo mới kết luận (Sẽ đi qua hàm chặn trùng create đã có sẵn của bạn)
        try:
            new_ketluan = self.create([vals])  # Bọc dạng list để tối ưu hóa theo phương thức @api.model_create_multi
            return new_ketluan
        except Exception as e:
            _logger.error(f"Lỗi xảy ra khi thực hiện sao chép kết luận: {str(e)}")
            raise UserError(f"Quá trình sao chép kết luận thất bại: {str(e)}")