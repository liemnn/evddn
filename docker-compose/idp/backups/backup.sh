#!/bin/bash
export PGPASSWORD='evddn@123!@#$%'
docker exec -e PGPASSWORD='evddn@123!@#$%' odoo-db pg_dump -U evddn -h localhost evddn > /opt/odoo18/backups/evddn_backup-$(date +%Y%m%d).sql
find /opt/odoo18/backups -type f -name "evddn_backup-*.sql*" -mtime +10 -exec rm {} \;
