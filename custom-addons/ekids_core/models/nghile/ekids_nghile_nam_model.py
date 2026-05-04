from odoo import models, fields, api, _
from datetime import datetime
from datetime import date
from lunardate import LunarDate
from datetime import timedelta


class NghiLeNam(models.Model):
    _name = "ekids.nghile_nam"
    _description = "Mô tả về danh mục tỉnh "
    _order = "name desc"

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True, ondelete="restrict")
    name = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year-5, datetime.now().year + 2)], string="Năm",required=True)

    desc = fields.Html(string="Mô tả")

    _sql_constraints = [
        ('unique_nghile_nam',
         'UNIQUE(coso_id,name)',
         'Đã tồn tại thiệt lập [Năm]  của cơ sở, vui lòng kiểm tra lại !')
    ]
    @api._model_create_single
    def create(self, vals):
        # Tạo mới CSDL nghỉ lễ
        record = super(NghiLeNam, self).create(vals)
        if record:
            record.func_khoitao_default_ngay_nghile()
        return record

    def func_khoitao_default_ngay_nghile(self):
        # TH1: ngay 1/1/2025
        tu_ngay = date(int(self.name), 1, 1)
        den_ngay = date(int(self.name), 1, 1)
        data = {
            'nam_id': self.id,
            'name': 'Nghỉ tết dương lịch 1 ngày',
            'tu_ngay': tu_ngay,
            'den_ngay': den_ngay,
            'loai': '0',
            'desc': 'Nghỉ tết dương lịch'
                    + self.name,
            'trangthai': '1'

        }
        self.env['ekids.nghile'].create(data)

        # TH2: NGHỈ tết âm lịch
        days = self.func_get_nghi_tet_amlich(self.name)
        if days:
            tu_ngay = days[0]
            den_ngay = days[len(days)-1]
            data ={
                'nam_id': self.id,
                'name': 'Nghỉ lễ tết [Âm lịch]',
                'tu_ngay':tu_ngay,
                'den_ngay':den_ngay,
                'loai':'0',
                'desc': 'Nghỉ lễ tết nguyên đán(Âm lịch) '
                        + self.name
                         +', nếu có thay đổi thực tế vui lòng điều chỉnh lại',
                'trangthai':'1'

              }
            self.env['ekids.nghile'].create(data)

        #TH2 nghỉ 10/3 âm lịch
            tu_ngay = LunarDate(int(self.name), 3, 10).toSolarDate()
            den_ngay = tu_ngay
            data = {
                'nam_id': self.id,
                'name': 'Nghỉ lễ giỗ tổ hùng vương',
                'tu_ngay': tu_ngay,
                'den_ngay': den_ngay,
                'loai': '0',
                'desc': 'Nghỉ lễ tết giỗ tổ hùng vương'
                        + self.name,
                'trangthai': '1'

            }
            self.env['ekids.nghile'].create(data)

            # TH3 nghỉ 30/4/ 1/5
            tu_ngay = date(int (self.name),4,30)
            den_ngay = date(int(self.name), 5, 1)
            data = {
                'nam_id': self.id,
                'name': 'Nghỉ lễ 30/4 và 1/5',
                'tu_ngay': tu_ngay,
                'den_ngay': den_ngay,
                'loai': '0',
                'desc': 'Quốc khánh 2/9'
                        + self.name,
                'trangthai': '1'

            }
            self.env['ekids.nghile'].create(data)

            # TH4 2/9
            tu_ngay = date(int(self.name), 9, 1)
            den_ngay = date(int(self.name), 9, 2)
            data = {
                'nam_id': self.id,
                'name': 'Nghỉ tết quốc khánh',
                'tu_ngay': tu_ngay,
                'den_ngay': den_ngay,
                'loai': '0',
                'desc': 'Nghỉ tết quốc khánh'
                        + self.name,
                'trangthai': '1'

            }
            self.env['ekids.nghile'].create(data)

    def func_get_nghi_tet_amlich(self,nam):
        """
        Trả về danh sách các ngày nghỉ Tết Nguyên Đán trong năm dương lịch
        (29 Chạp năm trước đến mùng 5 tháng Giêng)
        """
        # 29 tháng Chạp năm trước (âm lịch)
        tet_start = LunarDate(int(nam) - 1, 12, 29).toSolarDate()
        # mùng 5 tháng Giêng năm nay
        tet_end = LunarDate(int(nam), 1, 5).toSolarDate()

        # Sinh danh sách các ngày nghỉ
        days = []
        current = tet_start
        while current <= tet_end:
            days.append(current)
            current += timedelta(days=1)
        return days



    def action_xem_toanbo_nghile_nam(self):
        """action view year tuition"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'NĂM '+self.name.upper(),
            'res_model': 'ekids.nghile',
            'view_mode': 'list,form',
            'domain': [('nam_id', '=', self.id)],
            'context': {
                'default_nam_id': self.id,
                'default_nam': self.name,
                'default_coso_id': self.coso_id.id,
                'search_default_trangthai': '1',
            }
        }


