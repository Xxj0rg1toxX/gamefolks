/* =====================================================================
   Gamefolks - Puente navegador <-> Python (Pyodide)
   GitHub Pages solo sirve archivos estáticos, así que no hay servidor Flask.
   En su lugar Python corre dentro del navegador (Pyodide) y este archivo
   intercepta fetch("/api/...") para pasarle la petición a web/api.py.
   El frontend (app.js) no se entera: sigue haciendo fetch como siempre.
   ===================================================================== */
"use strict";

(function () {
  const CLAVE_GUARDADO = "gamefolks:datos:v1";
  const RAIZ_PY = "/gamefolks";
  const fetchOriginal = window.fetch.bind(window);
  let app = null;                       // objeto web.api.Aplicacion (proxy de Python)

  const texto = (t) => { const el = document.getElementById("cargando-texto"); if (el) el.textContent = t; };

  function leerGuardado() {
    try { return localStorage.getItem(CLAVE_GUARDADO) || ""; } catch (_) { return ""; }
  }
  function guardar() {
    try { localStorage.setItem(CLAVE_GUARDADO, app.exportar()); } catch (_) { /* sin almacenamiento: la demo sigue en memoria */ }
  }

  async function arrancar() {
    if (location.protocol === "file:") {
      throw new Error("Esta página no se puede abrir con doble clic (file://). Súbela a GitHub Pages o corre `python -m http.server` en esta carpeta.");
    }
    texto("Cargando Python en tu navegador…");
    const py = await loadPyodide({ indexURL: new URL("pyodide/", document.baseURI).href });

    texto("Cargando estructuras y algoritmos…");
    const r = await fetchOriginal("python/paquete.json?v=2", { cache: "no-cache" });
    if (!r.ok) throw new Error("No se pudo cargar python/paquete.json (revisa que esté subido al repositorio).");
    const { archivos } = await r.json();
    const rutas = Object.keys(archivos);
    for (const ruta of rutas) {
      const destino = `${RAIZ_PY}/${ruta}`;
      py.FS.mkdirTree(destino.slice(0, destino.lastIndexOf("/")));
      py.FS.writeFile(destino, archivos[ruta]);
    }
    // Cada carpeta de código es un paquete: si falta su __init__.py (GitHub no sube archivos vacíos), se crea aquí.
    for (const carpeta of new Set(rutas.filter(x => x.endsWith(".py") && x.includes("/")).map(x => x.slice(0, x.lastIndexOf("/"))))) {
      const init = `${RAIZ_PY}/${carpeta}/__init__.py`;
      if (!py.FS.analyzePath(init).exists) py.FS.writeFile(init, "");
    }

    texto("Armando la red social…");
    py.globals.set("_guardado", leerGuardado());
    py.runPython(`
import sys
sys.path.insert(0, "${RAIZ_PY}")
from web.api import Aplicacion
_app = Aplicacion(_guardado or None)
`);
    app = py.globals.get("_app");
    guardar();
  }

  const listo = arrancar().then(() => {
    const c = document.getElementById("cargando");
    if (c) { c.classList.add("listo"); setTimeout(() => c.remove(), 400); }
  }).catch((e) => {
    console.error(e);
    texto("No se pudo iniciar: " + (e && e.message ? e.message : e));
    const rueda = document.querySelector(".rueda");
    if (rueda) rueda.style.display = "none";
    throw e;
  });
  listo.catch(() => { /* ya se mostró el error; evita 'unhandled rejection' */ });

  // Todo fetch a /api/... se resuelve con Python; lo demás va a la red normal.
  window.fetch = async function (entrada, opciones = {}) {
    // entrada puede ser string, URL o Request (Pyodide mismo llama a fetch con un objeto URL)
    const url = typeof entrada === "string" ? entrada : (entrada && entrada.url) || String(entrada);
    if (!url.startsWith("/api/")) return fetchOriginal(entrada, opciones);
    await listo;
    const metodo = (opciones.method || "GET").toUpperCase();
    const crudo = app.manejar(metodo, url, opciones.body || "");
    const { estado, cuerpo } = JSON.parse(crudo);
    if (metodo !== "GET") guardar();
    return new Response(JSON.stringify(cuerpo), { status: estado, headers: { "Content-Type": "application/json" } });
  };

  document.addEventListener("click", async (ev) => {
    if (ev.target && ev.target.id === "restablecer") {
      ev.preventDefault();
      if (!confirm("Esto borra las cuentas, publicaciones y eventos que creaste y vuelve a los datos de ejemplo. ¿Seguir?")) return;
      try { await listo; app.reiniciar(); guardar(); } catch (_) { /* nada */ }
      location.reload();
    }
  });
})();
