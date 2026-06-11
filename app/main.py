"""API de Registro de Estudiantes — Deploy en AWS.

Curso: 5to. Modelado Ágil del Software
"""
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import database
from app.schemas import Estudiante, EstudianteCrear


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(
    title="Registro de Estudiantes",
    description="API REST con FastAPI desplegada en AWS con CI/CD (GitHub Actions).",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/api/health", tags=["sistema"])
def health():
    return {"status": "ok"}


@app.get("/api/estudiantes", response_model=list[Estudiante], tags=["estudiantes"])
def listar_estudiantes():
    return database.listar_estudiantes()


@app.get("/api/estudiantes/{estudiante_id}", response_model=Estudiante, tags=["estudiantes"])
def obtener_estudiante(estudiante_id: int):
    estudiante = database.obtener_estudiante(estudiante_id)
    if estudiante is None:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return estudiante


@app.post("/api/estudiantes", response_model=Estudiante, status_code=201, tags=["estudiantes"])
def crear_estudiante(datos: EstudianteCrear):
    try:
        return database.crear_estudiante(
            datos.nombre, datos.correo, datos.carrera, datos.semestre
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="El correo ya está registrado")


@app.delete("/api/estudiantes/{estudiante_id}", status_code=204, tags=["estudiantes"])
def eliminar_estudiante(estudiante_id: int):
    if not database.eliminar_estudiante(estudiante_id):
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")


# Frontend: formulario de registro servido como archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse("static/index.html")
