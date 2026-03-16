#!/bin/sh
echo "=== Custom entrypoint.sh đã chạy ==="
# Chạy Odoo ở foreground
echo "=== Starting Odoo service ==="
exec odoo -c /etc/odoo/odoo.conf
