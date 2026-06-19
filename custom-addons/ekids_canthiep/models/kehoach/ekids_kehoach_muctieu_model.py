from odoo import models, fields, api
from datetime import  timedelta,date
from odoo.exceptions import ValidationError, UserError


class KeHoach2MucTieu(models.Model):
    _name = 'ekids.kehoach_muctieu'
    _description = 'Các mục tiêu cho kế hoạch'
    _order = 'id desc'

    sequence = fields.Integer(string="STT", compute="_compute_sequence")
    index = fields.Integer(string="STT", default=1,compute="_compute_index")

    kehoach_id = fields.Many2one("ekids.kehoach",
                                 related="kehoach_linhvuc_id.kehoach_id",
                                 string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")

    kehoach_linhvuc_id = fields.Many2one("ekids.kehoach_linhvuc",
                                 string=" Thuộc Kế hoạch Lĩnh vực nào",
                                 required=True,
                                 ondelete="cascade")

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc',
                                 related="muctieu_id.linhvuc_id", string='Lĩnh vực', required=True, ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi',
                              related="muctieu_id.tuoi_id", required=True, ondelete="cascade")

    name = fields.Char("Tên",compute="_compute_name")
    chucnang = fields.Html(string="Chức năng phát triển cốt lõi & Lập luận lâm sàng",compute="_compute_chucnang")
    thietke = fields.Html(string="Thiết kế hoạt động cho giáo viên Theo mô tả (ABC)",compute="_compute_thietke")
    tieuchi_chuadat = fields.Char(string="Chưa đạt (-)",compute="_compute_tieuchi_chuadat")
    tieuchi_hinhthanh = fields.Char(string="Đang hình thành (+/-)",compute="_compute_tieuchi_hinhthanh")
    tieuchi_dat = fields.Char(string="Đạt (+)",compute="_compute_tieuchi_dat")

    muctieu_id = fields.Many2one('ekids.ct_muctieu', string='Mục tiêu', required=True, ondelete="cascade")

    trangthai = fields.Selection([
        ("0", "Chưa can thiệp"),
        ("1", "Đạt (+)"),
        ("-1", "Chưa đạt (-)"),

    ], string="Trạng thái", default="0")

    ketqua2muctieu_ids = fields.One2many("ekids.kehoach_ketqua2muctieu", "kehoach_muctieu_id"
                                        , string="Thuộc kế hoạch mục tiêu nào")

    def _compute_sequence(self):
        for mt in self:
            mt.sequence =mt.muctieu_id.sequence

    # 2. Viết hàm xử lý thuật toán phân nhóm và reset số thứ tự

    def _compute_index(self):
        index =1
        for mt in self:
            mt.index =index
            index +=1

    def _compute_name(self):
        for mt in self:
            mt.name =mt.muctieu_id.name

    def _compute_chucnang(self):
        for mt in self:
            mt.chucnang =mt.muctieu_id.chucnang
    def _compute_thietke(self):
        for mt in self:
            mt.thietke =mt.muctieu_id.thietke

    def _compute_tieuchi_chuadat(self):
        for mt in self:
            mt.tieuchi_chuadat =mt.muctieu_id.tieuchi_chuadat

    def _compute_tieuchi_hinhthanh(self):
        for mt in self:
            mt.tieuchi_hinhthanh =mt.muctieu_id.tieuchi_hinhthanh

    def _compute_tieuchi_dat(self):
        for mt in self:
            mt.tieuchi_dat =mt.muctieu_id.tieuchi_dat

    def action_canthiep(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_muctieu_form').id

        self.func_khoitao_ketqua2muctieu()
        return {
            'type': 'ir.actions.act_window',
            'name': 'KẾT QUẢ CAN THIỆP',
            'res_model': 'ekids.kehoach_muctieu',
            'view_mode': 'form',
            'res_id':self.id,
            'views': [(form_view_id, 'form')],
            'target': 'new',

        }

    def action_donglai_ve_kehoach(self):
        """ Hàm nằm ở chân Form View giúp đóng popup và ép màn hình OWL cha reload dữ liệu """
        self.ensure_one()

        # Phòng hờ bốc ID kế hoạch từ trường dữ liệu hoặc từ context ẩn của hệ thống
        hocsinh = self.kehoach_id.hocsinh_id

        if not hocsinh:
            # Nếu không tìm thấy ID kế hoạch, đóng popup đơn thuần để tránh sập trang
            return {'type': 'ir.actions.act_window_close'}

        return {
            'type': 'ir.actions.client',
            'tag': 'ekids_canthiep.kehoach_canthiep_action',

            # 🌟 THAM SỐ CHÍ MẠNG: Ép phá vỡ Modal Dialog để làm mới không gian làm việc chính
            'target': 'main',

            'context': {
                'active_id': hocsinh.id,
                'kehoach_id': hocsinh.id,
            }
        }

    def func_khoitao_ketqua2muctieu(self):
        # 1. Chuẩn hóa ngày hiện tại (Nên dùng context_today để đúng múi giờ người dùng Odoo)
        today = fields.Date.context_today(self)

        # 2. Ép kiểu an toàn về Date, triệt tiêu hoàn toàn lỗi Datetime vs Date
        tu_ngay = fields.Date.to_date(self.kehoach_id.tu_ngay)
        den_ngay = fields.Date.to_date(self.kehoach_id.den_ngay)

        if not tu_ngay or not den_ngay:
            raise UserError("Kế hoạch chưa thiết lập đủ Từ ngày và Đến ngày.")

        if today <tu_ngay:
            raise UserError("Kế hoạch chưa đến thời gian can thiệp")

        # 3. Tìm ngày bắt đầu chạy vòng lặp (Dùng max() thay cho if-else cho ngắn gọn)
        current_date = max(tu_ngay, today)

        # =========================================================================
        # BƯỚC TỐI ƯU HIỆU SUẤT (Senior Level):
        # Thay vì query Database mỗi ngày trong vòng lặp, ta lấy hết 1 lần.
        # =========================================================================

        # Tìm tất cả các kết quả đã sinh ra trong khoảng thời gian này (Chỉ tốn 1 query)
        ketqua_da_co = self.env['ekids.kehoach_ketqua2muctieu'].search_read([
            ('kehoach_muctieu_id', '=', self.id),
            ('ngay', '>=', current_date),
            ('ngay', '<=', den_ngay)
        ], ['ngay'])

        # Tạo một mảng chứa các ngày đã tồn tại để đối chiếu
        danh_sach_ngay_da_co = [fields.Date.to_date(kq['ngay']) for kq in ketqua_da_co]

        # Khởi tạo mảng trống để chứa data chuẩn bị tạo mới
        vals_list = []

        # 4. Quét vòng lặp để lọc ra các ngày chưa có
        while current_date <= den_ngay:
            if current_date not in danh_sach_ngay_da_co:
                vals_list.append({
                    "kehoach_muctieu_id": self.id,
                    "ngay": current_date,
                })
            current_date += timedelta(days=1)

        # 5. Bulk Create: Đẩy toàn bộ mảng vào Database trong 1 câu query duy nhất
        if vals_list:
            self.env['ekids.kehoach_ketqua2muctieu'].create(vals_list)






