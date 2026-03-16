/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const actionRegistry = registry.category("actions");

actionRegistry.add("reload_chamcong_jsless", async (env, action) => {
    const actionService = env.services.action;
    const { record_id, ngay_field, giatri } = action.params || {};
    if (record_id && ngay_field && giatri) {
        console.log("B1: Vao")
        let divs = document.getElementsByName(ngay_field);
        let html = "";
        console.log("B2: Vao Div")
        switch (giatri) {
            case "1":
                html = "<span><i style='font-size:20px;' class='fa fa-check-circle text-success'></i></span>"; // đi học
                break;
             case "10":
                html = "<span><i style='font-size:20px;' class='fa fa-check-circle text-info'></i></span>"; // đi học
                break;

            case "-1":
                html = "<span><i style='font-size:20px;' class='fa fa-times-circle text-danger'></i></span>"; // vắng
                break;
            case "0":
                html = "<span><i style='font-size:20px;' class='fa fa-adjust text-warning'></i></span>"; // nửa buổi
                break;

        }
        //alert(html)

        const selector = 'span[data-record_id="' + record_id + '"][name="' + ngay_field + '"]';
        const cell = document.querySelector(selector);
        //alert(cell)
        if (cell) {

            cell.innerHTML = html;
             // ✅ Đóng popup hiện tại
            actionService.doAction({ type: "ir.actions.act_window_close" });

            return Promise.resolve();
        }
    }
    return Promise.resolve();
});
