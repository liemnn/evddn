FROM odoo:18.0

# Ensure correct permissions for Odoo data and config
USER root

# Gộp lệnh cài đặt thư viện, tăng timeout và dùng mirror server tốc độ cao tránh nghẽn mạng
RUN pip3 install --break-system-packages \
    --default-timeout=1000 \
    --retries 5 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    lunardate \
    sympy

RUN mkdir -p /var/lib/odoo \
    && chown -R odoo:odoo /var/lib/odoo

# Switch back to odoo user
USER odoo