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
            summary: { total: 0, dat: 0, hinhthanh: 0, chuadat: 0, totalEvaluated: 0, phantram: 0 }
        });

        this.dayTypesMap = {};

        onWillStart(async () => { await this.buildKehoachKetQua2MucTieu(); });
        onWillUpdateProps(async () => { await this.buildKehoachKetQua2MucTieu(); });
    }

    _extractPlainText(htmlString) {
        if (!htmlString) return "";
        try {
            const doc = new DOMParser().parseFromString(htmlString, 'text/html');
            return doc.body.textContent || doc.body.innerText || "";
        } catch (e) {
            return String(htmlString).replace(/<[^>]*>/g, "");
        }
    }

    _formatDateISO(d) {
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    _parseDateObj(dateVal) {
        if (!dateVal) return null;
        let str = "";
        if (typeof dateVal === 'object' && dateVal.toISODate) {
            str = dateVal.toISODate();
        } else {
            str = String(dateVal).split(' ')[0];
        }
        const parts = str.split('-');
        if (parts.length === 3) {
            const y = parseInt(parts[0], 10);
            const m = parseInt(parts[1], 10) - 1;
            const d = parseInt(parts[2], 10);
            return new Date(y, m, d);
        }
        return null;
    }

    async _getPlanDateRange() {
        const parentData = this.props.record.data;
        let tuNgayRaw = parentData.tu_ngay;
        let denNgayRaw = parentData.den_ngay;
        let soNgay = parentData.songay;

        if (!tuNgayRaw) {
            let kehoachId = null;

            if (parentData.kehoach_id) {
                kehoachId = Array.isArray(parentData.kehoach_id) ? parentData.kehoach_id[0] : parentData.kehoach_id;
            } else if (parentData.kehoach_linhvuc_id) {
                const lvId = Array.isArray(parentData.kehoach_linhvuc_id) ? parentData.kehoach_linhvuc_id[0] : parentData.kehoach_linhvuc_id;
                try {
                    const [lv] = await this.orm.read("ekids.kehoach_linhvuc", [lvId], ["kehoach_id"]);
                    if (lv && lv.kehoach_id) {
                        kehoachId = Array.isArray(lv.kehoach_id) ? lv.kehoach_id[0] : lv.kehoach_id;
                    }
                } catch (e) {
                    console.warn(e);
                }
            }

            if (!kehoachId && this.props.record.resId) {
                try {
                    const [mt] = await this.orm.read("ekids.kehoach_muctieu", [this.props.record.resId], ["kehoach_linhvuc_id"]);
                    if (mt && mt.kehoach_linhvuc_id) {
                        const lvId = Array.isArray(mt.kehoach_linhvuc_id) ? mt.kehoach_linhvuc_id[0] : mt.kehoach_linhvuc_id;
                        const [lv] = await this.orm.read("ekids.kehoach_linhvuc", [lvId], ["kehoach_id"]);
                        if (lv && lv.kehoach_id) {
                            kehoachId = Array.isArray(lv.kehoach_id) ? lv.kehoach_id[0] : lv.kehoach_id;
                        }
                    }
                } catch (e) {
                    console.warn(e);
                }
            }

            if (kehoachId) {
                try {
                    const [kh] = await this.orm.read("ekids.kehoach", [kehoachId], ["tu_ngay", "den_ngay", "songay"]);
                    if (kh) {
                        tuNgayRaw = kh.tu_ngay;
                        denNgayRaw = kh.den_ngay;
                        soNgay = kh.songay;
                    }
                } catch (e) {
                    console.warn(e);
                }
            }
        }

        let startDate = this._parseDateObj(tuNgayRaw);
        let endDate = this._parseDateObj(denNgayRaw);

        if (!startDate) {
            const today = new Date();
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        }
        if (!endDate) {
            endDate = new Date(startDate);
            const totalD = parseInt(soNgay, 10) || 30;
            endDate.setDate(startDate.getDate() + totalD - 1);
        }

        return { startDate, endDate };
    }

    async buildKehoachKetQua2MucTieu() {
        const ketqua2muctieu = this.props.record.data[this.props.name]?.records || [];
        const { startDate, endDate } = await this._getPlanDateRange();

        if (this.props.record.resId && Object.keys(this.dayTypesMap).length === 0) {
            try {
                this.dayTypesMap = await this.orm.call(
                    "ekids.kehoach_muctieu",
                    "func_get_thongtin_nghiles_cungcap_ketqua2ngay",
                    [this.props.record.resId]
                ) || {};
            } catch (err) {
                console.warn("Không thể tải thông tin ngày nghỉ lễ từ hệ thống:", err);
            }
        }

        const recordMap = new Map();
        ketqua2muctieu.forEach(rec => {
            const rawNgay = rec.data.ngay;
            if (rawNgay) {
                const dateKey = typeof rawNgay === 'object' && rawNgay.toISODate ? rawNgay.toISODate() : String(rawNgay).split(' ')[0];
                recordMap.set(dateKey, rec);
            }
        });

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const todayStr = this._formatDateISO(today);

        const defaultSolanThu = Number(this.props.record.data.solan_thu) > 0 ? Number(this.props.record.data.solan_thu) : 10;

        let tempGrid = [];
        let countDat = 0, countHinhThanh = 0, countChuaDat = 0;
        let dayCounter = 1;

        let cur = new Date(startDate);
        while (cur <= endDate) {
            const curStr = this._formatDateISO(cur);
            const isSunday = cur.getDay() === 0;
            const isFuture = cur > today;
            const isToday = curStr === todayStr;

            let isDateStatus = isFuture ? "1" : (isToday ? "0" : "-1");

            const parts = curStr.split('-');
            const dateShortStr = `${parts[2]}/${parts[1]}`;
            const dateDisplayStr = `${parts[2]}/${parts[1]}/${parts[0]}`;

            let loaiFromBackend = this.dayTypesMap[curStr];
            let defaultLoai = loaiFromBackend || (isSunday ? "-1" : (isFuture ? "0" : "1"));

            const existRec = recordMap.get(curStr);

            if (existRec) {
                const rawStatusValue = existRec.data.trangthai || "0";
                const rawLoaiValue = existRec.data.loai || defaultLoai;

                if (rawLoaiValue === "1") {
                    if (rawStatusValue === "1") countDat++;
                    else if (rawStatusValue === "-1") countChuaDat++;
                    else if (rawStatusValue === "2") countHinhThanh++;
                }

                const solanThu = Number(existRec.data.solan_thu) > 0 ? Number(existRec.data.solan_thu) : defaultSolanThu;
                let solanThuDat = (existRec.data.solan_thu_dat !== undefined && existRec.data.solan_thu_dat !== false) ? Number(existRec.data.solan_thu_dat) : 0;
                if (solanThuDat > solanThu) solanThuDat = solanThu;
                if (solanThuDat < 0) solanThuDat = 0;

                let tyleThu = 0;
                if (existRec.data.tyle_thu !== undefined && existRec.data.tyle_thu !== false && rawStatusValue !== '0') {
                    tyleThu = Math.min(Number(existRec.data.tyle_thu), 100);
                } else if (solanThu > 0 && rawStatusValue !== '0') {
                    tyleThu = Math.min(Math.round((solanThuDat / solanThu) * 100), 100);
                }

                tempGrid.push({
                    dayNum: dayCounter,
                    resId: existRec.resId,
                    rawRecord: existRec,
                    dateIso: curStr,
                    trangthaiValue: rawStatusValue,
                    loai: rawLoaiValue,
                    is_date_status: existRec.data.is_date_status || isDateStatus,
                    solan_thu: solanThu,
                    solan_thu_dat: solanThuDat,
                    tyle_thu: tyleThu,
                    comment: this._extractPlainText(existRec.data.desc),
                    dateDisplayStr: dateDisplayStr,
                    dateShortStr: dateShortStr,
                    tooltipText: rawLoaiValue === "-1" ? `${curStr} (Nghỉ)` : curStr
                });
            } else {
                tempGrid.push({
                    dayNum: dayCounter,
                    resId: null,
                    rawRecord: null,
                    dateIso: curStr,
                    trangthaiValue: "0",
                    loai: defaultLoai,
                    is_date_status: isDateStatus,
                    solan_thu: defaultSolanThu,
                    solan_thu_dat: 0,
                    tyle_thu: 0,
                    comment: "",
                    dateDisplayStr: dateDisplayStr,
                    dateShortStr: dateShortStr,
                    tooltipText: defaultLoai === "-1" ? `${curStr} (Nghỉ)` : curStr
                });
            }

            cur.setDate(cur.getDate() + 1);
            dayCounter++;
        }

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
        if (day.loai === "1" && day.trangthaiValue === "0") {
            this._recalculateDayMetrics(0);
        }
    }

    _recalculateDayMetrics(rawVal, showWarning = false) {
        const day = this.state.selectedDay;
        if (!day || day.loai !== "1") return 0;

        const maxTrials = Number(day.solan_thu) > 0 ? Number(day.solan_thu) : 10;
        let val = parseInt(rawVal, 10);

        if (isNaN(val) || val < 0) {
            val = 0;
        }
        if (val > maxTrials) {
            if (showWarning) {
                this.notification.add(
                    `Số lần đạt tối đa là ${maxTrials}/${maxTrials} lần (100%)!`,
                    { type: "warning" }
                );
            }
            val = maxTrials;
        }

        day.solan_thu_dat = val;
        day.tyle_thu = maxTrials > 0 ? Math.min(Math.round((val / maxTrials) * 100), 100) : 0;

        if (day.tyle_thu >= 80) {
            day.trangthaiValue = "1";
        } else if (day.tyle_thu > 0) {
            day.trangthaiValue = "2";
        } else {
            day.trangthaiValue = "-1";
        }
        return val;
    }

    adjustSolanThuDat(delta) {
        const day = this.state.selectedDay;
        if (!day || day.loai !== "1") return;
        const current = Number(day.solan_thu_dat) || 0;
        this._recalculateDayMetrics(current + delta, false);
    }

    setQuickTrialRatio(ratio) {
        const day = this.state.selectedDay;
        if (!day || day.loai !== "1") return;
        const maxTrials = Number(day.solan_thu) > 0 ? Number(day.solan_thu) : 10;
        const targetVal = Math.ceil(maxTrials * ratio);
        this._recalculateDayMetrics(targetVal, false);
    }

    onKeydownSolanThuDat(ev) {
        if (["e", "E", "+", "-", ".", ","].includes(ev.key)) {
            ev.preventDefault();
        }
    }

    onInputSolanThuDat(ev) {
        const day = this.state.selectedDay;
        if (!day || day.loai !== "1") return;

        const digitsOnly = String(ev.target.value || "").replace(/\D+/g, "");
        if (digitsOnly === "") {
            ev.target.value = "";
            this._recalculateDayMetrics(0, false);
            return;
        }

        const clampedVal = this._recalculateDayMetrics(digitsOnly, true);
        ev.target.value = String(clampedVal);
    }

    onBlurSolanThuDat(ev) {
        const day = this.state.selectedDay;
        if (!day || day.loai !== "1") return;
        const clampedVal = this._recalculateDayMetrics(ev.target.value, false);
        ev.target.value = String(clampedVal);
    }

    navigateStudyDay(direction) {
        if (!this.state.selectedDay) return;
        const studyDays = this.state.daysGrid.filter(d => d.loai === "1");
        const curIdx = studyDays.findIndex(d => d.dayNum === this.state.selectedDay.dayNum);
        if (curIdx === -1) return;

        const targetIdx = curIdx + direction;
        if (targetIdx >= 0 && targetIdx < studyDays.length) {
            this.onDayClick(studyDays[targetIdx]);
        } else {
            this.notification.add(
                direction > 0 ? "Đã đến ngày học cuối cùng có thể nhập!" : "Đang ở ngày học đầu tiên của kế hoạch!",
                { type: "info" }
            );
        }
    }

    async saveInlineData(goNextDay = false) {
        if (this.props.readonly || !this.state.selectedDay || this.state.selectedDay.loai !== "1") return;
        const day = this.state.selectedDay;
        const currentDayNum = day.dayNum;

        const commentElem = document.getElementById("matrix_quick_desc");
        const nextComment = commentElem ? commentElem.value.trim() : "";

        const maxTrials = Number(day.solan_thu) > 0 ? Number(day.solan_thu) : 10;
        let solanThuDat = (day.solan_thu_dat !== undefined && day.solan_thu_dat !== null) ? Number(day.solan_thu_dat) : 0;

        if (isNaN(solanThuDat) || solanThuDat < 0) solanThuDat = 0;
        if (solanThuDat > maxTrials) {
            this.notification.add(`Dữ liệu không hợp lệ: Số lần đạt (${solanThuDat}) không được vượt quá ${maxTrials}!`, { type: "danger" });
            return;
        }

        const tyleThuCalc = maxTrials > 0 ? Math.min(Math.round((solanThuDat / maxTrials) * 100), 100) : 0;

        let nextStatus = day.trangthaiValue;
        if (!nextStatus || nextStatus === "0") {
            nextStatus = tyleThuCalc >= 80 ? "1" : (solanThuDat > 0 ? "2" : "-1");
            day.trangthaiValue = nextStatus;
        }

        const targetMuctieuId = this.props.record.resId;

        try {
            if (day.resId) {
                await this.orm.write("ekids.kehoach_ketqua2muctieu", [day.resId], {
                    trangthai: nextStatus,
                    desc: nextComment,
                    solan_thu_dat: solanThuDat,
                    tyle_thu: tyleThuCalc,
                    is_giaovien_capnhat: true,
                });
            } else {
                const [newId] = await this.orm.create("ekids.kehoach_ketqua2muctieu", [{
                    kehoach_muctieu_id: targetMuctieuId,
                    ngay: day.dateIso,
                    trangthai: nextStatus,
                    desc: nextComment,
                    solan_thu_dat: solanThuDat,
                    tyle_thu: tyleThuCalc,
                    is_giaovien_capnhat: true,
                }]);
                day.resId = newId;
            }

            this.notification.add(`Đã lưu nhật ký ngày ${day.dateDisplayStr} (${solanThuDat}/${maxTrials} - ${tyleThuCalc}%)`, { type: "success" });

            if (this.props.record && this.props.record.load) {
                await this.props.record.load();
            }
            await this.buildKehoachKetQua2MucTieu();

            if (goNextDay) {
                const studyDays = this.state.daysGrid.filter(d => d.loai === "1");
                const nextStudyDay = studyDays.find(d => d.dayNum > currentDayNum);
                if (nextStudyDay) {
                    this.onDayClick(nextStudyDay);
                } else {
                    this.state.selectedDay = null;
                    this.notification.add("Đã hoàn thành nhập đến ngày học cuối cùng!", { type: "info" });
                }
            } else {
                this.state.selectedDay = null;
            }
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