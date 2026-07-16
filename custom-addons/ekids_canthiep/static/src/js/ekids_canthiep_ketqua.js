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

            tempGrid.push({
                dayNum: d,
                resId: rec.resId,
                rawRecord: rec,
                trangthaiValue: rawStatusValue,
                loai: rawLoaiValue, // Truyền field loai xuống template
                is_date_status: rec.data.is_date_status,
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
            phantram: totalEvaluated ? Math.round((totalEvaluated/ tempGrid.length) * 100) : 0
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

    async saveInlineData() {
        if (this.props.readonly || this.state.selectedDay.loai !== "1") return;
        const day = this.state.selectedDay;
        const commentElem = document.getElementById("matrix_quick_desc");
        const nextStatus = day.trangthaiValue;
        const nextComment = commentElem.value.trim();

        try {
            if (day.rawRecord) {
                await day.rawRecord.update({
                    trangthai: nextStatus,
                    desc: nextComment
                });
                await day.rawRecord.save();
            }

            this.notification.add(`Đã lưu nhật ký ngày ${day.dateDisplayStr}`, { type: "success" });
            this.state.selectedDay = null;
            await this.buildKehoachKetQua2MucTieu();
        } catch (error) {
            console.error("Lỗi ghi nhận dữ liệu can thiệp:", error);
        }
    }
}

registry.category("fields").add("ekids_canthiep_ketqua", {
    component: CanThiepKetQuaWidget,
    supportedTypes: ["one2many"],
});