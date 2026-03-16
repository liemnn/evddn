FROM odoo:18.0
# Ensure correct permissions for Odoo data and config
USER root
RUN pip3 install --break-system-packages lunardate
RUN pip3 install --break-system-packages sympy
RUN mkdir -p /var/lib/odoo \
    && chown -R odoo:odoo /var/lib/odoo


# Switch back to odoo user
USER odoo




