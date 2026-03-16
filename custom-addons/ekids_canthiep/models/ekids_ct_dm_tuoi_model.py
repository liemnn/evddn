from odoo import models, fields, api, exceptions


class DanhMucTuoi(models.Model):
    _name = "ekids.ct_dm_tuoi"
    _description = "Tuổi thực tế"

    coso_ids = fields.Many2many(comodel_name="ekids.coso",
                                relation="ekids_ct_dm_tuoi4coso_rel",
                                column1="ct_dm_tuoi_id",
                                column2="coso_id"
                                , string="Áp dụng cho các cơ sở")
    ma = fields.Char(string="Mã")
    ten = fields.Char(string="Tên")
    name = fields.Char(string="Tên hiển thị", compute="_compute_ct_dm_tuoi_name", readonly=True)
    desc =fields.Html(string="Mô tả")

    def _compute_ct_dm_tuoi_name(self):
        for kh in self:
            if kh.ma:
                kh.name = '[' + kh.ma + ']-'
            if kh.ten:
                kh.name += kh.ten


