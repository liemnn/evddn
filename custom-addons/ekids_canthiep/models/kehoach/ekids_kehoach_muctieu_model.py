from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoach2MucTieu(models.Model):
    _name = 'ekids.kehoach_muctieu'
    _description = 'Các mục tiêu cho kế hoạch'
    _order = 'id desc'

    sequence = fields.Integer(string="STT", default=1)
    index = fields.Integer(string="STT", default=1,compute="_compute_index")

    kehoach_id = fields.Many2one("ekids.kehoach",
                                 string="Thuộc kế hoạch nào",
                                 required=True,
                                 ondelete="cascade")

    linhvuc_id = fields.Many2one('ekids.ct_linhvuc',
                                 related="muctieu_id.linhvuc_id", string='Lĩnh vực', required=True, ondelete="cascade")
    tuoi_id = fields.Many2one('ekids.ct_tuoi', string='Độ tuổi',
                              related="muctieu_id.tuoi_id", required=True, ondelete="cascade")

    name = fields.Char("Tên",compute="_compute_name")
    chucnang = fields.Html(string="Chức năng phát triển cốt lõi & Lập luận lâm sàng",compute="_compute_chucnang")
    thietke = fields.Html(string="Thiết kế hoạt động cho giáo viên Theo mô tả (ABC)",compute="_compute_thietke")
    tieuchi_chuadat = fields.Char(string="Chưa đạt (-)",compute="_compute_tieuchi_chuadat")
    tieuchi_hinhthanh = fields.Char(string="Đang hình thành (+/-)",compute="_compute_tieuchi_hinhthanh")
    tieuchi_dat = fields.Char(string="Đạt (+)",compute="_compute_tieuchi_dat")

    muctieu_id = fields.Many2one('ekids.ct_muctieu', string='Mục tiêu', required=True, ondelete="cascade")


    def _compute_index(self):
        index =1
        for record in self:
            record.index = index
            index +=1

    def _compute_name(self):
        for mt in self:
            mt.name =mt.muctieu_id.name

    def _compute_chucnang(self):
        for mt in self:
            mt.chucnang =mt.muctieu_id.chucnang
    def _compute_thietke(self):
        for mt in self:
            mt.thietke =mt.muctieu_id.thietke

    def _compute_tieuchi_chuadat(self):
        for mt in self:
            mt.tieuchi_chuadat =mt.muctieu_id.tieuchi_chuadat

    def _compute_tieuchi_hinhthanh(self):
        for mt in self:
            mt.tieuchi_hinhthanh =mt.muctieu_id.tieuchi_hinhthanh

    def _compute_tieuchi_dat(self):
        for mt in self:
            mt.tieuchi_dat =mt.muctieu_id.tieuchi_dat

    def action_ghinhan_ketqua_canthiep(self):
        return None