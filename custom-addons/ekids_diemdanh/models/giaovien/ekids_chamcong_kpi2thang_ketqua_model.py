from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from odoo.exceptions import ValidationError
import calendar




class ChamCongKPI2ThangKetQua(models.Model):
    _name = "ekids.chamcong_kpi2thang_ketqua"
    _description = "Đánh giá các chỉ số đạt để tính lương"

    chamcong_kpi2thang_id = fields.Many2one("ekids.chamcong_kpi2thang", string="Cơ sở",required=True,ondelete="cascade")
    loai_kpi = fields.Selection([
        ('0', 'Nhâp số'),
        ('1', 'Bật/Tắt')
    ], string="Loại KPI",default='0')

    code = fields.Char(string="Mã", required=True)
    name = fields.Char(string="Tên", required=True)
    donvi = fields.Char(string="Đơn vị", required=True)
    ketqua_boolean = fields.Boolean(string="Kết quả (Đạt)")
    tong = fields.Float("Đạt được", default=0, digits=(10, 1))
    desc = fields.Text(string="Ghi chú")



    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            result = super(ChamCongKPI2ThangKetQua, self).create(vals)
            if result:
                result.func_capnhat_giatri_cho_kpi2thang()
            records.append(result)
        return records[0] if len(records) == 1 else records

    def write(self, vals):
        if self.loai_kpi == '1':
            if vals['ketqua_boolean'] == 'True':
                vals['tong'] = '1'
            else:
                vals['tong'] = '0'


        res = super(ChamCongKPI2ThangKetQua, self).write(vals)
        # Logic xử lý khi danh sách học sinh thay đổi
        for rec in self:
            rec.func_capnhat_giatri_cho_kpi2thang()
        return res


    def func_capnhat_giatri_cho_kpi2thang(self):
        ketquas = (self.env['ekids.chamcong_kpi2thang_ketqua']
                 .search([('chamcong_kpi2thang_id', '=', self.chamcong_kpi2thang_id.id)]))
        if ketquas:
            result =""
            for ketqua in ketquas:
                if ketqua.loai_kpi=='0':
                    result =result + "-"+ketqua.name +"="+str(ketqua.tong)+" "+ str(ketqua.donvi)+"\n"
                else:
                    kq= "[Không đạt]"
                    if ketqua.ketqua_boolean == True:
                        kq = "[Đạt]"
                    result = result + "-" + ketqua.name + " là " + kq + "\n"

                self.chamcong_kpi2thang_id.desc=result


