#!/bin/bash
export PGPASSWORD='ERP@123!@#'
docker exec -e PGPASSWORD='ERP@123!@#' postgres pg_dump -U erp -h localhost erp > /opt/erp/backups/erp_backup-$(date +%Y%m%d).sql
find /opt/erp/backups -type f -name "erp_backup-*.sql*" -mtime +60 -exec rm {} \;
