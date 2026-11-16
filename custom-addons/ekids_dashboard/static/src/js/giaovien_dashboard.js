/** @odoo-module **/

import { Component, useState, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class EkidsGiaovienDashboard extends Component {
    static template = "ekids_dashboard.GiaovienDashboardTemplate";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            loading: true,
            monthStr: "",
            rowFilter: "all", // 'all' | 'pending' | 'done' | 'no_plan'
            data: null,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const res = await this.orm.call(
                "ekids.dashboard_giaovien",
                "get_dashboard_data",
                [],
                { month_str: this.state.monthStr || false }
            );
            this.state.data = res;
            if (res.has_teacher) {
                this.state.monthStr = String(res.selected_month);
            }
        } finally {
            this.state.loading = false;
        }
    }

    async onChangeMonth(ev) {
        this.state.monthStr = ev.target.value;
        await this.loadData();
    }
    async goiActionCoSo(tenHam, thamSoBoSung = {}) {
        const cosoId = parseInt(this.state.centerId || this.state.coso_id, 10);
        if (!cosoId || !tenHam) return;

        const extraContext = {
            active_id: cosoId,
            active_ids: [cosoId],
            active_model: "ekids.coso",
            default_coso_id: cosoId,
            ...thamSoBoSung,
        };

        const actionRes = await this.orm.call(
            "ekids.coso",
            tenHam,
            [[cosoId]],
            { context: extraContext }
        );

        if (!actionRes || typeof actionRes !== "object") return;

        // Bắt buộc chuyển 'view_mode' -> 'views' vì Odoo 18 _preprocessAction gọi action.views.map(...)
        if ((actionRes.type || "ir.actions.act_window") === "ir.actions.act_window") {
            actionRes.type = "ir.actions.act_window";
            if (!Array.isArray(actionRes.views)) {
                const modes = (actionRes.view_mode || "list,form")
                    .split(",")
                    .map((m) => m.trim())
                    .filter(Boolean);
                actionRes.views = modes.map((mode) => [false, mode]);
            }
            if (!Array.isArray(actionRes.domain)) {
                actionRes.domain = [];
            }
            actionRes.context = {
                ...(typeof actionRes.context === "object" && actionRes.context !== null ? actionRes.context : {}),
                ...extraContext,
            };
        }

        await this.action.doAction(actionRes);
    }

    setRowFilter(mode) {
        this.state.rowFilter = mode;
    }

    get filteredRows() {
        if (!this.state.data || !this.state.data.has_teacher) return [];
        const rows = this.state.data.student_rows || [];
        if (this.state.rowFilter === "all") return rows;
        return rows.filter((r) => r.status === this.state.rowFilter);
    }

    getSalaryChartSvg() {
        if (!this.state.data || !this.state.data.has_teacher) return "";
        const { labels, values, tr_labels, full_labels } = this.state.data.salary_chart;
        if (!labels || !labels.length) return "";

        const width = 760, height = 210;
        const pL = 24, pR = 24, pT = 30, pB = 24;
        const w = width - pL - pR, h = height - pT - pB;
        const maxVal = Math.max(...values, 1) * 1.18;
        const step = w / labels.length;
        const barW = Math.min(32, step * 0.48);

        let svg = `<svg viewBox="0 0 ${width} ${height}" style="width:100%;height:auto;display:block;">`;
        for (let i = 0; i <= 3; i++) {
            const y = pT + (h * i) / 3;
            svg += `<line x1="${pL}" y1="${y}" x2="${width - pR}" y2="${y}" stroke="#f1f5f9" stroke-width="1"/>`;
        }
        svg += `<line x1="${pL}" y1="${pT + h}" x2="${width - pR}" y2="${pT + h}" stroke="#94a3b8" stroke-width="1.3"/>`;

        let pts = [];
        labels.forEach((lbl, i) => {
            const cx = pL + step * i + step / 2;
            const bH = (values[i] / maxVal) * h;
            const bY = pT + h - bH;

            svg += `<g><title>Lương thực lĩnh ${lbl}: ${full_labels[i]}</title>`;
            svg += `<rect x="${cx - barW / 2}" y="${bY}" width="${barW}" height="${bH}" rx="4.5" fill="#16a34a" opacity="0.82"/>`;
            svg += `<text x="${cx}" y="${bY - 7}" text-anchor="middle" font-size="10.5" font-weight="800" fill="#15803d">${tr_labels[i]}</text>`;
            svg += `</g>`;
            svg += `<text x="${cx}" y="${height - 5}" text-anchor="middle" font-size="11" font-weight="800" fill="#475569">${lbl}</text>`;
            pts.push({ x: cx, y: bY });
        });

        svg += `<polyline fill="none" stroke="#2563eb" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" points="${pts.map((p) => `${p.x},${p.y}`).join(" ")}"/>`;
        pts.forEach((p) => {
            svg += `<circle cx="${p.x}" cy="${p.y}" r="3.8" fill="#2563eb" stroke="#ffffff" stroke-width="1.8"/>`;
        });
        svg += `</svg>`;
        return markup(svg);
    }

    openList(title, model, domain = [], context = {}) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            context: context,
            target: "current",
        });
    }

    openPlanForm(planId, studentId = false) {
        const gvId = this.state.data.teacher.id;
        const action = {
            type: "ir.actions.act_window",
            name: planId ? "Kế hoạch can thiệp" : "Lập kế hoạch can thiệp mới",
            res_model: "ekids.kehoach",
            view_mode: "form",
            views: [[false, "form"]],
            context: {
                default_hocsinh_id: studentId || false,
                default_gv_lapkehoach_id: gvId,
                default_giaovien_id: gvId,
            },
            target: "current",
        };
        if (planId) {
            action.res_id = planId;
        }
        this.action.doAction(action);
    }
}

registry.category("actions").add("ekids_dashboard.giaovien_action", EkidsGiaovienDashboard);