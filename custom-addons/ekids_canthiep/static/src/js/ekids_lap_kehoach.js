/** @odoo-module **/

// 🌟 BỔ SUNG: Import thêm 'markup' để OWL Component chịu render định dạng HTML giàu định dạng
import { Component, useState, onWillStart, markup } from "@odoo/owl";
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

        this.state = useState({
            groupedData: [],
            activeNotes: {},
            collapsedLinhVuc: {},
            expandedTargets: {},
        });

        onWillStart(async () => {
            await this.loadAllPlanData();
        });
    }

    /* 🌟 HÀM PHỤ TRỢ CHUẨN: Giải mã các ký tự thực thể HTML lồng nhau */
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
            const dom = parser.parseFromString(decoded, 'text/html');
            return dom.body.innerHTML || decoded;
        } catch (e) {
            return decoded;
        }
    }

    async loadAllPlanData() {
        const kehoachId = this.props.record.resId;
        if (!kehoachId) return;

        try {
            const linhVucLines = await this.orm.searchRead(
                "ekids.kehoach_linhvuc",
                [["kehoach_id", "=", kehoachId]],
                ["id", "linhvuc_id", "tuoi_id", "chuongtrinh_id"]
            );

            if (!linhVucLines.length) {
                this.state.groupedData = [];
                return;
            }

            const linhVucLineIds = linhVucLines.map(line => line.id);

            const muctieus_returns = await this.orm.searchRead(
                "ekids.kehoach_muctieu",
                [["kehoach_linhvuc_id", "in", linhVucLineIds]],
                ["id"
                ,"index"
                ,"muctieu_id"
                ,"ghichu"
                ,"kehoach_muctieu_thangtruoc_id"
                ,"sothang_da_chuyenttiep"
                ,"kehoach_linhvuc_id"
                ,"chucnang"
                ,"thietke"
                ,"tieuchi_chuadat"
                ,"tieuchi_hinhthanh"
                ,"tieuchi_dat"
                ,"is_readonly"
                ,"is_delete"
                ],
                { order: "sequence asc" }
            );

            this.state.groupedData = linhVucLines.map(line => {
                const muctieus = muctieus_returns.filter(t => t.kehoach_linhvuc_id[0] === line.id);

                muctieus.forEach(t => {
                    // 🌟 MẤU CHỐT: Bọc hàm decode vào markup() để thông báo cho OWL render đúng format HTML
                    t.chucnang = markup(this.decodeHtmlText(t.chucnang) || 'Không có');
                    t.thietke = markup(this.decodeHtmlText(t.thietke) || 'Không có');
                    t.tieuchi_chuadat = markup(this.decodeHtmlText(t.tieuchi_chuadat) || 'Chưa định nghĩa tiêu chí chưa đạt.');
                    t.tieuchi_hinhthanh = markup(this.decodeHtmlText(t.tieuchi_hinhthanh) || 'Chưa định nghĩa tiêu chí đang hình thành.');
                    t.tieuchi_dat = markup(this.decodeHtmlText(t.tieuchi_dat) || 'Chưa định nghĩa tiêu chí đạt.');

                    if (t.ghichu) {
                        t.ghichu_clean = this.decodeHtmlText(t.ghichu)
                            .replace(/<[^>]*>/g, '')
                            .trim();
                    } else {
                        t.ghichu_clean = '';
                    }
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
                    muctieus: muctieus
                };
            });

        } catch (error) {
            console.error("Lỗi đồng bộ cấu trúc dữ liệu phẳng:", error);
        }
    }

    toggleLinhVucCollapse(lineId) {
        this.state.collapsedLinhVuc[lineId] = !this.state.collapsedLinhVuc[lineId];
    }

    toggleTargetDetail(targetId) {
        this.state.expandedTargets[targetId] = !this.state.expandedTargets[targetId];
    }

    async openAddTargetWizard(lineId) {
        // 🌟 CHỐT CHẶN 1: Nếu form đang readonly, chặn không cho mở Wizard thêm/xóa mục tiêu
        if (this.props.readonly) {
            this.notification.add("Kế hoạch đã khóa (Read-only), không thể thay đổi danh sách mục tiêu!", { type: "danger" });
            return;
        }

        try {
            const action = await this.orm.call("ekids.kehoach_linhvuc", "action_them_muctieu_vao_kehoach_linhvuc", [lineId]);
            if (action) {
                this.actionService.doAction(action, {
                    onClose: async () => { await this.loadAllPlanData(); }
                });
            }
        } catch (error) {
            console.error(error);
        }
    }

    toggleNoteInline(targetId) {
        this.state.activeNotes[targetId] = !this.state.activeNotes[targetId];
        if (this.state.activeNotes[targetId]) {
            this.state.expandedTargets[targetId] = true;
        }
    }

    async saveNoteInline(target, event) {
        // 🌟 CHỐT CHẶN 2: Chặn tuyệt đối hành động ghi đè dữ liệu Note nếu đang xem bản ghi dạng chỉ đọc
        if (this.props.readonly) {
            this.notification.add("Không thể lưu ghi chú do kế hoạch đã ở trạng thái chỉ đọc!", { type: "danger" });
            return;
        }

        try {
            const textarea = event.target.closest('.inline-note-box').querySelector('.note-textarea');
            let newNote = textarea.value;

            if (newNote) {
                newNote = newNote.replace(/<\/?[^>]+(>|$)/g, "").trim();
            }

            await this.orm.write("ekids.kehoach_muctieu", [target.id], { ghichu: newNote });

            target.ghichu = newNote;
            target.ghichu_clean = newNote;

            this.state.activeNotes[target.id] = false;
            this.notification.add("Đã cập nhật nhật ký tiến độ mục tiêu thô sạch!", { type: "success" });

            await this.loadAllPlanData();
        } catch (error) {
            console.error(error);
        }
    }

    async removeTargetFromPlan(targetId) {
        // 🌟 CHỐT CHẶN 3: Chặn hành động xóa mục tiêu ra khỏi kế hoạch khi form đang khóa
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