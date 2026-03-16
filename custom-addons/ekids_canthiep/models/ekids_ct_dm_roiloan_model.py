from odoo import models, fields, api, exceptions


class DanhMucRoiLoan(models.Model):
    _name = "ekids.ct_dm_roiloan"
    _description = "Dạng rồi loạn"

    coso_ids = fields.Many2many(comodel_name="ekids.coso",
                                relation="ekids_ct_dm_roiloan4coso_rel",
                                column1="dm_roiloan_id",
                                column2="coso_id"
                                , string="Áp dụng cho các cơ sở")
    ma = fields.Char(string="Mã")
    ten = fields.Char(string="Tên")
    name = fields.Char(string="Tên hiển thị", compute="_compute_ct_dm_roiloan_name", readonly=True)
    desc =fields.Html(string="Mô tả")

    def _compute_ct_dm_roiloan_name(self):
        for kh in self:
            if kh.ma:
                kh.name = '[' + kh.ma + ']-'
            if kh.ten:
                kh.name += kh.ten


