"""Pruebas de la API de Registro de Estudiantes."""
import os

import pytest
from fastapi.testclient import TestClient

os.environ["DB_PATH"] = "test_estudiantes.db"

from app.main import app  # noqa: E402


@pytest.fixture()
def cliente():
    if os.path.exists("test_estudiantes.db"):
        os.remove("test_estudiantes.db")
    with TestClient(app) as cliente_pruebas:
        yield cliente_pruebas
    if os.path.exists("test_estudiantes.db"):
        os.remove("test_estudiantes.db")


ESTUDIANTE = {
    "nombre": "Ana Pérez",
    "correo": "ana@ejemplo.com",
    "carrera": "Ingeniería de Software",
    "semestre": 5,
}


def test_health(cliente):
    respuesta = cliente.get("/api/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_lista_vacia_al_inicio(cliente):
    respuesta = cliente.get("/api/estudiantes")
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_crear_estudiante(cliente):
    respuesta = cliente.post("/api/estudiantes", json=ESTUDIANTE)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["nombre"] == ESTUDIANTE["nombre"]
    assert datos["correo"] == ESTUDIANTE["correo"]
    assert datos["id"] == 1


def test_correo_duplicado_devuelve_409(cliente):
    cliente.post("/api/estudiantes", json=ESTUDIANTE)
    respuesta = cliente.post("/api/estudiantes", json=ESTUDIANTE)
    assert respuesta.status_code == 409


def test_correo_invalido_devuelve_422(cliente):
    invalido = {**ESTUDIANTE, "correo": "no-es-un-correo"}
    respuesta = cliente.post("/api/estudiantes", json=invalido)
    assert respuesta.status_code == 422


def test_semestre_fuera_de_rango_devuelve_422(cliente):
    invalido = {**ESTUDIANTE, "semestre": 20}
    respuesta = cliente.post("/api/estudiantes", json=invalido)
    assert respuesta.status_code == 422


def test_obtener_estudiante(cliente):
    cliente.post("/api/estudiantes", json=ESTUDIANTE)
    respuesta = cliente.get("/api/estudiantes/1")
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == ESTUDIANTE["nombre"]


def test_obtener_inexistente_devuelve_404(cliente):
    respuesta = cliente.get("/api/estudiantes/999")
    assert respuesta.status_code == 404


def test_eliminar_estudiante(cliente):
    cliente.post("/api/estudiantes", json=ESTUDIANTE)
    respuesta = cliente.delete("/api/estudiantes/1")
    assert respuesta.status_code == 204
    assert cliente.get("/api/estudiantes").json() == []


def test_eliminar_inexistente_devuelve_404(cliente):
    respuesta = cliente.delete("/api/estudiantes/999")
    assert respuesta.status_code == 404


def test_frontend_disponible(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert "Registro de Estudiantes" in respuesta.text
