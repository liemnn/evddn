from odoo import models, fields, api, exceptions
from datetime import  timedelta,date,datetime
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")



class HocSinhInherit(models.Model):
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
            ketluan = kehoach_util.func_get_ketluan_hocsinh_trangthai(self,hs,trangthais)
            if ketluan:
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
                kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self,hs,trangthais)
                if not kehoach:
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
        for hs in self:
            trangthais = [kehoach_util.KEHOACH_DANG_LAP]
            kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self,hs,trangthais)
            if not kehoach:
                hs.is_sua_kehoach = False
            else:
                giaovien = kehoach.ketluan_id.gv_lapkehoach_id
                if (is_admin or giaovien.user_id.id == user.id):
                    hs.is_sua_kehoach = True
                else:
                    hs.is_sua_kehoach = False

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
                        'default_ketluan_id': ketluan.id,
                        'default_hocsinh_id': self.id
                    },
                }

    def func_tao_kehoach_macdinh(self,ketluan):
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
        return None

    def action_sua_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        trangthais =[kehoach_util.KEHOACH_DANG_LAP]
        kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self,self,trangthais)
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
                    'default_hocsinh_id': self.id
                },
            }
        else:
            raise UserError(
                "Hiện đã có [Kế hoạch] đang lập không thể tạo kế hoạch mới !"
            )


    def action_duyet_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        kehoach = kehoach_util.func_get_kehoach_hocsinh(self,self)
        if kehoach:
            kehoach.trangthai = kehoach_util.TRANGTHAI_DANG_LAP_KEHOACH
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
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        kehoach = kehoach_util.func_get_kehoach_hocsinh(self,self)
        if kehoach:
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach_muctieu',
                'view_mode': 'kanban,list',
                'target': 'current',
                'domain': [('kehoach_id', '=', kehoach.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_kehoach_id': kehoach.id
                },
            }

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
