# Registro de Estudiantes — Deploy en AWS

Proyecto del curso **5to. Modelado Ágil del Software**.

API REST construida con **FastAPI** desplegada en **AWS EC2** (backend), frontend desplegado en **Google Cloud Run**, y **CI/CD mediante GitHub Actions**.

## Arquitectura

```
Navegador
   │
   ▼
Cloud Run (frontend: nginx + formulario)
   │  fetch() a la API
   ▼
CloudFront (HTTPS) ──► EC2 (backend: FastAPI + SQLite, puerto 8000)
```

- **Frontend**: formulario para registrar estudiantes y tabla con los registros (`frontend/`), servido por nginx en Cloud Run.
- **API** (`/docs` para Swagger):
  - `GET /api/health` — estado del servicio
  - `GET /api/estudiantes` — listar estudiantes
  - `GET /api/estudiantes/{id}` — obtener un estudiante
  - `POST /api/estudiantes` — registrar estudiante
  - `DELETE /api/estudiantes/{id}` — eliminar estudiante
- **Base de datos**: SQLite (archivo en la propia EC2).
- **CI/CD**: en cada push a `main`, GitHub Actions ejecuta las pruebas y, si pasan, despliega el backend en EC2 y el frontend en Cloud Run.

## Ejecutar en local

En local no necesitas nada de la nube: FastAPI sirve también el frontend.

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

## Despliegue — Paso 1: Backend en AWS EC2

### Crear la instancia

1. Consola de AWS → **EC2** → **Launch instance**.
2. Nombre: `registro-estudiantes`. AMI: **Ubuntu Server 24.04 LTS**. Tipo: **t2.micro** o **t3.micro** (capa gratuita).
3. Crear un **key pair** (descarga el `.pem`, lo necesitarás para los secrets).
4. En **Security Group**, permitir tráfico entrante:
   - SSH (puerto 22) — tu IP
   - Custom TCP (puerto 8000) — `0.0.0.0/0`

### Configurar el servidor

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

Verificar: `http://IP_PUBLICA_EC2:8000/api/health`

## Despliegue — Paso 2: HTTPS para la API con CloudFront

⚠️ **Este paso es obligatorio en esta arquitectura.** Cloud Run sirve el frontend por **HTTPS**, y los navegadores bloquean las peticiones desde una página HTTPS hacia una API **HTTP** ("mixed content"). CloudFront pone HTTPS delante de la EC2 sin necesidad de comprar dominio ni certificado.

1. Consola de AWS → **CloudFront** → **Create distribution**.
2. **Origin domain**: el DNS público de tu EC2 (ej. `ec2-54-123-45-67.compute-1.amazonaws.com`).
3. **Protocol**: HTTP only, puerto **8000**.
4. **Viewer protocol policy**: Redirect HTTP to HTTPS.
5. **Allowed HTTP methods**: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE (necesario para el formulario).
6. **Cache policy**: `CachingDisabled` (es una API, no debe cachearse).
7. Crear y esperar a que despliegue. Obtendrás una URL tipo `https://d1234abcd.cloudfront.net`.

Verificar: `https://TU_DISTRIBUCION.cloudfront.net/api/health`

## Despliegue — Paso 3: Frontend en Google Cloud Run

### Conectar el frontend con la API

Editar **una línea** en `frontend/script.js` con la URL de CloudFront:

```js
const API_BASE = "https://TU_DISTRIBUCION.cloudfront.net";
```

Hacer commit y push de ese cambio.

### Primer despliegue (manual)

1. Crear un proyecto en <https://console.cloud.google.com> y habilitar facturación (Cloud Run tiene capa gratuita generosa).
2. Instalar [gcloud CLI](https://cloud.google.com/sdk/docs/install) y ejecutar `gcloud init`.
3. Desde la raíz del proyecto:

```bash
gcloud run deploy registro-frontend --source frontend --region us-central1 --allow-unauthenticated
```

Al terminar te dará la URL pública del frontend (ej. `https://registro-frontend-xxxx-uc.a.run.app`). **Esa URL es la que entregas en la tarea.**

## Despliegue — Paso 4: CI/CD con GitHub Actions

En el repositorio de GitHub → **Settings** → **Secrets and variables** → **Actions**, crear estos secrets:

| Secret | Valor |
|---|---|
| `EC2_HOST` | IP pública de la instancia EC2 |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Contenido completo del archivo `.pem` |
| `GCP_PROJECT_ID` | ID del proyecto de Google Cloud |
| `GCP_SA_KEY` | JSON de una service account de GCP |

Para crear la service account de GCP: consola → **IAM y administración** → **Cuentas de servicio** → crear con los roles **Cloud Run Admin**, **Cloud Build Editor**, **Service Account User** y **Storage Admin** → **Claves** → crear clave JSON y pegar su contenido en el secret.

Para que `systemctl restart` no pida contraseña en la EC2, ejecutar `sudo visudo` y agregar al final:

```
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart registro-estudiantes
```

A partir de ahí, cada `git push` a `main`:

1. **CI**: ejecuta las pruebas con pytest.
2. **CD**: si pasan, despliega en paralelo el backend (SSH a EC2) y el frontend (Cloud Run).

## Estructura del proyecto

```
├── app/
│   ├── main.py        # Aplicación FastAPI y endpoints (con CORS)
│   ├── database.py    # Acceso a SQLite
│   └── schemas.py     # Validación con Pydantic
├── frontend/          # Frontend (formulario + tabla)
│   ├── Dockerfile     # Contenedor nginx para Cloud Run
│   └── nginx.conf
├── tests/             # Pruebas con pytest
├── deploy/            # Servicio systemd para EC2
└── .github/workflows/ # Pipeline CI/CD (pruebas + 2 despliegues)
```
