#!/bin/bash

# Backup directory
BACKUP_DIR="./backups"
# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup database
DATABASE_CONFIG="../config/database.json"
DATABASE_NAME=$(jq -r '.database' $DATABASE_CONFIG)
BACKUP_FILE="$BACKUP_DIR/${DATABASE_NAME}_backup_$(date +%Y%m%d%H%M%S).sql"

# Command to dump the database (adjust as necessary for your database system)
# Example for PostgreSQL
pg_dump $DATABASE_NAME > $BACKUP_FILE

# Backup workflow configurations
WORKFLOW_CONFIG="../workflows/howard-county-n8n-workflow.json"
cp $WORKFLOW_CONFIG $BACKUP_DIR

echo "Backup completed successfully. Files are stored in $BACKUP_DIR."