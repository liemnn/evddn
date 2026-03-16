from odoo import models, fields, api, _
from datetime import datetime
from datetime import date
from odoo.exceptions import UserError

class CoSo(models.Model):
    _inherit = "ekids.coso"

    dm_chamcong_ids = fields.One2many("ekids.luong_dm_chamcong",
                                      "coso_id", string="Cơ sở")

    chamcong_kanban_buttons = fields.Json(
        string="Buttons hiển thị chấm công",
        compute="_compute_chamcong_kanban_buttons",
        store=False
    )

    def _compute_chamcong_kanban_buttons(self):
        for rec in self:
            dm_chamcongs = rec.dm_chamcong_ids
            buttons=[]
            if dm_chamcongs:
                for dm in dm_chamcongs:
                    button ={
                        'id': dm.id,
                        'name': dm.name or f'B-{dm.id}',
                        'loai': dm.loai,
                    }
                    buttons.append(button)

            rec.chamcong_kanban_buttons = buttons

    def action_vao_dm_chamcong_thangnay(self):
        self.ensure_one()
        context =self.env.context
        dm_chamcong_id = int (context.get("dm_chamcong_id","0"))
        dm_chamcong = self.env['ekids.luong_dm_chamcong'].browse(dm_chamcong_id)
        if dm_chamcong:
            chamcong_loai =self.func_tao_chamcong_loai(dm_chamcong.coso_id.id,dm_chamcong_id)
            if chamcong_loai:
                return chamcong_loai.action_giaovien_chamcong_thang_nay()


    def action_quanly_lichnghi_giaovien(self):
        list_view_id = self.env.ref('ekids_diemdanh.giaovien_nghiphep_list').id
        form_view_id = self.env.ref('ekids_diemdanh.giaovien_nghiphep_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'NGHỈ PHÉP',
            'res_model': 'ekids.giaovien_nghiphep',
            'view_mode': 'list,form',
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }

    def action_giaovien_chamcong(self):
        self.func_tao_macdinh_chamcong_loai()
        kanban_view_id = self.env.ref('ekids_diemdanh.chamcong_loai_kanban').id

        return {
            'type': 'ir.actions.act_window',
            'name': 'CHẤM CÔNG',
            'res_model': 'ekids.chamcong_loai',
            'view_mode': 'kanban',
            'views': [(kanban_view_id, 'kanban')],
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {'default_coso_id': self.id},
        }
    def func_tao_macdinh_chamcong_loai(self):
        dm_chamcongs = self.env['ekids.luong_dm_chamcong'].search([
            ('coso_id', '=', self.id)
            , ('trangthai', '=', '1')
        ])
        if dm_chamcongs:
            for dm_chamcong in dm_chamcongs:
                count = self.env['ekids.chamcong_loai'].search_count([
                    ('coso_id', '=', self.id)
                    , ('dm_chamcong_id', '=', dm_chamcong.id)
                ])
                if count <= 0:
                    data ={
                        'coso_id':self.id,
                        'dm_chamcong_id': dm_chamcong.id
                    }
                    self.env['ekids.chamcong_loai'].create(data)

    def func_tao_chamcong_loai(self,coso_id,dm_chamcong_id):
        chamcong_loai = self.env['ekids.chamcong_loai'].search([
            ('coso_id', '=',coso_id)
            , ('dm_chamcong_id', '=', dm_chamcong_id)
        ])
        if not chamcong_loai:
            data = {
                'coso_id': coso_id,
                'dm_chamcong_id': dm_chamcong_id
            }
            chamcong_loai =self.env['ekids.chamcong_loai'].create(data)
            return chamcong_loai
        return chamcong_loai
