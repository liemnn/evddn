/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillUnmount, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class LapKehoachWidget extends Component {
    static template = "ekids_canthiep.LapKeHoachWidgetTemplate";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.actionService = useService("action");
        this._injectedToolbarBtn = null;

        this.state = useState({
            groupedData: [],
            activeNotes: {},
            collapsedLinhVuc: {},
            expandedTargets: {},
            // State cho tính năng thêm/quản lý lĩnh vực khi is_canthiep_ketluan == False
            showAddLinhVucBar: false,
            loadingAddLv: false,
            hasSummaryBarSlot: false,
            chuongtrinhs: [],
            linhvucs: [],
            tuois: [],
            selectedCtId: "",
            selectedLvId: "",
            selectedTuoiId: "",
        });

        onWillStart(async () => {
            await this.loadAllPlanData();
            if (this.canCustomLinhVuc) {
                await this.loadDanhMucLinhVuc();
            }
        });

        onMounted(() => {
            this.syncToolbarButton();
        });

        onWillUnmount(() => {
            if (this._injectedToolbarBtn && this._injectedToolbarBtn.parentNode) {
                this._injectedToolbarBtn.remove();
            }
        });
    }

    /* Kiểm tra điều kiện: Kế hoạch đang lập (không readonly) VÀ is_canthiep_ketluan == False */
    get canCustomLinhVuc() {
        const isCanThiepKetLuan = Boolean(this.props.record?.data?.is_canthiep_ketluan);
        return !this.props.readonly && !isCanThiepKetLuan;
    }

    /* Đưa nút "+ Thêm lĩnh vực" lên Summary Bar và đặt ĐỨNG SAU nút "Lập [Kế hoạch] 6 tháng" */
    /* Đưa nút "+ Thêm lĩnh vực" lên cùng hàng, nằm ngay bên phải sát lề sau nút "Lập [Kế hoạch] 6 tháng" */

    syncToolbarButton() {
        if (this._injectedToolbarBtn && this._injectedToolbarBtn.parentNode) {
            this._injectedToolbarBtn.remove();
            this._injectedToolbarBtn = null;
        }

        if (!this.canCustomLinhVuc || !this.props.record.resId) {
            this.state.hasSummaryBarSlot = false;
            return;
        }

        const btn6Thang = document.querySelector('button[name="action_lap_kehoach_6thang"]');
        const summaryBar = document.querySelector(".ekids-summary-action-bar");
        const targetContainer = btn6Thang ? btn6Thang.parentElement : (summaryBar?.querySelector(".action-right-zone") || summaryBar);

        if (!targetContainer) {
            this.state.hasSummaryBarSlot = false;
            return;
        }

        // 1. Đổi nút "Lập [Kế hoạch] 6 tháng" sang tông xanh nhạt viền mảnh (nhường điểm nhấn chính cho nút Thêm lĩnh vực)
        if (btn6Thang) {
            btn6Thang.style.setProperty("background-color", "#EFF6FF", "important");
            btn6Thang.style.setProperty("color", "#1D4ED8", "important");
            btn6Thang.style.setProperty("border", "1.5px solid #93C5FD", "important");
            btn6Thang.style.setProperty("border-radius", "8px", "important");
            btn6Thang.style.setProperty("height", "34px", "important");
        }

        targetContainer.style.display = "inline-flex";
        targetContainer.style.alignItems = "center";
        targetContainer.style.flexWrap = "wrap";
        targetContainer.style.gap = "8px";

        // 2. Tạo nút "Thêm lĩnh vực" với màu xanh dương đậm nổi bật (Primary)
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-sm fw-bold shadow-sm ekids-btn-add-domain-top";
        btn.style.cssText =
            "border-radius: 8px; font-size: 13px; padding: 6px 14px; height: 34px; display: inline-flex; align-items: center; gap: 6px; background-color: #2563EB; color: #FFFFFF; border: 1.5px solid #1D4ED8; white-space: nowrap; margin: 0;";
        btn.innerHTML = `<i class="fa fa-plus-circle"></i><span>Thêm lĩnh vực vào Kế hoạch</span>`;
        btn.addEventListener("click", (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            this.toggleAddLinhVucBar();
        });

        targetContainer.appendChild(btn);
        this._injectedToolbarBtn = btn;
        this.state.hasSummaryBarSlot = true;
        this.updateToolbarButtonStyle();
    }

    updateToolbarButtonStyle() {
        if (!this._injectedToolbarBtn) return;
        if (this.state.showAddLinhVucBar) {
            // Khi đang mở khung chọn: chuyển sang tông xám nhạt dịu mắt để tránh chói
            this._injectedToolbarBtn.style.backgroundColor = "#F1F5F9";
            this._injectedToolbarBtn.style.color = "#334155";
            this._injectedToolbarBtn.style.borderColor = "#CBD5E1";
            this._injectedToolbarBtn.innerHTML = `<i class="fa fa-chevron-up"></i><span>Đóng thêm lĩnh vực vào Kế hoạch</span>`;
        } else {
            // Khi đóng: hiển thị xanh dương đậm nổi bật
            this._injectedToolbarBtn.style.backgroundColor = "#2563EB";
            this._injectedToolbarBtn.style.color = "#FFFFFF";
            this._injectedToolbarBtn.style.borderColor = "#1D4ED8";
            this._injectedToolbarBtn.innerHTML = `<i class="fa fa-plus-circle"></i><span>Thêm lĩnh vực vào Kế hoạch</span>`;
        }
    }

    get filteredLinhVucs() {
        const ctId = parseInt(this.state.selectedCtId || 0);
        if (!ctId) return [];
        return this.state.linhvucs.filter((lv) => lv.ct_id === ctId);
    }

    get filteredTuois() {
        const ctId = parseInt(this.state.selectedCtId || 0);
        if (!ctId) return [];
        const lvId = parseInt(this.state.selectedLvId || 0);

        return this.state.tuois.filter((t) => {
            if (t.ct_id && t.ct_id !== ctId) return false;
            if (t.lv_id && lvId && t.lv_id !== lvId) return false;
            if (t.lv_id && !lvId) return false;
            return true;
        });
    }

    async toggleAddLinhVucBar() {
        this.state.showAddLinhVucBar = !this.state.showAddLinhVucBar;
        this.updateToolbarButtonStyle();
        if (this.state.showAddLinhVucBar && !this.state.chuongtrinhs.length) {
            await this.loadDanhMucLinhVuc();
        }
    }

    async loadDanhMucLinhVuc() {
        const kehoachId = this.props.record.resId;
        if (!kehoachId) return;
        try {
            const data = await this.orm.call("ekids.kehoach", "get_danhmuc_them_linhvuc", [[kehoachId]]);
            this.state.chuongtrinhs = data.chuongtrinhs || [];
            this.state.linhvucs = data.linhvucs || [];
            this.state.tuois = data.tuois || [];
            this.state.selectedCtId = "";
            this.state.selectedLvId = "";
            this.state.selectedTuoiId = "";
        } catch (error) {
            console.error("Lỗi tải danh mục thêm lĩnh vực:", error);
        }
    }

    onChangeProgram(ev) {
        this.state.selectedCtId = ev.target.value;
        this.state.selectedLvId = "";
        this.state.selectedTuoiId = "";
    }

    onChangeLinhVuc(ev) {
        this.state.selectedLvId = ev.target.value;
        const hasLvBoundTuoi = this.state.tuois.some((t) => Boolean(t.lv_id));
        if (hasLvBoundTuoi) {
            this.state.selectedTuoiId = "";
        }
    }

    onChangeTuoi(ev) {
        this.state.selectedTuoiId = ev.target.value;
    }

    async onConfirmAddLinhVuc() {
        if (!this.canCustomLinhVuc) return;
        if (!this.state.selectedCtId || !this.state.selectedLvId || !this.state.selectedTuoiId) {
            this.notification.add("Vui lòng chọn đầy đủ Chương trình, Lĩnh vực và Độ tuổi!", { type: "warning" });
            return;
        }
        this.state.loadingAddLv = true;
        try {
            const kehoachId = this.props.record.resId;
            const res = await this.orm.call("ekids.kehoach", "action_widget_them_linhvuc", [
                [kehoachId],
                parseInt(this.state.selectedCtId),
                parseInt(this.state.selectedLvId),
                parseInt(this.state.selectedTuoiId),
            ]);
            if (res && res.status === "exists") {
                this.notification.add("Lĩnh vực này đã tồn tại trong kế hoạch!", { type: "info" });
            } else {
                this.notification.add("Đã thêm lĩnh vực vào Kế hoạch !", { type: "success" });
                this.state.selectedLvId = "";
                this.state.selectedTuoiId = "";
                this.state.showAddLinhVucBar = false;
                this.updateToolbarButtonStyle();
                await this.loadAllPlanData();
            }
        } catch (error) {
            console.error("Lỗi thêm lĩnh vực:", error);
            const msg = error?.data?.message || error?.message || "Không thể thêm lĩnh vực. Kiểm tra log server!";
            this.notification.add(msg, { type: "danger" });
        } finally {
            this.state.loadingAddLv = false;
        }
    }

    async onMoveLinhVuc(lineId, direction) {
        if (!this.canCustomLinhVuc) return;
        try {
            const kehoachId = this.props.record.resId;
            const moved = await this.orm.call("ekids.kehoach", "action_widget_doi_vitri_linhvuc", [
                [kehoachId],
                lineId,
                direction,
            ]);
            if (moved) {
                await this.loadAllPlanData();
            }
        } catch (error) {
            console.error("Lỗi đổi vị trí lĩnh vực:", error);
        }
    }

    async onDeleteLinhVuc(lineId, lvName) {
        if (!this.canCustomLinhVuc) return;
        if (!confirm(`Bạn có chắc chắn muốn xóa lĩnh vực [${lvName}] khỏi cả Kế hoạch  không?`)) {
            return;
        }
        try {
            const kehoachId = this.props.record.resId;
            await this.orm.call("ekids.kehoach", "action_widget_xoa_linhvuc", [[kehoachId], lineId]);
            this.notification.add(`Đã xóa lĩnh vực [${lvName}].`, { type: "info" });
            await this.loadAllPlanData();
        } catch (error) {
            console.error("Lỗi xóa lĩnh vực:", error);
            const msg = error?.data?.message || error?.message || "Không thể xóa lĩnh vực!";
            this.notification.add(msg, { type: "danger" });
        }
    }

    decodeHtmlText(htmlTrack) {
        if (!htmlTrack) return "";
        let decoded = htmlTrack
            .replace(/&amp;lt;/g, "<")
            .replace(/&amp;gt;/g, ">")
            .replace(/&lt;/g, "<")
            .replace(/&gt;/g, ">")
            .replace(/&amp;/g, "&")
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");

        try {
            const parser = new DOMParser();
            const dom = parser.parseFromString(decoded, "text/html");
            return dom.body.innerHTML || decoded;
        } catch (e) {
            return decoded;
        }
    }

    /* Hàm kiểm tra chuỗi có nội dung thực tế hay không */
    hasValidContent(text) {
        if (!text) return false;
        const decoded = this.decodeHtmlText(text);
        const clean = decoded.replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").trim();
        return clean.length > 0 && clean !== "Không có";
    }

    async loadAllPlanData() {
        const kehoachId = this.props.record.resId;
        if (!kehoachId) return;

        try {
            const linhVucLines = await this.orm.searchRead(
                "ekids.kehoach_linhvuc",
                [["kehoach_id", "=", kehoachId]],
                ["id", "linhvuc_id", "tuoi_id", "chuongtrinh_id", "sequence"],
                { order: "sequence asc, id asc" }
            );

            if (!linhVucLines.length) {
                this.state.groupedData = [];
                return;
            }

            const linhVucLineIds = linhVucLines.map((line) => line.id);

            const muctieus_returns = await this.orm.searchRead(
                "ekids.kehoach_muctieu",
                [["kehoach_linhvuc_id", "in", linhVucLineIds]],
                [
                    "id", "index", "name", "muctieu_id", "muctieu_them", "ghichu",
                    "kehoach_muctieu_thangtruoc_id", "sothang_da_chuyenttiep", "kehoach_linhvuc_id",
                    "chucnang", "thietke", "tieuchi_chuadat", "tieuchi_hinhthanh", "tieuchi_dat",
                    "is_bientap_temp", "is_readonly", "is_delete",
                    "ketqua_dat_lientiep_thangtruoc", "ketqua_hinhthanh_thangtruoc",
                    "solan_thu", "solan_thu_dat", "tyle_thu"
                ],
                { order: "sequence asc, id asc" }
            );

            this.state.groupedData = linhVucLines.map((line) => {
                const muctieus = muctieus_returns.filter((t) => t.kehoach_linhvuc_id[0] === line.id);

                muctieus.forEach((t) => {
                    t.has_chucnang = this.hasValidContent(t.chucnang);
                    t.has_thietke = this.hasValidContent(t.thietke);
                    t.has_tc1 = this.hasValidContent(t.tieuchi_chuadat);
                    t.has_tc2 = this.hasValidContent(t.tieuchi_hinhthanh);
                    t.has_tc3 = this.hasValidContent(t.tieuchi_dat);
                    t.has_tieuchi = t.has_tc1 || t.has_tc2 || t.has_tc3;

                    t.chucnang = t.has_chucnang ? markup(this.decodeHtmlText(t.chucnang)) : "";
                    t.thietke = t.has_thietke ? markup(this.decodeHtmlText(t.thietke)) : "";
                    t.tieuchi_chuadat = t.has_tc1 ? markup(this.decodeHtmlText(t.tieuchi_chuadat)) : "";
                    t.tieuchi_hinhthanh = t.has_tc2 ? markup(this.decodeHtmlText(t.tieuchi_hinhthanh)) : "";
                    t.tieuchi_dat = t.has_tc3 ? markup(this.decodeHtmlText(t.tieuchi_dat)) : "";

                    t.ghichu_clean = t.ghichu ? this.decodeHtmlText(t.ghichu).replace(/<[^>]*>/g, "").trim() : "";
                });

                if (this.state.collapsedLinhVuc[line.id] === undefined) {
                    this.state.collapsedLinhVuc[line.id] = false;
                }

                return {
                    kehoach_linhvuc_id: line.id,
                    linhvuc: line.linhvuc_id ? line.linhvuc_id[1] : "",
                    tuoi: line.tuoi_id ? line.tuoi_id[1] : "",
                    chuongtrinh: line.chuongtrinh_id ? line.chuongtrinh_id[1] : "",
                    is_readonly: line.is_readonly,
                    tong_muctieu: muctieus.length,
                    muctieus: muctieus,
                };
            });

        } catch (error) {
            console.error("Lỗi tải dữ liệu kế hoạch:", error);
        }
    }

    /* MỞ FORM VIEW POPUP BẰNG PYTHON ACTION */
    async openModalTyLeThu(targetId) {
        if (this.props.readonly) {
            this.notification.add("Kế hoạch đã khóa (Chỉ đọc), không thể điều chỉnh kết quả!", { type: "warning" });
            return;
        }

        try {
            const action = await this.orm.call(
                "ekids.kehoach_muctieu",
                "action_capnhat_tyle_thu",
                [targetId]
            );
            if (action) {
                this.actionService.doAction(action, {
                    onClose: async () => {
                        await this.loadAllPlanData();
                    },
                });
            }
        } catch (error) {
            console.error("Lỗi khi gọi action cập nhật tỷ lệ thử:", error);
        }
    }

    toggleLinhVucCollapse(lineId) {
        this.state.collapsedLinhVuc[lineId] = !this.state.collapsedLinhVuc[lineId];
    }

    toggleTargetDetail(targetId) {
        this.state.expandedTargets[targetId] = !this.state.expandedTargets[targetId];
    }

    async them_MucTieu_Vao_KeHoach_LinhVuc(lineId) {
        if (this.props.readonly) {
            this.notification.add("Kế hoạch đã khóa (Read-only), không thể thay đổi danh sách mục tiêu!", { type: "danger" });
            return;
        }
        try {
            const action = await this.orm.call("ekids.kehoach_linhvuc", "action_them_muctieu_vao_kehoach_linhvuc", [lineId]);
            if (action) {
                this.actionService.doAction(action, {
                    onClose: async () => { await this.loadAllPlanData(); },
                });
            }
        } catch (error) {
            console.error(error);
        }
    }

    async open_GV_TaoMoi_MucTieu(lineId) {
        if (this.props.readonly) {
            this.notification.add("Kế hoạch đã khóa (Read-only), không thể thay đổi danh sách mục tiêu!", { type: "danger" });
            return;
        }
        try {
            const action = await this.orm.call("ekids.kehoach_linhvuc", "action_gv_tu_taomoi_muctieu", [lineId]);
            if (action) {
                this.actionService.doAction(action, {
                    onClose: async () => { await this.loadAllPlanData(); },
                });
            }
        } catch (error) {
            console.error(error);
        }
    }

    async open_GV_BienTap_NoiDung_MucTieu(targetId) {
        if (this.props.readonly) {
            this.notification.add("Kế hoạch đã khóa (Read-only), không thể biên tập nội dung chuyên môn!", { type: "danger" });
            return;
        }
        try {
            const action = await this.orm.call("ekids.kehoach_muctieu", "action_giaovien_bientap_thietke_muctieu", [targetId]);
            if (action) {
                this.actionService.doAction(action, {
                    onClose: async () => {
                        await this.loadAllPlanData();
                    },
                });
            }
        } catch (error) {
            console.error("Lỗi khi gọi action biên tập mục tiêu:", error);
        }
    }

    toggleNoteInline(targetId) {
        this.state.activeNotes[targetId] = !this.state.activeNotes[targetId];
        if (this.state.activeNotes[targetId]) {
            this.state.expandedTargets[targetId] = true;
        }
    }

    async saveNoteInline(muctieu, ev) {
        if (ev) {
            ev.stopPropagation();
            ev.preventDefault();
        }

        let textarea = document.getElementById(`note_muctieu_${muctieu.id}`);
        if (!textarea && ev && ev.target) {
            const container = ev.target.closest('.note-container-box');
            textarea = container ? container.querySelector('.note-textarea-input') : null;
        }

        if (!textarea) {
            console.error("Không tìm thấy ô textarea ghi chú cho mục tiêu:", muctieu.id);
            return;
        }

        const valGhiChu = textarea.value.trim();

        try {
            await this.orm.write("ekids.kehoach_muctieu", [muctieu.id], {
                ghichu: valGhiChu,
            });

            muctieu.ghichu = valGhiChu;
            muctieu.ghichu_clean = valGhiChu;

            if (this.state.activeNotes) {
                this.state.activeNotes[muctieu.id] = false;
            }

            if (this.notification) {
                this.notification.add("Đã lưu ghi chú thành công!", { type: "success" });
            }
        } catch (error) {
            console.error("Lỗi khi lưu ghi chú mục tiêu:", error);
            if (this.notification) {
                this.notification.add("Không thể lưu ghi chú. Vui lòng thử lại!", { type: "danger" });
            }
        }
    }

    async removeTargetFromPlan(targetId) {
        if (this.props.readonly) {
            this.notification.add("Kế hoạch đã khóa, không cho phép xóa mục tiêu!", { type: "danger" });
            return;
        }
        if (confirm("Bạn có chắc chắn muốn bỏ chọn mục tiêu này khỏi kế hoạch không?")) {
            try {
                await this.orm.unlink("ekids.kehoach_muctieu", [targetId]);
                this.notification.add("Đã gỡ mục tiêu.", { type: "info" });
                await this.loadAllPlanData();
            } catch (error) {
                console.error(error);
            }
        }
    }
}

registry.category("fields").add("ekids_lap_kehoach", {
    component: LapKehoachWidget,
    supportedTypes: ["one2many"],
});
