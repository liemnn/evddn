from odoo import models, fields, api, _
from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class KetLuan(models.Model):
    _name = "ekids.ketluan"
    _description = "Kết luận Đánh giá"

    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", readonly=True)
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh")
    ngay_danhgia = fields.Date(string="Ngày đánh giá")
    nguoi_danhgia = fields.Char(string="Người đánh giá")
    name = fields.Char(string="Tên hiển thị", compute="_compute_ketluan_name", readonly=True)
    chinh_dm_roiloan_id = fields.Many2one("ekids.ct_dm_roiloan", string="Dạng [Rối loạn]")
    chinh_ct_chuongtrinh_id = fields.Many2one("ekids.ct_chuongtrinh", string="Chương trình")
    chinh_dm_capdo_id = fields.Many2one("ekids.ct_dm_capdo", string="Cấp độ")
    dm_tuoi_id = fields.Many2one("ekids.ct_dm_tuoi", string="Tuổi can thiệp của trẻ")

    roiloan2dikem_ids = fields.One2many("ekids.ketluan_roiloan2dikem",
                                        "ketluan_id", string="Rối loạn đi kèm", ondelete='cascade')
    ketluan = fields.Html(string="Kết luận")

    gv_lapkehoach_id = fields.Many2one("ekids.giaovien"
                                       , string="Giáo viên [Lập kế hoạch khung]")
    gv_canthiep_id = fields.Many2one("ekids.giaovien"
                                     , string="Giáo viên phụ trách can thiệp")


    trangthai = fields.Selection([("0", "Đã kết luận để lên [Kế hoạch] can thiệp"),("1", "Đã hoàn thành [Can thiệp]")]
                                 , string="Trạng thái")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            coso_id = self.env.context.get('default_coso_id') or vals.get('coso_id')
            if not coso_id and vals.get('hocsinh_id'):
                hs = self.env['ekids.hocsinh'].browse(vals['hocsinh_id'])
                if hs:
                    coso_id = hs.coso_id.id
            vals['coso_id'] = coso_id
        return super().create(vals_list)

    def _compute_ketluan_name(self):
        for kh in self:
            if kh.hocsinh_id:
                name =""
                if kh.chinh_dm_roiloan_id and kh.chinh_dm_roiloan_id.ten:
                    name = str(kh.chinh_dm_roiloan_id.ten)
                    if kh.roiloan2dikem_ids:
                        name +="-(Rối loạn đi kèm:"
                        for rl in kh.roiloan2dikem_ids:
                            name += str(rl.dm_roiloan_id.ten) +"/"
                        name += ")"
                kh.name=name



    @api.constrains('trangthai')
    def _check_only_one_trangthai(self):
        for record in self:
            if record.trangthai == '0':
                existing = self.search_count([
                    ('id', '!=', record.id),
                    ('hocsinh_id', '=', record.hocsinh_id.id),
                    ('trangthai', '=', '0')
                ])
                if existing > 0:
                    raise ValidationError("Bạn không thể tạo một kết luận mới khi đang có một kết luận ở trạng thái [Đã kết luận] !")




