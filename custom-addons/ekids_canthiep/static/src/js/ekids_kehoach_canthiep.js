/** @odoo-module **/
// 🌟 ĐÃ CẢI TIẾN: Import thêm thẻ "xml" của OWL để viết giao diện trực tiếp trong JS
import { Component, useState, onWillStart, useRef, onMounted, onWillUpdateProps, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Sub-Component chuyên trách render Rich Text với template INLINE (Tuyệt đối không lo thiếu template)
class HtmlContent extends Component {
    // 🌟 KHẮC PHỤC LỖI CHÍ MẠNG: Khai báo giao diện trực tiếp tại đây, Odoo sẽ nạp tức thì
    static template = xml`
        <div class="text-muted text-justify clinical-desc-p" style="line-height:1.6; font-size: 0.95rem;" t-ref="htmlRoot"/>
    `;

    setup() {
        const rootRef = useRef("htmlRoot");

        const renderHtml = (props) => {
            if (rootRef.el) {
                let rawHtml = props.value || "";
                // Tự động giải mã nếu chuỗi bị dính thực thể mã hóa thô (&lt;p&gt;)
                if (typeof rawHtml === 'string' && (rawHtml.includes("&lt;") || rawHtml.includes("&gt;") || rawHtml.includes("&amp;"))) {
                    const doc = new DOMParser().parseFromString(rawHtml, "text/html");
                    rawHtml = doc.documentElement.textContent || "";
                }
                // Ép trình duyệt thực thi chạy định dạng format HTML giàu thuộc tính
                rootRef.el.innerHTML = rawHtml;
            }
        };

        onMounted(() => renderHtml(this.props));
        onWillUpdateProps((nextProps) => renderHtml(nextProps));
    }
}

export class KeHoachCanthiepComponent extends Component {
    static template = "ekids_canthiep.kehoach_canthiep";

    // Đăng ký Sub-Component vào bộ nạp của màn hình chính
    static components = { HtmlContent };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        this.state = useState({
            kehoach: {},
            linhvucs: [],
            expandedGoals: {},
            collapsedDomains: {},
            show_header_detail: false,

        });

        onWillStart(async () => {
            await this._loadData();
        });
    }

    toggleDomain(domainId, ev) {
        ev.stopPropagation();
        this.state.collapsedDomains[domainId] = !this.state.collapsedDomains[domainId];
    }

    async _loadData() {
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


    async goiMucTieuAction(tenAction,muctieu_id,ev) {
        ev.stopPropagation();
        if (!muctieu_id) return;

        try {

            const actionWindow = await this.orm.call("ekids.kehoach_muctieu", tenAction, [muctieu_id]);
            if (actionWindow) {
                await this.actionService.doAction(actionWindow);
            }
        } catch (error) {
            console.error(`Lỗi khi thực thi hàm ${tenAction} từ hệ thống:`, error);
        }
    }

    async goiKeHoachAction(tenAction, ev) {
        ev.stopPropagation();
        const kehoach_id = this.props.action.context.kehoach_id || this.props.action.context.active_id;
        if (!kehoach_id) return;

        try {
            const actionWindow = await this.orm.call("ekids.kehoach", tenAction, [kehoach_id]);
            if (actionWindow) {
                await this.actionService.doAction(actionWindow);
            }
        } catch (error) {
            console.error(`Lỗi khi thực thi hàm ${tenAction} từ hệ thống:`, error);
        }
    }

    async goiGuiDuyetKeHoachAction(tenAction, ev) {
        ev.stopPropagation();
        const hoanthanh = confirm("Bạn chắc chắc muốn kết thúc [Gửi duyệt kết quả] kế hoạch này ?");
        if (hoanthanh) {
            const kehoach_id = this.props.action.context.kehoach_id || this.props.action.context.active_id;
            if (!kehoach_id) return;

            try {
                const actionWindow = await this.orm.call("ekids.kehoach", tenAction, [kehoach_id]);
                if (actionWindow) {
                    await this.actionService.doAction(actionWindow);
                }
            } catch (error) {
                console.error(`Lỗi khi thực thi hàm ${tenAction} từ hệ thống:`, error);
            }

        }

    }
}

registry.category("actions").add("ekids_canthiep.kehoach_canthiep_action", KeHoachCanthiepComponent);