from odoo import models, fields, api, exceptions


class HocSinhInherit(models.Model):
   _inherit = "ekids.hocsinh"


   trangthai_kehoach = fields.Char(string="Trạng thái kế hoạch",compute="_compute_trangthai_kehoach")

   def _compute_trangthai_kehoach(self):
      for hs in self:
         hs.trangthai_kehoach ="Chưa có kế hoạch"