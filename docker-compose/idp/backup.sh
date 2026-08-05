#!/bin/bash
while true; do
  now=$(date +%H:%M)
  if [ "$now" == "23:00" ]; then
    pg_dump -h db -U evddn evddn > /backups/evddn_backup-$(date +%Y%m%d).sql
    sleep 60   # chờ 1 phút để tránh chạy nhiều lần trong 1 phút
  fi
  sleep 30
done
