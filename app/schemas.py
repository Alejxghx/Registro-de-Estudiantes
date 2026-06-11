"""Esquemas Pydantic para validación de entrada y salida de la API."""
from pydantic import BaseModel, EmailStr, Field


class EstudianteCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: EmailStr
    carrera: str = Field(min_length=2, max_length=100)
    semestre: int = Field(ge=1, le=12)


class Estudiante(EstudianteCrear):
    id: int
    creado_en: str
