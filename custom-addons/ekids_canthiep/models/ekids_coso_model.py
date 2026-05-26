from odoo import models, fields, api, _
from datetime import datetime, timedelta,date

class CoSo(models.Model):
    _inherit = "ekids.coso"

    def action_xem_kehoach_canthiep(self):
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


