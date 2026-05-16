import os

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    return psycopg2.connect(
        host=os.environ["PSQL_HOST"],
        port=os.environ.get("PSQL_PORT", "5432"),
        dbname=os.environ.get("PSQL_DATABASE", "bacula"),
        user=os.environ["PSQL_USER"],
        password=os.environ["PSQL_PASSWORD"],
        cursor_factory=RealDictCursor,
    )
