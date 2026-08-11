/** @odoo-module **/

// 🌟 BỔ SUNG: Import thêm 'markup' để OWL Component chịu render định dạng HTML giàu định dạng
import { Component, useState, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CanThiepKehoachWidget extends Component {
    static template = "ekids_canthiep.CanThiepKeHoachWidgetTemplate";
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
            hasAnyTargetDone: false, // 🌟 MỚI: Biến kiểm tra trạng thái xem có mục tiêu nào đạt (trangthai === '1') chưa
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
                ["id", "linhvuc_id", "tuoi_id", "chuongtrinh_id", "tong_muctieu_dat"]
            );

            if (!linhVucLines.length) {
                this.state.groupedData = [];
                this.state.hasAnyTargetDone = false;
                return;
            }

            const linhVucLineIds = linhVucLines.map(line => line.id);

            const muctieus_returns = await this.orm.searchRead(
                "ekids.kehoach_muctieu",
                [["kehoach_linhvuc_id", "in", linhVucLineIds]],
                ["id"
                ,"index"
                ,"name"
                ,"muctieu_id"
                ,"muctieu_them"
                ,"ghichu"
                ,"kehoach_muctieu_thangtruoc_id"
                ,"sothang_da_chuyenttiep"
                ,"kehoach_linhvuc_id"
                ,"chucnang"
                ,"thietke"
                ,"tieuchi_chuadat"
                ,"tieuchi_hinhthanh"
                ,"tieuchi_dat"
                ,"trangthai"
                ,"trangthai_kiemduyet"
                ,"is_readonly"
                ,"is_canthiep"
                ,"is_kiemduyet"
                ,"ketqua_dat_lientiep_thangtruoc"
                ,"ketqua_hinhthanh_thangtruoc"
                ],
                { order: "sequence asc,id asc" }
            );

            // 🌟 MỚI: Kiểm tra xem trong toàn bộ danh sách trả về, có bất kỳ mục tiêu nào đã đạt (trangthai === '1') chưa
            this.state.hasAnyTargetDone = muctieus_returns.some(t => t.trangthai === '1');

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
                    tong_muctieu: muctieus.length,
                    tong_muctieu_dat: line.tong_muctieu_dat,
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
        try {
            const action = await this.orm.call("ekids.kehoach_linhvuc", "action_xem_danhsach_ct_muctieu", [lineId]);
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

    async onCanThiepClick(muctieu, event) {
        if (muctieu.trangthai !='0') {
            try {
                console.log("Kích hoạt can thiệp cho mục tiêu ID:", muctieu.id);

                // 1. Hứng lấy Action Object do hàm Python return về
                const action = await this.orm.call(
                    "ekids.kehoach_muctieu",
                    "action_canthiep",
                    [muctieu.id]
                );

                // 2. Kiểm tra nếu Python trả về một Action hợp lệ, dùng Action Service để ép mở Popup
                if (action) {
                    this.actionService.doAction(action, {
                        onClose: async () => {
                            // Hàm này tự trigger khi giáo viên đóng popup hoặc bấm lưu trên popup
                            await this.loadAllPlanData();
                        }
                    });
                }

            } catch (error) {
                console.error("Lỗi thực thi Action Can Thiệp:", error);
            }
        } else {
            alert("Kế hoạch chưa thể can thiệp !");
        }
    }

    async onMucTieuClick(muctieu,actionName, event) {
        if (muctieu.trangthai !='0') {
            try {
                console.log("Kích hoạt can thiệp cho mục tiêu ID:", muctieu.id);

                // 1. Hứng lấy Action Object do hàm Python return về
                const action = await this.orm.call(
                    "ekids.kehoach_muctieu",
                     actionName,
                    [muctieu.id]
                );

                // 2. Kiểm tra nếu Python trả về một Action hợp lệ, dùng Action Service để ép mở Popup
                if (action) {
                    this.actionService.doAction(action, {
                        onClose: async () => {
                            // Hàm này tự trigger khi giáo viên đóng popup hoặc bấm lưu trên popup
                            await this.loadAllPlanData();
                        }
                    });
                }

            } catch (error) {
                console.error("Lỗi thực thi Action Can Thiệp:", error);
            }
        } else {
            alert("Kế hoạch chưa thể can thiệp !");
        }
    }
}

registry.category("fields").add("ekids_canthiep_kehoach", {
    component: CanThiepKehoachWidget,
    supportedTypes: ["one2many"],
});