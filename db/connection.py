import os
import streamlit as st
import psycopg2
import psycopg2.pool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Répertoire racine du projet (db/ -> racine)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load_db_config():
    """Charge la config DB depuis st.secrets ou secrets.toml en fallback."""
    try:
        cfg = st.secrets["postgres"]
        return {
            "host":     cfg["host"],
            "port":     int(cfg["port"]),
            "dbname":   cfg["database"],
            "user":     cfg["user"],
            "password": cfg["password"],
            "sslmode":  cfg.get("sslmode", "require"),
        }
    except Exception:
        pass

    # Fallback : lire secrets.toml directement
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    secrets_path = os.path.join(_BASE_DIR, ".streamlit", "secrets.toml")
    with open(secrets_path, "rb") as f:
        data = tomllib.load(f)
    cfg = data["postgres"]
    return {
        "host":     cfg["host"],
        "port":     int(cfg["port"]),
        "dbname":   cfg["database"],
        "user":     cfg["user"],
        "password": cfg["password"],
        "sslmode":  cfg.get("sslmode", "require"),
    }


@st.cache_resource
def get_connection_pool():
    cfg = _load_db_config()
    pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        connect_timeout=10,
        **cfg,
    )
    return pool


@contextmanager
def get_db():
    try:
        pool = get_connection_pool()
    except Exception as e:
        st.error(f"Impossible de se connecter a la base de donnees : {e}")
        raise ConnectionError(f"Connexion impossible : {e}") from e
    conn = pool.getconn()
    try:
        conn.set_client_encoding("UTF8")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def execute_query(sql: str, params=None, fetch: str = "all"):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch == "none":
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
