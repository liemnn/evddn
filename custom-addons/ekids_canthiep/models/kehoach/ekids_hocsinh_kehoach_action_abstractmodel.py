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
            return {
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
                        'default_ketluan_id': ketluan.id,
                        'default_hocsinh_id': self.id
                    },
                }

    def func_tao_kehoach_macdinh(self,ketluan):

        trangthais=[kehoach_util.KEHOACH_DANG_LAP,kehoach_util.KEHOACH_DANG_PHEDUYET,kehoach_util.KEHOACH_DANG_CANTHIEP]
        kehoach = kehoach_util.func_get_kehoach_hocsinh_trangthai(self,self,trangthais)
        if not kehoach:
            giaovien = giaovien_util.func_get_giaovien_tu_user(self)
            kehoach_gannhat = kehoach_util.func_get_kehoach_hocsinh_gannhat(self,self)
            tu_ngay = self.func_get_default_kehoach_tu_ngay(kehoach_gannhat)
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
            if kehoach_gannhat:
                data["kehoach_truoc_id"] =kehoach_gannhat.id

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
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        context_type = self.env.context.get("default_context_type")
        context_trangthai = self.env.context.get("default_context_trangthai")
        context_trangthai_pheduyet = self.env.context.get("default_context_trangthai_pheduyet")

        giaovien = giaovien_util.func_get_giaovien_tu_user(self)
        if giaovien:
            list_view_id = self.env.ref('ekids_canthiep.kehoach_list').id
            form_view_id = self.env.ref('ekids_canthiep.kehoach_form').id
            kanban_view_id = self.env.ref('ekids_canthiep.kehoach_kanban').id
            if context_type =="1":
                #Danh sách lập kế hoạch
                list_view_id = self.env.ref('ekids_canthiep.lap_kehoach_list').id


            url= {
                'type': 'ir.actions.act_window',
                'name': 'DANH SÁCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'list,kanban,form',
                'views': [(list_view_id, 'list'),(kanban_view_id, 'kanban'),(form_view_id, 'form')],
                'target': 'current',
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id
                },
            }
            if context_type =="1":
                # danh sách lập kế hoạch
                domain =[('hocsinh_id', '=', self.id)]
                if is_admin == False:
                    domain_gv= [('gv_lapkehoach_id','=',giaovien.id)]
                    domain = expression.AND([domain, domain_gv])
                url["domain"]=domain
            elif context_type=="2":
                # danh sách cần phê duyệt
                domain = [('hocsinh_id', '=', self.id)]
                if context_trangthai:
                    domain_trangthai =[('trangthai', 'in', context_trangthai)]
                    domain = expression.AND([domain, domain_trangthai])
                if context_trangthai_pheduyet:
                    domain_trangthai = [('trangthai_pheduyet', 'in', context_trangthai_pheduyet)]
                    domain = expression.AND([domain, domain_trangthai])
                if is_admin == False:
                    domain_gv_pheduyet = [('ketluan_id.gv_kiemduyet_id', '=', giaovien.id)]
                    domain = expression.AND([domain, domain_gv_pheduyet])

                url["domain"] = domain

            elif context_type == "4":
                # Danh sách tất cả kế hoạch do mình phê duyệt
                # danh sách cần phê duyệt
                domain = [('hocsinh_id', '=', self.id)]
                if is_admin == False:
                    domain_gv_pheduyet = [('ketluan_id.gv_kiemduyet_id', '=', giaovien.id)]
                    domain = expression.AND([domain, domain_gv_pheduyet])
                url["domain"] = domain

            else:
                # danh sách đang can thiệp
                domain = [('hocsinh_id', '=', self.id)]
                if context_trangthai:
                    domain_trangthai =[('trangthai', 'in', context_trangthai)]
                    domain = expression.AND([domain, domain_trangthai])
                if context_trangthai_pheduyet:
                    domain_trangthai = [('trangthai_pheduyet', 'in', context_trangthai_pheduyet)]
                    domain = expression.AND([domain, domain_trangthai])

                if is_admin == False:
                    domain_gv_lapkehoach= [('gv_lapkehoach_id','=',giaovien.id)]
                    domain_gv_kiemduyet = [('ketluan_id.gv_kiemduyet_id', '=', giaovien.id)]
                    domain_gv = expression.OR([domain_gv_lapkehoach, domain_gv_kiemduyet])

                    domain = expression.AND([domain, domain_gv])

                url["domain"] = domain
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





