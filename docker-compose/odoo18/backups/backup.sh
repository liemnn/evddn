#docker exec -e PGPASSWORD='evddn@123!@#$%' odoo-db pg_dump -U evddn -h localhost evddn > /opt/odoo18/backups/evddn_backup-$(date +%Y%m%d).sql

#!/bin/bash
# Thi?t l?p thông tin k?t n?i và du?ng d?n
BACKUP_DIR="/opt/odoo18/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/evddn_backup-$TIMESTAMP.sql"

# 1. Th?c hi?n backup d?ng nén custom c?a postgres d? file nh? và an toàn nh?t
docker exec -e PGPASSWORD='evddn@123!@#$%' odoo-db pg_dump -U evddn -h localhost -Fc evddn > "$BACKUP_FILE"

# 2. Xóa các file backup cu hon 10 ngày d? gi?i phóng dung lu?ng ? c?ng
find "$BACKUP_DIR" -type f -name "evddn_backup-*.sql*" -mtime +10 -exec rm {} \;

