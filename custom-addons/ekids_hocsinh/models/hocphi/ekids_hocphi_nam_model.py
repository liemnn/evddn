from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import ValidationError
import calendar
class HocPhiNam(models.Model):
    _name = 'ekids.hocphi_nam'
    _description = 'Học phí theo năm Cơ sở'
    _order = "id desc"


    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    name = fields.Selection([(str(year), str(year)) for year in range(datetime.now().year - 1, datetime.now().year + 1)],string="Năm",required=True,index=True)

    tong_hocsinh = fields.Integer(string="Tổng học sinh", readonly=True, compute="_compute_tong_hocsinh")
    tong_hocphi = fields.Float(string="Tổng học phí", readonly=True, compute="_compute_tong_hocphi")
    tong_hocphi_giam = fields.Float(string="Tổng tiền giảm học phí",digits=(10, 0), readonly=True,
                                      compute="_compute_tong_hocphi_giam")
    tong_hocphi_thucthu = fields.Float(string="Tổng học phí thực thu",digits=(10, 0), readonly=True,
                                         compute="_compute_tong_hocphi_thucthu")

    _sql_constraints = [
        ('unique_hocphi_nam',
         'UNIQUE(coso_id, name)',
         'Đã tồn tại học phí "Năm" này của cơ sở, vui lòng kiểm tra lại !')
    ]

    @api.constrains('coso_id', 'name')
    def _check_unique_hocphi_nam(self):
        for record in self:
            # Tìm các bản ghi khác có cùng 'code'
            count = self.env['ekids.hocphi_nam'].search_count([
                ('id', '!=', record.id),
                ('coso_id', '=', record.coso_id.id),
                ('name', '=', record.name),

            ])
            if count > 0:
                raise ValidationError("Năm để tính học phí đã tồn tại !")

    def _compute_tong_hocsinh(self):
        for nam in self:
            result = self.env['ekids.hocphi'].read_group(
                [('thang_id.nam_id','=',nam.id)],  # Không lọc gì cả
                ['id:count'],  # Đếm số lượng bản ghi (COUNT(id))
                ['hocsinh_id']  # Nhóm theo 'trangthai'
            )
            nam.tong_hocsinh =len(result)


    def _compute_tong_hocphi(self):
        for nam in self:
            result = self.env['ekids.hocphi'].read_group(
                domain=[('thang_id.nam_id', '=', nam.id)],  # điều kiện lọc (nếu cần)
                fields=['hocphi'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['hocphi'] if result else 0.0
            nam.tong_hocphi = total

    def _compute_tong_hocphi_giam(self):
        for nam in self:
            result = self.env['ekids.hocphi'].read_group(
                domain=[('thang_id.nam_id', '=', nam.id)],  # điều kiện lọc (nếu cần)
                fields=['hocphi_giam'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['hocphi_giam'] if result else 0.0
            nam.tong_hocphi_giam = total

    def _compute_tong_hocphi_thucthu(self):
        for nam in self:
            result = self.env['ekids.hocphi'].read_group(
                domain=[('thang_id.nam_id', '=', nam.id)],  # điều kiện lọc (nếu cần)
                fields=['hocphi_phaidong'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['hocphi_phaidong'] if result else 0.0
            nam.tong_hocphi_thucthu = total

    def action_form_hocphi_nam(self):
        """action view year tuition"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mở Form Cấu Hình',
            'res_model': 'ekids.hocphi_nam',
            'view_mode': 'form',
            'res_id': self.id,
        }
    def action_view_kanban_hocphi_thang(self):
        """action view year tuition"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'NĂM '+self.name.upper(),
            'res_model': 'ekids.hocphi_thang',
            'view_mode': 'kanban,list,form',
            'domain': [('nam_id', '=', self.id)],
            'context': {
                'default_nam_id': self.id,
                'default_coso_id': self.coso_id.id
            }
        }