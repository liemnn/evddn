from odoo import models, fields, api, exceptions


class MauKeHoachCanThiep(models.Model):
    _name = "ekids.mau_kehoach"
    _description = "Lĩnh vực"

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở")
    name = fields.Char(string="Tên",compute="_compute_mau_name", readonly=True)
    tacgia = fields.Char(string="Tác giả",compute="_compute_mau_tacgia", readonly=True)
    sothang = fields.Selection([("1", "1 Tháng"),
                                ("2", "2 Tháng"),
                                ("3", "3 Tháng"),
                                ("4", "4 Tháng"),
                                ("5", "5 Tháng"),
                                ("6", "6 Tháng"),
                                ("7", "7 Tháng"),
                                ("8", "8 Tháng"),
                                ("9", "9 Tháng"),
                                ("10", "10 Tháng"),
                                ("11", "11 Tháng"),
                                ("12", "12 Tháng")],
                               string="Số tháng lập [Kế hoạch]")

    rating_count = fields.Integer("Số lượt đánh giá", compute="_compute_mau_rating")
    rating_avg = fields.Float("Điểm trung bình", compute="_compute_mau_rating")
    mau_review_ids = fields.One2many("ekids.mau_kehoach_review", "mau_kehoach_id", string="Đánh giá")
    desc =fields.Html(string="Mô tả")


    gioitinh = fields.Selection([("0", "Nữ"), ("1", "Nam")], string="Giới tính")
    dm_tuoi_id = fields.Many2one("ekids.ct_dm_tuoi", string="Tuổi can thiệp của trẻ")
    chinh_dm_roiloan_id = fields.Many2one("ekids.ct_dm_roiloan", string="Dạng [Rối loạn] chính")
    chinh_ct_chuongtrinh_id = fields.Many2one("ekids.ct_chuongtrinh", string="[Chương trình] can thiệp")
    chinh_dm_capdo_id = fields.Many2one("ekids.ct_dm_capdo", string="[Cấp độ] can thiệp")
    roiloan_dikem_ids = fields.One2many("ekids.mau_kehoach_roiloan_dikem",
                                  "mau_kehoach_id", string="Rối loạn đi kèm",ondelete='cascade')

    @api.depends('mau_review_ids')
    def _compute_mau_rating(self):
        for record in self:
            if record.mau_review_ids:
                ratings = record.mau_review_ids.mapped('rating')
                values = [int(r) for r in ratings if r]
                record.rating_count = len(values)
                record.rating_avg = sum(values) / len(values) if values else 0
            else:
                record.rating_count = 0
                record.rating_avg = 0.0


    def _compute_mau_tacgia(self):
        for record in self:
            tacgia ="VDDN"
            if record.tacgia:
                tacgia =record.coso_id.name
            record.tacgia= tacgia
    def _compute_mau_name(self):
        for kh in self:
            name =""
            if kh.chinh_dm_roiloan_id and kh.chinh_dm_roiloan_id.ten:
                name = str(kh.chinh_dm_roiloan_id.ten)
                if kh.roiloan_dikem_ids:
                    name +="-(Rối loạn đi kèm:"
                    for rl in kh.roiloan_dikem_ids:
                        name += str(rl.dm_roiloan_id.ten) +"/"
                    name += ")"
            kh.name=name


    #ham phuc vu tim kiem cho lập kế hoạch
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100) -> list[tuple[int, str]]:
        if args is None:
            args = []
        # Kiểm tra context từ view có truyền hay không
        chinh_dm_roiloan_id = self.env.context.get('chinh_dm_roiloan_id')
        dikem_dm_roiloan_ids = self.env.context.get('dikem_dm_roiloan_ids')
        gioitinh = self.env.context.get('gioitinh')
        dm_tuoi_id = self.env.context.get('dm_tuoi_id')

        if (self.env.context.get('lap_kehoach_chon_mau_filter')
                and chinh_dm_roiloan_id):
            if dikem_dm_roiloan_ids and len(dikem_dm_roiloan_ids)>0:
                query = """
                    SELECT mau.id
                        FROM ekids_mau_kehoach mau
                        join ekids_mau_kehoach_roiloan_dikem dk on dk.mau_kehoach_id =mau.id 
                        WHERE
                        mau.chinh_dm_roiloan_id =%s
                        AND dk.dm_roiloan_id IN %s
                    """
                if gioitinh:
                    query += " AND mau.gioitinh = %s "
                if dm_tuoi_id:
                    query += " AND mau.dm_tuoi_id = %s "

                query += """
                        GROUP BY mau.id
                        HAVING COUNT(DISTINCT dk.dm_roiloan_id) = %s
    
                    """
                conditions = [chinh_dm_roiloan_id, tuple(dikem_dm_roiloan_ids)]

                if gioitinh:
                    conditions.append(gioitinh)
                if dm_tuoi_id:
                    conditions.append(dm_tuoi_id)

                conditions.append(len(dikem_dm_roiloan_ids))

                self.env.cr.execute(query, conditions)
                result= [row[0] for row in self.env.cr.fetchall()]
                if result:
                    args += [('id', 'in', result)]
                else:
                    args += [('id', '=', -1)]
            else:
                args += [('chinh_dm_roiloan_id', '=', chinh_dm_roiloan_id)]

        return super().name_search(name=name, args=args, operator=operator, limit=limit)




    def action_view_ekid_canthiep_kanban_mau_kehoach_thang(self):
        self.func_ekid_canthiep_tao_mau_kehoach_thang()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'ekids.mau_kehoach_thang',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('mau_kehoach_id', '=', self.id)],
            'context':{
                'default_mau_kehoach_id':self.id
            }

        }

    def func_ekid_canthiep_tao_mau_kehoach_thang(self):
        count = self.env['ekids.mau_kehoach_thang'].search_count(
            [('mau_kehoach_id', '=', self.id)])
        if count <= 0:
                for i in range(1, 7):
                    data = {
                        'mau_kehoach_id': self.id,
                        'name': str(i)

                    }
                    self.env['ekids.mau_kehoach_thang'].create(data)



    def action_luachon_mau_kehoach(self):
        active_id = self.env.context.get('active_id')
        mau_kehoach_id = self.env.context.get('mau_kehoach_id')
        kehoach_id = self.env.context.get('kehoach_id')
        if mau_kehoach_id and kehoach_id:
            if active_id and mau_kehoach_id:
                self.env['ekids.kehoach'].browse(kehoach_id).write({
                    'mau_kehoach_id':mau_kehoach_id
                })
                return {'type': 'ir.actions.act_window_close'}
            else:
                # Trường hợp tạo mới
                return {
                    'type': 'ir.actions.act_window_close',
                    'context': {'default_mau_kehoach_id': mau_kehoach_id}
                }
        else:
            return {
                'type': 'ir.actions.act_window_close',
                'context': {'default_mau_kehoach_id': 0}
            }









