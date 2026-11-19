/* =====================================================================
   Gamefolks - Frontend (HTML + CSS + JavaScript sin librerias).
   Habla con el backend por medio de la API REST (/api/...). En la versión GitHub Pages ese backend
   es Python (Pyodide) corriendo en el navegador; static/puente.js intercepta fetch('/api/...').
   ===================================================================== */
"use strict";

const estado = { yo: null, catalogos: { localidades: [], servidores: [], motivos: [] }, usuarios: [] };
const GANADORES_FEST = ["U1", "U3", "U4", "U5", "U7", "U9", "U10"];
const $ = (s, el = document) => el.querySelector(s);
const vista = () => $("#vista");

// ------------------------------------------------------------ utilidades
function esc(t) {
  return String(t ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function api(metodo, url, cuerpo) {
  const opciones = { method: metodo, headers: {} };
  if (cuerpo !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(cuerpo);
  }
  const r = await fetch(url, opciones);
  let datos = {};
  try { datos = await r.json(); } catch (_) { /* respuesta vacia */ }
  if (r.status === 401 && !url.startsWith("/api/login")) { mostrarEntrada(); throw new Error(datos.error || "Inicia sesión"); }
  if (!r.ok) throw new Error(datos.error || `Error ${r.status}`);
  return datos;
}

let temporizadorAviso;
function aviso(texto, tipo = "bien") {
  const el = $("#aviso");
  el.textContent = texto;
  el.className = `aviso ${tipo}`;
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => el.classList.add("oculto"), 3200);
}

async function intentar(fn) {
  try { return await fn(); } catch (e) { aviso(e.message, "error"); }
}

function colorDe(nombre) {
  let h = 0;
  for (const c of String(nombre)) h = (h * 31 + c.charCodeAt(0)) % 360;
  return `hsl(${h}, 65%, 72%)`;
}

function avatar(nombre, clase = "") {
  const ini = String(nombre).replace(/[^A-Za-z0-9]/g, "").slice(0, 2).toUpperCase() || "?";
  return `<div class="avatar ${clase}" style="background:${colorDe(nombre)}" aria-hidden="true">${esc(ini)}</div>`;
}

function haceCuanto(iso) {
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return "ahora";
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  return `hace ${Math.floor(s / 86400)} d`;
}

const alg = texto => `<span class="chip alg" title="Algoritmo del curso usado aquí">${esc(texto)}</span>`;
const seguidores = n => `${n} ${n === 1 ? "seguidor" : "seguidores"}`;
const enlaceUsuario = (id, nombre) => `<a href="#/u/${esc(id)}">${esc(nombre)}</a>`;

function abrirModal(html) {
  $("#modal-contenido").innerHTML = html;
  $("#modal").classList.remove("oculto");
}
function cerrarModal() { $("#modal").classList.add("oculto"); }

// ------------------------------------------------------------ entrada
function mostrarEntrada() {
  estado.yo = null;
  $("#pantalla-app").classList.add("oculto");
  $("#pantalla-entrada").classList.remove("oculto");
}

async function mostrarApp(yo) {
  estado.yo = yo;
  $("#pantalla-entrada").classList.add("oculto");
  $("#pantalla-app").classList.remove("oculto");
  $("#enlace-yo").innerHTML = `${avatar(yo.usuario, "mini")}<span class="nombre-yo">${esc(yo.usuario)}</span>`;
  $("#enlace-yo").href = `#/u/${yo.id}`;
  $("#menu-moderacion").classList.toggle("oculto", yo.rol !== "moderador");
  estado.usuarios = await api("GET", "/api/usuarios");
  if (!location.hash || location.hash === "#/") location.hash = "#/inicio";
  enrutar();
}

function prepararEntrada() {
  const sel = $("#reg-localidad");
  sel.innerHTML = `<option value="">Elige…</option>` +
    estado.catalogos.localidades.map(l => `<option>${esc(l)}</option>`).join("");
  $("#tab-login").onclick = () => cambiarTab(true);
  $("#tab-registro").onclick = () => cambiarTab(false);
  function cambiarTab(login) {
    $("#tab-login").classList.toggle("activa", login);
    $("#tab-registro").classList.toggle("activa", !login);
    $("#form-login").classList.toggle("oculto", !login);
    $("#form-registro").classList.toggle("oculto", login);
  }
  $("#form-login").onsubmit = ev => {
    ev.preventDefault();
    intentar(async () => mostrarApp(await api("POST", "/api/login",
      { usuario: $("#login-usuario").value, clave: $("#login-clave").value })));
  };
  $("#form-registro").onsubmit = ev => {
    ev.preventDefault();
    intentar(async () => {
      const yo = await api("POST", "/api/registro", {
        usuario: $("#reg-usuario").value, clave: $("#reg-clave").value,
        juego: $("#reg-juego").value, localidad: $("#reg-localidad").value,
      });
      aviso(`¡Bienvenido/a, ${yo.usuario}!`);
      mostrarApp(yo);
    });
  };
  $("#salir").onclick = async () => { await api("POST", "/api/logout"); location.hash = ""; mostrarEntrada(); };
}

// ------------------------------------------------------------ buscador (Trie)
function prepararBuscador() {
  const input = $("#buscador"), caja = $("#resultados");
  let t;
  input.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(async () => {
      const q = input.value.trim();
      if (q.length < 2) { caja.classList.add("oculto"); return; }
      const r = await intentar(() => api("GET", `/api/buscar?q=${encodeURIComponent(q)}`));
      if (!r) return;
      let html = "";
      if (r.usuarios.length) {
        html += `<div class="titulo">Gamers</div>` + r.usuarios.map(u =>
          `<a class="item" href="#/u/${esc(u.id)}">${avatar(u.usuario, "mini")}<span>${esc(u.usuario)}
           <span class="suave chico">· ${seguidores(u.seguidores)}</span></span></a>`).join("");
      }
      if (r.juegos.length) {
        html += `<div class="titulo">Juegos</div>` + r.juegos.map(j =>
          `<div class="item">🎮 <span>${esc(j.nombre)} <span class="suave chico">· ${j.popularidad.toLocaleString("es-CO")} vistas</span></span></div>`).join("");
      }
      caja.innerHTML = (html || `<div class="vacio chico">Sin coincidencias</div>`) +
        `<div class="titulo" style="text-align:right">${alg("Trie · Top-K")}</div>`;
      caja.classList.remove("oculto");
    }, 180);
  });
  document.addEventListener("click", ev => { if (!$(".buscador").contains(ev.target)) caja.classList.add("oculto"); });
  caja.addEventListener("click", ev => { if (ev.target.closest("a")) { caja.classList.add("oculto"); input.value = ""; } });
}

// ------------------------------------------------------------ router
async function enrutar() {
  if (!estado.yo) return;
  const [, ruta = "inicio", param] = location.hash.split("/");
  document.querySelectorAll("#menu a").forEach(a => a.classList.toggle("activo",
    a.dataset.ruta === ruta || (ruta === "u" && param === estado.yo.id && a.dataset.ruta === "perfil")));
  vista().innerHTML = `<div class="vacio">Cargando…</div>`;
  window.scrollTo(0, 0);
  const paginas = {
    inicio: () => paginaInicio(param || "siguiendo"), explorar: paginaExplorar, conexiones: () => paginaConexiones(param),
    eventos: paginaEventos, premios: paginaPremios, moderacion: paginaModeracion, laboratorio: () => paginaLaboratorio(param),
    perfil: () => paginaPerfil(estado.yo.id), u: () => paginaPerfil(param),
  };
  await intentar(paginas[ruta] || paginas.inicio);
  lateral();
}
window.addEventListener("hashchange", enrutar);

// ------------------------------------------------------------ publicaciones
function tarjetaPost(p) {
  const puedeBorrar = p.mia || estado.yo.rol === "moderador";
  return `<article class="tarjeta post" data-post="${p.id}">
    ${avatar(p.autor_nombre)}
    <div class="cuerpo">
      <div class="meta"><b>${enlaceUsuario(p.autor, p.autor_nombre)}</b>
        ${p.juego ? `<span class="chip">🎮 ${esc(p.juego)}</span>` : ""}<span>${haceCuanto(p.creado)}</span></div>
      <div class="texto">${esc(p.texto)}</div>
      <div class="acciones">
        <button class="accion ${p.me_gusta ? "activa" : ""}" data-accion="like">❤ <span>${p.n_likes}</span></button>
        <button class="accion" data-accion="comentarios">💬 ${p.n_comentarios}</button>
        ${p.mia ? "" : `<button class="accion" data-accion="reportar">⚑ Reportar</button>`}
        ${puedeBorrar ? `<button class="accion" data-accion="borrar">🗑 Borrar</button>` : ""}
      </div>
      <div class="comentarios oculto"></div>
    </div>
  </article>`;
}

function listaPosts(posts, vacio) {
  return posts.length ? posts.map(tarjetaPost).join("") : `<div class="tarjeta vacio">${vacio}</div>`;
}

async function pintarComentarios(caja, pid) {
  const lista = await api("GET", `/api/publicaciones/${pid}/comentarios`);
  caja.innerHTML = lista.map(c => `<div class="comentario"><b>${enlaceUsuario(c.autor, c.autor_nombre)}</b> ${esc(c.texto)}</div>`).join("") +
    `<form class="fila" data-form="comentar"><input placeholder="Escribe un comentario…" maxlength="300" required>
     <button class="btn chico">Enviar</button></form>`;
}

// acciones sobre publicaciones (delegacion de eventos)
document.addEventListener("click", ev => {
  const boton = ev.target.closest("[data-accion]");
  if (!boton) return;
  const tarjeta = boton.closest("[data-post]");
  const pid = tarjeta && tarjeta.dataset.post;
  const accion = boton.dataset.accion;
  intentar(async () => {
    if (accion === "like") {
      const r = await api("POST", `/api/publicaciones/${pid}/like`);
      boton.classList.toggle("activa", r.me_gusta);
      boton.querySelector("span").textContent = r.n_likes;
    } else if (accion === "comentarios") {
      const caja = tarjeta.querySelector(".comentarios");
      caja.classList.toggle("oculto");
      if (!caja.classList.contains("oculto")) await pintarComentarios(caja, pid);
    } else if (accion === "borrar") {
      await api("DELETE", `/api/publicaciones/${pid}`);
      tarjeta.remove();
      aviso("Publicación borrada");
    } else if (accion === "reportar") {
      abrirModal(`<h3>Reportar publicación</h3>
        <p class="suave chico">Tu reporte entra a la cola de moderación (Max-Heap): los más graves se atienden primero.</p>
        <label for="motivo">Motivo</label>
        <select id="motivo">${estado.catalogos.motivos.map(m => `<option>${esc(m)}</option>`).join("")}</select>
        <div class="fila" style="justify-content:flex-end;margin-top:16px">
          <button class="btn sec" data-accion="cerrar-modal">Cancelar</button>
          <button class="btn" data-accion="enviar-reporte" data-pid="${pid}">Enviar reporte</button></div>`);
    } else if (accion === "enviar-reporte") {
      await api("POST", `/api/publicaciones/${boton.dataset.pid}/reportar`, { motivo: $("#motivo").value });
      cerrarModal();
      aviso("Gracias, los moderadores lo revisarán");
    } else if (accion === "cerrar-modal") {
      cerrarModal();
    } else if (accion === "seguir") {
      const r = await api("POST", `/api/usuarios/${boton.dataset.uid}/seguir`);
      aviso(r.lo_sigo ? `Ahora sigues a ${r.usuario}` : `Dejaste de seguir a ${r.usuario}`);
      enrutar();
    }
  });
});

document.addEventListener("submit", ev => {
  const form = ev.target.closest("[data-form='comentar']");
  if (!form) return;
  ev.preventDefault();
  const tarjeta = form.closest("[data-post]");
  intentar(async () => {
    await api("POST", `/api/publicaciones/${tarjeta.dataset.post}/comentarios`, { texto: form.querySelector("input").value });
    await pintarComentarios(form.parentElement, tarjeta.dataset.post);
  });
});

// ------------------------------------------------------------ INICIO
async function paginaInicio(pestana) {
  const posts = await api("GET", pestana === "descubrir" ? "/api/descubrir" : "/api/feed");
  vista().innerHTML = `
    <form class="tarjeta" id="form-publicar">
      <div class="fila" style="align-items:flex-start">${avatar(estado.yo.usuario)}
        <textarea id="texto-post" maxlength="400" placeholder="¿Qué estás jugando, ${esc(estado.yo.usuario)}?"></textarea></div>
      <div class="fila" style="margin-top:10px">
        <input id="juego-post" list="lista-juegos" placeholder="Juego (autocompleta con Trie)" maxlength="40" style="flex:1">
        <datalist id="lista-juegos"></datalist>
        <button class="btn">Publicar</button></div>
    </form>
    <div class="pestanas" style="margin-top:16px">
      <button data-pestana="siguiendo" class="${pestana !== "descubrir" ? "activa" : ""}">Siguiendo</button>
      <button data-pestana="descubrir" class="${pestana === "descubrir" ? "activa" : ""}">Descubrir</button>
    </div>
    <div id="lista-posts">${listaPosts(posts, pestana === "descubrir" ? "Aún no hay publicaciones."
      : "Sigue a otros gamers para ver sus publicaciones aquí. Mira <a href='#/explorar'>Explorar</a>.")}</div>`;
  document.querySelectorAll("[data-pestana]").forEach(b => b.onclick = () => { location.hash = `#/inicio/${b.dataset.pestana}`; });
  autocompletarJuego($("#juego-post"), $("#lista-juegos"));
  $("#form-publicar").onsubmit = ev => {
    ev.preventDefault();
    intentar(async () => {
      const p = await api("POST", "/api/publicaciones", { texto: $("#texto-post").value, juego: $("#juego-post").value });
      $("#texto-post").value = ""; $("#juego-post").value = "";
      const lista = $("#lista-posts");
      if (lista.querySelector(".vacio")) lista.innerHTML = "";
      lista.insertAdjacentHTML("afterbegin", tarjetaPost(p));
      aviso("¡Publicado!");
    });
  };
}

function autocompletarJuego(input, datalist) {
  let t;
  input.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(async () => {
      if (input.value.trim().length < 2) return;
      const r = await api("GET", `/api/buscar?q=${encodeURIComponent(input.value.trim())}`).catch(() => null);
      if (r) datalist.innerHTML = r.juegos.map(j => `<option value="${esc(j.nombre)}">`).join("");
    }, 150);
  });
}

// ------------------------------------------------------------ EXPLORAR (BFS)
function tarjetaSugerencia(s) {
  const razon = s.nivel ? `Lo sigue ${esc(s.por_medio_de)} · nivel ${s.nivel}` : `${seguidores(s.seguidores ?? 0)} · popular`;
  return `<div class="tarjeta columna" style="align-items:center;text-align:center">
    ${avatar(s.usuario, "grande")}<b>${enlaceUsuario(s.id, s.usuario)}</b>
    <span class="suave chico">${esc(s.juego || "—")}</span><span class="chico">${razon}</span>
    <button class="btn chico" data-accion="seguir" data-uid="${esc(s.id)}">Seguir</button></div>`;
}

async function paginaExplorar() {
  const r = await api("GET", "/api/explorar");
  const niveles = Object.entries(r.niveles);
  vista().innerHTML = `
    <div class="tarjeta"><div class="cabecera"><h2>Sugerencias para ti</h2>${alg("BFS por niveles")}</div>
      <p class="explicacion">Recorremos la red <b>por niveles</b> desde tu perfil: nivel 1 = a quién sigues, nivel 2 = a quién siguen ellos.
      Los del nivel 2 y 3 que todavía no sigues son tus sugerencias.</p>
      <div class="rejilla" style="margin-top:12px">${r.sugerencias.map(tarjetaSugerencia).join("") || "<div class='vacio'>Ya sigues a todos 🎉</div>"}</div></div>
    <div class="tarjeta"><div class="cabecera"><h2>Tus círculos</h2>${alg("BFS")}</div>
      ${niveles.length ? `<table><tr><th>Nivel</th><th>Gamers</th></tr>${niveles.map(([n, us]) =>
        `<tr><td>${n}</td><td>${us.map(u => enlaceUsuario(u.id, u.usuario)).join(", ")}</td></tr>`).join("")}</table>`
        : `<div class="vacio">Todavía no sigues a nadie.</div>`}</div>
    <div class="tarjeta"><div class="cabecera"><h2>Juegos más vistos</h2>${alg("Catálogo + Trie")}</div>
      <div class="rejilla">${r.juegos.map(j => `<div class="tarjeta"><div class="numero">🎮</div><b>${esc(j.nombre)}</b>
        <div class="suave chico">${j.popularidad.toLocaleString("es-CO")} vistas</div></div>`).join("")}</div></div>`;
}

// ------------------------------------------------------------ PERFIL
async function paginaPerfil(uid) {
  const { perfil: p, publicaciones } = await api("GET", `/api/usuarios/${encodeURIComponent(uid)}`);
  const soyYo = p.id === estado.yo.id;
  vista().innerHTML = `
    <div class="tarjeta">
      <div class="portada"></div>
      <div class="perfil-top">${avatar(p.usuario, "grande")}
        <div style="flex:1"><h2 style="margin:0">${esc(p.usuario)}</h2>
          <div class="fila chico suave">${p.juego ? `<span class="chip">🎮 ${esc(p.juego)}</span>` : ""}
            ${p.localidad ? `📍 ${esc(p.localidad)}` : ""} ${p.rol === "moderador" ? `<span class="chip">🛡️ Moderador/a</span>` : ""}
            ${p.me_sigue && !soyYo ? `<span class="chip">Te sigue</span>` : ""}</div></div>
        ${soyYo ? `<button class="btn sec" id="editar-perfil">Editar perfil</button>`
          : `<button class="btn ${p.lo_sigo ? "sec" : ""}" data-accion="seguir" data-uid="${esc(p.id)}">${p.lo_sigo ? "Siguiendo ✓" : "Seguir"}</button>`}
      </div>
      <p>${esc(p.bio || "Sin biografía todavía.")}</p>
      <div class="estadisticas"><div><b>${p.publicaciones}</b><span class="suave chico">publicaciones</span></div>
        <div><b>${p.seguidores}</b><span class="suave chico">seguidores</span></div>
        <div><b>${p.siguiendo}</b><span class="suave chico">siguiendo</span></div></div>
      ${soyYo ? "" : `<div class="separador"></div><a class="btn sec chico" href="#/conexiones/${esc(p.id)}">🔗 ¿Cómo llego a ${esc(p.usuario)}?</a>`}
    </div>
    <h3 style="margin:18px 0 10px">Publicaciones</h3>
    ${listaPosts(publicaciones, "Todavía no ha publicado nada.")}`;
  if (soyYo) $("#editar-perfil").onclick = () => modalEditarPerfil(p);
}

function modalEditarPerfil(p) {
  abrirModal(`<h3>Editar perfil</h3>
    <label for="ed-bio">Biografía</label><textarea id="ed-bio" maxlength="160">${esc(p.bio)}</textarea>
    <label for="ed-juego">Juego favorito</label><input id="ed-juego" maxlength="40" value="${esc(p.juego)}">
    <label for="ed-loc">Localidad</label><select id="ed-loc">${estado.catalogos.localidades.map(l =>
      `<option ${l === p.localidad ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>
    <div class="fila" style="justify-content:flex-end;margin-top:16px">
      <button class="btn sec" data-accion="cerrar-modal">Cancelar</button><button class="btn" id="guardar-perfil">Guardar</button></div>`);
  $("#guardar-perfil").onclick = () => intentar(async () => {
    await api("PUT", "/api/yo", { bio: $("#ed-bio").value, juego: $("#ed-juego").value, localidad: $("#ed-loc").value });
    cerrarModal(); aviso("Perfil actualizado"); enrutar();
  });
}

// ------------------------------------------------------------ CONEXIONES (UCS + BFS + DFS)
function dibujarRed(red, caminoUCS = [], caminoBFS = []) {
  const xs = red.nodos.map(n => n.x), ys = red.nodos.map(n => n.y);
  const minX = Math.min(...xs) - 70, maxX = Math.max(...xs) + 70, minY = Math.min(...ys) - 60, maxY = Math.max(...ys) + 70;
  const pos = Object.fromEntries(red.nodos.map(n => [n.id, n]));
  const enUCS = new Set(caminoUCS.slice(1).map((id, i) => `${caminoUCS[i]}>${id}`));
  const enBFS = new Set(caminoBFS.slice(1).map((id, i) => `${caminoBFS[i]}>${id}`));
  const R = 26;
  const lineas = red.aristas.map(a => {
    const p = pos[a.a], q = pos[a.b];
    const dx = q.x - p.x, dy = q.y - p.y, d = Math.hypot(dx, dy) || 1;
    const off = 5;                                         // separa a->b de b->a
    const ox = -dy / d * off, oy = dx / d * off;
    const x1 = p.x + dx / d * R + ox, y1 = p.y + dy / d * R + oy, x2 = q.x - dx / d * (R + 4) + ox, y2 = q.y - dy / d * (R + 4) + oy;
    const clave = `${a.a}>${a.b}`;
    const color = enUCS.has(clave) ? "#e0407b" : enBFS.has(clave) ? "#8fb8de" : "#5a4760";
    const ancho = enUCS.has(clave) ? 5 : enBFS.has(clave) ? 3.5 : 1.6;
    const guion = enBFS.has(clave) && !enUCS.has(clave) ? `stroke-dasharray="8 6"` : "";
    const marca = enUCS.has(clave) ? "fr" : enBFS.has(clave) ? "fa" : "fg";
    return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${ancho}" ${guion} marker-end="url(#${marca})"/>
      <text x="${(x1 + x2) / 2 + ox * 2}" y="${(y1 + y2) / 2 + oy * 2}" font-size="11" fill="#bba8b1" text-anchor="middle">${a.peso}</text>`;
  }).join("");
  const nodos = red.nodos.map(n => {
    const resaltado = caminoUCS.includes(n.id);
    const yo = n.id === estado.yo.id;
    return `<g><circle cx="${n.x}" cy="${n.y}" r="${R}" fill="${yo ? "#8fb8de" : resaltado ? "#f2b8cb" : "#2d2131"}" stroke="#bba8b1" stroke-width="1.5"/>
      <text x="${n.x}" y="${n.y + R + 16}" text-anchor="middle" font-size="13">${esc(n.usuario)}</text>
      <text x="${n.x}" y="${n.y + 5}" text-anchor="middle" font-size="12" font-weight="700" fill="#1b1320">${esc(n.id)}</text></g>`;
  }).join("");
  const flecha = (id, c) => `<marker id="${id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${c}"/></marker>`;
  return `<svg class="lienzo" viewBox="${minX} ${minY} ${maxX - minX} ${maxY - minY}" role="img" aria-label="Red de seguidores">
    <defs>${flecha("fr", "#e0407b")}${flecha("fa", "#8fb8de")}${flecha("fg", "#5a4760")}</defs>${lineas}${nodos}</svg>`;
}

function pasosRuta(r) {
  if (!r.camino) return `<div class="vacio">No hay una cadena de seguidos que llegue hasta allá.</div>`;
  return `<div class="ruta">${r.camino.map((u, i) => `<span class="paso">${avatar(u.usuario, "mini")}${esc(u.usuario)}</span>` +
    (i < r.tramos.length ? `<span class="costo">→ ${r.tramos[i].costo} →</span>` : "")).join("")}</div>
    <p class="chico suave">Costo total: <b>${r.costo}</b> · ${r.saltos} saltos · ${r.expandidos} estados expandidos</p>`;
}

async function paginaConexiones(hasta) {
  const otros = estado.usuarios.filter(u => u.id !== estado.yo.id);
  const destino = hasta && otros.some(u => u.id === hasta) ? hasta : (otros.find(u => u.id === "U4") || otros[0] || {}).id;
  const [red, ciclos] = await Promise.all([api("GET", "/api/red"), api("GET", "/api/ciclos")]);
  vista().innerHTML = `
    <div class="tarjeta">
      <div class="cabecera"><h2>¿Cómo llego a…?</h2><span>${alg("UCS")} ${alg("BFS")}</span></div>
      <p class="explicacion">Para invitar a alguien que no conoces, la invitación pasa de mano en mano por la cadena "sigue a".
        El costo de cada salto es el peso del vínculo (interacciones por semana = qué tan saturado está ese canal).
        <b>UCS</b> busca la cadena de <b>menor costo total</b>; <b>BFS</b> la de <b>menos saltos</b>.</p>
      <div class="fila" style="margin-top:12px"><select id="destino" aria-label="Destino">${otros.map(u =>
        `<option value="${esc(u.id)}" ${u.id === destino ? "selected" : ""}>${esc(u.usuario)}</option>`).join("")}</select>
        <button class="btn" id="calcular-ruta">Calcular</button></div>
      <div id="resultado-ruta" style="margin-top:14px"></div>
    </div>
    <div class="tarjeta"><div class="cabecera"><h2>Cámaras de eco</h2>${alg("DFS · ciclos")}</div>
      <p class="explicacion">Con DFS buscamos <b>ciclos</b> de seguimiento: grupos donde un post puede dar vueltas sin salir del círculo.</p>
      ${ciclos.mios.length ? `<p>Estás en ${ciclos.mios.length} ciclo(s):</p>` + ciclos.mios.map(c => `<div class="ruta" style="margin:6px 0">${c.map(n =>
        `<span class="paso">${avatar(n, "mini")}${esc(n)}</span>`).join(`<span class="costo">→</span>`)}</div>`).join("")
        : `<p class="suave">No estás en ningún ciclo. En toda la red hay ${ciclos.total}.</p>`}
    </div>`;
  const calcular = () => intentar(async () => {
    const id = $("#destino").value;
    const r = await api("GET", `/api/ruta?hasta=${encodeURIComponent(id)}`);
    const mismo = r.UCS.camino && r.BFS.camino && r.UCS.camino.map(u => u.id).join() === r.BFS.camino.map(u => u.id).join();
    $("#resultado-ruta").innerHTML = `
      <h3>Ruta de menor costo (UCS)</h3>${pasosRuta(r.UCS)}
      <h3 style="margin-top:12px">Ruta con menos saltos (BFS)</h3>${pasosRuta(r.BFS)}
      ${r.UCS.camino ? `<p class="explicacion">${mismo ? "Aquí ambos algoritmos coinciden." :
        `UCS ahorra ${r.BFS.costo - r.UCS.costo} de costo frente a BFS${r.UCS.saltos > r.BFS.saltos ? ", aunque da más saltos" : ""}.`}</p>` : ""}
      <div style="margin-top:12px">${dibujarRed(red, r.UCS.camino ? r.UCS.camino.map(u => u.id) : [], r.BFS.camino ? r.BFS.camino.map(u => u.id) : [])}</div>
      <p class="chico suave">Rosa = ruta UCS · azul punteado = ruta BFS · tu nodo en azul. El número sobre cada flecha es el peso.</p>`;
  });
  $("#calcular-ruta").onclick = calcular;
  if (destino) calcular();
}

// ------------------------------------------------------------ EVENTOS (Welsh-Powell)
async function paginaEventos() {
  const r = await api("GET", "/api/eventos");
  vista().innerHTML = `
    <div class="tarjeta">
      <div class="cabecera"><h2>Horario de eventos en vivo</h2>${alg("Welsh-Powell")}</div>
      <p class="explicacion">Dos eventos <b>chocan</b> si comparten un streamer o el mismo servidor. Welsh-Powell ordena los eventos de
        mayor a menor número de choques y les asigna la primera franja libre. Resultado: <b>${r.n_turnos} franjas mínimas</b>
        para que nadie quede en dos eventos a la vez${r.valida ? " (sin colisiones ✓)" : ""}.</p>
      <div class="turnos" style="margin-top:12px">${r.turnos.map(t => `<div class="turno t${t.turno}">
        <b>Turno ${t.turno}</b><div class="suave chico">${t.inicio} – ${t.fin}</div>
        ${t.eventos.map(e => `<div style="margin-top:6px">${esc(e.id)} · ${esc(e.nombre)}</div>`).join("")}</div>`).join("")}</div>
    </div>
    <div class="tarjeta"><h3>Eventos (${r.eventos.length})</h3>${r.eventos.map(e => `<div class="evento">
      <div class="cabecera" style="margin:0"><b>${esc(e.id)} · ${esc(e.nombre)}</b><span class="chip turno-${e.turno}">Turno ${e.turno}</span></div>
      <div class="chico suave">🎮 ${esc(e.juego || "—")} · 🖥️ ${esc(e.servidor)} · ${e.grado} choque(s)</div>
      <div class="chico">👥 ${e.participantes.map(esc).join(", ")}</div></div>`).join("")}</div>
    <div class="tarjeta"><h3>¿Por qué chocan?</h3>${r.conflictos.length ? `<table><tr><th>Eventos</th><th>Motivo</th></tr>${r.conflictos.map(c =>
      `<tr><td>${esc(c.a)} – ${esc(c.b)}</td><td>${esc(c.motivo)}</td></tr>`).join("")}</table>` : "<p class='suave'>No hay choques.</p>"}</div>
    <form class="tarjeta" id="form-evento"><h3>Crear evento</h3>
      <label for="ev-nombre">Nombre</label><input id="ev-nombre" maxlength="60" required placeholder="Ej. Torneo relámpago">
      <div class="fila"><div style="flex:1"><label for="ev-juego">Juego</label><input id="ev-juego" maxlength="40"></div>
        <div style="flex:1"><label for="ev-servidor">Servidor</label><select id="ev-servidor">${estado.catalogos.servidores.map(s =>
          `<option>${esc(s)}</option>`).join("")}</select></div></div>
      <label>Participantes</label><div class="lista-check">${estado.usuarios.map(u =>
        `<label><input type="checkbox" value="${esc(u.id)}" ${u.id === estado.yo.id ? "checked" : ""}>${esc(u.usuario)}</label>`).join("")}</div>
      <button class="btn" style="margin-top:14px">Crear y recalcular horario</button></form>`;
  $("#form-evento").onsubmit = ev => {
    ev.preventDefault();
    intentar(async () => {
      const participantes = [...document.querySelectorAll("#form-evento input[type=checkbox]:checked")].map(c => c.value);
      const nuevo = await api("POST", "/api/eventos", { nombre: $("#ev-nombre").value, juego: $("#ev-juego").value,
        servidor: $("#ev-servidor").value, participantes });
      aviso(`Evento creado. Ahora se necesitan ${nuevo.n_turnos} franjas.`);
      paginaEventos();
    });
  };
}

// ------------------------------------------------------------ PREMIOS (TSP)
function dibujarMapa(puntos, ruta, mst) {
  const W = 640, H = 460, M = 60;
  const lats = puntos.map(p => p.lat), lons = puntos.map(p => p.lon);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats), minLon = Math.min(...lons), maxLon = Math.max(...lons);
  const escala = Math.min((W - 2 * M) / ((maxLon - minLon) || 1), (H - 2 * M) / ((maxLat - minLat) || 1));
  const xy = p => [M + (p.lon - minLon) * escala, M + (maxLat - p.lat) * escala];
  const pos = Object.fromEntries(puntos.map(p => [p.id, xy(p)]));
  const arbol = (mst || []).map(([a, b]) => `<line x1="${pos[a][0]}" y1="${pos[a][1]}" x2="${pos[b][0]}" y2="${pos[b][1]}"
      stroke="#8fb8de" stroke-opacity=".45" stroke-width="10" stroke-linecap="round"/>`).join("");
  const tramos = ruta.slice(1).map((b, i) => {
    const [x1, y1] = pos[ruta[i]], [x2, y2] = pos[b];
    const d = Math.hypot(x2 - x1, y2 - y1) || 1, r = 16;
    return `<line x1="${x1 + (x2 - x1) / d * r}" y1="${y1 + (y2 - y1) / d * r}" x2="${x2 - (x2 - x1) / d * (r + 4)}" y2="${y2 - (y2 - y1) / d * (r + 4)}"
      stroke="#e0407b" stroke-width="3" marker-end="url(#ft)"/>`;
  }).join("");
  const orden = Object.fromEntries(ruta.slice(1, -1).map((id, i) => [id, i + 1]));
  const nodos = puntos.map(p => {
    const [x, y] = pos[p.id], bodega = p.id === "BODEGA";
    return `<circle cx="${x}" cy="${y}" r="15" fill="${bodega ? "#f2c94c" : "#f2b8cb"}" stroke="#17101a" stroke-width="2"/>
      <text x="${x}" y="${y + 5}" text-anchor="middle" font-weight="700" font-size="13" fill="#1b1320">${bodega ? "🏠" : orden[p.id]}</text>
      <text x="${x}" y="${bodega ? y - 36 : y + 32}" text-anchor="middle" font-size="12">${esc(p.nombre)}</text>
      <text x="${x}" y="${bodega ? y - 22 : y + 46}" text-anchor="middle" font-size="11" fill="#bba8b1">${esc(p.localidad)}</text>`;
  }).join("");
  return `<svg class="lienzo" viewBox="0 0 ${W} ${H + 20}" role="img" aria-label="Mapa de la ruta de reparto">
    <defs><marker id="ft" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="#e0407b"/></marker></defs>${arbol}${tramos}${nodos}</svg>`;
}

async function paginaPremios() {
  vista().innerHTML = `
    <div class="tarjeta">
      <div class="cabecera"><h2>Reparto de premios del Gamefolks Fest</h2>${alg("TSP · aproximación MST")}</div>
      <p class="explicacion">El repartidor sale de la <b>Bodega Gamefolks (Chapinero)</b>, deja un kit en la localidad de cada ganador y vuelve.
        Primero armamos el <b>árbol de expansión mínima</b> (Prim) y lo recorremos en preorden saltando lugares repetidos:
        la ruta nunca cuesta más del <b>doble</b> de la óptima. Con pocos ganadores también calculamos el óptimo por fuerza bruta para comparar.</p>
      <label>Ganadores</label><div class="lista-check" id="ganadores">${estado.usuarios.map(u =>
        `<label><input type="checkbox" value="${esc(u.id)}" ${GANADORES_FEST.includes(u.id) ? "checked" : ""}>
         <span>${esc(u.usuario)}<span class="sub">${esc(u.localidad || "sin localidad")}</span></span></label>`).join("")}</div>
      <button class="btn" id="calcular-premios" style="margin-top:14px">Calcular ruta</button>
    </div>
    <div id="resultado-premios"></div>`;
  $("#calcular-premios").onclick = () => intentar(async () => {
    const ganadores = [...document.querySelectorAll("#ganadores input:checked")].map(c => c.value);
    const r = await api("POST", "/api/premios", { ganadores });
    const caja = $("#resultado-premios");
    const pintar = modo => {
      const ruta = modo === "exacto" ? r.exacto.ruta : r.aprox.ruta;
      caja.innerHTML = `<div class="tarjeta">
        <div class="rejilla" style="margin-bottom:12px">
          <div class="tarjeta"><div class="suave chico">Aproximación (MST)</div><div class="numero">${r.aprox.km} km</div></div>
          <div class="tarjeta"><div class="suave chico">Óptimo (fuerza bruta)</div><div class="numero">${r.exacto ? r.exacto.km + " km" : "—"}</div>
            <div class="suave chico">${r.exacto ? r.exacto.probadas.toLocaleString("es-CO") + " rutas probadas" : "demasiados puntos"}</div></div>
          <div class="tarjeta"><div class="suave chico">Aproximación / óptimo</div><div class="numero">${r.razon ?? "—"}</div>
            <div class="suave chico">la garantía dice ≤ 2</div></div></div>
        ${r.exacto ? `<div class="pestanas"><button data-modo="aprox" class="${modo === "aprox" ? "activa" : ""}">Ruta aproximada</button>
          <button data-modo="exacto" class="${modo === "exacto" ? "activa" : ""}">Ruta óptima</button></div>` : ""}
        ${dibujarMapa(r.puntos, ruta, modo === "aprox" ? r.aprox.mst : [])}
        <p class="chico suave">${modo === "aprox" ? "Azul claro = árbol de expansión mínima · " : ""}rosa = recorrido · número = orden de entrega · distancias en línea recta.</p>
        ${modo === "aprox" ? `<table><tr><th>#</th><th>Desde</th><th>Hasta</th><th>km</th></tr>${r.tramos.map((t, i) =>
          `<tr><td>${i + 1}</td><td>${esc(t.desde)}</td><td>${esc(t.hasta)}</td><td>${t.km}</td></tr>`).join("")}</table>` : ""}
      </div>`;
      caja.querySelectorAll("[data-modo]").forEach(b => b.onclick = () => pintar(b.dataset.modo));
    };
    pintar("aprox");
  });
  $("#calcular-premios").click();
}

// ------------------------------------------------------------ MODERACION (Heap + Vertex Cover)
async function paginaModeracion() {
  if (estado.yo.rol !== "moderador") { vista().innerHTML = `<div class="tarjeta vacio">Solo para moderadores.</div>`; return; }
  const r = await api("GET", "/api/moderacion");
  const nivel = p => p >= 80 ? "" : p >= 50 ? "media" : "baja";
  const m = r.monitorear;
  vista().innerHTML = `
    <div class="tarjeta">
      <div class="cabecera"><h2>Cola de reportes</h2>${alg("Max-Heap + envejecimiento")}</div>
      <p class="explicacion">Prioridad = gravedad del motivo + 5 puntos por cada día sin atender (así ningún reporte se queda olvidado).
        El Max-Heap siempre deja arriba el más urgente.</p>
      ${r.cola.length ? `<div class="fila" style="margin:12px 0"><b style="flex:1">Siguiente: reporte #${r.cola[0].id}</b>
        <button class="btn peligro chico" data-atender="eliminar">Eliminar publicación</button>
        <button class="btn sec chico" data-atender="descartar">Descartar reporte</button></div>` : ""}
      ${r.cola.map((x, i) => `<div class="reporte"><div class="prioridad ${nivel(x.prioridad)}">${x.prioridad}</div>
        <div style="flex:1"><div class="fila"><b>${i === 0 ? "▶ " : ""}${esc(x.motivo)}</b><span class="suave chico">gravedad ${x.gravedad} · ${x.dias} día(s)</span></div>
        <div>“${esc(x.texto)}”</div><div class="suave chico">de ${esc(x.autor)} · reportó ${esc(x.reportero)}</div></div></div>`).join("")
        || `<div class="vacio">No hay reportes pendientes 🎉</div>`}
    </div>
    <div class="tarjeta">
      <div class="cabecera"><h2>Usuarios a monitorear</h2>${alg("Vertex Cover · 2-aproximación")}</div>
      <p class="explicacion">Queremos vigilar a pocos usuarios pero ver <b>todas</b> las interacciones (${m.interacciones}).
        Tomamos una interacción sin vigilar y monitoreamos a <b>los dos</b> extremos; repetimos. Nunca usa más del doble del mínimo.</p>
      <div class="fila" style="flex-wrap:wrap;margin:10px 0">${m.aprox.map(n => `<span class="paso chip">🛡️ ${esc(n)}</span>`).join("")}</div>
      <p class="chico">Interacciones elegidas: ${m.elegidas.map(([a, b]) => `${esc(a)} – ${esc(b)}`).join("; ") || "ninguna"}</p>
      ${m.optimo ? `<p class="chico suave">Mínimo exacto (fuerza bruta): ${m.optimo.length} usuarios (${m.optimo.map(esc).join(", ")}).
        Aproximación / óptimo = ${(m.aprox.length / m.optimo.length).toFixed(2)}.</p>` : ""}
    </div>`;
  vista().querySelectorAll("[data-atender]").forEach(b => b.onclick = () => intentar(async () => {
    const res = await api("POST", "/api/moderacion/atender", { accion: b.dataset.atender });
    aviso(`Reporte #${res.atendido.id} atendido (${b.dataset.atender === "eliminar" ? "publicación eliminada" : "descartado"})`);
    paginaModeracion();
  }));
}

// ------------------------------------------------------------ LABORATORIO (todos los talleres)
const U = (n, l, v) => ({ n, l, v, tipo: "usuario" });
const T = (n, l, v = "") => ({ n, l, v });
const S = (n, l, ops, v) => ({ n, l, v: v ?? ops[0][0], tipo: "select", ops });

const LAB = [
  { corte: "Corte 1 · Árboles", talleres: [
    { id: "avl", titulo: "BST vs AVL", taller: "Reto 1 del Corte 1", desc: "Índice de videos por ID. Los IDs llegan en orden (1, 2, 3…): el BST se vuelve una lista y el AVL se mantiene balanceado con rotaciones.",
      campos: [T("n", "Videos a subir", "1000"), T("id", "ID a buscar (vacío = el último)")],
      botones: [["Subir videos", "avl_subir"], ["Comparar búsqueda", "avl_buscar"], ["Vaciar índices", "avl_reiniciar", 1]] },
    { id: "juegos", titulo: "Árbol de clasificación", taller: "Taller de árboles", desc: "Plataforma → Género → Subgénero → Juego. En el árbol binario un tercer hijo distinto se rechaza; el N-ario acepta cualquiera.",
      campos: [S("tipo", "Árbol", [["binario", "Binario (máx. 2 hijos)"], ["nario", "N-ario"]]), T("plataforma", "Plataforma", "PC"),
        T("genero", "Género", "Shooter"), T("subgenero", "Subgénero", "First Person Shooter"), T("juego", "Juego", "Counter-Strike 2"),
        S("nivel", "Nivel a eliminar", [["Juego", "Juego (hoja)"], ["Subgénero", "Subgénero"], ["Género", "Género"]])],
      botones: [["Ver árbol", "juegos_ver"], ["Insertar juego", "juegos_insertar"], ["Eliminar", "juegos_eliminar", 1]] },
    { id: "arbolb", titulo: "Árbol B", taller: "Taller de Árboles B", desc: "Índice de usuarios por ID con un Árbol B de orden 4 (máximo 3 claves por nodo). Al llenarse un nodo se divide y la clave del medio sube.",
      campos: [T("id", "ID de usuario", "1017"), T("nombre", "Nombre (para insertar)", "")],
      botones: [["Ver árbol", "b_ver"], ["Insertar", "b_insertar"], ["Buscar", "b_buscar"], ["Eliminar (hoja)", "b_eliminar", 1]] },
    { id: "bmas", titulo: "Árbol B+", taller: "Taller de Árboles B", desc: "Índice de videos por tag. Los datos viven solo en las hojas y las hojas están enlazadas, así que se pueden listar en orden desde cualquier tag.",
      campos: [T("tag", "Tag", "Shooter"), T("video", "ID del video", "V9")],
      botones: [["Ver estructura", "bmas_ver"], ["Indexar video", "bmas_indexar"], ["Buscar por tag", "bmas_buscar"], ["Listar desde el tag", "bmas_desde"], ["Quitar video", "bmas_quitar", 1]] },
    { id: "trie", titulo: "Trie", taller: "Taller de Tries y Heap · Reto 2", desc: "Autocompletado Top-K por popularidad sobre el catálogo de 50 juegos, y comparación de memoria contra una lista y un set.",
      campos: [T("prefijo", "Prefijo (mínimo 2 letras)", "ha"), T("k", "Top-K", "5")],
      botones: [["Autocompletar", "trie_top"], ["Comparar memoria", "trie_memoria"]] },
    { id: "heap", titulo: "Max-Heap", taller: "Taller de Heap · Reto 3", desc: "Cola de moderación con los 70 reportes del Corte 1. Muestra el arreglo interno del heap: cada padre está en la posición (i − 1) // 2.",
      campos: [T("id", "ID del reporte", "R100"), T("gravedad", "Gravedad", "95"), T("descripcion", "Descripción", "Reporte nuevo"), T("incremento", "Envejecer (+)", "5")],
      botones: [["Ver heap", "heap_ver"], ["Insertar", "heap_insertar"], ["Cambiar gravedad", "heap_cambiar"], ["Envejecer todos", "heap_envejecer"],
        ["Atender el más urgente", "heap_atender"], ["Recargar", "heap_recargar", 1]] },
  ] },
  { corte: "Corte 2 · Grafos", talleres: [
    { id: "grafo1", titulo: "Taller 1: la red", taller: "Taller 1 de grafos", desc: "Grafo dirigido y ponderado: usuarios como vértices y 'sigue a' como arcos. Lista de adyacencia, grados y recorridos BFS y DFS.",
      campos: [U("inicio", "Inicio del recorrido", "U1"), S("tipo", "Recorrido", [["BFS", "BFS (anchura)"], ["DFS", "DFS (profundidad)"]])],
      botones: [["Ver ficha y red", "grafo_ficha"], ["Recorrer", "grafo_recorrido"]] },
    { id: "taller2", titulo: "Taller 2: caminos mínimos", taller: "Taller 2 de grafos", desc: "Dijkstra (desde un usuario a todos) y Floyd-Warshall (todos contra todos). Con la promoción U3 → U1 = −30 aparece un ciclo negativo.",
      campos: [U("origen", "Origen para Dijkstra", "U1"), S("promocion", "Floyd con promoción", [["no", "No"], ["si", "Sí (U3 → U1 = −30)"]])],
      botones: [["Dijkstra", "dijkstra"], ["Floyd-Warshall", "floyd"]] },
    { id: "parcialc2", titulo: "Parcial C2: 4 retos", taller: "Parcial del Corte 2", desc: "Reto 1 ruta de mayor capacidad · Reto 2 puntos críticos de falla · Reto 3 ruta de respaldo sin arcos en común · Reto 4 auditoría de ciclo negativo.",
      campos: [U("origen", "Origen (retos 1 y 3)", "U1"), U("destino", "Destino (retos 1 y 3)", "U8"), U("referencia", "Referencia (reto 2)", "U1")],
      botones: [["Reto 1", "reto1"], ["Reto 2", "reto2"], ["Reto 3", "reto3"], ["Reto 4", "reto4"]] },
  ] },
  { corte: "Corte 3 · Búsqueda y optimización", talleres: [
    { id: "busqueda", titulo: "BFS, DFS y UCS", taller: "Taller de búsqueda · Parcial C3 Módulo 2", desc: "La invitación viaja por la cadena 'sigue a'. BFS minimiza saltos, UCS minimiza costo y DFS se queda con el primero que encuentra.",
      campos: [U("origen", "Inicio", "U1"), U("destino", "Meta", "U4")],
      botones: [["Comparar los tres", "busqueda_comparar"], ["BFS por niveles", "bfs_niveles"], ["DFS: ciclos", "dfs_ciclos"]] },
    { id: "wp", titulo: "Welsh-Powell", taller: "Taller Welsh-Powell · Parcial C3 Módulo 3", desc: "Turnos para los 8 eventos del taller. Prueba también el orden al revés (de menor a mayor grado) para comparar. En la pantalla Eventos el horario usa los eventos vivos de la app.",
      campos: [S("orden", "Orden voraz", [["mayor", "Mayor a menor grado (Welsh-Powell)"], ["menor", "Menor a mayor grado (prueba)"]])],
      botones: [["Calcular turnos", "welsh_powell"]], enlace: ["#/eventos", "Ir a Eventos"] },
    { id: "vc", titulo: "Vertex Cover", taller: "Exposición Vertex Cover", desc: "Usuarios a monitorear para ver todas las interacciones: 2-aproximación, voraz por grado y óptimo por fuerza bruta.",
      campos: [], botones: [["Calcular cobertura", "vertex_cover"]], enlace: ["#/moderacion", "Ir a Moderación"] },
    { id: "tsp", titulo: "TSP", taller: "Parcial C3 (exposición TSP)", desc: "Ruta de reparto de premios: árbol de expansión mínima + preorden (≤ 2 veces el óptimo) contra la fuerza bruta. El mapa está en la pantalla Premios.",
      campos: [T("ganadores", "Ganadores separados por coma (vacío = los del Fest)")], botones: [["Calcular ruta", "tsp"]], enlace: ["#/premios", "Ver el mapa en Premios"] },
  ] },
];

let usuariosLab = null;

function pintarBloques(bloques) {
  return bloques.map(b => {
    if (b.tipo === "ok") return `<div class="lab-msg">✓ ${esc(b.texto)}</div>`;
    if (b.tipo === "aviso") return `<div class="lab-msg aviso">⚠ ${esc(b.texto)}</div>`;
    if (b.tipo === "texto") return `<h3>${esc(b.titulo)}</h3><pre class="lab-pre">${b.lineas.map(esc).join("\n")}</pre>`;
    if (b.tipo === "red") return `<h3>${esc(b.titulo)}</h3>${dibujarRed(b, b.camino, b.camino2)}`;
    return `<h3>${esc(b.titulo)}</h3><div class="lab-tabla"><table><tr>${b.columnas.map(c => `<th>${esc(c)}</th>`).join("")}</tr>
      ${b.filas.map(f => `<tr>${f.map(x => `<td>${esc(x)}</td>`).join("")}</tr>`).join("")}</table></div>`;
  }).join("");
}

function campoLab(c) {
  const id = `lab-${c.n}`;
  if (c.tipo === "usuario") {
    return `<div><label for="${id}">${esc(c.l)}</label><select id="${id}" data-campo="${c.n}">${usuariosLab.map(u =>
      `<option value="${esc(u.id)}" ${u.id === c.v ? "selected" : ""}>${esc(u.usuario)}</option>`).join("")}</select></div>`;
  }
  if (c.tipo === "select") {
    return `<div><label for="${id}">${esc(c.l)}</label><select id="${id}" data-campo="${c.n}">${c.ops.map(([v, t]) =>
      `<option value="${esc(v)}" ${v === c.v ? "selected" : ""}>${esc(t)}</option>`).join("")}</select></div>`;
  }
  return `<div><label for="${id}">${esc(c.l)}</label><input id="${id}" data-campo="${c.n}" value="${esc(c.v)}"></div>`;
}

async function paginaLaboratorio(param) {
  if (!usuariosLab) usuariosLab = await api("GET", "/api/lab/usuarios");
  const todos = LAB.flatMap(g => g.talleres.map(t => ({ ...t, corte: g.corte })));
  const actual = todos.find(t => t.id === param) || todos[0];
  vista().innerHTML = `
    <div class="tarjeta">
      <div class="cabecera"><h2>🧪 Laboratorio de talleres</h2><button class="btn sec chico" id="lab-reiniciar">Reiniciar laboratorio</button></div>
      <p class="explicacion">Aquí están todos los talleres y parciales del semestre. Usan el mismo código del menú de consola y la red original
        de los talleres, así que los resultados coinciden con los documentos. Lo que hagas aquí no cambia la red social.</p>
      ${LAB.map(g => `<div class="lab-corte">${esc(g.corte)}</div><div class="lab-chips">${g.talleres.map(t =>
        `<a class="lab-chip ${t.id === actual.id ? "activo" : ""}" href="#/laboratorio/${t.id}">${esc(t.titulo)}</a>`).join("")}</div>`).join("")}
    </div>
    <div class="tarjeta">
      <div class="cabecera"><h2>${esc(actual.titulo)}</h2><span class="chip alg">${esc(actual.taller)}</span></div>
      <p class="explicacion">${esc(actual.desc)}</p>
      ${actual.campos.length ? `<div class="lab-campos">${actual.campos.map(campoLab).join("")}</div>` : ""}
      <div class="fila" style="flex-wrap:wrap;margin-top:14px">${actual.botones.map(([t, a, sec]) =>
        `<button class="btn ${sec ? "sec" : ""} chico" data-lab="${a}">${esc(t)}</button>`).join("")}
        ${actual.enlace ? `<a class="btn sec chico" href="${actual.enlace[0]}">${esc(actual.enlace[1])} →</a>` : ""}</div>
      <div id="lab-resultado" style="margin-top:14px"></div>
    </div>`;
  const correr = accion => intentar(async () => {
    const datos = {};
    document.querySelectorAll("[data-campo]").forEach(el => { datos[el.dataset.campo] = el.value; });
    const r = await api("POST", `/api/lab/${accion}`, datos);
    $("#lab-resultado").innerHTML = pintarBloques(r.bloques);
  });
  vista().querySelectorAll("[data-lab]").forEach(b => b.onclick = () => correr(b.dataset.lab));
  $("#lab-reiniciar").onclick = () => intentar(async () => {
    const r = await api("POST", "/api/lab/reiniciar_todo", {});
    $("#lab-resultado").innerHTML = pintarBloques(r.bloques);
  });
  correr(actual.botones[0][1]);                    // muestra algo de una vez
}

// ------------------------------------------------------------ columna lateral
async function lateral() {
  const caja = $("#lateral");
  if (getComputedStyle(caja).display === "none") return;
  const r = await api("GET", "/api/explorar").catch(() => null);
  if (!r) return;
  caja.innerHTML = `<div class="tarjeta"><div class="cabecera"><h3>A quién seguir</h3>${alg("BFS")}</div>
    ${r.sugerencias.slice(0, 4).map(s => `<div class="fila" style="margin:10px 0">${avatar(s.usuario, "mini")}
      <div style="flex:1;min-width:0"><b>${enlaceUsuario(s.id, s.usuario)}</b><div class="suave chico">${s.nivel ? `vía ${esc(s.por_medio_de)}` : "popular"}</div></div>
      <button class="btn chico" data-accion="seguir" data-uid="${esc(s.id)}">Seguir</button></div>`).join("") || "<p class='suave chico'>Nada por ahora.</p>"}
    <a class="chico" href="#/explorar">Ver más</a></div>
    <div class="tarjeta"><h3>Tendencias</h3>${r.juegos.slice(0, 5).map((j, i) =>
      `<div class="fila chico" style="margin:6px 0"><span class="suave">${i + 1}</span><b style="flex:1">${esc(j.nombre)}</b>
       <span class="suave">${Math.round(j.popularidad / 1000)}k</span></div>`).join("")}</div>
    <p class="suave chico" style="padding:0 6px">Gamefolks · Estructuras No Lineales<br>Sebastian Constain, Natali Miranda, Jorge Nocua y Camilo Rodriguez</p>`;
}

// ------------------------------------------------------------ arranque
$("#modal").addEventListener("click", ev => { if (ev.target.id === "modal") cerrarModal(); });

(async function iniciar() {
  estado.catalogos = await api("GET", "/api/catalogos").catch(() => estado.catalogos);
  prepararEntrada();
  prepararBuscador();
  try { await mostrarApp(await api("GET", "/api/yo")); } catch (_) { mostrarEntrada(); }
})();
