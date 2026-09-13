#!/bin/sh
set -e
echo "=== Custom entrypoint.sh running ==="
exec /usr/bin/odoo -c /etc/odoo/odoo.conf
