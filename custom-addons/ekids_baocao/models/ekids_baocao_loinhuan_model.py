from odoo import models, fields, api
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta

class BaoCaoLoiNhuanWizard(models.TransientModel):
    _name = 'ekids.baocao_loinhuan'
    _description = 'Báo cáo lợi nhuận của cơ sở'

    coso_id = fields.Many2one("ekids.coso", string="Cơ sở", readonly=True)


    tu_thang = fields.Selection(
        [('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng',
        required=True,
        default='1'

    )

    tu_nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 5, datetime.now().year + 1)],
        string="Năm",
        required=True,
        default=lambda self: str((date.today() - relativedelta(months=+1)).year)
    )

    den_thang = fields.Selection(
        [('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'),
         ('6', 'Tháng 6'), ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'),
         ('11', 'Tháng 11'), ('12', 'Tháng 12')],
        string='Tháng',
        required=True,
        default='1'
    )

    den_nam = fields.Selection(
        [(str(year), str(year)) for year in range(datetime.now().year - 5, datetime.now().year + 2)],
        string="Năm",
        required=True,
        default=lambda self: str((date.today() - relativedelta(months=+1)).year +1)
        )


    def get_table_data(self):

        table_data = [['Tháng','Năm', '[1] Học phí'
                          ,'[2] Nguồn thu khác'
                          ,'[3] Chi lương \n (Lương + BHXH nhà trường đóng cho GV)'
                          ,'[4] Chi BHXH \n (Giáo viên phải đóng)'
                          ,'[5] Chi/Tiêu khác'
                          ,'Lợi nhuận = \n [1]+[2]-[3]-[4]-[5]']]  # Header
        tu_thang =self.tu_thang
        tu_nam =self.tu_nam
        den_thang = self.den_thang
        den_nam = self.den_nam
        ngay_first = date(int(tu_nam),int(tu_thang),1)
        ngay_last = date(int(den_nam), int(den_thang), 1)

        ngay =ngay_first
        while ngay <= ngay_last:
            self.get_table_data_by_thang(table_data, str(ngay.year),str(ngay.month))
            ngay = ngay + relativedelta(months=1)

        self.get_table_data_by_nam(table_data)


        return table_data



    #Tinh toán tháng

    def get_table_data_by_thang(self,table_data,nam,thang):
        hocphi = self.sum_tong_hocphi_thucthu_by_thang(nam,thang)
        thukhac = self.sum_tong_thu_by_thang(nam, thang)
        luong = self.sum_tong_luong_chitra_by_thang(nam,thang)
        thuho = self.sum_tong_nhatruong_thuho_chitra_by_thang(nam, thang)
        chikhac = self.sum_tong_chi_by_thang(nam,thang)


        loinhuan = (hocphi + thukhac) - (luong +thuho+chikhac)
        table_data.append([
            'Tháng:'+thang,
            nam,
            self.number2string(hocphi),
            self.number2string(thukhac),
            self.number2string(luong),
            self.number2string(thuho),
            self.number2string(chikhac),
            self.number2string(loinhuan)
        ])
        return table_data


    def sum_tong_hocphi_thucthu_by_thang(self,nam,thang):
        result = self.env['ekids.hocphi'].read_group(
            domain=[('coso_id','=',self.coso_id.id)
                    ,('thang_id.nam_id.name', '=', nam)
                    ,('thang_id.name', '=', thang)],  # điều kiện lọc (nếu cần)
            fields=['hocphi_phaidong'],  # tên trường cần tính tổng
            groupby=[]  # không cần group theo trường nào cả
        )

        total = result[0]['hocphi_phaidong'] if result else 0.0

        return total

    def sum_tong_nhatruong_thuho_chitra_by_thang(self,nam,thang):
        result = self.env['ekids.luong'].read_group(
            domain=[('coso_id', '=', self.coso_id.id)
                , ('thang_id.nam_id.name', '=', nam)
                , ('thang_id.name', '=', thang)],  # điều kiện lọc (nếu cần)
            fields=['nhatruong_thuho'],  # tên trường cần tính tổng
            groupby=[]  # không cần group theo trường nào cả
        )

        total = result[0]['nhatruong_thuho'] if result else 0.0

        return total

    def sum_tong_luong_chitra_by_thang(self,nam,thang):
        result = self.env['ekids.luong'].read_group(
            domain=[('coso_id', '=', self.coso_id.id)
                , ('thang_id.nam_id.name', '=', nam)
                , ('thang_id.name', '=', thang)],  # điều kiện lọc (nếu cần)
            fields=['tong_nhatruong_chi'],  # tên trường cần tính tổng
            groupby=[]  # không cần group theo trường nào cả
        )

        total = result[0]['tong_nhatruong_chi'] if result else 0.0

        return total


    def sum_tong_chi_by_thang(self,nam,thang):
        result = self.env['ekids.chitieu_chi'].read_group(
            domain=[('coso_id', '=', self.coso_id.id)
                , ('thang_id.nam_id.name', '=', nam)
                , ('thang_id.name', '=', thang)],  # điều kiện lọc (nếu cần)
            fields=['tien'],  # tên trường cần tính tổng
            groupby=[]  # không cần group theo trường nào cả
        )

        total = result[0]['tien'] if result else 0.0

        return total

    def sum_tong_thu_by_thang(self,nam,thang):
        result = self.env['ekids.chitieu_thu'].read_group(
            domain=[('coso_id', '=', self.coso_id.id)
                , ('thang_id.nam_id.name', '=', nam)
                , ('thang_id.name', '=', thang)],  # điều kiện lọc (nếu cần)
            fields=['tien'],  # tên trường cần tính tổng
            groupby=[]  # không cần group theo trường nào cả
        )

        total = result[0]['tien'] if result else 0.0

        return total


    #Tinh toán tổng của năm

    def get_table_data_by_nam(self,table_data):
        hocphi = 0.0
        thukhac = 0.0
        luong = 0.0
        thuho = 0.0
        chikhac = 0.0

        if table_data:
            i=0
            for data in table_data:
                if i == 0:
                    i =i+1
                    continue
                hocphi = hocphi + self.string2number(data[2])
                thukhac = thukhac + self.string2number(data[3])
                luong = luong + self.string2number(data[4])
                thuho = thuho + self.string2number(data[5])
                chikhac = chikhac + self.string2number(data[6])
                i = i+1


        loinhuan = (hocphi + thukhac) - (luong +chikhac)
        table_data.append([
            'TỔNG THEO NĂM TÀI CHÍNH','',
            self.number2string(hocphi),
            self.number2string(thukhac),
            self.number2string(luong),
            self.number2string(thuho),
            self.number2string(chikhac),
            self.number2string(loinhuan)
        ])
        return table_data

    def action_xem_baocao(self):
        # Lấy ngày giờ hiện tại chuẩn theo múi giờ của người dùng thao tác
        current_time = fields.Datetime.context_timestamp(self, fields.Datetime.now())

        # Định dạng lại chuỗi
        formatted = current_time.strftime("Vào hồi %H:%M ngày %d/%m/%Y")

        data = {
            'coso': self.coso_id.fullname,
            'thoigian': formatted,
            'nam': self.tu_nam,
            'table_data': self.get_table_data()
        }
        return (self.env.ref('ekids_baocao.action_report_view_loinhuan')
                .report_action(self, data=data))


    def number2string(self,total):
        total = "{:,.0f}".format(total)
        return total

    def string2number(self, s):
        if not s:
            return 0
        # bỏ dấu phẩy ngăn cách hàng nghìn
        s = s.replace(",", "").strip()
        return float(s)