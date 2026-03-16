from odoo import api, fields, models
from datetime import datetime,date
from odoo.exceptions import UserError
import calendar
class LuongNam(models.Model):
    _name = 'ekids.luong_nam'
    _description = 'Lương của một năm của trung tâm'
    _order = "id desc"


    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    name = fields.Selection([(str(year), str(year))
                             for year in range(datetime.now().year - 1,
                                               datetime.now().year + 1)],string="Năm",required=True)
    tong_luong =fields.Float(string="Tổng lương chi trả",digits=(10, 0),compute="_compute_tong_luong")
    tong_giaovien = fields.Integer(string="Tổng số giáo viên",compute="_compute_tong_giaovien")

    _sql_constraints = [
        ('unique_luong_nam',
         'UNIQUE(coso_id,name)',
         'Đã tồn tại [Bảng lương Năm]  của cơ sở, vui lòng kiểm tra lại !')
    ]

    def _compute_tong_luong(self):
        for rec in self:
            result = self.env['ekids.luong'].read_group(
                domain=[('coso_id','=',rec.coso_id.id)
                        ,('nam_id', '=', rec.id)],  # điều kiện lọc (nếu cần)
                fields=['tong_nhatruong_chi'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )
            total=0.0
            try:
                total = result[0]['tong_nhatruong_chi']
            except:
                total=0.0
            rec.tong_luong = total

    def _compute_tong_giaovien(self):


        for rec in self:
            start_year = date(int(rec.name), 1, 1)
            end_year = date(int(rec.name), 12, 31)

            total = self.env['ekids.giaovien'].search_count([
                ('coso_id', '<=', rec.coso_id.id),
                ('dilam_tungay', '<=', end_year),
                '|',
                ('dilam_denngay', '=', False),
                ('dilam_denngay', '>=', start_year)
            ])
            rec.tong_giaovien= total

    def action_form_luong_nam(self):
        """action view year tuition"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mở Form Cấu Hình',
            'res_model': 'ekids.luong_nam',
            'view_mode': 'form',
            'res_id': self.id,
        }
    def action_view_kanban_luong_thang(self):
        """action view year tuition"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'LƯƠNG NĂM:'+self.name,
            'res_model': 'ekids.luong_thang',
            'view_mode': 'kanban,list,form',
            'domain': [('nam_id', '=', self.id)],
            'context': {
                'default_nam_id': self.id,
                'default_coso_id': self.coso_id.id
            }
        }

    #xoa ban ghi

    def action_delete_luong_nam(self):
        count = self.env['ekids.luong_thang'].search_count(
            [('coso_id', '=', self.coso_id.id)
                , ('nam_id', '=', self.id)])
        if count > 0 :
            raise UserError("Đã tôn tại việc tính Lương cho Giáo viên tại Tháng trong Năm:"
                            +self.name
                            +". Bạn không thể xóa bản ghi này!")
        else:
            return self.unlink()
