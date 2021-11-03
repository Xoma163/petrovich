#!/bin/bash
#
# Backup a Postgresql database into a daily file.
#

BACKUP_DIR=/mnt/NAS/NAS/backup/db
DAYS_TO_KEEP=31
FILE_SUFFIX=_pg_backup.sql

FILE=$(date +"%Y-%m-%d_%H-%M")${FILE_SUFFIX}
OUTPUT_FILE=${BACKUP_DIR}/${FILE}

# do the database backup (dump)
# use this command for a database server on localhost. add other options if need be.
pg_dump "$1" -F p -f "${OUTPUT_FILE}"

# gzip the mysql database dump file
gzip "$OUTPUT_FILE"

# show the user the result
echo "${OUTPUT_FILE}.gz was created:"
ls -l "${OUTPUT_FILE}.gz"

# prune old backups
find $BACKUP_DIR -maxdepth 1 -mtime +$DAYS_TO_KEEP -name "*${FILE_SUFFIX}.gz" -exec rm -rf '{}' ';'
