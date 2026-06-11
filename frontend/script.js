// Si el frontend se aloja separado del backend (S3, Cloud Run, etc.),
// poner aquí la URL pública de la API, p. ej. "http://IP_EC2:8000"
const API_BASE = "";

const API = `${API_BASE}/api/estudiantes`;

const formulario = document.getElementById("formulario");
const lista = document.getElementById("lista-estudiantes");
const mensaje = document.getElementById("mensaje");
const btnEnviar = document.getElementById("btn-enviar");

function mostrarMensaje(texto, tipo) {
  mensaje.textContent = texto;
  mensaje.className = `mensaje ${tipo}`;
  setTimeout(() => mensaje.classList.add("oculto"), 4000);
}

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

async function cargarEstudiantes() {
  try {
    const respuesta = await fetch(API);
    const estudiantes = await respuesta.json();

    if (estudiantes.length === 0) {
      lista.innerHTML = '<tr><td colspan="5" class="vacio">Sin registros todavía</td></tr>';
      return;
    }

    lista.innerHTML = estudiantes
      .map(
        (e) => `
        <tr>
          <td>${escapar(e.nombre)}</td>
          <td>${escapar(e.correo)}</td>
          <td>${escapar(e.carrera)}</td>
          <td>${e.semestre}</td>
          <td><button class="btn-eliminar" data-id="${e.id}">✕</button></td>
        </tr>`
      )
      .join("");
  } catch {
    lista.innerHTML = '<tr><td colspan="5" class="vacio">Error al cargar los datos</td></tr>';
  }
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  btnEnviar.disabled = true;

  const datos = {
    nombre: formulario.nombre.value.trim(),
    correo: formulario.correo.value.trim(),
    carrera: formulario.carrera.value.trim(),
    semestre: Number(formulario.semestre.value),
  };

  try {
    const respuesta = await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    });

    if (respuesta.status === 201) {
      mostrarMensaje("✅ Estudiante registrado correctamente", "exito");
      formulario.reset();
      cargarEstudiantes();
    } else if (respuesta.status === 409) {
      mostrarMensaje("⚠️ Ese correo ya está registrado", "error");
    } else {
      mostrarMensaje("❌ Datos inválidos, revisa el formulario", "error");
    }
  } catch {
    mostrarMensaje("❌ No se pudo conectar con la API", "error");
  } finally {
    btnEnviar.disabled = false;
  }
});

lista.addEventListener("click", async (evento) => {
  const boton = evento.target.closest(".btn-eliminar");
  if (!boton) return;

  await fetch(`${API}/${boton.dataset.id}`, { method: "DELETE" });
  cargarEstudiantes();
});

cargarEstudiantes();
