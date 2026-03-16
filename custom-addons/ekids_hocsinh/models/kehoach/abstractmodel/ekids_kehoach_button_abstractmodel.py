from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class KeHoachButtonAbstractModel(models.AbstractModel):
    _name = 'ekids.kehoach_button_abstractmodel'
    _description = 'Can thiệp'
    _abstract = True

    @api.depends('tu_ngay','sothang','ketluan_id')
    def _compute_is_lapkehoach(self):
        for r in self:
            is_lapkehoach = False
            if r.gv_lapkehoach_id.user_id.id == self.env.uid:
                # TH: Kế hoạch đã đủ thông tin để tạo lập
                if (self.ketluan_id
                        and  self.sothang
                        and   self.tu_ngay
                        and self.trangthai=='0' # phải ở trạng thái đang lập kế hoạch
                    ):
                    is_lapkehoach =True

            r.is_lapkehoach = is_lapkehoach


    def _compute_is_gui_pheduyet(self):
        for r in self:
            is_gui_pheduyet = False
            if r.gv_lapkehoach_id.user_id.id == self.env.uid:
                #TH: Giao vien phải là người được phân công lập kế hoạch

                is_gui_pheduyet = True
            r.is_gui_pheduyet = is_gui_pheduyet

    def _compute_is_keolai_lap_kehoach(self):
        for r in self:
            is_keolai_lap_kehoach = False
            if r.gv_lapkehoach_id.user_id.id == self.env.uid:
                # TH1 neu la nguoi lập kế hoạch và ở trạng thái đợi phê duyệt
                if r.trangthai =='1':
                    is_keolai_lap_kehoach = True
                #TH2 Trạng thái đang can thiệp nhưng người lập kế hoạch cũng chính là người phê duyệt, người can thiệp



            r.is_keolai_lap_kehoach = is_keolai_lap_kehoach

    def _compute_is_pheduyet(self):
        for r in self:
            is_pheduyet = False



            r.is_pheduyet = is_pheduyet

    def _compute_is_ketthuc(self):
        for r in self:
            is_ketthuc = False
            if r.gv_canthiep_id.user_id.id == self.env.uid:
                if r.trangthai == '3':
                    is_ketthuc = True
            r.is_ketthuc = is_ketthuc

    #Ham lọc dữ liệu phù hợp ngữ cảnh


    def action_tao_kehoach_hocsinh_gui_pheduyet(self):
        self.write({'trangthai': '1'})

    def action_tao_kehoach_hocsinh_dualai_lapkehoach(self):
        self.write({'trangthai': '0'})

    def action_tao_kehoach_hocsinh_pheduyet_lapkehoach(self):
        self.write({'trangthai': '3'})
    def action_tao_kehoach_hocsinh_tuchoi_lapkehoach(self):
        self.write({'trangthai': '2'})

    def action_tao_kehoach_hocsinh_ketthuc_canthiep(self):
        self.write({'trangthai': '4'})

