FROM odoo:19.0

# Chuyển sang user root để cài đặt gói và phân quyền
USER root

# Cập nhật pip và cài đặt các thư viện Python bổ sung
# Thêm --no-cache-dir để giảm dung lượng image
RUN pip3 install --no-cache-dir --break-system-packages \
    lunardate \
    sympy

# Tạo thư mục data và phân quyền chính xác cho user odoo
RUN mkdir -p /var/lib/odoo \
    && chown -R odoo:odoo /var/lib/odoo

# Chuyển lại user odoo mặc định để chạy ứng dụng an toàn
USER odoo