import ast
import json
from collections import defaultdict
from datetime import timedelta,date
from odoo import models, fields, api, _


class CoSo(models.Model):
    _inherit = "ekids.coso"



    def action_view_ekids_baocao_loinhuan_action_window(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'báo cáo lợi nhuận',
            'res_model': 'ekids.baocao_loinhuan',
            'view_mode': 'form',
            'target': 'new',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'default_tu_thang':'2',
                'default_tu_nam':str(date.today().year),
                'default_den_thang': '1',
                'default_den_nam': str(date.today().year+1),
            }
        }

    def action_view_ekids_baocao_nguonluc_action_window(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'BÁO CÁO- [HỌC SINH/GIÁO VIÊN] HÀNG THANG',
            'res_model': 'ekids.baocao_nguonluc',
            'view_mode': 'form',
            'target': 'new',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'default_tu_thang':'2',
                'default_tu_nam':str(date.today().year),
                'default_den_thang': '1',
                'default_den_nam': str(date.today().year+1),
            }
        }


