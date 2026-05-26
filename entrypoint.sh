#!/usr/bin/env sh
set -e

# Wait for DB, create tables and admin user, then start the app
echo "--> Waiting for database and preparing application..."
python /app/wait_for_db.py
python /app/init_db.py
python /app/create_admin.py

echo "--> Starting server: $@"
exec "$@"
