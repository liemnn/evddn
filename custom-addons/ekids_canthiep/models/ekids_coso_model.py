from odoo import models, fields, api, _
from datetime import datetime, timedelta,date
from odoo.osv import expression

import logging
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



class CoSo(models.Model):
    _inherit = "ekids.coso"

    is_ketluan = fields.Boolean(compute="_compute_is_ketluan")
    is_duyet_kehoach = fields.Boolean(compute="_compute_is_duyet_kehoach")

    is_ql_chuongtrinh = fields.Boolean(compute="_compute_is_ql_chuongtrinh")

    is_theodoi_kehoach = fields.Boolean(compute="_compute_is_theodoi_kehoach")

    def _compute_is_ql_chuongtrinh(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_ql_ct = user.has_group('ekids_core.ql_ct_canthiep')

        for record in self:
            is_ql_chuongtrinh = False
            if (is_admin == True
                or  is_ql_ct == True):
                is_ql_chuongtrinh = True
            record.is_ql_chuongtrinh = is_ql_chuongtrinh

    def _compute_is_duyet_kehoach(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        for record in self:
            is_duyet_kehoach = False
            if is_admin:
                is_duyet_kehoach = True
            else:
                hocsinh_ids = kehoach_util.func_get_ids_hocsinh_theo_vaitro_duyet_kehoach(self)
                if hocsinh_ids and len(hocsinh_ids)>0:
                    is_duyet_kehoach = True
            record.is_duyet_kehoach = is_duyet_kehoach

    def _compute_is_theodoi_kehoach(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_ql_coso = user.has_group('ekids_core.quanlycoso')

        for record in self:
            is_theodoi_kehoach = False
            if is_admin  or is_ql_coso:
                is_theodoi_kehoach = True

            record.is_theodoi_kehoach = is_theodoi_kehoach


    def _compute_is_ketluan(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_role_ketluan = user.has_group('ekids_core.ketluan')

        for record in self:
           if (is_admin
               or is_role_ketluan):
               record.is_ketluan = True
           else:
               record.is_ketluan = False


    def action_xem_chuongtrinh_kanban(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'CHƯƠNG TRÌNH',
            'res_model': 'ekids.ct_chuongtrinh',
            'view_mode': 'kanban,list,form',
            'domain': [('coso_id', '=', self.id)],
            'target': 'current',
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_roiloan(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH MỤC [RỐI LOẠN]',
            'res_model': 'ekids.ct_dm_roiloan',
            'view_mode': 'list,kanban,form',

            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_lieuluong(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH MỤC [LIỀU LƯỢNG]',
            'res_model': 'ekids.ct_dm_lieuluong',
            'view_mode': 'list,kanban,form',

            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_mucdo(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH MỤC [MỨC ĐỘ]',
            'res_model': 'ekids.ct_dm_mucdo',
            'view_mode': 'list,kanban,form',

            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_phuongphap(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH MỤC [PHƯƠNG PHÁP]',
            'res_model': 'ekids.ct_dm_phuongphap',
            'view_mode': 'list,kanban,form',

            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_lichhen(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH MỤC [LICH HẸN]',
            'res_model': 'ekids.ct_dm_lichhen',
            'view_mode': 'list,kanban,form',

            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_xem_danhmuc_cg_danhgia(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SACHS [CHUYÊN GIA ĐÁNH GIÁ]',
            'res_model': 'ekids.ct_dm_cg_danhgia',
            'view_mode': 'list,kanban,form',

            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_danhsach_hocsinh_ketluan(self):
        list_view_id = self.env.ref('ekids_canthiep.hocsinh_ketluan_inherit_list').id
        domain = [('coso_id', '=', self.id)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            },
        }

    def action_danhsach_hocsinh_lap_kehoach(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        list_view_id = self.env.ref('ekids_canthiep.hocsinh_lap_kehoach_inherit_list').id
        domain = [('coso_id', '=', self.id)]

        if is_admin == False:
            hocsinh_ids = kehoach_util.func_get_ids_hocsinh_theo_vaitro_lap_kehoach(self)
            domain = [('coso_id', '=', self.id),('id','in',hocsinh_ids)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            },
        }

    def action_danhsach_hocsinh_duyet_kehoach(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        list_view_id = self.env.ref('ekids_canthiep.hocsinh_duyet_kehoach_inherit_list').id
        domain = [('coso_id', '=', self.id)]
        if is_admin == False:
            hocsinh_ids = kehoach_util.func_get_ids_hocsinh_theo_vaitro_duyet_kehoach(self)
            domain = [('coso_id', '=', self.id),('id','in',hocsinh_ids)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            },
        }

    def action_danhsach_hocsinh_canthiep(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        list_view_id = self.env.ref('ekids_canthiep.hocsinh_canthiep_inherit_list').id
        domain = [('coso_id', '=', self.id)]
        if is_admin == False:
            hocsinh_ids = kehoach_util.func_get_ids_hocsinh_theo_vaitro_canthiep_kehoach(self)
            domain = [('coso_id', '=', self.id), ('id', 'in', hocsinh_ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH',
            'res_model': 'ekids.hocsinh',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'current',
            'domain': domain,
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            },
        }

    def action_danhsach_hocsinh_theodoi_kehoach(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_ql_coso = user.has_group('ekids_core.quanlycoso')
        if is_admin or is_ql_coso:
            list_view_id = self.env.ref('ekids_canthiep.hocsinh_theodoi_kehoach_inherit_list').id
            domain = [('coso_id', '=', self.id)]
            return {
                'type': 'ir.actions.act_window',
                'name': 'DANH SÁCH',
                'res_model': 'ekids.hocsinh',
                'view_mode': 'list',
                'views': [(list_view_id, 'list')],
                'target': 'current',
                'domain': domain,
                'context': {
                    'default_coso_id': self.id,
                    'search_default_trangthai': '1',
                },
            }

    def action_kiemduyet_noidung_thietke(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')

        list_view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_kiemduyet_thietke_list').id
        form_view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_duyet_thietke_form').id
        search_view_id = self.env.ref('ekids_canthiep.kehoach_muctieu_search').id
        #giaovien = giaovien_util.func_get_giaovien_tu_user(self)

        # Tập các giá trị đại diện cho HTML rỗng
        EMPTY_HTML = [False, '', '<p><br></p>', '<p></p>', '<p><br/></p>', '<p>&nbsp;</p>']

        # 1. Điều kiện chung: thuộc cơ sở, có mục tiêu và bản ghi temp PHẢI có nội dung
        domain_base = [
            ('kehoach_id.coso_id', '=', self.id),
            ('muctieu_id', '!=', False),
            ('thietke_temp', 'not in', EMPTY_HTML),
        ]

        # 2. Nhánh 1: Chưa xem ('0') VÀ mục tiêu gốc CHƯA CÓ thiết kế
        domain_chua_xem = [
            ('trangthai_thietke', '=', '0'),
            ('muctieu_id.thietke', 'in', EMPTY_HTML),
        ]

        # 3. Nhánh 2: Đã xem / đã xử lý (khác '0')
        domain_da_xu_ly = [
            ('trangthai_thietke', '!=', '0'),
        ]

        # Kết hợp: domain_base AND (domain_chua_xem OR domain_da_xu_ly)
        domain = expression.AND([
            domain_base,
            expression.OR([domain_chua_xem, domain_da_xu_ly])
        ])




        return {
            'type': 'ir.actions.act_window',
            'name': 'DANH SÁCH CẦN KIỂM DUYỆT',
            'res_model': 'ekids.kehoach_muctieu',
            'view_mode': 'list,form',
            'views': [(list_view_id, 'list'),(form_view_id, 'form')],
            'search_view_id': [search_view_id, 'search'], # 🌟 BẮT BUỘC KHAI BÁO DÒNG NÀY
            'target': 'current',
            'domain':domain,
            'context': {
                'default_duyet_bientap_chuongtrinh': '1',
                'default_coso_id': self.id,
                'search_default_trangthai_thietke_0': '0',

            },
        }






