# Gamefolks · Red social gamer (versión GitHub Pages)

**Equipo Gamefolks:** Sebastian Constain, Natali Miranda, Jorge Nocua y Camilo Rodriguez

Es la misma app web del proyecto (inicio, buscador, explorar, conexiones, eventos, premios, moderación y laboratorio),
pero convertida en una página **estática** que se puede ver directamente en GitHub Pages, sin instalar nada.

## Cómo publicarla en GitHub (5 pasos)

1. En GitHub: **New repository** (por ejemplo `gamefolks`), público.
2. Sube **todo el contenido de esta carpeta** a la raíz del repositorio (arrastra los archivos en *Add file → Upload files*, o usa `git add . && git commit && git push`). Debe verse `index.html` en la raíz y también el archivo oculto `.nojekyll`.
3. Ve a **Settings → Pages**.
4. En *Build and deployment* elige **Deploy from a branch**, rama `main`, carpeta `/ (root)` y **Save**.
5. Espera 1–2 minutos: la página queda en `https://TU_USUARIO.github.io/gamefolks/`.

Usuario de prueba: **Juana_Gamer** (moderadora) o **Valentina_Streams** · clave **gamefolks123**. También se puede crear una cuenta.

## Cómo verla en tu computador antes de subirla

No funciona con doble clic en `index.html` (los navegadores bloquean WebAssembly desde `file://`). Usa un servidor local:

    python -m http.server 8000      # y abre http://localhost:8000

## Cómo funciona (qué cambió frente a la versión Flask)

GitHub Pages solo sirve archivos; no puede correr Flask ni SQLite. Para no reescribir los algoritmos:

| Versión Flask | Versión GitHub Pages |
|---|---|
| Servidor Flask (`web/app.py`) | `python/web/api.py`: mismas rutas `/api/...`, como despachador en Python puro |
| SQLite (`web/db.py`) | `python/web/almacen.py`: las mismas tablas como listas y diccionarios; se guarda en `localStorage` |
| Python en el servidor | **Pyodide** (Python compilado a WebAssembly) corre dentro del navegador, vendorizado en `pyodide/` |
| `fetch("/api/...")` a Flask | `static/puente.js` intercepta esas llamadas y se las pasa a Python; `static/app.js` casi no cambió |
| `model/`, `controller/`, `web/laboratorio.py` | **Sin cambios**: son exactamente el mismo código de los algoritmos |

```
index.html            # pantalla de la app
static/               # app.js (frontend), puente.js (navegador <-> Python), styles.css
pyodide/              # runtime de Python en WebAssembly (sin depender de CDNs)
python/               # model/ controller/ web/ data/  (+ paquete.json: todo el código en un solo archivo)
tests/test_api_local.py   # las mismas pruebas de la API de la versión Flask, contra api.py
tools/generar_paquete.py
```

## Pruebas

    python tests/test_api_local.py        # imprime: API LOCAL OK

Si agregas o quitas archivos en `python/`, corre `python tools/generar_paquete.py` para actualizar `python/paquete.json`.

## Limitaciones

- Es una demo: **los datos (cuentas, posts, eventos) viven solo en el navegador de cada persona** y no se comparten entre usuarios. El enlace *Restablecer datos de la demo* (pantalla de entrada) vuelve a los datos de ejemplo.
- Las contraseñas se guardan con hash sha256 con sal en el propio navegador; no es un sistema de autenticación real.
- La primera carga descarga ~13 MB (Python + WebAssembly); después queda en caché.

Pyodide es software libre (licencia MPL-2.0): https://pyodide.org
