from odoo import models, fields, api, exceptions


class KeHoachThang(models.Model):
    _name = "ekids.kehoach_thang"
    _description = "[KẾ HOẠCH] THÁNG"

    kehoach_id = fields.Many2one("ekids.kehoach", string="Kế hoạch")
    name = fields.Selection([("1", "Tháng thứ 1"),
                             ("2", "Tháng thứ 2"),
                             ("3", "Tháng thứ 3"),
                             ("4", "Tháng thứ 4"),
                             ("5", "Tháng thứ 5"),
                             ("6", "Tháng thứ 6"),
                             ("7", "Tháng thứ 7"),
                             ("8", "Tháng thứ 8"),
                             ("9", "Tháng thứ 9"),
                             ("10", "Tháng thứ 10"),
                             ("11", "Tháng thứ 11"),
                             ("12", "Tháng thứ 12")]
                            , string="Tháng")

    tu_ngay = fields.Date(string="Can thiệp từ ngày")
    den_ngay = fields.Date(string="Can thiệp đến ngày")

    muctieu_ids = fields.One2many("ekids.kehoach_muctieu2thang",
                                  "kehoach_thang_id", string="Mục tiêu can thiệp")

    trangthai = fields.Selection([("0", "Đợi làm [Kế hoạch]")
                                     , ("1", "Đã gửi duyệt")
                                     , ("2", "Đã được duyệt")
                                     , ("3", "Đang can thiệp")
                                     , ("4", "Đã hoàn thành")
                                       ], string="Trạng thái [Can thiệp]"
                                 , default="0")
    tong_muctieu = fields.Integer(string="Tổng mục tiêu", readonly=True, compute="_compute_tong_muctieu")

    def _compute_tong_muctieu(self):
        for thang in self:
            total = self.env['ekids.kehoach_muctieu2thang'].search_count([('kehoach_thang_id', '=', thang.id)])
            thang.tong_muctieu = total


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        result = super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)

        if groupby and groupby[0] == 'trangthai':
            # 1. Lấy danh sách tất cả các giá trị của field selection
            selection_values = self.fields_get(allfields=['trangthai'])['trangthai']['selection']

            # 2. Chuyển thành dict: {'draft': 'Nháp', ...}
            selection_dict = dict(selection_values)

            # 3. Lấy danh sách key đã có trong kết quả
            existing_keys = [r['trangthai'] for r in result]

            # 4. Thêm các key còn thiếu (chưa có record nào nhưng vẫn cần hiển thị)
            for key in selection_dict:
                if key not in existing_keys:
                    result.append({
                        'trangthai': key,
                        'trangthai_count': 0,
                        '__count': 0,
                    })

            # 5. Sắp xếp theo thứ tự mong muốn
            desired_order = ['0', '1', '2']  # <-- sửa theo field của bạn
            result.sort(key=lambda r: desired_order.index(r['trangthai']) if r['trangthai'] in desired_order else 999)

        return result


    def action_xem_kehoach_hocsinh_muctieu_theo_thang_phucvu_canthiep(self):
        self.ensure_one()
        kanban_view_id = self.env.ref('ekids_hocsinh.kehoach_muctieu2thang_canthiep_kanban_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'MỤC TIÊU',
            'res_model': 'ekids.kehoach_muctieu2thang',
            'view_mode': 'kanban,list,form',
            'views': [
                (kanban_view_id, 'kanban'),
                # Thêm form view ở đây nếu có sẵn ID (tuỳ chọn, không bắt buộc)
                # (form_view_id, 'form'),
            ],
            'target': 'current',
            'domain': [('kehoach_thang_id', '=', self.id)],
            'context': dict(
                self.env.context,
                default_kehoach_thang_id=self.id,
                create_popup=True,
                form_view_initial_mode='edit',
            ),
        }


    def action_sua_kehoach_thang(self):
        self.ensure_one()


        return {
            'type': 'ir.actions.act_window',
            'name': 'KẾ HOẠCH CAN THIỆP [THÁNG]',
            'res_model': 'ekids.kehoach_thang',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('kehoach_id','=',self.id)],
            'context': dict(
                self.env.context,
                default_kehoach_id=self.id,
            ),
        }








