/** @odoo-module **/

// 1. Chặn chuột phải (Context Menu) trên toàn bộ trang
document.addEventListener('contextmenu', (e) => {
    // Không chặn trên các ô nhập liệu để người dùng vẫn paste được
    if (['INPUT', 'TEXTAREA'].includes(e.target.tagName) || e.target.isContentEditable) {
        return;
    }
    e.preventDefault();
}, true);

// 2. Chặn các phím tắt sao chép, xem mã nguồn, mở DevTools
document.addEventListener('keydown', (e) => {
    const key = e.key.toLowerCase();

    // Nếu đang trong ô nhập liệu thì cho phép Ctrl+C / Ctrl+V
    if (['INPUT', 'TEXTAREA'].includes(e.target.tagName) || e.target.isContentEditable) {
        return;
    }

    // Chặn Ctrl+C (Copy), Ctrl+U (Xem Source), Ctrl+S (Lưu trang), Ctrl+P (In), Ctrl+A (Chọn tất cả)
    if (e.ctrlKey && ['c', 'u', 's', 'p', 'a'].includes(key)) {
        e.preventDefault();
        e.stopPropagation();
        return false;
    }

    // Chặn F12 và Ctrl+Shift+I/J/C (Mở Developer Tools)
    if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && ['i', 'j', 'c'].includes(key))) {
        e.preventDefault();
        e.stopPropagation();
        return false;
    }
}, true);

// 3. Xóa dữ liệu khi cố tình thực hiện thao tác copy
document.addEventListener('copy', (e) => {
    if (['INPUT', 'TEXTAREA'].includes(e.target.tagName) || e.target.isContentEditable) {
        return;
    }
    e.preventDefault();
    if (e.clipboardData) {
        e.clipboardData.setData('text/plain', 'Nội dung thuộc bản quyền đơn vị can thiệp, không được sao chép.');
    }
}, true);