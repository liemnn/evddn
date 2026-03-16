from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar




class ChamCongKPI2Thang(models.Model):
    _name = "ekids.chamcong_kpi2thang"
    _description = "Đánh giá các chỉ số đạt để tính lương"
    _order = "giaovien_id asc"

    sequence = fields.Integer(string="TT", compute="_compute_sequence")
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True)

    chamcong_loai2thang_id = fields.Many2one("ekids.chamcong_loai2thang", string="Thuộc",required=True, ondelete="cascade")
    giaovien_id = fields.Many2one('ekids.giaovien', string="Họ và tên",
                                 domain="[('coso_id','=',coso_id)]",required=True)

    desc = fields.Text(string="Ghi chú")
    kpi2thang_ketqua_ids = fields.One2many('ekids.chamcong_kpi2thang_ketqua', 'chamcong_kpi2thang_id')

    def action_nhap_ketqua_kpi(self):
        form_view_id = self.env.ref('ekids_diemdanh.chamcong_kpi2thang_form').id  # chú ý id chính xác
        self.func_tao_macdinh_ketqua_kpi()
        return {
            'type': 'ir.actions.act_window',
            'name': 'KPI',
            'res_model': 'ekids.chamcong_kpi2thang',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,

            ),
        }

    def func_tao_macdinh_ketqua_kpi(self):
        dm_chamcong = self.chamcong_loai2thang_id.chamcong_loai_id.dm_chamcong_id
        kpis =dm_chamcong.kpi_ids
        if kpis:
            for kpi in kpis:
                count =(self.env['ekids.chamcong_kpi2thang_ketqua']
                        .search_count([('chamcong_kpi2thang_id','=',self.id),('code','=',kpi.code)]))
                if count<=0:
                    data={
                        'chamcong_kpi2thang_id':self.id,
                        'code': kpi.code,
                        'name': kpi.name,
                        'donvi': kpi.donvi,
                        'is_tyle_phantram':  kpi.is_tyle_phantram,
                        'tong': 0,
                    }
                    self.env['ekids.chamcong_kpi2thang_ketqua'].create(data)



    def _compute_sequence(self):
        index =1
        for record in self:
            record.sequence = index
            index +=1





