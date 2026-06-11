# Guía para explicar el proyecto: Registro de Estudiantes

> Resumen de estudio para explicar la arquitectura, el despliegue y el CI/CD del proyecto.

---

## 1. ¿Qué construí? (la idea en 30 segundos)

Una aplicación web de **registro de estudiantes** dividida en dos partes que viven en nubes distintas:

- **Backend**: una API REST hecha con **FastAPI** (Python) que guarda los datos, desplegada en **AWS**.
- **Frontend**: una página web con un formulario que consume esa API, desplegada en **Google Cloud Run**.
- **CI/CD**: cada vez que subo código a GitHub, las pruebas corren solas y los dos despliegues se actualizan **automáticamente**, sin tocar ningún servidor a mano.

```
Navegador del usuario
      │
      ▼
Cloud Run (Google) ── el frontend: formulario HTML/CSS/JS servido por nginx
      │  fetch() HTTPS
      ▼
CloudFront (AWS) ──── le da HTTPS a la API
      │
      ▼
EC2 (AWS) ─────────── el backend: FastAPI + SQLite, puerto 8000
```

---

## 2. El Backend en AWS

### ¿Qué es FastAPI?

Un framework de Python para construir APIs REST. Lo elegí porque:
- Valida los datos automáticamente con **Pydantic** (por ejemplo, rechaza correos inválidos o semestres fuera de 1-12 con un error 422).
- Genera **documentación interactiva sola** (Swagger, en `/docs`).
- Es rápido y moderno (asíncrono).

La API expone 5 endpoints: salud del servicio (`GET /api/health`), listar, obtener, crear y eliminar estudiantes. Los datos se guardan en **SQLite**, una base de datos en un solo archivo — suficiente para esta escala y sin necesidad de instalar un motor aparte.

### ¿Qué es EC2?

**EC2 (Elastic Compute Cloud)** es el servicio de AWS de **máquinas virtuales**: alquilas una computadora en sus centros de datos. Usé una instancia **t3.micro** (capa gratuita) con **Ubuntu Linux**.

Pasos que hice en la EC2:
1. Configuré el **grupo de seguridad** (el firewall de AWS): abrí el puerto 22 (SSH, para administrar) y el 8000 (donde escucha la API).
2. Me conecté por **SSH** con una clave privada (`.pem`).
3. Cloné el repositorio de GitHub, creé un entorno virtual de Python e instalé las dependencias.
4. Registré la API como **servicio de systemd**: así Linux la mantiene corriendo siempre, la reinicia si se cae y la arranca sola si el servidor se reinicia.

### ¿Qué es CloudFront y por qué lo necesité?

**CloudFront** es la CDN de AWS, pero aquí lo usé con un propósito específico: **darle HTTPS a mi API**.

El problema que resuelve se llama **contenido mixto (mixed content)**: Cloud Run sirve mi frontend por HTTPS, y los navegadores **bloquean** que una página HTTPS haga peticiones a una API HTTP (insegura). Mi EC2 solo hablaba HTTP. CloudFront se pone delante: recibe las peticiones por **HTTPS** con su propio certificado y las reenvía a la EC2 por HTTP al puerto 8000. Lo configuré sin caché (es una API, los datos deben estar siempre frescos) y permitiendo todos los métodos HTTP (POST, DELETE, etc.).

---

## 3. El Frontend en Cloud Run

### ¿Qué es el frontend aquí?

HTML, CSS y JavaScript puros (sin framework): un formulario que hace `fetch()` a la API para crear, listar y eliminar estudiantes. La URL de la API está en una constante (`API_BASE`) que apunta a CloudFront.

### ¿Qué es Cloud Run?

Es el servicio **serverless de contenedores** de Google Cloud: tú le das un **contenedor Docker** y él lo ejecuta, le pone una URL HTTPS pública, lo escala solo (incluso a cero cuando nadie lo usa — por eso es casi gratis) y no administras ningún servidor.

Mi contenedor es muy simple (está en `frontend/Dockerfile`): una imagen de **nginx** (un servidor web ligero) que sirve los 3 archivos estáticos en el puerto 8080, que es el que Cloud Run espera.

### ¿Por qué separar frontend y backend?

- Cada parte **escala y se despliega de forma independiente**: puedo cambiar el diseño de la página sin tocar el servidor de datos, y viceversa.
- Es la arquitectura real de la industria (el frontend en una CDN/serverless, la API en su propio servicio).
- Obliga a resolver problemas reales de integración: **CORS** y **HTTPS** (ver sección 5).

---

## 4. CI/CD: qué es y cómo lo apliqué

### Los conceptos

- **CI (Integración Continua)**: cada vez que se sube código al repositorio, se ejecutan **pruebas automáticas** que verifican que nada se rompió. Si fallan, el código malo no llega a producción.
- **CD (Despliegue Continuo)**: si las pruebas pasan, el código se **despliega automáticamente** a los servidores, sin pasos manuales.

El beneficio: se elimina el "en mi máquina funciona" y los despliegues a mano (lentos y propensos a errores). Cada `git push` deja la aplicación actualizada en producción en minutos.

### Mi pipeline (dos sistemas en paralelo)

Cuando hago `git push` a la rama `main` de GitHub:

**1. GitHub Actions** (definido en `.github/workflows/ci-cd.yml`):
   - **Job de pruebas (CI)**: levanta una máquina Ubuntu limpia, instala Python y las dependencias, y corre las **11 pruebas de pytest** (verifican cada endpoint: creación, duplicados, validaciones, errores 404...).
   - **Job de despliegue (CD)**: solo si las pruebas pasaron, se conecta **por SSH a la EC2**, hace `git pull`, actualiza dependencias y reinicia el servicio. Las credenciales (IP, usuario, clave SSH) están guardadas como **secrets** de GitHub: cifradas, nunca expuestas en el código.

**2. Cloud Build** (integración de Cloud Run con GitHub):
   - Google detecta el push, **reconstruye el contenedor** del frontend con el Dockerfile y lo **redespliega** en Cloud Run automáticamente.

```
git push a main
   ├── GitHub Actions ── pytest ✅ ──► SSH a EC2 ──► backend actualizado
   └── Cloud Build ──── docker build ──► Cloud Run ──► frontend actualizado
```

---

## 5. Problemas reales que tuve que resolver (por si preguntan)

1. **Contenido mixto (HTTPS → HTTP bloqueado)**: el frontend HTTPS no podía llamar a la API HTTP. **Solución**: CloudFront como capa HTTPS delante de la EC2.

2. **CORS**: por seguridad, los navegadores bloquean peticiones entre dominios distintos (mi frontend en `*.run.app` llamando a `*.cloudfront.net`). **Solución**: habilitar el middleware de CORS en FastAPI para que la API declare qué orígenes acepta.

3. **Pruebas que pasaban local pero fallaban en CI**: el CI ejecutaba `pytest` sin tener el proyecto en el path de Python y no encontraba el paquete `app`. **Solución**: un `conftest.py` en la raíz del proyecto.

4. **Puertos cerrados**: por defecto AWS bloquea todo; hubo que abrir explícitamente los puertos 22 y 8000 en el grupo de seguridad.

---

## 6. Chuleta de términos

| Término | Qué es en una frase |
|---|---|
| **API REST** | Interfaz para que programas se comuniquen por HTTP con verbos estándar (GET, POST, DELETE...) |
| **FastAPI** | Framework de Python para construir APIs con validación y documentación automáticas |
| **EC2** | Máquinas virtuales de AWS |
| **Grupo de seguridad** | Firewall de AWS que define qué puertos están abiertos |
| **systemd** | Sistema de Linux que mantiene servicios corriendo permanentemente |
| **CloudFront** | CDN de AWS; aquí, la capa HTTPS delante de la API |
| **Contenedor (Docker)** | Paquete con la aplicación y todo lo que necesita para correr igual en cualquier lado |
| **Cloud Run** | Servicio de Google que ejecuta contenedores sin administrar servidores |
| **nginx** | Servidor web ligero que sirve los archivos del frontend |
| **CI/CD** | Pruebas y despliegues automáticos en cada cambio de código |
| **GitHub Actions** | El sistema de automatización (pipelines) de GitHub |
| **Secrets** | Credenciales cifradas que el pipeline usa sin exponerlas en el código |
| **CORS** | Mecanismo del navegador que controla peticiones entre dominios distintos |
| **Mixed content** | Bloqueo del navegador a recursos HTTP dentro de páginas HTTPS |

---

## 7. URLs del proyecto

- **Frontend (la entrega)**: https://registro-de-estudiantes-frontend-327379982878.us-south1.run.app
- **API + Swagger**: https://d3cgsyx6f70cts.cloudfront.net/docs
- **Repositorio**: https://github.com/Alejxghx/Registro-de-Estudiantes

**Demo sugerida**: abrir el frontend → registrar un estudiante → mostrar que aparece en la tabla → abrir el Swagger y mostrar el mismo dato con `GET /api/estudiantes` → enseñar la pestaña Actions de GitHub con el pipeline en verde.
