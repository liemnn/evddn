from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from odoo.exceptions import UserError

class TimKiemMau2KeHoach(models.TransientModel):
    _name = 'ekids.kehoach_timkiem_mau'
    _description = 'Chọn một mẫu cho kê hoạch'



    chinh_dm_roiloan_id = fields.Many2one("ekids.ct_dm_roiloan", string="Rối loạn chính")

    dikem_dm_roiloan_ids = fields.Many2many(comodel_name="ekids.ct_dm_roiloan",
                                            relation="ekids_kehoach_timkiem_mau4dikem_dm_roiloan_ids_rel",
                                            column1="kehoach_timkiem_mau_id",
                                            column2="ct_dm_roiloan_od",
                                           string="Rối loạn [Đi kèm]")
    is_advanced_search = fields.Boolean(string="Tìm kiếm nâng cao")

    gioitinh = fields.Selection([("0", "Nữ"), ("1", "Nam")], string="Giới tính")
    dm_tuoi_id = fields.Many2one("ekids.ct_dm_tuoi", string="Tuổi can thiệp của trẻ")

    mau_kehoach_ids = fields.Many2many("ekids.mau_kehoach",
                                       relation="ekids_kehoach_timkiem_mau4mau_kehoach_ids_rel",
                                       column1="kehoach_timkiem_mau_id",
                                       column2="mau_kehoach_id",
        compute="_compute_mau_kehoach_ids",
        string="Danh sách kết quả [Mẫu] Kế hoạch"
    )

    kehoach_id = fields.Many2one('ekids.kehoach', string="Kế hoạch", required=True)

    @api.depends('chinh_dm_roiloan_id','dikem_dm_roiloan_ids','gioitinh','dm_tuoi_id')
    def _compute_mau_kehoach_ids(self):
        for record in self:
            try:
                record.mau_kehoach_ids = []  # gán rỗng trước tiên

                # Nếu chưa đủ dữ liệu để tìm kiếm ⇒ giữ nguyên là []
                if not record.chinh_dm_roiloan_id:
                    continue

                ids = record.func_search_mau_kehoach(
                    record.chinh_dm_roiloan_id,
                    record.dikem_dm_roiloan_ids,20
                ) or []

                if ids:
                    record.mau_kehoach_ids = self.env['ekids.mau_kehoach'].search([('id', 'in', ids)])

            except Exception as e:
                _logger.error("Compute lỗi ở record ID %s: %s", record.id, e)
                record.mau_kehoach_ids = []  # gán lại để đảm bảo không lỗi

    def func_search_mau_kehoach(self, chinh_dm_roiloan_id, dikem_dm_roiloan_ids,limit=20):
        conditions = ()
        if chinh_dm_roiloan_id:
            query = """
                SELECT mau.id
                FROM ekids_mau_kehoach mau
                JOIN ekids_mau_kehoach_roiloan_dikem dk ON dk.mau_kehoach_id = mau.id 
                WHERE
                    mau.chinh_dm_roiloan_id = %s
                """
            if dikem_dm_roiloan_ids:
                query +=" AND dk.dm_roiloan_id IN %s "
            query+= "GROUP BY mau.id"
            if dikem_dm_roiloan_ids:
                query += " HAVING COUNT(DISTINCT dk.dm_roiloan_id) = %s "
            query += " LIMIT %s"

            conditions += (chinh_dm_roiloan_id.id,)
            if dikem_dm_roiloan_ids:
                conditions += (tuple(dikem_dm_roiloan_ids.ids),)
                conditions += (len(dikem_dm_roiloan_ids.ids),)
            conditions += (limit,)

            self.env.cr.execute(query,conditions)
            result = [row[0] for row in self.env.cr.fetchall()]
            return result
        return []  # Bắt buộc phải return danh sách



    def action_chon_mau_cho_kehoach(self):
        return {
            'name': 'Chọn [Mẫu] cho lập kế hoạch',
            'type': 'ir.actions.act_window',
            'res_model': 'ekids.mau_kehoach',
            'view_mode': 'kanban',
            'views': [(False, 'kanban')],
            'target': 'new',
            'context': {
                'teacher_filter_name': self.name,
                'teacher_filter_subject': self.subject,
                'active_student_id': self.env.context.get('active_id')
            },
            'domain': [
                '|', ('name', 'ilike', self.name or ''),
                ('subject', 'ilike', self.subject or '')
            ]
        }







