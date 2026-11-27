/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onWillUpdateProps } from "@odoo/owl";

export class CoSoCauHinhWidget extends Component {
    static template = "ekids_core.CoSoCauHinhWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({
            data: this.parseJson(this.props.record.data[this.props.name]),
            newLuongItem: "",
            showRawJson: false,
        });

        onWillUpdateProps((nextProps) => {
            const nextVal = nextProps.record.data[nextProps.name];
            const currentSerialized = this.serializeJson(this.state.data);
            if (nextVal !== currentSerialized) {
                this.state.data = this.parseJson(nextVal);
            }
        });
    }

    getDefaultConfig() {
        return {
            KEHOACH_CANTHIEP: {
                muctieu_soluong_mo: "1",
                macdinh_songay_kehoach: "30",
                muctieu_soluong_dat_lientiep: "6",
                muctieu_thietke_uutien: "0",
                muctieu_soluong_ngay_tudong_capnhat: "3",
            },
            LUONG: {
                dm_luong_list: ["Lương cơ bản", "Thưởng học sinh"],
            },
        };
    }

    parseJson(rawStr) {
        const defaults = this.getDefaultConfig();
        if (!rawStr || typeof rawStr !== "string" || !rawStr.trim()) {
            return defaults;
        }
        try {
            const parsed = JSON.parse(rawStr);
            const rawKh = { ...(parsed.KEHOACH_CANTHIEP || {}) };
            // Loại bỏ 3 tham số tỷ lệ mặc định nếu tồn tại trong JSON cũ
            delete rawKh.muctieu_tyle_macdinh_chuadat;
            delete rawKh.muctieu_tyle_macdinh_hinhthanh;
            delete rawKh.muctieu_tyle_macdinh_dat;

            const kh = { ...defaults.KEHOACH_CANTHIEP, ...rawKh };
            const rawLuong = parsed.LUONG?.dm_luong;
            let luongList = [...defaults.LUONG.dm_luong_list];

            if (Array.isArray(rawLuong)) {
                luongList = rawLuong;
            } else if (typeof rawLuong === "string" && rawLuong.trim()) {
                const normalized = rawLuong.replace(/'/g, '"');
                try {
                    const arr = JSON.parse(normalized);
                    if (Array.isArray(arr)) luongList = arr;
                } catch {
                    luongList = rawLuong
                        .replace(/^\[|\]$/g, "")
                        .split(",")
                        .map((s) => s.trim().replace(/^['"]|['"]$/g, ""))
                        .filter(Boolean);
                }
            }

            return {
                KEHOACH_CANTHIEP: kh,
                LUONG: { dm_luong_list: luongList },
            };
        } catch {
            return defaults;
        }
    }

    serializeJson(stateData) {
        const kh = stateData.KEHOACH_CANTHIEP;
        const luongStr = "[" + stateData.LUONG.dm_luong_list.map((item) => `'${item}'`).join(",") + "]";
        const payload = {
            KEHOACH_CANTHIEP: {
                muctieu_soluong_mo: String(kh.muctieu_soluong_mo ?? "1"),
                macdinh_songay_kehoach: String(kh.macdinh_songay_kehoach ?? "30"),
                muctieu_soluong_dat_lientiep: String(kh.muctieu_soluong_dat_lientiep ?? "6"),
                muctieu_thietke_uutien: String(kh.muctieu_thietke_uutien ?? "0"),
                muctieu_soluong_ngay_tudong_capnhat: String(kh.muctieu_soluong_ngay_tudong_capnhat ?? "3"),
            },
            LUONG: {
                dm_luong: luongStr,
            },
        };
        return JSON.stringify(payload, null, 2);
    }

    async commitChange() {
        const jsonString = this.serializeJson(this.state.data);
        await this.props.record.update({ [this.props.name]: jsonString });
    }

    onKhInputChange(key, ev) {
        this.state.data.KEHOACH_CANTHIEP[key] = ev.target.value;
        this.commitChange();
    }

    onKhToggleChange(key, ev) {
        this.state.data.KEHOACH_CANTHIEP[key] = ev.target.checked ? "1" : "0";
        this.commitChange();
    }

    addLuongItem() {
        const val = this.state.newLuongItem.trim();
        if (!val) return;
        if (!this.state.data.LUONG.dm_luong_list.includes(val)) {
            this.state.data.LUONG.dm_luong_list.push(val);
            this.state.newLuongItem = "";
            this.commitChange();
        }
    }

    removeLuongItem(index) {
        this.state.data.LUONG.dm_luong_list.splice(index, 1);
        this.commitChange();
    }

    onLuongKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.addLuongItem();
        }
    }

    get rawJsonPreview() {
        return this.serializeJson(this.state.data);
    }
}

registry.category("fields").add("ekids_coso_cauhinh", {
    component: CoSoCauHinhWidget,
    supportedTypes: ["text"],
});