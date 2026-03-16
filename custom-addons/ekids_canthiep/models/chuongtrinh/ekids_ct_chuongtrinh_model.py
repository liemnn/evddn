from odoo import models, fields, api, exceptions


class ChuongTrinh(models.Model):
    _name = "ekids.ct_chuongtrinh"
    _description = "CHƯƠNG TRÌNH CAN THIỆP"

    ma = fields.Char(string="Mã")
    ten = fields.Char(string="Tên")
    name = fields.Char(string="Tên hiển thị",compute="_compute_ct_chuongtrinh_name",readonly=True)
    desc =fields.Html(string="Mô tả")
    coso_ids = fields.Many2many(comodel_name="ekids.coso",
                                relation="ekids_ct_chuongtrinh4coso_ids_rel",
                                column1="ct_chuongtrinh_id",
                                column2="coso_id"
                                , string="Các cơ sở áp dụng")

    linhvuc_ids = fields.One2many("ekids.ct_linhvuc",
                                  "chuongtrinh_id", string="Lĩnh vực")

    tong_capdo = fields.Integer(string="Tổng cấp độ",compute="_compute_ct_chuongtrinh_tong_capdo",store=False)
    tong_linhvuc = fields.Integer(string="Tổng lĩnh vực",compute="_compute_ct_chuongtrinh_tong_linhvuc",store=False)
    tong_muctieu = fields.Integer(string="Tổng mục tiêu",compute="_compute_ct_chuongtrinh_tong_muctieu",store=False)


    def _compute_ct_chuongtrinh_name(self):
        for kh in self:
            if kh.ma:
                kh.name = '[' +kh.ma+']-'
            if kh.ten:
                kh.name += kh.ten

    def _compute_ct_chuongtrinh_tong_capdo(self):
        for ct in self:
            count = self.env['ekids.ct_dm_capdo'].search_count([('chuongtrinh_id','=',ct.id)])
            if count:
                ct.tong_capdo =count
            else:
                ct.tong_capdo = 0

    def _compute_ct_chuongtrinh_tong_linhvuc(self):
        for ct in self:
            count = self.env['ekids.ct_linhvuc'].search_count([('chuongtrinh_id','=',ct.id)])
            if count:
                ct.tong_linhvuc =count
            else:
                ct.tong_linhvuc = 0
    def _compute_ct_chuongtrinh_tong_muctieu(self):
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

        # Điều kiện lọc (ví dụ: chỉ cho phép xem các đơn hàng có đối tác là khách hàng của user)
        if user.has_group('base.group_system'):  # Kiểm tra nhóm quyền
            # TH1: là admin của toàn hệ thống
            domain = []  # Thêm điều kiện cho

        else:
           if user.has_group('ekids_core.ql_ct_canthiep'):
                # TH3: user khác của cơ sở ( thường là giáo viên được phân quyền)
                # sẽ tính trên danh sách các cơ sở được phân cho user này
                if user.coso_ids:
                    domain = ['|']
                    domain += [('coso_ids','=',False)]
                    domain +=[('coso_ids', 'in', user.coso_ids.ids)]# Thêm điều kiện cho

        return super().search_fetch(domain, field_names, offset, limit, order)


    def action_view_ekid_canthiep_kanban_linhvuc(self):
        return {
            'type': 'ir.actions.act_window',
            'name': self.ma,
            'res_model': 'ekids.ct_linhvuc',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('chuongtrinh_id', '=', self.id)],
            'context':{
                'default_chuongtrinh_id':self.id
            }

        }
    def action_view_ekid_canthiep_kanban_dm_capdo(self):
        return {
            'type': 'ir.actions.act_window',
            'name': self.ma,
            'res_model': 'ekids.ct_dm_capdo',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('chuongtrinh_id', '=', self.id)],
            'context':{
                'default_chuongtrinh_id':self.id
            }

        }