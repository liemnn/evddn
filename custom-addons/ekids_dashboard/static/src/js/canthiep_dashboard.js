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
        const barColor = "#2563eb";   // Xanh dương tươi
        const lineColor = "#dc2626";  // Đỏ đậm
        const width = 680, height = 210;
        const pL = 24, pR = 24, pT = 26, pB = 24;
        const w = width - pL - pR, h = height - pT - pB;
        const max = Math.max(...bars, ...lines, 1) * 1.18;
        const step = w / Math.max(labels.length, 1);
        const barW = Math.min(26, step * 0.46);

        let svg = `<svg viewBox="0 0 ${width} ${height}" style="width:100%;height:auto;display:block;">`;

        // Lưới ngang mảnh
        for (let i = 0; i <= 3; i++) {
            const y = pT + (h * i) / 3;
            svg += `<line x1="${pL}" y1="${y}" x2="${width - pR}" y2="${y}" stroke="#f1f5f9" stroke-width="1"/>`;
        }
        // Đường trục đáy
        svg += `<line x1="${pL}" y1="${pT + h}" x2="${width - pR}" y2="${pT + h}" stroke="#94a3b8" stroke-width="1.3"/>`;

        let pts = [];
        labels.forEach((lbl, i) => {
            const cx = pL + step * i + step / 2;
            const bH = (bars[i] / max) * h;
            const bY = pT + h - bH;

            // Cột xanh dương
            svg += `<rect x="${cx - barW / 2}" y="${bY}" width="${barW}" height="${bH}" rx="4" fill="${barColor}" opacity="0.82"/>`;
            // Số trên đỉnh cột (màu xanh dương đậm)
            svg += `<text x="${cx}" y="${bY - 6}" text-anchor="middle" font-size="11" font-weight="800" fill="#1d4ed8">${bars[i]}</text>`;

            const lY = pT + h - (lines[i] / max) * h;
            pts.push({ x: cx, y: lY, val: lines[i], bY });

            // Nhãn tháng T1..T12 dưới trục X
            svg += `<text x="${cx}" y="${height - 5}" text-anchor="middle" font-size="11.5" font-weight="800" fill="#475569">${lbl}</text>`;
        });

        // Đường nối màu đỏ đậm
        svg += `<polyline fill="none" stroke="${lineColor}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" points="${pts.map(p => `${p.x},${p.y}`).join(' ')}"/>`;

        // Điểm tròn và nhãn số màu đỏ đậm có nền trắng chống đè chữ
        pts.forEach(p => {
            svg += `<circle cx="${p.x}" cy="${p.y}" r="4.2" fill="${lineColor}" stroke="#ffffff" stroke-width="1.8"/>`;
            const lblY = p.val === 0 ? p.y - 9 : (Math.abs(p.y - p.bY) < 18 ? p.y + 17 : p.y - 9);
            const textStr = String(p.val);
            const pillW = Math.max(18, textStr.length * 7 + 8);
            svg += `<rect x="${p.x - pillW / 2}" y="${lblY - 10}" width="${pillW}" height="13" rx="3.5" fill="#ffffff" stroke="#fecaca" stroke-width="0.8" opacity="0.95"/>`;
            svg += `<text x="${p.x}" y="${lblY}" text-anchor="middle" font-size="10.5" font-weight="900" fill="#b91c1c">${textStr}</text>`;
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