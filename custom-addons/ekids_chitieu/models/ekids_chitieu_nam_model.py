from odoo import models, fields, api, _

from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class ChiTieuNam(models.Model):
    _name = "ekids.chitieu_nam"
    _description = "Mô tả về chi tiêu hàng năm"


    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True,ondelete="restrict")
    name = fields.Selection([(str(year), str(year))
                             for year in range(datetime.now().year - 1,
                                               datetime.now().year + 1)], string="Năm",required=True)
    tong_chi = fields.Integer(string="Tổng chi", readonly=True, compute="_compute_tong_chi_nam")
    tong_thu = fields.Integer(string="Tổng chi", readonly=True, compute="_compute_tong_thu_nam")

    _sql_constraints = [
        ('unique_chitieu_nam',
         'UNIQUE(coso_id,name)',
         'Đã tồn tại chi tiêu "của Năm"  của cơ sở, vui lòng kiểm tra lại !')
    ]

    # tong chi tieu
    def _compute_tong_chi_nam(self):
        for nam in self:
            result = self.env['ekids.chitieu_chi'].read_group(
                domain=[('thang_id.nam_id', '=', nam.id)],  # điều kiện lọc (nếu cần)

                fields=['tien'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['tien'] if result else 0.0
            nam.tong_chi = total

    def _compute_tong_thu_nam(self):
        for nam in self:
            result = self.env['ekids.chitieu_thu'].read_group(
                domain=[('thang_id.nam_id', '=', nam.id)],  # điều kiện lọc (nếu cần)
                fields=['tien'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['tien'] if result else 0.0
            nam.tong_thu = total

    def action_view_kanban_chitieu_thang(self):
        """action view year tuition"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'NĂM ' + str(self.name).upper(),
            'res_model': 'ekids.chitieu_thang',
            'view_mode': 'kanban,list,form',
            'domain': [('nam_id', '=', self.id)],
            'context': {
                'default_nam_id': self.id,
                'default_coso_id': self.coso_id.id
            }
        }

    def action_delete_chitieu_nam(self):
        count = self.env['ekids.chitieu_thang'].search_count(
            [('coso_id', '=', self.coso_id.id)
                , ('nam_id', '=', self.id)])
        if count > 0 :
            raise UserError("Đã tôn tại các Tháng trong Năm:"
                            +self.name
                            +". Bạn không thể xóa bản ghi này!")
        else:
            return self.unlink()
