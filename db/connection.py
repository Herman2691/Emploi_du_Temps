# db/connection.py
import streamlit as st
import psycopg2
import psycopg2.pool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@st.cache_resource
def get_connection_pool():
    try:
        cfg = st.secrets["postgres"]
        pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=cfg["host"],
            port=int(cfg["port"]),
            dbname=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            sslmode=cfg.get("sslmode", "disable"),
            options="-c client_encoding=UTF8",
            connect_timeout=10,
        )
        return pool
    except Exception as e:
        st.error(f"❌ Impossible de se connecter à la base de données : {e}")
        return None


@contextmanager
def get_db():
    pool = get_connection_pool()
    if pool is None:
        raise ConnectionError("Pool de connexions non disponible.")
    conn = pool.getconn()
    try:
        conn.set_client_encoding("UTF8")
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def execute_query(sql: str, params=None, fetch: str = "all"):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch == "none":
                try:
                    return cur.fetchone()
                except Exception:
                    return None
            columns = [desc[0] for desc in cur.description] if cur.description else []
            if fetch == "one":
                row = cur.fetchone()
                return dict(zip(columns, row)) if row else None
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]


def execute_many(sql: str, params_list: list):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, params_list)
