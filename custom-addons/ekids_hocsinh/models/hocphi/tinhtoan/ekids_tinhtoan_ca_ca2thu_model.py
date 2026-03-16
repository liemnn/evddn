from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _  # <-- THÊM DÒNG NÀY
from datetime import datetime
class TinhToanCa2Thu(models.Model):
    _name = "ekids.tinhtoan_ca2thu"
    _description = "Tính toán truoc so luong Ca/ Thu trong tuan"

    hocsinh_id = fields.Many2one('ekids.hocsinh', string="Họ và tên",
                                 domain="[('coso_id','=',coso_id)]",required=True)
    dm_ca_id = fields.Many2one("ekids.hocphi_dm_ca", string="Loại ca",required=True,ondelete="cascade")
    thu =fields.Integer(string="Thứ trong tuần",required=True)
    soca = fields.Integer(string="Tổng ca",required=True)




