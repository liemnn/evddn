from odoo import api, fields, models
from datetime import datetime,date, timedelta
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import json  # 🌟 BẮT BUỘC: Sử dụng bộ Json an toàn của Odoo

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




class HocSinhKeHoachActionAbstractModel(models.AbstractModel):
    _name = 'ekids.hocsinh_kehoach_action_abstractmodel'
    _description = 'Kế hoạch can thiệp của học sinh'
    _abstract = True


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

    def action_sua_ketluan(self):
        form_view_id = self.env.ref('ekids_canthiep.kehoach_ketluan_form').id
        ketluan = kehoach_util.func_get_ketluan_hocsinh_trangthai(self, self,
                                                                          [kehoach_util.KETLUAN_DANG_TAO])
        if ketluan:
            url= {
                'type': 'ir.actions.act_window',
                'name': 'CHƯƠNG TRÌNH CAN THIỆP',
                'res_model': 'ekids.kehoach_ketluan',
                'view_mode': 'form',
                'views': [(form_view_id, 'form')],
                "res_id":ketluan.id,
                'target': 'current',
                'domain': [('coso_id', '=', self.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id
                },
            }
            return url
    def action_copy_ketluan_gannhat(self):
        self.ensure_one()

        ketluan_gannhat = kehoach_util.func_get_ketluan_hocsinh_trangthai(self, self,
                                                                  [kehoach_util.KEHOACH_DANG_CANTHIEP])
        if ketluan_gannhat:
            ketlua_copy =ketluan_gannhat.func_copy_ketluan_tu_nguon(ketluan_gannhat.id,ketluan_gannhat.hocsinh_id.id)
            if ketlua_copy:
                url = self.action_sua_ketluan()
                return url
    def action_copy_ketluan(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH CAN THIỆP',
            'res_model': 'ekids.kehoach_ketluan',
            'view_mode': 'list',
            'target': 'new',  # Vẫn giữ nguyên mở dạng Pop-up
            'domain': [('coso_id', '=', self.coso_id.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id,
                'create': False,
                'edit': False,
                'delete': False,
                'dialog_size': 'extra-large',  # 🌟 GIẢI PHÁP: Giúp phóng cực đại bề ngang Pop-up
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

        trangthais = [kehoach_util.KETLUAN_CHOPHEP_LAP_KEHOACH]
        ketluan = kehoach_util.func_get_ketluan_hocsinh_trangthai(self,self,trangthais)
        if ketluan:
            kehoach = self.func_tao_kehoach_macdinh(ketluan)
            if kehoach:
                url= {
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
                        'default_ketluan_id': ketluan.id,
                        'default_hocsinh_id': self.id
                    },
                }
                return url

    def func_tao_kehoach_macdinh(self,ketluan):

        trangthais=[kehoach_util.KEHOACH_DANG_LAP,kehoach_util.KEHOACH_DANG_PHEDUYET,kehoach_util.KEHOACH_DANG_CANTHIEP]
        kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self,self,trangthais)
        if not kehoach:
            giaovien = giaovien_util.func_get_giaovien_tu_user(self)
            # tim ke hoach truoc
            trangthais = [kehoach_util.KEHOACH_HET_HIEULUC]
            kehoach_truoc = kehoach_util.func_get_kehoach_hocsinh_trangthai(self, self, trangthais)
            tu_ngay = date.today()
            if kehoach_truoc:
                tu_ngay = self.func_get_default_kehoach_tu_ngay(kehoach_truoc)
            den_ngay = self.func_get_default_kehoach_den_ngay(tu_ngay)
            songay = (den_ngay - tu_ngay).days + 1
            data ={
                "hocsinh_id":self.id,
                "ketluan_id": ketluan.id,
                "gv_lapkehoach_id": giaovien.id,
                "tu_ngay": tu_ngay,
                "den_ngay": den_ngay,
                "songay": songay
            }
            if kehoach_truoc:
                data["kehoach_truoc_id"] =kehoach_truoc.id

            kehoach = self.env['ekids.kehoach'].create(data)
            if kehoach:
                linhvucs = ketluan.linhvuc_ids
                for linhvuc in linhvucs:
                    data2={
                        'sequence':linhvuc.sequence,
                        'kehoach_id':kehoach.id,
                        'chuongtrinh_id': linhvuc.chuongtrinh_id.id,
                        'linhvuc_id': linhvuc.linhvuc_id.id,
                        'tuoi_id': linhvuc.tuoi_id.id,
                    }
                    self.env['ekids.kehoach_linhvuc'].create(data2)
                kehoach.func_copy_muctieu_thangtruoc_khongdat_sang()
        return kehoach

    def func_get_default_kehoach_tu_ngay(self, kehoach_gan_nhat):
        tu_ngay = fields.Date.context_today(self)
        if kehoach_gan_nhat and kehoach_gan_nhat.den_ngay:
            # 2. Bốc được ngày kết thúc, tiến hành cộng thêm 1 ngày tịnh tiến
            tu_ngay = fields.Date.to_date(kehoach_gan_nhat.den_ngay)
            tu_ngay = tu_ngay + timedelta(days=1)

        return tu_ngay

    # Default = Hôm nay + 31 ngày (Dùng hàm lambda để tính toán nhanh)

    def func_get_default_kehoach_den_ngay(self, tu_ngay):
        if tu_ngay:
            songay_str = coso_util.func_cauhinh_canthiep(self, self.coso_id, "macdinh_songay_kehoach", "30")
            songay = int(songay_str) - 1
            return fields.Date.to_date(tu_ngay) + timedelta(days=songay)
        return False

    def action_sua_kehoach(self):
        self.ensure_one()  # Đảm bảo hàm chỉ chạy trên 1 dòng học sinh duy nhất, tránh lỗi sập hệ thống


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
            giaoviens= target_kehoach.ketluan_id.gv_canthiep_ids
            user_ids = giaoviens.mapped('user_id').ids
            if not (is_admin or (giaoviens and user.id in user_ids)):
                raise UserError(
                    "Bạn không có quyền chỉnh sửa kế hoạch này! Chỉ Giáo viên lập kế hoạch này hoặc Quản trị viên mới có quyền.")

            # Trả về Action mở đúng Form phiếu kế hoạch tìm thấy
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',

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

        trangthais = [kehoach_util.KEHOACH_DANG_PHEDUYET]
        kehoach = kehoach_util.func_get_kehoach_can_kiemduyet_hocsinh_trangthai(self, self, trangthais)
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
                    'default_hocsinh_id': self.id,
                    # 🌟 THÊM 3 DÒNG CHỐT CHẶN DƯỚI ĐÂY ĐỂ KHÓA ĐỂN FORM VIEW
                    'edit': True,  # 🚫 Tắt hoàn toàn tính năng và ẩn nút [Sửa]
                    'create': False,  # 🚫 Tắt tính năng và ẩn nút [Tạo mới]
                    'delete': False,  # 🚫 Tắt tính năng và ẩn nút [Xóa]
                },
            }

    def action_xem_kehoach(self):

        kehoach = kehoach_util.func_get_kehoach_hocsinh(self, self)
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
                    'default_hocsinh_id': self.id
                },
            }
    def action_canthiep(self):
        self.ensure_one()
        today = date.today()
        # Kiểm tra phân quyền lâm sàng nâng cao nếu cần
        trangthai = [kehoach_util.KEHOACH_DANG_CANTHIEP]
        kehoach = kehoach_util.func_get_kehoach_can_canthiep_hocsinh_trangthai_ngay(self, self, trangthai, today)
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
                    'default_hocsinh_id': self.id,
                    # 🌟 THÊM 3 DÒNG CHỐT CHẶN DƯỚI ĐÂY ĐỂ KHÓA ĐỂN FORM VIEW
                    'edit': True,  # 🚫 Tắt hoàn toàn tính năng và ẩn nút [Sửa]
                    'create': False,  # 🚫 Tắt tính năng và ẩn nút [Tạo mới]
                    'delete': False,  # 🚫 Tắt tính năng và ẩn nút [Xóa]
                },
            }
        else:
            raise UserError(
                f"Học sinh [{self.name}] hiện không có Kế hoạch nào ở trạng thái có thể Can thiệp"

            )

    def action_xem_danhsach_kehoach(self):
        self.ensure_one()
        giaovien = giaovien_util.func_get_giaovien_tu_user(self)
        if not giaovien:
            return False

        env_ctx = self.env.context
        context_type = env_ctx.get("default_context_type")
        is_admin = self.env.user.has_group('base.group_system')

        # 1. Chọn View ID
        list_view_xml = 'ekids_canthiep.lap_kehoach_list' if context_type == "1" else 'ekids_canthiep.kehoach_list'
        list_view_id = self.env.ref(list_view_xml).id
        form_view_id = self.env.ref('ekids_canthiep.kehoach_form').id
        kanban_view_id = self.env.ref('ekids_canthiep.kehoach_kanban').id

        # 2. Xây dựng Domain cơ bản
        domain = [('hocsinh_id', '=', self.id)]

        # Bổ sung trạng thái từ Context nếu có
        if env_ctx.get("default_context_trangthai"):
            domain.append(('trangthai', 'in', env_ctx["default_context_trangthai"]))
        if env_ctx.get("default_context_trangthai_pheduyet") and context_type not in ["1", "5"]:
            domain.append(('trangthai_pheduyet', 'in', env_ctx["default_context_trangthai_pheduyet"]))

        # 3. Phân quyền theo Giáo viên (Nếu không phải Admin)
        if not is_admin:
            gv_lap_domain = [('gv_lapkehoach_id', '=', giaovien.id)]
            gv_duyet_domain = [('ketluan_id.gv_kiemduyet_id', '=', giaovien.id)]

            if context_type == "1":
                domain.extend(gv_lap_domain)
            elif context_type in ["2", "4"]:
                domain.extend(gv_duyet_domain)
            elif context_type in ["5", None]:  # Type 5 hoặc mặc định (Đang can thiệp)
                domain = expression.AND([domain, expression.OR([gv_duyet_domain, gv_lap_domain])])

        # 4. Trả về Window Action
        url= {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH KẾ HOẠCH',
            'res_model': 'ekids.kehoach',
            'view_mode': 'list,kanban,form',
            'views': [(list_view_id, 'list'), (kanban_view_id, 'kanban'), (form_view_id, 'form')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id,
            },
        }
        return url

    def action_xem_danhsach_kehoach_can_kiemduyet_ketqua(self):
        self._compute_tong_kehoach_dang_canthiep()
        tong_kehoach_dang_canthiep =  self.tong_kehoach_dang_canthiep
        if tong_kehoach_dang_canthiep >1:
            url =self.action_xem_danhsach_kehoach()
            return url
        else:
           trangthais =[kehoach_util.KEHOACH_DANG_CANTHIEP]
           kehoach =kehoach_util.func_get_kehoach_can_kiemduyet_hocsinh_trangthai(self, self, trangthais)
           if kehoach:
               self.func_tinhtoan_kehoach2muctieu_ketqua_canthiep(kehoach)
               url= {
                   'type': 'ir.actions.act_window',
                   'name': 'LẬP KẾ HOẠCH',
                   'res_model': 'ekids.kehoach',
                   'view_mode': 'form',
                   'res_id': kehoach.id,
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
               return url

        return  None

    def func_tinhtoan_kehoach2muctieu_ketqua_canthiep(self,kehoach):
        kehoach_linhvuc_ids = kehoach.kehoach_linhvuc_ids
        if kehoach_linhvuc_ids:
            for kehoach_linhvuc in kehoach_linhvuc_ids:
                kehoach_muctieu_ids = kehoach_linhvuc.kehoach_muctieu_ids
                if kehoach_muctieu_ids:
                    for kehoach_muctieu in kehoach_muctieu_ids:
                        kehoach_muctieu.func_khoitao_ketqua2muctieu()





