from odoo import models, fields, api, exceptions


class HocSinhInherit(models.Model):
   _inherit = "ekids.hocsinh"


   trangthai_kehoach = fields.Char(string="Trạng thái kế hoạch",compute="_compute_trangthai_kehoach")

   is_co_ketluan =fields.Boolean(string="Xem có kết luận còn hiệu lực không",compute="_compute_is_co_ketluan")

   def _compute_is_co_ketluan(self):
      for hs in self:
         domain =[('hocsinh_id','=',hs.id),
                  ('trangthai', '=', '1'),
                  ]
         count = self.env['ekids.kehoach_ketluan'].search_count(domain)
         if count >0:
            hs.is_co_ketluan = True
         else:
            hs.is_co_ketluan = False


   def _compute_trangthai_kehoach(self):
      for hs in self:
         hs.trangthai_kehoach ="Chưa có kế hoạch"