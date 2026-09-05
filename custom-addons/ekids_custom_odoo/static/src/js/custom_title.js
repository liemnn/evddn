/** @odoo-module **/
import { WebClient } from "@web/webclient/webclient";
import { registry } from "@web/core/registry";

class CustomWebClient extends WebClient {
    setup() {
        super.setup();
        document.title = "eVDDN - Hệ thống quản lý Trường/Cơ sở mầm non chuyên biệt";
    }
}

registry.category("web_client").add("CustomWebClient", CustomWebClient, { sequence: 1 });
