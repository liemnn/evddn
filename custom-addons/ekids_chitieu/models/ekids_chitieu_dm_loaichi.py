from odoo import models, fields, api, _


class LoaiChiTieu(models.Model):
    _name = 'ekids.chitieu_dm_loaichi'
    _description = 'Mô tả về các nhóm/loại chi tiêu'

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True,ondelete="restrict")
    name = fields.Char(string='Tên',required=True)
    loai = fields.Selection([("0", "Chi"), ("1", "Thu")
                                     ], string="Phân loại",required=True,default="0")

    desc = fields.Html(string="Mô tả")
    trangthai = fields.Selection([("0", "Không hoạt động")
                                     , ("1", "Đang hoạt động")], default="1", required=True)

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=50, order=None):
        # Lấy thông tin người dùng hiện tại
        user = self.env.user
        context = self.env.context

        domain += [('coso_id', '=', context.get('default_coso_id'))]  # Thêm điều kiện cho
        return super().search_fetch(domain, field_names, offset, limit, order)


