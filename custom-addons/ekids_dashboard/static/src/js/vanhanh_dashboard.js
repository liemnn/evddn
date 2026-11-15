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
            dang_tai: true,
            coso_id: "",
            nam_taichinh: "",
            thang_nam: "",
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
                "ekids.dashboard_vanhanh",
                "get_dashboard_data",
                [],
                {
                    coso_id: this.state.coso_id || false,
                    nam_taichinh: this.state.nam_taichinh || false,
                    thang_nam: this.state.thang_nam || false,
                }
            );
            this.state.dulieu = ketqua;
            this.state.coso_id = String(ketqua.coso_id);
            this.state.nam_taichinh = String(ketqua.nam_taichinh);
            this.state.thang_nam = String(ketqua.thang_nam);
        } finally {
            this.state.dang_tai = false;
        }
    }

    async khiDoiCoSo(ev) {
        this.state.coso_id = ev.target.value;
        await this.taiDuLieu();
    }

    async khiDoiNamTaiChinh(ev) {
        this.state.nam_taichinh = ev.target.value;
        this.state.thang_nam = "";
        await this.taiDuLieu();
    }

    async khiDoiThang(ev) {
        this.state.thang_nam = ev.target.value;
        await this.taiDuLieu();
    }

    veBieuDoTronHocPhi() {
        if (!this.state.dulieu) return "";
        const hp = this.state.dulieu.hocphi_thang;
        // Chỉ đưa Đã thu & Chưa thu vào vòng tròn tỷ lệ (không đưa Miễn giảm vào %)
        const ds_phan = [
            { giatri: hp.da_thu_val, mau: "#16a34a" },
            { giatri: hp.chua_thu_val, mau: "#dc2626" },
        ];
        const size = 136, stroke = 20, c = size / 2, r = c - stroke / 2, circ = 2 * Math.PI * r;
        const tong = ds_phan.reduce((s, x) => s + x.giatri, 0);
        let tich_luy = 0;

        let svg = `<svg viewBox="0 0 ${size} ${size}" style="width:100%;height:100%;transform:rotate(-90deg);">`;
        if (tong <= 0) {
            svg += `<circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="#e2e8f0" stroke-width="${stroke}"/>`;
        } else {
            ds_phan.forEach((phan) => {
                const tyle = phan.giatri / tong;
                svg += `<circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="${phan.mau}" stroke-width="${stroke}"
                        stroke-dasharray="${tyle * circ} ${circ}" stroke-dashoffset="${-tich_luy * circ}"/>`;
                tich_luy += tyle;
            });
        }
        svg += `<g transform="rotate(90 ${c} ${c})">
                    <text x="${c}" y="${c - 2}" text-anchor="middle" font-size="18" font-weight="800" fill="#0f172a">${hp.tyle_da_thu_tron}%</text>
                    <text x="${c}" y="${c + 13}" text-anchor="middle" font-size="10" font-weight="700" fill="#64748b">ĐÃ THU</text>
                </g></svg>`;
        return markup(svg);
    }

    veBieuDoTongHopTaiChinh() {
        if (!this.state.dulieu) return "";
        const nhan_thang = this.state.dulieu.bieudo.nhan_thang;
        const dl = this.state.dulieu.bieudo.tonghop_taichinh;
        if (!dl || !nhan_thang.length) return "";

        const { cot_thu, cot_chi, duong_loinhuan, nhan_thu, nhan_chi, nhan_ln, full_thu, full_chi, full_ln } = dl;
        const mau_thu = "#2563eb";
        const mau_chi = "#ef4444";
        const mau_loinhuan = "#16a34a";

        const rong = 820, cao = 225;
        const pL = 22, pR = 22, pT = 36, pB = 24;
        const w = rong - pL - pR, h = cao - pT - pB;

        const max_val = Math.max(...cot_thu, ...cot_chi, ...duong_loinhuan, 1) * 1.18;
        const min_val = Math.min(0, ...duong_loinhuan);
        const range_val = (max_val - min_val) || 1;
        const zero_y = pT + (max_val / range_val) * h;

        const buoc = w / nhan_thang.length;
        const rong_cot = Math.min(20, buoc * 0.35);
        const khe_cot = 3;

        let svg = `<svg viewBox="0 0 ${rong} ${cao}" style="width:100%;height:auto;display:block;">`;

        for (let i = 0; i <= 3; i++) {
            const y = pT + (h * i) / 3;
            svg += `<line x1="${pL}" y1="${y}" x2="${rong - pR}" y2="${y}" stroke="#f1f5f9" stroke-width="1"/>`;
        }
        svg += `<line x1="${pL}" y1="${zero_y}" x2="${rong - pR}" y2="${zero_y}" stroke="#94a3b8" stroke-width="1.3"/>`;

        let ds_diem_ln = [];
        nhan_thang.forEach((nhan, i) => {
            const cx = pL + buoc * i + buoc / 2;

            // Cột 1: Tổng thu (hiển thị dạng 428,9tr)
            const x_thu = cx - rong_cot - khe_cot / 2;
            const cao_thu = (cot_thu[i] / range_val) * h;
            const y_thu = zero_y - cao_thu;
            const tx_thu = x_thu + rong_cot / 2;
            const ty_thu = y_thu - 5;
            svg += `<g><title>Tổng thu ${nhan}: ${full_thu[i]}</title>`;
            svg += `<rect x="${x_thu}" y="${y_thu}" width="${rong_cot}" height="${cao_thu}" rx="3.5" fill="${mau_thu}" opacity="0.88"/>`;
            svg += `<text x="${tx_thu}" y="${ty_thu}" transform="rotate(-35 ${tx_thu} ${ty_thu})" text-anchor="start" font-size="9" font-weight="800" fill="#1d4ed8">${nhan_thu[i]}</text>`;
            svg += `</g>`;

            // Cột 2: Tổng chi (hiển thị dạng 332,4tr)
            const x_chi = cx + khe_cot / 2;
            const cao_chi = (cot_chi[i] / range_val) * h;
            const y_chi = zero_y - cao_chi;
            const tx_chi = x_chi + rong_cot / 2;
            const ty_chi = y_chi - 5;
            svg += `<g><title>Tổng chi ${nhan}: ${full_chi[i]}</title>`;
            svg += `<rect x="${x_chi}" y="${y_chi}" width="${rong_cot}" height="${cao_chi}" rx="3.5" fill="${mau_chi}" opacity="0.85"/>`;
            svg += `<text x="${tx_chi}" y="${ty_chi}" transform="rotate(-35 ${tx_chi} ${ty_chi})" text-anchor="start" font-size="9" font-weight="800" fill="#dc2626">${nhan_chi[i]}</text>`;
            svg += `</g>`;

            const y_ln = zero_y - (duong_loinhuan[i] / range_val) * h;
            ds_diem_ln.push({ x: cx, y: y_ln, giatri_tr: nhan_ln[i], full: full_ln[i], thang: nhan });

            svg += `<text x="${cx}" y="${cao - 5}" text-anchor="middle" font-size="11" font-weight="800" fill="#475569">${nhan}</text>`;
        });

        svg += `<polyline fill="none" stroke="${mau_loinhuan}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" points="${ds_diem_ln.map(p => `${p.x},${p.y}`).join(" ")}"/>`;

        ds_diem_ln.forEach((p) => {
            const chuoi_so = String(p.giatri_tr);
            const rong_nhan = Math.max(38, chuoi_so.length * 6 + 8);
            const y_nhan = p.y - 8;
            svg += `<g><title>Lợi nhuận ${p.thang}: ${p.full}</title>`;
            svg += `<circle cx="${p.x}" cy="${p.y}" r="4.2" fill="${mau_loinhuan}" stroke="#ffffff" stroke-width="1.8"/>`;
            svg += `<rect x="${p.x - rong_nhan / 2}" y="${y_nhan - 10}" width="${rong_nhan}" height="13" rx="3.5" fill="#ffffff" stroke="#86efac" stroke-width="1"/>`;
            svg += `<text x="${p.x}" y="${y_nhan}" text-anchor="middle" font-size="9.5" font-weight="900" fill="#15803d">${chuoi_so}</text>`;
            svg += `</g>`;
        });

        svg += `</svg>`;
        return markup(svg);
    }

    veBieuDoKetHop(loai_bieudo) {
        if (!this.state.dulieu) return "";
        const nhan_thang = this.state.dulieu.bieudo.nhan_thang;
        const bo_dulieu = this.state.dulieu.bieudo[loai_bieudo];
        if (!bo_dulieu || !nhan_thang.length) return "";

        const cauhinh_bieudo = {
            thu_hocphi: { mau_cot: "#2563eb", mau_duong: "#16a34a", co_duong: true, rong: 640, cao: 185 },
            chi_luong: { mau_cot: "#7c3aed", mau_duong: "#d97706", co_duong: true, rong: 640, cao: 185 },
            nguon_chi: { mau_cot: "#ef4444", mau_duong: null, co_duong: false, rong: 740, cao: 185 },
        };
        const cfg = cauhinh_bieudo[loai_bieudo];
        const cot = bo_dulieu.cot || [];
        const duong = bo_dulieu.duong || [];
        const nhan_so = bo_dulieu.nhan || [];
        const full_so = bo_dulieu.full || [];
        const { mau_cot, mau_duong, co_duong, rong, cao } = cfg;

        const pL = 20, pR = 22, pT = 28, pB = 22;
        const w = rong - pL - pR, h = cao - pT - pB;
        const tatca_so = co_duong ? [...cot, ...duong] : [...cot];
        const max_val = Math.max(...tatca_so, 1) * 1.18;
        const buoc = w / nhan_thang.length;
        const rong_cot = Math.min(28, buoc * 0.48);

        let svg = `<svg viewBox="0 0 ${rong} ${cao}" style="width:100%;height:auto;display:block;">`;
        for (let i = 0; i <= 2; i++) {
            const y = pT + (h * i) / 2;
            svg += `<line x1="${pL}" y1="${y}" x2="${rong - pR}" y2="${y}" stroke="#f1f5f9" stroke-width="1"/>`;
        }
        svg += `<line x1="${pL}" y1="${pT + h}" x2="${rong - pR}" y2="${pT + h}" stroke="#cbd5e1" stroke-width="1.2"/>`;

        let ds_diem = [];
        nhan_thang.forEach((nhan, i) => {
            const cx = pL + buoc * i + buoc / 2;
            const cao_cot = (cot[i] / max_val) * h;
            const y_cot = pT + h - cao_cot;

            svg += `<g><title>${nhan}: ${full_so[i] || ""}</title>`;
            svg += `<rect x="${cx - rong_cot / 2}" y="${y_cot}" width="${rong_cot}" height="${cao_cot}" rx="4" fill="${mau_cot}" opacity="0.86"/>`;
            svg += `<text x="${cx}" y="${y_cot - 5}" text-anchor="middle" font-size="9.5" font-weight="800" fill="${mau_cot}">${nhan_so[i] || ""}</text>`;
            svg += `</g>`;

            if (co_duong && duong.length > i) {
                const y_duong = pT + h - (duong[i] / max_val) * h;
                ds_diem.push({ x: cx, y: y_duong });
            }
            svg += `<text x="${cx}" y="${cao - 5}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#64748b">${nhan}</text>`;
        });

        if (co_duong && ds_diem.length) {
            svg += `<polyline fill="none" stroke="${mau_duong}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" points="${ds_diem.map(p => `${p.x},${p.y}`).join(" ")}"/>`;
            ds_diem.forEach((p) => {
                svg += `<circle cx="${p.x}" cy="${p.y}" r="3.6" fill="${mau_duong}" stroke="#fff" stroke-width="1.8"/>`;
            });
        }

        svg += `</svg>`;
        return markup(svg);
    }

    moDanhSach(tieu_de, ten_model, domain = []) {
        const domain_cuoi = [...domain];
        if (this.state.coso_id && this.state.coso_id !== "0") {
            domain_cuoi.push(["coso_id", "=", parseInt(this.state.coso_id, 10)]);
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: tieu_de,
            res_model: ten_model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: domain_cuoi,
            target: "current",
        });
    }
}

registry.category("actions").add("ekids_dashboard.vanhanh_action", EkidsVanhanhDashboard);