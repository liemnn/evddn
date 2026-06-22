from odoo import models, fields, api
from datetime import  timedelta,date
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")




class KeHoach2MucTieu(models.Model):
    _name = 'ekids.kehoach_muctieu'
    _description = 'Các mục tiêu cho kế hoạch'
    _order = 'sequence asc,id desc'

    sequence = fields.Integer(string="STT", compute="_compute_sequence",store=True)
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

    # 🌟 1. TRƯỜNG ĐỨNG TRƯỚC (Predecessor - Many2one về chính mình)
    kehoach_muctieu_truoc_id = fields.Many2one(
        'ekids.kehoach_muctieu',
        string='Muc tiêu đứng trước',
    )
    kehoach_muctieu_thangtruoc_id = fields.Many2one(
        'ekids.kehoach_muctieu',
        string='Muc tiêu của tháng trước chuyển sang do không đạt',
    )

    trangthai = fields.Selection([
        ("0", "Chưa can thiệp"),
        ("1", "Đạt (+)"),
        ("-1", "Chưa đạt (-)"),

    ], string="Trạng thái", default="0")

    is_chophep_canthiep = fields.Boolean(string="cho phép can thiệp hay không",compute="_compute_is_chophep_canthiep")


    ketqua2muctieu_ids = fields.One2many("ekids.kehoach_ketqua2muctieu", "kehoach_muctieu_id"
                                        , string="Thuộc kế hoạch mục tiêu nào")

    ketqua_dat= fields.Integer(string="Kết quả Đạt", compute="_compute_ketqua_dat")
    ketqua_hinhthanh= fields.Integer(string="Kết quả Đạt", compute="_compute_ketqua_hinhthanh")
    ketqua_khongdat = fields.Integer(string="Kết quả Đạt", compute="_compute_ketqua_khongdat")
    ketqua_dat_lientiep = fields.Integer(string="Kết quả Đạt liên tiếp", compute="_compute_ketqua_dat_lientiep")

    @api.depends('ketqua2muctieu_ids', 'ketqua2muctieu_ids.trangthai')
    def _compute_ketqua_dat_lientiep(self):
        today =date.today()
        for mt in self:
            max = 0
            current_max = 0

            # 🌟 BƯỚC QUY HOẠCH CHÍ MẠNG: Ép sắp xếp danh sách kết quả tịnh tiến theo ngày tăng dần
            # Sử dụng sorted() của Python giúp chạy mượt mà trên RAM mà không cần Re-query SQL
            ketquas = mt.ketqua2muctieu_ids
            if ketquas:
                for kq in ketquas:
                    if kq.ngay > today:
                        continue
                    # Nếu trạng thái bằng '1' (Đạt) dạng chuỗi hoặc số nguyên tùy cấu hình database của anh
                    if kq.trangthai == '1':
                        current_max += 1
                        # Cập nhật lại chuỗi dài nhất nếu chuỗi hiện tại vượt mốc cũ
                        if current_max > max:
                            max = current_max
                    else:
                        # Đứt gãy chuỗi đạt liên tiếp -> Reset bộ đếm tạm thời về 0
                        current_max = 0

                # Gán kết quả chuỗi kỷ lục tìm được vào trường compute
            mt.ketqua_dat_lientiep = max
            soluong_dat_lientiep_str = coso_util.func_cauhinh_canthiep(self, mt.kehoach_id.coso_id, "muctieu_soluong_dat_lientiep","6")
            if max >= int(soluong_dat_lientiep_str):
                mt.trangthai ="1"
            else:
                mt.trangthai = "-1"


    def _compute_ketqua_dat(self):
        for mt in self:
            tong = 0
            ketquas = mt.ketqua2muctieu_ids
            if ketquas:

                for ketqua in ketquas:
                    if ketqua.trangthai =="1":
                        tong += 1
            mt.ketqua_dat=tong

    def _compute_ketqua_khongdat(self):
        for mt in self:
            tong = 0
            ketquas = mt.ketqua2muctieu_ids
            if ketquas:

                for ketqua in ketquas:
                    if ketqua.trangthai =="-1":
                        tong += 1
            mt.ketqua_khongdat=tong

    def _compute_ketqua_hinhthanh(self):
        for mt in self:
            tong = 0
            ketquas = mt.ketqua2muctieu_ids
            if ketquas:

                for ketqua in ketquas:
                    if ketqua.trangthai =="0":
                        tong += 1
            mt.ketqua_hinhthanh=tong


    def _compute_sequence(self):
        for mt in self:
            mt.sequence =mt.muctieu_id.sequence

    def _compute_is_chophep_canthiep(self):
        today =date.today()

        for mt in self:
            kehoach =mt.kehoach_id
            is_chophep_canthiep = False
            if kehoach.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                if today >= kehoach.tu_ngay and today <=kehoach.den_ngay:
                    soluong_str = coso_util.func_cauhinh_canthiep(self,kehoach.coso_id,"muctieu_soluong_mo","2")
                    is_chophep_canthiep = mt.func_is_chophep_canthiep(int(soluong_str))
            mt.is_chophep_canthiep = is_chophep_canthiep
            if is_chophep_canthiep and mt.trangthai=="0":
                mt.trangthai="-1"

    def func_is_chophep_canthiep(self,index):
        if not self.kehoach_muctieu_truoc_id:
            return True
        elif self.kehoach_muctieu_truoc_id.trangthai=="1":
            # trang thai truoc đã đạt
            return True
        else:
            if index <=1:
                return False
            elif self.trangthai == "1":
                return True
            else:
                index = index -1
                muctieu= self.kehoach_muctieu_truoc_id
                return muctieu.func_is_chophep_canthiep(index)



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
        form_view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_capnhat_ketqua_form').id

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






