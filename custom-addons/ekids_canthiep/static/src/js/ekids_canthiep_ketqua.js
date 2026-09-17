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

            // LOGIC TỔNG HỢP KẾT QUẢ: CHỈ TÍNH KHI ĐI HỌC (loai === '1')
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

            // 🌟 ĐỌC DỮ LIỆU TỶ LỆ THỬ TỪ RECORD
            const solanThu = rec.data.solan_thu || 0;
            const solanThuDat = rec.data.solan_thu_dat || 0;
            let tyleThu = rec.data.tyle_thu || 0;
            if (!tyleThu && solanThu > 0 && solanThuDat > 0) {
                tyleThu = Math.round((solanThuDat / solanThu) * 100);
            }

            tempGrid.push({
                dayNum: d,
                resId: rec.resId,
                rawRecord: rec,
                trangthaiValue: rawStatusValue,
                loai: rawLoaiValue,
                is_date_status: rec.data.is_date_status,
                // Bổ sung các trường số liệu thử nghiệm
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
            phantram: totalEvaluated ? Math.round((totalEvaluated / tempGrid.length) * 100) : 0
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

    /* 🌟 HÀM TÍNH TOÁN REALTIME KHI GÕ SỐ LẦN ĐẠT */
    onInputSolanThuDat(ev) {
        const day = this.state.selectedDay;
        if (!day || day.loai !== "1") return;

        let val = parseInt(ev.target.value, 10);
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

        // Tự động tính tỷ lệ % và gợi ý trạng thái
        if (day.solan_thu > 0) {
            day.tyle_thu = Math.round((val / day.solan_thu) * 100);
            if (day.tyle_thu >= 80) {
                day.trangthaiValue = "1";   // Đạt (+)
            } else if (day.tyle_thu >0) {
                day.trangthaiValue = "2";   // Đang hình thành (+/-)
            } else {
                day.trangthaiValue = "-1";  // Chưa đạt (-)
            }
        } else {
            day.tyle_thu = 0;
        }
    }

    async saveInlineData() {
        if (this.props.readonly || !this.state.selectedDay || this.state.selectedDay.loai !== "1") return;
        const day = this.state.selectedDay;
        const commentElem = document.getElementById("matrix_quick_desc");
        const nextStatus = day.trangthaiValue || "0";
        const nextComment = commentElem ? commentElem.value.trim() : "";
        const solanThuDat = parseInt(day.solan_thu_dat, 10) || 0;

        // Kiểm tra hợp lệ trước khi lưu
        if (day.solan_thu > 0 && solanThuDat > day.solan_thu) {
            this.notification.add(`Số lần đạt không thể lớn hơn số lần thử (${day.solan_thu})!`, { type: "danger" });
            return;
        }

        try {
            // 🌟 SỬ DỤNG ORM.WRITE TRỰC TIẾP: Tránh lỗi _preprocessX2manyChanges của Record Proxy
            // Lưu ý: Không truyền `tyle_thu` vì backend đã tự compute từ `solan_thu_dat`
            await this.orm.write("ekids.kehoach_ketqua2muctieu", [day.resId], {
                trangthai: nextStatus,
                desc: nextComment,
                solan_thu_dat: solanThuDat,
            });

            // Nếu record proxy của form chính đang active, đồng bộ nhẹ lại
            if (day.rawRecord && day.rawRecord.data) {
                day.rawRecord.data.trangthai = nextStatus;
                day.rawRecord.data.desc = nextComment;
                day.rawRecord.data.solan_thu_dat = solanThuDat;
                if (day.solan_thu > 0) {
                    day.rawRecord.data.tyle_thu = Math.round((solanThuDat / day.solan_thu) * 100);
                }
            }

            this.notification.add(`Đã lưu nhật ký ngày ${day.dateDisplayStr}`, { type: "success" });
            this.state.selectedDay = null;

            // Tải lại toàn bộ dữ liệu widget để cập nhật lưới ngày và thanh tổng kết
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