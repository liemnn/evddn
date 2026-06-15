from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
import re
from bs4 import BeautifulSoup


class MucTieu(models.Model):
    _name = "ekids.ct_muctieu"
    _description = "Lĩnh vực"
    _order = "sequence asc"

    coso_id = fields.Many2one("ekids.coso", related="linhvuc_id.coso_id", string="Cơ sở", required=True,ondelete="restrict")
    chuongtrinh_id = fields.Many2one("ekids.ct_chuongtrinh", related="linhvuc_id.chuongtrinh_id", string="Chương trình", required=True,
                              ondelete="restrict")

    sequence = fields.Integer(string="STT", default=1)
    index = fields.Integer(string="STT hiển thị", compute="_compute_index", store=False)
    index_list = fields.Integer(string="STT hiển thị", compute="_compute_index_list", store=False)
    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực',required=True)
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi',required=True)

    name = fields.Char(string="Tên",required=True)
    chucnang = fields.Html(string="Chức năng phát triển cốt lõi & Lập luận lâm sàng")
    thietke = fields.Html(string="Thiết kế hoạt động cho giáo viên Theo mô tả (ABC)")
    tieuchi_chuadat = fields.Char(string="Chưa đạt (-)",required=True)
    tieuchi_hinhthanh = fields.Char(string="Đang hình thành (+/-)",required=True)
    tieuchi_dat = fields.Char(string="Đạt (+)",required=True)

    @api.depends('linhvuc_id', 'sequence')
    def _compute_index(self):
        # 1. Gom nhóm các bản ghi thực tế đang hiển thị trên màn hình theo từng Lĩnh vực
        linhvuc_groups = {}
        for rec in self:
            linhvuc_groups.setdefault(rec.linhvuc_id.id, []).append(rec)

        # 2. Sắp xếp tuyến tính nội bộ từng nhóm và đánh số thứ tự từ 1 trở đi
        for lv_id, rec_list in linhvuc_groups.items():
            # Sắp xếp danh sách dựa trên sequence và id để đảm bảo thứ tự kéo thả không đổi
            sorted_list = sorted(rec_list, key=lambda r: (r.sequence, r.id))

            for idx, rec in enumerate(sorted_list, 1):
                rec.index = idx


    def _compute_index_list(self):
        index =1
        for record in self:
            record.index_list = index
            index +=1

    def action_luachon_ct_muctieu_vao_kehoach(self):
        self.ensure_one()  # Xử lý đích danh dòng vừa được bấm nút

        # Bốc các ID cấu trúc được truyền từ context ngầm của nút cha
        kehoach_id = self.env.context.get('default_kehoach_id')
        linhvuc_id = self.env.context.get('default_linhvuc_id')
        tuoi_id = self.env.context.get('default_tuoi_id')

        return self.action_chon_kehoach_muctieu()



    def action_chon_kehoach_muctieu(self):
        # Lấy ID của danh sách list view danh mục mục tiêu mẫu
        list_view_id = self.env.ref('ekids_canthiep.ct_muctieu_list').id

        return {
            'type': 'ir.actions.act_window',
            'name': 'LỰA CHỌN MỤC TIÊU CHO KẾ HOẠCH',
            'res_model': 'ekids.ct_muctieu',
            'view_mode': 'list',  # 🌟 SỬA TỪ 'form' THÀNH 'list' để hiện danh sách
            'views': [(list_view_id, 'list')],  # Chuẩn Odoo 18
            'target': 'new',  # Mở dạng Pop-up
            'context': {
                # Ép bộ lọc tự động chỉ hiển thị các mục tiêu thuộc Lĩnh vực và Độ tuổi này
                'search_default_linhvuc_id': self.linhvuc_id.id,
                'search_default_tuoi_id': self.tuoi_id.id,

                'edit': False,  # 🚫 Tắt hoàn toàn tính năng và ẩn nút [Sửa]
                'create': False,  # 🚫 Tắt tính năng và ẩn nút [Tạo mới]
                'delete': False,  # 🚫 Tắt tính năng và ẩn nút [Xóa]
            },
        }


    def func_chon_muctieu_vao_kehoach(self,kehoach_linhvuc_id):
        return None

