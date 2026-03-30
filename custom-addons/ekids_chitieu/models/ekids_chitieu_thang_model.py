from odoo import models, fields, api, _

from odoo.exceptions import UserError
import calendar


class ChiTieuThang(models.Model):
    _name = "ekids.chitieu_thang"
    _description = "Mô tả về chi tiêu tổng hơ cua to chuc "
    _order = "id desc"

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở",required=True,ondelete="restrict")
    nam_id = fields.Many2one("ekids.chitieu_nam", string="Năm",required=True,ondelete="restrict")
    name = fields.Selection(
        [('1', 'Tháng 1'),('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng',
        required=True
    )
    thu_ids = fields.One2many("ekids.chitieu_thu",
                              "thang_id", string="Nguồn thu khác của")
    chi_ids = fields.One2many("ekids.chitieu_chi",
                                    "thang_id", string="Chi tiêu của tháng")


    tong_chi = fields.Integer(string="Tổng chi", readonly=True, compute="_compute_tong_chi_thang")
    tong_thu = fields.Integer(string="Tổng thu", readonly=True, compute="_compute_tong_thu_thang")

    _sql_constraints = [
        ('unique_thuchi_thang',
         'UNIQUE(coso_id,nam_id,name)',
         'Đã tồn tại chi tiêu "Tháng này của Năm"  của cơ sở, vui lòng kiểm tra lại !')
    ]

    #tong chi tieu
    def _compute_tong_chi_thang(self):
        for thang in self:
            result = self.env['ekids.chitieu_chi'].read_group(
                domain=[('thang_id','=',thang.id)],  # điều kiện lọc (nếu cần)
                fields=['tien'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['tien'] if result else 0.0
            thang.tong_chi =total

    def _compute_tong_thu_thang(self):
        for thang in self:
            result = self.env['ekids.chitieu_thu'].read_group(
                domain=[('thang_id', '=', thang.id)],  # điều kiện lọc (nếu cần)
                fields=['tien'],  # tên trường cần tính tổng

                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['tien'] if result else 0.0
            thang.tong_thu = total


    def action_delete_chitieu_thang(self):
        count = self.env['ekids.chitieu_chi'].search_count(
            [('coso_id', '=', self.coso_id.id)
                , ('thang_id', '=', self.id)])
        if count > 0:
            raise UserError("Đã tôn tại các các khoảng [Chi] trong Tháng:"
                            + self.name
                            +". Bạn không thể xóa bản ghi này!")

        else:
            count = self.env['ekids.chitieu_thu'].search_count(
                [('coso_id', '=', self.coso_id.id)
                    , ('thang_id', '=', self.id)])
            if count > 0:
                raise UserError("Đã tôn tại các các khoảng [Thu] trong Tháng:"
                                + self.name
                                + ". Bạn không thể xóa bản ghi này!")
            return self.unlink()

