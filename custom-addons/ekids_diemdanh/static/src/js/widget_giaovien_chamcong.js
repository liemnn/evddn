/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";


class DiemDanhWidget extends Component {
    setup() {
        super.setup();
        this.action = useService("action"); // 👈 lấy service action
        this.orm = useService("orm");   // 👈 dùng orm thay vì rpc
    }

    getIconClass() {
        const value = this.props.record.data[this.props.name];
        switch (value) {
            case "1": return "fa fa-check-circle text-success";   // đi học
            case "10": return "fa fa-check-circle text-warning";   // đi làm muộn
            case "11": return "fa fa-times-circle text-muted";   // không đăng ký đi lam
            case "-1": return "fa fa-times-circle text-danger";   // nghỉ
            case "0": return "fa fa-adjust text-info";        // nửa buổi
            case "00": return "fa fa-adjust text-warning";        // nửa buổi
            case "2": return "fa fa-circle";        // nửa buổi
            case "3": return "fa fa-calendar-minus-o text-danger";        // nửa buổi
            case "4": return "fa fa-calendar-minus-o";        // nửa buổi
            default: return "fa fa-question-circle text-muted";
        }
    }

    getLabel() {
        const labels = {
         "-1": "Nghỉ làm",
         "0": "Đi làm nửa ngày",
         "1": "Đi làm",
         "10": "Đi làm(đi làm muộn)",
         "11": "Không đăng ký đi làm ngày này",
         "2":"Nghỉ lễ",
         '3':"Nhà trường cho nghỉ",
         "4": "Giáo vin nghỉ có phép"
         };
        return labels[this.props.record.data[this.props.name]] || "Chưa chọn";
    }

    openPopup() {
        // 👇 lấy id bản ghi hiện tại
        const recordId = this.props.record.resId;
        const fieldName = this.props.name;
        const fieldValue = this.props.record.data[fieldName];


        this.orm.call(
            "ekids.chamcong_giaovien2thang",
            "action_mo_popup_chamcong_giaovien2thang_ngay",
            [recordId],                        // chỉ truyền id làm positional
            { record_id:recordId,field_name: fieldName, field_value: fieldValue }  // truyền theo tên
        ).then((action) => {
            this.action.doAction(action);

        });

    }


    static template = "ekids_diemdanh.ChamCongWidget";
}


registry.category("fields").add("widget_giaovien_chamcong", {
    component: DiemDanhWidget,
    supportedTypes: ["selection"],  // khai báo rõ ràng
});
