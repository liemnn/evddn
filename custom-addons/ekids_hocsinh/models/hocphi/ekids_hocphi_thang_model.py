from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError
from .ekids_hocphi_thang_abstractmodel import HocPhiThangAbstractModel

import calendar


class HocPhiThang(models.Model,HocPhiThangAbstractModel):
    _name = 'ekids.hocphi_thang'
    _description = 'Lương của một thang của trung tâm'
    _order = "id desc"

    coso_id = fields.Many2one("ekids.coso",related="nam_id.coso_id", string="Cơ sở", required=True, ondelete="restrict",index=True)
    nam_id = fields.Many2one("ekids.hocphi_nam", string="Thuộc Năm", readonly=True,required=True,ondelete="restrict",index=True)
    name = fields.Selection([("1", "Tháng 01"),
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
                             , string="Khởi tạo học phí của Tháng",required=True,index=True)


    tong_hocsinh = fields.Integer(string="Tổng học sinh", readonly=True, compute="_compute_tong_hocsinh")
    tong_hocphi = fields.Float(string="Tổng học phí",readonly=True,digits=(10, 0),compute="_compute_tong_hocphi")
    tong_hocphi_giam = fields.Float(string="Tổng tiền giảm học phí",digits=(10, 0),readonly=True,compute="_compute_tong_hocphi_giam")
    tong_hocphi_thucthu = fields.Float(string="Tổng học phí thực thu",digits=(10, 0),readonly=True,compute="_compute_tong_hocphi_thucthu")

    tong_dong_ck=fields.Float(string="Tổng đã [Chuyển khoản]", digits=(10, 0),compute="_compute_tong_dong_ck")
    tong_dong_tm = fields.Float(string="Tổng đã [Tiền mặt]", digits=(10, 0),compute="_compute_tong_dong_tm")
    tong_no = fields.Float(string="Tổng chưa thu", digits=(10, 0), compute="_compute_tong_no")
    _sql_constraints = [
        ('unique_hocphi_thang',
         'UNIQUE(coso_id,nam_id,name)',
         'Đã tồn tại học phí "Tháng này của Năm"  của cơ sở, vui lòng kiểm tra lại !')
    ]

    def _compute_tong_dong_ck(self):
        for thang in self:
            result = self.env['ekids.hocphi'].read_group(
                domain=[('thang_id', '=', thang.id),('trangthai', '=', '11')],  # điều kiện lọc (nếu cần)
                fields=['hocphi_phaidong'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['hocphi_phaidong'] if result else 0.0
            thang.tong_dong_ck = total
    def _compute_tong_dong_tm(self):
        for thang in self:
            result = self.env['ekids.hocphi'].read_group(
                domain=[('thang_id', '=', thang.id),('trangthai', '=', '10')],  # điều kiện lọc (nếu cần)
                fields=['hocphi_phaidong'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['hocphi_phaidong'] if result else 0.0
            thang.tong_dong_tm = total

    def _compute_tong_no(self):
        for thang in self:
            result = self.env['ekids.hocphi'].read_group(
                domain=[('thang_id', '=', thang.id),('trangthai', 'in', ['-1','0','2'])],  # điều kiện lọc (nếu cần)
                fields=['hocphi_phaidong'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['hocphi_phaidong'] if result else 0.0
            thang.tong_no = total

    def _compute_tong_hocsinh(self):
        for thang in self:
            total = self.env['ekids.hocphi'].search_count([('thang_id','=',thang.id)])
            thang.tong_hocsinh = total
    def _compute_tong_hocphi(self):
        for thang in self:
            result = self.env['ekids.hocphi'].read_group(
                domain=[('thang_id','=',thang.id)],  # điều kiện lọc (nếu cần)
                fields=['hocphi'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['hocphi'] if result else 0.0
            thang.tong_hocphi =total
    def _compute_tong_hocphi_giam(self):
        for thang in self:
            result = self.env['ekids.hocphi'].read_group(
                domain=[('thang_id', '=', thang.id)],  # điều kiện lọc (nếu cần)
                fields=['hocphi_giam'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['hocphi_giam'] if result else 0.0
            thang.tong_hocphi_giam = total
    def _compute_tong_hocphi_thucthu(self):
        for thang in self:
            result = self.env['ekids.hocphi'].read_group(
                domain=[('thang_id', '=', thang.id)],  # điều kiện lọc (nếu cần)
                fields=['hocphi_phaidong'],  # tên trường cần tính tổng
                groupby=[]  # không cần group theo trường nào cả
            )

            total = result[0]['hocphi_phaidong'] if result else 0.0
            thang.tong_hocphi_thucthu = total


    def action_delete_hocphi_thang(self):
        count = self.env['ekids.hocphi'].search_count(
            [('coso_id', '=', self.coso_id.id)
                , ('thang_id', '=', self.id)])
        if count > 0 :
            raise UserError("Đã tôn tại việc tính toán học phí cho học sinh tại Tháng:"
                            +self.name
                            +". Bạn không thể xóa bản ghi này!")
        else:
            return self.unlink()


