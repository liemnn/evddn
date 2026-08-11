from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


import logging
_logger = logging.getLogger(__name__)


try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import kehoach_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util

except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")





class KetLuanPhanCongLaiWizard(models.TransientModel):
    _name = 'ekids.kehoach_ketluan_phancong_lai_wizard'
    _description = 'Phân công lại giáo viên trong kết luận'

    coso_id = fields.Many2one("ekids.coso", related="ketluan_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")

    ketluan_id = fields.Many2one("ekids.kehoach_ketluan", string="Kết luận", required=True,
                                         ondelete="cascade")

    gv_canthiep_wizard_ids = fields.One2many("ekids.kehoach_ketluan_giaovien_wizard", "gv_canthiep_wizard_id"
                                  , string="Giáo viên can thiệp lựa chon")

    gv_kiemduyet_id = fields.Many2one('ekids.giaovien'
                                      , string="Giáo viên [Kiểm duyệt chuyên môn]", required=True)

    gv_canthiep_ids = fields.Many2many(comodel_name="ekids.giaovien"
                                       , relation="ekids_kehoach_ketluan_giaovien2wizard_rel"
                                       , column1="wizard_id"
                                       , column2="giaovien_id"
                                       , string="Kết luận phân công lại")

    def action_phancong_lai(self):
        self.ensure_one()

        # Lấy bản ghi kết luận gốc cần cập nhật
        ketluan = self.ketluan_id
        if not ketluan:
            raise ValidationError("Không tìm thấy kết luận gốc để cập nhật!")
        else:

            # -------------------------------------------------------------
            # Bước 1. CẬP NHẬT LẠI KẾT LUẬN GỐC (Giáo viên kiểm duyệt & Giáo viên can thiệp)
            # -------------------------------------------------------------
            ketluan_vals = {}

            # Cập nhật giáo viên kiểm duyệt nếu có thay đổi
            if ketluan.gv_kiemduyet_id != self.gv_kiemduyet_id:
                ketluan_vals['gv_kiemduyet_id'] = self.gv_kiemduyet_id.id

            # Cập nhật danh sách giáo viên can thiệp chung
            # Sử dụng lệnh (6, 0, ids) để thay thế toàn bộ danh sách cũ bằng danh sách mới chọn trên Wizard
            ketluan_vals['gv_canthiep_ids'] = [(6, 0, self.gv_canthiep_ids.ids)]

            # Tiến hành ghi nhận thay đổi lên kết luận
            ketluan.write(ketluan_vals)

            # -------------------------------------------------------------
            # 2. CẬP NHẬT LẠI CÁC KẾ HOẠCH CÓ SỰ THAY ĐỔI VỀ NGƯỜI
            # -------------------------------------------------------------
            if self.gv_canthiep_wizard_ids:
                for line in self.gv_canthiep_wizard_ids:
                    kehoach = line.kehoach_id
                    if not kehoach:
                        continue

                    # Chuẩn bị bộ giá trị thay đổi riêng cho từng kế hoạch
                    kehoach_vals = {}

                    # Kiểm tra thay đổi Giáo viên lập kế hoạch/can thiệp của dòng
                    if (line.gv_canthiep_id
                            and kehoach.gv_lapkehoach_id != line.gv_canthiep_id):
                        kehoach_vals['gv_lapkehoach_id'] = line.gv_canthiep_id.id


                    if kehoach_vals:
                        kehoach.write(kehoach_vals)

            # Trả về thông báo thành công và tự động đóng Popup Wizard lại (target="new")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thành công',
                    'message': 'Đã cập nhật phân công lại giáo viên thành công!',
                    'sticky': False,
                    'type': 'success',
                    'next': {'type': 'ir.actions.act_window_close'},  # Đóng popup sau khi thông báo hiện ra
                }
            }
