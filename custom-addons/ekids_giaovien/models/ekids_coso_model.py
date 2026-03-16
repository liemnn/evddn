import ast
import json
from collections import defaultdict
from datetime import timedelta,date,datetime
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


class CoSo(models.Model):
    _inherit = "ekids.coso"

    def action_xem_toanbo_giaovien(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Giao viên của cơ sở',
            'res_model': 'ekids.giaovien',
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id,
                'search_default_trangthai': '1',
            }
        }

    def action_xem_toanbo_luong_nam(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'LƯƠNG',
            'res_model': 'ekids.luong_nam',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id
            }
        }

    def action_tinh_luong_thang_qua(self):
       # cấu hình, danh mục lương
        luong2thang = self.func_macdinh_tao_luong_thang_qua()
        if luong2thang:
            luong2thang.action_view_khoitao_luong_giaovien()
            name ="LƯƠNG THÁNG "+ str(luong2thang.name) +"/"+str(luong2thang.nam_id.name)
            return {
                'type': 'ir.actions.act_window',
                'name': name,
                'res_model': 'ekids.luong',
                'view_mode': 'list,kanban,form',
                'target': 'current',
                'domain': [('coso_id', '=', self.id), ('thang_id', '=', luong2thang.id)],
                'context': {
                    'default_coso_id': self.id,
                    'default_nam': luong2thang.nam_id.name,
                    'default_thang': luong2thang.name
                }
            }

    def action_quanly_luong_sukien(self):
        # cấu hình, danh mục lương

            return {
                'type': 'ir.actions.act_window',
                'name': 'LƯƠNG SỰ KIỆN',
                'res_model': 'ekids.luong_sukien',
                'view_mode': 'list,form',
                'target': 'current',
                'domain': [('coso_id', '=', self.id)],
                'context': {
                    'default_coso_id': self.id
                }
            }

    def func_macdinh_tao_luong_thang_qua(self):
        today = date.today()  # ví dụ: 2025-08-17
        last_month_same_day = today - relativedelta(months=1)
        month = last_month_same_day.month
        year = last_month_same_day.year

        luong2nam = self.env['ekids.luong_nam'].search(
            [('coso_id', '=', self.id)
                , ('name', '=', str(year))

             ])
        if not luong2nam:
            data = {
                'coso_id': self.id,
                'name': str(year),
            }
            luong2nam = self.env['ekids.luong_nam'].create(data)

        luong2thang = self.env['ekids.luong_thang'].search(
            [('coso_id', '=', self.id)
                , ('nam_id', '=', luong2nam.id)
                , ('name', '=', str(month))

             ])
        if not luong2thang:
            data = {
                'coso_id': self.id,
                'nam_id': luong2nam.id,
                'name': str(month),
            }
            luong2thang = self.env['ekids.luong_thang'].create(data)
        return luong2thang

    def action_view_giaovien_luong_dm_chitra(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Định nghĩa danh mục Lương' + self.name,
            'res_model': 'ekids.luong_dm_chitra',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id
            }
        }

    def action_view_giaovien_luong_dm_chamcong(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Định nghĩa loại điểm danh' + self.name,
            'res_model': 'ekids.luong_dm_chamcong',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.id
            }
        }

