from odoo import models, fields, api, exceptions
from datetime import  timedelta,date,datetime
from odoo.exceptions import UserError

from .ekids_hocsinh_kehoach_abstractmodel import HocSinhKeHoachAbstractModel

import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")



class HocSinhInherit(models.Model,HocSinhKeHoachAbstractModel):
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


    is_tao_ketluan = fields.Boolean(compute="_compute_is_tao_ketluan")
    is_lap_kehoach = fields.Boolean(compute="_compute_is_lap_kehoach")
    is_sua_kehoach = fields.Boolean(compute="_compute_is_sua_kehoach")
    is_kiemduyet = fields.Boolean(compute="_compute_is_kiemduyet")
    is_canthiep = fields.Boolean(compute="_compute_is_canthiep")


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


    def _compute_is_lap_kehoach(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for hs in self:
            trangthais = [kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH]
            ketluan = kehoach_util.func_get_ketluan_hocsinh_trangthai(self,hs,trangthais)
            if not ketluan:
                hs.is_lap_kehoach = False
            else:
                trangthais =[kehoach_util.KEHOACH_DANG_LAP
                                ,kehoach_util.KEHOACH_DANG_PHEDUYET]
                kehoach_count = kehoach_util.func_count_kehoach_hocsinh_trangthai(self,hs,trangthais)
                if kehoach_count <=0:
                    if is_admin:
                        hs.is_lap_kehoach = True
                    else:
                        giaovien = ketluan.gv_lapkehoach_id
                        if giaovien.user_id.id == user.id:
                            hs.is_lap_kehoach = True
                        else:
                            hs.is_lap_kehoach = False
                else:
                    hs.is_lap_kehoach = False

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
                giaovien_lap = target_kehoach.ketluan_id.gv_lapkehoach_id

                # So sánh trực tiếp Recordset (giaovien_lap.user_id == user) cực kỳ an toàn, không lo crash
                if is_admin or (giaovien_lap and giaovien_lap.user_id == user):
                    rec.is_sua_kehoach = True

    def _compute_is_kiemduyet(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for hs in self:
            kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self,hs,kehoach_util.KEHOACH_DANG_PHEDUYET)
            if not kehoach:
                hs.is_kiemduyet = False
            else:
                if kehoach.trangthai_pheduyet == kehoach_util.PHEDUYET_DOI_DUYET:
                    if is_admin:
                        hs.is_kiemduyet = True
                    else:
                        giaovien = kehoach.ketluan_id.gv_kiemduyet_id
                        if giaovien.user_id.id == user.id:
                            hs.is_kiemduyet = True
                        else:
                            hs.is_kiemduyet = False
                else:
                    hs.is_kiemduyet = False





    def _compute_is_canthiep(self):
        today = date.today()
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        for hs in self:
            # LƯU Ý SỐNG CÒN: Luôn gán mặc định False đầu vòng lặp cho từng học sinh
            # để tránh lỗi lọt điều kiện không gán dữ liệu của Odoo Compute
            hs.is_canthiep = False

            kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self,hs, kehoach_util.KEHOACH_DANG_CANTHIEP)

            if kehoach:
                # --- ÉP KIỂU NGÀY AN TOÀN TUYỆT ĐỐI (DATE VS DATETIME) ---
                tu_ngay = kehoach.tu_ngay.date() if isinstance(kehoach.tu_ngay, datetime) else kehoach.tu_ngay
                den_ngay = kehoach.den_ngay.date() if isinstance(kehoach.den_ngay, datetime) else kehoach.den_ngay


                # Kiểm tra khoảng thời gian hiệu lực (Đảm bảo các ô ngày không bị False/Rỗng)
                if tu_ngay and den_ngay and tu_ngay <= today <= den_ngay:

                    # Phân quyền xử lý gán kết quả True
                    if is_admin:
                        hs.is_canthiep = True
                    else:
                        giaovien = kehoach.ketluan_id.gv_canthiep_id
                        # Phòng thủ kiểm tra chắc chắn để tránh lỗi sập hệ thống (Null Pointer) khi chưa chọn giáo viên
                        if giaovien and giaovien.user_id and giaovien.user_id.id == user.id:
                            hs.is_canthiep = True





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

        for hs in self:
            kehoach = kehoach_util.func_get_kehoach_hocsinh(self,hs)
            trangthai = ""

            if not kehoach:
                trangthai = kehoach_util.HOCSINH_CHUA_CO_KEHOACH
            else:
                # --- ÉP KIỂU NGÀY AN TOÀN TRÁNH LỖI DATETIME VS DATE ---
                tu_ngay = kehoach.tu_ngay.date() if isinstance(kehoach.tu_ngay, datetime) else kehoach.tu_ngay
                den_ngay = kehoach.den_ngay.date() if isinstance(kehoach.den_ngay, datetime) else kehoach.den_ngay

                # Khối 1: Tính toán các trạng thái ban đầu và phê duyệt
                if kehoach.trangthai == kehoach_util.KEHOACH_DANG_LAP:
                    trangthai = kehoach_util.HOCSINH_DANG_LAP_KEHOACH

                elif kehoach.trangthai == kehoach_util.KEHOACH_DANG_PHEDUYET:
                    if kehoach.trangthai_pheduyet == kehoach_util.PHEDUYET_DOI_DUYET:
                        trangthai = kehoach_util.HOCSINH_DOI_DUYET
                    elif kehoach.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH:
                        trangthai = kehoach_util.HOCSINH_CAN_DIEUCHINH
                    else:
                        # Đã duyệt -> Chuyển trạng thái học sinh thành ĐÃ DUYỆT
                        trangthai = kehoach_util.HOCSINH_DA_DUYET
                        # Cập nhật trạng thái của chính bản ghi kế hoạch sang ĐANG CAN THIỆP
                        kehoach.trangthai = kehoach_util.KEHOACH_DANG_CANTHIEP

                # Khối 2: ĐƯA VÀO TRONG ELSE - Tính toán thời hạn riêng cho trạng thái ĐANG CAN THIỆP
                # (Sử dụng luôn giá trị vừa cập nhật từ Khối 1 nếu có)
                if kehoach.trangthai == kehoach_util.KEHOACH_DANG_CANTHIEP:
                    if den_ngay and den_ngay < today:
                        trangthai = kehoach_util.HOCSINH_HET_HIEULUC
                        kehoach.trangthai = kehoach_util.KEHOACH_HET_HIEULUC
                    elif tu_ngay and den_ngay and tu_ngay <= today <= den_ngay:
                        trangthai = kehoach_util.HOCSINH_DANG_CANTHIEP
                    else:
                        trangthai = kehoach_util.HOCSINH_DA_DUYET

            # Gán giá trị cuối cùng cho học sinh
            hs.trangthai_kehoach = trangthai





    def action_taomoi_ketluan(self):
        form_view_id = self.env.ref('ekids_canthiep.kehoach_ketluan_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.kehoach_ketluan',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id
            },
        }

    def action_xem_danhsach_ketluan(self):
          return {
            'type': 'ir.actions.act_window',
            'name': 'KẾT LUẬN',
            'res_model': 'ekids.kehoach_ketluan',
            'view_mode': 'kanban,form',

            'target': 'current',
            'domain': [('hocsinh_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id
            },
        }

    def action_lap_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        trangthais = [kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH]
        ketluan = kehoach_util.func_get_ketluan_hocsinh_trangthai(self,self,trangthais)
        if ketluan:
            kehoach = self.func_tao_kehoach_macdinh(ketluan)
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
                        'default_ketluan_id': ketluan.id,
                        'default_hocsinh_id': self.id
                    },
                }

    def func_tao_kehoach_macdinh(self,ketluan):

        trangthais=[kehoach_util.KEHOACH_DANG_LAP,kehoach_util.KEHOACH_DANG_PHEDUYET]
        kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self,self,trangthais)
        if not kehoach:
            data ={
                "hocsinh_id":self.id,
                "ketluan_id": ketluan.id,
            }
            kehoach = self.env['ekids.kehoach'].create(data)
            if kehoach:
                linhvucs = ketluan.linhvuc_ids
                for linhvuc in linhvucs:
                    data2={
                        'kehoach_id':kehoach.id,
                        'chuongtrinh_id': linhvuc.linhvuc_id.chuongtrinh_id.id,
                        'linhvuc_id': linhvuc.linhvuc_id.id,
                        'tuoi_id': linhvuc.tuoi_id.id,
                    }
                    self.env['ekids.kehoach_linhvuc'].create(data2)
                return  kehoach
        return kehoach

    def action_sua_kehoach(self):
        self.ensure_one()  # Đảm bảo hàm chỉ chạy trên 1 dòng học sinh duy nhất, tránh lỗi sập hệ thống
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id

        user = self.env.user
        is_admin = user.has_group('base.group_system')
        target_kehoach = None

        # 🌟 BƯỚC 1: ĐỒNG BỘ LOGIC TÌM KIẾM KẾ HOẠCH ĐƯỢC PHÉP SỬA
        # Ưu tiên 1: Tìm kế hoạch "Đang lập"
        kh_dang_lap = kehoach_util.func_get_kehoach_hocsinh_trangthai(self, self, [kehoach_util.KEHOACH_DANG_LAP])

        if kh_dang_lap:
            target_kehoach = kh_dang_lap
        else:
            # Ưu tiên 2: Tìm kế hoạch "Đợi duyệt" nhưng ở trạng thái "Cần điều chỉnh"
            kh_doi_duyet = kehoach_util.func_get_kehoach_hocsinh_trangthai(self, self,
                                                                           [kehoach_util.KEHOACH_DANG_PHEDUYET])
            if kh_doi_duyet and kh_doi_duyet.trangthai_pheduyet == kehoach_util.PHEDUYET_CAN_DIEUCHINH:
                target_kehoach = kh_doi_duyet

        # 🌟 BƯỚC 2: ĐIỀU HƯỚNG MỞ FORM HOẶC BÁO LỖI CHẶN QUYỀN
        if target_kehoach:
            # Phòng thủ tầng sâu (Backend Security Check): Đảm bảo người dùng thực sự có quyền sửa
            giaovien_lap = target_kehoach.ketluan_id.gv_lapkehoach_id
            if not (is_admin or (giaovien_lap and giaovien_lap.user_id == user)):
                raise UserError(
                    "Bạn không có quyền chỉnh sửa kế hoạch này! Chỉ Giáo viên lập kế hoạch này hoặc Quản trị viên mới có quyền.")

            # Trả về Action mở đúng Form phiếu kế hoạch tìm thấy
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',
                'views': [(form_view_id, 'form')],
                'res_id': target_kehoach.id,  # Ghim đúng ID của kế hoạch vào form view
                'target': 'current',
                'domain': [('coso_id', '=', self.coso_id.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id
                },
            }

        # 🌟 BƯỚC 3: SỬA LẠI THÔNG BÁO LỖI ĐÚNG NGỮ NGHĨA
        raise UserError(
            f"Học sinh [{self.name}] hiện không có Kế hoạch nào ở trạng thái có thể chỉnh sửa "
            f"(Đang lập hoặc Cần điều chỉnh sửa lại)!"
        )


    def action_duyet_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        trangthais = [kehoach_util.KEHOACH_DANG_PHEDUYET]
        kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self, self, trangthais)
        if kehoach:
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',
                'res_id': kehoach.id,
                'views': [(form_view_id, 'form')],
                'target': 'current',
                'domain': [('coso_id', '=', self.coso_id.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id,
                    # 🌟 THÊM 3 DÒNG CHỐT CHẶN DƯỚI ĐÂY ĐỂ KHÓA ĐỂN FORM VIEW
                    'edit': True,  # 🚫 Tắt hoàn toàn tính năng và ẩn nút [Sửa]
                    'create': False,  # 🚫 Tắt tính năng và ẩn nút [Tạo mới]
                    'delete': False,  # 🚫 Tắt tính năng và ẩn nút [Xóa]
                },
            }

    def action_xem_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        kehoach = kehoach_util.func_get_kehoach_hocsinh(self,self)
        if kehoach:
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',
                'res_id': kehoach.id,
                'views': [(form_view_id, 'form')],
                'target': 'current',
                'domain': [('coso_id', '=', self.coso_id.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id
                },
            }

    def action_canthiep(self):
        self.ensure_one()
        # Kiểm tra phân quyền lâm sàng nâng cao nếu cần
        trangthai=[kehoach_util.KEHOACH_DANG_CANTHIEP]
        kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self,self,trangthai)
        if kehoach:
            return {
                'type': 'ir.actions.client',
                # 🌟 BỔ SUNG DÒNG NÀY: Định nghĩa tiêu đề xuất hiện trên Breadcrumbs
                'name': 'KẾ HOẠCH CAN THIỆP:'+ self.name,
                'tag': 'ekids_canthiep.kehoach_canthiep_action',  # Thẻ tag đăng ký trùng khớp với file JS Registry
                'target': 'current',  # Mở tràn màn hình làm việc hiện tại
                'context': {
                    'kehoach_id': kehoach.id,  # Gửi ID phiếu kế hoạch sang cấu phần Frontend
                },
            }
        else:
            raise UserError(
                f"Học sinh [{self.name}] hiện không có Kế hoạch nào ở trạng thái có thể Can thiệp"

            )

    def action_xem_danhsach_kehoach(self):
        kanban_view_id = self.env.ref('ekids_canthiep.danhsach_kehoach_kanban').id
        form_view_id = self.env.ref('ekids_canthiep.kehoach_ketluan_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH KẾ HOẠCH',
            'res_model': 'ekids.kehoach',
            'view_mode': 'kanban',
            'views': [(kanban_view_id, 'kanban'),(form_view_id, 'form')],
            'target': 'current',
            'domain': [('hocsinh_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id
            },
        }

