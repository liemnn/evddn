from odoo import models, fields, api, _

class DanhMucTinh(models.Model):
    _name = "ekids.dm_tinh"
    _description = "Mô tả về danh mục tỉnh "
    code = fields.Char(string="Mã ", required=True)
    name = fields.Char(string="Tên",required=True)
    desc = fields.Html(string="Mô tả")
    json = fields.Char(string="Thuộc tính mở rộng")
    dm_xa_ids = fields.One2many("ekids.dm_xa", "dm_tinh_id"
                                        , string="Các xã trực thuộc")

    _sql_constraints = [
        ('unique_dm_tinh',
         'UNIQUE(name)',
         'Đã tồn tại thiệt lập Tỉnh  vui lòng kiểm tra lại !')
    ]
