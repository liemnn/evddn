import logging
from odoo import models, fields, api, exceptions
from datetime import date

_logger = logging.getLogger(__name__)
class HocSinhCaCanThiep(models.Model):
    _name = "ekids.hocsinh_ca_canthiep"
    _description = "Cấu hình thiết các ca can thiệp cho học sinh"




    sequence = fields.Integer(string="Thứ tự", default=1)
    coso_id = fields.Many2one("ekids.coso", related="hocsinh_id.coso_id", string="Cơ sở", required=True,
                              ondelete="restrict")
    hocsinh_id = fields.Many2one("ekids.hocsinh", string="Học sinh", required=True, ondelete="cascade")
    name =fields.Char(string="Thời gian áp dụng",compute="_compute_diemdanh_thoigian_hoc_name", readonly=True)

    t2= fields.Boolean(string="T2")
    t3 = fields.Boolean(string="T3")
    t4 = fields.Boolean(string="T4")
    t5 = fields.Boolean(string="T5")
    t6 = fields.Boolean(string="T6")
    t7 = fields.Boolean(string="T7")
    t8 = fields.Boolean(string="CN")

    tu = fields.Char(string="Từ (HH:MM)", help='Format: HH:MM')
    den = fields.Char(string="Đến (HH:MM)", help='Format: HH:MM')

    dm_ca_id = fields.Many2one('ekids.hocphi_dm_ca', string="Loại hình(ca) can thiệp",required=True,ondelete="cascade")
    is_ganthucong =fields.Boolean(string="Người dùng gán thủ công",default=True)
    giaovien_id = fields.Many2one("ekids.giaovien" , string="Giáo viên",ondelete="restrict")
    tien = fields.Float(string='Số tiền(vnđ)', digits=(10, 0),required=True)
    is_hoantien_khi_nghi = fields.Boolean(string="Sẽ [Hoàn tiền] theo quy định khi [Nghỉ]", default=True)

    desc = fields.Html(string="Ghi chú")


    @api.onchange('dm_ca_id')
    def _onchange_hocsinh_ca_canthiep_dm_ca_id(self):
        for record in self:
            if record.dm_ca_id:
                record.tien = record.dm_ca_id.tien
                record.desc = record.dm_ca_id.desc
                record.is_hoantien_khi_nghi =record.dm_ca_id.is_hoantien_khi_nghi
            else:
                record.tien = 0
                record.desc = ""
                record.is_hoantien_khi_nghi =True


    def _compute_diemdanh_thoigian_hoc_name(self):
        for e in self:
            day =""
            if e.t2:
                day+= "T2 "
            if e.t3:
                day+= "T3 "
            if e.t4:
                day+= "T4 "
            if e.t5:
                day+= "T5 "
            if e.t6:
                day+= "T6 "
            if e.t7:
                day+= "T7 "
            if e.t8:
                day+= "CN "
            e.name=day

    def func_kiemtra_ca_hocnay_co_chophep(self,ngay:date.today()):
        weekday = ngay.weekday() +2
        thu_field = 't' + str(weekday )
        is_hoc = getattr(self, thu_field)
        return is_hoc

    @api.model_create_multi
    def create(self, vals_list):
        records = []
        for vals in vals_list:
            coso = None
            coso_id = self.env.context.get('default_coso_id') or vals.get('coso_id')
            if not coso_id:
                if vals['hocsinh_id']:
                    hs = self.env['ekids.hocsinh'].browse(vals['hocsinh_id'])
                    if hs:
                        coso_id = hs.coso_id.id
            vals['coso_id'] = coso_id
            result =super(HocSinhCaCanThiep, self).create(vals)
            if result:
                #Tinh toan so ca trong
                hocsinh_id=result.hocsinh_id.id
                result.func_tinhtoan_soca_thu_may_trong_tuan(hocsinh_id)
                records.append(result)
        return records[0] if len(records) == 1 else records

    @api.model
    def write(self, vals):
        hocsinh_id = self.hocsinh_id.id
        result =super().write(vals)
        if result == True:
            (self.env['ekids.hocsinh_ca_canthiep']
             .func_tinhtoan_soca_thu_may_trong_tuan(hocsinh_id))
        return  result

    @api.model
    def unlink(self):
        hocsinh_id =self.hocsinh_id.id
        result = super().unlink()
        if result == True:
            (self.env['ekids.hocsinh_ca_canthiep']
             .func_tinhtoan_soca_thu_may_trong_tuan(hocsinh_id))
        return result


    # thực hiện tinnh toán trước số ca học trong tuần của trẻ khi thay đổi hoặc thiết lập giá trị trong tuần


    def func_tinhtoan_soca_thu_may_trong_tuan(self,hocsinh_id):
        # B1 xoa toàn bộ dữ liệu cũ
        ca_thus = self.env['ekids.tinhtoan_ca2thu'].search([
            ('hocsinh_id', '=', hocsinh_id)
        ])

        if ca_thus:
            for ca_thu in ca_thus:
                ca_thu.unlink()

        # thiết lập tính toán lại từng ngày trong tháng
        for i in range(2, 9):
            field_name ='t'+str(i)
            # lay về tất cả các ca thuộc thu trong tuần
            domain =[
                    ('hocsinh_id', '=', hocsinh_id),
                    ('dm_ca_id.trangthai','=','1'),
                    (field_name,'=', True)
                    ]
            ca_canthieps = self.env['ekids.hocsinh_ca_canthiep'].search(domain)
            if ca_canthieps:
                for ca_canthiep in ca_canthieps:
                    ca2thu = self.env['ekids.tinhtoan_ca2thu'].search([
                        ('hocsinh_id', '=', hocsinh_id),
                        ('dm_ca_id', '=', ca_canthiep.dm_ca_id.id),
                        ('thu', '=',i),
                    ])
                    if ca2thu:
                        soca =ca2thu.soca + 1
                        ca2thu.write({'soca':soca})

                    else:
                        data = {
                            'hocsinh_id':hocsinh_id,
                            'dm_ca_id':ca_canthiep.dm_ca_id.id,
                            'thu':i,
                            'soca':1

                        }
                        self.env['ekids.tinhtoan_ca2thu'].create(data)