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

    async buildKehoachKetQua2MucTieu() {
        const ketqua2muctieu = this.props.record.data[this.props.name].records || [];

        // Sắp xếp tăng dần theo trường 'ngay' để các ô chạy đúng tuyến tính tự nhiên
        let sortedRecords = [...ketqua2muctieu].sort((a, b) => {
            if (!a.data.ngay) return 1;
            if (!b.data.ngay) return -1;
            return a.data.ngay.localeCompare(b.data.ngay);
        });

        let tempGrid = [];
        let countDat = 0, countHinhThanh = 0, countChuaDat = 0;

        sortedRecords.forEach((rec, index) => {
            const d = index + 1;
            const currentDateStr = rec.data.ngay;
            const resId = rec.resId;
            const currentComment = rec.data.desc || "";
            const rawStatusValue = rec.data.trangthai;

            // 🌟 LẤY TRỰC TIẾP GIÁ TRỊ ĐÃ TÍNH TOÁN TỪ PYTHON MODEL (Không lo lệch múi giờ)
            const mốcThờiGian = rec.data.is_date_status;

            let statusClass = "empty";
            let symbol = "";
            let isFutureDay = (mốcThờiGian === "1");
            let isToday = (mốcThờiGian === "0");

            let dateDisplayStr = "";
            if (currentDateStr) {
                const parts = currentDateStr.split('-');
                dateDisplayStr = `${parts[2]}/${parts[1]}/${parts[0]}`;
            }

            // ĐIỀU HƯỚNG HIỂN THỊ MÀU SẮC ĐỒNG BỘ 100% THEO CHỈ THỊ
            if (isFutureDay) {
                statusClass = "bg-future-gray"; // 1. Tương lai: màu xám nhẹ, không ký hiệu
                symbol = "";
            } else if (isToday) {
                statusClass = "today-marker";   // 2. Today: màu xám đậm định vị
                symbol = "";
            } else {
                // 3. Quá khứ: Hiển thị theo kết quả
                if (rawStatusValue === "1") { statusClass = "success"; symbol = "+"; countDat++; }
                else if (rawStatusValue === "-1") { statusClass = "danger"; symbol = "-"; countChuaDat++; }
                else if (rawStatusValue === "2") { statusClass = "warning"; symbol = "+/-"; countHinhThanh++; }
                else if (rawStatusValue === "0") { statusClass = "none-canthiep"; symbol = "0"; }
            }

            tempGrid.push({
                dayNum: d,
                resId: resId,
                statusClass: statusClass,
                symbol: symbol,
                comment: currentComment,
                trangthaiValue: rawStatusValue,
                dateDisplayStr: dateDisplayStr,
                isToday: isToday,
                isFuture: isFutureDay,
                tooltipText: dateDisplayStr
            });
        });

        this.state.daysGrid = tempGrid;

        const totalEvaluated = countDat + countHinhThanh + countChuaDat;
        this.state.summary = {
            total: tempGrid.length,
            dat: countDat,
            hinhthanh: countHinhThanh,
            chuadat: countChuaDat,
            phantram: totalEvaluated ? Math.round((countDat / totalEvaluated) * 100) : 0
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
        if (!this.state.selectedDay || this.state.selectedDay.isFuture) return;
        this.state.selectedDay.trangthaiValue = statusValue;
    }

    async saveInlineData() {
        if (this.props.readonly || this.state.selectedDay.isFuture) return;
        const day = this.state.selectedDay;
        const commentElem = document.getElementById("matrix_quick_desc");
        const nextStatus = day.trangthaiValue;
        const nextComment = commentElem.value.trim();

        try {
            if (day.resId) {
                await this.orm.write("ekids.kehoach_ketqua2muctieu", [day.resId], {
                    trangthai: nextStatus,
                    desc: nextComment
                });

                this.notification.add(`Đã lưu nhật ký Ngày thứ ${day.dayNum}`, { type: "success" });
                this.state.selectedDay = null;
                await this.buildKehoachKetQua2MucTieu();
            }
        } catch (error) {
            console.error(error);
        }
    }
}

registry.category("fields").add("ekids_canthiep_ketqua", {
    component: CanThiepKetQuaWidget,
    supportedTypes: ["one2many"],
});