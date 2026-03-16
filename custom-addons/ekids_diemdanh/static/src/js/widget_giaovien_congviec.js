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




getValue() {
    const value = this.props.record.data[this.props.name];
    const floatVal = parseFloat(value) || 0;

    if (floatVal === 0) {
        // Hiển thị icon nếu bằng 0
        return floatVal
    } else {
        // Hiển thị số màu xanh
        return value
    }
}



    getLabel() {
        const labels = {
         "0": "Không thực hiện",
         "1": "Đạt được kết quả",

         };
        return labels[this.props.record.data[this.props.name]] || "Chưa chọn";
    }

    openPopup() {
        // 👇 lấy id bản ghi hiện tại
        const recordId = this.props.record.resId;
        const fieldName = this.props.name;
        const fieldValue = this.props.record.data[fieldName];


        this.orm.call(
            "ekids.chamcong_congviec2thang_giatri",
            "action_mo_popup_chamcong_congviec2ngay_giatri",
            [recordId],                        // chỉ truyền id làm positional
            { record_id:recordId,field_name: fieldName, field_value: fieldValue }  // truyền theo tên
        ).then((action) => {
            this.action.doAction(action);

        });

    }


    static template = "ekids_diemdanh.GiaoViecWidget";
}


registry.category("fields").add("widget_giaovien_giaoviec", {
    component: DiemDanhWidget,
    supportedTypes: ["selection"],  // khai báo rõ ràng
});
