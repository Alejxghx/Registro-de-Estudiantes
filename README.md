# Registro de Estudiantes — Deploy en AWS

Proyecto del curso **5to. Modelado Ágil del Software**.

API REST construida con **FastAPI** (backend) + formulario web (frontend), desplegada en **AWS EC2** con **CI/CD mediante GitHub Actions**.

## Funcionalidad

- **Frontend** (`/`): formulario para registrar estudiantes y tabla con los registros.
- **API** (`/docs` para Swagger):
  - `GET /api/health` — estado del servicio
  - `GET /api/estudiantes` — listar estudiantes
  - `GET /api/estudiantes/{id}` — obtener un estudiante
  - `POST /api/estudiantes` — registrar estudiante
  - `DELETE /api/estudiantes/{id}` — eliminar estudiante
- **Base de datos**: SQLite.
- **CI/CD**: en cada push a `main`, GitHub Actions ejecuta las pruebas y, si pasan, despliega automáticamente en EC2.

## Ejecutar en local

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir <http://localhost:8000> (frontend) y <http://localhost:8000/docs> (API).

Ejecutar pruebas:

```bash
pytest -v
```

## Despliegue en AWS (EC2)

### 1. Crear la instancia

1. En la consola de AWS → **EC2** → **Launch instance**.
2. Nombre: `registro-estudiantes`. AMI: **Ubuntu Server 24.04 LTS**. Tipo: **t2.micro** o **t3.micro** (capa gratuita).
3. Crear un **key pair** (descarga el `.pem`, lo necesitarás para los secrets).
4. En **Security Group**, permitir tráfico entrante:
   - SSH (puerto 22) — tu IP
   - Custom TCP (puerto 8000) — `0.0.0.0/0`

### 2. Configurar el servidor

Conectarse por SSH y ejecutar:

```bash
sudo apt update && sudo apt install -y python3-venv git
git clone https://github.com/TU_USUARIO/Proyect_arquitectura.git
cd Proyect_arquitectura
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Instalar el servicio para que la API corra siempre (y arranque sola si la instancia se reinicia):

```bash
sudo cp deploy/registro-estudiantes.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now registro-estudiantes
```

Verificar: `http://IP_PUBLICA_EC2:8000`

### 3. Configurar CI/CD (GitHub Actions)

En el repositorio de GitHub → **Settings** → **Secrets and variables** → **Actions**, crear estos secrets:

| Secret | Valor |
|---|---|
| `EC2_HOST` | IP pública de la instancia EC2 |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Contenido completo del archivo `.pem` |

Para que `systemctl restart` no pida contraseña, en el servidor ejecutar `sudo visudo` y agregar al final:

```
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart registro-estudiantes
```

A partir de ahí, cada `git push` a `main`:

1. **CI**: ejecuta las pruebas con pytest.
2. **CD**: si pasan, se conecta a EC2, actualiza el código y reinicia el servicio.

## Estructura del proyecto

```
├── app/
│   ├── main.py        # Aplicación FastAPI y endpoints
│   ├── database.py    # Acceso a SQLite
│   └── schemas.py     # Validación con Pydantic
├── static/            # Frontend (formulario + tabla)
├── tests/             # Pruebas con pytest
├── deploy/            # Servicio systemd para EC2
└── .github/workflows/ # Pipeline CI/CD
```
