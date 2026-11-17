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
            dang_tai: true,
            thang_nam: "",
            loc_dong: "tatca",
            dulieu: null,
        });

        onWillStart(async () => {
            await this.taiDuLieu();
        });
    }

    async taiDuLieu() {
        this.state.dang_tai = true;
        try {
            const ketqua = await this.orm.call(
                "ekids.dashboard_giaovien",
                "get_dashboard_data",
                [],
                { thang_nam: this.state.thang_nam || false }
            );
            this.state.dulieu = ketqua;
            if (ketqua && ketqua.co_giaovien) {
                this.state.thang_nam = String(ketqua.thang_nam);
            }
        } finally {
            this.state.dang_tai = false;
        }
    }

    async khiDoiThang(ev) {
        this.state.thang_nam = ev.target.value;
        await this.taiDuLieu();
    }

    datBoLocDong(che_do) {
        this.state.loc_dong = che_do;
    }

    get dsDongDaLoc() {
        if (!this.state.dulieu || !this.state.dulieu.co_giaovien) return [];
        const ds_dong = this.state.dulieu.ds_dong_hocsinh || [];
        if (this.state.loc_dong === "tatca") return ds_dong;
        return ds_dong.filter((r) => r.trangthai === this.state.loc_dong);
    }

    veBieuDoLuong() {
        if (!this.state.dulieu || !this.state.dulieu.co_giaovien) return "";
        const { nhan_thang, giatri_cot, nhan_trieu, nhan_daydu } = this.state.dulieu.bieudo_luong;
        if (!nhan_thang || !nhan_thang.length) return "";

        const rong = 760, cao = 210;
        const pL = 24, pR = 24, pT = 30, pB = 24;
        const w = rong - pL - pR, h = cao - pT - pB;
        const giatri_max = Math.max(...giatri_cot, 1) * 1.18;
        const buoc = w / nhan_thang.length;
        const rong_cot = Math.min(32, buoc * 0.48);

        let svg = `<svg viewBox="0 0 ${rong} ${cao}" style="width:100%;height:auto;display:block;">`;
        for (let i = 0; i <= 3; i++) {
            const y = pT + (h * i) / 3;
            svg += `<line x1="${pL}" y1="${y}" x2="${rong - pR}" y2="${y}" stroke="#f1f5f9" stroke-width="1"/>`;
        }
        svg += `<line x1="${pL}" y1="${pT + h}" x2="${rong - pR}" y2="${pT + h}" stroke="#94a3b8" stroke-width="1.3"/>`;

        let ds_diem = [];
        nhan_thang.forEach((nhan, i) => {
            const cx = pL + buoc * i + buoc / 2;
            const cao_cot = (giatri_cot[i] / giatri_max) * h;
            const y_cot = pT + h - cao_cot;

            svg += `<g><title>Lương thực lĩnh ${nhan}: ${nhan_daydu[i]}</title>`;
            svg += `<rect x="${cx - rong_cot / 2}" y="${y_cot}" width="${rong_cot}" height="${cao_cot}" rx="4.5" fill="#16a34a" opacity="0.82"/>`;
            svg += `<text x="${cx}" y="${y_cot - 7}" text-anchor="middle" font-size="10.5" font-weight="800" fill="#15803d">${nhan_trieu[i]}</text>`;
            svg += `</g>`;
            svg += `<text x="${cx}" y="${cao - 5}" text-anchor="middle" font-size="11" font-weight="800" fill="#475569">${nhan}</text>`;
            ds_diem.push({ x: cx, y: y_cot });
        });

        svg += `<polyline fill="none" stroke="#2563eb" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" points="${ds_diem.map((p) => `${p.x},${p.y}`).join(" ")}"/>`;
        ds_diem.forEach((p) => {
            svg += `<circle cx="${p.x}" cy="${p.y}" r="3.8" fill="#2563eb" stroke="#ffffff" stroke-width="1.8"/>`;
        });
        svg += `</svg>`;
        return markup(svg);
    }

    moDanhSach(tieu_de, ten_model, domain = [], context = {}) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: tieu_de,
            res_model: ten_model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            context: context,
            target: "current",
        });
    }

    moFormKeHoach(kehoachId, hocsinhId = false) {
        const gvId = this.state.dulieu.giaovien.id;
        const action = {
            type: "ir.actions.act_window",
            name: kehoachId ? "Kế hoạch can thiệp" : "Lập kế hoạch can thiệp mới",
            res_model: "ekids.kehoach",
            view_mode: "form",
            views: [[false, "form"]],
            context: {
                default_hocsinh_id: hocsinhId || false,
                default_gv_lapkehoach_id: gvId,
                default_giaovien_id: gvId,
            },
            target: "current",
        };
        if (kehoachId) {
            action.res_id = kehoachId;
        }
        this.action.doAction(action);
    }
}

registry.category("actions").add("ekids_dashboard.giaovien_action", EkidsGiaovienDashboard);