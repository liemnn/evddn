from odoo import api, fields, models
from datetime import datetime,date
import calendar

from odoo.api import ValuesType, Self


class LuongSuKien(models.Model):
    _name = 'ekids.luong_sukien'
    _description = 'Lương theo sự kiện'
    _order = "nam,thang desc"

    # Khai báo các trường dữ liệu
    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True,
                              ondelete="restrict")
    name = fields.Char(string="Tên khoản Lương")
    nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 10, datetime.now().year + 1)], string="Năm",
        required=True,default=lambda self: str(date.today().year))

    thang = fields.Selection([("1", "Tháng 01"),
                             ("2", "Tháng 02"),
                             ("3", "Tháng 03"),
                             ("4", "Tháng 04"),
                             ("5", "Tháng 05"),
                             ("6", "Tháng 06"),
                             ("7", "Tháng 07"),
                             ("8", "Tháng 08"),
                             ("9", "Tháng 09"),
                             ("10", "Tháng 10"),
                             ("11", "Tháng 11"),
                             ("12", "Tháng 12"),
                             ]
                            , string="Tháng", required=True,default=lambda self: str(date.today().month))

    loai = fields.Selection(
        [("1", "Được cộng tiền"),
         ("-1", "Bị trừ tiền"),
         ("0", "Thông tin từ nhà trường")], string="Khoản", required=True)

    desc = fields.Char(string="Ghi chú")
    tien = fields.Float('Số tiền(vnđ)', digits=(10, 0), required=True)

    giaovien_ids = fields.Many2many(comodel_name="ekids.giaovien"
                                , relation="ekids_luong_sukien4giaovien_rel"
                                , column1="luong_sukien_id"
                                , column2="giaovien_id"
                                , string="Các Giáo viên được hưởng")
    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            result = super(LuongSuKien, self).create(vals)
            if result:
                result.func_xuly_luong_sukien_cho_giaoviens(True)
            records.append(result)
        return records[0] if len(records) == 1 else records

    def write(self, vals):
        res = super(LuongSuKien, self).write(vals)
        if "giaovien_ids" in vals:
            # Logic xử lý khi danh sách học sinh thay đổi
            for rec in self:
                    rec.func_xuly_luong_sukien_cho_giaoviens(True)
        return res
    def unlink(self):
        for rec in self:
            if rec.giaovien_ids:
                rec.func_xuly_luong_sukien_cho_giaoviens(False)
        return super().unlink()



    def func_xuly_luong_sukien_cho_giaoviens(self,is_create):
        # Ví dụ: tạo bản ghi học phí chi tiết cho từng học sinh
        #B1: Xoa toan bo hoc phi thu tinh cho Thu ngoài nay
        luongs = self.env["ekids.luong"].search([
            ('coso_id', '=', self.coso_id.id),
            ('nam_id.name', '=', self.nam),
            ('thang_id.name', '=', self.thang)

        ])
        if luongs:
            for luong in luongs:
                luong_cong_ids = luong.luong_cong_ids
                luong_tru_ids = luong.luong_tru_ids
                luong_thongtin_ids = luong.luong_thongtin_ids

                if luong_cong_ids:
                    for luong_cong_id in luong_cong_ids:
                        if luong_cong_id.sukien_id.id == self.id:
                            luong_cong_id.unlink()
                if luong_tru_ids:
                    for luong_tru_id in luong_tru_ids:
                        if luong_tru_id.sukien_id.id == self.id:
                            luong_tru_id.unlink()
                if luong_thongtin_ids:
                    for luong_thongtin_id in luong_thongtin_ids:
                        if luong_thongtin_id.sukien_id.id == self.id:
                            luong_thongtin_id.unlink()

        #B2: them moi cho cac giáo viên
        if self.giaovien_ids:
            for gv in self.giaovien_ids:
                if is_create:
                    self.func_tao_luong_sukien_cho_giaovien(gv,self.nam,self.thang)


    def func_tao_luong_sukien_cho_giaovien(self,giaovien,nam,thang):

        luong = self.env["ekids.luong"].search([
            ('giaovien_id', '=', giaovien.id),
            ('nam_id.name', '=', nam),
            ('thang_id.name', '=', thang)
        ], limit=1)
        if luong and luong.trangthai =='-1':
            count = self.env["ekids.luong_hangmuc"].search_count([
                ('luong_id', '=', luong.id),
                ('sukien_id', '=', self.id)])
            if count<=0:
                data = {
                    'luong_id': luong.id,
                    'sukien_id': self.id,
                    'name': self.name,
                    'tien': self.tien,
                    'loai':self.loai
                }
                self.env['ekids.luong_hangmuc'].create(data)





