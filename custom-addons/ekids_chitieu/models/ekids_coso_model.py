from odoo import models, fields, api, _
from datetime import datetime, timedelta,date

class CoSo(models.Model):
    _inherit = "ekids.coso"

    def action_view_chitieu_thang_nay(self):
        thang_chi =self.func_tao_macdinh_chitieu_nam_thang_nay()
        if thang_chi:
            return {
                'type': 'ir.actions.act_window',
                'name': 'THÁNG' + str(thang_chi.name).upper(),
                'res_model': 'ekids.chitieu_thang',
                'view_mode': 'form',
                'res_id': thang_chi.id,
                'domain': [('nam_id', '=', self.id)],
                'context': {
                    'default_nam_id': self.id,
                    'default_coso_id': self.id
                }
            }

    def func_tao_macdinh_chitieu_nam_thang_nay(self):
        today = date.today()
        year = today.year
        month =today.month
        nam_chi = self.env['ekids.chitieu_nam'].search(
                [('coso_id', '=', self.id)
                    ,('name', '=', str(year))
                 ])
        if not nam_chi:
            data ={
                'coso_id':self.id,
                'name': str(year),
            }
            nam_chi = self.env['ekids.chitieu_nam'].create(data)
        # đã có năm giờ tạo mới tháng chi tiêu
        if nam_chi:
            thang_chi = self.env['ekids.chitieu_thang'].search(
                [('coso_id', '=', self.id)
                    , ('nam_id', '=',nam_chi.id)
                    , ('name', '=', str(month))
                 ])
            if not thang_chi:
                data = {
                    'coso_id': self.id,
                    'nam_id': nam_chi.id,
                    'name': str(month),
                }
                thang_chi = self.env['ekids.chitieu_thang'].create(data)
            return thang_chi

    def action_view_ekid_chitieu_kanban_chitieu_nam(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CHI',
            'res_model': 'ekids.chitieu_nam',
            'view_mode': 'kanban,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id
            }
        }


    def action_view_ekid_chitieu_list_dm_loaichi(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Loại chi',
            'res_model': 'ekids.chitieu_dm_loaichi',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai':'1',
            }
        }


