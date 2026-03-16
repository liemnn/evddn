from odoo import models, fields, api, _

from odoo.exceptions import UserError
from datetime import datetime
from datetime import date,timedelta
from odoo.exceptions import ValidationError
import calendar
from dateutil.relativedelta import relativedelta


class ChamCongLoai(models.Model):
    _name = "ekids.chamcong_loai"
    _description = "Chấm công giáo viên"
    _order = "loai asc"

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True)
    name = fields.Char(string="Tên hiển thị", compute="_compute_chamcong_name", readonly=True)
    dm_chamcong_id = fields.Many2one("ekids.luong_dm_chamcong"
                                     , string="Lựa chọn loại chấm công/điểm danh",ondelete ="cascade")
    loai = fields.Selection(
        related="dm_chamcong_id.loai",
        store=True
    )
    def _compute_chamcong_name(self):
        for record in self:
            name =""
            if record.dm_chamcong_id:
                name += record.dm_chamcong_id.name
            record.name =name.upper()

    def action_giaovien_chamcong_thang_nay(self):
        today = date.today()
        if self.dm_chamcong_id.loai =='1':
            #giao nhiem vu kpi thì sang tháng trước:
            ngay_dauthang = today.replace(day=1)
            ngay_thangtruoc =last_day_last_month = ngay_dauthang - timedelta(days=1)
            today = ngay_thangtruoc

        loai2thang = self.func_tao_macdinh_chamcong_thangnay_loai2thang(today.year, today.month)
        return loai2thang.action_vao_chamcong_theoloai()

    def action_giaovien_chamcong_thang_truoc(self):
        today = date.today()
        last_day = today - relativedelta(months=1)

        loai2thang =self.func_tao_macdinh_chamcong_thangnay_loai2thang(last_day.year,last_day.month)
        return loai2thang.action_vao_chamcong_theoloai()







    def action_giaovien_chamcong_loai2thang(self):
        today =date.today()
        self.func_tao_macdinh_chamcong_thangnay_loai2thang(today.year,today.month)

        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'ekids.chamcong_loai2thang',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.coso_id.id),
                       ('chamcong_loai_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_chamcong_loai_id': self.id
            },
        }
    def func_tao_macdinh_chamcong_thangnay_loai2thang(self,nam,thang):

        result = self.env['ekids.chamcong_loai2thang'].search([
            ('coso_id', '=', self.coso_id.id)
            ,('chamcong_loai_id', '=', self.id)
            ,('thang', '=', str(thang))
            ,('nam', '=', str(nam))
        ],limit=1)
        if result:
            return result
        else:
            data ={
                'coso_id':self.coso_id.id,
                'chamcong_loai_id': self.id,
                'thang': str(thang),
                'nam':str(nam),
            }
            result = self.env['ekids.chamcong_loai2thang'].create(data)
            return result



