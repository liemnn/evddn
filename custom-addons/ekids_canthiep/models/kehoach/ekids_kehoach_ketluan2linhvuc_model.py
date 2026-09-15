from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KetLuan2LinhVuc(models.Model):
    _name = 'ekids.kehoach_ketluan2linhvuc'
    _description = 'Các lĩnh vực thuộc kết luận'
    _order = 'sequence asc,id desc'

    sequence = fields.Integer(string="STT", default=1)
    ketluan_id = fields.Many2one("ekids.kehoach_ketluan", string="Thuộc kết luận nào",
                                 required=True,
                                 ondelete="cascade")


    chuongtrinh_id = fields.Many2one("ekids.ct_chuongtrinh", related="linhvuc_id.chuongtrinh_id"
                                     , string="Chương trình")



    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực', required=True, ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi', required=True, ondelete="cascade")

    tong_muctieu = fields.Integer(string="Tổng mục tiêu",compute="_compute_tong_muctieu")

    @api.depends("chuongtrinh_id","linhvuc_id","tuoi_id")
    def _compute_tong_muctieu(self):
        for record in self:

            domain =[('linhvuc_id','=',record.linhvuc_id.id)
                ,('tuoi_id','=',record.tuoi_id.id)]
            tong_muctieu = self.env['ekids.ct_muctieu'].search_count(domain)
            record.tong_muctieu = tong_muctieu

    def action_xem_danhsach_muctieu(self):
        # Lấy ID của danh sách list view danh mục mục tiêu mẫu
        list_view_id = self.env.ref('ekids_canthiep.ct_muctieu_list').id
        domain=[('linhvuc_id','=',self.linhvuc_id.id)
            ,('tuoi_id','=',self.tuoi_id.id)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'LỰA CHỌN MỤC TIÊU CHO KẾ HOẠCH',
            'res_model': 'ekids.ct_muctieu',
            'view_mode': 'list',  # 🌟 SỬA TỪ 'form' THÀNH 'list' để hiện danh sách
            'views': [(list_view_id, 'list')],  # Chuẩn Odoo 18
            'target': 'new',  # Mở dạng Pop-up
            'domain:':domain,
            'context': {
                # Ép bộ lọc tự động chỉ hiển thị các mục tiêu thuộc Lĩnh vực và Độ tuổi này
                'search_default_linhvuc_id': self.linhvuc_id.id,
                'search_default_tuoi_id': self.tuoi_id.id,

                'edit': False,  # 🚫 Tắt hoàn toàn tính năng và ẩn nút [Sửa]
                'create': False,  # 🚫 Tắt tính năng và ẩn nút [Tạo mới]
                'delete': False,  # 🚫 Tắt tính năng và ẩn nút [Xóa]
            },
        }
