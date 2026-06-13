/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class KeHoachCanthiepComponent extends Component {
    static template = "ekids_canthiep.kehoach_canthiep";

    setup() {
        this.orm = useService("orm");

        // 🌟 SỬA LỖI 1: Khai báo action Service của Odoo 18 để thực thi được hàm doAction
        this.actionService = useService("action");

        this.state = useState({
            kehoach: {},
            linhvucs: [],
            expandedGoals: {},
            collapsedDomains: {},
        });

        onWillStart(async () => {
            await this._loadData();
        });
    }

    // Đảo ngược trạng thái Ẩn/Hiện của khối Lĩnh vực khi giáo viên click
    toggleDomain(domainId, ev) {
        ev.stopPropagation();
        this.state.collapsedDomains[domainId] = !this.state.collapsedDomains[domainId];
    }

    async _loadData() {
        // Phòng hờ kiểm tra cả 2 khóa ID trong context để tránh rỗng dữ liệu đầu vào
        const planId = this.props.action.context.active_id || this.props.action.context.kehoach_id;
        const result = await this.orm.call("ekids.hocsinh", "get_owl_canthiep_data", [planId]);
        if (result && result.status === "success") {
            this.state.kehoach = result.kehoach;
            this.state.linhvucs = result.linhvucs;
        }
    }

    toggleGoalDetails(goalId, ev) {
        ev.stopPropagation();
        this.state.expandedGoals[goalId] = !this.state.expandedGoals[goalId];
    }

    async actionGhiNhanKetQua(goalId, ev) {
        ev.stopPropagation();
        alert("Ghi nhận kết quả cho mục tiêu ID: " + goalId);
    }

    // 🌟 BỔ SUNG: Hàm đóng màn hình quay lại nếu XML của anh có gọi nút actionQuayLai
    actionQuayLai(ev) {
        ev.stopPropagation();
        this.actionService.doAction({ type: "ir.actions.act_window_close" });
    }

    // Hàm gọi chung các Action từ model Python
    async goiKeHoachAction(tenAction, ev) {
        ev.stopPropagation();

        // 🌟 TỐI ƯU: Lấy linh hoạt giữa kehoach_id hoặc active_id để không bị rỗng ID khi chạy
        const kehoach_id = this.props.action.context.kehoach_id || this.props.action.context.active_id;
        console.log("Kehoach_id =========", kehoach_id);

        if (!kehoach_id) {
            console.warn("Không tìm thấy ID Kế hoạch trong context hành động!");
            return;
        }

        try {
            // 🌟 SỬA LỖI 2: Vá lỗi chuỗi nháy kép Python thành chuỗi JavaScript hợp lệ
            console.log("Bắt đầu gọi hành động: " + tenAction);

            // Truyền động tên hàm Python được gửi từ XML vào tầng ORM
            const actionWindow = await this.orm.call("ekids.kehoach", tenAction, [kehoach_id]);
            if (actionWindow) {
                // Thực thi trả giao diện về WebClient Odoo 18
                await this.actionService.doAction(actionWindow);
            }
        } catch (error) {
            console.error(`Lỗi khi thực thi hàm ${tenAction} từ hệ thống:`, error);
        }
    }
}

registry.category("actions").add("ekids_canthiep.kehoach_canthiep_action", KeHoachCanthiepComponent);