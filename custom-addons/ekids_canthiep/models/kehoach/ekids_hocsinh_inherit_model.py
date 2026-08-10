from odoo import models, fields, api, exceptions
from datetime import  timedelta,date,datetime
from odoo.exceptions import UserError


from .ekids_hocsinh_kehoach_action_abstractmodel import HocSinhKeHoachActionAbstractModel

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



class HocSinhInherit(models.Model
    ,HocSinhKeHoachActionAbstractModel):
    _inherit = "ekids.hocsinh"

    trangthai_ketluan = fields.Selection([
        (kehoach_util.KETLUAN_CHUA_CO, "Chưa có"),
        (kehoach_util.KETLUAN_DANG_TAO, "Đang soạn thảo"),
        (kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH, "Cho phép lập [Kế hoạch]"),
        (kehoach_util.KETLUAN_HET_HIEULUC, "Hết hiệu lực lập [Kế hoạch]"),

    ],compute="_compute_trangthai_ketluan"
    ,string="Trạng thái")

    trangthai_kehoach = fields.Selection([
        (kehoach_util.HOCSINH_CHUA_CO_KEHOACH, "Chưa có"),
        (kehoach_util.HOCSINH_DANG_LAP_KEHOACH, "Đang lập"),
        (kehoach_util.HOCSINH_DANG_CANTHIEP, "Đang can thiệp"),
        (kehoach_util.HOCSINH_HET_HIEULUC, "Hết hiệu lực"),
        (kehoach_util.HOCSINH_DA_DUYET, "Đã duyệt"),
        (kehoach_util.HOCSINH_DOI_DUYET, "Đợi duyệt"),
        (kehoach_util.HOCSINH_CAN_DIEUCHINH, "Cần chỉnh sửa"),


    ],string="Trạng thái kế hoạch",compute="_compute_trangthai_kehoach")







    kehoach_ids = fields.One2many("ekids.kehoach",
             "hocsinh_id", string="Các kế hoạch can thệp của học sinh")

    ketluan_ids = fields.One2many("ekids.kehoach_ketluan",
                                  "hocsinh_id", string="Kết luận")


    is_tao_ketluan = fields.Boolean(compute="_compute_is_tao_ketluan",compute_sudo=False)
    is_sua_ketluan = fields.Boolean(compute="_compute_is_sua_ketluan", compute_sudo=False)
    is_lap_kehoach = fields.Boolean(compute="_compute_is_lap_kehoach",compute_sudo=False)
    is_sua_kehoach = fields.Boolean(compute="_compute_is_sua_kehoach",compute_sudo=False)
    is_kiemduyet = fields.Boolean(compute="_compute_is_kiemduyet",compute_sudo=False)
    is_canthiep = fields.Boolean(compute="_compute_is_canthiep",compute_sudo=False)

    tong_ketluan = fields.Integer(compute="_compute_tong_ketluan", string="Số lượng")
    tong_kehoach = fields.Integer(compute="_compute_tong_kehoach",string="Số lượng")

    tong_kehoach_doiduyet = fields.Integer(compute="_compute_tong_kehoach_doiduyet", string="Số lượng đợi duyệt")
    ngay_guiduyet = fields.Char(string="Ngày [Gửi duyệt]",compute="_compute_tong_kehoach_doiduyet")
    ten_kehoach = fields.Char(string="Kế hoạch tháng", compute="_compute_ten_kehoach")

    ngay_duyet = fields.Char(string="Ngày [Duyệt]", compute="_compute_tong_kehoach_doiduyet")


    tong_kehoach_taomoi = fields.Integer(compute="_compute_tong_kehoach_taomoi", string="Số lượng đã tạo")
    tong_kehoach_dang_canthiep = fields.Integer(compute="_compute_tong_kehoach_dang_canthiep", string="Số lượng đang can thiêp")
    tong_kehoach_da_canthiep = fields.Integer(compute="_compute_tong_kehoach_da_canthiep",string="Số [Kế hoạch] Đã can thiệp")

    ngay_conlai_kehoach = fields.Integer(compute="_compute_ngay_conlai_kehoach",string="Ngày còn lại [Kế hoạch]")


    def _compute_ngay_conlai_kehoach(self):
        today = date.today()
        for hs in self:
            so_ngay = 0
            if hs.kehoach_ids:
                if hs.kehoach_ids:
                    for kh in hs.kehoach_ids:
                        if kh.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                            so_ngay = (kh.den_ngay - today).days
                            if so_ngay <= 0:
                                so_ngay=0
            hs.ngay_conlai_kehoach = so_ngay


    def _compute_tong_ketluan(self):
        for hs in self:
            if hs.ketluan_ids:
                hs.tong_ketluan = len(hs.ketluan_ids)
            else:
                hs.tong_ketluan = 0

    def _compute_tong_kehoach(self):
        for hs in self:
            if hs.kehoach_ids:
                hs.tong_kehoach = len(hs.kehoach_ids)
            else:
                hs.tong_kehoach = 0

    def _compute_tong_kehoach_doiduyet(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        giaovien = giaovien_util.func_get_giaovien_tu_user(self)
        for hs in self:
            if hs.kehoach_ids:
                tong =0
                ngay = None
                if hs.kehoach_ids:
                    for kh in hs.kehoach_ids:
                        if (kh.trangthai == kehoach_util.KEHOACH_DANG_PHEDUYET
                            and kh.trangthai_pheduyet == kehoach_util.PHEDUYET_DOI_DUYET):
                            if kh.ngay_guiduyet:
                                ngay = kh.ngay_guiduyet
                            else:
                                ngay = kh.write_date

                            if is_admin:
                                tong +=1
                            elif (kh.ketluan_id.gv_kiemduyet_id.id == giaovien.id):
                                tong +=1

                hs.tong_kehoach_doiduyet = tong
                hs.ngay_guiduyet = string_util.date2string_format(ngay,'%d/%m/%Y')

            else:
                hs.tong_kehoach_doiduyet = 0
                hs.ngay_guiduyet = None

    def _compute_ten_kehoach(self):
        for hs in self:
            ten_kehoach=""
            if hs.kehoach_ids:
                tu_ngay = None
                for kehoach in hs.kehoach_ids:
                    if not tu_ngay:
                        tu_ngay = kehoach.tu_ngay
                        ten_kehoach = kehoach.name
                    else:
                        if tu_ngay < kehoach.tu_ngay:
                            tu_ngay = kehoach.tu_ngay
                            ten_kehoach = kehoach.name


            hs.ten_kehoach = ten_kehoach



   


    def _compute_tong_kehoach_taomoi(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        giaovien = giaovien_util.func_get_giaovien_tu_user(self
                                                           )
        for hs in self:
            if hs.kehoach_ids:
                tong = 0
                if is_admin:
                    tong = len(hs.kehoach_ids)
                else:
                    if hs.kehoach_ids:
                        for kh in hs.kehoach_ids:
                            if kh.gv_lapkehoach_id.id == giaovien.id:
                                tong +=1
                hs.tong_kehoach_taomoi = tong
            else:
                hs.tong_kehoach_taomoi = 0

    def _compute_tong_kehoach_dang_canthiep(self):
        today = date.today()
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        context_type = self.env.context.get("default_context_type","-1")
        giaovien = giaovien_util.func_get_giaovien_tu_user(self)
        for hs in self:
            if hs.kehoach_ids:
                tong =0
                if hs.kehoach_ids:
                    for kh in hs.kehoach_ids:
                        if kh.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                            if today>= kh.tu_ngay:

                                if context_type =="2":
                                    #TH: Kiem duyet
                                    if is_admin:
                                        tong += 1
                                    elif (kh.ketluan_id.gv_kiemduyet_id.id == giaovien.id):
                                        tong += 1
                                elif context_type =="3":
                                    #TH can thiep
                                    if is_admin:
                                        tong += 1
                                    elif (kh.gv_lapkehoach_id.id == giaovien.id):
                                        tong +=1


                hs.tong_kehoach_dang_canthiep = tong
            else:
                hs.tong_kehoach_dang_canthiep = 0

    def _compute_tong_kehoach_da_canthiep(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        giaovien = giaovien_util.func_get_giaovien_tu_user(self)
        for hs in self:
            if hs.kehoach_ids:
                tong =0
                if hs.kehoach_ids:
                    for kh in hs.kehoach_ids:
                        if (kh.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP
                                or kh.trangthai == kehoach_util.KEHOACH_HET_HIEULUC):
                            if is_admin:
                                tong += 1
                            elif (kh.gv_lapkehoach_id.id == giaovien.id):
                                tong += 1
                hs.tong_kehoach_da_canthiep = tong
            else:
                hs.tong_kehoach_da_canthiep = 0


    def _compute_is_tao_ketluan(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_role_ketluan = user.has_group('ekids_core.ketluan')

        is_taomoi= False
        if is_admin or is_role_ketluan:
            is_taomoi = True

        for hs in self:
            trangthais =[kehoach_util.KETLUAN_DANG_TAO]
            count = kehoach_util.func_count_ketluan_hocsinh_trangthai(self,hs,trangthais)
            if count>0:
                hs.is_tao_ketluan = False

            else:
                hs.is_tao_ketluan = is_taomoi


    def _compute_is_sua_ketluan(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        for rec in self:
            # Bước 1: Mặc định ban đầu là không cho sửa
            is_sua_ketluan = False

            ketluan_danglap = kehoach_util.func_get_ketluan_hocsinh_trangthai(self, rec,
                                                                          [kehoach_util.KETLUAN_DANG_TAO])
            if ketluan_danglap:
                if is_admin:
                    is_sua_ketluan = True
                else:
                    is_ketluan = user.has_group('ekids_core.ketluan')
                    if is_ketluan:
                        is_sua_ketluan =True
            rec.is_sua_ketluan =is_sua_ketluan


    def _compute_is_lap_kehoach(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for hs in self:
            trangthais = [kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH]
            ketluan = kehoach_util.func_get_ketluan_hocsinh_trangthai(self,hs,trangthais)
            is_lap_kehoach = False
            if ketluan:
                trangthais =[kehoach_util.KEHOACH_DANG_LAP
                                ,kehoach_util.KEHOACH_DANG_PHEDUYET,kehoach_util.KEHOACH_DANG_CANTHIEP]
                kehoach_count = kehoach_util.func_count_kehoach_hocsinh_trangthai(self,hs,trangthais)
                if kehoach_count <=0:

                    giaoviens = ketluan.gv_canthiep_ids
                    if giaoviens:
                        user_ids = giaoviens.mapped('user_id').ids
                        if user.id in user_ids:
                            is_lap_kehoach = True
            hs.is_lap_kehoach = is_lap_kehoach



    def _compute_is_sua_kehoach(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        for rec in self:
            # Bước 1: Mặc định ban đầu là không cho sửa
            rec.is_sua_kehoach = False
            target_kehoach = None

            # Bước 2: Tìm kế hoạch thỏa mãn điều kiện quy trình
            # Ưu tiên 1: Tìm kế hoạch "Đang lập"
            kh_dang_lap = kehoach_util.func_get_kehoach_hocsinh_trangthai(self, rec, [kehoach_util.KEHOACH_DANG_LAP])

            if kh_dang_lap:
                target_kehoach = kh_dang_lap
            else:
                # Ưu tiên 2: Nếu không có "Đang lập", tìm "Đợi duyệt" nhưng phải ở trạng thái "Cần điều chỉnh"
                kh_doi_duyet = kehoach_util.func_get_kehoach_hocsinh_trangthai(self, rec,
                                                                               [kehoach_util.KEHOACH_DANG_PHEDUYET])
                # Check an toàn tránh lỗi sập hệ thống bằng cách kiểm tra kh_doi_duyet có tồn tại hay không trước
                if kh_doi_duyet and kh_doi_duyet.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH:
                    target_kehoach = kh_doi_duyet

            # Bước 3: Nếu tìm thấy kế hoạch hợp lệ, tiến hành kiểm tra quyền hạn của người dùng
            if target_kehoach:

                if is_admin:
                    rec.is_sua_kehoach = True
                else:
                    giaoviens = target_kehoach.ketluan_id.gv_canthiep_ids
                    user_ids = giaoviens.mapped('user_id').ids
                    if giaoviens and user.id in user_ids:
                        rec.is_sua_kehoach = True

    def _compute_is_kiemduyet(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for hs in self:
            is_kiemduyet = False
            trangthais =[kehoach_util.KEHOACH_DANG_PHEDUYET]
            kehoach = kehoach_util.func_get_kehoach_can_kiemduyet_hocsinh_trangthai(self,hs,trangthais)
            if kehoach:
                if kehoach.trangthai_pheduyet == kehoach_util.PHEDUYET_DOI_DUYET:
                    if is_admin:
                        is_kiemduyet = True
                    else:
                        giaovien = kehoach.ketluan_id.gv_kiemduyet_id
                        if giaovien.user_id.id == user.id:
                            is_kiemduyet = True
            hs.is_kiemduyet = is_kiemduyet






    def _compute_is_canthiep(self):
        today = date.today()
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        today =date.today()
        for hs in self:
            # LƯU Ý SỐNG CÒN: Luôn gán mặc định False đầu vòng lặp cho từng học sinh
            # để tránh lỗi lọt điều kiện không gán dữ liệu của Odoo Compute
            is_canthiep = False
            trangthais=[kehoach_util.KEHOACH_DANG_CANTHIEP]
            kehoach = kehoach_util.func_get_kehoach_can_canthiep_hocsinh_trangthai_ngay(self,hs, trangthais,today)

            if kehoach:
                # --- ÉP KIỂU NGÀY AN TOÀN TUYỆT ĐỐI (DATE VS DATETIME) ---
                tu_ngay = kehoach.tu_ngay.date() if isinstance(kehoach.tu_ngay, datetime) else kehoach.tu_ngay
                den_ngay = kehoach.den_ngay.date() if isinstance(kehoach.den_ngay, datetime) else kehoach.den_ngay


                # Kiểm tra khoảng thời gian hiệu lực (Đảm bảo các ô ngày không bị False/Rỗng)
                if tu_ngay and tu_ngay <= today:

                    # Phân quyền xử lý gán kết quả True
                    if is_admin:
                        is_canthiep = True
                    else:

                        giaoviens = kehoach.ketluan_id.gv_canthiep_ids
                        # Phòng thủ kiểm tra chắc chắn để tránh lỗi sập hệ thống (Null Pointer) khi chưa chọn giáo viên
                        if giaoviens:
                            user_ids = giaoviens.mapped('user_id').ids
                            if user_ids and user.id in user_ids:
                                is_canthiep = True
                        else:
                            giaovien = kehoach.ketluan_id.gv_kiemduyet_id
                            if giaovien and giaovien.user_id and giaovien.user_id.id == user.id:
                                # cho phép giáo viên vào kiểm duyệt
                                is_canthiep = True
            hs.is_canthiep = is_canthiep






    def _compute_trangthai_ketluan(self):
        today =date.today()
        for hs in self:
            ketluan = kehoach_util.func_get_ketluan_hocsinh(self,hs)

            if not ketluan:
                hs.trangthai_ketluan= kehoach_util.KETLUAN_CHUA_CO
            else:
                hs.trangthai_ketluan =ketluan.trangthai





    def _compute_trangthai_kehoach(self):
        # Lấy ngày hôm nay chuẩn dạng date
        today = date.today()
        context_type = self.env.context.get("default_context_type")

        for hs in self:
            kehoach = kehoach_util.func_get_kehoach_hocsinh(self,hs)
            trangthai = ""

            if context_type == "1":
                # TH1: Lập kế hoạch:
                if not kehoach:
                    trangthai = kehoach_util.HOCSINH_CHUA_CO_KEHOACH
                else:
                    if not kehoach:
                        trangthai = kehoach_util.HOCSINH_CHUA_CO_KEHOACH
                    else:
                        # --- ÉP KIỂU NGÀY AN TOÀN TRÁNH LỖI DATETIME VS DATE ---
                        if kehoach.trangthai == kehoach_util.KEHOACH_DANG_LAP:
                            trangthai = kehoach_util.HOCSINH_DANG_LAP_KEHOACH

                        elif kehoach.trangthai == kehoach_util.KEHOACH_DANG_PHEDUYET:
                            if kehoach.trangthai_pheduyet == kehoach_util.PHEDUYET_DOI_DUYET:
                                trangthai = kehoach_util.HOCSINH_DOI_DUYET
                            elif kehoach.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH:
                                trangthai = kehoach_util.HOCSINH_CAN_DIEUCHINH
                            else:
                                # Đã duyệt -> Chuyển trạng thái học sinh thành ĐÃ DUYỆT
                                trangthai = kehoach_util.HOCSINH_DANG_CANTHIEP
                        else:

                            if kehoach.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                                trangthai = kehoach_util.HOCSINH_DANG_CANTHIEP
                            elif kehoach.trangthai == kehoach_util.KEHOACH_HET_HIEULUC:
                                trangthai = kehoach_util.HOCSINH_HET_HIEULUC
            else:
                if kehoach.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                    if today < kehoach.tu_ngay:
                        trangthai = kehoach_util.HOCSINH_DA_DUYET
                    else:
                        trangthai = kehoach_util.HOCSINH_DANG_CANTHIEP




            hs.trangthai_kehoach = trangthai








    def func_get_default_kehoach_tu_ngay(self,kehoach_gan_nhat):
        tu_ngay = fields.Date.context_today(self)
        if kehoach_gan_nhat and kehoach_gan_nhat.den_ngay:
            # 2. Bốc được ngày kết thúc, tiến hành cộng thêm 1 ngày tịnh tiến
            tu_ngay = fields.Date.to_date(kehoach_gan_nhat.den_ngay)
            tu_ngay =tu_ngay + timedelta(days=1)
           
        return tu_ngay

    # Default = Hôm nay + 31 ngày (Dùng hàm lambda để tính toán nhanh)

    def func_get_default_kehoach_den_ngay(self,tu_ngay):
        if tu_ngay:
            songay_str = coso_util.func_cauhinh_canthiep(self,self.coso_id,"macdinh_songay_kehoach","30")
            songay =int(songay_str)-1
            return fields.Date.to_date(tu_ngay) + timedelta(days=songay)
        return False



