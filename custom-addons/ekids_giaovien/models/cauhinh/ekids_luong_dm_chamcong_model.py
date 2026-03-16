from odoo import api, fields, models
from datetime import datetime
import calendar
from odoo.exceptions import ValidationError

class LuongDMChamCong(models.Model):
    _name = "ekids.luong_dm_chamcong"
    _rec_name = 'name'
    _description = "Định nghĩa danh mục điểm danh chấm công"
    _order = "sequence asc"

    sequence = fields.Integer(string="Thứ tự tính toán", required=True, default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    name =fields.Char(string="Tên",required=True)
    loai = fields.Selection(
        [("0", "Chấm công - Đi làm"),
         ("2", "Chấm công - Công việc khác(theo ngày)"),
         ("3", "Chấm công - Công việc khác(theo giá trị/ngày)"),
         ("1", "Giao  nhiệm vụ(KPI)")],string="Loại")

    is_default_ok = fields.Boolean(string="Mặc định được tích [Thực hiện]",default=False)

    is_kpi = fields.Boolean(compute="_compute_is_kpi")
  


    trangthai = fields.Selection([("0", "Không hoạt động")
                                     , ("1", "Đang hoạt động")],default="1")
    donvi = fields.Char(string="Đơn vị", required=True,default="ca")

    kpi_ids = fields.One2many('ekids.luong_dm_chamcong_kpi', 'dm_chamcong_id')

    _sql_constraints = [
        ('unique_luong_dm_chamcong',
         'UNIQUE(coso_id,name)',
         'Không thể tạo lập trùng tên ! bạn cần kiểm tra lại')
    ]

    @api.constrains('coso_id', 'loai')
    def _check_unique_loai0_per_coso(self):
        for rec in self:
            if rec.loai == "0":
                count = self.search_count([
                    ('id', '!=', rec.id),
                    ('coso_id', '=', rec.coso_id.id),
                    ('loai', '=', "0")
                ])
                if count > 0:
                    raise ValidationError("Mỗi cơ sở chỉ được phép có duy nhất một bản ghi loại 'Chấm công - Đi làm'.")

    @api.depends("loai")
    def _compute_is_kpi(self):
        for record in self:
            if record.loai == '1':
                # Chỉ hiển thị khi loại là  Lương có điều kiện
                record.is_kpi = True
            else:
                record.is_kpi = False

    def name_get(self):
        result = []
        for rec in self:
            loai_label = dict(self._fields['loai'].selection).get(rec.loai, '')
            label = f"{rec.name} ({loai_label}) [{rec.donvi}]" if rec.donvi else f"{rec.name} ({loai_label})"
            result.append((rec.id, label))
        return result
