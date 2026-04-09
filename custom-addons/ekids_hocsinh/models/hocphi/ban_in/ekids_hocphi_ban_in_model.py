from odoo import models, fields, api
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.ekids_func import string_util
    from odoo.addons.ekids_func import hocsinh_util
    from odoo.addons.ekids_func import nghile_util
    from odoo.addons.ekids_func import coso_util
    from odoo.addons.ekids_func import ngay_util
    from odoo.addons.ekids_func import hocsinh_util
except ImportError as e:
    _logger.warning(f"Không thể import ekids_func.string_util: {e}")




class HocPhiBanIn(models.TransientModel):
    _name = 'ekids.hocphi_banin'
    _description = 'Bản In học phí'

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", readonly=True)

    thang = fields.Selection(
        [('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng',
        required=True,
        default='1'

    )

    nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 5, datetime.now().year + 1)],
        string="Năm",
        required=True,
        default=lambda self: str(date.today().year)
    )

    loai = fields.Selection(
        [('0', 'In phiếu - Xác nhận thu học phí (phụ huynh ký)')
            , ('1', 'In phiếu - Học phí(Cơ quan Thuế)')],
        string='Loai',
        required=True,
        default='0'

    )




    def get_table_data(self):

        dm_bantrus = self.env['ekids.hocphi_dm_thu_bantru'].search(
            [('coso_id', '=', self.coso_id.id)
                , ('trangthai', '=', '1')
                , ('is_hocphi', '=', True)

             ])
        if self.loai =='0':
            header = ['TT', 'Học sinh', '1.Học phí (vnđ)','Phụ huynh ký xác nhận', 'Ghi chú']
        else:
            header =['TT','Học sinh','1.Học phí (vnđ)','2.Thu khác(vnđ)','Tổng phải đóng =[1]+[2] (vnđ)','Ghi chú'
                ,'Địa chỉ','Ngày đóng']
        table_data = [header]  # Header
        thang =self.thang
        nam =self.nam




        hocphis = self.env['ekids.hocphi'].search(
            [('coso_id', '=', self.coso_id.id)
                , ('thang_id.name', '=', str(thang))
                , ('nam_id.name', '=', str(nam))

             ])
        if hocphis:
            index =1
            for hocphi in hocphis:
                table_data = self.get_table_data_by_hocphi(table_data,index,dm_bantrus,hocphi)
                index =index +1

            # thực hiện tính tổng
            if self.loai == '1':
                if len(table_data)>1:
                    index =0
                    tong_hocphi=0
                    tong_khac=0
                    tong_dong=0
                    for data in table_data:
                        if index>0:
                           tong_hocphi += string_util.string2number(data[2])
                           tong_khac += string_util.string2number(data[3])
                           tong_dong += string_util.string2number(data[4])
                        index = index + 1

                    table_data.append([
                    '',
                    'Tổng',
                    string_util.number2string(tong_hocphi),
                    string_util.number2string(tong_khac),
                    string_util.number2string(tong_dong),
                    " ",
                    " ",
                    " "
                ])
            else:
                if len(table_data) > 1:
                    index = 0
                    tong_dong = 0
                    for data in table_data:
                        if index > 0:
                            tong_dong += string_util.string2number(data[2])
                        index = index + 1

                    table_data.append([
                        '',
                        'Tổng',
                        string_util.number2string(tong_dong),
                        " ",
                        " "
                    ])


        return table_data



    #Tinh toán tháng

    def get_table_data_by_hocphi(self,table_data,index,dm_bantrus,hocphi):
        tien =string_util.number2string(hocphi.hocphi_phaidong)
        data =[]
        data.append(index)
        data.append(hocphi.hocsinh_id.name)
        if self.loai == '1':
            #tính toán thu khác
            hs =hocphi.hocsinh_id
            diachi =""
            if hs.diachi_chitiet:
                diachi+= str(hs.diachi_chitiet)+", "
            if hs.dm_xa_id:
                diachi+= str(hs.dm_xa_id.name)+", "
            if hs.dm_tinh_id:
                diachi += str(hs.dm_tinh_id.name)

            other_desc =""
            other_tien =0
            hocphi_tien=0
            if dm_bantrus:
                for dm_bantru in dm_bantrus:
                    hocphi_bantru_ids = hocphi.hocphi_bantru_ids
                    if hocphi_bantru_ids:
                        for hocphi_bantru in hocphi_bantru_ids:
                            if hocphi_bantru.dm_thu_bantru_id.id == dm_bantru.id:
                                dm_tien =0
                                if hocphi.is_giamhocphi_dacthu == True:
                                    if dm_bantru.is_giam_hocphi ==True:
                                        dm_tien= hocphi_bantru.tien - ((hocphi_bantru.tien / 100) * hocphi.tyle_giamhocphi_bantru)
                                    else:
                                        dm_tien += hocphi_bantru.tien
                                else:
                                    if dm_bantru.is_giam_hocphi ==True:
                                        dm_tien += hocphi_bantru.tien - ((hocphi_bantru.tien / 100) * hocphi.tyle_giamhocphi)
                                    else:
                                        dm_tien += hocphi_bantru.tien
                                other_desc += "-" + str(dm_bantru.name) + "=" + string_util.number2string(
                                            dm_tien) + " vnđ \n"
                                other_tien += dm_tien


                                # them vao tien ban tru
            hocphi_tien = hocphi.hocphi_phaidong - other_tien
            data.append(string_util.number2string(hocphi_tien))
            data.append(string_util.number2string(other_tien))
            data.append(string_util.number2string(hocphi.hocphi_phaidong))
            data.append(other_desc)
            data.append(diachi)
            data.append(string_util.date2string(hocphi.ngay_dong_hocphi))
        else:
            data.append(string_util.number2string(hocphi.hocphi_phaidong))
            data.append("")
            data.append("")

        table_data.append(data)


        return table_data



    def action_xem_banin(self):
        today = date.today()
        formatted = today.strftime("Vào hồi %H:%M  ngày %d/%m/%Y")
        data = {
            'coso': self.coso_id.fullname,
            'thoigian':formatted,
            'nam': self.nam,
            'thang': self.thang,
            'table_data': self.get_table_data()

        }
        return (self.env.ref('ekids_hocsinh.action_hocphi_banin_report')
                .report_action(self, data=data))


