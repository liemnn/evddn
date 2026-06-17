from odoo import models, fields, api, exceptions


class ChuongTrinh(models.Model):
    _name = "ekids.ct_chuongtrinh"
    _description = "CHƯƠNG TRÌNH CAN THIỆP"

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    name = fields.Char(string="Tên (viết tắt)",required=True)
    title = fields.Char(string="Tên chương trình", required=True)
    desc =fields.Html(string="Mô tả")
    coso_ids = fields.Many2many(comodel_name="ekids.coso",
                                relation="ekids_ct_chuongtrinh4coso_ids_rel",
                                column1="ct_chuongtrinh_id",
                                column2="coso_id"
                                , string="Các cơ sở áp dụng")

    linhvuc_ids = fields.One2many("ekids.ct_linhvuc",
                                  "chuongtrinh_id", string="Lĩnh vực")
    tuoi_ids = fields.One2many("ekids.ct_tuoi",
                                  "chuongtrinh_id", string="Độ tuổi")

    muctieu_ids = fields.One2many("ekids.ct_muctieu",
                               "chuongtrinh_id", string="Độ tuổi")

    tong_tuoi = fields.Integer(string="Tổng cấp độ",compute="_compute_tong_tuoi",store=False)
    tong_linhvuc = fields.Integer(string="Tổng lĩnh vực",compute="_compute_tong_linhvuc",store=False)
    tong_muctieu = fields.Integer(string="Tổng mục tiêu",compute="_compute_tong_muctieu",store=False)

    trangthai = fields.Selection([("0", "Không hoạt động")
                                     , ("1", "Đang hoạt động")], default="1", required=True)

    def _compute_tong_tuoi(self):
        for ct in self:
            count = self.env['ekids.ct_tuoi'].search_count([('chuongtrinh_id','=',ct.id)])
            if count:
                ct.tong_tuoi =count
            else:
                ct.tong_tuoi = 0

    def _compute_tong_linhvuc(self):
        for ct in self:
            count = self.env['ekids.ct_linhvuc'].search_count([('chuongtrinh_id','=',ct.id)])
            if count:
                ct.tong_linhvuc =count
            else:
                ct.tong_linhvuc = 0
    def _compute_tong_muctieu(self):
        for ct in self:
            count = self.env['ekids.ct_muctieu'].search_count([('linhvuc_id.chuongtrinh_id','=',ct.id)])
            if count:
                ct.tong_muctieu =count
            else:
                ct.tong_muctieu = 0

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=50, order=None):
        # Lấy thông tin người dùng hiện tại
        user = self.env.user
        # TH3: user khác của cơ sở ( thường là giáo viên được phân quyền)
        # sẽ tính trên danh sách các cơ sở được phân cho user này
        if user.coso_ids:
            ids = user.coso_ids
            if len(ids) > 0:
                domain += [('coso_id', 'in', ids)]


        return super().search_fetch(domain, field_names, offset, limit, order)

    def action_xem_tuoi(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "ĐỘ TUỔI",
            'res_model': 'ekids.ct_tuoi',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('chuongtrinh_id', '=', self.id)],
            'context':{
                'default_chuongtrinh_id':self.id
            }

        }

    def action_xem_linhvuc(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "LĨNH VỰC",
            'res_model': 'ekids.ct_linhvuc',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('chuongtrinh_id', '=', self.id)],
            'context':{
                'default_chuongtrinh_id':self.id
            }

        }

    def action_xem_muctieu(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "MỤC TIÊU",
            'res_model': 'ekids.ct_muctieu',
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'domain': [('chuongtrinh_id', '=', self.id)],
            'context': {
                'default_chuongtrinh_id': self.id
            }

        }

