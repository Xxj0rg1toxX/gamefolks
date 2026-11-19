"""Empaqueta todo lo de python/ en UN solo archivo (python/paquete.json) que el navegador copia a Pyodide.
Córrelo cada vez que cambies algo en python/:   python tools/generar_paquete.py"""
import json, os
raiz = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python")
archivos = {}
for d, _, fs in os.walk(raiz):
    if "__pycache__" in d:
        continue
    for f in fs:
        if f.endswith((".py", ".json")) and f not in ("paquete.json", "manifest.json"):
            ruta = os.path.relpath(os.path.join(d, f), raiz).replace(os.sep, "/")
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                archivos[ruta] = fh.read()
with open(os.path.join(raiz, "paquete.json"), "w", encoding="utf-8") as out:
    json.dump({"archivos": archivos}, out, ensure_ascii=False)
print(len(archivos), "archivos empaquetados en python/paquete.json")
