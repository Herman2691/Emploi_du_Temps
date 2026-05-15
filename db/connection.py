import os
import streamlit as st
import psycopg2
import psycopg2.pool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_db_config() -> dict:
    """Charge la config DB depuis st.secrets ou secrets.toml en fallback."""
    try:
        cfg = st.secrets["postgres"]
        base = {
            "host":     cfg["host"],
            "port":     int(cfg["port"]),
            "dbname":   cfg["database"],
            "user":     cfg["user"],
            "password": cfg["password"],
            "sslmode":  cfg.get("sslmode", "require"),
        }
    except Exception:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        secrets_path = os.path.join(_BASE_DIR, ".streamlit", "secrets.toml")
        with open(secrets_path, "rb") as f:
            data = tomllib.load(f)
        cfg = data["postgres"]
        base = {
            "host":     cfg["host"],
            "port":     int(cfg["port"]),
            "dbname":   cfg["database"],
            "user":     cfg["user"],
            "password": cfg["password"],
            "sslmode":  cfg.get("sslmode", "require"),
        }

    # Keepalives TCP : évite que Neon coupe les connexions inactives
    base.update({
        "connect_timeout":    10,
        "keepalives":         1,
        "keepalives_idle":    30,
        "keepalives_interval": 10,
        "keepalives_count":   5,
    })
    return base


@st.cache_resource
def get_connection_pool() -> psycopg2.pool.ThreadedConnectionPool:
    return psycopg2.pool.ThreadedConnectionPool(
        minconn=1, maxconn=10, **_load_db_config()
    )


def _is_alive(conn) -> bool:
    """Vérifie si une connexion du pool est encore utilisable côté serveur."""
    if conn is None or conn.closed != 0:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


@contextmanager
def get_db():
    pool = get_connection_pool()
    conn = None
    try:
        conn = pool.getconn()

        # Si Neon a fermé la connexion côté serveur, on en crée une fraîche
        if not _is_alive(conn):
            logger.warning("Connexion périmée détectée — reconnexion en cours…")
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
            conn = psycopg2.connect(**_load_db_config())

        conn.set_client_encoding("UTF8")
        yield conn
        conn.commit()

    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        raise

    finally:
        if conn is not None:
            try:
                if conn.closed == 0:
                    pool.putconn(conn)
                else:
                    pool.putconn(conn, close=True)
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass


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
