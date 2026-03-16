from odoo import models, fields, api, exceptions


class MauKeHoachCanThiepThang(models.Model):
    _name = "ekids.mau_kehoach_muctieu2thang"
    _description = "MẪU [KẾ HOẠCH] THÁNG"

    sequence = fields.Integer(string="STT", default=10)
    mau_kehoach_id = fields.Many2one("ekids.mau_kehoach", string="Mẫu kế hoạch")
    mau_kehoach_thang_id = fields.Many2one('ekids.mau_kehoach_thang',string="Tháng")

    name =fields.Char(string="Chương trình/Lĩnh vực/Cấp độ", compute="_compute_muctieu_name",readonly=True)
    chuongtrinh_id = fields.Many2one('ekids.ct_chuongtrinh', string='Chương trình')
    linhvuc_id = fields.Many2one('ekids.ct_linhvuc', string='Lĩnh vực')
    capdo_id = fields.Many2one('ekids.ct_dm_capdo', string='Cấp độ')
    muctieu_id = fields.Many2one('ekids.ct_muctieu', string='Mục tiêu')
    domain_muctieu_ids = fields.Many2many('ekids.ct_muctieu', compute='_compute_domain_muctieu')


    @api.depends('chuongtrinh_id', 'linhvuc_id', 'capdo_id')
    def _compute_domain_muctieu(self):
        for rec in self:
            domain = []
            if rec.linhvuc_id:
                domain.append(('linhvuc_id', '=', rec.linhvuc_id.id))
            if rec.capdo_id:
                domain.append(('dm_capdo_id', '=', rec.capdo_id.id))

            rec.domain_muctieu_ids = self.env['ekids.ct_muctieu'].search(domain)

    def _compute_muctieu_name(self):
        for muctieu in self:
            ct_ma = muctieu.muctieu_id.linhvuc_id.chuongtrinh_id.ma
            ct_linhvuc = muctieu.muctieu_id.linhvuc_id.name
            capdo =muctieu.muctieu_id.dm_capdo_id.name
            muctieu.name = "["+str(ct_ma).upper()+"]" +str(ct_linhvuc) +"("+str(capdo)+")"


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        result = super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        # Nếu groupby là 'model_a_id', ta thêm các nhóm không có bản ghi
        if 'mau_kehoach_thang_id' in groupby:
            group_ids = set(r['mau_kehoach_thang_id'][0] for r in result if r['mau_kehoach_thang_id'])
            # Lọc các bản ghi model.a phù hợp điều kiện
            valid_a_records = self.env['ekids.ct_mau_kehoach_thang'].search([])
            for a in valid_a_records:
                if a.id not in group_ids:
                    result.append({
                        'mau_kehoach_thang_id': (a.id, a.name),
                        '__domain': [('mau_kehoach_thang_id', '=', a.id)],
                        '__context': {'group_by': groupby},
                        '__count': 0,
                    })
        return result