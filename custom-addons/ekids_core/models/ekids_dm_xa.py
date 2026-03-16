from odoo import models, fields, api, _


class DanhMucXa(models.Model):

    _name = "ekids.dm_xa"
    _description = "Mô tả về danh mục tỉnh "
    dm_tinh_id = fields.Many2one("ekids.dm_tinh", string="Tỉnh")

    code = fields.Char(string="Mã ", required=True)
    name = fields.Char(string="Tên",required=True)
    desc = fields.Html(string="Mô tả")
    json = fields.Char(string="Thuộc tính mở rộng")

    _sql_constraints = [
        ('unique_dm_xa',
         'UNIQUE(dm_tinh_id,name)',
         'Đã tồn tại thiệt lập Xã  vui lòng kiểm tra lại !')
    ]

