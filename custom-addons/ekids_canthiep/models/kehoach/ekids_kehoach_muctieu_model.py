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
    from odoo.addons.ekids_func import giaovien_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")




class KeHoach2MucTieu(models.Model):
    _name = 'ekids.kehoach_muctieu'
    _description = 'Các mục tiêu cho kế hoạch'
    _order = 'sequence asc,id asc'

    sequence = fields.Integer(string="STT", compute="_compute_sequence",recursive=True,store=True)
    index = fields.Integer(string="STT", default=1,compute="_compute_index")

    coso_id = fields.Many2one("ekids.coso"
                              ,related="kehoach_id.gv_lapkehoach_id.coso_id"
                              , string="Cơ sở"
                              ,required=True,
                              ondelete="restrict")

    kehoach_id = fields.Many2one("ekids.kehoach",
                                 related="kehoach_linhvuc_id.kehoach_id",
                                 string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")



    kehoach_linhvuc_id = fields.Many2one("ekids.kehoach_linhvuc",
                                 string=" Thuộc Kế hoạch Lĩnh vực nào",
                                 required=True,
                                 ondelete="cascade")

    chuongtrinh_id = fields.Many2one(
        'ekids.ct_chuongtrinh',
        related='kehoach_linhvuc_id.linhvuc_id.chuongtrinh_id',
        string='Chương trình',
        store=True,
        readonly=True,
    )

    linhvuc_id = fields.Many2one(
        'ekids.ct_linhvuc',
        related='kehoach_linhvuc_id.linhvuc_id',
        string='Lĩnh vực',
        store=True,
        readonly=True,
    )

    tuoi_id = fields.Many2one(
        'ekids.ct_tuoi',
        related='kehoach_linhvuc_id.tuoi_id',
        string='Độ tuổi',
        store=True,
        readonly=True,
    )


    name = fields.Char("Tên",compute="_compute_name")
    muctieu_them = fields.Char("Tên")




    ghichu = fields.Text(string="Ghi chú")

    chucnang = fields.Html(string="Chức năng phát triển cốt lõi & Lập luận lâm sàng",compute="_compute_chucnang")
    thietke = fields.Html(string="Thiết kế hoạt động cho giáo viên Theo mô tả (ABC)",compute="_compute_thietke")
    tieuchi_chuadat = fields.Char(string="Chưa đạt (-)",compute="_compute_tieuchi_chuadat")
    tieuchi_hinhthanh = fields.Char(string="Đang hình thành (+/-)",compute="_compute_tieuchi_hinhthanh")
    tieuchi_dat = fields.Char(string="Đạt (+)",compute="_compute_tieuchi_dat")

    muctieu_id = fields.Many2one('ekids.ct_muctieu', string='Mục tiêu', ondelete="cascade")

    chucnang_temp = fields.Html(string="Chức năng phát triển cốt lõi & Lập luận lâm sàng")
    thietke_temp = fields.Html(string="Thiết kế hoạt động cho giáo viên Theo mô tả (ABC)")

    trangthai_thietke = fields.Selection([
        ('0', 'Chưa xem'),
        ('1', 'Đưa vào [Chương trình]'),
        ('-1','Không đưa vào'),
    ], string="Trạng thái đưa thiết kế vào [Chương trình]", default='0')

    gv_lapkehoach_id = fields.Many2one(
        'ekids.giaovien',
        related='kehoach_id.gv_lapkehoach_id',
        string='giáo viên lập kế hoạch',
        store=True,
        readonly=True,
    )


    tieuchi_chuadat_temp = fields.Char(string="Chưa đạt (-)")
    tieuchi_hinhthanh_temp = fields.Char(string="Đang hình thành (+/-)")
    tieuchi_dat_temp = fields.Char(string="Đạt (+)")

    is_bientap_temp = fields.Boolean(compute="_compute_is_bientap_temp")




    # 🌟 1. TRƯỜNG ĐỨNG TRƯỚC (Predecessor - Many2one về chính mình)
    kehoach_muctieu_truoc_id = fields.Many2one(
        'ekids.kehoach_muctieu',
        string='Muc tiêu đứng trước',
        ondelete='set null'  # Chí mạng giúp triệt tiêu lỗi hệ thống
    )
    sothang_da_chuyenttiep = fields.Integer(string="Số tháng đã được chuyển tiếp sang",compute="_compute_sothang_da_chuyenttiep")
    ketqua_dat_lientiep_thangtruoc = fields.Integer(string="Kết quả can thiệp đạt liên tiêp tháng trước",
                                            compute="_compute_ketqua_dat_lientiep_thangtruoc")
    ketqua_hinhthanh_thangtruoc = fields.Integer(string="Kết quả can thiệp đạt liên tiêp tháng trước",
                                                    compute="_compute_ketqua_hinhthanh_thangtruoc")

    kehoach_muctieu_thangtruoc_id = fields.Many2one(
        'ekids.kehoach_muctieu',
        string='Muc tiêu của tháng trước chuyển sang do không đạt',
    )

    trangthai = fields.Selection([
        ("0", "Chưa can thiệp"),
        ("1", "Đạt (+)"),
        ("-1", "Đang can thiệp"),

    ], string="Trạng thái", default="0",compute="_compute_trangthai",store=False)

    is_co_thietke = fields.Boolean(compute="_compute_is_co_thietke")

    # Thêm vào Model: ekids.kehoach_muctieu
    trangthai_kiemduyet = fields.Selection([
        ('0', 'Chờ duyệt'),
        ('1', 'Đạt (+)'),
        ('-1', 'Chuyển (-)'),
        ('-2', 'Dừng (-)')
    ], string="Trạng thái kiểm duyệt chuyên môn", default='0')



    # ghi chú kiểm duyet
    ghichu_kiemduyet = fields.Html(string="Nội dung kiểm duyệt")
    dinhhuong_kiemduyet = fields.Html(string="Ý kiến/ Định hướng")



    # Hàm RPC cho GV chuyên môn click duyệt nhanh từ OWL


    ketqua2muctieu_ids = fields.One2many("ekids.kehoach_ketqua2muctieu",
                                         "kehoach_muctieu_id"
                                        , string="Thuộc kế hoạch mục tiêu nào")

    ketqua_dat= fields.Integer(string="Kết quả Đạt", compute="_compute_ketqua_dat")
    ketqua_hinhthanh= fields.Integer(string="Kết quả Đạt", compute="_compute_ketqua_hinhthanh")
    ketqua_khongdat = fields.Integer(string="Kết quả Đạt", compute="_compute_ketqua_khongdat")
    tong_ngay_cothe_canthiep = fields.Integer(string="Kết quả Đạt", compute="_compute_tong_ngay_cothe_canthiep")

    is_readonly = fields.Boolean(compute="_compute_is_readonly")
    is_delete = fields.Boolean(compute="_compute_is_delete")

    is_canthiep = fields.Boolean(compute="_compute_is_canthiep")
    is_kiemduyet = fields.Boolean(compute="_compute_is_kiemduyet")
    is_canthiep_readonly = fields.Boolean(compute="_compute_is_canthiep_readonly")
    is_kiemduyet_readonly = fields.Boolean(compute="_compute_is_kiemduyet_readonly")

    solan_thu = fields.Integer(string="Số làn thử",default=10)
    solan_thu_dat = fields.Integer(string="Số lần đạt(+)")
    tyle_thu = fields.Integer(string="Tỷ lệ %",compute="_compute_tyle_thu")

    tyle_canthiep = fields.Integer(string="Tỷ lệ đạt %", compute="_compute_tyle_canthiep")

    solan_kiemduyet_dat = fields.Integer(string="Số lần đạt(+)")
    tyle_kiemduyet = fields.Integer(string="Tỷ lệ %", compute="_compute_tyle_kiemduyet")




    @api.onchange('trangthai_kiemduyet')
    def _onchange_trangthai_kiemduyet(self):
        """Khi bấm nút Đạt (+), nếu số lần đạt đang < 80% thì tự động gợi ý mốc 8/10"""
        tong_thu = self.solan_thu if self.solan_thu > 0 else 10
        nguong_dat = int(tong_thu * 0.8)  # 80% của tổng lần thử (ví dụ 8/10)

        if self.trangthai_kiemduyet == '1':
            if self.solan_kiemduyet_dat < nguong_dat:
                self.solan_kiemduyet_dat = nguong_dat

    @api.onchange('solan_kiemduyet_dat')
    def _onchange_solan_kiemduyet_dat(self):
        """Khi nhập số lần đạt, tự động điều chỉnh tỷ lệ và đồng bộ nút bấm"""
        tong_thu = self.solan_thu if self.solan_thu > 0 else 10

        # 1. Chống nhập vượt quá tổng số lần thử
        if self.solan_kiemduyet_dat > tong_thu:
            self.solan_kiemduyet_dat = tong_thu
            return {
                'warning': {
                    'title': 'Cảnh báo số liệu',
                    'message': f'Số lần đạt không thể vượt quá tổng số lần thử ({tong_thu})!'
                }
            }
        if self.solan_kiemduyet_dat < 0:
            self.solan_kiemduyet_dat = 0

        # 2. Tính tỷ lệ %
        nguong_dat = int(tong_thu * 0.8)
        if self.solan_kiemduyet_dat >= nguong_dat:
            # Từ 80% trở lên tự động đồng bộ sang nút Đạt (+)
            self.trangthai_kiemduyet = '1'
        else:
            # Dưới 80% mà đang để Đạt (+) thì chuyển sang Chuyển (-)
            if self.trangthai_kiemduyet == '1':
                self.trangthai_kiemduyet = '-1'

    @api.constrains('trangthai_kiemduyet', 'solan_kiemduyet_dat', 'solan_thu')
    def _check_kiemduyet_dat_hople(self):
        """Ràng buộc cứng khi Lưu (Save): Đã chọn Đạt (+) thì bắt buộc >= 80%"""
        for rec in self:
            tong_thu = rec.solan_thu if rec.solan_thu > 0 else 10
            nguong_dat = int(tong_thu * 0.8)

            if rec.trangthai_kiemduyet == '1' and rec.solan_kiemduyet_dat < nguong_dat:
                raise ValidationError(
                    f"Không thể xác nhận trạng thái [Đạt (+)]!\n"
                    f"Tiêu chuẩn đánh giá lâm sàng bắt buộc đạt từ 80% trở lên.\n"
                    f"• Số lần đạt hiện tại: {rec.solan_kiemduyet_dat}/{tong_thu} ({rec.tyle_kiemduyet}%)\n"
                    f"• Yêu cầu tối thiểu: từ {nguong_dat}/{tong_thu} (≥ 80%) trở lên.\n\n"
                    f"Vui lòng điều chỉnh lại số lần đạt hoặc chọn [Chuyển (-)] / [Dừng (-)]."
                )

    @api.depends("solan_kiemduyet_dat")
    def _compute_tyle_kiemduyet(self):
        for record in self:
            tyle = 0
            if record.solan_thu > 0:
                tyle = (record.solan_kiemduyet_dat / record.solan_thu) * 100
            else:
                tyle = 0
            record.tyle_kiemduyet = tyle

    def _compute_solan_dat_lientiep(self):

        for rec in self:

            solan = rec.func_ketqua_dat_lientiep_lonnhat()
            rec.solan_dat_lientiep = solan

    def _compute_tyle_canthiep(self):
        for rec in self:
            soluong_dat_lientiep_str = coso_util.func_cauhinh_canthiep(
                self, rec.coso_id, "muctieu_soluong_dat_lientiep", "5"
            )
            soluong_dat_lientiep_quydinh = int(soluong_dat_lientiep_str)
            # Đã đạt liên tiếp đủ số ngày quy định -> lấy % trung bình chuỗi đạt '1'
            tyle = rec.func_ketqua_tyle_lientiep_lonnhat_loai("1",soluong_dat_lientiep_quydinh)
            if tyle <=0:
                # Chưa có ngày nào đạt liên tiếp -> lấy % trung bình của chuỗi ngày đang hình thành '2' (hoặc '-1')
                tyle = rec.func_ketqua_tyle_lientiep_lonnhat_loai("2",soluong_dat_lientiep_quydinh)


            rec.tyle_canthiep = int(tyle)




    @api.constrains('solan_thu', 'solan_thu_dat')
    def _check_solan_thu_hop_le(self):
        for rec in self:
            # Nếu đã nhập số lần đạt hoặc số lần thử thì bắt buộc số lần thử > 0
            if rec.solan_thu < 0 or rec.solan_thu_dat < 0:
                raise ValidationError("Số lần thử và số lần đạt (+) không được là số âm!")

            if rec.solan_thu == 0 and rec.solan_thu_dat > 0:
                raise ValidationError("Tổng số lần thử phải lớn hơn 0 khi đã có số lần đạt (+)! ")

            if rec.solan_thu_dat > rec.solan_thu:
                raise ValidationError(
                    f"Dữ liệu không hợp lệ!\n"
                    f"• Số lần đạt (+): {rec.solan_thu_dat}\n"
                    f"• Tổng số lần thử: {rec.solan_thu}\n\n"
                    f"Số lần đạt (+) không được lớn hơn tổng số lần thử."
                )

    # 2. CẢNH BÁO TỨC THÌ (ONCHANGE) KHI VỪA NHẬP TRÊN GIAO DIỆN
    @api.onchange('solan_thu', 'solan_thu_dat')
    def _onchange_check_solan_thu(self):
        if self.solan_thu < 0:
            self.solan_thu = 0
            return {
                'warning': {
                    'title': 'Cảnh báo nhập liệu',
                    'message': 'Tổng số lần thử không thể là số âm!'
                }
            }

        if self.solan_thu_dat < 0:
            self.solan_thu_dat = 0
            return {
                'warning': {
                    'title': 'Cảnh báo nhập liệu',
                    'message': 'Số lần đạt (+) không thể là số âm!'
                }
            }

        if self.solan_thu > 0 and self.solan_thu_dat > self.solan_thu:
            return {
                'warning': {
                    'title': 'Số liệu chưa hợp lệ',
                    'message': f'Số lần đạt ({self.solan_thu_dat}) đang vượt quá tổng số lần thử ({self.solan_thu})!'
                }
            }

    @api.depends("solan_thu","solan_thu_dat")
    def _compute_tyle_thu(self):
        for record in self:
            if record.solan_thu >0:
                tyle = (record.solan_thu_dat/record.solan_thu)*100
            else:
                tyle=0
            record.tyle_thu = tyle



    def _compute_is_bientap_temp(self):

        for record in self:
            is_bientap_tem = False
            if not record.muctieu_id:
                is_bientap_tem = True
            else:
                if string_util._is_html_empty(record.muctieu_id.thietke) == True:
                    is_bientap_tem = True
            record.is_bientap_temp = is_bientap_tem

    def _compute_is_kiemduyet_readonly(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        giaoviens = giaovien_util.func_get_giaoviens_tu_user(self)
        for record in self:
            is_kiemduyet_readonly = True
            if is_admin:
                is_kiemduyet_readonly = False
            else:
                kehoach = record.kehoach_id
                if kehoach:
                    gv_kiemduyet = kehoach.ketluan_id.gv_kiemduyet_id

                    if gv_kiemduyet.id in giaoviens.ids:
                        if kehoach.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                            is_kiemduyet_readonly= False

            record.is_kiemduyet_readonly = is_kiemduyet_readonly

    def _compute_is_canthiep_readonly(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for record in self:
            is_canthiep_readonly = True
            if is_admin:
                is_canthiep_readonly = False
            else:
                kehoach = record.kehoach_id
                if kehoach:
                    gv_lap = kehoach.gv_lapkehoach_id
                    if gv_lap.user_id.id == user.id:
                        if kehoach.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                            is_canthiep_readonly = False

            record.is_canthiep_readonly = is_canthiep_readonly

    @api.depends("muctieu_id")
    def _compute_is_canthiep(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        giaoviens = giaovien_util.func_get_giaoviens_tu_user(self)
        for record in self:
            is_canthiep = False
            if is_admin:
                is_canthiep = True
            else:
                kehoach = record.kehoach_id
                if kehoach:
                    gv_kiemduyet = kehoach.ketluan_id.gv_kiemduyet_id
                    gv_lap = kehoach.gv_lapkehoach_id
                    if gv_kiemduyet.id in giaoviens.ids:
                        #if record.trangthai == '1':
                        is_canthiep = True
                    elif gv_lap.user_id.id == user.id:
                        is_canthiep = True

            record.is_canthiep = is_canthiep

    @api.depends("kehoach_linhvuc_id.is_readonly")
    def _compute_is_kiemduyet(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        giaoviens = giaovien_util.func_get_giaoviens_tu_user(self)
        for record in self:
            is_kiemduyet = False
            if is_admin:
                is_kiemduyet = True
            else:
                kehoach = record.kehoach_id
                if kehoach:
                    gv_kiemduyet = kehoach.ketluan_id.gv_kiemduyet_id
                    gv_lap = kehoach.gv_lapkehoach_id
                    if gv_kiemduyet.id in giaoviens.ids:
                        #if record.trangthai == "1":
                         is_kiemduyet = True
                    elif gv_lap.user_id.id == user.id:
                        if record.trangthai_kiemduyet != "0":
                            is_kiemduyet = True

            record.is_kiemduyet = is_kiemduyet

    @api.depends("kehoach_linhvuc_id.is_readonly")
    def _compute_is_delete(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        giaoviens = giaovien_util.func_get_giaoviens_tu_user(self)
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
                    if giaovien.id in giaoviens.ids:
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

    def _compute_ketqua_dat_lientiep_thangtruoc(self):
        for mt in self:
            ketqua_dat_lientiep_thangtruoc = 0
            muctieu_thangtruoc = mt.kehoach_muctieu_thangtruoc_id
            if muctieu_thangtruoc:
                ketqua_dat_lientiep_thangtruoc =muctieu_thangtruoc.func_ketqua_dat_lientiep_lonnhat()
            mt.ketqua_dat_lientiep_thangtruoc = ketqua_dat_lientiep_thangtruoc


    def _compute_ketqua_hinhthanh_thangtruoc(self):
        for mt in self:
            ketqua_hinhthanh_thangtruoc =0
            muctieu_thangtruoc = mt.kehoach_muctieu_thangtruoc_id
            if muctieu_thangtruoc:
                muctieu_thangtruoc._compute_ketqua_hinhthanh()
                ketqua_hinhthanh_thangtruoc = muctieu_thangtruoc.ketqua_hinhthanh
            mt.ketqua_hinhthanh_thangtruoc = ketqua_hinhthanh_thangtruoc



    @api.depends('ketqua2muctieu_ids', 'ketqua2muctieu_ids.trangthai')
    def _compute_trangthai(self):
        today = date.today()
        for mt in self:
            kehoach = mt.kehoach_id
            is_chophep_canthiep = False
            if kehoach.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                if today >= kehoach.tu_ngay:
                    soluong_str = coso_util.func_cauhinh_canthiep(self, kehoach.coso_id, "muctieu_soluong_mo", "2")
                    is_chophep_canthiep = mt.func_is_chophep_canthiep(int(soluong_str))
            elif kehoach.trangthai == kehoach_util.KEHOACH_HET_HIEULUC:
                    is_chophep_canthiep = True # Cho phep xem lai

            if is_chophep_canthiep == False:
                #TH1: Chua cho can thiep
                mt.trangthai = "0"
            else:
                #TH2: Da cho can thiep
                soluong_dat_lientiep_str = coso_util.func_cauhinh_canthiep(self, kehoach.coso_id, "muctieu_soluong_dat_lientiep", "5")

                ketqua_dat_lientiep= mt.func_ketqua_dat_lientiep_lonnhat()
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

    def func_ketqua_dat_lientiep_lonnhat(self):
        self.ensure_one()
        today = date.today()
        # Lấy từ cache recordset và sắp xếp tăng dần theo ngày
        kqs = [
            kq for kq in self.ketqua2muctieu_ids
            if kq.ngay and fields.Date.to_date(kq.ngay) <= today and kq.loai == '1'
        ]
        kqs.sort(key=lambda x: fields.Date.to_date(x.ngay))

        max_len = 0
        cur_len = 0
        for kq in kqs:
            if kq.trangthai == '1':
                cur_len += 1
                if cur_len > max_len:
                    max_len = cur_len
            else:
                cur_len = 0
        return max_len

    def func_ketqua_tyle_lientiep_lonnhat_loai(self, trangthai,solan_macdinh):
        self.ensure_one()
        today = date.today()
        kqs = [
            kq for kq in self.ketqua2muctieu_ids
            if kq.ngay and fields.Date.to_date(kq.ngay) <= today and kq.loai == '1'
        ]
        kqs.sort(key=lambda x: fields.Date.to_date(x.ngay))

        max_len = 0
        best_tong_tyle = 0
        cur_len = 0
        cur_tong_tyle = 0
        target_str = str(trangthai)

        for kq in kqs:
            if str(kq.trangthai) == target_str:
                cur_len += 1
                cur_tong_tyle += kq.tyle_thu
                if cur_len > max_len:
                    max_len = cur_len
                    best_tong_tyle = cur_tong_tyle
            else:
                # Reset sạch sẽ cả 2 biến tạm khi đứt gãy chuỗi
                cur_len = 0
                cur_tong_tyle = 0

        if (max_len < solan_macdinh and trangthai =="1"):
            max_len = solan_macdinh
        ketqua = round(best_tong_tyle / max_len) if max_len > 0 else 0

        return ketqua


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
                    if (ketqua.trangthai == "1"
                            and ketqua.loai =='1'):
                        tong += 1
            mt.ketqua_dat=tong

    @api.depends('ketqua2muctieu_ids', 'ketqua2muctieu_ids.trangthai')
    def _compute_ketqua_khongdat(self):
        for mt in self:
            tong = 0
            ketquas = mt.ketqua2muctieu_ids
            if ketquas:

                for ketqua in ketquas:
                    if (ketqua.trangthai =="-1"
                            and ketqua.loai =='1'):
                        tong += 1
            mt.ketqua_khongdat=tong

    @api.depends('ketqua2muctieu_ids', 'ketqua2muctieu_ids.trangthai')
    def _compute_ketqua_hinhthanh(self):
        for mt in self:
            tong = 0
            ketquas = mt.ketqua2muctieu_ids
            if ketquas:

                for ketqua in ketquas:
                    if (ketqua.trangthai == "2"
                            and ketqua.loai =='1'):
                        tong += 1
            mt.ketqua_hinhthanh=tong

    @api.depends('ketqua2muctieu_ids', 'ketqua2muctieu_ids.trangthai')
    def _compute_tong_ngay_cothe_canthiep(self):
        for mt in self:
            mt.tong_ngay_cothe_canthiep = mt.kehoach_id.songay

        # 🌟 BẮT BUỘC: Khai báo các trường phụ thuộc để kích hoạt compute khi tạo mới/chỉnh sửa
    @api.depends('muctieu_id','muctieu_them', 'muctieu_id.sequence', 'kehoach_muctieu_truoc_id',
                 'kehoach_muctieu_truoc_id.sequence')
    def _compute_sequence(self):
        for mt in self:
            if mt.muctieu_id:
                mt.sequence =mt.muctieu_id.sequence
            else:
                if mt.kehoach_muctieu_truoc_id:
                    mt.sequence = mt.kehoach_muctieu_truoc_id.sequence
                else:
                    mt.sequence = 0

    def func_is_chophep_canthiep(self, index):
        cur_mt = self.kehoach_muctieu_truoc_id
        if not cur_mt:
            return True

        coso = self.kehoach_id.coso_id
        tyle_dat_str = coso_util.func_cauhinh_canthiep(self, coso, "muctieu_tyle_dat", "80")
        nguong_dat = int(tyle_dat_str)
        steps = index

        while cur_mt and steps > 1:
            if cur_mt.trangthai == "1":
                return True
            if cur_mt.func_ketqua_tyle_canthiep() >= nguong_dat:
                return True
            steps -= 1
            cur_mt = cur_mt.kehoach_muctieu_truoc_id

        return False

    



    # 2. Viết hàm xử lý thuật toán phân nhóm và reset số thứ tự

    def _compute_index(self):
        index =1
        for mt in self:
            mt.index =index
            index +=1


    def _compute_name(self):
        for mt in self:
            if mt.muctieu_id:
                mt.name =mt.muctieu_id.name
            else:
                mt.name =mt.muctieu_them


    # 1. COMPUTE CHỨC NĂNG (Kiểu HTML)
    @api.depends('muctieu_id', 'muctieu_id.chucnang', 'chucnang_temp')
    def _compute_chucnang(self):
        for mt in self:
            if (mt.muctieu_id
                    and string_util._is_html_empty(mt.muctieu_id.chucnang) == False):
                mt.chucnang = mt.muctieu_id.chucnang
            else:
                mt.chucnang = mt.chucnang_temp or ''

    # 2. COMPUTE THIẾT KẾ (Kiểu HTML)
    @api.depends('muctieu_id', 'muctieu_id.thietke', 'thietke_temp')
    def _compute_thietke(self):
        for mt in self:
            if (mt.muctieu_id
                    and string_util._is_html_empty(mt.muctieu_id.thietke)== False):
                mt.thietke = mt.muctieu_id.thietke
            else:
                mt.thietke = mt.thietke_temp or ''

    # 3. COMPUTE TIÊU CHÍ CHƯA ĐẠT (Kiểu Char)
    @api.depends('muctieu_id', 'muctieu_id.tieuchi_chuadat', 'tieuchi_chuadat_temp')
    def _compute_tieuchi_chuadat(self):
        for mt in self:
            if (mt.muctieu_id
                    and string_util._is_char_empty(mt.muctieu_id.tieuchi_chuadat) == False):
                mt.tieuchi_chuadat = mt.muctieu_id.tieuchi_chuadat
            else:
                mt.tieuchi_chuadat = mt.tieuchi_chuadat_temp or ''

    # 4. COMPUTE TIÊU CHÍ ĐANG HÌNH THÀNH (Kiểu Char)
    @api.depends('muctieu_id', 'muctieu_id.tieuchi_hinhthanh', 'tieuchi_hinhthanh_temp')
    def _compute_tieuchi_hinhthanh(self):
        for mt in self:
            if (mt.muctieu_id
                    and string_util._is_char_empty(mt.muctieu_id.tieuchi_hinhthanh) == False):
                mt.tieuchi_hinhthanh = mt.muctieu_id.tieuchi_hinhthanh
            else:
                mt.tieuchi_hinhthanh = mt.tieuchi_hinhthanh_temp or ''

    # 5. COMPUTE TIÊU CHÍ ĐẠT (Kiểu Char)
    @api.depends('muctieu_id', 'muctieu_id.tieuchi_dat', 'tieuchi_dat_temp')
    def _compute_tieuchi_dat(self):
        for mt in self:
            if (mt.muctieu_id
                    and string_util._is_char_empty(mt.muctieu_id.tieuchi_dat)==False):
                mt.tieuchi_dat = mt.muctieu_id.tieuchi_dat
            else:
                mt.tieuchi_dat = mt.tieuchi_dat_temp or ''

    def action_canthiep(self):
        form_view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_capnhat_ketqua_form').id
        self._compute_is_canthiep_readonly()
        is_canthiep_readonly = self.is_canthiep_readonly
        self.func_khoitao_ketqua2muctieu()
        url= {
            'type': 'ir.actions.act_window',
            'name': 'KẾT QUẢ CAN THIỆP',
            'res_model': 'ekids.kehoach_muctieu',
            'view_mode': 'form',
            'res_id':self.id,
            'views': [(form_view_id, 'form')],
            'target': 'new',

        }
        if is_canthiep_readonly == True:
            url["context"] = {
                'create': False,
                'edit': False,  # Ẩn hoặc vô hiệu hóa hoàn toàn nút "Sửa" (Edit) ngoài giao diện
                'delete': False,  # Ẩn nút "Xóa"
            }
        return url


    def action_kiemduyet(self):
        form_view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_kiemduyet_ketqua_form').id
        self._compute_is_kiemduyet_readonly()
        is_kiemduyet_readonly = self.is_kiemduyet_readonly
        url ={
            'type': 'ir.actions.act_window',
            'name': 'XÁC NHẬN KẾT QUẢ CAN THIỆP',
            'res_model': 'ekids.kehoach_muctieu',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(form_view_id, 'form')],
            'target': 'new',

        }
        if is_kiemduyet_readonly == True:
            url["context"] = {
                    'create': False,
                    'edit': False,   # Ẩn hoặc vô hiệu hóa hoàn toàn nút "Sửa" (Edit) ngoài giao diện
                    'delete': False, # Ẩn nút "Xóa"
                }
        return  url

    def action_donglai_ve_kehoach(self):
        """ Hàm nằm ở chân Form View giúp đóng popup và ép màn hình OWL cha reload dữ liệu """
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}


    def func_khoitao_ketqua2muctieu(self):
        # 1. Chuẩn hóa ngày hiện tại (Nên dùng context_today để đúng múi giờ người dùng Odoo)
        ketqua2muctieus =self.ketqua2muctieu_ids
        coso = self.kehoach_id.coso_id
        today =fields.Date.today()
        # TH1: Đã tạo kết quả trước đây:
        if ketqua2muctieus:
            last_ketqua2muctieu = None
            for ketqua2muctieu in ketqua2muctieus:
                ngay =  fields.Date.to_date(ketqua2muctieu.ngay)
                if (ngay <today
                        and ketqua2muctieu.trangthai in ['1','-1','2']
                        and ketqua2muctieu.is_giaovien_capnhat == True): # phai la giao vien tu cap nhat
                    last_ketqua2muctieu = ketqua2muctieu
            #TON TAI ban ghi cuoi co ngay:
            soluong_dat_lientiep_str = coso_util.func_cauhinh_canthiep(self, coso, "muctieu_soluong_dat_lientiep", "5")
            max_lientiep_dat = self.func_ketqua_dat_lientiep_lonnhat()

            if last_ketqua2muctieu:
                last_ngay =fields.Date.to_date(last_ketqua2muctieu.ngay)
                next_ngay = last_ngay + timedelta(days=3)
                # ngay cap nhat 3 ngay tức chỉ tự động 3 ngày tiếp theo thôi

                for ketqua2muctieu in ketqua2muctieus:
                    ngay = fields.Date.to_date(ketqua2muctieu.ngay)
                    if (ngay >last_ngay
                        and ngay<= next_ngay):# tinh toan đến tận hôm nay
                       if ketqua2muctieu.trangthai == '0':
                           if max_lientiep_dat < int(soluong_dat_lientiep_str):
                               ketqua2muctieu.write({
                                   'trangthai': last_ketqua2muctieu.trangthai,
                                   'solan_thu_dat': last_ketqua2muctieu.solan_thu_dat,
                                   'is_giaovien_capnhat': False,
                               })




        else:
            #TH2: Lần đầu click

            today = fields.Date.context_today(self)
            # 2. Ép kiểu an toàn về Date, triệt tiêu hoàn toàn lỗi Datetime vs Date
            tu_ngay = fields.Date.to_date(self.kehoach_id.tu_ngay)
            den_ngay = fields.Date.to_date(self.kehoach_id.den_ngay)

            datas = []
            current_date =tu_ngay

            while current_date <= den_ngay:
                data ={
                    "kehoach_muctieu_id": self.id,
                    "ngay": current_date,
                    "trangthai": "0"
                }
                datas.append(data)
                current_date += timedelta(days=1)

            # 5. Bulk Create: Đẩy toàn bộ mảng vào Database trong 1 câu query duy nhất
            if datas and len(datas)>0:
                self.env['ekids.kehoach_ketqua2muctieu'].create(datas)

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

    def action_giaovien_bientap_thietke_muctieu(self):
        form_view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_bientap_thietke_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'BIÊN TẬP NỘI DUNG THIẾT KÉ CAN THIỆP CHO MỤC TIÊU',
            'res_model': 'ekids.kehoach_muctieu',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'res_id': self.id,
            'target': 'new',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'default_linhvuc_id': self.linhvuc_id.id,
                'default_tuoi_id': self.tuoi_id.id
            },
        }

    def action_thietke_muctieu_vao_truongtrinh(self):
        setattr(self,"trangthai_thietke","1")
        url = self.kehoach_id.coso_id.action_kiemduyet_noidung_thietke()
        return url

    def action_thietke_muctieu_khongvao_truongtrinh(self):
        for record  in self:
            setattr(record,"trangthai_thietke","-1")
        url = self.kehoach_id.coso_id.action_kiemduyet_noidung_thietke()
        return url

    def action_xem_chitiet_muctieu(self):
        self.ensure_one()
        ct_muctieu = self.muctieu_id
        if ct_muctieu:
            form_view_id = self.env.ref('ekids_canthiep.ct_muctieu_form').id

            return {
                'type': 'ir.actions.act_window',
                'name': 'NỘI DUNG MỤC TIÊU TRONG CHƯƠNG TRÌNH',
                'res_model': 'ekids.ct_muctieu',
                'res_id': ct_muctieu.id,  # 🌟 BẮT BUỘC có res_id để mở đúng bản ghi mục tiêu
                'view_mode': 'form',
                'views': [(form_view_id, 'form')],
                'target': 'new',  # Mở dạng Pop-up
                'flags': {
                    'mode': 'readonly',  # 🌟 Ép view mở thẳng ở chế độ Readonly
                },
                'context': {
                    'form_view_initial_mode': 'readonly',  # 🌟 Khóa chế độ khởi tạo form là Readonly
                    'edit': False,  # 🚫 Tắt nút Edit
                    'create': False,  # 🚫 Tắt nút Create
                    'delete': False,  # 🚫 Tắt nút Delete
                },
            }

    def _compute_is_co_thietke(self):
        for mt in self:
            is_co_thietke = False
            if string_util._is_html_empty(mt.chucnang) == False:
                is_co_thietke = True
            if string_util._is_html_empty(mt.thietke) == False:
               is_co_thietke = True
            if string_util._is_char_empty(mt.tieuchi_chuadat) == False:
                is_co_thietke = True
            if string_util._is_char_empty(mt.tieuchi_hinhthanh) == False:
                is_co_thietke = True
            if string_util._is_char_empty(mt.tieuchi_dat) == False:
                is_co_thietke = True

            mt.is_co_thietke = is_co_thietke



    @api.model_create_multi
    def create(self, vals_list):
        # 1. Gọi hàm tạo của super để lấy về toàn bộ recordset được tạo ra
        records = super(KeHoach2MucTieu, self).create(vals_list)

        # 2. Duyệt qua từng bản ghi vừa tạo thành công để cập nhật nghiệp vụ liên quan
        if records and len(records)>0:
            kehoach_linhvuc = records[0].kehoach_linhvuc_id
            kehoach_linhvuc.func_capnhat_kehoach_muctieu_truoc()

        return records

    def write(self, vals):
        self.func_capnhat_thietke_vao_chuongtrinh(vals)
        res = super(KeHoach2MucTieu, self).write(vals)
        return res


    def func_capnhat_thietke_vao_chuongtrinh(self,vals):

        context = self.env.context
        bientap_thietke_muctieu = context.get("default_duyet_bientap_chuongtrinh")
        if bientap_thietke_muctieu == '1':
            if 'trangthai_thietke' in vals:
                if vals['trangthai_thietke'] == '1':
                    ct_muctieu = self.muctieu_id
                    if ct_muctieu:
                        is_update = self.is_role_dua_vao_chuongtrinh()
                        if (string_util._is_html_empty(self.thietke_temp) == False
                                and is_update == True):
                            data = {
                                'thietke': self.thietke_temp,
                                'is_gv_bientap': True
                            }
                            if string_util._is_html_empty(self.chucnang_temp) == False:
                                data['chucnang'] = self.chucnang_temp

                            if string_util._is_char_empty(self.tieuchi_chuadat_temp) == False:
                                data['tieuchi_chuadat'] = self.tieuchi_chuadat_temp

                            if string_util._is_char_empty(self.tieuchi_hinhthanh_temp) == False:
                                data['tieuchi_hinhthanh'] = self.tieuchi_hinhthanh_temp

                            if string_util._is_char_empty(self.tieuchi_dat_temp) == False:
                                data['tieuchi_dat'] = self.tieuchi_dat_temp

                            ct_muctieu.write(data)



    def is_role_dua_vao_chuongtrinh(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_ql_ct = user.has_group('ekids_core.ql_ct_canthiep')
        is_ketluan = user.has_group('ekids_core.ketluan')
        if (is_admin == True
                or is_ql_ct == True
                or is_ketluan == True):
            return True
        else:
            return False

    def action_capnhat_tyle_thu(self):
        self.ensure_one()
        view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_bientap_tyle_thu_form').id
        return {
            'name': 'Kết quả [Thử] trước khi lập kế hoạch',
            'type': 'ir.actions.act_window',
            'res_model': 'ekids.kehoach_muctieu',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': self.env.context,
        }




    def unlink(self):
        kehoach_linhvuc = self.kehoach_linhvuc_id
        result= super().unlink()

        if kehoach_linhvuc:
            kehoach_linhvuc.func_capnhat_kehoach_muctieu_truoc()
        return result







