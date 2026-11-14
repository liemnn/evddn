/** @odoo-module **/

import { Component, useState, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class EkidsVanhanhDashboard extends Component {
    static template = "ekids_dashboard.VanhanhDashboardTemplate";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            loading: true,
            centerId: "",
            monthStr: "",
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
                "ekids.dashboard_vanhanh",
                "get_dashboard_data",
                [],
                {
                    center_id: this.state.centerId || false,
                    month_str: this.state.monthStr || false,
                }
            );
            this.state.data = result;
            this.state.centerId = String(result.selected_center_id);
            this.state.monthStr = String(result.selected_month);
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
        await this.loadData();
    }

    getDonutSvg() {
        if (!this.state.data) return "";
        const d = this.state.data.tuition_donut;
        const items = [
            { val: d.paid_val, color: "#16a34a" },
            { val: d.unpaid_val, color: "#dc2626" },
            { val: d.exempt_val, color: "#f59e0b" },
        ];
        const size = 136, stroke = 20, c = size / 2, r = c - stroke / 2, circ = 2 * Math.PI * r;
        const total = items.reduce((s, x) => s + x.val, 0);
        let acc = 0;

        let svg = `<svg viewBox="0 0 ${size} ${size}" style="width:100%;height:100%;transform:rotate(-90deg);">`;
        items.forEach((it) => {
            const pct = total > 0 ? it.val / total : 0;
            svg += `<circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="${it.color}" stroke-width="${stroke}"
                    stroke-dasharray="${pct * circ} ${circ}" stroke-dashoffset="${-acc * circ}"/>`;
            acc += pct;
        });
        svg += `<g transform="rotate(90 ${c} ${c})">
                    <text x="${c}" y="${c - 2}" text-anchor="middle" font-size="18" font-weight="800" fill="#0f172a">${d.paid_pct_int}%</text>
                    <text x="${c}" y="${c + 13}" text-anchor="middle" font-size="10" font-weight="700" fill="#64748b">ĐÃ THU</text>
                </g></svg>`;
        return markup(svg);
    }

    getComboChartSvg(type) {
        if (!this.state.data) return "";
        const labels = this.state.data.charts.labels;
        const chartSet = this.state.data.charts[type];
        if (!chartSet || !labels.length) return "";

        const configs = {
            profit: { barColor: "#22c55e", lineColor: "#d97706", width: 720, height: 185, showLineLabels: false },
            tuition: { barColor: "#2563eb", lineColor: "#16a34a", width: 420, height: 170, showLineLabels: false },
            salary: { barColor: "#7c3aed", lineColor: "#d97706", width: 420, height: 170, showLineLabels: false },
            io: { barColor: "#16a34a", lineColor: "#dc2626", width: 420, height: 130, showLineLabels: true },
        };
        const cfg = configs[type];
        const { bars, lines } = chartSet;
        const { barColor, lineColor, width, height, showLineLabels } = cfg;

        const pL = 20, pR = 20, pT = 26, pB = 22;
        const w = width - pL - pR, h = height - pT - pB;
        const max = Math.max(...bars, ...lines, 1) * 1.18;
        const step = w / labels.length;
        const barW = Math.min(24, step * 0.48);

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
            svg += `<rect x="${cx - barW / 2}" y="${bY}" width="${barW}" height="${bH}" rx="4" fill="${barColor}" opacity="0.85"/>`;
            svg += `<text x="${cx}" y="${bY - 5}" text-anchor="middle" font-size="10.5" font-weight="800" fill="${barColor}">${bars[i]}</text>`;

            const lY = pT + h - (lines[i] / max) * h;
            pts.push({ x: cx, y: lY, val: lines[i], bY });
            svg += `<text x="${cx}" y="${height - 5}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#64748b">${lbl}</text>`;
        });

        svg += `<polyline fill="none" stroke="${lineColor}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" points="${pts.map(p => `${p.x},${p.y}`).join(" ")}"/>`;
        pts.forEach((p) => {
            svg += `<circle cx="${p.x}" cy="${p.y}" r="3.6" fill="${lineColor}" stroke="#fff" stroke-width="1.8"/>`;
            if (showLineLabels) {
                const off = Math.abs(p.y - p.bY) < 16 ? 15 : -8;
                const textStr = String(p.val);
                const pillW = Math.max(22, textStr.length * 6.5 + 6);
                svg += `<rect x="${p.x - pillW / 2}" y="${p.y + off - 9}" width="${pillW}" height="12" rx="3" fill="#fff" stroke="#fecaca" stroke-width="0.8"/>`;
                svg += `<text x="${p.x}" y="${p.y + off}" text-anchor="middle" font-size="9.5" font-weight="900" fill="${lineColor}">${textStr}</text>`;
            }
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
}

registry.category("actions").add("ekids_dashboard.vanhanh_action", EkidsVanhanhDashboard);