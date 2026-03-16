#!/bin/bash
set -e

# Kiểm tra DB đã init chưa
if [ ! -f /var/lib/odoo/.db_initialized ]; then
    echo "=== Initializing Odoo database ==="
    odoo -c /etc/odoo/odoo.conf -i base --without-demo=all --stop-after-init
    touch /var/lib/odoo/.db_initialized
fi

# Chạy Odoo ở foreground
echo "=== Starting Odoo service ==="
exec odoo -c /etc/odoo/odoo.conf
