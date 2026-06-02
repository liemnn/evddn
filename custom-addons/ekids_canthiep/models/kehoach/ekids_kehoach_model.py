from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KeHoach(models.Model):
    _name = 'ekids.kehoach'
    _description = 'Kết luận Đánh giá & Định hướng Kế hoạch'
    _order = 'id desc'

    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    name = fields.Char(string="Mã phiếu", required=True, compute="_compute_name")

    # 1. THÔNG TIN HỌC SINH
    hocsinh_id = fields.Many2one('ekids.hocsinh', string="Họ và tên", required=True, tracking=True)  # [cite: 2]

    # 2. CHẨN ĐOÁN & MỨC ĐỘ

    trangthai = fields.Selection([
        ("00", "Kết luận đợi lập kế hoạch"),
        ("01", "Đang lập kế hoạch"),
        ("1", "Đang can thiệp"),
        ("02", "Kế hoạch đã phê duyệt"),
        ("-1", "Kế hoạch hết hiệu lực"),
        ("03", "Kế hoạch cần chỉnh sửa"),

    ], string="Trạng thái",default="00")


    tu_ngay = fields.Date(string="Từ ngày")
    den_ngay = fields.Date(string="Đến ngày")
    songay = fields.Integer(string="Số ngày")

    muctieu_ids = fields.Many2many(comodel_name="ekids.ct_muctieu"
                                   , relation="ekids_kehoach_ct_muctieu4kehoach_rel"
                                   , column1="kehoach_id"
                                   , column2="muctieu_id"
                                   , string="Các mục tiêu cho kế hoạch")

    kehoach_linhvuc_ids = fields.One2many("ekids.kehoach_linhvuc",
                                          "kehoach_id", string="Các Lĩnh vực của kế hoạch")

    kehoach_muctieu_ids = fields.One2many("ekids.kehoach_muctieu",
                                  "kehoach_id", string="Các mục tiêu của kế hoạch")





    def _compute_name(self):
        for kh in self:
            kh.name = kh.hocsinh_id.name

    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            result = super(KeHoach, self).create(vals)
            if result:
                # Tinh toan so ca trong
                result.func_tao_macdinh_kehoach_muctieu()
                records.append(result)
        return records[0] if len(records) == 1 else records

    @api.model
    def write(self, vals):
        result = super().write(vals)
        if "kehoach_linhvuc_ids" in vals:
            result.func_tao_macdinh_kehoach_muctieu()
        return result


    def func_tao_macdinh_kehoach_muctieu(self):
        # unlink cái cũ

        # tao cai moi
        if self.kehoach_linhvuc_ids:
            for lv in self.kehoach_linhvuc_ids:
                muctieus = self.func_danhsach_muctieu(lv.linhvuc_id,lv.tuoi_id)
                if muctieus:
                    for muctieu in muctieus:
                        data={
                            'kehoach_id':self.id,
                            'muctieu_id':muctieu.id
                        }
                        self.env['ekids.kehoach_muctieu'].create(data)




    def func_danhsach_muctieu(self,linhvuc_id,tuoi_id):
        domain =[('linhvuc_id','=',linhvuc_id)]
        if tuoi_id:
            domain.append(('tuoi_id', '=', tuoi_id))
        muctieus = self.env['ekids.ct_muctieu'].search(domain)
        return muctieus


    def action_lap_kehoach(self):
        form_view_id = self.env.ref('ekids_canthiep.lap_kehoach_form').id
        kehoach = self.func_get_kehoach_hocsinh(self)
        if kehoach:
            return {
                'type': 'ir.actions.act_window',
                'name': 'LẬP KẾ HOẠCH',
                'res_model': 'ekids.kehoach',
                'view_mode': 'form',
                'res_id': kehoach.id,
                'views': [(form_view_id, 'form')],
                'target': 'new',
                'domain': [('coso_id', '=', self.id)],
                'context': {
                    'default_coso_id': self.coso_id.id,
                    'default_hocsinh_id': self.id
                },
            }

    def action_them_muctie(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'THÊM MỤC TIÊU',
            'res_model': 'ekids.kehoach_muctieu_wizard',
            'view_mode': 'form',

            'target': 'new',
            'domain': [('coso_id', '=', self.id)],
            'context': {
                'default_coso_id': self.coso_id.id,
                'default_hocsinh_id': self.id
            },
        }


