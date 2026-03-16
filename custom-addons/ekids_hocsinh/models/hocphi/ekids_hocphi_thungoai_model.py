from odoo import api, fields, models
from datetime import datetime,date
import calendar

from odoo.api import ValuesType, Self


class HocPhiThuNgoai(models.Model):
    _name = 'ekids.hocphi_thungoai'
    _description = 'Học phí thu ngoài'
    _order = "nam,thang desc"

    # Khai báo các trường dữ liệu
    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True,
                              ondelete="restrict",index=True)
    name = fields.Char(string="Tên khoản thu ngoài",index=True)
    nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 10, datetime.now().year + 1)], string="Năm",
        required=True,default=lambda self: str(date.today().year),index=True)

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
                            , string="Tháng", required=True,index=True,default=lambda self: str(date.today().month))

    desc = fields.Char(string="Ghi chú")
    tien = fields.Float('Số tiền(vnđ)', digits=(10, 0), required=True)
    hocsinh_ids = fields.Many2many(comodel_name="ekids.hocsinh"
                                , relation="ekids_hocphi_thungoai4hocsinh_rel"
                                , column1="hocphi_thungoai_id"
                                , column2="hocsinh_id"
                                , string="Các học sinh được tính")
    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            result = super(HocPhiThuNgoai, self).create(vals)
            if result:
                result.func_xuly_hocphi_thungoai_cho_hocsinhs(True)
            records.append(result)
        return records[0] if len(records) == 1 else records

    def write(self, vals):
        res = super(HocPhiThuNgoai, self).write(vals)
        for rec in self:
            rec.func_xuly_hocphi_thungoai_cho_hocsinhs(True)
        return res
    def unlink(self):
        for rec in self:
            if rec.hocsinh_ids:
                rec.func_xuly_hocphi_thungoai_cho_hocsinhs(False)
        return super().unlink()



    def func_xuly_hocphi_thungoai_cho_hocsinhs(self,is_create):
        # Ví dụ: tạo bản ghi học phí chi tiết cho từng học sinh
        #B1: Xoa toan bo hoc phi thu tinh cho Thu ngoài nay
        hocphis = self.env["ekids.hocphi"].search([
            ('coso_id', '=', self.coso_id.id),
            ('nam_id.name', '=', self.nam),
            ('thang_id.name', '=', self.thang)

        ])
        if hocphis:
            for hocphi in hocphis:
                bantru_ids = hocphi.hocphi_bantru_ids
                if bantru_ids:
                    for bantru_id in bantru_ids:
                        if bantru_id.thungoai_id.id == self.id:
                            bantru_id.unlink()
        #B2: them moi cho cac hoc sinh
        if self.hocsinh_ids:
            for hs in self.hocsinh_ids:
                if is_create:
                    self.func_tao_hocphi_thungoai_cho_hocsinh(hs,self.nam,self.thang)


    def func_tao_hocphi_thungoai_cho_hocsinh(self,hocsinh,nam,thang):

        hocphi = self.env["ekids.hocphi"].search([
            ('hocsinh_id', '=', hocsinh.id),
            ('nam_id.name', '=', nam),
            ('thang_id.name', '=', thang)
        ], limit=1)
        if hocphi:

            data = {
                'hocphi_id': hocphi.id,
                'thungoai_id': self.id,
                'name': self.name,
                'tien': self.tien,

            }
            self.env['ekids.hocphi_bantru'].create(data)





