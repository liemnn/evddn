/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class PlanManagerWidget extends Component {
    static template = "ekids_canthiep.PlanManagerTemplate";
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
        });

        onWillStart(async () => {
            await this.loadAllPlanData();
        });
    }

    async loadAllPlanData() {
        const kehoachId = this.props.record.resId;
        if (!kehoachId) return;

        try {
            const linhVucLines = await this.orm.searchRead(
                "ekids.kehoach_linhvuc",
                [["kehoach_id", "=", kehoachId]],
                ["id", "linhvuc_id", "tuoi_id", "chuongtrinh_id"]
            );

            if (!linhVucLines.length) {
                this.state.groupedData = [];
                return;
            }

            const linhVucLineIds = linhVucLines.map(line => line.id);

            const allTargets = await this.orm.searchRead(
                "ekids.kehoach_muctieu",
                [["kehoach_linhvuc_id", "in", linhVucLineIds]],
                ["id", "muctieu_id", "ghichu", "kehoach_muctieu_thangtruoc_id", "kehoach_linhvuc_id", "tieuchi_chuadat", "tieuchi_hinhthanh", "tieuchi_dat"],
                { order: "id asc" }
            );

            this.state.groupedData = linhVucLines.map(line => {
                const targetsOfLine = allTargets.filter(t => t.kehoach_linhvuc_id[0] === line.id);

                // XỬ LÝ MẤU CHỐT: Lọc sạch thẻ <p> hoặc tag HTML còn sót lại dưới DB trước khi render lên textarea
                targetsOfLine.forEach(t => {
                    if (t.ghichu) {
                        t.ghichu_clean = t.ghichu.replace(/<[^>]*>/g, '').replace(/&lt;[^&gt;]*&gt;/g, '').trim();
                    } else {
                        t.ghichu_clean = '';
                    }
                });

                if (this.state.collapsedLinhVuc[line.id] === undefined) {
                    this.state.collapsedLinhVuc[line.id] = false;
                }

                return {
                    lineId: line.id,
                    linhVucName: line.linhvuc_id ? line.linhvuc_id[1] : "",
                    tuoiName: line.tuoi_id ? line.tuoi_id[1] : "",
                    chuongTrinhCode: line.chuongtrinh_id ? line.chuongtrinh_id[1] : "",
                    total: targetsOfLine.length,
                    targets: targetsOfLine
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
                    onClose: async () => { await this.loadAllPlanData(); }
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
            const textarea = event.target.closest('.inline-note-box').querySelector('.note-textarea');
            let newNote = textarea.value;

            // XỬ LÝ: Dùng RegEx quét sạch sẽ mọi thẻ phát sinh ngoài ý muốn trước khi ghi nhận xuống database thuần Text
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
}

registry.category("fields").add("ekids_lap_kehoach", {
    component: PlanManagerWidget,
    supportedTypes: ["one2many"],
});