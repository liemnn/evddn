from odoo import api, fields, models
from datetime import datetime
import calendar
from odoo.exceptions import UserError
from .ekids_luong_func_abstractmodel import LuongFuncAbstractModel
from .ekids_luong_formula_abstractmodel import LuongFolmulaAbstractModel


class LuongThang(models.Model,LuongFuncAbstractModel,LuongFolmulaAbstractModel):
    _name = 'ekids.luong_thang'
    _description = 'Lương của một thang của trung tâm'
    _order = "id desc"

    coso_id = fields.Many2one("ekids.coso",related="nam_id.coso_id", string="Cơ sở", required=True, ondelete="restrict")
    nam_id = fields.Many2one("ekids.luong_nam", string="Thuộc Năm", readonly=True)
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
                             , string="Tháng")

    tong_luong = fields.Float(string="Tổng lương chi trả",digits=(10, 0), compute="_compute_tong_luong")
    tong_giaovien = fields.Integer(string="Tổng số giáo viên",compute="_compute_tong_giaovien")

    _sql_constraints = [
        ('unique_luong_thang',
         'UNIQUE(coso_id,nam_id,name)',
         'Đã tồn tại [Lương Tháng]  của cơ sở, vui lòng kiểm tra lại !')
    ]

    def _compute_tong_luong(self):
        for thang in self:
            dms = self.env['ekids.luong'].search([('thang_id.nam_id.coso_id', '=', thang.nam_id.coso_id.id)
                                                     , ('thang_id', '=', thang.id)])
            thang.tong_luong = sum(gv.tong_nhatruong_chi for gv in dms)


    def _compute_tong_giaovien(self):
        for thang in self:
            total = self.env['ekids.luong'].search_count([('thang_id', '=', thang.id)])
            thang.tong_giaovien = total


