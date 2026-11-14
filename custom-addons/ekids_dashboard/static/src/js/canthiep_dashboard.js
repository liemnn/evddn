/** @odoo-module **/

import { Component, useState, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class EkidsCanthiepDashboard extends Component {
    static template = "ekids_dashboard.CanthiepDashboardTemplate";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            loading: true,
            centerId: "",      // Backend tự mặc định chọn 1 cơ sở đầu tiên
            monthStr: "",      // Backend tự mặc định chọn tháng hiện tại
            weekIndex: null,   // Backend tự mặc định chọn tuần hiện tại
            rowFilter: "all",  // 'all' | 'pending' | 'done'
            data: null,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const result = await this.orm.call(
                "ekids.dashboard_canthiep",
                "get_dashboard_data",
                [],
                {
                    center_id: this.state.centerId || false,
                    month_str: this.state.monthStr || false,
                    week_index: this.state.weekIndex || false,
                }
            );
            this.state.data = result;
            this.state.centerId = String(result.selected_center_id);
            this.state.monthStr = String(result.selected_month);
            this.state.weekIndex = Number(result.selected_week_index);
        } finally {
            this.state.loading = false;
        }
    }

    async onChangeCenter(ev) {
        this.state.centerId = ev.target.value;
        await this.loadData();
    }

    async onChangeMonth(ev) {
        this.state.monthStr = ev.target.value;
        this.state.weekIndex = null; // Reset để tự chọn tuần 1 (hoặc tuần hiện tại nếu là tháng này)
        await this.loadData();
    }

    async onChangeWeek(ev) {
        this.state.weekIndex = parseInt(ev.target.value, 10);
        await this.loadData();
    }

    setRowFilter(mode) {
        this.state.rowFilter = mode;
    }

    get filteredWeeklyStudents() {
        if (!this.state.data) return [];
        const mode = this.state.rowFilter;
        const students = this.state.data.weekly.students;
        if (mode === "all") return students;

        return students
            .map((st) => ({
                ...st,
                plans: st.plans.filter((p) => (mode === "done" ? p.is_done : !p.is_done)),
            }))
            .filter((st) => st.plans.length > 0);
    }

    getMiniGaugeSvg(pct, color) {
        const size = 38, stroke = 4.5, c = size / 2, r = c - stroke, circ = 2 * Math.PI * r;
        const svg = `<svg viewBox="0 0 ${size} ${size}" style="width:100%;height:100%;transform:rotate(-90deg);">
            <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="#e2e8f0" stroke-width="${stroke}"/>
            <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="${color}" stroke-width="${stroke}"
                    stroke-dasharray="${(pct / 100) * circ} ${circ}" stroke-linecap="round"/>
            <text x="${c}" y="${c + 3.5}" transform="rotate(90 ${c} ${c})" text-anchor="middle" font-size="9.5" font-weight="800" fill="${color}">${pct}%</text>
        </svg>`;
        return markup(svg);
    }

    getComboChartSvg() {
        if (!this.state.data) return "";
        const { labels, bars, lines } = this.state.data.chart_compare;
        const barColor = "#3b6e8c", lineColor = "#7c3aed";
        const width = 680, height = 225;
        const pL = 22, pR = 22, pT = 28, pB = 22;
        const w = width - pL - pR, h = height - pT - pB;
        const max = Math.max(...bars, ...lines, 1) * 1.18;
        const step = w / Math.max(labels.length, 1);
        const barW = Math.min(24, step * 0.45);

        let svg = `<svg viewBox="0 0 ${width} ${height}" style="width:100%;height:auto;display:block;">`;
        for (let i = 0; i <= 2; i++) {
            const y = pT + (h * i) / 2;
            svg += `<line x1="${pL}" y1="${y}" x2="${width - pR}" y2="${y}" stroke="#f1f5f9" stroke-width="1"/>`;
        }
        svg += `<line x1="${pL}" y1="${pT + h}" x2="${width - pR}" y2="${pT + h}" stroke="#cbd5e1" stroke-width="1.2"/>`;

        let pts = [];
        labels.forEach((lbl, i) => {
            const cx = pL + step * i + step / 2;
            const bH = (bars[i] / max) * h;
            const bY = pT + h - bH;
            svg += `<rect x="${cx - barW / 2}" y="${bY}" width="${barW}" height="${bH}" rx="4" fill="${barColor}" opacity="0.88"/>`;
            svg += `<text x="${cx}" y="${bY - 6}" text-anchor="middle" font-size="10.5" font-weight="800" fill="${barColor}">${bars[i]}</text>`;

            const lY = pT + h - (lines[i] / max) * h;
            pts.push({ x: cx, y: lY, val: lines[i], bY });
            svg += `<text x="${cx}" y="${height - 5}" text-anchor="middle" font-size="11" font-weight="700" fill="#64748b">${lbl}</text>`;
        });

        svg += `<polyline fill="none" stroke="${lineColor}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" points="${pts.map(p => `${p.x},${p.y}`).join(' ')}"/>`;
        pts.forEach(p => {
            svg += `<circle cx="${p.x}" cy="${p.y}" r="3.6" fill="#fff" stroke="${lineColor}" stroke-width="2.4"/>`;
            const off = Math.abs(p.y - p.bY) < 16 ? 15 : -8;
            svg += `<text x="${p.x}" y="${p.y + off}" text-anchor="middle" font-size="10.5" font-weight="800" fill="${lineColor}">${p.val}</text>`;
        });
        svg += `</svg>`;
        return markup(svg);
    }

    openList(title, model, domain = []) {
        const finalDomain = [...domain];
        if (this.state.centerId && this.state.centerId !== "0") {
            finalDomain.push(["coso_id", "=", parseInt(this.state.centerId, 10)]);
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: finalDomain,
            target: "current",
        });
    }

    openPlanForm(planId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Đánh giá kết quả can thiệp",
            res_model: "ekids.kehoach",
            res_id: planId,
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("ekids_dashboard.canthiep_action", EkidsCanthiepDashboard);