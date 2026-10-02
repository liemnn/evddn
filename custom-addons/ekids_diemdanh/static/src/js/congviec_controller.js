/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const actionRegistry = registry.category("actions");

actionRegistry.add("reload_congviec_jsless", async (env, action) => {
    const actionService = env.services.action;
    const { record_id, ngay_field, giatri,tong_str} = action.params || {};
    if (record_id && ngay_field) {

        let divs = document.getElementsByName(ngay_field);
        let html = "";

        switch (giatri) {
            case "0":
                html = '<i class="fa fa-ban text-muted" title="Không có giá trị"/>'
                break;
            default:
                html = '<span class="fa text-success fw-bold fs-4">'+giatri+'</span>'
                break;

        }
        //alert(html)

        const selector = 'span[data-record_id="' + record_id + '"][name="' + ngay_field + '"]';
        const cell = document.querySelector(selector);
        //alert(cell)
        if (cell) {

            cell.innerHTML = html;
             // ✅ Đóng popup hiện tại
             // cap nhat tong

            const selector_tong_str = 'span[data-record_id="' + record_id + '"][name="tong_str"]';

            const cell_tong_str = document.querySelector(selector_tong_str);

            cell_tong_str.innerHTML ='<span class="fa text-success fw-bold fs-4">'+tong_str+'</span>'

            actionService.doAction({ type: "ir.actions.act_window_close" });

            return Promise.resolve();
        }
    }
    return Promise.resolve();
});
