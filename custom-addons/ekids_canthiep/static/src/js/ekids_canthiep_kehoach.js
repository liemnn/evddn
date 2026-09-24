/** @odoo-module **/

import { Component, useState, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CanThiepKehoachWidget extends Component {
    static template = "ekids_canthiep.CanThiepKeHoachWidgetTemplate";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.actionService = useService("action");

        this.state = useState({
            groupedData: [],
            activeNotes: {},
            collapsedLinhVuc: {},
            expandedTargets: {},
            hasAnyTargetDone: false,
        });

        onWillStart(async () => {
            await this.loadAllPlanData();
        });
    }

    decodeHtmlText(htmlTrack) {
        if (!htmlTrack) return "";
        let decoded = htmlTrack
            .replace(/&amp;lt;/g, "<")
            .replace(/&amp;gt;/g, ">")
            .replace(/&lt;/g, "<")
            .replace(/&gt;/g, ">")
            .replace(/&amp;/g, "&")
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");

        try {
            const parser = new DOMParser();
            const dom = parser.parseFromString(decoded, "text/html");
            return dom.body.innerHTML || decoded;
        } catch (e) {
            return decoded;
        }
    }

    /* 🌟 Hàm kiểm tra chuỗi có nội dung thực tế hay không */
    hasValidContent(text) {
        if (!text) return false;
        const decoded = this.decodeHtmlText(text);
        const clean = decoded.replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").trim();
        return clean.length > 0 && clean !== "Không có";
    }

    async loadAllPlanData() {
        const kehoachId = this.props.record.resId;
        if (!kehoachId) return;

        try {
            const linhVucLines = await this.orm.searchRead(
                "ekids.kehoach_linhvuc",
                [["kehoach_id", "=", kehoachId]],
                ["id", "linhvuc_id", "tuoi_id", "chuongtrinh_id", "tong_muctieu_dat"]
            );

            if (!linhVucLines.length) {
                this.state.groupedData = [];
                this.state.hasAnyTargetDone = false;
                return;
            }

            const linhVucLineIds = linhVucLines.map((line) => line.id);

            const muctieus_returns = await this.orm.searchRead(
                "ekids.kehoach_muctieu",
                [["kehoach_linhvuc_id", "in", linhVucLineIds]],
                [
                    "id", "index", "name", "muctieu_id", "muctieu_them", "ghichu",
                    "kehoach_muctieu_thangtruoc_id", "sothang_da_chuyenttiep", "kehoach_linhvuc_id",
                    "chucnang", "thietke", "tieuchi_chuadat", "tieuchi_hinhthanh", "tieuchi_dat",
                    "trangthai", "trangthai_kiemduyet", "is_readonly", "is_canthiep", "is_kiemduyet",
                    "ketqua_dat_lientiep_thangtruoc", "ketqua_hinhthanh_thangtruoc",
                    "solan_thu", "solan_thu_dat", "tyle_thu", "tyle_canthiep", "tyle_kiemduyet"
                ],
                { order: "sequence asc, id asc" }
            );

            this.state.hasAnyTargetDone = muctieus_returns.some((t) => t.trangthai === "1");

            this.state.groupedData = linhVucLines.map((line) => {
                const muctieus = muctieus_returns.filter((t) => t.kehoach_linhvuc_id[0] === line.id);

                muctieus.forEach((t) => {
                    // Kiểm tra cờ dữ liệu thực tế
                    t.has_chucnang = this.hasValidContent(t.chucnang);
                    t.has_thietke = this.hasValidContent(t.thietke);
                    t.has_tc1 = this.hasValidContent(t.tieuchi_chuadat);
                    t.has_tc2 = this.hasValidContent(t.tieuchi_hinhthanh);
                    t.has_tc3 = this.hasValidContent(t.tieuchi_dat);
                    t.has_tieuchi = t.has_tc1 || t.has_tc2 || t.has_tc3;

                    // Chỉ gán markup khi thực sự có nội dung
                    t.chucnang = t.has_chucnang ? markup(this.decodeHtmlText(t.chucnang)) : "";
                    t.thietke = t.has_thietke ? markup(this.decodeHtmlText(t.thietke)) : "";
                    t.tieuchi_chuadat = t.has_tc1 ? markup(this.decodeHtmlText(t.tieuchi_chuadat)) : "";
                    t.tieuchi_hinhthanh = t.has_tc2 ? markup(this.decodeHtmlText(t.tieuchi_hinhthanh)) : "";
                    t.tieuchi_dat = t.has_tc3 ? markup(this.decodeHtmlText(t.tieuchi_dat)) : "";

                    if (t.ghichu) {
                        t.ghichu_clean = this.decodeHtmlText(t.ghichu).replace(/<[^>]*>/g, "").trim();
                    } else {
                        t.ghichu_clean = "";
                    }
                });

                if (this.state.collapsedLinhVuc[line.id] === undefined) {
                    this.state.collapsedLinhVuc[line.id] = false;
                }

                return {
                    kehoach_linhvuc_id: line.id,
                    linhvuc: line.linhvuc_id ? line.linhvuc_id[1] : "",
                    tuoi: line.tuoi_id ? line.tuoi_id[1] : "",
                    chuongtrinh: line.chuongtrinh_id ? line.chuongtrinh_id[1] : "",
                    tong_muctieu: muctieus.length,
                    tong_muctieu_dat: line.tong_muctieu_dat,
                    muctieus: muctieus,
                };
            });

        } catch (error) {
            console.error("Lỗi đồng bộ cấu trúc dữ liệu phẳng:", error);
        }
    }

    toggleLinhVucCollapse(lineId) {
        this.state.collapsedLinhVuc[lineId] = !this.state.collapsedLinhVuc[lineId];
    }

    toggleTargetDetail(targetId) {
        this.state.expandedTargets[targetId] = !this.state.expandedTargets[targetId];
    }

    async openAddTargetWizard(lineId) {
        try {
            const action = await this.orm.call("ekids.kehoach_linhvuc", "action_xem_danhsach_ct_muctieu", [lineId]);
            if (action) {
                this.actionService.doAction(action, {
                    onClose: async () => { await this.loadAllPlanData(); },
                });
            }
        } catch (error) {
            console.error(error);
        }
    }

    toggleNoteInline(targetId) {
        this.state.activeNotes[targetId] = !this.state.activeNotes[targetId];
        if (this.state.activeNotes[targetId]) {
            this.state.expandedTargets[targetId] = true;
        }
    }

    async saveNoteInline(target, event) {
        try {
            const textarea = event.target.closest(".inline-note-box").querySelector(".note-textarea");
            let newNote = textarea.value;

            if (newNote) {
                newNote = newNote.replace(/<\/?[^>]+(>|$)/g, "").trim();
            }

            await this.orm.write("ekids.kehoach_muctieu", [target.id], { ghichu: newNote });

            target.ghichu = newNote;
            target.ghichu_clean = newNote;

            this.state.activeNotes[target.id] = false;
            this.notification.add("Đã cập nhật nhật ký tiến độ mục tiêu thô sạch!", { type: "success" });

            await this.loadAllPlanData();
        } catch (error) {
            console.error(error);
        }
    }

    async removeTargetFromPlan(targetId) {
        if (confirm("Bạn có chắc chắn muốn bỏ chọn mục tiêu này khỏi kế hoạch không?")) {
            try {
                await this.orm.unlink("ekids.kehoach_muctieu", [targetId]);
                this.notification.add("Đã gỡ mục tiêu.", { type: "info" });
                await this.loadAllPlanData();
            } catch (error) {
                console.error(error);
            }
        }
    }

    async onCanThiepClick(muctieu, event) {
        if (muctieu.trangthai !== "0") {
            try {
                const action = await this.orm.call("ekids.kehoach_muctieu", "action_canthiep", [muctieu.id]);
                if (action) {
                    this.actionService.doAction(action, {
                        onClose: async () => { await this.loadAllPlanData(); },
                    });
                }
            } catch (error) {
                console.error("Lỗi thực thi Action Can Thiệp:", error);
            }
        } else {
            alert("Kế hoạch chưa thể can thiệp !");
        }
    }

    async onMucTieuClick(muctieu, actionName, event) {
        if (muctieu.trangthai !== "0") {
            try {
                const action = await this.orm.call("ekids.kehoach_muctieu", actionName, [muctieu.id]);
                if (action) {
                    this.actionService.doAction(action, {
                        onClose: async () => { await this.loadAllPlanData(); },
                    });
                }
            } catch (error) {
                console.error("Lỗi thực thi Action Can Thiệp:", error);
            }
        } else {
            alert("Kế hoạch chưa thể can thiệp !");
        }
    }
}

registry.category("fields").add("ekids_canthiep_kehoach", {
    component: CanThiepKehoachWidget,
    supportedTypes: ["one2many"],
});