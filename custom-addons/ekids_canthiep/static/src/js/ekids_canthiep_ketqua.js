/** @odoo-module **/

import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CanThiepKetQuaWidget extends Component {
    static template = "ekids_canthiep.CanThiepKetQuaWidgetTemplate";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            daysGrid: [],
            selectedDay: null,
            summary: { total: 0, dat: 0, hinhthanh: 0, chuadat: 0, phantram: 0 }
        });

        onWillStart(async () => { await this.buildKehoachKetQua2MucTieu(); });
        onWillUpdateProps(async () => { await this.buildKehoachKetQua2MucTieu(); });
    }

    _extractPlainText(htmlString) {
        if (!htmlString) return "";
        try {
            const doc = new DOMParser().parseFromString(htmlString, 'text/html');
            return doc.body.textContent || doc.body.innerText || "";
        } catch (e) {
            return htmlString.replace(/<\/?[^>]+(>|$)/g, "");
        }
    }

    async buildKehoachKetQua2MucTieu() {
        const ketqua2muctieu = this.props.record.data[this.props.name].records || [];

        // Sắp xếp bản ghi theo ngày
        let sortedRecords = [...ketqua2muctieu].sort((a, b) => {
            let dateA = a.data.ngay ? (typeof a.data.ngay === 'object' ? a.data.ngay.toISODate() : String(a.data.ngay)) : '';
            let dateB = b.data.ngay ? (typeof b.data.ngay === 'object' ? b.data.ngay.toISODate() : String(b.data.ngay)) : '';
            return dateA.localeCompare(dateB);
        });

        let tempGrid = [];
        let countDat = 0, countHinhThanh = 0, countChuaDat = 0;

        sortedRecords.forEach((rec, index) => {
            const d = index + 1;
            const currentDateStr = rec.data.ngay;
            const rawStatusValue = rec.data.trangthai;
            const rawLoaiValue = rec.data.loai;

            // LOGIC TỔNG HỢP: CHỈ TÍNH KHI ĐI HỌC (loai === '1')
            if (rawLoaiValue === "1") {
                if (rawStatusValue === "1") countDat++;
                else if (rawStatusValue === "-1") countChuaDat++;
                else if (rawStatusValue === "2") countHinhThanh++;
            }

            let dateShortStr = "";
            if (currentDateStr) {
                if (typeof currentDateStr === 'object' && currentDateStr.toFormat) {
                    dateShortStr = currentDateStr.toFormat('dd/MM');
                } else {
                    const parts = String(currentDateStr).split('-');
                    dateShortStr = parts.length === 3 ? `${parts[2]}/${parts[1]}` : String(currentDateStr);
                }
            } else {
                dateShortStr = `${d}`;
            }

            // 🌟 ĐỌC DỮ LIỆU: Cho phép số 0 hiển thị nguyên bản, không dùng || 0 làm mờ giá trị
            const solanThu = rec.data.solan_thu !== undefined && rec.data.solan_thu !== false ? Number(rec.data.solan_thu) : 10;
            const solanThuDat = rec.data.solan_thu_dat !== undefined && rec.data.solan_thu_dat !== false ? Number(rec.data.solan_thu_dat) : 0;

            let tyleThu = 0;
            if (rec.data.tyle_thu !== undefined && rec.data.tyle_thu !== false && rawStatusValue !== '0') {
                tyleThu = Number(rec.data.tyle_thu);
            } else if (solanThu > 0 && rawStatusValue !== '0') {
                tyleThu = Math.round((solanThuDat / solanThu) * 100);
            }

            tempGrid.push({
                dayNum: d,
                resId: rec.resId,
                rawRecord: rec,
                trangthaiValue: rawStatusValue || "0",
                loai: rawLoaiValue,
                is_date_status: rec.data.is_date_status,
                solan_thu: solanThu,
                solan_thu_dat: solanThuDat,
                tyle_thu: tyleThu,
                comment: this._extractPlainText(rec.data.desc),
                dateDisplayStr: currentDateStr ? (typeof currentDateStr === 'object' ? currentDateStr.toFormat('dd/MM/yyyy') : currentDateStr) : '',
                dateShortStr: dateShortStr,
                tooltipText: currentDateStr ? String(currentDateStr) : ''
            });
        });

        this.state.daysGrid = tempGrid;

        const totalEvaluated = countDat + countHinhThanh + countChuaDat;

        this.state.summary = {
            total: tempGrid.length,
            dat: countDat,
            hinhthanh: countHinhThanh,
            chuadat: countChuaDat,
            totalEvaluated: totalEvaluated,
            phantram: tempGrid.length ? Math.round((totalEvaluated / tempGrid.length) * 100) : 0
        };

        if (this.state.selectedDay) {
            const currentSelected = tempGrid.find(g => g.dayNum === this.state.selectedDay.dayNum);
            if (currentSelected) {
                this.state.selectedDay = { ...currentSelected };
            }
        }
    }

    onDayClick(day) {
        this.state.selectedDay = { ...day };
    }

    selectQuickStatus(statusValue) {
        if (!this.state.selectedDay || this.state.selectedDay.loai !== "1") return;
        this.state.selectedDay.trangthaiValue = statusValue;
    }

    /* 🌟 HÀM TÍNH TOÁN REALTIME KHI GÕ SỐ LẦN ĐẠT (CHO PHÉP SỐ 0) */
    onInputSolanThuDat(ev) {
        const day = this.state.selectedDay;
        if (!day || day.loai !== "1") return;

        let rawVal = ev.target.value.trim();
        let val = rawVal === "" ? 0 : parseInt(rawVal, 10);

        if (isNaN(val) || val < 0) {
            val = 0;
            ev.target.value = 0;
        }

        // Kiểm tra không vượt quá tổng lần thử
        if (day.solan_thu > 0 && val > day.solan_thu) {
            this.notification.add(`Số lần đạt (${val}) không được vượt quá số lần thử (${day.solan_thu})!`, { type: "warning" });
            val = day.solan_thu;
            ev.target.value = day.solan_thu;
        }

        day.solan_thu_dat = val;

        // 🌟 TỰ ĐỘNG CHỐT TRẠNG THÁI: Dù là 0 vẫn tính tỷ lệ và chuyển trạng thái rõ ràng
        if (day.solan_thu > 0) {
            day.tyle_thu = Math.round((val / day.solan_thu) * 100);
            if (day.tyle_thu >= 80) {
                day.trangthaiValue = "1";   // Đạt (+)
            } else if (day.tyle_thu > 0) {
                day.trangthaiValue = "2";   // Đang hình thành (+/-)
            } else {
                day.trangthaiValue = "-1";  // 0 lần đạt -> Chưa đạt (-)
            }
        } else {
            day.tyle_thu = 0;
            day.trangthaiValue = "-1";
        }
    }

    async saveInlineData() {
        if (this.props.readonly || !this.state.selectedDay || this.state.selectedDay.loai !== "1") return;
        const day = this.state.selectedDay;
        const commentElem = document.getElementById("matrix_quick_desc");
        const nextComment = commentElem ? commentElem.value.trim() : "";

        // 🌟 ĐẢM BẢO LẤY CHÍNH XÁC GIÁ TRỊ SỐ NGUYÊN (KỂ CẢ SỐ 0)
        const solanThuDat = (day.solan_thu_dat !== undefined && day.solan_thu_dat !== null) ? Number(day.solan_thu_dat) : 0;

        // Nếu số lần đạt = 0 mà trạng thái vẫn là '0' (chưa chọn) thì tự động chuyển thành '-1' (Chưa đạt)
        let nextStatus = day.trangthaiValue;
        if (!nextStatus || nextStatus === "0") {
            nextStatus = solanThuDat > 0 ? "2" : "-1";
            day.trangthaiValue = nextStatus;
        }

        // Kiểm tra logic hợp lệ
        if (day.solan_thu > 0 && solanThuDat > day.solan_thu) {
            this.notification.add(`Số lần đạt không thể lớn hơn số lần thử (${day.solan_thu})!`, { type: "danger" });
            return;
        }

        try {
            // 🌟 ÉP BUỘC is_giaovien_capnhat = true VÌ GIÁO VIÊN ĐÃ CHỦ ĐỘNG BẤM "XÁC NHẬN LƯU"
            await this.orm.write("ekids.kehoach_ketqua2muctieu", [day.resId], {
                trangthai: nextStatus,
                desc: nextComment,
                solan_thu_dat: solanThuDat,
                tyle_thu: day.solan_thu > 0 ? Math.round((solanThuDat / day.solan_thu) * 100) : 0,
                is_giaovien_capnhat: true,
            });

            // Đồng bộ lại proxy record trong form view
            if (day.rawRecord && day.rawRecord.data) {
                day.rawRecord.data.trangthai = nextStatus;
                day.rawRecord.data.desc = nextComment;
                day.rawRecord.data.solan_thu_dat = solanThuDat;
                day.rawRecord.data.tyle_thu = day.solan_thu > 0 ? Math.round((solanThuDat / day.solan_thu) * 100) : 0;
                day.rawRecord.data.is_giaovien_capnhat = true;
            }

            this.notification.add(`Đã lưu nhật ký ngày ${day.dateDisplayStr}`, { type: "success" });
            this.state.selectedDay = null;

            if (this.props.record && this.props.record.load) {
                await this.props.record.load();
            }
            await this.buildKehoachKetQua2MucTieu();
        } catch (error) {
            console.error("Lỗi ghi nhận dữ liệu can thiệp:", error);
            this.notification.add("Không thể lưu kết quả can thiệp.", { type: "danger" });
        }
    }
}

registry.category("fields").add("ekids_canthiep_ketqua", {
    component: CanThiepKetQuaWidget,
    supportedTypes: ["one2many"],
});