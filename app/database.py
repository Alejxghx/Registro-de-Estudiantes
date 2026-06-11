"""Acceso a la base de datos SQLite para el registro de estudiantes."""
import os
import sqlite3
from contextlib import closing

DB_PATH = os.environ.get("DB_PATH", "estudiantes.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    # closing() cierra la conexión al salir; el "with conn" interno confirma la transacción
    with closing(get_connection()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS estudiantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE,
                carrera TEXT NOT NULL,
                semestre INTEGER NOT NULL,
                creado_en TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def listar_estudiantes() -> list[dict]:
    with closing(get_connection()) as conn:
        filas = conn.execute(
            "SELECT * FROM estudiantes ORDER BY id DESC"
        ).fetchall()
    return [dict(fila) for fila in filas]


def obtener_estudiante(estudiante_id: int) -> dict | None:
    with closing(get_connection()) as conn:
        fila = conn.execute(
            "SELECT * FROM estudiantes WHERE id = ?", (estudiante_id,)
        ).fetchone()
    return dict(fila) if fila else None


def crear_estudiante(nombre: str, correo: str, carrera: str, semestre: int) -> dict:
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO estudiantes (nombre, correo, carrera, semestre) VALUES (?, ?, ?, ?)",
            (nombre, correo, carrera, semestre),
        )
        nuevo_id = cursor.lastrowid
    estudiante = obtener_estudiante(nuevo_id)
    assert estudiante is not None
    return estudiante


def eliminar_estudiante(estudiante_id: int) -> bool:
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute(
            "DELETE FROM estudiantes WHERE id = ?", (estudiante_id,)
        )
    return cursor.rowcount > 0
