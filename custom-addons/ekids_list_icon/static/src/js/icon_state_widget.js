/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class AttendanceIconWidget extends Component {
    setup() {
        this.action = useService("action");
    }

    getIconClass() {
        const value = this.props.record.data[this.props.name];
        switch (value) {
            case "X": return "fa fa-check-circle text-success";   // đi học
            case "O": return "fa fa-times-circle text-danger";   // nghỉ
            case "A": return "fa fa-adjust text-warning";        // nửa buổi
            default: return "fa fa-question-circle text-muted";
        }
    }

    getLabel() {
        const labels = { X: "Đi học", O: "Nghỉ", A: "Đi nửa buổi" };
        return labels[this.props.record.data[this.props.name]] || "Chưa chọn";
    }

    openPopup() {
        const value = this.props.record.data[this.props.name];
        const recordId = this.props.record.resId;
        console.log("value:", value, "id:", recordId);
        alert("value:"+value+",id:"+recordId)

        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Attendance Logs",
            res_model: "res.users",
            views: [[false, "list"], [false, "form"]],  // 👈 dùng "tree" thay vì "list"
            target: "new",  // 👈 mở popup, không thay thế list model.a
        });
    }

    static template = "ekids_list_icon.AttendanceIconWidget";
}


registry.category("fields").add("diemdanh", {
    component: AttendanceIconWidget,
    supportedTypes: ["selection"],  // khai báo rõ ràng
});
