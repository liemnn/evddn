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
    ghichu = fields.Text(string="Ghi chú")

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
        ondelete='set null'  # Chí mạng giúp triệt tiêu lỗi hệ thống
    )
    sothang_da_chuyenttiep = fields.Integer(string="Số tháng đã được chuyển tiếp sang",compute="_compute_sothang_da_chuyenttiep")
    kehoach_muctieu_thangtruoc_id = fields.Many2one(
        'ekids.kehoach_muctieu',
        string='Muc tiêu của tháng trước chuyển sang do không đạt',
    )

    trangthai = fields.Selection([
        ("0", "Chưa can thiệp"),
        ("1", "Đạt (+)"),
        ("-1", "Đang can thiệp"),

    ], string="Trạng thái", default="0",compute="_compute_trangthai",store=False)

    # Thêm vào Model: ekids.kehoach_muctieu
    trangthai_kiemduyet = fields.Selection([
        ('0', 'Chờ duyệt'),
        ('1', 'Đạt (+)'),
        ('-1', 'Chuyển (-)'),
        ('-2', 'Dừng (-)')
    ], string="Trạng thái kiểm duyệt chuyên môn", default='0')

    # ghi chú kiểm duyet
    ghichu_kiemduyet = fields.Html(string="Nội dung kiểm duyệt")



    # Hàm RPC cho GV chuyên môn click duyệt nhanh từ OWL


    ketqua2muctieu_ids = fields.One2many("ekids.kehoach_ketqua2muctieu", "kehoach_muctieu_id"
                                        , string="Thuộc kế hoạch mục tiêu nào")

    ketqua_dat= fields.Integer(string="Kết quả Đạt", compute="_compute_ketqua_dat")
    ketqua_hinhthanh= fields.Integer(string="Kết quả Đạt", compute="_compute_ketqua_hinhthanh")
    ketqua_khongdat = fields.Integer(string="Kết quả Đạt", compute="_compute_ketqua_khongdat")

    is_readonly = fields.Boolean(compute="_compute_is_readonly")
    is_delete = fields.Boolean(compute="_compute_is_delete")

    is_canthiep = fields.Boolean(compute="_compute_is_canthiep")
    is_kiemduyet = fields.Boolean(compute="_compute_is_kiemduyet")

    @api.depends("kehoach_linhvuc_id.is_readonly")
    def _compute_is_canthiep(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for record in self:
            is_canthiep = False
            if is_admin:
                is_canthiep = True
            else:
                giaoviens =  record.kehoach_id.ketluan_id.gv_canthiep_ids
                user_ids = giaoviens.mapped('user_id').ids
                if user.id in user_ids:
                    is_canthiep = True
            record.is_canthiep = is_canthiep

    @api.depends("kehoach_linhvuc_id.is_readonly")
    def _compute_is_kiemduyet(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for record in self:
            is_kiemduyet = False
            if is_admin:
                is_kiemduyet = True
            else:
                giaovien = record.kehoach_id.ketluan_id.gv_kiemduyet_id
                if giaovien.user_id.id == user.id:
                    is_kiemduyet = True
            record.is_kiemduyet = is_kiemduyet

    @api.depends("kehoach_linhvuc_id.is_readonly")
    def _compute_is_delete(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for record in self:
            is_delete = False
            if is_admin:
                is_delete = True
            else:
                kehoach = record.kehoach_id
                #TH1: Đang lập kế hoạch và ko phải là tháng trước chuyển sang thì cho phép xoa
                if (kehoach.trangthai == kehoach_util.KEHOACH_DANG_LAP
                        or kehoach.trangthai_pheduyet==kehoach_util.PHEDUYET_CAN_DIEUCHINH):
                    if not record.kehoach_muctieu_thangtruoc_id:
                        giaoviens = kehoach.ketluan_id.gv_canthiep_ids
                        user_ids = giaoviens.mapped('user_id').ids
                        if user.id in user_ids:
                            is_delete = True
                # TH2: Đagn phê duyệt thì người duoc xóa thoải mái
                if kehoach.trangthai == kehoach_util.KEHOACH_DANG_PHEDUYET:
                    giaovien = kehoach.ketluan_id.gv_kiemduyet_id
                    if giaovien.user_id.id == user.id:
                        is_delete = True

            record.is_delete = is_delete

    def _compute_is_readonly(self):
        for record in self:
            record.is_readonly = record.kehoach_linhvuc_id.is_readonly

    def _compute_sothang_da_chuyenttiep(self):
        today = date.today()
        for mt in self:
            so_thang =0
            if mt.kehoach_muctieu_thangtruoc_id:
                so_thang = mt.kehoach_muctieu_thangtruoc_id.sothang_da_chuyenttiep +1
            mt.sothang_da_chuyenttiep=so_thang

    @api.depends('ketqua2muctieu_ids', 'ketqua2muctieu_ids.trangthai')
    def _compute_trangthai(self):
        today = date.today()
        for mt in self:
            kehoach = mt.kehoach_id
            is_chophep_canthiep = False
            if kehoach.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                if today >= kehoach.tu_ngay and today <= kehoach.den_ngay:
                    soluong_str = coso_util.func_cauhinh_canthiep(self, kehoach.coso_id, "muctieu_soluong_mo", "2")
                    is_chophep_canthiep = mt.func_is_chophep_canthiep(int(soluong_str))

            if is_chophep_canthiep == False:
                #TH1: Chua cho can thiep
                mt.trangthai = "0"
            else:
                #TH2: Da cho can thiep
                soluong_dat_lientiep_str = coso_util.func_cauhinh_canthiep(self, kehoach.coso_id, "muctieu_soluong_dat_lientiep", "6")

                ketqua_dat_lientiep= mt.func_ketqua_dat_lientiep()
                if ketqua_dat_lientiep >= int(soluong_dat_lientiep_str):
                    mt.trangthai="1"
                else:
                    mt.trangthai = "-1"




    def action_owl_review_approve(self):
        for rec in self:
            rec.state_review = 'approved'
        return True

    def action_owl_review_reject(self):
        for rec in self:
            rec.state_review = 'rejected'
        return True


    def func_ketqua_dat_lientiep(self):
        today =date.today()
        max = 0
        current_max = 0

        # 🌟 BƯỚC QUY HOẠCH CHÍ MẠNG: Ép sắp xếp danh sách kết quả tịnh tiến theo ngày tăng dần
        # Sử dụng sorted() của Python giúp chạy mượt mà trên RAM mà không cần Re-query SQL
        ketquas = self.ketqua2muctieu_ids
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

        return max


    def func_ketqua_tyle_canthiep(self):
        today = date.today()
        kqs = self.ketqua2muctieu_ids
        tyle=0
        if kqs:
            tong =len(kqs)
            tong_ct =0
            for kq in kqs:
                if (kq.trangthai !="0"
                        and kq.ngay<=today):
                    tong_ct +=1
            tyle = int((tong_ct/tong)*100)
        return tyle

    @api.depends('ketqua2muctieu_ids', 'ketqua2muctieu_ids.trangthai')
    def _compute_ketqua_dat(self):
        for mt in self:
            tong = 0
            ketquas = mt.ketqua2muctieu_ids
            if ketquas:

                for ketqua in ketquas:
                    if ketqua.trangthai =="1":
                        tong += 1
            mt.ketqua_dat=tong

    @api.depends('ketqua2muctieu_ids', 'ketqua2muctieu_ids.trangthai')
    def _compute_ketqua_khongdat(self):
        for mt in self:
            tong = 0
            ketquas = mt.ketqua2muctieu_ids
            if ketquas:

                for ketqua in ketquas:
                    if ketqua.trangthai =="-1":
                        tong += 1
            mt.ketqua_khongdat=tong

    @api.depends('ketqua2muctieu_ids', 'ketqua2muctieu_ids.trangthai')
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


    def func_is_chophep_canthiep(self,index):
        muctieu_truoc = self.kehoach_muctieu_truoc_id
        coso = muctieu_truoc.kehoach_id.coso_id

        if not muctieu_truoc:
            return True
        elif muctieu_truoc.trangthai=="1":
            # trang thai truoc đã đạt
            return True
        else:
            if index <= 1:
                return False
            else:
                tyle_dat_str = coso_util.func_cauhinh_canthiep(self, coso, "muctieu_tyle_dat", "80")
                ketqua_tyle_canthiep = muctieu_truoc.func_ketqua_tyle_canthiep()
                if ketqua_tyle_canthiep >= int(tyle_dat_str):
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

    def action_kiemduyet(self):
        form_view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_kiemduyet_ketqua_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'XÁC NHẬN KẾT QUẢ CAN THIỆP',
            'res_model': 'ekids.kehoach_muctieu',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(form_view_id, 'form')],
            'target': 'new',

        }

    def action_donglai_ve_kehoach(self):
        """ Hàm nằm ở chân Form View giúp đóng popup và ép màn hình OWL cha reload dữ liệu """
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}


    def func_khoitao_ketqua2muctieu(self):
        # 1. Chuẩn hóa ngày hiện tại (Nên dùng context_today để đúng múi giờ người dùng Odoo)
        coso = self.kehoach_id.coso_id
        today = fields.Date.context_today(self)

        # 2. Ép kiểu an toàn về Date, triệt tiêu hoàn toàn lỗi Datetime vs Date
        tu_ngay = fields.Date.to_date(self.kehoach_id.tu_ngay)
        den_ngay = fields.Date.to_date(self.kehoach_id.den_ngay)


        if not tu_ngay or not den_ngay:
            raise UserError("Kế hoạch chưa thiết lập đủ Từ ngày và Đến ngày.")

        if today <tu_ngay:
            raise UserError("Kế hoạch chưa đến thời gian can thiệp")

        # 3. Tìm ngày bắt đầu chạy vòng lặp (Dùng max() thay cho if-else cho ngắn gọn)
        current_date = tu_ngay

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
        so_ngay_conlai = (den_ngay -today).days
        chuadat_str = coso_util.func_cauhinh_canthiep(self, coso,
                                                                   "muctieu_tyle_macdinh_chuadat", "6")
        hinhthanh_str = coso_util.func_cauhinh_canthiep(self, coso,
                                                                   "muctieu_tyle_macdinh_hinhthanh", "6")
        dat_str = coso_util.func_cauhinh_canthiep(self, coso,
                                                                   "muctieu_tyle_macdinh_dat", "6")

        index_chuadat = int((so_ngay_conlai/100) * int(chuadat_str))
        index_hinhthanh = int((so_ngay_conlai/100) * int(hinhthanh_str))


        while current_date <= den_ngay:
            if current_date not in danh_sach_ngay_da_co:
                if current_date <today:
                    vals_list.append({
                        "kehoach_muctieu_id": self.id,
                        "ngay": current_date,
                        "trangthai": "0"
                    })
                else:
                    if index_chuadat >0:
                        trangthai="-1"
                        index_chuadat -=1
                    elif index_hinhthanh >0:
                        trangthai="2"
                        index_hinhthanh -=1
                    else:
                        trangthai = "1"
                    vals_list.append({
                        "kehoach_muctieu_id": self.id,
                        "ngay": current_date,
                        "trangthai": trangthai
                    })

            current_date += timedelta(days=1)

        # 5. Bulk Create: Đẩy toàn bộ mảng vào Database trong 1 câu query duy nhất
        if vals_list:
            self.env['ekids.kehoach_ketqua2muctieu'].create(vals_list)

    def action_open_target_note(self):
        """ Hàm xử lý mở Popup khi click vào nút ghi chú từ HTML """
        # Lấy target_id được truyền từ context bên trong mã HTML
        target_id = self.env.context.get('target_id')
        if not target_id:
            return False

        # Khởi tạo bản ghi mục tiêu cụ thể
        target_record = self.env['ekids.kehoach_muctieu'].browse(target_id)

        # Trả về action dạng popup ('target': 'new')
        return {
            'name': f"Ghi chú mục tiêu: {target_record.muctieu_id.name or ''}",
            'type': 'ir.actions.act_window',
            'res_model': 'ekids.kehoach_muctieu',
            'res_id': target_record.id,
            'view_mode': 'form',
            # Điền ID của form view nhỏ gọn dùng để nhập ghi chú (Xem ở bước 3)
            'views': [(self.env.ref('ekids_canthiep.kehoach_muctieu_form_view_compact').id, 'form')],
            'target': 'new',
            'context': self.env.context,
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            result = super(KeHoach2MucTieu, self).create(vals)
            if result:
                kehoach_linhvuc = result.kehoach_linhvuc_id
                if kehoach_linhvuc:
                    kehoach_linhvuc.func_capnhat_kehoach_muctieu_truoc()
        return records[0] if len(records) == 1 else records



    def unlink(self):
        kehoach_linhvuc = self.kehoach_linhvuc_id
        result= super().unlink()

        if kehoach_linhvuc:
            kehoach_linhvuc.func_capnhat_kehoach_muctieu_truoc()
        return result







