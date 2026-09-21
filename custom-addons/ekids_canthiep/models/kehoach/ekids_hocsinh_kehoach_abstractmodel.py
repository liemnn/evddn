from odoo import models, fields, api, exceptions
from datetime import  timedelta,date,datetime
from dateutil.relativedelta import relativedelta
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



class HocSinhKeHoachAbstractModel(models.AbstractModel):
    _register = False
    _description = 'Kế hoạch can thiệp của học sinh'

    def _compute_kehoach_thang(self):
        today = fields.Date.today()
        # 1. Tính toán mốc ngày 1 lần duy nhất ngoài vòng lặp
        d_thangnay_1 = today.replace(day=1)
        d_thangnay_15 = today.replace(day=15)

        d_thangtruoc_1 = d_thangnay_1 - relativedelta(months=1)
        d_thangtruoc_15 = d_thangtruoc_1.replace(day=15)

        d_thangsau_1 = d_thangnay_1 + relativedelta(months=1)
        d_thangsau_15 = d_thangsau_1.replace(day=15)

        for hs in self:
            # Lọc ngay trên bộ nhớ RAM qua hs.kehoach_ids
            has_truoc = any(
                kh.tu_ngay and kh.den_ngay and kh.tu_ngay <= d_thangtruoc_15 and kh.den_ngay >= d_thangtruoc_1
                for kh in hs.kehoach_ids
            )
            has_nay = any(
                kh.tu_ngay and kh.den_ngay and kh.tu_ngay <= d_thangnay_15 and kh.den_ngay >= d_thangnay_1
                for kh in hs.kehoach_ids
            )
            has_sau = any(
                kh.tu_ngay and kh.den_ngay and kh.tu_ngay <= d_thangsau_15 and kh.den_ngay >= d_thangsau_1
                for kh in hs.kehoach_ids
            )

            hs.kehoach_thangtruoc = "Có" if has_truoc else "Không"
            hs.kehoach_thangnay = "Có" if has_nay else "Không"
            hs.kehoach_thangsau = "Có" if has_sau else "Không"


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
        giaoviens = giaovien_util.func_get_giaoviens_tu_user(self)
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
                            elif (kh.ketluan_id.gv_kiemduyet_id.id in giaoviens.ids):
                                tong +=1

                hs.tong_kehoach_doiduyet = tong
                hs.ngay_guiduyet = string_util.date2string_format(ngay,'%d/%m/%Y')

            else:
                hs.tong_kehoach_doiduyet = 0
                hs.ngay_guiduyet = None

    def _compute_ten_kehoach(self):
        for hs in self:
            # Do kehoach_ids đã có _order tu_ngay desc nên phần tử đầu tiên luôn là kế hoạch mới nhất
            latest_kh = hs.kehoach_ids[:1]
            hs.ten_kehoach = latest_kh.name if latest_kh else ""


    def _compute_tong_kehoach_taomoi(self):
        is_admin = self.env.user.has_group('base.group_system')
        giaovien = giaovien_util.func_get_giaovien_tu_user(self)
        gv_id = giaovien.id if giaovien else False

        for hs in self:
            if is_admin:
                hs.tong_kehoach_taomoi = len(hs.kehoach_ids)
            else:
                hs.tong_kehoach_taomoi = sum(1 for kh in hs.kehoach_ids if kh.gv_lapkehoach_id.id == gv_id)

    def _compute_tong_kehoach_dang_canthiep(self):
        today = date.today()
        is_admin = self.env.user.has_group('base.group_system')
        context_type = self.env.context.get("default_context_type", "-1")
        giaoviens = giaovien_util.func_get_giaoviens_tu_user(self)
        gv_ids = set(giaoviens.ids) if giaoviens else set()

        for hs in self:
            tong = 0
            for kh in hs.kehoach_ids:
                if kh.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP and kh.tu_ngay and today >= kh.tu_ngay:
                    if is_admin:
                        tong += 1
                    elif context_type == "2" and kh.ketluan_id.gv_kiemduyet_id.id in gv_ids:
                        tong += 1
                    elif context_type == "3" and kh.gv_lapkehoach_id.id in gv_ids:
                        tong += 1
                    elif context_type not in ["2", "3"]:
                        tong += 1
            hs.tong_kehoach_dang_canthiep = tong

    def _compute_tong_kehoach_da_canthiep(self):
        is_admin = self.env.user.has_group('base.group_system')
        giaovien = giaovien_util.func_get_giaovien_tu_user(self)
        gv_id = giaovien.id if giaovien else False

        for hs in self:
            if is_admin:
                hs.tong_kehoach_da_canthiep = sum(
                    1 for kh in hs.kehoach_ids if kh.trangthai == kehoach_util.KEHOACH_HET_HIEULUC)
            else:
                hs.tong_kehoach_da_canthiep = sum(1 for kh in hs.kehoach_ids if
                                                  kh.trangthai == kehoach_util.KEHOACH_HET_HIEULUC and kh.gv_lapkehoach_id.id == gv_id)







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
                                                                          [kehoach_util.KETLUAN_DANG_TAO,kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH])
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
        giaoviens =giaovien_util.func_get_giaoviens_tu_user(self)
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
                        if giaovien.id in giaoviens.ids:
                            is_kiemduyet = True
            hs.is_kiemduyet = is_kiemduyet






    def _compute_is_canthiep(self):
        today = date.today()
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        giaoviens =giaovien_util.func_get_giaoviens_tu_user(self)
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
                            if (giaovien and giaovien.id in giaoviens.ids):
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












