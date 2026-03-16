from odoo import models, fields, api, _
from odoo.api import ValuesType
from odoo.exceptions import ValidationError

class ThongBaoPhuHuynh(models.Model):
    _name = "ekids.thongbao_phuhuynh"
    _description = "Mô tả thông báo đến phụ huynh "


    sequence = fields.Integer(string="STT", default=1)
    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", required=True,
                              ondelete="restrict")

    name = fields.Char(string="Tiêu đề")
    desc = fields.Html(string="Nội dung gửi")
    trangthai = fields.Selection([("0", "Đang soạn thảo")
                                , ("1", "Đã gửi đến toàn bộ [Phụ huynh]")
                                ],
                            string="Trạng thái",default='0',required=True)

    is_gui_phuhuynh =fields.Boolean(string="Đã gửi phụ huynh",compute="_compute_is_gui_phuhuynh")

    is_viewed = fields.Boolean(string="Đã xem",compute="_compute_is_viewed")

    viewed_ids = fields.Many2many('res.users', string="Người đã xem",readonly=True)

    @api.depends("trangthai")
    def _compute_is_gui_phuhuynh(self):
        uid = self.env.uid
        for rec in self:
            if rec.trangthai =='1':
                rec.is_gui_phuhuynh = True
            else:
                rec.is_gui_phuhuynh = False


    def _compute_is_viewed(self):
        uid = self.env.uid
        for rec in self:
            rec.is_viewed = uid in rec.viewed_ids.ids

    def action_gui_thongbao_phuhuynh(self):
        for rec in self:
            rec.trangthai = '1'

    def read(self, fields=None, load='_classic_read'):
        res = super().read(fields=fields, load=load)

        # Chỉ xử lý khi mở form view
        if self.env.context.get("from_form_view"):
            liem=3
        return res


