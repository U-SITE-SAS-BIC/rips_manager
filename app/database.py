import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rips_manager.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            query_type TEXT NOT NULL CHECK(query_type IN ('terceros','transaccion')),
            query_text TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS envios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tipo TEXT NOT NULL CHECK(tipo IN ('terceros','transaccion')),
            factura TEXT,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            pacientes_count INTEGER DEFAULT 0,
            servicios_count INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pendiente',
            json_enviado TEXT,
            respuesta_api TEXT,
            codigo_cuv TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()
