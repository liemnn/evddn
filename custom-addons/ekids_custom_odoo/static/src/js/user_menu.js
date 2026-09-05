/** @odoo-module **/

// BẮT BUỘC: nạp các mục mặc định trước khi thao tác
import "@web/webclient/user_menu/user_menu_items";
import { registry } from "@web/core/registry";



const userMenu = registry.category("user_menuitems");

function trimAndTranslateUserMenu() {


    // Các key muốn loại bỏ
    const removeKeys = [
        "documentation",
        "support",
        "shortcuts",
        "odoo_account",
        "install_pwa",
        "onboarding",
    ];

    // Xóa menu thừa nếu tồn tại
    for (const key of removeKeys) {
        if (userMenu.contains(key)) {
            userMenu.remove(key);

        }

    }

    // Duyệt và dịch menu còn lại
    for (const [key, item] of userMenu.getEntries()) {
        if (!item) continue;

       // console.log("KEY:", key, "ITEM:", item);

        if (key === "profile") {

           item.description =  "Hồ sơ cá nhân";   // phải gán function
        }
        if (key === "log_out") {

            item.description = "Đăng xuất";
        }
        if (key === "onboarding") {
             item.description = "Trực tuyến(On)";   // phải gán function
        }
        if (key === "preferences") {
            item.description = "Hồ sơ cá nhân";
        }

    }


}

// Delay 1 chút cho chắc ăn (registry load xong)
setTimeout(trimAndTranslateUserMenu,1000);