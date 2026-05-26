import os
import time
import sys

DATABASE_URL = os.getenv('DATABASE_URL')

def wait_for_postgres(dsn, timeout=60):
    import psycopg2
    start = time.time()
    while True:
        try:
            conn = psycopg2.connect(dsn)
            conn.close()
            print("✓ Connected to Postgres")
            return True
        except Exception as e:
            if time.time() - start > timeout:
                print(f"Timed out waiting for database: {e}")
                return False
            print("Waiting for database...", end="\r")
            time.sleep(2)

if __name__ == '__main__':
    if not DATABASE_URL:
        print("No DATABASE_URL set, assuming SQLite or other local DB. Skipping wait.")
        sys.exit(0)

    ok = wait_for_postgres(DATABASE_URL, timeout=120)
    if not ok:
        sys.exit(1)
